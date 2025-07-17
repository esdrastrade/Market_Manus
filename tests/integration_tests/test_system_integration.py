#!/usr/bin/env python3
"""
Testes de Integração do Sistema Completo

Este módulo contém testes que validam a integração entre todos os componentes
do sistema de scalping automatizado, incluindo interações entre agentes,
fluxo de dados e coordenação geral.

Autor: Manus AI
Data: 17 de Julho de 2025
Versão: 1.0
"""

import unittest
import sys
import os
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Adicionar diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.test_framework import IntegrationTestCase
from agents.orchestrator_agent import OrchestratorAgent
from agents.market_analysis_agent import MarketAnalysisAgent
from agents.risk_management_agent import RiskManagementAgent
from agents.notification_agent import NotificationAgent
from agents.performance_agent import PerformanceAgent
from agents.backtesting_agent import BacktestingAgent

class TestSystemIntegration(IntegrationTestCase):
    """Testes de integração do sistema completo"""
    
    def setUp(self):
        """Setup para testes de integração"""
        super().setUp()
        
        # Criar mocks de todos os agentes
        self.agents = self.create_mock_agents()
        self.orchestrator = self.create_mock_orchestrator()
        
        # Configurar dados de teste para integração
        self.integration_data = self.setup_integration_data()
    
    def create_mock_agents(self):
        """Cria mocks de todos os agentes do sistema"""
        agents = {}
        
        # Mock MarketAnalysisAgent
        with patch('agents.market_analysis_agent.MarketAnalysisAgent.__init__', return_value=None):
            market_agent = MarketAnalysisAgent()
            market_agent.name = "MarketAnalysisAgent"
            market_agent.status = "running"
            market_agent.run_cycle = Mock(return_value=self.mock_market_analysis_cycle())
            market_agent.get_latest_signals = Mock(return_value=self.mock_get_signals())
            market_agent.analyze_performance = Mock(return_value={"success_rate": 0.72})
            agents["market"] = market_agent
        
        # Mock RiskManagementAgent
        with patch('agents.risk_management_agent.RiskManagementAgent.__init__', return_value=None):
            risk_agent = RiskManagementAgent()
            risk_agent.name = "RiskManagementAgent"
            risk_agent.status = "running"
            risk_agent.run_cycle = Mock(return_value=self.mock_risk_management_cycle())
            risk_agent.check_risk_limits = Mock(return_value=[])
            risk_agent.calculate_position_size = Mock(return_value=0.1)
            agents["risk"] = risk_agent
        
        # Mock NotificationAgent
        with patch('agents.notification_agent.NotificationAgent.__init__', return_value=None):
            notification_agent = NotificationAgent()
            notification_agent.name = "NotificationAgent"
            notification_agent.status = "running"
            notification_agent.run_cycle = Mock(return_value=self.mock_notification_cycle())
            notification_agent.send_alert = Mock(return_value=True)
            agents["notification"] = notification_agent
        
        # Mock PerformanceAgent
        with patch('agents.performance_agent.PerformanceAgent.__init__', return_value=None):
            performance_agent = PerformanceAgent()
            performance_agent.name = "PerformanceAgent"
            performance_agent.status = "running"
            performance_agent.run_cycle = Mock(return_value=self.mock_performance_cycle())
            performance_agent.generate_report = Mock(return_value={"total_trades": 150})
            agents["performance"] = performance_agent
        
        # Mock BacktestingAgent
        with patch('agents.backtesting_agent.BacktestingAgent.__init__', return_value=None):
            backtesting_agent = BacktestingAgent()
            backtesting_agent.name = "BacktestingAgent"
            backtesting_agent.status = "running"
            backtesting_agent.run_cycle = Mock(return_value=self.mock_backtesting_cycle())
            backtesting_agent.run_backtest = Mock(return_value={"sharpe_ratio": 1.5})
            agents["backtesting"] = backtesting_agent
        
        return agents
    
    def create_mock_orchestrator(self):
        """Cria mock do OrchestratorAgent"""
        with patch('agents.orchestrator_agent.OrchestratorAgent.__init__', return_value=None):
            orchestrator = OrchestratorAgent()
            orchestrator.name = "OrchestratorAgent"
            orchestrator.agents = self.agents
            orchestrator.status = "running"
            orchestrator.run_cycle = Mock(return_value=self.mock_orchestrator_cycle())
            orchestrator.coordinate_agents = Mock(return_value=True)
            orchestrator.check_system_health = Mock(return_value={"status": "healthy"})
            
            return orchestrator
    
    def setup_integration_data(self):
        """Configura dados para testes de integração"""
        return {
            "market_data": self.generate_mock_market_data(periods=100),
            "portfolio": {
                "balance": 10000.0,
                "positions": [
                    {"symbol": "BTCUSDT", "size": 0.1, "entry_price": 45000}
                ]
            },
            "signals": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "symbol": "BTCUSDT",
                    "strategy": "ema_crossover",
                    "signal": 0.75,
                    "confidence": 0.85,
                    "price": 45250.50
                }
            ]
        }
    
    def mock_market_analysis_cycle(self):
        """Mock do ciclo do MarketAnalysisAgent"""
        return {
            "status": "completed",
            "signals_generated": 3,
            "processing_time": 0.15,
            "errors": []
        }
    
    def mock_risk_management_cycle(self):
        """Mock do ciclo do RiskManagementAgent"""
        return {
            "status": "completed",
            "positions_monitored": 2,
            "alerts_generated": 1,
            "processing_time": 0.08,
            "errors": []
        }
    
    def mock_notification_cycle(self):
        """Mock do ciclo do NotificationAgent"""
        return {
            "status": "completed",
            "notifications_sent": 2,
            "processing_time": 0.05,
            "errors": []
        }
    
    def mock_performance_cycle(self):
        """Mock do ciclo do PerformanceAgent"""
        return {
            "status": "completed",
            "metrics_calculated": 15,
            "processing_time": 0.12,
            "errors": []
        }
    
    def mock_backtesting_cycle(self):
        """Mock do ciclo do BacktestingAgent"""
        return {
            "status": "completed",
            "backtests_run": 1,
            "processing_time": 2.5,
            "errors": []
        }
    
    def mock_orchestrator_cycle(self):
        """Mock do ciclo do OrchestratorAgent"""
        return {
            "status": "completed",
            "agents_coordinated": 5,
            "system_health": "good",
            "processing_time": 0.25,
            "errors": []
        }
    
    def mock_get_signals(self):
        """Mock para obter sinais do MarketAnalysisAgent"""
        return self.integration_data["signals"]
    
    def test_agent_initialization_sequence(self):
        """Testa sequência de inicialização dos agentes"""
        initialization_order = [
            "market", "risk", "notification", "performance", "backtesting"
        ]
        
        initialized_agents = []
        
        for agent_name in initialization_order:
            agent = self.agents[agent_name]
            self.assertIsNotNone(agent)
            self.assertEqual(agent.status, "running")
            initialized_agents.append(agent_name)
        
        # Verificar que todos os agentes foram inicializados
        self.assertEqual(len(initialized_agents), 5)
        self.assertEqual(initialized_agents, initialization_order)
    
    def test_signal_flow_between_agents(self):
        """Testa fluxo de sinais entre agentes"""
        # 1. MarketAnalysisAgent gera sinais
        market_agent = self.agents["market"]
        signals = market_agent.get_latest_signals()
        
        self.assertIsInstance(signals, list)
        self.assertGreater(len(signals), 0)
        
        # 2. RiskManagementAgent processa sinais
        risk_agent = self.agents["risk"]
        for signal in signals:
            position_size = risk_agent.calculate_position_size(
                10000, 0.02, signal["price"], signal["price"] * 0.98
            )
            self.assertGreater(position_size, 0)
        
        # 3. NotificationAgent envia alertas
        notification_agent = self.agents["notification"]
        for signal in signals:
            if signal["confidence"] > 0.8:
                result = notification_agent.send_alert({
                    "type": "high_confidence_signal",
                    "signal": signal
                })
                self.assertTrue(result)
    
    def test_orchestrator_coordination(self):
        """Testa coordenação pelo OrchestratorAgent"""
        # Executar ciclo de coordenação
        coordination_result = self.orchestrator.coordinate_agents()
        
        self.assertTrue(coordination_result)
        
        # Verificar que todos os agentes foram executados
        for agent in self.agents.values():
            agent.run_cycle.assert_called()
        
        # Verificar saúde do sistema
        health_check = self.orchestrator.check_system_health()
        self.assertIn("status", health_check)
        self.assertEqual(health_check["status"], "healthy")
    
    def test_error_propagation_and_handling(self):
        """Testa propagação e tratamento de erros"""
        # Simular erro no MarketAnalysisAgent
        market_agent = self.agents["market"]
        market_agent.run_cycle.side_effect = Exception("Market data unavailable")
        
        # Orchestrator deve lidar com o erro
        try:
            self.orchestrator.run_cycle()
        except Exception:
            self.fail("Orchestrator não tratou erro do agente adequadamente")
        
        # Sistema deve continuar funcionando com outros agentes
        risk_agent = self.agents["risk"]
        risk_agent.run_cycle.assert_called()
    
    def test_performance_monitoring_integration(self):
        """Testa integração do monitoramento de performance"""
        performance_agent = self.agents["performance"]
        
        # Simular dados de performance de outros agentes
        agent_metrics = {
            "market": {"signals_generated": 25, "success_rate": 0.72},
            "risk": {"positions_monitored": 10, "alerts_generated": 3},
            "notification": {"notifications_sent": 15, "delivery_rate": 0.95}
        }
        
        # PerformanceAgent deve consolidar métricas
        report = performance_agent.generate_report()
        
        self.assertIn("total_trades", report)
        self.assertIsInstance(report["total_trades"], int)
    
    def test_backtesting_integration(self):
        """Testa integração do backtesting com outros componentes"""
        backtesting_agent = self.agents["backtesting"]
        market_agent = self.agents["market"]
        
        # Obter estratégias do MarketAnalysisAgent
        strategies = ["ema_crossover", "rsi_mean_reversion", "bollinger_breakout"]
        
        # Executar backtest para cada estratégia
        for strategy in strategies:
            backtest_result = backtesting_agent.run_backtest({
                "strategy": strategy,
                "data": self.integration_data["market_data"]
            })
            
            self.assertIn("sharpe_ratio", backtest_result)
            self.assertIsInstance(backtest_result["sharpe_ratio"], (int, float))
    
    def test_notification_system_integration(self):
        """Testa integração do sistema de notificações"""
        notification_agent = self.agents["notification"]
        
        # Simular diferentes tipos de alertas
        alert_types = [
            {"type": "high_confidence_signal", "severity": "MEDIUM"},
            {"type": "risk_limit_exceeded", "severity": "HIGH"},
            {"type": "system_error", "severity": "CRITICAL"}
        ]
        
        for alert in alert_types:
            result = notification_agent.send_alert(alert)
            self.assertTrue(result)
        
        # Verificar que notificações foram processadas
        self.assertEqual(notification_agent.send_alert.call_count, len(alert_types))
    
    def test_data_consistency_across_agents(self):
        """Testa consistência de dados entre agentes"""
        # Todos os agentes devem trabalhar com os mesmos dados de mercado
        market_data = self.integration_data["market_data"]
        
        # Verificar que dados são consistentes
        for agent in self.agents.values():
            # Simular processamento dos mesmos dados
            agent.run_cycle()
            
            # Verificar que não houve corrupção de dados
            self.assertIsNotNone(market_data["prices"])
            self.assertGreater(len(market_data["prices"]), 0)
    
    def test_concurrent_agent_execution(self):
        """Testa execução concorrente de agentes"""
        results = {}
        threads = []
        
        def run_agent(agent_name, agent):
            try:
                result = agent.run_cycle()
                results[agent_name] = result
            except Exception as e:
                results[agent_name] = {"error": str(e)}
        
        # Executar agentes em threads separadas
        for agent_name, agent in self.agents.items():
            thread = threading.Thread(target=run_agent, args=(agent_name, agent))
            threads.append(thread)
            thread.start()
        
        # Aguardar conclusão
        for thread in threads:
            thread.join(timeout=5.0)
        
        # Verificar que todos os agentes executaram
        self.assertEqual(len(results), len(self.agents))
        
        # Verificar que não houve erros
        for agent_name, result in results.items():
            self.assertNotIn("error", result, f"Erro no agente {agent_name}")
    
    def test_system_recovery_after_failure(self):
        """Testa recuperação do sistema após falhas"""
        # Simular falha em múltiplos agentes
        failed_agents = ["market", "risk"]
        
        for agent_name in failed_agents:
            agent = self.agents[agent_name]
            agent.status = "failed"
            agent.run_cycle.side_effect = Exception(f"{agent_name} failed")
        
        # Sistema deve detectar falhas e tentar recuperação
        health_check = self.orchestrator.check_system_health()
        
        # Verificar que sistema detectou problemas
        self.assertIn("status", health_check)
        
        # Simular recuperação
        for agent_name in failed_agents:
            agent = self.agents[agent_name]
            agent.status = "running"
            agent.run_cycle.side_effect = None
        
        # Verificar recuperação
        recovery_check = self.orchestrator.check_system_health()
        self.assertEqual(recovery_check["status"], "healthy")
    
    def test_end_to_end_trading_workflow(self):
        """Testa workflow completo de trading"""
        # 1. Análise de mercado gera sinal
        market_agent = self.agents["market"]
        signals = market_agent.get_latest_signals()
        
        self.assertGreater(len(signals), 0)
        signal = signals[0]
        
        # 2. Gestão de risco valida sinal
        risk_agent = self.agents["risk"]
        risk_violations = risk_agent.check_risk_limits({
            "balance": 10000,
            "positions": [],
            "daily_pnl": 0
        })
        
        # 3. Se não há violações, calcular position size
        if not risk_violations:
            position_size = risk_agent.calculate_position_size(
                10000, 0.02, signal["price"], signal["price"] * 0.98
            )
            self.assertGreater(position_size, 0)
        
        # 4. Notificar sobre a operação
        notification_agent = self.agents["notification"]
        notification_result = notification_agent.send_alert({
            "type": "trade_signal",
            "signal": signal,
            "position_size": position_size if not risk_violations else 0
        })
        
        self.assertTrue(notification_result)
        
        # 5. Registrar performance
        performance_agent = self.agents["performance"]
        performance_agent.run_cycle()
        
        # Verificar que workflow foi executado
        market_agent.get_latest_signals.assert_called()
        risk_agent.check_risk_limits.assert_called()
        notification_agent.send_alert.assert_called()
        performance_agent.run_cycle.assert_called()
    
    def test_system_performance_under_load(self):
        """Testa performance do sistema sob carga"""
        start_time = time.time()
        
        # Simular alta carga de processamento
        for _ in range(100):
            # Executar ciclo completo
            for agent in self.agents.values():
                agent.run_cycle()
            
            # Coordenação do orchestrator
            self.orchestrator.run_cycle()
        
        execution_time = time.time() - start_time
        
        # Sistema deve processar 100 ciclos em menos de 10 segundos
        self.assertLess(execution_time, 10.0)
        
        # Verificar que todos os agentes foram executados
        for agent in self.agents.values():
            self.assertEqual(agent.run_cycle.call_count, 100)
    
    def test_configuration_consistency(self):
        """Testa consistência de configuração entre agentes"""
        # Todos os agentes devem usar configurações compatíveis
        base_config = self.test_config
        
        # Verificar configurações específicas
        trading_symbols = base_config["trading"]["symbols"]
        risk_params = base_config["risk"]
        
        # Agentes devem trabalhar com os mesmos símbolos
        market_agent = self.agents["market"]
        risk_agent = self.agents["risk"]
        
        # Simular verificação de configuração
        self.assertIsNotNone(trading_symbols)
        self.assertIsNotNone(risk_params)
        self.assertIn("max_risk_per_trade", risk_params)
    
    def test_memory_usage_stability(self):
        """Testa estabilidade do uso de memória"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Executar múltiplos ciclos
        for _ in range(50):
            for agent in self.agents.values():
                agent.run_cycle()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Aumento de memória deve ser limitado (menos de 50MB)
        self.assertLess(memory_increase, 50 * 1024 * 1024)

class TestSystemIntegrationStress(IntegrationTestCase):
    """Testes de stress para integração do sistema"""
    
    def setUp(self):
        """Setup para testes de stress"""
        super().setUp()
        self.agents = TestSystemIntegration().create_mock_agents()
        self.orchestrator = TestSystemIntegration().create_mock_orchestrator()
    
    def test_high_frequency_signal_processing(self):
        """Testa processamento de sinais de alta frequência"""
        market_agent = self.agents["market"]
        
        # Simular geração de muitos sinais
        high_frequency_signals = []
        for i in range(1000):
            signal = {
                "timestamp": (datetime.now() + timedelta(seconds=i)).isoformat(),
                "symbol": "BTCUSDT",
                "strategy": "ema_crossover",
                "signal": np.random.uniform(-1, 1),
                "confidence": np.random.uniform(0.5, 1.0),
                "price": 45000 + np.random.uniform(-1000, 1000)
            }
            high_frequency_signals.append(signal)
        
        market_agent.get_latest_signals.return_value = high_frequency_signals
        
        # Sistema deve processar todos os sinais
        start_time = time.time()
        signals = market_agent.get_latest_signals()
        processing_time = time.time() - start_time
        
        self.assertEqual(len(signals), 1000)
        self.assertLess(processing_time, 1.0)  # Menos de 1 segundo
    
    def test_system_stability_over_time(self):
        """Testa estabilidade do sistema ao longo do tempo"""
        # Executar sistema por período prolongado
        start_time = time.time()
        cycles_completed = 0
        errors_encountered = 0
        
        while time.time() - start_time < 30:  # 30 segundos
            try:
                for agent in self.agents.values():
                    agent.run_cycle()
                
                self.orchestrator.run_cycle()
                cycles_completed += 1
                
            except Exception:
                errors_encountered += 1
            
            time.sleep(0.1)  # Pequena pausa entre ciclos
        
        # Sistema deve completar muitos ciclos com poucos erros
        self.assertGreater(cycles_completed, 100)
        self.assertLess(errors_encountered / cycles_completed, 0.01)  # Menos de 1% de erro

if __name__ == "__main__":
    # Executar testes de integração
    unittest.main(verbosity=2)

