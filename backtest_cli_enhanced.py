#!/usr/bin/env python3
"""
BACKTEST CLI ENHANCED - DADOS HISTÓRICOS REAIS DA API BYBIT V5 + GESTÃO DE CAPITAL
Sistema de Trading Automatizado - Suporte a múltiplas estratégias combinadas + Capital Inicial
"""

import asyncio
import json
import logging
import os
import sys
import time
import hmac
import hashlib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Importar o CapitalManager
from capital_manager import CapitalManager, CapitalConfig, create_default_capital_config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('backtest_enhanced.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BybitAPIV5RealData:
    """Cliente para API V5 da Bybit - Dados Históricos Reais"""
    
    def __init__(self):
        # Tentar carregar credenciais de múltiplas fontes
        self.api_key = None
        self.api_secret = None
        
        # 1. Tentar variáveis de ambiente primeiro
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        
        # 2. Se não encontrar, tentar arquivo de configuração
        if not self.api_key or not self.api_secret:
            self._load_credentials_from_config()
        
        # 3. Verificar se conseguiu carregar
        if not self.api_key or not self.api_secret:
            raise ValueError(
                "❌ Credenciais da API Bybit não encontradas!\n"
                "Configure uma das opções:\n"
                "1. Variáveis de ambiente: BYBIT_API_KEY e BYBIT_API_SECRET\n"
                "2. Arquivo config/exchange_settings.json com as chaves da API"
            )
        
        self.base_url = 'https://api.bybit.com'
        
        print(f"✅ API Bybit configurada: {self.api_key[:8]}...")
        
        # Timeframes suportados pela API
        self.timeframe_mapping = {
            '1m': '1',
            '3m': '3', 
            '5m': '5',
            '15m': '15',
            '30m': '30',
            '1h': '60',
            '2h': '120',
            '4h': '240',
            '6h': '360',
            '12h': '720',
            '1d': 'D',
            '1w': 'W',
            '1M': 'M'
        }
    
    def _load_credentials_from_config(self):
        """Carrega credenciais do arquivo de configuração"""
        try:
            config_path = 'config/exchange_settings.json'
            
            if not os.path.exists(config_path):
                print(f"⚠️  Arquivo {config_path} não encontrado")
                return
            
            print(f"🔄 Carregando credenciais de {config_path}...")
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Verificar se tem configuração da Bybit
            if 'exchanges' in config and 'bybit' in config['exchanges']:
                bybit_config = config['exchanges']['bybit']
                
                # Tentar diferentes formatos de configuração
                if 'api_key' in bybit_config and 'api_secret' in bybit_config:
                    # Formato direto
                    self.api_key = bybit_config['api_key']
                    self.api_secret = bybit_config['api_secret']
                    print("✅ Credenciais carregadas diretamente do arquivo")
                    
                elif 'api_key_env' in bybit_config and 'api_secret_env' in bybit_config:
                    # Formato com nomes de variáveis de ambiente
                    api_key_env = bybit_config['api_key_env']
                    api_secret_env = bybit_config['api_secret_env']
                    
                    self.api_key = os.getenv(api_key_env)
                    self.api_secret = os.getenv(api_secret_env)
                    
                    if self.api_key and self.api_secret:
                        print(f"✅ Credenciais carregadas das variáveis {api_key_env} e {api_secret_env}")
                    else:
                        print(f"⚠️  Variáveis {api_key_env} e {api_secret_env} não encontradas")
                
                else:
                    print("⚠️  Formato de configuração da Bybit não reconhecido")
            
            else:
                print("⚠️  Configuração da Bybit não encontrada no arquivo")
                
        except Exception as e:
            print(f"⚠️  Erro ao carregar configuração: {e}")
    
    def test_connection(self) -> bool:
        """Testa conexão com a API"""
        try:
            print("🔄 Testando conexão com API Bybit...")
            
            # Endpoint público (não requer autenticação)
            response = requests.get(f"{self.base_url}/v5/market/time", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                server_time = data['result']['timeSecond']
                print(f"✅ Conexão OK - Server Time: {server_time}")
                return True
            else:
                print(f"❌ Erro na conexão: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            return False
    
    def get_historical_klines(self, symbol: str, interval: str, start_time: str, end_time: str) -> List[Dict]:
        """Obtém dados históricos reais da API Bybit"""
        try:
            print(f"📊 Obtendo dados históricos: {symbol} {interval} de {start_time} a {end_time}")
            
            # Converter datas para timestamps
            start_timestamp = int(datetime.strptime(start_time, '%Y-%m-%d').timestamp() * 1000)
            end_timestamp = int(datetime.strptime(end_time, '%Y-%m-%d').timestamp() * 1000)
            
            # Mapear timeframe
            bybit_interval = self.timeframe_mapping.get(interval)
            if not bybit_interval:
                raise ValueError(f"Timeframe {interval} não suportado")
            
            all_data = []
            current_start = start_timestamp
            
            # API Bybit retorna máximo 1000 candles por request
            max_candles_per_request = 1000
            
            while current_start < end_timestamp:
                print(f"   📈 Buscando dados a partir de {datetime.fromtimestamp(current_start/1000).strftime('%Y-%m-%d %H:%M')}")
                
                # Parâmetros da requisição
                params = {
                    'category': 'linear',  # Futuros USDT
                    'symbol': symbol,
                    'interval': bybit_interval,
                    'start': current_start,
                    'end': min(current_start + (max_candles_per_request * self._get_interval_ms(interval)), end_timestamp),
                    'limit': max_candles_per_request
                }
                
                # Fazer requisição
                response = requests.get(
                    f"{self.base_url}/v5/market/kline",
                    params=params,
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"❌ Erro na API: {response.status_code} - {response.text}")
                    break
                
                data = response.json()
                
                if data['retCode'] != 0:
                    print(f"❌ Erro da API: {data['retMsg']}")
                    break
                
                klines = data['result']['list']
                
                if not klines:
                    print("   ⚠️  Sem mais dados disponíveis")
                    break
                
                # Processar dados (API retorna em ordem decrescente)
                klines.reverse()  # Ordenar cronologicamente
                
                for kline in klines:
                    timestamp_ms = int(kline[0])
                    
                    # Evitar duplicatas
                    if timestamp_ms <= current_start:
                        continue
                    
                    # Converter para formato padrão
                    candle = {
                        'timestamp': datetime.fromtimestamp(timestamp_ms / 1000).isoformat(),
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5]),
                        'turnover': float(kline[6]) if len(kline) > 6 else 0
                    }
                    
                    all_data.append(candle)
                    current_start = timestamp_ms
                
                print(f"   ✅ Obtidos {len(klines)} candles - Total: {len(all_data)}")
                
                # Rate limiting - evitar excesso de requisições
                time.sleep(0.1)
                
                # Atualizar para próxima iteração
                if klines:
                    current_start = int(klines[-1][0]) + 1
                else:
                    break
            
            print(f"✅ Total de dados obtidos: {len(all_data)} candles")
            
            if not all_data:
                raise ValueError("Nenhum dado histórico obtido da API")
            
            # Validar qualidade dos dados
            self._validate_real_data(all_data, symbol, interval)
            
            return all_data
            
        except Exception as e:
            logger.error(f"Erro ao obter dados históricos: {e}")
            raise
    
    def _get_interval_ms(self, interval: str) -> int:
        """Converte intervalo para milissegundos"""
        mapping = {
            '1m': 60 * 1000,
            '3m': 3 * 60 * 1000,
            '5m': 5 * 60 * 1000,
            '15m': 15 * 60 * 1000,
            '30m': 30 * 60 * 1000,
            '1h': 60 * 60 * 1000,
            '2h': 2 * 60 * 60 * 1000,
            '4h': 4 * 60 * 60 * 1000,
            '6h': 6 * 60 * 60 * 1000,
            '12h': 12 * 60 * 60 * 1000,
            '1d': 24 * 60 * 60 * 1000,
            '1w': 7 * 24 * 60 * 60 * 1000
        }
        return mapping.get(interval, 60 * 1000)
    
    def _validate_real_data(self, data: List[Dict], symbol: str, interval: str):
        """Valida dados reais obtidos da API"""
        if len(data) < 10:
            raise ValueError(f"Dados insuficientes: apenas {len(data)} candles")
        
        # Verificar integridade dos dados
        for i, candle in enumerate(data[:5]):  # Verificar primeiros 5
            if candle['high'] < candle['low']:
                raise ValueError(f"Dados inválidos no candle {i}: High < Low")
            if candle['high'] < max(candle['open'], candle['close']):
                raise ValueError(f"Dados inválidos no candle {i}: High < max(Open, Close)")
            if candle['low'] > min(candle['open'], candle['close']):
                raise ValueError(f"Dados inválidos no candle {i}: Low > min(Open, Close)")
        
        # Verificar variação de preços
        prices = [d['close'] for d in data]
        price_range = (max(prices) - min(prices)) / min(prices)
        
        print(f"✅ Dados reais validados:")
        print(f"   📊 {len(data)} candles de {symbol}")
        print(f"   📈 Variação de preços: {price_range:.2%}")
        print(f"   📅 Período: {data[0]['timestamp'][:10]} a {data[-1]['timestamp'][:10]}")

class RealDataIndicators:
    """Indicadores técnicos para dados reais"""
    
    @staticmethod
    def ema(prices: List[float], period: int) -> List[float]:
        """Média móvel exponencial"""
        if len(prices) < period:
            return [prices[0] if prices else 0] * len(prices)
        
        multiplier = 2 / (period + 1)
        ema_values = [0] * len(prices)
        
        # Primeira EMA é a média simples
        ema_values[period-1] = sum(prices[:period]) / period
        
        # Calcular EMA para o resto
        for i in range(period, len(prices)):
            ema_values[i] = (prices[i] * multiplier) + (ema_values[i-1] * (1 - multiplier))
        
        # Preencher valores iniciais
        for i in range(period-1):
            ema_values[i] = ema_values[period-1]
        
        return ema_values
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[float]:
        """RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return [50] * len(prices)
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [max(delta, 0) for delta in deltas]
        losses = [abs(min(delta, 0)) for delta in deltas]
        
        rsi_values = [50] * len(prices)
        
        # Primeira média
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi_values[i + 1] = 100
            else:
                rs = avg_gain / avg_loss
                rsi_values[i + 1] = 100 - (100 / (1 + rs))
        
        return rsi_values
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> Tuple[List[float], List[float], List[float]]:
        """Bandas de Bollinger"""
        if len(prices) < period:
            return [prices[0]] * len(prices), [prices[0]] * len(prices), [prices[0]] * len(prices)
        
        middle = []  # SMA
        upper = []
        lower = []
        
        for i in range(len(prices)):
            if i < period - 1:
                window = prices[:i+1]
            else:
                window = prices[i-period+1:i+1]
            
            sma = sum(window) / len(window)
            
            # Calcular desvio padrão
            variance = sum((x - sma) ** 2 for x in window) / len(window)
            std = variance ** 0.5
            
            middle.append(sma)
            upper.append(sma + (std_dev * std))
            lower.append(sma - (std_dev * std))
        
        return middle, upper, lower

class RealDataStrategyEngine:
    """Engine de estratégias para dados reais"""
    
    def __init__(self):
        self.indicators = RealDataIndicators()
        
        self.strategies = {
            'ema_crossover': self._ema_crossover_strategy,
            'rsi_mean_reversion': self._rsi_mean_reversion_strategy,
            'bollinger_breakout': self._bollinger_breakout_strategy
        }
        
        self.strategy_configs = {
            'ema_crossover': {
                'name': 'EMA Crossover (Dados Reais)',
                'description': 'Cruzamento de médias móveis exponenciais com dados históricos reais',
                'params': {'fast_ema': 12, 'slow_ema': 26, 'volume_filter': True},
                'risk_level': 'medium',
                'best_timeframes': ['15m', '30m', '1h'],
                'market_conditions': 'Tendencial'
            },
            'rsi_mean_reversion': {
                'name': 'RSI Mean Reversion (Dados Reais)',
                'description': 'Reversão à média com RSI em dados históricos reais',
                'params': {'rsi_period': 14, 'oversold': 30, 'overbought': 70},
                'risk_level': 'low',
                'best_timeframes': ['5m', '15m', '30m'],
                'market_conditions': 'Lateral'
            },
            'bollinger_breakout': {
                'name': 'Bollinger Breakout (Dados Reais)',
                'description': 'Rompimento de bandas de Bollinger com dados históricos reais',
                'params': {'bb_period': 20, 'bb_std': 2.0, 'volume_filter': True},
                'risk_level': 'high',
                'best_timeframes': ['15m', '1h', '4h'],
                'market_conditions': 'Volátil'
            }
        }
    
    def _ema_crossover_strategy(self, data: List[Dict], config: Dict) -> List[Dict]:
        """Estratégia EMA Crossover com dados reais"""
        closes = [float(d['close']) for d in data]
        volumes = [float(d['volume']) for d in data]
        
        fast_period = config.get('fast_ema', 12)
        slow_period = config.get('slow_ema', 26)
        use_volume_filter = config.get('volume_filter', True)
        
        fast_ema = self.indicators.ema(closes, fast_period)
        slow_ema = self.indicators.ema(closes, slow_period)
        
        # Filtro de volume (média móvel de 20 períodos)
        volume_ma = []
        for i in range(len(volumes)):
            if i < 20:
                volume_ma.append(sum(volumes[:i+1]) / (i+1))
            else:
                volume_ma.append(sum(volumes[i-19:i+1]) / 20)
        
        signals = []
        for i, d in enumerate(data):
            signal = 0
            strength = 0.0
            
            if i > 0 and fast_ema[i] > 0 and slow_ema[i] > 0:
                # Filtro de volume
                volume_ok = True
                if use_volume_filter and i > 0:
                    volume_ok = volumes[i] > volume_ma[i] * 1.1
                
                # Long: EMA rápida cruza acima da lenta
                if (fast_ema[i] > slow_ema[i] and 
                    fast_ema[i-1] <= slow_ema[i-1] and 
                    volume_ok):
                    signal = 1
                    strength = min(abs(fast_ema[i] - slow_ema[i]) / closes[i], 1.0)
                
                # Short: EMA rápida cruza abaixo da lenta
                elif (fast_ema[i] < slow_ema[i] and 
                      fast_ema[i-1] >= slow_ema[i-1] and 
                      volume_ok):
                    signal = -1
                    strength = min(abs(fast_ema[i] - slow_ema[i]) / closes[i], 1.0)
            
            signals.append({
                **d,
                'signal': signal,
                'signal_strength': strength,
                'fast_ema': fast_ema[i],
                'slow_ema': slow_ema[i],
                'volume_ma': volume_ma[i]
            })
        
        return signals
    
    def _rsi_mean_reversion_strategy(self, data: List[Dict], config: Dict) -> List[Dict]:
        """Estratégia RSI Mean Reversion com dados reais"""
        closes = [float(d['close']) for d in data]
        
        rsi_period = config.get('rsi_period', 14)
        oversold = config.get('oversold', 30)
        overbought = config.get('overbought', 70)
        
        rsi_values = self.indicators.rsi(closes, rsi_period)
        
        signals = []
        for i, d in enumerate(data):
            signal = 0
            strength = 0.0
            rsi = rsi_values[i]
            
            # Long: RSI oversold
            if rsi < oversold:
                signal = 1
                strength = (oversold - rsi) / oversold
            
            # Short: RSI overbought
            elif rsi > overbought:
                signal = -1
                strength = (rsi - overbought) / (100 - overbought)
            
            signals.append({
                **d,
                'signal': signal,
                'signal_strength': min(strength, 1.0),
                'rsi': rsi
            })
        
        return signals
    
    def _bollinger_breakout_strategy(self, data: List[Dict], config: Dict) -> List[Dict]:
        """Estratégia Bollinger Breakout com dados reais"""
        closes = [float(d['close']) for d in data]
        volumes = [float(d['volume']) for d in data]
        
        bb_period = config.get('bb_period', 20)
        bb_std = config.get('bb_std', 2.0)
        use_volume_filter = config.get('volume_filter', True)
        
        middle, upper, lower = self.indicators.bollinger_bands(closes, bb_period, bb_std)
        
        # Filtro de volume
        volume_ma = []
        for i in range(len(volumes)):
            if i < 20:
                volume_ma.append(sum(volumes[:i+1]) / (i+1))
            else:
                volume_ma.append(sum(volumes[i-19:i+1]) / 20)
        
        signals = []
        for i, d in enumerate(data):
            signal = 0
            strength = 0.0
            
            if i > 0:
                # Filtro de volume
                volume_ok = True
                if use_volume_filter:
                    volume_ok = volumes[i] > volume_ma[i] * 1.2
                
                # Long: Preço rompe banda superior
                if (closes[i] > upper[i] and 
                    closes[i-1] <= upper[i-1] and 
                    volume_ok):
                    signal = 1
                    band_width = (upper[i] - lower[i]) / middle[i]
                    strength = min(band_width, 1.0)
                
                # Short: Preço rompe banda inferior
                elif (closes[i] < lower[i] and 
                      closes[i-1] >= lower[i-1] and 
                      volume_ok):
                    signal = -1
                    band_width = (upper[i] - lower[i]) / middle[i]
                    strength = min(band_width, 1.0)
            
            signals.append({
                **d,
                'signal': signal,
                'signal_strength': strength,
                'bb_upper': upper[i],
                'bb_middle': middle[i],
                'bb_lower': lower[i],
                'volume_ma': volume_ma[i]
            })
        
        return signals

class EnhancedBacktestEngine:
    """Engine de backtesting com gestão de capital aprimorada"""
    
    def __init__(self):
        self.api_client = BybitAPIV5RealData()
        self.strategy_engine = RealDataStrategyEngine()
        
        # Testar conexão na inicialização
        if not self.api_client.test_connection():
            raise ConnectionError("❌ Não foi possível conectar à API Bybit")
    
    def run_backtest_with_capital(self, symbol: str, strategy: str, timeframe: str, 
                                 start_date: str, end_date: str, capital_manager: CapitalManager) -> Dict:
        """Executa backtest com gestão de capital"""
        try:
            print(f"\n🔄 Executando {strategy} em {symbol} ({timeframe}) - DADOS REAIS + CAPITAL")
            print("="*70)
            print(f"💰 Capital inicial: ${capital_manager.config.initial_capital_usd:,.2f}")
            print(f"📊 Position size: {capital_manager.config.position_size_percent}%")
            print(f"🔄 Compound interest: {capital_manager.config.compound_interest}")
            print("="*70)
            
            start_time = time.time()
            
            # 1. Obter dados históricos reais da API
            print("📊 Fase 1: Obtendo dados históricos da API Bybit...")
            data_start = time.time()
            historical_data = self.api_client.get_historical_klines(
                symbol, timeframe, start_date, end_date
            )
            data_time = time.time() - data_start
            print(f"   ✅ Dados obtidos em {data_time:.2f}s")
            
            # 2. Aplicar estratégia
            print("🧠 Fase 2: Aplicando estratégia aos dados reais...")
            strategy_start = time.time()
            strategy_func = self.strategy_engine.strategies[strategy]
            config = self.strategy_engine.strategy_configs[strategy]['params']
            signals = strategy_func(historical_data, config)
            strategy_time = time.time() - strategy_start
            print(f"   ✅ Estratégia aplicada em {strategy_time:.2f}s")
            
            # 3. Simular trades com gestão de capital
            print("💰 Fase 3: Simulando trades com gestão de capital...")
            capital_start = time.time()
            
            # Reset do capital manager
            capital_manager.reset_capital()
            
            # Parâmetros de trading
            stop_loss_pct = 0.015  # 1.5%
            take_profit_pct = 0.03  # 3%
            max_holding_periods = 48  # Máximo de períodos em posição
            
            position = None
            valid_signals = [s for s in signals if s['signal'] != 0]
            
            print(f"   📊 Processando {len(valid_signals)} sinais válidos...")
            
            for i, signal in enumerate(signals):
                current_price = float(signal['close'])
                
                # Entrada em nova posição
                if signal['signal'] != 0 and position is None:
                    position = {
                        'direction': signal['signal'],
                        'entry_price': current_price,
                        'entry_time': signal['timestamp'],
                        'entry_index': i,
                        'signal_strength': signal['signal_strength']
                    }
                    
                    # Definir níveis de saída
                    if signal['signal'] == 1:  # Long
                        position['stop_loss'] = current_price * (1 - stop_loss_pct)
                        position['take_profit'] = current_price * (1 + take_profit_pct)
                    else:  # Short
                        position['stop_loss'] = current_price * (1 + stop_loss_pct)
                        position['take_profit'] = current_price * (1 - take_profit_pct)
                
                # Verificar condições de saída
                elif position is not None:
                    should_exit = False
                    exit_reason = ""
                    
                    # Stop loss
                    if ((position['direction'] == 1 and current_price <= position['stop_loss']) or
                        (position['direction'] == -1 and current_price >= position['stop_loss'])):
                        should_exit = True
                        exit_reason = "stop_loss"
                    
                    # Take profit
                    elif ((position['direction'] == 1 and current_price >= position['take_profit']) or
                          (position['direction'] == -1 and current_price <= position['take_profit'])):
                        should_exit = True
                        exit_reason = "take_profit"
                    
                    # Sinal contrário
                    elif signal['signal'] == -position['direction']:
                        should_exit = True
                        exit_reason = "signal_reversal"
                    
                    # Tempo máximo em posição
                    elif i - position['entry_index'] >= max_holding_periods:
                        should_exit = True
                        exit_reason = "max_time"
                    
                    # Fechar posição usando CapitalManager
                    if should_exit:
                        trade_result = capital_manager.execute_trade(
                            entry_price=position['entry_price'],
                            exit_price=current_price,
                            direction=position['direction'],
                            timestamp=signal['timestamp'],
                            exit_reason=exit_reason,
                            stop_loss_percent=stop_loss_pct
                        )
                        
                        position = None
            
            capital_time = time.time() - capital_start
            print(f"   ✅ Simulação concluída em {capital_time:.2f}s")
            
            # 4. Obter métricas do CapitalManager
            print("📊 Fase 4: Calculando métricas com gestão de capital...")
            metrics = capital_manager.get_metrics()
            
            total_time = time.time() - start_time
            print(f"\n✅ BACKTEST CONCLUÍDO EM {total_time:.2f}s")
            
            return {
                'symbol': symbol,
                'strategy': strategy,
                'timeframe': timeframe,
                'period': f"{start_date}_to_{end_date}",
                'data_source': 'bybit_api_v5_real_with_capital',
                'metrics': metrics,
                'total_signals': len(valid_signals),
                'data_points': len(historical_data),
                'execution_time': {
                    'data_retrieval': data_time,
                    'strategy_application': strategy_time,
                    'capital_simulation': capital_time,
                    'total': total_time
                },
                'capital_config': capital_manager.config.to_dict(),
                'data_quality': {
                    'source': 'Bybit API V5 - Dados Históricos Reais',
                    'first_candle': historical_data[0]['timestamp'] if historical_data else None,
                    'last_candle': historical_data[-1]['timestamp'] if historical_data else None,
                    'price_range': f"{min(d['close'] for d in historical_data):.2f} - {max(d['close'] for d in historical_data):.2f}"
                }
            }
            
        except Exception as e:
            logger.error(f"Erro no backtest com capital: {e}")
            return {'error': str(e)}

class BacktestCLIEnhanced:
    """CLI Enhanced para backtesting com gestão de capital"""
    
    def __init__(self):
        try:
            self.backtest_engine = EnhancedBacktestEngine()
            self.symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT', 'SOLUSDT', 'DOTUSDT', 'AVAXUSDT']
            self.timeframes = ['5m', '15m', '30m', '1h', '4h', '1d']
            
            # Períodos históricos reais com contexto de mercado
            self.historical_periods = {
                'Q1_2024': {
                    'start': '2024-01-01', 'end': '2024-03-31', 
                    'name': 'Q1 2024 - Bull Market (BTC: $42k → $73k)',
                    'context': 'Forte tendência de alta, aprovação ETF Bitcoin'
                },
                'Q2_2024': {
                    'start': '2024-04-01', 'end': '2024-06-30',
                    'name': 'Q2 2024 - Correção (BTC: $73k → $60k)', 
                    'context': 'Correção saudável, consolidação'
                },
                'Q3_2024': {
                    'start': '2024-07-01', 'end': '2024-09-30',
                    'name': 'Q3 2024 - Recuperação (BTC: $60k → $65k)',
                    'context': 'Recuperação gradual, mercado lateral'
                },
                'Q4_2024': {
                    'start': '2024-10-01', 'end': '2024-12-31',
                    'name': 'Q4 2024 - Rally Final (BTC: $65k → $100k)',
                    'context': 'Rally de fim de ano, máximas históricas'
                },
                'RECENT_30D': {
                    'start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                    'end': datetime.now().strftime('%Y-%m-%d'),
                    'name': 'Últimos 30 dias - Dados Recentes',
                    'context': 'Período mais recente disponível'
                },
                'RECENT_7D': {
                    'start': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                    'end': datetime.now().strftime('%Y-%m-%d'),
                    'name': 'Última semana - Dados Muito Recentes',
                    'context': 'Análise de curto prazo'
                }
            }
            
            # Tentar carregar configuração de capital salva
            self.capital_manager = CapitalManager.load_config()
            if self.capital_manager is None:
                # Criar configuração padrão
                config = create_default_capital_config(10000.0)
                self.capital_manager = CapitalManager(config)
                print("💰 Usando configuração padrão de capital: $10,000")
            else:
                print(f"💰 Configuração de capital carregada: ${self.capital_manager.config.initial_capital_usd:,.2f}")
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            sys.exit(1)
    
    def display_header(self):
        """Exibe cabeçalho"""
        print("\n" + "="*80)
        print("🚀 BACKTEST CLI ENHANCED - DADOS REAIS + GESTÃO DE CAPITAL")
        print("="*80)
        print("✅ Conectado à sua API Bybit configurada")
        print("📈 Dados históricos reais obtidos diretamente da exchange")
        print("💰 Gestão de capital com position sizing dinâmico")
        print("🔄 Compound interest e reinvestimento automático")
        print("📊 Métricas precisas em USD e percentuais")
        print("🎯 Estratégias testadas em condições reais de mercado")
        print("="*80)
    
    def display_menu(self):
        """Exibe menu principal"""
        print("\n📋 OPÇÕES DISPONÍVEIS:")
        print("   1️⃣  Configurar Capital Inicial")
        print("   2️⃣  Backtesting Rápido com Capital (BTCUSDT, 15m, Q4 2024)")
        print("   3️⃣  Backtesting Personalizado com Capital")
        print("   4️⃣  Análise de Períodos Históricos")
        print("   5️⃣  Informações das Estratégias")
        print("   6️⃣  Teste de Conexão API")
        print("   7️⃣  Ver Configuração Atual de Capital")
        print("   0️⃣  Sair")
        print()
    
    def configure_capital(self):
        """Configurar capital inicial e parâmetros"""
        print("\n💰 CONFIGURAÇÃO DE CAPITAL INICIAL")
        print("="*50)
        
        # Mostrar configuração atual
        current_config = self.capital_manager.config
        print(f"\n📊 CONFIGURAÇÃO ATUAL:")
        print(f"   💰 Capital inicial: ${current_config.initial_capital_usd:,.2f}")
        print(f"   📊 Position size: {current_config.position_size_percent}%")
        print(f"   🔄 Compound interest: {'Sim' if current_config.compound_interest else 'Não'}")
        print(f"   ⚠️  Risco por trade: {current_config.risk_per_trade_percent}%")
        print(f"   📏 Posição mínima: ${current_config.min_position_size_usd:.2f}")
        print(f"   📏 Posição máxima: ${current_config.max_position_size_usd:,.2f}")
        
        print(f"\n🔧 NOVA CONFIGURAÇÃO:")
        
        # Capital inicial
        while True:
            try:
                capital_input = input(f"💰 Capital inicial em USD (atual: ${current_config.initial_capital_usd:,.2f}): ").strip()
                if not capital_input:
                    initial_capital = current_config.initial_capital_usd
                    break
                
                initial_capital = float(capital_input)
                if initial_capital < 100:
                    print("❌ Capital mínimo: $100")
                    continue
                if initial_capital > 1000000:
                    print("❌ Capital máximo: $1,000,000")
                    continue
                break
            except ValueError:
                print("❌ Digite um valor numérico válido")
        
        # Position size
        while True:
            try:
                pos_input = input(f"📊 Position size em % do capital (atual: {current_config.position_size_percent}%): ").strip()
                if not pos_input:
                    position_size_percent = current_config.position_size_percent
                    break
                
                position_size_percent = float(pos_input)
                if position_size_percent < 0.1:
                    print("❌ Position size mínimo: 0.1%")
                    continue
                if position_size_percent > 10:
                    print("❌ Position size máximo: 10%")
                    continue
                break
            except ValueError:
                print("❌ Digite um valor numérico válido")
        
        # Compound interest
        compound_input = input(f"🔄 Usar compound interest? (s/N) (atual: {'s' if current_config.compound_interest else 'n'}): ").strip().lower()
        if compound_input == '':
            compound_interest = current_config.compound_interest
        else:
            compound_interest = compound_input == 's'
        
        # Risco por trade
        while True:
            try:
                risk_input = input(f"⚠️  Risco máximo por trade em % (atual: {current_config.risk_per_trade_percent}%): ").strip()
                if not risk_input:
                    risk_per_trade = current_config.risk_per_trade_percent
                    break
                
                risk_per_trade = float(risk_input)
                if risk_per_trade < 0.1:
                    print("❌ Risco mínimo: 0.1%")
                    continue
                if risk_per_trade > 5:
                    print("❌ Risco máximo: 5%")
                    continue
                break
            except ValueError:
                print("❌ Digite um valor numérico válido")
        
        # Criar nova configuração
        new_config = CapitalConfig(
            initial_capital_usd=initial_capital,
            position_size_percent=position_size_percent,
            compound_interest=compound_interest,
            min_position_size_usd=max(10.0, initial_capital * 0.001),  # Mínimo 0.1% do capital
            max_position_size_usd=min(initial_capital * 0.1, 10000.0),  # Máximo 10% do capital
            risk_per_trade_percent=risk_per_trade
        )
        
        # Mostrar resumo
        print(f"\n📋 RESUMO DA NOVA CONFIGURAÇÃO:")
        print(f"   💰 Capital inicial: ${new_config.initial_capital_usd:,.2f}")
        print(f"   📊 Position size: {new_config.position_size_percent}%")
        print(f"   🔄 Compound interest: {'Sim' if new_config.compound_interest else 'Não'}")
        print(f"   ⚠️  Risco por trade: {new_config.risk_per_trade_percent}%")
        print(f"   📏 Posição mínima: ${new_config.min_position_size_usd:.2f}")
        print(f"   📏 Posição máxima: ${new_config.max_position_size_usd:,.2f}")
        
        # Exemplo de position sizing
        example_price = 50000  # Exemplo com BTC
        example_position = new_config.initial_capital_usd * (new_config.position_size_percent / 100)
        print(f"\n💡 EXEMPLO (BTC a ${example_price:,}):")
        print(f"   📊 Tamanho da posição: ${example_position:,.2f}")
        print(f"   🪙 Quantidade: {example_position/example_price:.6f} BTC")
        
        # Confirmar
        confirm = input(f"\n✅ Salvar esta configuração? (s/N): ").strip().lower()
        if confirm == 's':
            self.capital_manager = CapitalManager(new_config)
            if self.capital_manager.save_config():
                print(f"✅ Configuração salva com sucesso!")
            else:
                print(f"⚠️  Configuração aplicada mas não foi possível salvar")
        else:
            print(f"❌ Configuração cancelada")
    
    def view_capital_config(self):
        """Visualizar configuração atual de capital"""
        print("\n💰 CONFIGURAÇÃO ATUAL DE CAPITAL")
        print("="*50)
        
        config = self.capital_manager.config
        
        print(f"💰 Capital inicial: ${config.initial_capital_usd:,.2f}")
        print(f"📊 Position size: {config.position_size_percent}% do capital")
        print(f"🔄 Compound interest: {'✅ Ativado' if config.compound_interest else '❌ Desativado'}")
        print(f"⚠️  Risco por trade: {config.risk_per_trade_percent}% do capital")
        print(f"📏 Posição mínima: ${config.min_position_size_usd:.2f}")
        print(f"📏 Posição máxima: ${config.max_position_size_usd:,.2f}")
        
        # Exemplos de position sizing
        print(f"\n💡 EXEMPLOS DE POSITION SIZING:")
        examples = [
            ("BTCUSDT", 50000),
            ("ETHUSDT", 3000),
            ("BNBUSDT", 300)
        ]
        
        for symbol, price in examples:
            position_size = config.initial_capital_usd * (config.position_size_percent / 100)
            quantity = position_size / price
            
            print(f"   {symbol} (${price:,}): ${position_size:,.2f} = {quantity:.6f} tokens")
        
        # Informações sobre compound interest
        if config.compound_interest:
            print(f"\n🔄 COMPOUND INTEREST:")
            print(f"   ✅ Lucros são reinvestidos automaticamente")
            print(f"   📈 Capital cresce com trades lucrativos")
            print(f"   📊 Position size aumenta conforme capital cresce")
        else:
            print(f"\n🔄 CAPITAL FIXO:")
            print(f"   📊 Position size sempre baseado no capital inicial")
            print(f"   💰 Lucros/perdas não afetam tamanho das posições")
        
        input(f"\n📱 Pressione Enter para continuar...")
    
    def run_quick_backtest_with_capital(self):
        """Backtesting rápido com gestão de capital"""
        print("\n🚀 BACKTESTING RÁPIDO COM GESTÃO DE CAPITAL")
        print("="*60)
        
        # Configuração otimizada
        symbol = 'BTCUSDT'
        timeframe = '15m'
        strategy = 'ema_crossover'
        period = self.historical_periods['Q4_2024']
        
        print(f"📊 Configuração:")
        print(f"   • Símbolo: {symbol}")
        print(f"   • Timeframe: {timeframe}")
        print(f"   • Estratégia: {strategy}")
        print(f"   • Período: {period['name']}")
        print(f"   • Contexto: {period['context']}")
        print(f"   • Capital inicial: ${self.capital_manager.config.initial_capital_usd:,.2f}")
        print(f"   • Position size: {self.capital_manager.config.position_size_percent}%")
        print(f"   • Compound interest: {'Sim' if self.capital_manager.config.compound_interest else 'Não'}")
        
        confirm = input("\n✅ Executar backtest com gestão de capital? (s/N): ").strip().lower()
        if confirm != 's':
            return
        
        print(f"\n🔄 Executando backtesting com gestão de capital...")
        print("="*60)
        
        result = self.backtest_engine.run_backtest_with_capital(
            symbol, strategy, timeframe, period['start'], period['end'], self.capital_manager
        )
        
        if 'error' in result:
            print(f"❌ Erro: {result['error']}")
            return
        
        # Exibir resultados detalhados com capital
        self._display_capital_results(result, period['context'])
        
        # Salvar relatório
        self._save_capital_report(result, 'quick_backtest_with_capital')
    
    def _display_capital_results(self, result: Dict, context: str = ""):
        """Exibe resultados detalhados com informações de capital"""
        metrics = result['metrics']
        
        print(f"\n📊 RESULTADOS DETALHADOS COM GESTÃO DE CAPITAL")
        print("="*70)
        
        # Informações básicas
        print(f"🎯 Estratégia: {result['strategy']}")
        print(f"📊 Símbolo: {result['symbol']} ({result['timeframe']})")
        print(f"📅 Período: {result['period'].replace('_to_', ' a ')}")
        if context:
            print(f"🌍 Contexto: {context}")
        
        # CAPITAL E RETORNOS
        print(f"\n💰 CAPITAL E RETORNOS:")
        print(f"   💰 Capital inicial: ${metrics['initial_capital_usd']:,.2f}")
        print(f"   💰 Capital final: ${metrics['final_capital_usd']:,.2f}")
        print(f"   📈 Retorno absoluto: ${metrics['total_return_usd']:,.2f}")
        print(f"   📊 ROI: {metrics['roi_percent']:+.2f}%")
        
        # TRADES
        print(f"\n📊 ESTATÍSTICAS DE TRADES:")
        print(f"   🎯 Total de trades: {metrics['total_trades']}")
        print(f"   ✅ Trades vencedores: {metrics['winning_trades']} ({metrics['win_rate']:.1%})")
        print(f"   ❌ Trades perdedores: {metrics['losing_trades']}")
        print(f"   📈 Profit factor: {metrics['profit_factor']:.2f}")
        
        # P&L EM USD
        print(f"\n💵 P&L EM USD:")
        print(f"   💚 Lucro bruto: ${metrics['gross_profit_usd']:,.2f}")
        print(f"   💔 Perda bruta: ${metrics['gross_loss_usd']:,.2f}")
        print(f"   📊 Trade médio vencedor: ${metrics['avg_win_usd']:,.2f}")
        print(f"   📊 Trade médio perdedor: ${metrics['avg_loss_usd']:,.2f}")
        print(f"   🏆 Melhor trade: ${metrics['best_trade_usd']:,.2f}")
        print(f"   💥 Pior trade: ${metrics['worst_trade_usd']:,.2f}")
        
        # POSITION SIZING
        print(f"\n📏 POSITION SIZING:")
        print(f"   📊 Tamanho médio da posição: ${metrics['avg_position_size_usd']:,.2f}")
        print(f"   📊 Position size configurado: {metrics['position_size_percent']}%")
        print(f"   🔄 Compound interest: {'✅ Ativo' if metrics['compound_interest'] else '❌ Inativo'}")
        print(f"   ⚠️  Risco por trade: {metrics['risk_per_trade_percent']}%")
        
        # DRAWDOWN
        print(f"\n📉 DRAWDOWN:")
        print(f"   📉 Drawdown máximo: ${metrics['max_drawdown_usd']:,.2f} ({metrics['max_drawdown_percent']:.1f}%)")
        
        # DIREÇÕES
        print(f"\n🔄 ANÁLISE POR DIREÇÃO:")
        print(f"   📈 Trades long: {metrics['long_trades']} (win rate: {metrics['long_win_rate']:.1%})")
        print(f"   📉 Trades short: {metrics['short_trades']} (win rate: {metrics['short_win_rate']:.1%})")
        
        # PERFORMANCE
        print(f"\n⚡ PERFORMANCE:")
        print(f"   📊 Dados processados: {result['data_points']} candles")
        print(f"   🎯 Sinais gerados: {result['total_signals']}")
        print(f"   ⏱️  Tempo total: {result['execution_time']['total']:.2f}s")
        
        # EVOLUÇÃO DO CAPITAL (últimos 10 pontos)
        if 'capital_evolution' in metrics and len(metrics['capital_evolution']) > 1:
            print(f"\n📈 EVOLUÇÃO DO CAPITAL (últimos 10 pontos):")
            evolution = metrics['capital_evolution'][-10:]
            for timestamp, capital in evolution:
                date_str = timestamp[:10]  # YYYY-MM-DD
                print(f"   {date_str}: ${capital:,.2f}")
        
        print(f"\n" + "="*70)
        
        # Análise de performance
        if metrics['roi_percent'] > 0:
            print(f"🎉 RESULTADO POSITIVO: +{metrics['roi_percent']:.2f}% de retorno!")
        else:
            print(f"⚠️  RESULTADO NEGATIVO: {metrics['roi_percent']:.2f}% de retorno")
        
        if metrics['win_rate'] > 0.5:
            print(f"✅ Win rate acima de 50%: {metrics['win_rate']:.1%}")
        else:
            print(f"⚠️  Win rate abaixo de 50%: {metrics['win_rate']:.1%}")
        
        if metrics['profit_factor'] > 1.0:
            print(f"✅ Profit factor positivo: {metrics['profit_factor']:.2f}")
        else:
            print(f"❌ Profit factor negativo: {metrics['profit_factor']:.2f}")
    
    def _save_capital_report(self, result: Dict, filename_prefix: str):
        """Salva relatório detalhado com informações de capital"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{filename_prefix}_{result['symbol']}_{result['strategy']}_{timestamp}.json"
            
            os.makedirs('reports', exist_ok=True)
            filepath = f"reports/{filename}"
            
            with open(filepath, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            print(f"\n💾 Relatório salvo: {filepath}")
            
        except Exception as e:
            print(f"⚠️  Erro ao salvar relatório: {e}")
    
    def run(self):
        """Executa o CLI principal"""
        self.display_header()
        
        while True:
            self.display_menu()
            
            try:
                choice = input("🔢 Escolha uma opção: ").strip()
                
                if choice == '0':
                    print("\n👋 Obrigado por usar o Backtest CLI Enhanced!")
                    break
                
                elif choice == '1':
                    self.configure_capital()
                
                elif choice == '2':
                    self.run_quick_backtest_with_capital()
                
                elif choice == '3':
                    print("\n🚧 Backtesting personalizado em desenvolvimento...")
                    print("Use a opção 2 para teste rápido com capital.")
                
                elif choice == '4':
                    print("\n🚧 Análise de períodos históricos em desenvolvimento...")
                
                elif choice == '5':
                    self._display_strategy_info()
                
                elif choice == '6':
                    self.backtest_engine.api_client.test_connection()
                
                elif choice == '7':
                    self.view_capital_config()
                
                else:
                    print("❌ Opção inválida. Tente novamente.")
                
            except KeyboardInterrupt:
                print("\n\n👋 Saindo...")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")
    
    def _display_strategy_info(self):
        """Exibe informações das estratégias"""
        print("\n🧠 INFORMAÇÕES DAS ESTRATÉGIAS")
        print("="*50)
        
        for strategy_key, config in self.backtest_engine.strategy_engine.strategy_configs.items():
            print(f"\n📊 {config['name']}")
            print(f"   📝 {config['description']}")
            print(f"   ⚠️ Nível de risco: {config['risk_level']}")
            print(f"   📊 Melhores timeframes: {', '.join(config['best_timeframes'])}")
            print(f"   🎯 Condições ideais: {config['market_conditions']}")
            print(f"   ⚙️ Parâmetros: {config['params']}")
        
        input(f"\n📱 Pressione Enter para continuar...")

if __name__ == "__main__":
    try:
        cli = BacktestCLIEnhanced()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)

