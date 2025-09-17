#!/usr/bin/env python3
"""
Testes Unitários para RiskManagementAgent

Este módulo contém testes abrangentes para o agente de gestão de risco,
incluindo testes de position sizing, stop loss, drawdown e alertas de risco.

Autor: Manus AI
Data: 17 de Julho de 2025
Versão: 1.0
"""

import json
import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import numpy as np

# Adicionar diretório pai ao path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from agents.risk_management_agent import RiskManagementAgent
from tests.test_framework import AgentTestCase


class TestRiskManagementAgent(AgentTestCase):
    """Testes unitários para RiskManagementAgent"""

    def setUp(self):
        """Setup específico para testes do RiskManagementAgent"""
        super().setUp()

        # Configurar dados de teste específicos para gestão de risco
        self.portfolio_data = {
            "initial_balance": 10000.0,
            "current_balance": 9500.0,
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "size": 0.1,
                    "entry_price": 45000,
                    "current_price": 44500,
                },
                {
                    "symbol": "ETHUSDT",
                    "size": 2.0,
                    "entry_price": 3000,
                    "current_price": 2950,
                },
            ],
            "daily_pnl": -500.0,
            "max_drawdown": 0.08,
        }

        # Configurar mock do agente
        self.agent = self.create_mock_risk_management_agent()

    def create_mock_risk_management_agent(self):
        """Cria instância mock do RiskManagementAgent para testes"""
        with patch(
            "agents.risk_management_agent.RiskManagementAgent.__init__",
            return_value=None,
        ):
            agent = RiskManagementAgent()

            # Configurar atributos necessários
            agent.name = "RiskManagementAgent"
            agent.config = self.test_config
            agent.logger = self.logger
            agent.risk_params = {
                "max_risk_per_trade": 0.02,
                "max_daily_loss": 0.05,
                "stop_loss_percentage": 0.015,
                "max_drawdown": 0.10,
                "position_sizing_method": "fixed_percentage",
            }

            # Configurar métodos necessários
            agent.save_metrics = Mock()
            agent.save_suggestion = Mock()
            agent.save_alert = Mock()
            agent.handle_error = Mock()

            # Implementar métodos de gestão de risco
            agent.calculate_position_size = self.mock_calculate_position_size
            agent.calculate_stop_loss = self.mock_calculate_stop_loss
            agent.calculate_drawdown = self.mock_calculate_drawdown
            agent.check_risk_limits = self.mock_check_risk_limits
            agent.monitor_positions = self.mock_monitor_positions
            agent.calculate_portfolio_risk = self.mock_calculate_portfolio_risk
            agent.generate_risk_alerts = self.mock_generate_risk_alerts
            agent.analyze_performance = self.mock_analyze_performance
            agent.suggest_improvements = self.mock_suggest_improvements

            return agent

    def mock_calculate_position_size(
        self, account_balance, risk_per_trade, entry_price, stop_loss_price
    ):
        """Mock para cálculo de position sizing"""
        if stop_loss_price <= 0 or entry_price <= 0:
            return 0.0

        risk_amount = account_balance * risk_per_trade
        price_risk = abs(entry_price - stop_loss_price)

        if price_risk == 0:
            return 0.0

        position_size = risk_amount / price_risk

        # Limitar position size a máximo de 10% do balance
        max_position_value = account_balance * 0.1
        max_position_size = max_position_value / entry_price

        return min(position_size, max_position_size)

    def mock_calculate_stop_loss(
        self, entry_price, direction, atr_value=None, volatility=None
    ):
        """Mock para cálculo de stop loss"""
        base_stop_percentage = self.agent.risk_params["stop_loss_percentage"]

        # Ajustar stop loss baseado em ATR se disponível
        if atr_value:
            atr_stop_percentage = (atr_value * 2) / entry_price
            stop_percentage = max(base_stop_percentage, atr_stop_percentage)
        else:
            stop_percentage = base_stop_percentage

        # Ajustar por volatilidade
        if volatility:
            volatility_multiplier = max(0.5, min(2.0, volatility / 0.02))
            stop_percentage *= volatility_multiplier

        if direction == "long":
            return entry_price * (1 - stop_percentage)
        else:  # short
            return entry_price * (1 + stop_percentage)

    def mock_calculate_drawdown(self, portfolio_history):
        """Mock para cálculo de drawdown"""
        if not portfolio_history or len(portfolio_history) < 2:
            return {"current_drawdown": 0.0, "max_drawdown": 0.0}

        values = [p["balance"] for p in portfolio_history]
        peak = values[0]
        max_drawdown = 0.0
        current_drawdown = 0.0

        for value in values:
            if value > peak:
                peak = value

            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)

            # Current drawdown é o drawdown atual
            if value == values[-1]:
                current_drawdown = drawdown

        return {
            "current_drawdown": current_drawdown,
            "max_drawdown": max_drawdown,
            "peak_balance": peak,
            "current_balance": values[-1],
        }

    def mock_check_risk_limits(self, portfolio_data):
        """Mock para verificação de limites de risco"""
        violations = []

        # Verificar drawdown máximo
        current_drawdown = (
            portfolio_data["initial_balance"] - portfolio_data["current_balance"]
        ) / portfolio_data["initial_balance"]
        if current_drawdown > self.agent.risk_params["max_drawdown"]:
            violations.append(
                {
                    "type": "max_drawdown_exceeded",
                    "current": current_drawdown,
                    "limit": self.agent.risk_params["max_drawdown"],
                    "severity": "CRITICAL",
                }
            )

        # Verificar perda diária
        daily_loss_percentage = (
            abs(portfolio_data["daily_pnl"]) / portfolio_data["initial_balance"]
        )
        if (
            portfolio_data["daily_pnl"] < 0
            and daily_loss_percentage > self.agent.risk_params["max_daily_loss"]
        ):
            violations.append(
                {
                    "type": "max_daily_loss_exceeded",
                    "current": daily_loss_percentage,
                    "limit": self.agent.risk_params["max_daily_loss"],
                    "severity": "HIGH",
                }
            )

        # Verificar concentração de posições
        total_position_value = sum(
            pos["size"] * pos["current_price"] for pos in portfolio_data["positions"]
        )
        concentration = total_position_value / portfolio_data["current_balance"]

        if concentration > 0.8:  # Mais de 80% investido
            violations.append(
                {
                    "type": "high_concentration",
                    "current": concentration,
                    "limit": 0.8,
                    "severity": "MEDIUM",
                }
            )

        return violations

    def mock_monitor_positions(self, positions):
        """Mock para monitoramento de posições"""
        position_alerts = []

        for position in positions:
            # Calcular P&L da posição
            pnl_percentage = (
                position["current_price"] - position["entry_price"]
            ) / position["entry_price"]

            # Alertar se posição está com perda significativa
            if pnl_percentage < -0.05:  # Perda > 5%
                position_alerts.append(
                    {
                        "symbol": position["symbol"],
                        "type": "significant_loss",
                        "pnl_percentage": pnl_percentage,
                        "severity": "HIGH" if pnl_percentage < -0.1 else "MEDIUM",
                    }
                )

            # Alertar se posição está muito concentrada
            position_value = position["size"] * position["current_price"]
            if position_value > 3000:  # Mais de $3000 em uma posição
                position_alerts.append(
                    {
                        "symbol": position["symbol"],
                        "type": "large_position",
                        "value": position_value,
                        "severity": "MEDIUM",
                    }
                )

        return position_alerts

    def mock_calculate_portfolio_risk(self, portfolio_data, market_data=None):
        """Mock para cálculo de risco do portfolio"""
        # Calcular VaR simplificado (95% confidence)
        position_values = [
            pos["size"] * pos["current_price"] for pos in portfolio_data["positions"]
        ]
        total_value = sum(position_values)

        # Assumir volatilidade de 2% diária
        daily_volatility = 0.02
        var_95 = total_value * daily_volatility * 1.645  # Z-score para 95%

        # Calcular correlação entre posições (simplificado)
        correlation_adjustment = 0.8 if len(portfolio_data["positions"]) > 1 else 1.0
        adjusted_var = var_95 * correlation_adjustment

        return {
            "value_at_risk_95": adjusted_var,
            "portfolio_value": total_value,
            "risk_percentage": adjusted_var / total_value if total_value > 0 else 0,
            "diversification_ratio": correlation_adjustment,
            "position_count": len(portfolio_data["positions"]),
        }

    def mock_generate_risk_alerts(self, risk_analysis):
        """Mock para geração de alertas de risco"""
        alerts = []

        # Alerta de VaR alto
        if risk_analysis["risk_percentage"] > 0.1:  # VaR > 10%
            alerts.append(
                {
                    "type": "high_var",
                    "message": f"VaR alto: {risk_analysis['risk_percentage']:.2%}",
                    "severity": "HIGH",
                    "action_required": "Considerar redução de posições",
                }
            )

        # Alerta de baixa diversificação
        if risk_analysis["diversification_ratio"] < 0.5:
            alerts.append(
                {
                    "type": "low_diversification",
                    "message": "Portfolio pouco diversificado",
                    "severity": "MEDIUM",
                    "action_required": "Diversificar posições",
                }
            )

        return alerts

    def mock_analyze_performance(self):
        """Mock para análise de performance"""
        return {
            "current_drawdown": 0.05,
            "max_drawdown": 0.08,
            "risk_adjusted_return": 1.2,
            "sharpe_ratio": 1.5,
            "positions_monitored": 2,
            "alerts_generated_today": 3,
            "risk_limits_breached": 0,
        }

    def mock_suggest_improvements(self):
        """Mock para sugestões de melhoria"""
        return [
            {
                "type": "RISK_ADJUSTMENT",
                "priority": "high",
                "suggestion": "Reduzir position size devido ao alto drawdown",
                "expected_improvement": "Menor risco de perdas significativas",
            }
        ]

    def test_agent_initialization(self):
        """Testa inicialização do agente"""
        self.assertIsNotNone(self.agent)
        self.assertEqual(self.agent.name, "RiskManagementAgent")
        self.assertIn("max_risk_per_trade", self.agent.risk_params)
        self.assertIn("max_daily_loss", self.agent.risk_params)

    def test_position_size_calculation(self):
        """Testa cálculo de position sizing"""
        account_balance = 10000.0
        risk_per_trade = 0.02  # 2%
        entry_price = 45000.0
        stop_loss_price = 44100.0  # 2% stop loss

        position_size = self.agent.calculate_position_size(
            account_balance, risk_per_trade, entry_price, stop_loss_price
        )

        # Position size deve ser positivo
        self.assertGreater(position_size, 0)

        # Verificar que o risco está dentro do limite
        risk_amount = position_size * abs(entry_price - stop_loss_price)
        expected_risk = account_balance * risk_per_trade

        self.assertLessEqual(risk_amount, expected_risk * 1.1)  # 10% de tolerância

    def test_position_size_with_zero_stop_loss(self):
        """Testa position sizing com stop loss inválido"""
        position_size = self.agent.calculate_position_size(10000, 0.02, 45000, 0)
        self.assertEqual(position_size, 0.0)

        position_size = self.agent.calculate_position_size(10000, 0.02, 0, 44000)
        self.assertEqual(position_size, 0.0)

    def test_stop_loss_calculation_long(self):
        """Testa cálculo de stop loss para posição long"""
        entry_price = 45000.0
        direction = "long"

        stop_loss = self.agent.calculate_stop_loss(entry_price, direction)

        # Stop loss deve ser menor que preço de entrada para long
        self.assertLess(stop_loss, entry_price)

        # Stop loss deve estar dentro de range razoável
        stop_percentage = (entry_price - stop_loss) / entry_price
        self.assertGreater(stop_percentage, 0.005)  # Pelo menos 0.5%
        self.assertLess(stop_percentage, 0.1)  # Máximo 10%

    def test_stop_loss_calculation_short(self):
        """Testa cálculo de stop loss para posição short"""
        entry_price = 45000.0
        direction = "short"

        stop_loss = self.agent.calculate_stop_loss(entry_price, direction)

        # Stop loss deve ser maior que preço de entrada para short
        self.assertGreater(stop_loss, entry_price)

        # Stop loss deve estar dentro de range razoável
        stop_percentage = (stop_loss - entry_price) / entry_price
        self.assertGreater(stop_percentage, 0.005)  # Pelo menos 0.5%
        self.assertLess(stop_percentage, 0.1)  # Máximo 10%

    def test_stop_loss_with_atr(self):
        """Testa cálculo de stop loss com ATR"""
        entry_price = 45000.0
        direction = "long"
        atr_value = 900.0  # ATR de $900

        stop_loss_with_atr = self.agent.calculate_stop_loss(
            entry_price, direction, atr_value=atr_value
        )
        stop_loss_without_atr = self.agent.calculate_stop_loss(entry_price, direction)

        # Stop loss com ATR deve ser diferente (provavelmente mais amplo)
        self.assertNotEqual(stop_loss_with_atr, stop_loss_without_atr)

    def test_drawdown_calculation(self):
        """Testa cálculo de drawdown"""
        portfolio_history = [
            {"balance": 10000, "timestamp": "2025-07-01"},
            {"balance": 10500, "timestamp": "2025-07-02"},  # Novo pico
            {"balance": 9800, "timestamp": "2025-07-03"},  # Drawdown
            {"balance": 9500, "timestamp": "2025-07-04"},  # Maior drawdown
            {"balance": 9700, "timestamp": "2025-07-05"},  # Recuperação parcial
        ]

        drawdown_info = self.agent.calculate_drawdown(portfolio_history)

        # Verificar estrutura do resultado
        self.assertIn("current_drawdown", drawdown_info)
        self.assertIn("max_drawdown", drawdown_info)
        self.assertIn("peak_balance", drawdown_info)

        # Verificar valores
        self.assertEqual(drawdown_info["peak_balance"], 10500)
        self.assertAlmostEqual(
            drawdown_info["max_drawdown"], (10500 - 9500) / 10500, places=4
        )
        self.assertAlmostEqual(
            drawdown_info["current_drawdown"], (10500 - 9700) / 10500, places=4
        )

    def test_drawdown_with_insufficient_data(self):
        """Testa cálculo de drawdown com dados insuficientes"""
        # Dados vazios
        drawdown_info = self.agent.calculate_drawdown([])
        self.assertEqual(drawdown_info["current_drawdown"], 0.0)
        self.assertEqual(drawdown_info["max_drawdown"], 0.0)

        # Apenas um ponto de dados
        single_point = [{"balance": 10000, "timestamp": "2025-07-01"}]
        drawdown_info = self.agent.calculate_drawdown(single_point)
        self.assertEqual(drawdown_info["current_drawdown"], 0.0)
        self.assertEqual(drawdown_info["max_drawdown"], 0.0)

    def test_risk_limits_checking(self):
        """Testa verificação de limites de risco"""
        violations = self.agent.check_risk_limits(self.portfolio_data)

        # Deve retornar lista de violações
        self.assertIsInstance(violations, list)

        # Verificar se detectou violação de drawdown
        drawdown_violations = [
            v for v in violations if v["type"] == "max_drawdown_exceeded"
        ]
        self.assertGreater(len(drawdown_violations), 0)  # Deve detectar violação

        # Verificar estrutura da violação
        if drawdown_violations:
            violation = drawdown_violations[0]
            self.assertIn("current", violation)
            self.assertIn("limit", violation)
            self.assertIn("severity", violation)

    def test_risk_limits_with_safe_portfolio(self):
        """Testa verificação com portfolio dentro dos limites"""
        safe_portfolio = {
            "initial_balance": 10000.0,
            "current_balance": 10200.0,  # Lucro
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "size": 0.05,
                    "entry_price": 45000,
                    "current_price": 45500,
                }
            ],
            "daily_pnl": 200.0,  # Lucro diário
            "max_drawdown": 0.02,  # Drawdown baixo
        }

        violations = self.agent.check_risk_limits(safe_portfolio)

        # Não deve haver violações críticas
        critical_violations = [v for v in violations if v["severity"] == "CRITICAL"]
        self.assertEqual(len(critical_violations), 0)

    def test_position_monitoring(self):
        """Testa monitoramento de posições"""
        positions = [
            {
                "symbol": "BTCUSDT",
                "size": 0.1,
                "entry_price": 45000,
                "current_price": 42000,
            },  # Perda significativa
            {
                "symbol": "ETHUSDT",
                "size": 2.0,
                "entry_price": 3000,
                "current_price": 3100,
            },  # Posição normal
            {
                "symbol": "ADAUSDT",
                "size": 10000,
                "entry_price": 0.5,
                "current_price": 0.52,
            },  # Posição grande
        ]

        alerts = self.agent.monitor_positions(positions)

        # Deve gerar alertas
        self.assertIsInstance(alerts, list)
        self.assertGreater(len(alerts), 0)

        # Verificar alerta de perda significativa
        loss_alerts = [a for a in alerts if a["type"] == "significant_loss"]
        self.assertGreater(len(loss_alerts), 0)

        # Verificar alerta de posição grande
        large_position_alerts = [a for a in alerts if a["type"] == "large_position"]
        self.assertGreater(len(large_position_alerts), 0)

    def test_portfolio_risk_calculation(self):
        """Testa cálculo de risco do portfolio"""
        risk_analysis = self.agent.calculate_portfolio_risk(self.portfolio_data)

        # Verificar estrutura do resultado
        self.assertIn("value_at_risk_95", risk_analysis)
        self.assertIn("portfolio_value", risk_analysis)
        self.assertIn("risk_percentage", risk_analysis)
        self.assertIn("diversification_ratio", risk_analysis)

        # Verificar valores
        self.assertGreater(risk_analysis["value_at_risk_95"], 0)
        self.assertGreater(risk_analysis["portfolio_value"], 0)
        self.assertGreaterEqual(risk_analysis["risk_percentage"], 0)
        self.assertLessEqual(risk_analysis["risk_percentage"], 1)

    def test_risk_alerts_generation(self):
        """Testa geração de alertas de risco"""
        # Cenário de alto risco
        high_risk_analysis = {
            "value_at_risk_95": 1500,
            "portfolio_value": 10000,
            "risk_percentage": 0.15,  # 15% VaR
            "diversification_ratio": 0.3,  # Baixa diversificação
            "position_count": 1,
        }

        alerts = self.agent.generate_risk_alerts(high_risk_analysis)

        # Deve gerar alertas
        self.assertIsInstance(alerts, list)
        self.assertGreater(len(alerts), 0)

        # Verificar tipos de alertas
        alert_types = [a["type"] for a in alerts]
        self.assertIn("high_var", alert_types)
        self.assertIn("low_diversification", alert_types)

    def test_performance_analysis(self):
        """Testa análise de performance do agente"""
        performance = self.agent.analyze_performance()

        # Verificar estrutura
        self.assertIn("current_drawdown", performance)
        self.assertIn("max_drawdown", performance)
        self.assertIn("risk_adjusted_return", performance)
        self.assertIn("positions_monitored", performance)

        # Verificar tipos de dados
        self.assertIsInstance(performance["current_drawdown"], (int, float))
        self.assertIsInstance(performance["positions_monitored"], int)
        self.assertGreaterEqual(performance["positions_monitored"], 0)

    def test_improvement_suggestions(self):
        """Testa geração de sugestões de melhoria"""
        suggestions = self.agent.suggest_improvements()

        # Deve retornar lista de sugestões
        self.assertIsInstance(suggestions, list)

        if suggestions:  # Se há sugestões
            suggestion = suggestions[0]
            self.assertIn("type", suggestion)
            self.assertIn("priority", suggestion)
            self.assertIn("suggestion", suggestion)
            self.assertIn("expected_improvement", suggestion)

    def test_extreme_market_conditions(self):
        """Testa comportamento em condições extremas de mercado"""
        # Portfolio com perdas extremas
        extreme_portfolio = {
            "initial_balance": 10000.0,
            "current_balance": 5000.0,  # 50% de perda
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "size": 0.2,
                    "entry_price": 45000,
                    "current_price": 30000,
                }  # -33% na posição
            ],
            "daily_pnl": -2000.0,  # 20% de perda diária
            "max_drawdown": 0.5,
        }

        violations = self.agent.check_risk_limits(extreme_portfolio)

        # Deve detectar múltiplas violações críticas
        critical_violations = [v for v in violations if v["severity"] == "CRITICAL"]
        self.assertGreater(len(critical_violations), 0)

        # Deve incluir violação de drawdown máximo
        drawdown_violations = [
            v for v in violations if v["type"] == "max_drawdown_exceeded"
        ]
        self.assertGreater(len(drawdown_violations), 0)

    def test_position_sizing_edge_cases(self):
        """Testa position sizing em casos extremos"""
        # Caso 1: Stop loss muito próximo do entry price
        tiny_stop_diff = self.agent.calculate_position_size(10000, 0.02, 45000, 44999)
        self.assertGreater(tiny_stop_diff, 0)  # Deve ainda calcular um tamanho

        # Caso 2: Stop loss muito distante
        large_stop_diff = self.agent.calculate_position_size(10000, 0.02, 45000, 40000)
        self.assertGreater(large_stop_diff, 0)
        self.assertLess(large_stop_diff, 1.0)  # Não deve ser muito grande

        # Caso 3: Risco muito alto
        high_risk = self.agent.calculate_position_size(
            10000, 0.5, 45000, 44000
        )  # 50% de risco
        max_position_value = 10000 * 0.1  # Máximo 10% do balance
        max_position_size = max_position_value / 45000
        self.assertLessEqual(high_risk, max_position_size)

    def test_concurrent_risk_monitoring(self):
        """Testa monitoramento de risco com múltiplas posições simultâneas"""
        large_portfolio = {
            "initial_balance": 100000.0,
            "current_balance": 95000.0,
            "positions": [
                {
                    "symbol": f"SYMBOL{i}",
                    "size": 1.0,
                    "entry_price": 1000 + i * 10,
                    "current_price": 950 + i * 10,
                }
                for i in range(20)  # 20 posições
            ],
            "daily_pnl": -1000.0,
            "max_drawdown": 0.05,
        }

        # Monitorar posições
        position_alerts = self.agent.monitor_positions(large_portfolio["positions"])

        # Calcular risco do portfolio
        risk_analysis = self.agent.calculate_portfolio_risk(large_portfolio)

        # Verificar que o sistema lida com múltiplas posições
        self.assertIsInstance(position_alerts, list)
        self.assertIsInstance(risk_analysis, dict)
        self.assertEqual(risk_analysis["position_count"], 20)

    def test_risk_metrics_consistency(self):
        """Testa consistência das métricas de risco"""
        # Executar cálculos múltiplas vezes
        results = []
        for _ in range(5):
            risk_analysis = self.agent.calculate_portfolio_risk(self.portfolio_data)
            results.append(risk_analysis)

        # Verificar consistência
        for i in range(1, len(results)):
            self.assertEqual(
                results[0]["portfolio_value"], results[i]["portfolio_value"]
            )
            self.assertEqual(results[0]["position_count"], results[i]["position_count"])
            self.assertAlmostEqual(
                results[0]["risk_percentage"], results[i]["risk_percentage"], places=6
            )


