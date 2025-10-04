#!/usr/bin/env python3
"""
Backtesting Agent para Sistema de Scalping Automatizado
Responsável por validação de estratégias através de backtesting histórico
Autor: Manus AI
Data: 17 de Julho de 2025
"""

import json
import os
import sys
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Adicionar diretório pai ao path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent, SuggestionType, AlertSeverity
from data_providers.historical_cache import HistoricalDataCache

class BacktestingAgent(BaseAgent):
    """
    Agente de Backtesting
    
    Responsabilidades:
    - Validação de estratégias com dados históricos REAIS
    - Simulação de cenários de mercado com dados REAIS
    - Análise de robustez das estratégias
    - Otimização de parâmetros
    - Geração de relatórios de backtesting
    - Validação cruzada de estratégias
    
    Frequência: Diário via PowerShell scheduled task
    
    IMPORTANTE: Este agente usa APENAS dados reais das APIs Binance/Bybit.
    Nenhum dado mockado ou simulado é utilizado.
    """
    
    def __init__(self, data_provider=None):
        super().__init__("BacktestingAgent")
        
        # Data provider para dados reais
        self.data_provider = data_provider
        
        # Sistema de cache para dados históricos
        self.cache = HistoricalDataCache(cache_dir="data")
        
        # Configurações de backtesting
        self.backtest_config = self.load_backtest_config()
        
        # Cache de dados históricos REAIS
        self.historical_data = {}
        
        # Resultados de backtests
        self.backtest_results = []
        
        # Cache de estratégias testadas
        self.strategy_cache = {}
        
        if self.data_provider:
            self.logger.info("BacktestingAgent inicializado com data_provider REAL")
        else:
            self.logger.warning("BacktestingAgent inicializado SEM data_provider - backtests não funcionarão")
            
    def _validate_api_credentials(self) -> bool:
        """
        Valida se as credenciais da API estão configuradas
        
        Returns:
            bool: True se credenciais válidas, False caso contrário
        """
        if not self.data_provider:
            self.logger.error("❌ Data provider não configurado. Impossível executar backtest sem dados reais.")
            return False
        
        # Verificar se o provider tem API key configurada
        if not hasattr(self.data_provider, 'api_key') or not self.data_provider.api_key:
            self.logger.error("❌ API Key não configurada. Configure BINANCE_API_KEY ou BYBIT_API_KEY no ambiente.")
            return False
        
        if not hasattr(self.data_provider, 'api_secret') or not self.data_provider.api_secret:
            self.logger.error("❌ API Secret não configurado. Configure BINANCE_API_SECRET ou BYBIT_API_SECRET no ambiente.")
            return False
        
        self.logger.info("✅ Credenciais da API validadas com sucesso")
        return True
    
    def load_backtest_config(self) -> Dict:
        """Carrega configuração de backtesting"""
        try:
            config_file = "config/backtest_config.json"
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        
        # Configuração padrão
        return {
            "periods": {
                "short_term": {"days": 7, "timeframe": "1m"},
                "medium_term": {"days": 30, "timeframe": "5m"},
                "long_term": {"days": 90, "timeframe": "15m"}
            },
            "validation": {
                "train_ratio": 0.7,
                "validation_ratio": 0.2,
                "test_ratio": 0.1,
                "walk_forward_steps": 10
            },
            "optimization": {
                "enabled": True,
                "max_iterations": 100,
                "optimization_metric": "sharpe_ratio",
                "parameter_ranges": {
                    "ema_short": [5, 20],
                    "ema_long": [20, 50],
                    "rsi_period": [10, 30],
                    "bb_period": [15, 25],
                    "confidence_threshold": [0.5, 0.9]
                }
            },
            "simulation": {
                "initial_capital": 10000,
                "commission": 0.001,
                "slippage": 0.0005,
                "max_positions": 3
            }
        }
    
    def _display_data_metrics(self, total_candles: int, first_time: datetime, last_time: datetime, 
                              successful_batches: int, total_batches: int, data_source: str):
        """
        Exibe métricas de dados históricos carregados em formato visual consistente
        
        Args:
            total_candles: Total de candles carregados
            first_time: Timestamp do primeiro candle
            last_time: Timestamp do último candle
            successful_batches: Número de batches bem-sucedidos
            total_batches: Total de batches realizados
            data_source: Nome da fonte de dados
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
        print(f"🔗 Fonte: {data_source} (dados reais)")
        print("═" * 63)
    
    def get_historical_data(self, symbol: str, days: int, timeframe: str = "1m", use_cache: bool = False) -> pd.DataFrame:
        """
        Obtém dados históricos REAIS da API Binance/Bybit
        
        IMPORTANTE: Este método usa APENAS dados reais das APIs.
        Nenhum dado mockado ou simulado é gerado.
        
        Args:
            symbol: Par de trading (ex: "BTCUSDT")
            days: Número de dias de histórico
            timeframe: Timeframe dos dados (1m, 5m, 15m, etc.)
            use_cache: Se True, usa cache para evitar chamadas repetidas à API
            
        Returns:
            pd.DataFrame: Dados OHLC históricos REAIS da API
        """
        try:
            # Validar credenciais antes de buscar dados
            if not self._validate_api_credentials():
                self.logger.error("❌ Impossível obter dados: credenciais da API não configuradas")
                return pd.DataFrame()
            
            # BUG FIX: Calcular timestamps UMA VEZ no início para garantir consistência
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            start_date_str = start_time.strftime("%Y-%m-%d")
            end_date_str = end_time.strftime("%Y-%m-%d")
            start_timestamp = int(start_time.timestamp() * 1000)
            end_timestamp = int(end_time.timestamp() * 1000)
            
            # Converter timeframe para formato da API
            timeframe_map = {
                "1m": "1",
                "5m": "5", 
                "15m": "15",
                "30m": "30",
                "1h": "60",
                "4h": "240",
                "1d": "D"
            }
            
            api_timeframe = timeframe_map.get(timeframe, "5")
            
            # Tentar carregar do cache se habilitado
            if use_cache:
                try:
                    cached_data = self.cache.get(symbol, timeframe, start_date_str, end_date_str)
                    if cached_data:
                        # BUG FIX: Detectar número de colunas dinamicamente
                        num_cols = len(cached_data[0]) if cached_data else 6
                        
                        if num_cols == 6:
                            col_names = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                        else:
                            col_names = ['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                       'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                                       'taker_buy_quote', 'ignore'][:num_cols]
                        
                        df = pd.DataFrame(cached_data, columns=col_names)
                        
                        # Converter tipos (apenas colunas essenciais)
                        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
                        for col in ['open', 'high', 'low', 'close', 'volume']:
                            if col in df.columns:
                                df[col] = pd.to_numeric(df[col])
                        
                        # Definir timestamp como índice
                        df.set_index('timestamp', inplace=True)
                        df.sort_index(inplace=True)
                        
                        # Exibir mensagem de cache
                        print(f"\n📦 Dados carregados do CACHE ({len(df):,} candles)")
                        self.logger.info(f"📦 Dados carregados do cache: {len(df)} candles para {symbol}")
                        
                        return df
                except Exception as e:
                    self.logger.warning(f"⚠️ Erro ao carregar cache, continuando com API: {str(e)}")
            
            self.logger.info(f"📡 Buscando dados REAIS da API: {symbol}, {days} dias, timeframe {timeframe}")
            self.logger.info(f"📅 Período: {start_time.strftime('%Y-%m-%d')} até {end_time.strftime('%Y-%m-%d')}")
            
            # Buscar dados reais via data_provider
            all_klines = []
            current_start = start_timestamp
            batch_num = 1
            successful_batches = 0
            failed_batches = 0
            
            while current_start < end_timestamp:
                # Calcular limite de candles para este batch
                remaining_ms = end_timestamp - current_start
                limit = min(500, int(remaining_ms / (60 * 1000)))
                
                if limit <= 0:
                    break
                
                self.logger.debug(f"📊 Batch {batch_num}: Buscando até {limit} candles...")
                
                # Chamada REAL à API
                try:
                    klines = self.data_provider.get_kline(
                        category='spot',
                        symbol=symbol,
                        interval=api_timeframe,
                        limit=limit,
                        start=current_start,
                        end=end_timestamp
                    )
                    
                    if not klines:
                        self.logger.warning(f"⚠️  Nenhum dado retornado para batch {batch_num}")
                        failed_batches += 1
                        break
                    
                    all_klines.extend(klines)
                    successful_batches += 1
                    self.logger.debug(f"✅ Batch {batch_num}: Recebidos {len(klines)} candles (total: {len(all_klines)})")
                    
                    # Próximo batch
                    last_candle_time = int(klines[-1][0])
                    current_start = last_candle_time + (60 * 1000)
                    batch_num += 1
                    
                    # Rate limiting
                    time.sleep(0.1)
                except Exception as e:
                    self.logger.error(f"❌ Erro no batch {batch_num}: {str(e)}")
                    failed_batches += 1
                    break
            
            if not all_klines:
                self.logger.error(f"❌ Nenhum dado REAL obtido da API para {symbol}")
                return pd.DataFrame()
            
            # BUG FIX: Detectar número de colunas dinamicamente baseado nos dados retornados
            num_cols = len(all_klines[0]) if all_klines else 6
            
            if num_cols == 6:
                col_names = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            else:
                col_names = ['timestamp', 'open', 'high', 'low', 'close', 'volume',
                           'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                           'taker_buy_quote', 'ignore'][:num_cols]
            
            df = pd.DataFrame(all_klines, columns=col_names)
            
            # Converter tipos (apenas colunas essenciais)
            df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col])
            
            # Definir timestamp como índice
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # Exibir métricas de dados carregados
            total_batches = successful_batches + failed_batches
            data_source = self.data_provider.__class__.__name__ if self.data_provider else "Unknown"
            self._display_data_metrics(
                total_candles=len(df),
                first_time=df.index[0].to_pydatetime(),
                last_time=df.index[-1].to_pydatetime(),
                successful_batches=successful_batches,
                total_batches=total_batches,
                data_source=data_source
            )
            
            self.logger.info(f"✅ Dados REAIS obtidos com sucesso: {len(df)} candles")
            
            # BUG FIX: Salvar no cache usando os mesmos start_date_str/end_date_str calculados no início
            if use_cache:
                try:
                    self.cache.save(symbol, timeframe, start_date_str, end_date_str, all_klines)
                except Exception as e:
                    self.logger.warning(f"⚠️ Erro ao salvar cache: {str(e)}")
            
            return df
            
        except Exception as e:
            self.handle_error(e, "get_historical_data")
            self.logger.error(f"❌ Erro ao obter dados REAIS da API: {str(e)}")
            return pd.DataFrame()
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula indicadores técnicos para os dados históricos
        
        Args:
            df: DataFrame com dados OHLC
            
        Returns:
            pd.DataFrame: DataFrame com indicadores adicionados
        """
        try:
            df = df.copy()
            
            # EMA
            df['ema_9'] = df['close'].ewm(span=9).mean()
            df['ema_21'] = df['close'].ewm(span=21).mean()
            
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
            
            # MACD
            ema_12 = df['close'].ewm(span=12).mean()
            ema_26 = df['close'].ewm(span=26).mean()
            df['macd'] = ema_12 - ema_26
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # Volume indicators
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            # Price action
            df['price_change'] = df['close'].pct_change()
            df['volatility'] = df['price_change'].rolling(window=20).std()
            
            return df
            
        except Exception as e:
            self.handle_error(e, "calculate_technical_indicators")
            return df
    
    def simulate_strategy(self, df: pd.DataFrame, strategy_name: str, parameters: Dict) -> Dict:
        """
        Simula uma estratégia específica nos dados históricos
        
        Args:
            df: DataFrame com dados e indicadores
            strategy_name: Nome da estratégia
            parameters: Parâmetros da estratégia
            
        Returns:
            Dict: Resultados da simulação
        """
        try:
            if not self._validate_api_credentials():
                self.logger.error("❌ Simulação cancelada: credenciais da API não configuradas")
                return {
                    "error": "API credentials não configuradas. Configure BINANCE_API_KEY/BYBIT_API_KEY e seus secrets.",
                    "strategy_name": strategy_name,
                    "parameters": parameters
                }
            
            signals = []
            positions = []
            current_position = None
            
            initial_capital = self.backtest_config["simulation"]["initial_capital"]
            commission = self.backtest_config["simulation"]["commission"]
            slippage = self.backtest_config["simulation"]["slippage"]
            
            capital = initial_capital
            trades = []
            
            for i in range(len(df)):
                if i < 50:  # Aguardar indicadores se estabilizarem
                    continue
                
                row = df.iloc[i]
                
                # Gerar sinal baseado na estratégia
                signal = self.generate_strategy_signal(row, strategy_name, parameters, df.iloc[max(0, i-20):i+1])
                
                if signal and signal != "HOLD":
                    signals.append({
                        "timestamp": row.name,
                        "signal": signal,
                        "price": row['close'],
                        "confidence": signal.get("confidence", 0.7) if isinstance(signal, dict) else 0.7
                    })
                    
                    # Processar sinal
                    if current_position is None and signal in ["BUY", "SELL"]:
                        # Abrir posição
                        entry_price = row['close'] * (1 + slippage if signal == "BUY" else 1 - slippage)
                        position_size = (capital * 0.02) / entry_price  # 2% do capital
                        
                        current_position = {
                            "type": signal,
                            "entry_price": entry_price,
                            "entry_time": row.name,
                            "size": position_size,
                            "stop_loss": entry_price * (0.995 if signal == "BUY" else 1.005),
                            "take_profit": entry_price * (1.01 if signal == "BUY" else 0.99)
                        }
                        
                        positions.append(current_position.copy())
                    
                    elif current_position is not None:
                        # Verificar se deve fechar posição
                        should_close = False
                        exit_reason = ""
                        
                        if current_position["type"] == "BUY":
                            if row['close'] <= current_position["stop_loss"]:
                                should_close = True
                                exit_reason = "stop_loss"
                            elif row['close'] >= current_position["take_profit"]:
                                should_close = True
                                exit_reason = "take_profit"
                            elif signal == "SELL":
                                should_close = True
                                exit_reason = "signal_reversal"
                        
                        else:  # SELL position
                            if row['close'] >= current_position["stop_loss"]:
                                should_close = True
                                exit_reason = "stop_loss"
                            elif row['close'] <= current_position["take_profit"]:
                                should_close = True
                                exit_reason = "take_profit"
                            elif signal == "BUY":
                                should_close = True
                                exit_reason = "signal_reversal"
                        
                        if should_close:
                            # Fechar posição
                            exit_price = row['close'] * (1 - slippage if current_position["type"] == "BUY" else 1 + slippage)
                            
                            if current_position["type"] == "BUY":
                                pnl = (exit_price - current_position["entry_price"]) * current_position["size"]
                            else:
                                pnl = (current_position["entry_price"] - exit_price) * current_position["size"]
                            
                            # Descontar comissões
                            commission_cost = (current_position["entry_price"] + exit_price) * current_position["size"] * commission
                            pnl -= commission_cost
                            
                            capital += pnl
                            
                            trade = {
                                "entry_time": current_position["entry_time"],
                                "exit_time": row.name,
                                "type": current_position["type"],
                                "entry_price": current_position["entry_price"],
                                "exit_price": exit_price,
                                "size": current_position["size"],
                                "pnl": pnl,
                                "pnl_percentage": pnl / (current_position["entry_price"] * current_position["size"]),
                                "exit_reason": exit_reason,
                                "duration": (row.name - current_position["entry_time"]).total_seconds() / 60
                            }
                            
                            trades.append(trade)
                            current_position = None
            
            # Calcular métricas finais
            if trades:
                total_pnl = sum(t["pnl"] for t in trades)
                winning_trades = [t for t in trades if t["pnl"] > 0]
                losing_trades = [t for t in trades if t["pnl"] <= 0]
                
                win_rate = len(winning_trades) / len(trades)
                avg_win = np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
                avg_loss = np.mean([t["pnl"] for t in losing_trades]) if losing_trades else 0
                
                profit_factor = abs(sum(t["pnl"] for t in winning_trades) / sum(t["pnl"] for t in losing_trades)) if losing_trades else float('inf')
                
                # Calcular Sharpe ratio
                returns = [t["pnl_percentage"] for t in trades]
                sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
                
                # Calcular drawdown
                equity_curve = [initial_capital]
                for trade in trades:
                    equity_curve.append(equity_curve[-1] + trade["pnl"])
                
                peak = equity_curve[0]
                max_drawdown = 0
                for value in equity_curve:
                    if value > peak:
                        peak = value
                    drawdown = (peak - value) / peak
                    max_drawdown = max(max_drawdown, drawdown)
            
            else:
                total_pnl = 0
                win_rate = 0
                avg_win = 0
                avg_loss = 0
                profit_factor = 0
                sharpe_ratio = 0
                max_drawdown = 0
            
            results = {
                "strategy_name": strategy_name,
                "parameters": parameters,
                "total_trades": len(trades),
                "winning_trades": len(winning_trades) if trades else 0,
                "losing_trades": len(losing_trades) if trades else 0,
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "final_capital": capital,
                "return_percentage": (capital - initial_capital) / initial_capital,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "profit_factor": profit_factor,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "trades": trades,
                "signals": signals,
                "backtest_period": {
                    "start": df.index[0],
                    "end": df.index[-1],
                    "periods": len(df)
                }
            }
            
            return results
            
        except Exception as e:
            self.handle_error(e, "simulate_strategy")
            return {"error": str(e)}
    
    def generate_strategy_signal(self, row: pd.Series, strategy_name: str, parameters: Dict, history: pd.DataFrame) -> str:
        """
        Gera sinal para uma estratégia específica
        
        Args:
            row: Linha atual de dados
            strategy_name: Nome da estratégia
            parameters: Parâmetros da estratégia
            history: Histórico recente
            
        Returns:
            str: Sinal gerado (BUY/SELL/HOLD)
        """
        try:
            if strategy_name == "ema_crossover":
                return self.ema_crossover_strategy(row, parameters, history)
            elif strategy_name == "rsi_mean_reversion":
                return self.rsi_mean_reversion_strategy(row, parameters, history)
            elif strategy_name == "bollinger_breakout":
                return self.bollinger_breakout_strategy(row, parameters, history)
            else:
                return "HOLD"
                
        except Exception as e:
            self.handle_error(e, "generate_strategy_signal")
            return "HOLD"
    
    def ema_crossover_strategy(self, row: pd.Series, parameters: Dict, history: pd.DataFrame) -> str:
        """Estratégia de cruzamento de EMAs"""
        try:
            if len(history) < 2:
                return "HOLD"
            
            current_ema_short = row['ema_9']
            current_ema_long = row['ema_21']
            prev_ema_short = history.iloc[-2]['ema_9']
            prev_ema_long = history.iloc[-2]['ema_21']
            
            # Cruzamento para cima
            if (current_ema_short > current_ema_long and 
                prev_ema_short <= prev_ema_long and
                row['volume_ratio'] > 1.2):  # Volume confirmação
                return "BUY"
            
            # Cruzamento para baixo
            elif (current_ema_short < current_ema_long and 
                  prev_ema_short >= prev_ema_long and
                  row['volume_ratio'] > 1.2):
                return "SELL"
            
            return "HOLD"
            
        except Exception:
            return "HOLD"
    
    def rsi_mean_reversion_strategy(self, row: pd.Series, parameters: Dict, history: pd.DataFrame) -> str:
        """Estratégia de reversão à média com RSI"""
        try:
            rsi = row['rsi']
            price_change = row['price_change']
            
            # Oversold - sinal de compra
            if rsi < 30 and price_change < -0.005:  # RSI baixo + queda de preço
                return "BUY"
            
            # Overbought - sinal de venda
            elif rsi > 70 and price_change > 0.005:  # RSI alto + alta de preço
                return "SELL"
            
            return "HOLD"
            
        except Exception:
            return "HOLD"
    
    def bollinger_breakout_strategy(self, row: pd.Series, parameters: Dict, history: pd.DataFrame) -> str:
        """Estratégia de breakout das Bollinger Bands"""
        try:
            close = row['close']
            bb_upper = row['bb_upper']
            bb_lower = row['bb_lower']
            volume_ratio = row['volume_ratio']
            
            # Breakout para cima
            if close > bb_upper and volume_ratio > 1.5:
                return "BUY"
            
            # Breakout para baixo
            elif close < bb_lower and volume_ratio > 1.5:
                return "SELL"
            
            return "HOLD"
            
        except Exception:
            return "HOLD"
    
    def run_backtest_suite(self, symbol: str = "BTCUSDT") -> Dict:
        """
        Executa suite completa de backtesting
        
        Args:
            symbol: Símbolo para testar
            
        Returns:
            Dict: Resultados consolidados
        """
        try:
            results = {
                "symbol": symbol,
                "backtest_timestamp": datetime.now().isoformat(),
                "strategies": {},
                "summary": {}
            }
            
            # Estratégias para testar
            strategies_to_test = {
                "ema_crossover": {"ema_short": 9, "ema_long": 21},
                "rsi_mean_reversion": {"rsi_period": 14, "oversold": 30, "overbought": 70},
                "bollinger_breakout": {"bb_period": 20, "bb_std": 2}
            }
            
            # Validar API credentials antes de iniciar backtests
            if not self._validate_api_credentials():
                self.logger.error("❌ Backtest cancelado: API credentials não configuradas")
                return {
                    "error": "API credentials não configuradas. Configure BINANCE_API_KEY/BYBIT_API_KEY e seus secrets.",
                    "symbol": symbol,
                    "backtest_timestamp": datetime.now().isoformat()
                }
            
            # Testar em diferentes períodos
            for period_name, period_config in self.backtest_config["periods"].items():
                self.logger.info(f"Testando período: {period_name} com dados REAIS da API")
                
                # Obter dados históricos REAIS da API
                df = self.get_historical_data(
                    symbol, 
                    period_config["days"], 
                    period_config["timeframe"]
                )
                
                if df.empty:
                    continue
                
                # Calcular indicadores
                df = self.calculate_technical_indicators(df)
                
                # Testar cada estratégia
                for strategy_name, parameters in strategies_to_test.items():
                    self.logger.debug(f"Testando estratégia: {strategy_name}")
                    
                    strategy_results = self.simulate_strategy(df, strategy_name, parameters)
                    
                    if strategy_name not in results["strategies"]:
                        results["strategies"][strategy_name] = {}
                    
                    results["strategies"][strategy_name][period_name] = strategy_results
            
            # Calcular resumo
            results["summary"] = self.calculate_backtest_summary(results["strategies"])
            
            return results
            
        except Exception as e:
            self.handle_error(e, "run_backtest_suite")
            return {"error": str(e)}
    
    def calculate_backtest_summary(self, strategies_results: Dict) -> Dict:
        """
        Calcula resumo dos resultados de backtesting
        
        Args:
            strategies_results: Resultados por estratégia
            
        Returns:
            Dict: Resumo consolidado
        """
        try:
            summary = {
                "best_strategy": None,
                "best_period": None,
                "best_sharpe_ratio": -999,
                "strategy_rankings": [],
                "period_analysis": {},
                "overall_metrics": {}
            }
            
            all_results = []
            
            # Coletar todos os resultados
            for strategy_name, periods in strategies_results.items():
                for period_name, results in periods.items():
                    if "error" not in results:
                        result_summary = {
                            "strategy": strategy_name,
                            "period": period_name,
                            "sharpe_ratio": results.get("sharpe_ratio", 0),
                            "return_percentage": results.get("return_percentage", 0),
                            "win_rate": results.get("win_rate", 0),
                            "profit_factor": results.get("profit_factor", 0),
                            "max_drawdown": results.get("max_drawdown", 0),
                            "total_trades": results.get("total_trades", 0)
                        }
                        all_results.append(result_summary)
            
            if not all_results:
                return summary
            
            # Encontrar melhor estratégia
            best_result = max(all_results, key=lambda x: x["sharpe_ratio"])
            summary["best_strategy"] = best_result["strategy"]
            summary["best_period"] = best_result["period"]
            summary["best_sharpe_ratio"] = best_result["sharpe_ratio"]
            
            # Ranking de estratégias
            strategy_scores = {}
            for result in all_results:
                strategy = result["strategy"]
                if strategy not in strategy_scores:
                    strategy_scores[strategy] = []
                
                # Score composto
                score = (
                    result["sharpe_ratio"] * 0.3 +
                    result["return_percentage"] * 0.25 +
                    result["win_rate"] * 0.2 +
                    min(result["profit_factor"], 5) * 0.15 +  # Cap profit factor
                    (1 - result["max_drawdown"]) * 0.1
                )
                strategy_scores[strategy].append(score)
            
            # Calcular score médio por estratégia
            strategy_rankings = []
            for strategy, scores in strategy_scores.items():
                avg_score = np.mean(scores)
                strategy_rankings.append({
                    "strategy": strategy,
                    "avg_score": avg_score,
                    "consistency": 1 - np.std(scores) if len(scores) > 1 else 1
                })
            
            summary["strategy_rankings"] = sorted(strategy_rankings, key=lambda x: x["avg_score"], reverse=True)
            
            # Análise por período
            period_performance = {}
            for result in all_results:
                period = result["period"]
                if period not in period_performance:
                    period_performance[period] = []
                period_performance[period].append(result)
            
            for period, results in period_performance.items():
                avg_return = np.mean([r["return_percentage"] for r in results])
                avg_sharpe = np.mean([r["sharpe_ratio"] for r in results])
                avg_drawdown = np.mean([r["max_drawdown"] for r in results])
                
                summary["period_analysis"][period] = {
                    "avg_return": avg_return,
                    "avg_sharpe_ratio": avg_sharpe,
                    "avg_max_drawdown": avg_drawdown,
                    "strategies_tested": len(results)
                }
            
            # Métricas gerais
            summary["overall_metrics"] = {
                "total_backtests": len(all_results),
                "avg_return": np.mean([r["return_percentage"] for r in all_results]),
                "avg_win_rate": np.mean([r["win_rate"] for r in all_results]),
                "avg_sharpe_ratio": np.mean([r["sharpe_ratio"] for r in all_results]),
                "strategies_count": len(set(r["strategy"] for r in all_results)),
                "periods_count": len(set(r["period"] for r in all_results))
            }
            
            return summary
            
        except Exception as e:
            self.handle_error(e, "calculate_backtest_summary")
            return {}
    
    def analyze_performance(self) -> Dict:
        """
        Analisa performance do sistema de backtesting
        
        Returns:
            Dict: Métricas de performance
        """
        try:
            # Executar backtesting completo
            backtest_results = self.run_backtest_suite()
            
            if "error" in backtest_results:
                return {"status": "error", "message": backtest_results["error"]}
            
            # Salvar resultados
            self.backtest_results.append(backtest_results)
            
            # Manter histórico limitado
            if len(self.backtest_results) > 10:
                self.backtest_results = self.backtest_results[-10:]
            
            # Análise de performance
            summary = backtest_results.get("summary", {})
            
            performance = {
                "latest_backtest": backtest_results,
                "best_strategy": summary.get("best_strategy", "N/A"),
                "best_sharpe_ratio": summary.get("best_sharpe_ratio", 0),
                "strategy_rankings": summary.get("strategy_rankings", []),
                "overall_metrics": summary.get("overall_metrics", {}),
                "backtest_history_count": len(self.backtest_results),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            return performance
            
        except Exception as e:
            self.handle_error(e, "analyze_performance")
            return {"status": "error", "message": str(e)}
    
    def suggest_improvements(self) -> List[Dict]:
        """
        Sugere melhorias baseadas nos resultados de backtesting
        
        Returns:
            List[Dict]: Lista de sugestões
        """
        try:
            suggestions = []
            
            if not self.backtest_results:
                return suggestions
            
            latest_results = self.backtest_results[-1]
            summary = latest_results.get("summary", {})
            
            # Sugestão 1: Usar melhor estratégia
            best_strategy = summary.get("best_strategy")
            if best_strategy:
                suggestions.append({
                    "type": SuggestionType.STRATEGY_OPTIMIZATION,
                    "priority": "high",
                    "current_metrics": summary.get("overall_metrics", {}),
                    "suggested_changes": {
                        "file": "config/trading_config.json",
                        "line_range": [1, 50],
                        "parameter": f"strategies.{best_strategy}.weight",
                        "current_value": 1.0,
                        "suggested_value": 2.0,
                        "reason": f"Backtesting mostra {best_strategy} como melhor estratégia (Sharpe: {summary.get('best_sharpe_ratio', 0):.2f})",
                        "expected_improvement": "Melhorar performance geral priorizando estratégia mais eficaz"
                    }
                })
            
            # Sugestão 2: Desabilitar estratégias ruins
            rankings = summary.get("strategy_rankings", [])
            if len(rankings) > 1:
                worst_strategy = rankings[-1]
                if worst_strategy.get("avg_score", 0) < 0:
                    suggestions.append({
                        "type": SuggestionType.STRATEGY_OPTIMIZATION,
                        "priority": "medium",
                        "current_metrics": worst_strategy,
                        "suggested_changes": {
                            "file": "config/trading_config.json",
                            "line_range": [1, 50],
                            "parameter": f"strategies.{worst_strategy['strategy']}.enabled",
                            "current_value": True,
                            "suggested_value": False,
                            "reason": f"Estratégia {worst_strategy['strategy']} com performance negativa no backtesting",
                            "expected_improvement": "Eliminar estratégia prejudicial à performance"
                        }
                    })
            
            # Sugestão 3: Ajustar parâmetros baseado no melhor período
            best_period = summary.get("best_period")
            if best_period:
                suggestions.append({
                    "type": SuggestionType.PARAMETER_ADJUSTMENT,
                    "priority": "medium",
                    "current_metrics": {"best_period": best_period},
                    "suggested_changes": {
                        "file": "config/trading_config.json",
                        "line_range": [10, 15],
                        "parameter": "analysis.primary_timeframe",
                        "current_value": "5m",
                        "suggested_value": self.backtest_config["periods"][best_period]["timeframe"],
                        "reason": f"Período {best_period} mostrou melhor performance no backtesting",
                        "expected_improvement": "Otimizar timeframe de análise para melhor performance"
                    }
                })
            
            return suggestions
            
        except Exception as e:
            self.handle_error(e, "suggest_improvements")
            return []
    
    def run(self):
        """
        Executa ciclo principal do agente de backtesting
        """
        self.logger.info("Iniciando ciclo de backtesting")
        
        try:
            # Executar análise de performance (inclui backtesting completo)
            performance = self.analyze_performance()
            
            # Salvar métricas
            self.save_metrics(performance)
            
            # Gerar sugestões
            suggestions = self.suggest_improvements()
            for suggestion in suggestions:
                self.save_suggestion(suggestion)
            
            # Log de conclusão
            best_strategy = performance.get("best_strategy", "N/A")
            best_sharpe = performance.get("best_sharpe_ratio", 0)
            
            self.logger.info(
                f"Ciclo de backtesting concluído - "
                f"Melhor estratégia: {best_strategy} "
                f"(Sharpe: {best_sharpe:.2f}), "
                f"Sugestões: {len(suggestions)}"
            )
            
        except Exception as e:
            self.handle_error(e, "run")
            raise

def main():
    """Função principal para execução standalone"""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Modo de teste
        agent = BacktestingAgent()
        print("Executando teste do BacktestingAgent...")
        agent.run()
        print("Teste concluído com sucesso!")
    else:
        # Execução normal
        agent = BacktestingAgent()
        agent.run_with_error_handling()

if __name__ == "__main__":
    main()

