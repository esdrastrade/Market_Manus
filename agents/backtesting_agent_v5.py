"""
BacktestingAgent V5 - Implementação com API V5 da Bybit
Utiliza endpoints reais da API para backtesting com dados históricos
"""

import os
import json
import asyncio
import pandas as pd
import numpy as np
import requests
import hmac
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass

from .base_agent import BaseAgent

@dataclass
class BacktestConfig:
    """Configuração para backtesting"""
    symbol: str
    strategy: str
    start_date: str
    end_date: str
    timeframe: str
    initial_capital: float
    commission: float = 0.001
    slippage: float = 0.0005

@dataclass
class TradeResult:
    """Resultado de um trade"""
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    side: str  # 'buy' or 'sell'
    pnl: float
    commission: float

class BybitAPIV5:
    """Cliente para API V5 da Bybit"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api-testnet.bybit.com" if testnet else "https://api.bybit.com"
        self.demo_url = "https://api-demo.bybit.com"
        
    def _generate_signature(self, params: dict, timestamp: str) -> str:
        """Gerar assinatura para autenticação"""
        param_str = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        sign_str = f"{timestamp}{self.api_key}5000{param_str}"
        
        return hmac.new(
            self.api_secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def get_klines(self, symbol: str, interval: str, start_time: int, end_time: int, 
                   category: str = 'linear', limit: int = 1000) -> Optional[List]:
        """
        Obter dados históricos de klines usando API V5
        
        Args:
            symbol: Par de trading (ex: BTCUSDT)
            interval: Timeframe (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)
            start_time: Timestamp de início (ms)
            end_time: Timestamp de fim (ms)
            category: Tipo de produto (spot, linear, inverse, option)
            limit: Limite de registros por request (max 1000)
        
        Returns:
            Lista de klines ou None se erro
        """
        
        url = f"{self.base_url}/v5/market/kline"
        
        params = {
            'category': category,
            'symbol': symbol,
            'interval': interval,
            'start': start_time,
            'end': end_time,
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('retCode') == 0:
                return data['result']['list']
            else:
                logging.error(f"Erro API Bybit: {data.get('retMsg', 'Erro desconhecido')}")
                return None
                
        except Exception as e:
            logging.error(f"Erro ao obter klines: {e}")
            return None
    
    def get_historical_data(self, symbol: str, interval: str, start_date: str, 
                           end_date: str, category: str = 'linear') -> Optional[pd.DataFrame]:
        """
        Obter dados históricos completos para um período
        
        Args:
            symbol: Par de trading
            interval: Timeframe
            start_date: Data início (YYYY-MM-DD)
            end_date: Data fim (YYYY-MM-DD)
            category: Tipo de produto
        
        Returns:
            DataFrame com dados OHLCV ou None se erro
        """
        
        # Converter datas para timestamps
        start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
        end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
        
        all_klines = []
        current_end = end_ts
        
        logging.info(f"Obtendo dados históricos: {symbol} {interval} de {start_date} a {end_date}")
        
        while current_end > start_ts:
            klines = self.get_klines(symbol, interval, start_ts, current_end, category)
            
            if not klines:
                break
            
            all_klines.extend(klines)
            
            # Se obtivemos menos que o limite, chegamos ao fim
            if len(klines) < 1000:
                break
            
            # Próxima página - usar timestamp do último kline
            current_end = int(klines[-1][0]) - 1
            
            # Evitar rate limiting
            time.sleep(0.1)
        
        if not all_klines:
            logging.error(f"Nenhum dado obtido para {symbol}")
            return None
        
        # Converter para DataFrame
        df = pd.DataFrame(all_klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
        ])
        
        # Processar dados
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume', 'turnover']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Ordenar por timestamp e remover duplicatas
        df = df.sort_values('timestamp').drop_duplicates(subset=['timestamp']).reset_index(drop=True)
        
        # Filtrar pelo período exato
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        df = df[(df['timestamp'] >= start_dt) & (df['timestamp'] <= end_dt)]
        
        logging.info(f"Dados obtidos: {len(df)} registros de {df['timestamp'].min()} a {df['timestamp'].max()}\")\n        \n        return df.reset_index(drop=True)

class StrategyEngine:
    \"\"\"Engine para execução de estratégias de trading\"\"\"
    
    @staticmethod
    def ema_crossover(data: pd.DataFrame, fast_period: int = 12, slow_period: int = 26) -> pd.DataFrame:
        \"\"\"
        Estratégia EMA Crossover
        
        Sinais:
        - EMA rápida cruza acima EMA lenta = COMPRA
        - EMA rápida cruza abaixo EMA lenta = VENDA
        \"\"\"
        
        df = data.copy()
        
        # Calcular EMAs
        df['ema_fast'] = df['close'].ewm(span=fast_period).mean()
        df['ema_slow'] = df['close'].ewm(span=slow_period).mean()
        
        # Inicializar colunas de sinal
        df['signal'] = 0
        df['position'] = 0
        
        # Gerar sinais
        for i in range(1, len(df)):
            if (df.iloc[i]['ema_fast'] > df.iloc[i]['ema_slow'] and 
                df.iloc[i-1]['ema_fast'] <= df.iloc[i-1]['ema_slow']):
                # Crossover para cima = Compra
                df.iloc[i, df.columns.get_loc('signal')] = 1
                df.iloc[i, df.columns.get_loc('position')] = 1
                
            elif (df.iloc[i]['ema_fast'] < df.iloc[i]['ema_slow'] and 
                  df.iloc[i-1]['ema_fast'] >= df.iloc[i-1]['ema_slow']):
                # Crossover para baixo = Venda
                df.iloc[i, df.columns.get_loc('signal')] = -1
                df.iloc[i, df.columns.get_loc('position')] = 0
            else:
                # Manter posição anterior
                df.iloc[i, df.columns.get_loc('position')] = df.iloc[i-1]['position']
        
        return df
    
    @staticmethod
    def rsi_mean_reversion(data: pd.DataFrame, rsi_period: int = 14, 
                          oversold: float = 30, overbought: float = 70) -> pd.DataFrame:
        \"\"\"
        Estratégia RSI Mean Reversion
        
        Sinais:
        - RSI < oversold = COMPRA
        - RSI > overbought = VENDA
        \"\"\"
        
        df = data.copy()
        
        # Calcular RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Inicializar colunas
        df['signal'] = 0
        df['position'] = 0
        
        # Gerar sinais
        for i in range(rsi_period, len(df)):
            current_rsi = df.iloc[i]['rsi']
            prev_position = df.iloc[i-1]['position']
            
            if current_rsi < oversold and prev_position == 0:
                # Oversold = Compra
                df.iloc[i, df.columns.get_loc('signal')] = 1
                df.iloc[i, df.columns.get_loc('position')] = 1
                
            elif current_rsi > overbought and prev_position == 1:
                # Overbought = Venda
                df.iloc[i, df.columns.get_loc('signal')] = -1
                df.iloc[i, df.columns.get_loc('position')] = 0
            else:
                # Manter posição
                df.iloc[i, df.columns.get_loc('position')] = prev_position
        
        return df
    
    @staticmethod
    def bollinger_breakout(data: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        \"\"\"
        Estratégia Bollinger Bands Breakout
        
        Sinais:
        - Preço rompe banda superior = COMPRA
        - Preço rompe banda inferior = VENDA
        \"\"\"
        
        df = data.copy()
        
        # Calcular Bollinger Bands
        df['bb_middle'] = df['close'].rolling(window=period).mean()
        bb_std = df['close'].rolling(window=period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * std_dev)
        df['bb_lower'] = df['bb_middle'] - (bb_std * std_dev)
        
        # Inicializar colunas
        df['signal'] = 0
        df['position'] = 0
        
        # Gerar sinais
        for i in range(period, len(df)):
            current_price = df.iloc[i]['close']
            prev_price = df.iloc[i-1]['close']
            upper_band = df.iloc[i]['bb_upper']
            lower_band = df.iloc[i]['bb_lower']
            prev_position = df.iloc[i-1]['position']
            
            if current_price > upper_band and prev_price <= df.iloc[i-1]['bb_upper']:
                # Breakout para cima = Compra
                df.iloc[i, df.columns.get_loc('signal')] = 1
                df.iloc[i, df.columns.get_loc('position')] = 1
                
            elif current_price < lower_band and prev_price >= df.iloc[i-1]['bb_lower']:
                # Breakout para baixo = Venda
                df.iloc[i, df.columns.get_loc('signal')] = -1
                df.iloc[i, df.columns.get_loc('position')] = 0
            else:
                # Manter posição
                df.iloc[i, df.columns.get_loc('position')] = prev_position
        
        return df

class PerformanceAnalyzer:
    \"\"\"Analisador de performance para backtesting\"\"\"
    
    @staticmethod
    def calculate_performance(data: pd.DataFrame, config: BacktestConfig) -> Dict[str, Any]:
        \"\"\"
        Calcular métricas de performance do backtest
        
        Args:
            data: DataFrame com sinais de trading
            config: Configuração do backtest
        
        Returns:
            Dicionário com métricas de performance
        \"\"\"
        
        # Simular execução de trades
        capital = config.initial_capital
        position_size = 0
        trades = []
        equity_curve = []
        
        for i in range(len(data)):
            current_price = data.iloc[i]['close']
            signal = data.iloc[i]['signal']
            timestamp = data.iloc[i]['timestamp']
            
            # Aplicar slippage
            if signal == 1:  # Compra
                execution_price = current_price * (1 + config.slippage)
            elif signal == -1:  # Venda
                execution_price = current_price * (1 - config.slippage)
            else:
                execution_price = current_price
            
            if signal == 1 and position_size == 0:
                # Abrir posição longa
                commission_cost = capital * config.commission
                capital -= commission_cost
                position_size = capital / execution_price
                
                trades.append({
                    'type': 'buy',
                    'price': execution_price,
                    'time': timestamp,
                    'quantity': position_size,
                    'commission': commission_cost
                })
                
            elif signal == -1 and position_size > 0:
                # Fechar posição longa
                capital = position_size * execution_price
                commission_cost = capital * config.commission
                capital -= commission_cost
                
                trades.append({
                    'type': 'sell',
                    'price': execution_price,
                    'time': timestamp,
                    'quantity': position_size,
                    'commission': commission_cost
                })
                
                position_size = 0
            
            # Calcular equity atual
            if position_size > 0:
                current_equity = position_size * current_price
            else:
                current_equity = capital
            
            equity_curve.append(current_equity)
        
        # Fechar posição final se necessário
        if position_size > 0:
            final_price = data.iloc[-1]['close']
            capital = position_size * final_price
            commission_cost = capital * config.commission
            capital -= commission_cost
            
            trades.append({
                'type': 'sell',
                'price': final_price,
                'time': data.iloc[-1]['timestamp'],
                'quantity': position_size,
                'commission': commission_cost
            })
        
        # Calcular métricas
        total_return = (capital - config.initial_capital) / config.initial_capital
        
        # Análise de trades
        trade_pairs = []
        for i in range(0, len(trades) - 1, 2):
            if i + 1 < len(trades):
                buy_trade = trades[i]
                sell_trade = trades[i + 1]
                
                pnl = (sell_trade['price'] - buy_trade['price']) * buy_trade['quantity']
                pnl -= (buy_trade['commission'] + sell_trade['commission'])
                
                trade_pairs.append({
                    'entry_time': buy_trade['time'],
                    'exit_time': sell_trade['time'],
                    'entry_price': buy_trade['price'],
                    'exit_price': sell_trade['price'],
                    'quantity': buy_trade['quantity'],
                    'pnl': pnl,
                    'return': pnl / (buy_trade['price'] * buy_trade['quantity'])
                })
        
        # Métricas de trades
        total_trades = len(trade_pairs)
        winning_trades = sum(1 for trade in trade_pairs if trade['pnl'] > 0)
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # PnL
        gross_profit = sum(trade['pnl'] for trade in trade_pairs if trade['pnl'] > 0)
        gross_loss = sum(trade['pnl'] for trade in trade_pairs if trade['pnl'] < 0)
        net_profit = gross_profit + gross_loss
        
        # Profit factor
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf')
        
        # Drawdown
        equity_series = pd.Series(equity_curve)
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max
        max_drawdown = abs(drawdown.min())
        
        # Sharpe ratio
        returns = equity_series.pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252 * 24 * 12)  # Para 5min
        else:
            sharpe_ratio = 0
        
        # Calmar ratio
        calmar_ratio = total_return / max_drawdown if max_drawdown > 0 else 0
        
        return {
            'initial_capital': config.initial_capital,
            'final_capital': capital,
            'total_return': total_return,
            'net_profit': net_profit,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'calmar_ratio': calmar_ratio,
            'equity_curve': equity_curve,
            'trades': trades,
            'trade_pairs': trade_pairs
        }

class BacktestingAgentV5(BaseAgent):
    \"\"\"
    Agente de Backtesting usando API V5 da Bybit
    
    Funcionalidades:
    - Obtenção de dados históricos via API V5
    - Execução de múltiplas estratégias
    - Análise de performance detalhada
    - Testes em diferentes cenários de mercado
    - Geração de relatórios
    \"\"\"
    
    def __init__(self):
        super().__init__(\"BacktestingAgentV5\")
        
        # Configuração da API
        self.api_key = os.getenv('BYBIT_API_KEY')
        self.api_secret = os.getenv('BYBIT_API_SECRET')
        
        if not self.api_key or not self.api_secret:
            raise ValueError(\"Credenciais da API Bybit não encontradas nas variáveis de ambiente\")
        
        # Inicializar componentes
        self.api_client = BybitAPIV5(self.api_key, self.api_secret)
        self.strategy_engine = StrategyEngine()
        self.performance_analyzer = PerformanceAnalyzer()
        
        # Carregar configurações
        self.config = self.load_backtesting_config()
        
        self.logger.info(\"BacktestingAgentV5 inicializado com sucesso\")
    
    def load_backtesting_config(self) -> Dict[str, Any]:
        \"\"\"Carregar configurações de backtesting\"\"\"
        
        config_path = 'config/backtesting_config.json'
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.logger.info(f\"Configuração carregada: {config_path}\")
            return config
            
        except FileNotFoundError:
            self.logger.warning(f\"Arquivo de configuração não encontrado: {config_path}\")
            return self.get_default_config()
        except json.JSONDecodeError as e:
            self.logger.error(f\"Erro ao decodificar JSON: {e}\")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        \"\"\"Configuração padrão para backtesting\"\"\"
        
        return {
            \"symbols\": [\"BTCUSDT\", \"ETHUSDT\"],
            \"timeframes\": [\"5\", \"15\", \"60\"],
            \"strategies\": [\"ema_crossover\", \"rsi_mean_reversion\", \"bollinger_breakout\"],
            \"test_scenarios\": [
                {
                    \"name\": \"bull_market\",
                    \"period\": \"2025-01-01_to_2025-03-01\",
                    \"description\": \"Mercado em alta - Bitcoin $42k → $73k\"
                },
                {
                    \"name\": \"bear_market\",
                    \"period\": \"2025-03-01_to_2025-05-01\",
                    \"description\": \"Mercado em baixa - Bitcoin $73k → $56k\"
                },
                {
                    \"name\": \"sideways_market\",
                    \"period\": \"2025-05-01_to_2025-07-01\",
                    \"description\": \"Mercado lateral - Bitcoin $56k ↔ $62k\"
                }
            ],
            \"initial_capital\": 10000,
            \"commission\": 0.001,
            \"slippage\": 0.0005
        }
    
    async def run_backtest(self, config: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"
        Executar backtesting para uma configuração específica
        
        Args:
            config: Configuração do backtest
                - symbol: Par de trading
                - strategy: Nome da estratégia
                - start_date: Data de início (YYYY-MM-DD)
                - end_date: Data de fim (YYYY-MM-DD)
                - timeframe: Timeframe dos dados
                - initial_capital: Capital inicial
        
        Returns:
            Resultado do backtesting
        \"\"\"
        
        try:
            self.logger.info(f\"Iniciando backtesting: {config['symbol']} {config['strategy']}\")
            
            # Criar configuração do backtest
            backtest_config = BacktestConfig(
                symbol=config['symbol'],
                strategy=config['strategy'],
                start_date=config['start_date'],
                end_date=config['end_date'],
                timeframe=config['timeframe'],
                initial_capital=config.get('initial_capital', 10000),
                commission=config.get('commission', 0.001),
                slippage=config.get('slippage', 0.0005)
            )
            
            # Obter dados históricos
            self.logger.info(f\"Obtendo dados históricos para {config['symbol']}\")
            data = self.api_client.get_historical_data(
                symbol=config['symbol'],
                interval=config['timeframe'],
                start_date=config['start_date'],
                end_date=config['end_date']
            )
            
            if data is None or len(data) == 0:
                return {
                    'status': 'error',
                    'error': 'Não foi possível obter dados históricos'
                }
            
            self.logger.info(f\"Dados obtidos: {len(data)} registros\")
            
            # Aplicar estratégia
            strategy_func = getattr(self.strategy_engine, config['strategy'], None)
            if strategy_func is None:
                return {
                    'status': 'error',
                    'error': f'Estratégia não encontrada: {config[\"strategy\"]}'
                }
            
            self.logger.info(f\"Aplicando estratégia: {config['strategy']}\")
            data_with_signals = strategy_func(data)
            
            # Calcular performance
            self.logger.info(\"Calculando métricas de performance\")
            performance = self.performance_analyzer.calculate_performance(
                data_with_signals, backtest_config
            )
            
            # Salvar resultados
            result = {
                'status': 'success',
                'config': config,
                'data_points': len(data),
                'performance': performance,
                'timestamp': datetime.now().isoformat()
            }
            
            # Salvar em arquivo
            self.save_backtest_result(result)
            
            self.logger.info(f\"Backtesting concluído: Retorno {performance['total_return']:.2%}\")
            
            return result
            
        except Exception as e:
            self.logger.error(f\"Erro durante backtesting: {e}\")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    async def run_scenario_backtest(self, scenario_name: str) -> Dict[str, Any]:
        \"\"\"
        Executar backtesting para um cenário específico
        
        Args:
            scenario_name: Nome do cenário (bull_market, bear_market, sideways_market)
        
        Returns:
            Resultados do backtesting para o cenário
        \"\"\"
        
        # Encontrar cenário
        scenario = None
        for s in self.config['test_scenarios']:
            if s['name'] == scenario_name:
                scenario = s
                break
        
        if scenario is None:
            return {
                'status': 'error',
                'error': f'Cenário não encontrado: {scenario_name}'
            }
        
        # Extrair datas do período
        period_parts = scenario['period'].split('_to_')
        start_date = period_parts[0]
        end_date = period_parts[1]
        
        results = {}
        
        # Testar todas as combinações
        for symbol in self.config['symbols']:
            results[symbol] = {}
            
            for strategy in self.config['strategies']:
                for timeframe in self.config['timeframes']:
                    
                    config = {
                        'symbol': symbol,
                        'strategy': strategy,
                        'start_date': start_date,
                        'end_date': end_date,
                        'timeframe': timeframe,
                        'initial_capital': self.config['initial_capital'],
                        'commission': self.config['commission'],
                        'slippage': self.config['slippage']
                    }
                    
                    result = await self.run_backtest(config)
                    
                    key = f\"{strategy}_{timeframe}\"
                    results[symbol][key] = result
        
        return {
            'status': 'success',
            'scenario': scenario,
            'results': results
        }
    
    async def run_full_backtest_suite(self) -> Dict[str, Any]:
        \"\"\"
        Executar suite completa de backtesting
        
        Returns:
            Resultados completos de todos os cenários
        \"\"\"
        
        self.logger.info(\"Iniciando suite completa de backtesting\")
        
        full_results = {}
        
        for scenario in self.config['test_scenarios']:
            scenario_name = scenario['name']
            
            self.logger.info(f\"Executando cenário: {scenario_name}\")
            
            scenario_results = await self.run_scenario_backtest(scenario_name)
            full_results[scenario_name] = scenario_results
        
        # Gerar análise comparativa
        analysis = self.generate_comparative_analysis(full_results)
        
        final_result = {
            'status': 'success',
            'scenarios': full_results,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        }
        
        # Salvar resultados completos
        self.save_full_results(final_result)
        
        self.logger.info(\"Suite completa de backtesting concluída\")
        
        return final_result
    
    def generate_comparative_analysis(self, results: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Gerar análise comparativa dos resultados\"\"\"
        
        analysis = {
            'best_strategies': {},
            'scenario_performance': {},
            'overall_rankings': [],
            'recommendations': []
        }
        
        # Analisar performance por cenário
        for scenario_name, scenario_data in results.items():
            if scenario_data['status'] != 'success':
                continue
            
            scenario_results = scenario_data['results']
            best_return = -float('inf')
            best_config = None
            
            for symbol, symbol_results in scenario_results.items():
                for config_key, result in symbol_results.items():
                    if result['status'] == 'success':
                        total_return = result['performance']['total_return']
                        
                        if total_return > best_return:
                            best_return = total_return
                            best_config = {
                                'symbol': symbol,
                                'config': config_key,
                                'return': total_return,
                                'win_rate': result['performance']['win_rate'],
                                'max_drawdown': result['performance']['max_drawdown']
                            }
            
            analysis['best_strategies'][scenario_name] = best_config
            analysis['scenario_performance'][scenario_name] = {
                'best_return': best_return,
                'description': scenario_data['scenario']['description']
            }
        
        # Gerar recomendações
        if analysis['best_strategies']:
            avg_return = np.mean([s['return'] for s in analysis['best_strategies'].values() if s])
            
            if avg_return > 0.1:  # 10%
                analysis['recommendations'].append(\"✅ Performance satisfatória - Prosseguir para Demo Trading\")
            elif avg_return > 0.05:  # 5%
                analysis['recommendations'].append(\"⚠️ Performance moderada - Otimizar parâmetros\")
            else:
                analysis['recommendations'].append(\"❌ Performance insatisfatória - Revisar estratégias\")
        
        return analysis
    
    def save_backtest_result(self, result: Dict[str, Any]):
        \"\"\"Salvar resultado individual de backtesting\"\"\"
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f\"backtest_{result['config']['symbol']}_{result['config']['strategy']}_{timestamp}.json\"
        filepath = os.path.join('results', 'backtests', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        self.logger.info(f\"Resultado salvo: {filepath}\")
    
    def save_full_results(self, results: Dict[str, Any]):
        \"\"\"Salvar resultados completos da suite\"\"\"
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f\"backtest_suite_{timestamp}.json\"
        filepath = os.path.join('results', 'backtests', filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f\"Resultados completos salvos: {filepath}\")
    
    def generate_html_report(self, results: Dict[str, Any]) -> str:
        \"\"\"Gerar relatório HTML dos resultados\"\"\"
        
        # Implementar geração de relatório HTML
        # Por enquanto, retornar caminho placeholder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f\"results/reports/backtest_report_{timestamp}.html\"
        
        # TODO: Implementar geração real do HTML
        self.logger.info(f\"Relatório HTML seria gerado em: {report_path}\")
        
        return report_path

# Exemplo de uso
if __name__ == \"__main__\":
    async def main():
        agent = BacktestingAgentV5()
        
        # Executar backtesting para um cenário específico
        result = await agent.run_scenario_backtest('bull_market')
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(main())