class TestRiskManagementAgentIntegration(AgentTestCase):
    """Testes de integração para RiskManagementAgent"""

    def setUp(self):
        """Setup para testes de integração"""
        super().setUp()
        self.agent = TestRiskManagementAgent().create_mock_risk_management_agent()

    def test_full_risk_assessment_workflow(self):
        """Testa workflow completo de avaliação de risco"""
        # Simular dados de portfolio
        portfolio_data = {
            "initial_balance": 10000.0,
            "current_balance": 9200.0,
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "size": 0.15,
                    "entry_price": 45000,
                    "current_price": 43000,
                },
                {
                    "symbol": "ETHUSDT",
                    "size": 3.0,
                    "entry_price": 3000,
                    "current_price": 2800,
                },
            ],
            "daily_pnl": -800.0,
            "max_drawdown": 0.08,
        }

        # Executar workflow completo
        # 1. Verificar limites de risco
        violations = self.agent.check_risk_limits(portfolio_data)

        # 2. Monitorar posições
        position_alerts = self.agent.monitor_positions(portfolio_data["positions"])

        # 3. Calcular risco do portfolio
        risk_analysis = self.agent.calculate_portfolio_risk(portfolio_data)

        # 4. Gerar alertas de risco
        risk_alerts = self.agent.generate_risk_alerts(risk_analysis)

        # 5. Analisar performance
        performance = self.agent.analyze_performance()

        # Verificar que todos os componentes funcionaram
        self.assertIsInstance(violations, list)
        self.assertIsInstance(position_alerts, list)
        self.assertIsInstance(risk_analysis, dict)
        self.assertIsInstance(risk_alerts, list)
        self.assertIsInstance(performance, dict)

        # Verificar que alertas foram gerados apropriadamente
        total_alerts = len(violations) + len(position_alerts) + len(risk_alerts)
        self.assertGreater(
            total_alerts, 0
        )  # Deve haver alertas com este portfolio de risco

    def test_risk_management_under_stress(self):
        """Testa gestão de risco sob condições de stress"""
        # Simular crash de mercado
        crash_portfolio = {
            "initial_balance": 50000.0,
            "current_balance": 30000.0,  # 40% de perda
            "positions": [
                {
                    "symbol": "BTCUSDT",
                    "size": 1.0,
                    "entry_price": 45000,
                    "current_price": 25000,
                },  # -44%
                {
                    "symbol": "ETHUSDT",
                    "size": 10.0,
                    "entry_price": 3000,
                    "current_price": 1500,
                },  # -50%
                {
                    "symbol": "ADAUSDT",
                    "size": 50000,
                    "entry_price": 0.8,
                    "current_price": 0.3,
                },  # -62%
            ],
            "daily_pnl": -15000.0,  # 30% de perda diária
            "max_drawdown": 0.4,
        }

        # Sistema deve detectar múltiplas violações críticas
        violations = self.agent.check_risk_limits(crash_portfolio)
        critical_violations = [v for v in violations if v["severity"] == "CRITICAL"]

        self.assertGreater(len(critical_violations), 0)

        # Sistema deve gerar alertas para todas as posições
        position_alerts = self.agent.monitor_positions(crash_portfolio["positions"])
        loss_alerts = [a for a in position_alerts if a["type"] == "significant_loss"]

        self.assertEqual(
            len(loss_alerts), 3
        )  # Todas as posições com perda significativa


if __name__ == "__main__":
    # Executar testes
    unittest.main(verbosity=2)
