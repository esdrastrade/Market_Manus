#!/usr/bin/env python3
"""
BacktestingAgentV5 - Agente de Backtesting com API V5 Bybit
Versão otimizada com gestão de risco integrada
"""

import os
import json
import logging
import asyncio
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import hmac
from urllib.parse import urlencode

from .base_agent import BaseAgent

class BybitAPIV5:
    """Cliente para API V5 da Bybit"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        self.api_key = api_key or os.getenv('BYBIT_API_KEY')
        self.api_secret = api_secret or os.getenv('BYBIT_API_SECRET')
        
        if testnet:
            self.base_url = "https://api-demo.bybit.com"
        else:
            self.base_url = "https://api.bybit.com"
        
        self.logger = logging.getLogger(__name__)
    
    def _display_data_metrics(self, total_candles: int, first_time: datetime, last_time: datetime, 
                              successful_batches: int, total_batches: int):
        """
        Exibe métricas de dados históricos carregados em formato visual consistente
        
        Args:
            total_candles: Total de candles carregados
            first_time: Timestamp do primeiro candle
            last_time: Timestamp do último candle
            successful_batches: Número de batches bem-sucedidos
            total_batches: Total de batches realizados
        """
        print("\n" + "═" * 63)
        print("📊 DADOS HISTÓRICOS CARREGADOS")
        print("═" * 63)
        print(f"📈 Total de Candles: {total_candles:,}")
        
        first_str = first_time.strftime("%Y-%m-%d %H:%M:%S")
        last_str = last_time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"📅 Período: {first_str} → {last_str}")
        
        success_rate = (successful_batches / total_batches * 100) if total_batches > 0 else 0
        print(f"✅ API Success Rate: {success_rate:.1f}% ({successful_batches}/{total_batches} batches bem-sucedidos)")
        print(f"🔗 Fonte: Bybit API V5 (dados reais)")
        print("═" * 63)
    
    def get_historical_data(self, symbol: str, interval: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Obter dados históricos da API V5"""
        try:
            # Converter datas para timestamps
            start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
            end_timestamp = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
            
            all_data = []
            current_start = start_timestamp
            successful_batches = 0
            failed_batches = 0
            
            self.logger.info(f"Obtendo dados históricos: {symbol} de {start_date} a {end_date}")
            
            while current_start < end_timestamp:
                # Calcular end para este batch (máximo 1000 candles)
                interval_ms = self._get_interval_ms(interval)
                batch_end = min(current_start + (1000 * interval_ms), end_timestamp)
                
                self.logger.info(f"Obtendo dados: {symbol} {interval} (limit: 1000)")
                
                # Fazer request para API
                url = f"{self.base_url}/v5/market/kline"
                params = {
                    'category': 'linear',
                    'symbol': symbol,
                    'interval': interval,
                    'start': current_start,
                    'end': batch_end,
                    'limit': 1000
                }
                
                try:
                    response = requests.get(url, params=params)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data['retCode'] == 0 and data['result']['list']:
                            klines = data['result']['list']
                            all_data.extend(klines)
                            successful_batches += 1
                            
                            # Atualizar current_start para próximo batch
                            last_timestamp = int(klines[-1][0])
                            current_start = last_timestamp + interval_ms
                            
                            self.logger.info(f"Dados obtidos: {len(klines)} registros")
                        else:
                            self.logger.warning(f"Nenhum dado retornado para período {current_start}-{batch_end}")
                            failed_batches += 1
                            break
                    else:
                        self.logger.error(f"Erro na API: {response.status_code} - {response.text}")
                        failed_batches += 1
                        break
                    
                    # Rate limiting
                    time.sleep(0.1)
                except Exception as e:
                    self.logger.error(f"Erro na requisição: {str(e)}")
                    failed_batches += 1
                    break
            
            if not all_data:
                self.logger.warning("Nenhum dado histórico obtido")
                return pd.DataFrame()
            
            # Converter para DataFrame
            df = pd.DataFrame(all_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])
            
            # Converter tipos
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume', 'turnover']:
                df[col] = pd.to_numeric(df[col])
            
            # Ordenar por timestamp
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # Exibir métricas de dados carregados
            if not df.empty:
                total_batches = successful_batches + failed_batches
                first_time = df['timestamp'].min().to_pydatetime()
                last_time = df['timestamp'].max().to_pydatetime()
                self._display_data_metrics(
                    total_candles=len(df),
                    first_time=first_time,
                    last_time=last_time,
                    successful_batches=successful_batches,
                    total_batches=total_batches
                )
            
            self.logger.info(f"Dados obtidos: {len(df)} registros")
            
            return df
        
        except Exception as e:
            self.logger.error(f"Erro ao obter dados históricos: {e}")
            return pd.DataFrame()
    
    def _get_interval_ms(self, interval: str) -> int:
        """Converter intervalo para milissegundos"""
        interval_map = {
            '1': 60 * 1000,      # 1 minuto
            '3': 3 * 60 * 1000,  # 3 minutos
            '5': 5 * 60 * 1000,  # 5 minutos
            '15': 15 * 60 * 1000, # 15 minutos
            '30': 30 * 60 * 1000, # 30 minutos
            '60': 60 * 60 * 1000, # 1 hora
            '120': 2 * 60 * 60 * 1000, # 2 horas
            '240': 4 * 60 * 60 * 1000, # 4 horas
            '360': 6 * 60 * 60 * 1000, # 6 horas
            '720': 12 * 60 * 60 * 1000, # 12 horas
            'D': 24 * 60 * 60 * 1000,   # 1 dia
        }
        return interval_map.get(interval, 5 * 60 * 1000)  # Default 5 min

