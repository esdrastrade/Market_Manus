#!/usr/bin/env python3
"""
Risk Management Agent para Sistema de Scalping Automatizado
Responsável por monitoramento de riscos, position sizing e proteção de capital
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

class RiskManagementAgent(BaseAgent):
    """
    Agente de Gestão de Risco
    
    Responsabilidades:
    - Monitoramento contínuo de drawdown
    - Cálculo de position sizing dinâmico
    - Implementação de stop losses dinâmicos
    - Controles de circuit breaker
    - Alertas automáticos para situações de risco elevado
    - Sugestões de ajuste de parâmetros de risco
    
    Frequência: A cada 1 minuto via PowerShell scheduled task
    """
    
    def __init__(self):
        super().__init__("RiskManagementAgent", "config/risk_parameters.json")
        
        # Carregar configuração de trading também
        self.trading_config = self.load_trading_config()
        
        # Histórico de portfolio para cálculo de drawdown
        self.portfolio_history = []
        self.max_history_size = 10000  # Manter últimos 10k valores
        
        # Estado atual do sistema de risco
        self.risk_state = {
            "current_drawdown": 0.0,
            "max_drawdown_today": 0.0,
            "consecutive_losses": 0,
            "daily_pnl": 0.0,
            "weekly_pnl": 0.0,
            "monthly_pnl": 0.0,
            "circuit_breaker_active": False,
            "last_position_size_adjustment": None
        }
        
        # Alertas ativos
        self.active_alerts = []
        
        self.logger.info("RiskManagementAgent inicializado")
    
    def load_trading_config(self) -> Dict:
        """Carrega configuração de trading"""
        try:
            with open("config/trading_config.json", 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self.get_default_config()["trading"]
    
    def load_portfolio_history(self) -> List[float]:
        """
        Carrega histórico de portfolio de arquivo
        
        Returns:
            List[float]: Valores históricos do portfolio
        """
        try:
            portfolio_file = "data/portfolio_history.json"
            if os.path.exists(portfolio_file):
                with open(portfolio_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("values", [])
        except (json.JSONDecodeError, FileNotFoundError):
            pass
        
        # Valor inicial padrão
        return [10000.0]  # $10,000 inicial
    
    def save_portfolio_history(self):
        """Salva histórico de portfolio em arquivo"""
        try:
            portfolio_file = "data/portfolio_history.json"
            data = {
                "values": self.portfolio_history[-self.max_history_size:],
                "last_update": datetime.now().isoformat(),
                "current_value": self.portfolio_history[-1] if self.portfolio_history else 0
            }
            
            with open(portfolio_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.handle_error(e, "save_portfolio_history")
    
    def simulate_portfolio_value(self) -> float:
        """
        Simula valor atual do portfolio
        
        Em produção, conectaria com API da exchange para obter saldo real
        Para demonstração, simula baseado em sinais e performance
        
        Returns:
            float: Valor atual simulado do portfolio
        """
        try:
            # Valor base
            if not self.portfolio_history:
                self.portfolio_history = self.load_portfolio_history()
            
            current_value = self.portfolio_history[-1] if self.portfolio_history else 10000.0
            
            # Simular mudança baseada em sinais recentes
            recent_signals = self.get_performance_window_data("signals", 10)
            
            if recent_signals:
                # Calcular mudança baseada na confiança dos sinais
                total_confidence = sum(s.get('confidence', 0) for s in recent_signals if s.get('signal') != 'HOLD')
                signal_count = len([s for s in recent_signals if s.get('signal') != 'HOLD'])
                
                if signal_count > 0:
                    avg_confidence = total_confidence / signal_count
                    # Simular retorno baseado na confiança (simplificado)
                    daily_return = (avg_confidence - 0.5) * 0.02  # ±2% baseado na confiança
                    
                    # Adicionar ruído realista
                    noise = np.random.normal(0, 0.005)  # 0.5% de ruído
                    total_change = daily_return + noise
                    
                    new_value = current_value * (1 + total_change)
                else:
                    # Sem sinais, pequena variação aleatória
                    new_value = current_value * (1 + np.random.normal(0, 0.001))
            else:
                # Sem dados, manter valor atual com pequena variação
                new_value = current_value * (1 + np.random.normal(0, 0.001))
            
            return max(0, new_value)  # Não pode ser negativo
            
        except Exception as e:
            self.handle_error(e, "simulate_portfolio_value")
            return self.portfolio_history[-1] if self.portfolio_history else 10000.0
    
    def calculate_drawdown(self) -> Tuple[float, float]:
        """
        Calcula drawdown atual e máximo
        
        Returns:
            Tuple[float, float]: (drawdown_atual, drawdown_máximo)
        """
        try:
            if len(self.portfolio_history) < 2:
                return 0.0, 0.0
            
            values = np.array(self.portfolio_history)
            
            # Calcular peak running (máximo até cada ponto)
            peak = np.maximum.accumulate(values)
            
            # Calcular drawdown em cada ponto
            drawdown = (peak - values) / peak
            
            current_drawdown = drawdown[-1]
            max_drawdown = np.max(drawdown)
            
            return float(current_drawdown), float(max_drawdown)
            
        except Exception as e:
            self.handle_error(e, "calculate_drawdown")
            return 0.0, 0.0
    
    def calculate_position_size(self, signal_confidence: float, symbol: str, current_price: float) -> Dict:
        """
        Calcula tamanho da posição baseado no risco
        
        Args:
            signal_confidence: Confiança do sinal (0.0 a 1.0)
            symbol: Par de trading
            current_price: Preço atual do ativo
            
        Returns:
            Dict: Informações sobre position sizing
        """
        try:
            account_balance = self.portfolio_history[-1] if self.portfolio_history else 10000.0
            
            # Parâmetros base
            base_risk = self.config["position_sizing"]["base_risk_per_trade"]
            min_size_usd = self.config["position_sizing"]["min_position_size_usd"]
            max_size_usd = self.config["position_sizing"]["max_position_size_usd"]
            
            # Ajuste por confiança do sinal
            confidence_multiplier = signal_confidence if self.config["position_sizing"]["confidence_multiplier"] else 1.0
            
            # Ajuste por drawdown atual
            current_drawdown, _ = self.calculate_drawdown()
            if self.config["position_sizing"]["drawdown_adjustment"]:
                if current_drawdown > 0.05:  # 5%
                    drawdown_multiplier = 0.5  # Reduzir pela metade
                elif current_drawdown > 0.03:  # 3%
                    drawdown_multiplier = 0.75  # Reduzir 25%
                else:
                    drawdown_multiplier = 1.0
            else:
                drawdown_multiplier = 1.0
            
            # Ajuste por volatilidade (simplificado)
            volatility_multiplier = 1.0
            if self.config["position_sizing"]["volatility_adjustment"]:
                # Em produção, calcularia volatilidade real do ativo
                # Para demonstração, usar valor fixo
                volatility_multiplier = 0.9  # Reduzir 10% por volatilidade
            
            # Calcular tamanho final
            adjusted_risk = base_risk * confidence_multiplier * drawdown_multiplier * volatility_multiplier
            position_size_usd = account_balance * adjusted_risk
            
            # Aplicar limites
            position_size_usd = max(min_size_usd, min(max_size_usd, position_size_usd))
            
            # Calcular quantidade em unidades do ativo
            position_quantity = position_size_usd / current_price
            
            result = {
                "position_size_usd": round(position_size_usd, 2),
                "position_quantity": round(position_quantity, 6),
                "risk_percentage": round(adjusted_risk * 100, 2),
                "adjustments": {
                    "base_risk": base_risk,
                    "confidence_multiplier": confidence_multiplier,
                    "drawdown_multiplier": drawdown_multiplier,
                    "volatility_multiplier": volatility_multiplier
                },
                "account_balance": account_balance,
                "current_drawdown": current_drawdown
            }
            
            self.logger.debug(f"Position size calculado: ${position_size_usd:.2f} ({adjusted_risk:.2%} risk)")
            
            return result
            
        except Exception as e:
            self.handle_error(e, "calculate_position_size")
            return {
                "position_size_usd": min_size_usd,
                "position_quantity": min_size_usd / current_price,
                "risk_percentage": 1.0,
                "error": str(e)
            }
    
    def check_risk_limits(self) -> List[Dict]:
        """
        Verifica todos os limites de risco configurados
        
        Returns:
            List[Dict]: Lista de alertas de risco
        """
        alerts = []
        
        try:
            current_drawdown, max_drawdown = self.calculate_drawdown()
            
            # Verificar drawdown
            max_allowed_drawdown = self.config["risk_limits"]["max_drawdown"]
            drawdown_warning = self.config["alerts"]["drawdown_warning_threshold"]
            drawdown_critical = self.config["alerts"]["drawdown_critical_threshold"]
            
            if current_drawdown > drawdown_critical:
                alerts.append({
                    "type": "drawdown_critical",
                    "severity": AlertSeverity.CRITICAL,
                    "current_value": current_drawdown,
                    "limit": max_allowed_drawdown,
                    "message": f"CRÍTICO: Drawdown {current_drawdown:.1%} próximo ao limite {max_allowed_drawdown:.1%}",
                    "action_required": "Considerar pausar trading ou reduzir drasticamente position sizes",
                    "timestamp": datetime.now().isoformat()
                })
            elif current_drawdown > drawdown_warning:
                alerts.append({
                    "type": "drawdown_warning",
                    "severity": AlertSeverity.HIGH,
                    "current_value": current_drawdown,
                    "limit": max_allowed_drawdown,
                    "message": f"ALERTA: Drawdown {current_drawdown:.1%} se aproximando do limite {max_allowed_drawdown:.1%}",
                    "action_required": "Monitorar de perto e considerar reduzir riscos",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Verificar perdas consecutivas
            consecutive_losses = self.risk_state["consecutive_losses"]
            max_consecutive = self.config["risk_limits"]["max_consecutive_losses"]
            loss_warning = self.config["alerts"]["loss_streak_warning"]
            
            if consecutive_losses >= max_consecutive:
                alerts.append({
                    "type": "consecutive_losses_critical",
                    "severity": AlertSeverity.CRITICAL,
                    "current_value": consecutive_losses,
                    "limit": max_consecutive,
                    "message": f"CRÍTICO: {consecutive_losses} perdas consecutivas (limite: {max_consecutive})",
                    "action_required": "Pausar trading e revisar estratégias",
                    "timestamp": datetime.now().isoformat()
                })
            elif consecutive_losses >= loss_warning:
                alerts.append({
                    "type": "consecutive_losses_warning",
                    "severity": AlertSeverity.HIGH,
                    "current_value": consecutive_losses,
                    "limit": max_consecutive,
                    "message": f"ALERTA: {consecutive_losses} perdas consecutivas se aproximando do limite",
                    "action_required": "Revisar estratégias e considerar reduzir riscos",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Verificar P&L diário
            daily_loss_limit = self.config["risk_limits"]["daily_loss_limit"]
            daily_pnl = self.risk_state["daily_pnl"]
            
            if daily_pnl < -daily_loss_limit:
                alerts.append({
                    "type": "daily_loss_limit",
                    "severity": AlertSeverity.CRITICAL,
                    "current_value": daily_pnl,
                    "limit": -daily_loss_limit,
                    "message": f"CRÍTICO: Perda diária {daily_pnl:.1%} excede limite {daily_loss_limit:.1%}",
                    "action_required": "Pausar trading pelo resto do dia",
                    "timestamp": datetime.now().isoformat()
                })
            
            return alerts
            
        except Exception as e:
            self.handle_error(e, "check_risk_limits")
            return []
    
    def update_risk_state(self):
        """Atualiza estado atual do sistema de risco"""
        try:
            # Atualizar drawdown
            current_drawdown, max_drawdown = self.calculate_drawdown()
            self.risk_state["current_drawdown"] = current_drawdown
            
            # Atualizar máximo drawdown do dia
            if current_drawdown > self.risk_state["max_drawdown_today"]:
                self.risk_state["max_drawdown_today"] = current_drawdown
            
            # Simular P&L (em produção, calcularia baseado em trades reais)
            if len(self.portfolio_history) >= 2:
                daily_change = (self.portfolio_history[-1] - self.portfolio_history[-2]) / self.portfolio_history[-2]
                self.risk_state["daily_pnl"] = daily_change
            
            # Verificar circuit breaker
            circuit_breaker_config = self.config["circuit_breakers"]
            if circuit_breaker_config["enabled"]:
                should_activate = (
                    current_drawdown > circuit_breaker_config["drawdown_pause_threshold"] or
                    self.risk_state["consecutive_losses"] >= circuit_breaker_config["loss_streak_pause_threshold"]
                )
                
                if should_activate and not self.risk_state["circuit_breaker_active"]:
                    self.risk_state["circuit_breaker_active"] = True
                    self.logger.warning("Circuit breaker ativado!")
                    
                    # Gerar alerta crítico
                    self.save_alert({
                        "type": "circuit_breaker_activated",
                        "severity": AlertSeverity.CRITICAL,
                        "message": "Circuit breaker ativado - trading pausado automaticamente",
                        "reason": f"Drawdown: {current_drawdown:.1%}, Perdas consecutivas: {self.risk_state['consecutive_losses']}",
                        "action_required": "Sistema pausado automaticamente. Revisar estratégias antes de reativar."
                    })
            
        except Exception as e:
            self.handle_error(e, "update_risk_state")
    
    def calculate_dynamic_stop_loss(self, entry_price: float, signal_type: str, symbol: str) -> Dict:
        """
        Calcula stop loss dinâmico baseado em ATR e volatilidade
        
        Args:
            entry_price: Preço de entrada
            signal_type: 'BUY' ou 'SELL'
            symbol: Par de trading
            
        Returns:
            Dict: Informações sobre stop loss
        """
        try:
            # Parâmetros base
            default_percentage = self.config["stop_loss"]["default_percentage"]
            min_percentage = self.config["stop_loss"]["min_percentage"]
            max_percentage = self.config["stop_loss"]["max_percentage"]
            atr_multiplier = self.config["stop_loss"]["atr_multiplier"]
            
            # Em produção, obteria ATR real do mercado
            # Para demonstração, simular ATR baseado na volatilidade típica
            simulated_atr = entry_price * 0.003  # 0.3% do preço como ATR típico
            
            # Calcular stop loss baseado em ATR
            if self.config["stop_loss"]["dynamic_adjustment"]:
                atr_based_percentage = (simulated_atr * atr_multiplier) / entry_price
                stop_loss_percentage = max(min_percentage, min(max_percentage, atr_based_percentage))
            else:
                stop_loss_percentage = default_percentage
            
            # Calcular preços de stop loss
            if signal_type == 'BUY':
                stop_loss_price = entry_price * (1 - stop_loss_percentage)
            else:  # SELL
                stop_loss_price = entry_price * (1 + stop_loss_percentage)
            
            result = {
                "stop_loss_price": round(stop_loss_price, 2),
                "stop_loss_percentage": round(stop_loss_percentage * 100, 2),
                "atr_value": round(simulated_atr, 2),
                "method": "dynamic" if self.config["stop_loss"]["dynamic_adjustment"] else "fixed",
                "entry_price": entry_price,
                "signal_type": signal_type
            }
            
            return result
            
        except Exception as e:
            self.handle_error(e, "calculate_dynamic_stop_loss")
            return {
                "stop_loss_price": entry_price * (0.995 if signal_type == 'BUY' else 1.005),
                "stop_loss_percentage": 0.5,
                "error": str(e)
            }
    
    def analyze_performance(self) -> Dict:
        """
        Analisa métricas de risco e performance
        
        Returns:
            Dict: Métricas de risco atualizadas
        """
        try:
            current_drawdown, max_drawdown = self.calculate_drawdown()
            
            # Estatísticas do portfolio
            portfolio_stats = self.calculate_basic_stats(self.portfolio_history[-100:])  # Últimos 100 valores
            
            # Verificar alertas ativos
            active_alerts = self.check_risk_limits()
            
            performance = {
                "current_drawdown": round(current_drawdown, 4),
                "max_drawdown": round(max_drawdown, 4),
                "max_allowed_drawdown": self.config["risk_limits"]["max_drawdown"],
                "portfolio_value": self.portfolio_history[-1] if self.portfolio_history else 0,
                "portfolio_stats": portfolio_stats,
                "risk_state": self.risk_state,
                "active_alerts": len(active_alerts),
                "alert_details": active_alerts,
                "circuit_breaker_active": self.risk_state["circuit_breaker_active"],
                "risk_limits": self.config["risk_limits"],
                "last_update": datetime.now().isoformat()
            }
            
            return performance
            
        except Exception as e:
            self.handle_error(e, "analyze_performance")
            return {"status": "error", "message": str(e)}
    
    def suggest_improvements(self) -> List[Dict]:
        """
        Sugere ajustes de parâmetros de risco baseados na performance
        
        Returns:
            List[Dict]: Lista de sugestões de melhoria
        """
        try:
            suggestions = []
            performance = self.analyze_performance()
            
            current_drawdown = performance.get("current_drawdown", 0)
            
            # Sugestão 1: Reduzir risco se drawdown alto
            if current_drawdown > 0.05:  # 5%
                current_risk = self.config["position_sizing"]["base_risk_per_trade"]
                suggested_risk = max(0.005, current_risk * 0.5)  # Reduzir pela metade, mín 0.5%
                
                suggestions.append({
                    "type": SuggestionType.RISK_REDUCTION,
                    "priority": "high",
                    "current_metrics": {"current_drawdown": current_drawdown},
                    "suggested_changes": {
                        "file": "config/risk_parameters.json",
                        "line_range": [8, 12],
                        "parameter": "position_sizing.base_risk_per_trade",
                        "current_value": current_risk,
                        "suggested_value": suggested_risk,
                        "reason": f"Drawdown atual {current_drawdown:.1%} alto - reduzir risco por trade",
                        "expected_improvement": "Reduzir velocidade de perda durante período adverso"
                    }
                })
            
            # Sugestão 2: Ajustar stop loss se muitas perdas consecutivas
            if self.risk_state["consecutive_losses"] >= 3:
                current_stop = self.config["stop_loss"]["default_percentage"]
                suggested_stop = max(0.002, current_stop * 0.8)  # Reduzir 20%
                
                suggestions.append({
                    "type": SuggestionType.RISK_REDUCTION,
                    "priority": "medium",
                    "current_metrics": {"consecutive_losses": self.risk_state["consecutive_losses"]},
                    "suggested_changes": {
                        "file": "config/risk_parameters.json",
                        "line_range": [20, 25],
                        "parameter": "stop_loss.default_percentage",
                        "current_value": current_stop,
                        "suggested_value": suggested_stop,
                        "reason": f"{self.risk_state['consecutive_losses']} perdas consecutivas - reduzir stop loss",
                        "expected_improvement": "Reduzir tamanho das perdas individuais"
                    }
                })
            
            # Sugestão 3: Ativar circuit breaker se não estiver ativo
            if not self.config["circuit_breakers"]["enabled"] and current_drawdown > 0.03:
                suggestions.append({
                    "type": SuggestionType.SYSTEM_MAINTENANCE,
                    "priority": "high",
                    "current_metrics": {"current_drawdown": current_drawdown},
                    "suggested_changes": {
                        "file": "config/risk_parameters.json",
                        "line_range": [45, 50],
                        "parameter": "circuit_breakers.enabled",
                        "current_value": False,
                        "suggested_value": True,
                        "reason": f"Drawdown {current_drawdown:.1%} - ativar circuit breaker para proteção",
                        "expected_improvement": "Proteção automática contra perdas excessivas"
                    }
                })
            
            # Sugestão 4: Ajustar threshold de drawdown se muito conservador
            portfolio_stats = performance.get("portfolio_stats", {})
            if (portfolio_stats.get("std", 0) < 0.01 and  # Baixa volatilidade
                current_drawdown < 0.01 and  # Drawdown muito baixo
                len(self.portfolio_history) > 100):  # Dados suficientes
                
                current_threshold = self.config["alerts"]["drawdown_warning_threshold"]
                suggested_threshold = min(0.08, current_threshold + 0.01)  # Aumentar 1%
                
                suggestions.append({
                    "type": SuggestionType.PARAMETER_ADJUSTMENT,
                    "priority": "low",
                    "current_metrics": portfolio_stats,
                    "suggested_changes": {
                        "file": "config/risk_parameters.json",
                        "line_range": [55, 60],
                        "parameter": "alerts.drawdown_warning_threshold",
                        "current_value": current_threshold,
                        "suggested_value": suggested_threshold,
                        "reason": "Sistema muito conservador - ajustar threshold de alerta",
                        "expected_improvement": "Permitir maior utilização do capital disponível"
                    }
                })
            
            return suggestions
            
        except Exception as e:
            self.handle_error(e, "suggest_improvements")
            return []
    
    def run(self):
        """
        Executa ciclo principal do agente de gestão de risco
        """
        self.logger.info("Iniciando ciclo de gestão de risco")
        
        try:
            # Carregar histórico se necessário
            if not self.portfolio_history:
                self.portfolio_history = self.load_portfolio_history()
            
            # Simular valor atual do portfolio
            current_value = self.simulate_portfolio_value()
            self.portfolio_history.append(current_value)
            
            # Manter tamanho do histórico controlado
            if len(self.portfolio_history) > self.max_history_size:
                self.portfolio_history = self.portfolio_history[-self.max_history_size:]
            
            # Salvar histórico atualizado
            self.save_portfolio_history()
            
            # Atualizar estado de risco
            self.update_risk_state()
            
            # Verificar limites de risco
            alerts = self.check_risk_limits()
            
            # Processar alertas
            for alert in alerts:
                self.save_alert(alert)
                
                if alert["severity"] == AlertSeverity.CRITICAL:
                    self.logger.critical(f"ALERTA CRÍTICO: {alert['message']}")
                elif alert["severity"] == AlertSeverity.HIGH:
                    self.logger.warning(f"ALERTA: {alert['message']}")
            
            # Analisar performance e gerar sugestões
            performance = self.analyze_performance()
            self.save_metrics(performance)
            
            suggestions = self.suggest_improvements()
            for suggestion in suggestions:
                self.save_suggestion(suggestion)
            
            # Log de status
            current_drawdown = self.risk_state["current_drawdown"]
            self.logger.info(
                f"Ciclo de risco concluído - Portfolio: ${current_value:.2f}, "
                f"Drawdown: {current_drawdown:.2%}, Alertas: {len(alerts)}"
            )
            
        except Exception as e:
            self.handle_error(e, "run")
            raise

def main():
    """Função principal para execução standalone"""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Modo de teste
        agent = RiskManagementAgent()
        print("Executando teste do RiskManagementAgent...")
        agent.run()
        print("Teste concluído com sucesso!")
    else:
        # Execução normal
        agent = RiskManagementAgent()
        agent.run_with_error_handling()

if __name__ == "__main__":
    main()

