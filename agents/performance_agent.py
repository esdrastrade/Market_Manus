#!/usr/bin/env python3
"""
Performance Agent para Sistema de Scalping Automatizado
Responsável por análise de performance, métricas e otimização do sistema
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

from agents.base_agent import BaseAgent, SuggestionType, AlertSeverity, calculate_sharpe_ratio, calculate_max_drawdown

class PerformanceAgent(BaseAgent):
    """
    Agente de Monitoramento de Performance
    
    Responsabilidades:
    - Cálculo de métricas de trading avançadas
    - Análise de tendências de performance
    - Identificação de padrões de mercado
    - Geração de relatórios HTML detalhados
    - Sugestões de otimização de estratégias
    - Benchmarking e comparação de performance
    
    Frequência: A cada 6 horas via PowerShell scheduled task
    """
    
    def __init__(self):
        super().__init__("PerformanceAgent")
        
        # Configurações de análise
        self.analysis_periods = {
            "short_term": 24,    # 24 horas
            "medium_term": 168,  # 1 semana
            "long_term": 720     # 1 mês
        }
        
        # Cache de dados para análise
        self.performance_cache = {}
        self.benchmark_data = {}
        
        # Métricas calculadas
        self.calculated_metrics = {}
        
        # Histórico de relatórios
        self.report_history = []
        
        self.logger.info("PerformanceAgent inicializado")
    
    def load_trading_data(self, period_hours: int = 168) -> Dict:
        """
        Carrega dados de trading para análise
        
        Args:
            period_hours: Período em horas para carregar dados
            
        Returns:
            Dict: Dados consolidados de trading
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=period_hours)
            
            # Carregar sinais
            signals = []
            signals_dir = Path("data/signals")
            if signals_dir.exists():
                for signal_file in signals_dir.glob("*.json"):
                    try:
                        file_time = datetime.fromtimestamp(signal_file.stat().st_mtime)
                        if file_time >= cutoff_time:
                            with open(signal_file, 'r', encoding='utf-8') as f:
                                signal = json.load(f)
                                signals.append(signal)
                    except Exception:
                        continue
            
            # Carregar histórico de portfolio
            portfolio_history = []
            portfolio_file = "data/portfolio_history.json"
            if os.path.exists(portfolio_file):
                try:
                    with open(portfolio_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        portfolio_history = data.get("values", [])
                except Exception:
                    pass
            
            # Carregar alertas de risco
            risk_alerts = []
            alerts_dir = Path("data/alerts")
            if alerts_dir.exists():
                for alert_file in alerts_dir.glob("*.json"):
                    try:
                        file_time = datetime.fromtimestamp(alert_file.stat().st_mtime)
                        if file_time >= cutoff_time:
                            with open(alert_file, 'r', encoding='utf-8') as f:
                                alert = json.load(f)
                                risk_alerts.append(alert)
                    except Exception:
                        continue
            
            return {
                "signals": signals,
                "portfolio_history": portfolio_history,
                "risk_alerts": risk_alerts,
                "period_hours": period_hours,
                "data_loaded_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.handle_error(e, "load_trading_data")
            return {"signals": [], "portfolio_history": [], "risk_alerts": []}
    
    def simulate_trade_results(self, signals: List[Dict]) -> List[Dict]:
        """
        Simula resultados de trades baseado nos sinais
        
        Em produção, usaria dados reais de execução
        Para demonstração, simula baseado na confiança dos sinais
        
        Args:
            signals: Lista de sinais de trading
            
        Returns:
            List[Dict]: Lista de trades simulados
        """
        try:
            trades = []
            
            for signal in signals:
                if signal.get("signal") in ["BUY", "SELL"]:
                    confidence = signal.get("confidence", 0.5)
                    price = signal.get("price", 1000)
                    
                    # Simular resultado baseado na confiança
                    # Maior confiança = maior probabilidade de sucesso
                    win_probability = min(0.9, confidence * 1.1)
                    is_winner = np.random.random() < win_probability
                    
                    # Simular P&L
                    if is_winner:
                        # Ganho entre 0.3% e 1.5%
                        pnl_percentage = np.random.uniform(0.003, 0.015)
                    else:
                        # Perda entre 0.2% e 0.8%
                        pnl_percentage = -np.random.uniform(0.002, 0.008)
                    
                    # Simular duração do trade (scalping: 5-30 minutos)
                    duration_minutes = np.random.uniform(5, 30)
                    
                    # Simular position size (baseado na confiança)
                    position_size_usd = 1000 * confidence  # $500-$1000 típico
                    
                    pnl_usd = position_size_usd * pnl_percentage
                    
                    trade = {
                        "signal_id": signal.get("timestamp", ""),
                        "symbol": signal.get("symbol", ""),
                        "signal_type": signal.get("signal"),
                        "confidence": confidence,
                        "entry_price": price,
                        "exit_price": price * (1 + pnl_percentage),
                        "position_size_usd": position_size_usd,
                        "pnl_usd": pnl_usd,
                        "pnl_percentage": pnl_percentage,
                        "duration_minutes": duration_minutes,
                        "is_winner": is_winner,
                        "timestamp": signal.get("timestamp", ""),
                        "strategies_used": [s.get("strategy") for s in signal.get("individual_signals", [])]
                    }
                    
                    trades.append(trade)
            
            return trades
            
        except Exception as e:
            self.handle_error(e, "simulate_trade_results")
            return []
    
    def calculate_trading_metrics(self, trades: List[Dict]) -> Dict:
        """
        Calcula métricas avançadas de trading
        
        Args:
            trades: Lista de trades
            
        Returns:
            Dict: Métricas calculadas
        """
        try:
            if not trades:
                return {
                    "total_trades": 0,
                    "win_rate": 0,
                    "total_pnl": 0,
                    "avg_win": 0,
                    "avg_loss": 0,
                    "profit_factor": 0,
                    "sharpe_ratio": 0,
                    "max_drawdown": 0
                }
            
            # Métricas básicas
            total_trades = len(trades)
            winning_trades = [t for t in trades if t["is_winner"]]
            losing_trades = [t for t in trades if not t["is_winner"]]
            
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            
            # P&L
            total_pnl = sum(t["pnl_usd"] for t in trades)
            avg_win = np.mean([t["pnl_usd"] for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t["pnl_usd"] for t in losing_trades]) if losing_trades else 0
            
            # Profit Factor
            gross_profit = sum(t["pnl_usd"] for t in winning_trades)
            gross_loss = abs(sum(t["pnl_usd"] for t in losing_trades))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
            
            # Sharpe Ratio
            returns = [t["pnl_percentage"] for t in trades]
            sharpe_ratio = calculate_sharpe_ratio(returns)
            
            # Drawdown
            cumulative_pnl = np.cumsum([t["pnl_usd"] for t in trades])
            equity_curve = 10000 + cumulative_pnl  # Assumindo $10k inicial
            max_drawdown = calculate_max_drawdown(equity_curve.tolist())
            
            # Métricas de duração
            avg_trade_duration = np.mean([t["duration_minutes"] for t in trades])
            
            # Métricas por símbolo
            symbols_performance = {}
            for symbol in set(t["symbol"] for t in trades):
                symbol_trades = [t for t in trades if t["symbol"] == symbol]
                symbol_pnl = sum(t["pnl_usd"] for t in symbol_trades)
                symbol_win_rate = len([t for t in symbol_trades if t["is_winner"]]) / len(symbol_trades)
                
                symbols_performance[symbol] = {
                    "trades": len(symbol_trades),
                    "pnl": symbol_pnl,
                    "win_rate": symbol_win_rate
                }
            
            # Métricas por estratégia
            strategies_performance = {}
            for trade in trades:
                for strategy in trade.get("strategies_used", []):
                    if strategy not in strategies_performance:
                        strategies_performance[strategy] = {
                            "trades": 0,
                            "pnl": 0,
                            "wins": 0
                        }
                    
                    strategies_performance[strategy]["trades"] += 1
                    strategies_performance[strategy]["pnl"] += trade["pnl_usd"]
                    if trade["is_winner"]:
                        strategies_performance[strategy]["wins"] += 1
            
            # Calcular win rate por estratégia
            for strategy in strategies_performance:
                perf = strategies_performance[strategy]
                perf["win_rate"] = perf["wins"] / perf["trades"] if perf["trades"] > 0 else 0
            
            # Métricas de consistência
            daily_pnl = self.calculate_daily_pnl(trades)
            winning_days = len([pnl for pnl in daily_pnl if pnl > 0])
            total_days = len(daily_pnl)
            daily_win_rate = winning_days / total_days if total_days > 0 else 0
            
            # Consecutive wins/losses
            max_consecutive_wins = self.calculate_max_consecutive(trades, True)
            max_consecutive_losses = self.calculate_max_consecutive(trades, False)
            
            metrics = {
                "total_trades": total_trades,
                "win_rate": round(win_rate, 4),
                "total_pnl": round(total_pnl, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "profit_factor": round(profit_factor, 2),
                "sharpe_ratio": round(sharpe_ratio, 2),
                "max_drawdown": round(max_drawdown, 4),
                "avg_trade_duration": round(avg_trade_duration, 1),
                "gross_profit": round(gross_profit, 2),
                "gross_loss": round(gross_loss, 2),
                "daily_win_rate": round(daily_win_rate, 4),
                "max_consecutive_wins": max_consecutive_wins,
                "max_consecutive_losses": max_consecutive_losses,
                "symbols_performance": symbols_performance,
                "strategies_performance": strategies_performance,
                "daily_pnl": daily_pnl,
                "calculation_timestamp": datetime.now().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            self.handle_error(e, "calculate_trading_metrics")
            return {"error": str(e)}
    
    def calculate_daily_pnl(self, trades: List[Dict]) -> List[float]:
        """Calcula P&L diário"""
        try:
            daily_pnl = {}
            
            for trade in trades:
                try:
                    trade_date = datetime.fromisoformat(trade["timestamp"].replace('Z', '+00:00')).date()
                    if trade_date not in daily_pnl:
                        daily_pnl[trade_date] = 0
                    daily_pnl[trade_date] += trade["pnl_usd"]
                except:
                    continue
            
            return list(daily_pnl.values())
            
        except Exception as e:
            self.handle_error(e, "calculate_daily_pnl")
            return []
    
    def calculate_max_consecutive(self, trades: List[Dict], winners: bool) -> int:
        """Calcula máximo de trades consecutivos (ganhos ou perdas)"""
        try:
            max_consecutive = 0
            current_consecutive = 0
            
            for trade in trades:
                if trade["is_winner"] == winners:
                    current_consecutive += 1
                    max_consecutive = max(max_consecutive, current_consecutive)
                else:
                    current_consecutive = 0
            
            return max_consecutive
            
        except Exception as e:
            self.handle_error(e, "calculate_max_consecutive")
            return 0
    
    def analyze_market_conditions(self, signals: List[Dict]) -> Dict:
        """
        Analisa condições de mercado baseado nos sinais
        
        Args:
            signals: Lista de sinais
            
        Returns:
            Dict: Análise das condições de mercado
        """
        try:
            if not signals:
                return {"status": "no_data"}
            
            # Análise de volatilidade
            prices = [s.get("price", 0) for s in signals if s.get("price")]
            if prices:
                price_changes = [abs(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                avg_volatility = np.mean(price_changes) if price_changes else 0
            else:
                avg_volatility = 0
            
            # Análise de direção do mercado
            buy_signals = len([s for s in signals if s.get("signal") == "BUY"])
            sell_signals = len([s for s in signals if s.get("signal") == "SELL"])
            hold_signals = len([s for s in signals if s.get("signal") == "HOLD"])
            
            total_signals = len(signals)
            
            if buy_signals > sell_signals * 1.5:
                market_bias = "bullish"
            elif sell_signals > buy_signals * 1.5:
                market_bias = "bearish"
            else:
                market_bias = "neutral"
            
            # Análise de confiança média
            confidences = [s.get("confidence", 0) for s in signals]
            avg_confidence = np.mean(confidences) if confidences else 0
            
            # Análise por estratégia
            strategy_activity = {}
            for signal in signals:
                for individual in signal.get("individual_signals", []):
                    strategy = individual.get("strategy", "unknown")
                    if strategy not in strategy_activity:
                        strategy_activity[strategy] = {"signals": 0, "avg_confidence": 0}
                    
                    strategy_activity[strategy]["signals"] += 1
                    strategy_activity[strategy]["avg_confidence"] += individual.get("confidence", 0)
            
            # Calcular médias
            for strategy in strategy_activity:
                count = strategy_activity[strategy]["signals"]
                if count > 0:
                    strategy_activity[strategy]["avg_confidence"] /= count
            
            # Classificar condições de mercado
            if avg_volatility > 0.02:
                market_condition = "high_volatility"
            elif avg_volatility < 0.005:
                market_condition = "low_volatility"
            else:
                market_condition = "normal"
            
            analysis = {
                "market_bias": market_bias,
                "market_condition": market_condition,
                "avg_volatility": round(avg_volatility, 4),
                "avg_confidence": round(avg_confidence, 3),
                "signal_distribution": {
                    "buy": buy_signals,
                    "sell": sell_signals,
                    "hold": hold_signals,
                    "total": total_signals
                },
                "strategy_activity": strategy_activity,
                "analysis_period": len(signals),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            self.handle_error(e, "analyze_market_conditions")
            return {"status": "error", "message": str(e)}
    
    def generate_html_report(self, metrics: Dict, market_analysis: Dict) -> str:
        """
        Gera relatório HTML detalhado
        
        Args:
            metrics: Métricas de trading
            market_analysis: Análise de mercado
            
        Returns:
            str: HTML do relatório
        """
        try:
            html_template = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Performance - Sistema de Scalping</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            border-left: 4px solid #667eea;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .positive {{ color: #28a745; }}
        .negative {{ color: #dc3545; }}
        .neutral {{ color: #6c757d; }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .table th, .table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .table th {{
            background-color: #f8f9fa;
            font-weight: 600;
        }}
        .progress-bar {{
            background-color: #e9ecef;
            border-radius: 4px;
            height: 20px;
            overflow: hidden;
            margin: 5px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #28a745, #20c997);
            transition: width 0.3s ease;
        }}
        .alert {{
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .alert-success {{ background-color: #d4edda; border-left: 4px solid #28a745; }}
        .alert-warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; }}
        .alert-danger {{ background-color: #f8d7da; border-left: 4px solid #dc3545; }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Relatório de Performance</h1>
            <p>Sistema de Scalping Automatizado - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        </div>
        
        <div class="content">
            <!-- Métricas Principais -->
            <div class="section">
                <h2>📈 Métricas Principais</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value {'positive' if metrics.get('total_pnl', 0) > 0 else 'negative'}">
                            ${metrics.get('total_pnl', 0):,.2f}
                        </div>
                        <div class="metric-label">P&L Total</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value {'positive' if metrics.get('win_rate', 0) > 0.6 else 'negative'}">
                            {metrics.get('win_rate', 0):.1%}
                        </div>
                        <div class="metric-label">Win Rate</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">
                            {metrics.get('total_trades', 0)}
                        </div>
                        <div class="metric-label">Total de Trades</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value {'positive' if metrics.get('profit_factor', 0) > 1.5 else 'negative'}">
                            {metrics.get('profit_factor', 0):.2f}
                        </div>
                        <div class="metric-label">Profit Factor</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value {'positive' if metrics.get('sharpe_ratio', 0) > 1 else 'negative'}">
                            {metrics.get('sharpe_ratio', 0):.2f}
                        </div>
                        <div class="metric-label">Sharpe Ratio</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value {'positive' if metrics.get('max_drawdown', 0) < 0.05 else 'negative'}">
                            {metrics.get('max_drawdown', 0):.1%}
                        </div>
                        <div class="metric-label">Max Drawdown</div>
                    </div>
                </div>
            </div>
            
            <!-- Performance por Símbolo -->
            <div class="section">
                <h2>💱 Performance por Símbolo</h2>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Símbolo</th>
                            <th>Trades</th>
                            <th>P&L</th>
                            <th>Win Rate</th>
                            <th>Performance</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # Adicionar dados de símbolos
            symbols_perf = metrics.get('symbols_performance', {})
            for symbol, perf in symbols_perf.items():
                win_rate = perf.get('win_rate', 0)
                pnl = perf.get('pnl', 0)
                trades = perf.get('trades', 0)
                
                pnl_class = 'positive' if pnl > 0 else 'negative'
                win_rate_class = 'positive' if win_rate > 0.6 else 'negative'
                
                html_template += f"""
                        <tr>
                            <td><strong>{symbol}</strong></td>
                            <td>{trades}</td>
                            <td class="{pnl_class}">${pnl:,.2f}</td>
                            <td class="{win_rate_class}">{win_rate:.1%}</td>
                            <td>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {min(100, win_rate * 100):.0f}%"></div>
                                </div>
                            </td>
                        </tr>
                """
            
            html_template += """
                    </tbody>
                </table>
            </div>
            
            <!-- Performance por Estratégia -->
            <div class="section">
                <h2>🎯 Performance por Estratégia</h2>
                <table class="table">
                    <thead>
                        <tr>
                            <th>Estratégia</th>
                            <th>Trades</th>
                            <th>P&L</th>
                            <th>Win Rate</th>
                            <th>Performance</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            # Adicionar dados de estratégias
            strategies_perf = metrics.get('strategies_performance', {})
            for strategy, perf in strategies_perf.items():
                win_rate = perf.get('win_rate', 0)
                pnl = perf.get('pnl', 0)
                trades = perf.get('trades', 0)
                
                pnl_class = 'positive' if pnl > 0 else 'negative'
                win_rate_class = 'positive' if win_rate > 0.6 else 'negative'
                
                html_template += f"""
                        <tr>
                            <td><strong>{strategy.replace('_', ' ').title()}</strong></td>
                            <td>{trades}</td>
                            <td class="{pnl_class}">${pnl:,.2f}</td>
                            <td class="{win_rate_class}">{win_rate:.1%}</td>
                            <td>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: {min(100, win_rate * 100):.0f}%"></div>
                                </div>
                            </td>
                        </tr>
                """
            
            # Análise de mercado
            market_bias = market_analysis.get('market_bias', 'neutral')
            market_condition = market_analysis.get('market_condition', 'normal')
            avg_volatility = market_analysis.get('avg_volatility', 0)
            
            bias_class = 'positive' if market_bias == 'bullish' else 'negative' if market_bias == 'bearish' else 'neutral'
            
            html_template += f"""
                    </tbody>
                </table>
            </div>
            
            <!-- Análise de Mercado -->
            <div class="section">
                <h2>🌍 Análise de Mercado</h2>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value {bias_class}">
                            {market_bias.title()}
                        </div>
                        <div class="metric-label">Tendência do Mercado</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">
                            {market_condition.replace('_', ' ').title()}
                        </div>
                        <div class="metric-label">Condição do Mercado</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value neutral">
                            {avg_volatility:.2%}
                        </div>
                        <div class="metric-label">Volatilidade Média</div>
                    </div>
                </div>
            </div>
            
            <!-- Alertas e Recomendações -->
            <div class="section">
                <h2>⚠️ Alertas e Recomendações</h2>
            """
            
            # Adicionar alertas baseados nas métricas
            if metrics.get('win_rate', 0) < 0.5:
                html_template += """
                <div class="alert alert-danger">
                    <strong>⚠️ Win Rate Baixo:</strong> Win rate abaixo de 50%. Considere revisar estratégias ou ajustar parâmetros.
                </div>
                """
            
            if metrics.get('max_drawdown', 0) > 0.1:
                html_template += """
                <div class="alert alert-danger">
                    <strong>🚨 Drawdown Alto:</strong> Drawdown máximo acima de 10%. Revisar gestão de risco urgentemente.
                </div>
                """
            
            if metrics.get('profit_factor', 0) < 1.2:
                html_template += """
                <div class="alert alert-warning">
                    <strong>📊 Profit Factor Baixo:</strong> Profit factor abaixo de 1.2. Otimizar relação risco/retorno.
                </div>
                """
            
            if metrics.get('total_trades', 0) < 10:
                html_template += """
                <div class="alert alert-warning">
                    <strong>📈 Poucos Trades:</strong> Número baixo de trades pode indicar sinais muito restritivos.
                </div>
                """
            
            html_template += f"""
            </div>
        </div>
        
        <div class="footer">
            <p>Relatório gerado automaticamente pelo PerformanceAgent</p>
            <p>Sistema de Scalping Automatizado - Manus AI</p>
        </div>
    </div>
</body>
</html>
            """
            
            return html_template
            
        except Exception as e:
            self.handle_error(e, "generate_html_report")
            return f"<html><body><h1>Erro ao gerar relatório: {e}</h1></body></html>"
    
    def save_html_report(self, html_content: str) -> str:
        """
        Salva relatório HTML em arquivo
        
        Args:
            html_content: Conteúdo HTML
            
        Returns:
            str: Caminho do arquivo salvo
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"performance_report_{timestamp}.html"
            filepath = Path("data/reports") / filename
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Relatório HTML salvo: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.handle_error(e, "save_html_report")
            return ""
    
    def analyze_performance(self) -> Dict:
        """
        Executa análise completa de performance
        
        Returns:
            Dict: Análise consolidada de performance
        """
        try:
            # Carregar dados para diferentes períodos
            short_term_data = self.load_trading_data(self.analysis_periods["short_term"])
            medium_term_data = self.load_trading_data(self.analysis_periods["medium_term"])
            long_term_data = self.load_trading_data(self.analysis_periods["long_term"])
            
            # Simular trades e calcular métricas
            short_term_trades = self.simulate_trade_results(short_term_data["signals"])
            medium_term_trades = self.simulate_trade_results(medium_term_data["signals"])
            long_term_trades = self.simulate_trade_results(long_term_data["signals"])
            
            short_term_metrics = self.calculate_trading_metrics(short_term_trades)
            medium_term_metrics = self.calculate_trading_metrics(medium_term_trades)
            long_term_metrics = self.calculate_trading_metrics(long_term_trades)
            
            # Análise de mercado
            market_analysis = self.analyze_market_conditions(medium_term_data["signals"])
            
            # Consolidar análise
            performance_analysis = {
                "short_term": {
                    "period_hours": self.analysis_periods["short_term"],
                    "metrics": short_term_metrics,
                    "trades_count": len(short_term_trades)
                },
                "medium_term": {
                    "period_hours": self.analysis_periods["medium_term"],
                    "metrics": medium_term_metrics,
                    "trades_count": len(medium_term_trades)
                },
                "long_term": {
                    "period_hours": self.analysis_periods["long_term"],
                    "metrics": long_term_metrics,
                    "trades_count": len(long_term_trades)
                },
                "market_analysis": market_analysis,
                "system_health": self.assess_system_health(medium_term_metrics),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            # Gerar e salvar relatório HTML
            html_report = self.generate_html_report(medium_term_metrics, market_analysis)
            report_path = self.save_html_report(html_report)
            performance_analysis["html_report_path"] = report_path
            
            return performance_analysis
            
        except Exception as e:
            self.handle_error(e, "analyze_performance")
            return {"status": "error", "message": str(e)}
    
    def assess_system_health(self, metrics: Dict) -> Dict:
        """
        Avalia saúde geral do sistema baseado nas métricas
        
        Args:
            metrics: Métricas de trading
            
        Returns:
            Dict: Avaliação da saúde do sistema
        """
        try:
            health_score = 0
            max_score = 100
            issues = []
            recommendations = []
            
            # Avaliar win rate (30 pontos)
            win_rate = metrics.get('win_rate', 0)
            if win_rate >= 0.6:
                health_score += 30
            elif win_rate >= 0.5:
                health_score += 20
                issues.append("Win rate moderado")
                recommendations.append("Otimizar estratégias para melhorar win rate")
            else:
                health_score += 10
                issues.append("Win rate baixo")
                recommendations.append("Revisar estratégias urgentemente")
            
            # Avaliar profit factor (25 pontos)
            profit_factor = metrics.get('profit_factor', 0)
            if profit_factor >= 2.0:
                health_score += 25
            elif profit_factor >= 1.5:
                health_score += 20
            elif profit_factor >= 1.2:
                health_score += 15
                issues.append("Profit factor moderado")
                recommendations.append("Melhorar relação risco/retorno")
            else:
                health_score += 5
                issues.append("Profit factor baixo")
                recommendations.append("Revisar gestão de risco")
            
            # Avaliar drawdown (25 pontos)
            max_drawdown = metrics.get('max_drawdown', 0)
            if max_drawdown <= 0.05:
                health_score += 25
            elif max_drawdown <= 0.08:
                health_score += 20
            elif max_drawdown <= 0.12:
                health_score += 15
                issues.append("Drawdown moderado")
                recommendations.append("Monitorar gestão de risco")
            else:
                health_score += 5
                issues.append("Drawdown alto")
                recommendations.append("Reduzir tamanhos de posição")
            
            # Avaliar Sharpe ratio (20 pontos)
            sharpe_ratio = metrics.get('sharpe_ratio', 0)
            if sharpe_ratio >= 2.0:
                health_score += 20
            elif sharpe_ratio >= 1.5:
                health_score += 15
            elif sharpe_ratio >= 1.0:
                health_score += 10
                issues.append("Sharpe ratio moderado")
            else:
                health_score += 5
                issues.append("Sharpe ratio baixo")
                recommendations.append("Melhorar consistência dos retornos")
            
            # Determinar status geral
            if health_score >= 80:
                status = "excellent"
                status_text = "Excelente"
            elif health_score >= 60:
                status = "good"
                status_text = "Bom"
            elif health_score >= 40:
                status = "fair"
                status_text = "Regular"
            else:
                status = "poor"
                status_text = "Ruim"
            
            return {
                "health_score": health_score,
                "max_score": max_score,
                "status": status,
                "status_text": status_text,
                "issues": issues,
                "recommendations": recommendations,
                "assessment_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.handle_error(e, "assess_system_health")
            return {"status": "error", "message": str(e)}
    
    def suggest_improvements(self) -> List[Dict]:
        """
        Sugere melhorias baseadas na análise de performance
        
        Returns:
            List[Dict]: Lista de sugestões de melhoria
        """
        try:
            suggestions = []
            
            # Carregar dados recentes para análise
            recent_data = self.load_trading_data(168)  # 1 semana
            trades = self.simulate_trade_results(recent_data["signals"])
            metrics = self.calculate_trading_metrics(trades)
            
            if not metrics or metrics.get("error"):
                return suggestions
            
            # Sugestão 1: Melhorar win rate se baixo
            win_rate = metrics.get('win_rate', 0)
            if win_rate < 0.55:
                suggestions.append({
                    "type": SuggestionType.STRATEGY_OPTIMIZATION,
                    "priority": "high",
                    "current_metrics": {"win_rate": win_rate},
                    "suggested_changes": {
                        "file": "config/trading_config.json",
                        "line_range": [1, 50],
                        "parameter": "strategies.*.min_confidence",
                        "current_value": 0.6,
                        "suggested_value": 0.75,
                        "reason": f"Win rate {win_rate:.1%} baixo - aumentar threshold de confiança mínima",
                        "expected_improvement": "Filtrar sinais fracos e melhorar qualidade dos trades"
                    }
                })
            
            # Sugestão 2: Otimizar estratégia com pior performance
            strategies_perf = metrics.get('strategies_performance', {})
            if strategies_perf:
                worst_strategy = min(strategies_perf.items(), key=lambda x: x[1].get('win_rate', 0))
                strategy_name, strategy_perf = worst_strategy
                
                if strategy_perf.get('win_rate', 0) < 0.4 and strategy_perf.get('trades', 0) > 5:
                    suggestions.append({
                        "type": SuggestionType.STRATEGY_OPTIMIZATION,
                        "priority": "high",
                        "current_metrics": strategy_perf,
                        "suggested_changes": {
                            "file": "config/trading_config.json",
                            "line_range": [1, 50],
                            "parameter": f"strategies.{strategy_name}.enabled",
                            "current_value": True,
                            "suggested_value": False,
                            "reason": f"Estratégia {strategy_name} com performance ruim ({strategy_perf['win_rate']:.1%}) - desabilitar temporariamente",
                            "expected_improvement": "Melhorar performance geral removendo estratégia problemática"
                        }
                    })
            
            # Sugestão 3: Ajustar gestão de risco se drawdown alto
            max_drawdown = metrics.get('max_drawdown', 0)
            if max_drawdown > 0.08:
                suggestions.append({
                    "type": SuggestionType.RISK_REDUCTION,
                    "priority": "critical",
                    "current_metrics": {"max_drawdown": max_drawdown},
                    "suggested_changes": {
                        "file": "config/risk_parameters.json",
                        "line_range": [8, 12],
                        "parameter": "position_sizing.base_risk_per_trade",
                        "current_value": 0.02,
                        "suggested_value": 0.01,
                        "reason": f"Drawdown máximo {max_drawdown:.1%} muito alto - reduzir risco por trade",
                        "expected_improvement": "Reduzir volatilidade do portfolio e proteger capital"
                    }
                })
            
            # Sugestão 4: Otimizar duração média de trades
            avg_duration = metrics.get('avg_trade_duration', 0)
            if avg_duration > 25:  # Mais de 25 minutos para scalping
                suggestions.append({
                    "type": SuggestionType.PARAMETER_ADJUSTMENT,
                    "priority": "medium",
                    "current_metrics": {"avg_trade_duration": avg_duration},
                    "suggested_changes": {
                        "file": "config/trading_config.json",
                        "line_range": [20, 25],
                        "parameter": "risk_management.take_profit_percentage",
                        "current_value": 0.010,
                        "suggested_value": 0.008,
                        "reason": f"Duração média {avg_duration:.1f}min alta para scalping - reduzir take profit",
                        "expected_improvement": "Reduzir tempo de exposição e aumentar frequência de trades"
                    }
                })
            
            return suggestions
            
        except Exception as e:
            self.handle_error(e, "suggest_improvements")
            return []
    
    def run(self):
        """
        Executa ciclo principal do agente de performance
        """
        self.logger.info("Iniciando análise de performance")
        
        try:
            # Executar análise completa
            performance_analysis = self.analyze_performance()
            
            # Salvar métricas
            self.save_metrics(performance_analysis)
            
            # Gerar sugestões de melhoria
            suggestions = self.suggest_improvements()
            for suggestion in suggestions:
                self.save_suggestion(suggestion)
            
            # Adicionar ao histórico de relatórios
            report_summary = {
                "timestamp": datetime.now().isoformat(),
                "html_report_path": performance_analysis.get("html_report_path", ""),
                "system_health": performance_analysis.get("system_health", {}),
                "suggestions_count": len(suggestions)
            }
            
            self.report_history.append(report_summary)
            
            # Manter histórico limitado
            if len(self.report_history) > 100:
                self.report_history = self.report_history[-100:]
            
            # Log de conclusão
            health_status = performance_analysis.get("system_health", {}).get("status_text", "Desconhecido")
            medium_term_trades = performance_analysis.get("medium_term", {}).get("trades_count", 0)
            
            self.logger.info(
                f"Análise de performance concluída - "
                f"Saúde do sistema: {health_status}, "
                f"Trades analisados: {medium_term_trades}, "
                f"Sugestões geradas: {len(suggestions)}"
            )
            
        except Exception as e:
            self.handle_error(e, "run")
            raise

def main():
    """Função principal para execução standalone"""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Modo de teste
        agent = PerformanceAgent()
        print("Executando teste do PerformanceAgent...")
        agent.run()
        print("Teste concluído com sucesso!")
    else:
        # Execução normal
        agent = PerformanceAgent()
        agent.run_with_error_handling()

if __name__ == "__main__":
    main()

