#!/usr/bin/env python3
"""
BacktestingAgent V5 - Corrigido
Sistema de backtesting com API V5 da Bybit

Funcionalidades:
- Integração com API V5 da Bybit
- Dados históricos reais
- Múltiplas estratégias de trading
- Análise de performance detalhada
- Relatórios automáticos
"""

import os
import sys
import json
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import requests
import time
import hashlib
import hmac
from urllib.parse import urlencode

# Adicionar diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from agents.base_agent import BaseAgent
except ImportError:
    # Fallback se base_agent não estiver disponível
    class BaseAgent:
        def __init__(self):
            self.logger = logging.getLogger(__name__)
            self.config = {}
            self.metrics = {}
            self.suggestions = []

class BybitAPIV5:
    """Cliente para API V5 da Bybit"""
    
    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = False):
        self.api_key = api_key or os.getenv('BYBIT_API_KEY')
        self.api_secret = api_secret or os.getenv('BYBIT_API_SECRET')
        self.testnet = testnet
        
        if testnet:
            self.base_url = "https://api-testnet.bybit.com"
        else:
            self.base_url = "https://api.bybit.com"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'ScalpingBot/1.0'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms entre requests
        
        self.logger = logging.getLogger(__name__)
    
    def _generate_signature(self, params: str, timestamp: str) -> str:
        """Gerar assinatura para autenticação"""
        if not self.api_secret:
            return ""
        
        param_str = f"{timestamp}{self.api_key}5000{params}"
        return hmac.new(
            self.api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        """Fazer requisição para API"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=30)
            else:
                response = self.session.post(url, json=params, timeout=30)
            
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data.get('retCode') == 0:
                    return data
                else:
                    self.logger.error(f"API Error: {data.get('retMsg', 'Unknown error')}")
                    return {'error': data.get('retMsg', 'Unknown error')}
            else:
                self.logger.error(f"HTTP Error: {response.status_code}")
                return {'error': f'HTTP {response.status_code}'}
        
        except Exception as e:
            self.logger.error(f"Request error: {e}")
            return {'error': str(e)}
    
    def get_kline_data(self, symbol: str, interval: str, start_time: int = None, 
                      end_time: int = None, limit: int = 1000) -> pd.DataFrame:
        """
        Obter dados de candlestick (kline) da API V5
        
        Args:
            symbol: Símbolo do ativo (ex: BTCUSDT)
            interval: Timeframe (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)
            start_time: Timestamp de início (ms)
            end_time: Timestamp de fim (ms)
            limit: Número máximo de registros (max 1000)
        
        Returns:
            DataFrame com dados OHLCV
        """
        
        params = {
            'category': 'linear',  # Para futuros USDT
            'symbol': symbol,
            'interval': interval,
            'limit': min(limit, 1000)
        }
        
        if start_time:
            params['start'] = start_time
        if end_time:
            params['end'] = end_time
        
        self.logger.info(f"Obtendo dados: {symbol} {interval} (limit: {limit})")
        
        response = self._make_request('GET', '/v5/market/kline', params)
        
        if 'error' in response:
            self.logger.error(f"Erro ao obter dados: {response['error']}")
            return pd.DataFrame()
        
        try:
            klines = response.get('result', {}).get('list', [])
            
            if not klines:
                self.logger.warning(f"Nenhum dado retornado para {symbol}")
                return pd.DataFrame()
            
            # Converter para DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
            ])
            
            # Converter tipos de dados
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'turnover']
            df[numeric_columns] = df[numeric_columns].astype(float)
            
            # Ordenar por timestamp (mais antigo primeiro)
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            self.logger.info(f"Dados obtidos: {len(df)} registros de {df['timestamp'].min()} a {df['timestamp'].max()}")
        
            return df.reset_index(drop=True)
        
        except Exception as e:
            self.logger.error(f"Erro ao processar dados: {e}")
            return pd.DataFrame()
    
    def get_historical_data(self, symbol: str, interval: str, 
                           start_date: str, end_date: str) -> pd.DataFrame:
        """
        Obter dados históricos para um período específico
        
        Args:
            symbol: Símbolo do ativo
            interval: Timeframe
            start_date: Data de início (YYYY-MM-DD)
            end_date: Data de fim (YYYY-MM-DD)
        
        Returns:
            DataFrame com dados históricos completos
        """
        
        # Converter datas para timestamps
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        start_timestamp = int(start_dt.timestamp() * 1000)
        end_timestamp = int(end_dt.timestamp() * 1000)
        
        all_data = []
        current_start = start_timestamp
        
        self.logger.info(f"Obtendo dados históricos: {symbol} de {start_date} a {end_date}")
        
        while current_start < end_timestamp:
            # Calcular fim do chunk (máximo 1000 registros por request)
            chunk_end = min(current_start + (1000 * self._get_interval_ms(interval)), end_timestamp)
            
            df_chunk = self.get_kline_data(
                symbol=symbol,
                interval=interval,
                start_time=current_start,
                end_time=chunk_end,
                limit=1000
            )
            
            if df_chunk.empty:
                break
            
            all_data.append(df_chunk)
            
            # Próximo chunk começa após o último timestamp
            if len(df_chunk) > 0:
                last_timestamp = int(df_chunk['timestamp'].iloc[-1].timestamp() * 1000)
                current_start = last_timestamp + self._get_interval_ms(interval)
            else:
                break
            
            # Rate limiting
            time.sleep(0.1)
        
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            final_df = final_df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
            
            self.logger.info(f"Total de dados obtidos: {len(final_df)} registros")
            return final_df.reset_index(drop=True)
        else:
            self.logger.warning("Nenhum dado histórico obtido")
            return pd.DataFrame()
    
    def _get_interval_ms(self, interval: str) -> int:
        """Converter intervalo para milissegundos"""
        interval_map = {
            '1': 60 * 1000,           # 1 minuto
            '3': 3 * 60 * 1000,       # 3 minutos
            '5': 5 * 60 * 1000,       # 5 minutos
            '15': 15 * 60 * 1000,     # 15 minutos
            '30': 30 * 60 * 1000,     # 30 minutos
            '60': 60 * 60 * 1000,     # 1 hora
            '120': 2 * 60 * 60 * 1000, # 2 horas
            '240': 4 * 60 * 60 * 1000, # 4 horas
            '360': 6 * 60 * 60 * 1000, # 6 horas
            '720': 12 * 60 * 60 * 1000, # 12 horas
            'D': 24 * 60 * 60 * 1000,  # 1 dia
            'W': 7 * 24 * 60 * 60 * 1000, # 1 semana
            'M': 30 * 24 * 60 * 60 * 1000  # 1 mês (aproximado)
        }
        return interval_map.get(interval, 5 * 60 * 1000)  # Default: 5 minutos

class StrategyEngine:
    """Engine para execução de estratégias de trading"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcular indicadores técnicos"""
        if df.empty:
            return df
        
        try:
            # EMA
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            # ATR para stop loss
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            df['atr'] = true_range.rolling(window=14).mean()
            
            return df
        
        except Exception as e:
            self.logger.error(f"Erro ao calcular indicadores: {e}")
            return df
    
    def ema_crossover_strategy(self, df: pd.DataFrame) -> pd.Series:
        """Estratégia EMA Crossover"""
        if df.empty or 'ema_12' not in df.columns:
            return pd.Series(dtype=float)
        
        signals = pd.Series(0, index=df.index)
        
        # Sinal de compra: EMA 12 cruza acima da EMA 26
        buy_condition = (df['ema_12'] > df['ema_26']) & (df['ema_12'].shift(1) <= df['ema_26'].shift(1))
        
        # Sinal de venda: EMA 12 cruza abaixo da EMA 26
        sell_condition = (df['ema_12'] < df['ema_26']) & (df['ema_12'].shift(1) >= df['ema_26'].shift(1))
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def rsi_mean_reversion_strategy(self, df: pd.DataFrame) -> pd.Series:
        """Estratégia RSI Mean Reversion"""
        if df.empty or 'rsi' not in df.columns:
            return pd.Series(dtype=float)
        
        signals = pd.Series(0, index=df.index)
        
        # Sinal de compra: RSI < 30 (oversold)
        buy_condition = (df['rsi'] < 30) & (df['rsi'].shift(1) >= 30)
        
        # Sinal de venda: RSI > 70 (overbought)
        sell_condition = (df['rsi'] > 70) & (df['rsi'].shift(1) <= 70)
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def bollinger_breakout_strategy(self, df: pd.DataFrame) -> pd.Series:
        """Estratégia Bollinger Bands Breakout"""
        if df.empty or 'bb_upper' not in df.columns:
            return pd.Series(dtype=float)
        
        signals = pd.Series(0, index=df.index)
        
        # Sinal de compra: preço rompe banda superior
        buy_condition = (df['close'] > df['bb_upper']) & (df['close'].shift(1) <= df['bb_upper'].shift(1))
        
        # Sinal de venda: preço rompe banda inferior
        sell_condition = (df['close'] < df['bb_lower']) & (df['close'].shift(1) >= df['bb_lower'].shift(1))
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def execute_strategy(self, df: pd.DataFrame, strategy_name: str) -> pd.Series:
        """Executar estratégia específica"""
        df_with_indicators = self.calculate_indicators(df)
        
        strategy_map = {
            'ema_crossover': self.ema_crossover_strategy,
            'rsi_mean_reversion': self.rsi_mean_reversion_strategy,
            'bollinger_breakout': self.bollinger_breakout_strategy
        }
        
        if strategy_name in strategy_map:
            return strategy_map[strategy_name](df_with_indicators)
        else:
            self.logger.error(f"Estratégia desconhecida: {strategy_name}")
            return pd.Series(0, index=df.index)

class BacktestEngine:
    """Engine para execução de backtesting"""
    
    def __init__(self, initial_capital: float = 10000, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.logger = logging.getLogger(__name__)
    
    def run_backtest(self, df: pd.DataFrame, signals: pd.Series) -> Dict[str, Any]:
        """Executar backtesting com sinais fornecidos"""
        if df.empty or signals.empty:
            return self._empty_result()
        
        try:
            # Inicializar variáveis
            capital = self.initial_capital
            position = 0
            trades = []
            equity_curve = [capital]
            
            for i in range(1, len(df)):
                current_price = df['close'].iloc[i]
                signal = signals.iloc[i]
                
                # Executar sinal
                if signal == 1 and position <= 0:  # Compra
                    if position < 0:  # Fechar posição short
                        pnl = position * (df['close'].iloc[i-1] - current_price)
                        capital += pnl - abs(position * current_price * self.commission)
                        trades.append({
                            'type': 'close_short',
                            'price': current_price,
                            'quantity': abs(position),
                            'pnl': pnl,
                            'timestamp': df['timestamp'].iloc[i]
                        })
                    
                    # Abrir posição long
                    position_size = capital * 0.95 / current_price  # 95% do capital
                    position = position_size
                    capital -= position_size * current_price * (1 + self.commission)
                    
                    trades.append({
                        'type': 'buy',
                        'price': current_price,
                        'quantity': position_size,
                        'timestamp': df['timestamp'].iloc[i]
                    })
                
                elif signal == -1 and position >= 0:  # Venda
                    if position > 0:  # Fechar posição long
                        pnl = position * (current_price - df['close'].iloc[i-1])
                        capital += position * current_price * (1 - self.commission)
                        trades.append({
                            'type': 'sell',
                            'price': current_price,
                            'quantity': position,
                            'pnl': pnl,
                            'timestamp': df['timestamp'].iloc[i]
                        })
                        position = 0
                
                # Calcular equity atual
                if position > 0:
                    current_equity = capital + position * current_price
                elif position < 0:
                    current_equity = capital + position * current_price
                else:
                    current_equity = capital
                
                equity_curve.append(current_equity)
            
            # Fechar posição final se necessário
            if position != 0:
                final_price = df['close'].iloc[-1]
                if position > 0:
                    capital += position * final_price * (1 - self.commission)
                    trades.append({
                        'type': 'final_sell',
                        'price': final_price,
                        'quantity': position,
                        'timestamp': df['timestamp'].iloc[-1]
                    })
                
                equity_curve[-1] = capital
            
            return self._calculate_performance(equity_curve, trades)
        
        except Exception as e:
            self.logger.error(f"Erro durante backtesting: {e}")
            return self._empty_result()
    
    def _calculate_performance(self, equity_curve: List[float], trades: List[Dict]) -> Dict[str, Any]:
        """Calcular métricas de performance"""
        if not equity_curve or len(equity_curve) < 2:
            return self._empty_result()
        
        try:
            # Métricas básicas
            final_capital = equity_curve[-1]
            total_return = (final_capital - self.initial_capital) / self.initial_capital
            
            # Trades
            winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
            losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
            total_trades = len([t for t in trades if 'pnl' in t])
            
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            
            # Drawdown
            peak = equity_curve[0]
            max_drawdown = 0
            for equity in equity_curve:
                if equity > peak:
                    peak = equity
                drawdown = (peak - equity) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            # Sharpe Ratio (simplificado)
            returns = np.diff(equity_curve) / equity_curve[:-1]
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
            
            # Profit Factor
            gross_profit = sum(t.get('pnl', 0) for t in winning_trades)
            gross_loss = abs(sum(t.get('pnl', 0) for t in losing_trades))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            return {
                'status': 'success',
                'performance': {
                    'initial_capital': self.initial_capital,
                    'final_capital': final_capital,
                    'total_return': total_return,
                    'total_trades': total_trades,
                    'winning_trades': len(winning_trades),
                    'losing_trades': len(losing_trades),
                    'win_rate': win_rate,
                    'max_drawdown': max_drawdown,
                    'sharpe_ratio': sharpe_ratio,
                    'profit_factor': profit_factor,
                    'gross_profit': gross_profit,
                    'gross_loss': gross_loss
                },
                'equity_curve': equity_curve,
                'trades': trades
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
                'max_drawdown': 0.0,
                'sharpe_ratio': 0.0,
                'profit_factor': 0.0,
                'gross_profit': 0.0,
                'gross_loss': 0.0
            },
            'equity_curve': [self.initial_capital],
            'trades': []
        }

class BacktestingAgentV5(BaseAgent):
    """Agent de backtesting com API V5 da Bybit"""
    
    def __init__(self):
        super().__init__()
        self.api_client = BybitAPIV5()
        self.strategy_engine = StrategyEngine()
        self.backtest_engine = BacktestEngine()
        
        # Configurações padrão
        self.default_config = {
            'symbols': ['BTCUSDT', 'ETHUSDT'],
            'strategies': ['ema_crossover', 'rsi_mean_reversion'],
            'timeframe': '5',
            'initial_capital': 10000,
            'commission': 0.001
        }
        
        self.logger.info("BacktestingAgentV5 inicializado com sucesso")
    
    async def run_backtest(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Executar backtesting individual"""
        try:
            symbol = config.get('symbol', 'BTCUSDT')
            strategy = config.get('strategy', 'ema_crossover')
            start_date = config.get('start_date', '2025-01-01')
            end_date = config.get('end_date', '2025-03-01')
            timeframe = config.get('timeframe', '5')
            initial_capital = config.get('initial_capital', 10000)
            
            self.logger.info(f"Iniciando backtesting: {symbol} {strategy} {start_date}-{end_date}")
            
            # Obter dados históricos
            df = self.api_client.get_historical_data(symbol, timeframe, start_date, end_date)
            
            if df.empty:
                return {
                    'status': 'error',
                    'error': f'Nenhum dado obtido para {symbol}',
                    'config': config
                }
            
            # Executar estratégia
            signals = self.strategy_engine.execute_strategy(df, strategy)
            
            # Configurar backtest engine
            self.backtest_engine.initial_capital = initial_capital
            self.backtest_engine.commission = config.get('commission', 0.001)
            
            # Executar backtesting
            result = self.backtest_engine.run_backtest(df, signals)
            result['config'] = config
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
            # Carregar configuração
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'backtesting_config.json')
            
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    full_config = json.load(f)
            else:
                full_config = self.default_config
            
            symbols = full_config.get('symbols', ['BTCUSDT', 'ETHUSDT'])
            strategies = full_config.get('strategies', ['ema_crossover', 'rsi_mean_reversion'])
            scenarios = full_config.get('test_scenarios', [
                {'name': 'bull_market', 'period': '2025-01-01_to_2025-03-01'},
                {'name': 'bear_market', 'period': '2025-03-01_to_2025-05-01'},
                {'name': 'sideways_market', 'period': '2025-05-01_to_2025-07-01'}
            ])
            
            all_results = {}
            
            for scenario in scenarios:
                scenario_name = scenario['name']
                period = scenario['period']
                start_date, end_date = period.split('_to_')
                
                self.logger.info(f"Executando cenário: {scenario_name}")
                scenario_results = {}
                
                for symbol in symbols:
                    symbol_results = {}
                    
                    for strategy in strategies:
                        config = {
                            'symbol': symbol,
                            'strategy': strategy,
                            'start_date': start_date,
                            'end_date': end_date,
                            'timeframe': full_config.get('timeframe', '5'),
                            'initial_capital': full_config.get('default_parameters', {}).get('initial_capital', 10000),
                            'commission': full_config.get('default_parameters', {}).get('commission', 0.001)
                        }
                        
                        result = await self.run_backtest(config)
                        symbol_results[strategy] = result
                    
                    scenario_results[symbol] = symbol_results
                
                all_results[scenario_name] = scenario_results
            
            # Análise dos resultados
            analysis = self._analyze_results(all_results)
            
            return {
                'status': 'success',
                'results': all_results,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            self.logger.error(f"Erro na suite de backtesting: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analisar resultados da suite de backtesting"""
        try:
            best_strategies = {}
            all_performances = []
            
            for scenario_name, scenario_data in results.items():
                scenario_best = None
                scenario_best_return = -float('inf')
                
                for symbol, symbol_data in scenario_data.items():
                    for strategy, result in symbol_data.items():
                        if result.get('status') == 'success':
                            perf = result['performance']
                            perf_data = {
                                'scenario': scenario_name,
                                'symbol': symbol,
                                'strategy': strategy,
                                'return': perf['total_return'],
                                'win_rate': perf['win_rate'],
                                'drawdown': perf['max_drawdown'],
                                'sharpe': perf['sharpe_ratio'],
                                'trades': perf['total_trades']
                            }
                            all_performances.append(perf_data)
                            
                            if perf['total_return'] > scenario_best_return:
                                scenario_best_return = perf['total_return']
                                scenario_best = perf_data
                
                best_strategies[scenario_name] = scenario_best
            
            # Estatísticas gerais
            if all_performances:
                avg_return = np.mean([p['return'] for p in all_performances])
                avg_win_rate = np.mean([p['win_rate'] for p in all_performances])
                avg_drawdown = np.mean([p['drawdown'] for p in all_performances])
                
                # Recomendações
                recommendations = []
                
                if avg_return > 0.1:  # 10%
                    recommendations.append("Performance excelente - Prosseguir para Demo Trading")
                elif avg_return > 0.05:  # 5%
                    recommendations.append("Performance satisfatória - Considerar otimização de parâmetros")
                else:
                    recommendations.append("Performance abaixo do esperado - Revisar estratégias")
                
                if avg_win_rate > 0.6:
                    recommendations.append("Taxa de acerto consistente")
                else:
                    recommendations.append("Melhorar taxa de acerto das estratégias")
                
                if avg_drawdown < 0.1:
                    recommendations.append("Risco controlado adequadamente")
                else:
                    recommendations.append("Revisar gestão de risco - Drawdown elevado")
            else:
                avg_return = avg_win_rate = avg_drawdown = 0
                recommendations = ["Nenhum resultado válido obtido - Verificar configurações"]
            
            return {
                'best_strategies': best_strategies,
                'statistics': {
                    'avg_return': avg_return,
                    'avg_win_rate': avg_win_rate,
                    'avg_drawdown': avg_drawdown,
                    'total_tests': len(all_performances)
                },
                'recommendations': recommendations,
                'all_performances': all_performances
            }
        
        except Exception as e:
            self.logger.error(f"Erro na análise de resultados: {e}")
            return {
                'best_strategies': {},
                'statistics': {},
                'recommendations': ["Erro na análise - Verificar logs"],
                'all_performances': []
            }

# Função de teste para execução direta
async def test_backtesting_agent():
    """Função de teste para o BacktestingAgentV5"""
    agent = BacktestingAgentV5()
    
    # Teste simples
    config = {
        'symbol': 'BTCUSDT',
        'strategy': 'ema_crossover',
        'start_date': '2025-01-01',
        'end_date': '2025-01-15',
        'timeframe': '5',
        'initial_capital': 10000
    }
    
    print("Testando BacktestingAgentV5...")
    result = await agent.run_backtest(config)
    
    if result['status'] == 'success':
        perf = result['performance']
        print(f"✅ Teste bem-sucedido!")
        print(f"   Retorno: {perf['total_return']:.2%}")
        print(f"   Win Rate: {perf['win_rate']:.1%}")
        print(f"   Trades: {perf['total_trades']}")
        print(f"   Drawdown: {perf['max_drawdown']:.2%}")
    else:
        print(f"❌ Erro no teste: {result.get('error', 'Desconhecido')}")

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Executar teste
    asyncio.run(test_backtesting_agent())