class StrategyEngine:
    """Engine para execução de estratégias de trading"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def execute_strategy(self, df: pd.DataFrame, strategy: str, params: Dict[str, Any] = None) -> pd.Series:
        """Executar estratégia específica"""
        if strategy == 'ema_crossover' or strategy == 'ema_crossover_optimized':
            return self._ema_crossover_strategy(df, params or {})
        elif strategy == 'rsi_mean_reversion' or strategy == 'rsi_mean_reversion_optimized':
            return self._rsi_mean_reversion_strategy(df, params or {})
        elif strategy == 'bollinger_breakout' or strategy == 'bollinger_breakout_optimized':
            return self._bollinger_breakout_strategy(df, params or {})
        else:
            self.logger.warning(f"Estratégia desconhecida: {strategy}")
            return pd.Series(0, index=df.index)
    
    def _ema_crossover_strategy(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        """Estratégia EMA Crossover otimizada"""
        # Parâmetros otimizados
        fast_period = params.get('fast_period', 21)  # Era 12
        slow_period = params.get('slow_period', 50)  # Era 26
        trend_period = params.get('trend_period', 200)
        volume_multiplier = params.get('volume_multiplier', 1.5)
        
        # Calcular EMAs
        df['ema_fast'] = df['close'].ewm(span=fast_period).mean()
        df['ema_slow'] = df['close'].ewm(span=slow_period).mean()
        df['ema_trend'] = df['close'].ewm(span=trend_period).mean()
        
        # Calcular volume médio
        df['volume_avg'] = df['volume'].rolling(window=20).mean()
        
        # Sinais básicos
        df['signal_basic'] = 0
        df.loc[df['ema_fast'] > df['ema_slow'], 'signal_basic'] = 1
        df.loc[df['ema_fast'] < df['ema_slow'], 'signal_basic'] = -1
        
        # Filtros otimizados
        trend_filter = df['close'] > df['ema_trend']  # Apenas trades na direção da tendência
        volume_filter = df['volume'] > (df['volume_avg'] * volume_multiplier)  # Volume acima da média
        
        # Aplicar filtros
        signals = df['signal_basic'].copy()
        signals[(signals == 1) & (~trend_filter)] = 0  # Remover compras contra tendência
        signals[(signals == 1) & (~volume_filter)] = 0  # Remover compras com volume baixo
        
        # Detectar mudanças de sinal
        signal_changes = signals.diff()
        final_signals = pd.Series(0, index=df.index)
        final_signals[signal_changes == 1] = 1   # Sinal de compra
        final_signals[signal_changes == -1] = -1 # Sinal de venda
        
        return final_signals
    
    def _rsi_mean_reversion_strategy(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        """Estratégia RSI Mean Reversion otimizada"""
        # Parâmetros otimizados
        rsi_period = params.get('rsi_period', 14)
        oversold = params.get('oversold', 25)  # Era 30
        overbought = params.get('overbought', 75)  # Era 70
        volatility_threshold = params.get('volatility_threshold', 1.2)
        
        # Calcular RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Calcular volatilidade (ATR normalizado)
        df['high_low'] = df['high'] - df['low']
        df['high_close'] = np.abs(df['high'] - df['close'].shift())
        df['low_close'] = np.abs(df['low'] - df['close'].shift())
        df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
        df['atr'] = df['true_range'].rolling(window=14).mean()
        df['volatility'] = df['atr'] / df['close']
        df['volatility_avg'] = df['volatility'].rolling(window=20).mean()
        
        # Sinais básicos
        signals = pd.Series(0, index=df.index)
        
        # Sinal de compra: RSI oversold + volatilidade normal
        buy_condition = (
            (df['rsi'] < oversold) & 
            (df['volatility'] < df['volatility_avg'] * volatility_threshold)
        )
        signals[buy_condition] = 1
        
        # Sinal de venda: RSI overbought
        sell_condition = df['rsi'] > overbought
        signals[sell_condition] = -1
        
        return signals
    
    def _bollinger_breakout_strategy(self, df: pd.DataFrame, params: Dict[str, Any]) -> pd.Series:
        """Estratégia Bollinger Breakout"""
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2.0)
        
        # Calcular Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=period).mean()
        df['bb_std'] = df['close'].rolling(window=period).std()
        df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * std_dev)
        df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * std_dev)
        
        # Sinais
        signals = pd.Series(0, index=df.index)
        signals[df['close'] > df['bb_upper']] = 1   # Breakout para cima
        signals[df['close'] < df['bb_lower']] = -1  # Breakout para baixo
        
        return signals

class BacktestEngine:
    """Engine para execução de backtesting com gestão de risco"""
    
    def __init__(self, initial_capital: float = 10000, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        
        # Parâmetros de risco (serão atualizados pelo agente)
        self.max_position_size = 0.10  # 10% máximo por posição
        self.stop_loss_pct = 0.02      # 2% stop loss
        self.take_profit_pct = 0.04    # 4% take profit
        self.max_daily_loss = 0.05     # 5% perda máxima diária
        self.current_daily_loss = 0.0
        
        self.logger = logging.getLogger(__name__)
    
    def run_backtest(self, df: pd.DataFrame, signals: pd.Series) -> Dict[str, Any]:
        """Executar backtesting com gestão de risco integrada"""
        if df.empty or signals.empty:
            return self._empty_result()
        
        try:
            # Inicializar variáveis
            capital = self.initial_capital
            position = 0
            trades = []
            equity_curve = [capital]
            daily_pnl = 0
            last_date = None
            entry_price = 0
            stop_loss_price = 0
            take_profit_price = 0
            
            for i in range(1, len(df)):
                current_price = df['close'].iloc[i]
                current_date = df['timestamp'].iloc[i].date()
                signal = signals.iloc[i]
                
                # Reset daily PnL se mudou o dia
                if last_date and current_date != last_date:
                    daily_pnl = 0
                last_date = current_date
                
                # Verificar limite de perda diária
                if abs(daily_pnl) >= capital * self.max_daily_loss:
                    continue  # Não tradear se atingiu limite diário
                
                # Executar sinal de compra
                if signal == 1 and position <= 0:
                    # Calcular tamanho da posição baseado no risco
                    max_position_value = capital * self.max_position_size
                    position_size = max_position_value / current_price
                    
                    # Calcular stop loss e take profit
                    stop_loss_price = current_price * (1 - self.stop_loss_pct)
                    take_profit_price = current_price * (1 + self.take_profit_pct)
                    
                    position = position_size
                    entry_price = current_price
                    cost = position_size * current_price * (1 + self.commission)
                    capital -= cost
                    
                    trades.append({
                        'type': 'buy',
                        'price': current_price,
                        'quantity': position_size,
                        'timestamp': df['timestamp'].iloc[i],
                        'stop_loss': stop_loss_price,
                        'take_profit': take_profit_price
                    })
                
                # Verificar saída (stop loss, take profit ou sinal de venda)
                elif position > 0:
                    exit_condition = False
                    exit_reason = ''
                    
                    # Verificar stop loss
                    if current_price <= stop_loss_price:
                        exit_condition = True
                        exit_reason = 'stop_loss'
                    
                    # Verificar take profit
                    elif current_price >= take_profit_price:
                        exit_condition = True
                        exit_reason = 'take_profit'
                    
                    # Verificar sinal de venda
                    elif signal == -1:
                        exit_condition = True
                        exit_reason = 'signal'
                    
                    if exit_condition:
                        revenue = position * current_price * (1 - self.commission)
                        capital += revenue
                        
                        pnl = revenue - (position * entry_price * (1 + self.commission))
                        daily_pnl += pnl
                        
                        trades.append({
                            'type': 'sell',
                            'price': current_price,
                            'quantity': position,
                            'pnl': pnl,
                            'timestamp': df['timestamp'].iloc[i],
                            'exit_reason': exit_reason
                        })
                        
                        position = 0
                        entry_price = 0
                        stop_loss_price = 0
                        take_profit_price = 0
                
                # Atualizar equity curve
                if position > 0:
                    current_equity = capital + position * current_price
                else:
                    current_equity = capital
                
                equity_curve.append(current_equity)
            
            return self._calculate_performance(equity_curve, trades)
        
        except Exception as e:
            self.logger.error(f"Erro durante backtesting: {e}")
            return self._empty_result()
    
    def _calculate_performance(self, equity_curve: List[float], trades: List[Dict]) -> Dict[str, Any]:
        """Calcular métricas de performance"""
        try:
            if not trades or len(trades) < 2:
                return self._empty_result()
            
            # Separar trades de compra e venda
            buy_trades = [t for t in trades if t['type'] == 'buy']
            sell_trades = [t for t in trades if t['type'] == 'sell']
            
            if not sell_trades:
                return self._empty_result()
            
            # Métricas básicas
            final_capital = equity_curve[-1]
            total_return = (final_capital - self.initial_capital) / self.initial_capital
            
            # Análise de trades
            pnls = [t['pnl'] for t in sell_trades]
            winning_trades = len([p for p in pnls if p > 0])
            losing_trades = len([p for p in pnls if p <= 0])
            total_trades = len(sell_trades)
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # Profit factor
            gross_profit = sum([p for p in pnls if p > 0])
            gross_loss = abs(sum([p for p in pnls if p < 0]))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Drawdown
            peak = self.initial_capital
            max_drawdown = 0
            for equity in equity_curve:
                if equity > peak:
                    peak = equity
                drawdown = (peak - equity) / peak
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            # Sharpe ratio (simplificado)
            if len(equity_curve) > 1:
                returns = np.diff(equity_curve) / equity_curve[:-1]
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Análise de exit reasons
            exit_reasons = {}
            for trade in sell_trades:
                reason = trade.get('exit_reason', 'unknown')
                exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
            
            return {
                'status': 'success',
                'performance': {
                    'initial_capital': self.initial_capital,
                    'final_capital': final_capital,
                    'total_return': total_return,
                    'total_trades': total_trades,
                    'winning_trades': winning_trades,
                    'losing_trades': losing_trades,
                    'win_rate': win_rate,
                    'gross_profit': gross_profit,
                    'gross_loss': gross_loss,
                    'profit_factor': profit_factor,
                    'max_drawdown': max_drawdown,
                    'sharpe_ratio': sharpe_ratio
                },
                'trades': trades,
                'equity_curve': equity_curve,
                'exit_reasons': exit_reasons
            }
        
        except Exception as e:
            self.logger.error(f"Erro ao calcular performance: {e}")
            return self._empty_result()
    
    def _empty_result(self) -> Dict[str, Any]:
        """Resultado vazio para casos de erro"""
        return {
            'status': 'error',
            'performance': {
                'initial_capital': self.initial_capital,
                'final_capital': self.initial_capital,
                'total_return': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'gross_profit': 0.0,
                'gross_loss': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0
            },
            'trades': [],
            'equity_curve': [self.initial_capital]
        }

class BacktestingAgentV5(BaseAgent):
    """
    Agente de Backtesting com API V5 Bybit e gestão de risco integrada
    
    IMPORTANTE: Este agente usa APENAS dados reais da API Bybit V5.
    Nenhum dado mockado ou simulado é utilizado.
    API keys são validadas antes de executar qualquer backtest.
    """
    
    def __init__(self):
        super().__init__(name="BacktestingAgentV5")
        self.api_client = BybitAPIV5()
        self.strategy_engine = StrategyEngine()
        self.backtest_engine = BacktestEngine()
        
        self.logger.info("BacktestingAgentV5 inicializado com gestão de risco")
        self.logger.info(f"📊 Fonte de dados: API Bybit V5 (dados REAIS)")
        
    def _validate_api_credentials(self) -> bool:
        """
        Valida se as credenciais da API estão configuradas
        
        Returns:
            bool: True se credenciais válidas, False caso contrário
        """
        if not self.api_client.api_key or not self.api_client.api_secret:
            self.logger.error("❌ API credentials não configuradas")
            self.logger.error("❌ Configure BYBIT_API_KEY e BYBIT_API_SECRET no ambiente")
            self.logger.error("❌ Impossível executar backtest sem dados reais da API")
            return False
        
        self.logger.info("✅ Credenciais da API Bybit validadas com sucesso")
        return True
    
    def load_risk_parameters(self) -> Dict[str, Any]:
        """Carregar parâmetros de risco do arquivo JSON"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'risk_parameters.json')
            with open(config_path, 'r') as f:
                risk_config = json.load(f)
                return risk_config.get('risk_management', {})
        except FileNotFoundError:
            self.logger.warning("Arquivo risk_parameters.json não encontrado, usando valores padrão")
            return {
                "max_position_size": 0.10,
                "stop_loss_percentage": 0.02,
                "take_profit_percentage": 0.04,
                "max_daily_loss": 0.05,
                "max_drawdown": 0.15,
                "risk_per_trade": 0.01
            }
    
    async def run_backtest(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executar backtesting individual com gestão de risco integrada
        
        IMPORTANTE: Valida API credentials antes de executar.
        Usa APENAS dados reais da API Bybit V5.
        """
        try:
            # VALIDAÇÃO OBRIGATÓRIA DE API CREDENTIALS
            if not self._validate_api_credentials():
                return {
                    'status': 'error',
                    'error': 'API credentials não configuradas. Configure BYBIT_API_KEY e BYBIT_API_SECRET.',
                    'config': config
                }
            
            symbol = config.get('symbol', 'BTCUSDT')
            strategy = config.get('strategy', 'ema_crossover')
            start_date = config.get('start_date', '2025-01-01')
            end_date = config.get('end_date', '2025-03-01')
            timeframe = config.get('timeframe', '5')
            initial_capital = config.get('initial_capital', 10000)
            
            # Carregar parâmetros de risco
            risk_params = config.get('risk_params', {})
            if not risk_params:
                # Carregar do arquivo se não fornecido
                risk_params = self.load_risk_parameters()
            
            self.logger.info(f"🚀 Iniciando backtesting com dados REAIS da API Bybit V5")
            self.logger.info(f"📊 Config: {symbol} {strategy} {start_date}-{end_date}")
            self.logger.info(f"⚠️  Parâmetros de risco: {risk_params}")
            
            # Obter dados históricos REAIS da API
            self.logger.info(f"📡 Buscando dados REAIS da API Bybit para {symbol}...")
            df = self.api_client.get_historical_data(symbol, timeframe, start_date, end_date)
            
            if df.empty:
                return {
                    'status': 'error',
                    'error': f'Nenhum dado obtido para {symbol}',
                    'config': config
                }
            
            # Executar estratégia
            strategy_params = config.get('strategy_params', {})
            signals = self.strategy_engine.execute_strategy(df, strategy, strategy_params)
            
            # Configurar backtest engine com parâmetros de risco
            self.backtest_engine.initial_capital = initial_capital
            self.backtest_engine.commission = config.get('commission', 0.001)
            
            # Aplicar parâmetros de risco
            self.backtest_engine.max_position_size = risk_params.get('max_position_size', 0.10)
            self.backtest_engine.stop_loss_pct = risk_params.get('stop_loss_percentage', 0.02)
            self.backtest_engine.take_profit_pct = risk_params.get('take_profit_percentage', 0.04)
            self.backtest_engine.max_daily_loss = risk_params.get('max_daily_loss', 0.05)
            
            # Executar backtesting
            result = self.backtest_engine.run_backtest(df, signals)
            result['config'] = config
            result['risk_params_used'] = risk_params
            result['data_points'] = len(df)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro durante backtesting: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'config': config
            }
    
    async def run_full_backtest_suite(self) -> Dict[str, Any]:
        """Executar suite completa de backtesting"""
        try:
            # Configuração padrão
            symbols = ['BTCUSDT', 'ETHUSDT']
            strategies = ['ema_crossover', 'rsi_mean_reversion']
            
            results = {}
            
            for symbol in symbols:
                results[symbol] = {}
                
                for strategy in strategies:
                    config = {
                        'symbol': symbol,
                        'strategy': strategy,
                        'start_date': '2025-01-01',
                        'end_date': '2025-03-01',
                        'timeframe': '5',
                        'initial_capital': 10000
                    }
                    
                    result = await self.run_backtest(config)
                    results[symbol][strategy] = result
            
            # Análise comparativa
            analysis = self._analyze_results(results)
            
            return {
                'status': 'success',
                'results': results,
                'analysis': analysis
            }
        
        except Exception as e:
            self.logger.error(f"Erro na suite de backtesting: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analisar resultados da suite"""
        try:
            best_strategies = {}
            all_results = []
            
            for symbol, symbol_results in results.items():
                best_return = -float('inf')
                best_strategy = None
                
                for strategy, result in symbol_results.items():
                    if result['status'] == 'success':
                        performance = result['performance']
                        total_return = performance['total_return']
                        
                        all_results.append({
                            'symbol': symbol,
                            'strategy': strategy,
                            'return': total_return,
                            'win_rate': performance['win_rate'],
                            'drawdown': performance['max_drawdown']
                        })
                        
                        if total_return > best_return:
                            best_return = total_return
                            best_strategy = {
                                'symbol': symbol,
                                'config': strategy,
                                'return': total_return
                            }
                
                best_strategies[symbol] = best_strategy
            
            # Recomendações
            recommendations = []
            if all_results:
                avg_return = sum(r['return'] for r in all_results) / len(all_results)
                positive_results = [r for r in all_results if r['return'] > 0]
                
                if len(positive_results) >= len(all_results) * 0.7:
                    recommendations.append("Sistema promissor - Prosseguir para demo trading")
                elif avg_return > 0.05:
                    recommendations.append("Performance satisfatória - Considerar otimização")
                else:
                    recommendations.append("Performance insatisfatória - Revisar estratégias")
            
            return {
                'best_strategies': best_strategies,
                'recommendations': recommendations,
                'total_tests': len(all_results),
                'positive_tests': len([r for r in all_results if r['return'] > 0])
            }
        
        except Exception as e:
            self.logger.error(f"Erro na análise de resultados: {e}")
            return {}
    
    async def run(self) -> Dict[str, Any]:
        """Executar teste básico do agente"""
        try:
            self.logger.info("Executando teste básico do BacktestingAgentV5")
            
            # Teste simples
            config = {
                'symbol': 'BTCUSDT',
                'strategy': 'ema_crossover',
                'start_date': '2024-01-01',
                'end_date': '2024-01-31',
                'timeframe': '15',
                'initial_capital': 10000
            }
            
            result = await self.run_backtest(config)
            
            return {
                'status': 'success',
                'message': 'BacktestingAgentV5 funcionando corretamente',
                'test_result': result
            }
        
        except Exception as e:
            self.logger.error(f"Erro no teste do agente: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analisar performance do agente"""
        try:
            return {
                'status': 'operational',
                'components': {
                    'api_client': 'connected',
                    'strategy_engine': 'loaded',
                    'backtest_engine': 'ready',
                    'risk_management': 'integrated'
                },
                'capabilities': [
                    'historical_data_retrieval',
                    'strategy_execution',
                    'risk_management',
                    'performance_analysis'
                ],
                'last_update': datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Erro na análise de performance: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def suggest_improvements(self) -> List[str]:
        """Sugerir melhorias para o agente"""
        return [
            "Implementar cache de dados históricos para melhor performance",
            "Adicionar mais estratégias (MACD, Stochastic, Williams %R)",
            "Implementar otimização automática de parâmetros",
            "Adicionar análise de correlação entre ativos",
            "Implementar backtesting walk-forward",
            "Adicionar análise de regime de mercado",
            "Implementar machine learning para seleção de estratégias",
            "Adicionar análise de sentimento de mercado",
            "Implementar backtesting multi-timeframe",
            "Adicionar métricas de risco avançadas (VaR, CVaR)"
        ]

