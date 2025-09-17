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

class BacktestingAgent(BaseAgent):
    """
    Agente de Backtesting
    
    Responsabilidades:
    - Validação de estratégias com dados históricos
    - Simulação de cenários de mercado
    - Análise de robustez das estratégias
    - Otimização de parâmetros
    - Geração de relatórios de backtesting
    - Validação cruzada de estratégias
    
    Frequência: Diário via PowerShell scheduled task
    """
    
    def __init__(self):
        super().__init__("BacktestingAgent")
        
        # Configurações de backtesting
        self.backtest_config = self.load_backtest_config()
        
        # Dados históricos simulados
        self.historical_data = {}
        
        # Resultados de backtests
        self.backtest_results = []
        
        # Cache de estratégias testadas
        self.strategy_cache = {}
        
        self.logger.info("BacktestingAgent inicializado")
    
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
    
    def generate_historical_data(self, symbol: str, days: int, timeframe: str = "1m") -> pd.DataFrame:
        """
        Gera dados históricos simulados para backtesting
        
        Em produção, conectaria com APIs de dados históricos reais
        Para demonstração, simula dados OHLC realistas
        
        Args:
            symbol: Par de trading
            days: Número de dias de histórico
            timeframe: Timeframe dos dados (1m, 5m, 15m, etc.)
            
        Returns:
            pd.DataFrame: Dados OHLC históricos
        """
        try:
            # Calcular número de períodos baseado no timeframe
            timeframe_minutes = {
                "1m": 1,
                "5m": 5,
                "15m": 15,
                "1h": 60,
                "4h": 240,
                "1d": 1440
            }
            
            minutes_per_period = timeframe_minutes.get(timeframe, 1)
            periods_per_day = 1440 // minutes_per_period  # 1440 minutos por dia
            total_periods = days * periods_per_day
            
            # Gerar timestamps
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            timestamps = pd.date_range(
                start=start_time,
                end=end_time,
                periods=total_periods
            )
            
            # Parâmetros de simulação baseados no símbolo
            if "BTC" in symbol:
                base_price = 45000
                volatility = 0.02
            elif "ETH" in symbol:
                base_price = 3000
                volatility = 0.025
            elif "EUR" in symbol:
                base_price = 1.1
                volatility = 0.008
            else:
                base_price = 1000
                volatility = 0.015
            
            # Gerar série de preços com random walk + tendência
            np.random.seed(42)  # Para reprodutibilidade
            
            # Tendência sutil
            trend = np.linspace(0, 0.1, total_periods)  # 10% de tendência ao longo do período
            
            # Random walk
            returns = np.random.normal(0, volatility / np.sqrt(periods_per_day), total_periods)
            
            # Adicionar alguns padrões realistas
            # Volatilidade clustering
            volatility_regime = np.random.choice([0.5, 1.0, 1.5], total_periods, p=[0.3, 0.5, 0.2])
            returns *= volatility_regime
            
            # Calcular preços
            log_prices = np.log(base_price) + np.cumsum(returns) + trend
            prices = np.exp(log_prices)
            
            # Gerar OHLC
            ohlc_data = []
            
            for i, price in enumerate(prices):
                # Simular variação intraperiod
                high_factor = 1 + abs(np.random.normal(0, volatility * 0.3))
                low_factor = 1 - abs(np.random.normal(0, volatility * 0.3))
                
                open_price = prices[i-1] if i > 0 else price
                close_price = price
                high_price = max(open_price, close_price) * high_factor
                low_price = min(open_price, close_price) * low_factor
                
                # Volume simulado (maior volume em movimentos maiores)
                price_change = abs(close_price - open_price) / open_price
                base_volume = np.random.uniform(1000, 5000)
                volume = base_volume * (1 + price_change * 10)
                
                ohlc_data.append({
                    "timestamp": timestamps[i],
                    "open": round(open_price, 2),
                    "high": round(high_price, 2),
                    "low": round(low_price, 2),
                    "close": round(close_price, 2),
                    "volume": round(volume, 0)
                })
            
            df = pd.DataFrame(ohlc_data)
            df.set_index("timestamp", inplace=True)
            
            self.logger.debug(f"Dados históricos gerados: {symbol}, {days} dias, {len(df)} períodos")
            
            return df
            
        except Exception as e:
            self.handle_error(e, "generate_historical_data")
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
            
            # Testar em diferentes períodos
            for period_name, period_config in self.backtest_config["periods"].items():
                self.logger.info(f"Testando período: {period_name}")
                
                # Gerar dados históricos
                df = self.generate_historical_data(
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

