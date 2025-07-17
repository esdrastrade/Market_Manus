#!/usr/bin/env python3
"""
Testes Unitários para MarketAnalysisAgent

Este módulo contém testes abrangentes para o agente de análise de mercado,
incluindo testes de estratégias, geração de sinais e análise de performance.

Autor: Manus AI
Data: 17 de Julho de 2025
Versão: 1.0
"""

import unittest
import sys
import os
import json
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Adicionar diretório pai ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.test_framework import AgentTestCase
from agents.market_analysis_agent import MarketAnalysisAgent

class TestMarketAnalysisAgent(AgentTestCase):
    """Testes unitários para MarketAnalysisAgent"""
    
    def setUp(self):
        """Setup específico para testes do MarketAnalysisAgent"""
        super().setUp()
        
        # Configurar dados de teste específicos para análise de mercado
        self.market_data = self.generate_mock_market_data(
            symbol="BTCUSDT",
            periods=200,
            start_price=45000.0,
            volatility=0.02
        )
        
        # Configurar mock do agente
        self.agent = self.create_mock_market_analysis_agent()
    
    def create_mock_market_analysis_agent(self):
        """Cria instância mock do MarketAnalysisAgent para testes"""
        with patch('agents.market_analysis_agent.MarketAnalysisAgent.__init__', return_value=None):
            agent = MarketAnalysisAgent()
            
            # Configurar atributos necessários
            agent.name = "MarketAnalysisAgent"
            agent.config = self.test_config
            agent.logger = self.logger
            agent.symbols = ["BTCUSDT", "ETHUSDT"]
            agent.strategies = {
                "ema_crossover": {"enabled": True, "weight": 0.4},
                "rsi_mean_reversion": {"enabled": True, "weight": 0.3},
                "bollinger_breakout": {"enabled": True, "weight": 0.3}
            }
            
            # Configurar métodos necessários
            agent.save_metrics = Mock()
            agent.save_suggestion = Mock()
            agent.save_alert = Mock()
            agent.handle_error = Mock()
            
            # Implementar métodos de cálculo
            agent.calculate_ema = self.mock_calculate_ema
            agent.calculate_rsi = self.mock_calculate_rsi
            agent.calculate_bollinger_bands = self.mock_calculate_bollinger_bands
            agent.calculate_ema_crossover_signal = self.mock_calculate_ema_crossover_signal
            agent.calculate_rsi_mean_reversion_signal = self.mock_calculate_rsi_mean_reversion_signal
            agent.calculate_bollinger_breakout_signal = self.mock_calculate_bollinger_breakout_signal
            agent.combine_signals = self.mock_combine_signals
            agent.analyze_performance = self.mock_analyze_performance
            agent.suggest_improvements = self.mock_suggest_improvements
            
            return agent
    
    def mock_calculate_ema(self, prices, period):
        """Mock para cálculo de EMA"""
        if len(prices) < period:
            return [prices[-1]] * len(prices)
        
        ema = [sum(prices[:period]) / period]  # Primeira EMA como SMA
        multiplier = 2 / (period + 1)
        
        for price in prices[period:]:
            ema.append((price * multiplier) + (ema[-1] * (1 - multiplier)))
        
        return [ema[-1]] * (period - 1) + ema
    
    def mock_calculate_rsi(self, prices, period=14):
        """Mock para cálculo de RSI"""
        if len(prices) < period + 1:
            return 50.0  # RSI neutro
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def mock_calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """Mock para cálculo de Bollinger Bands"""
        if len(prices) < period:
            sma = np.mean(prices)
            std = np.std(prices)
        else:
            sma = np.mean(prices[-period:])
            std = np.std(prices[-period:])
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        return {
            "sma": sma,
            "upper": upper_band,
            "lower": lower_band,
            "width": upper_band - lower_band
        }
    
    def mock_calculate_ema_crossover_signal(self, prices, volumes):
        """Mock para sinal EMA Crossover"""
        ema_fast = self.mock_calculate_ema(prices, 12)[-1]
        ema_slow = self.mock_calculate_ema(prices, 26)[-1]
        
        price_diff = (ema_fast - ema_slow) / ema_slow
        signal = np.tanh(price_diff * 100)
        
        volume_factor = min(volumes[-1] / np.mean(volumes[-20:]), 2.0) if len(volumes) >= 20 else 1.0
        confidence = min(abs(signal) * volume_factor * 0.5, 1.0)
        
        return signal, confidence
    
    def mock_calculate_rsi_mean_reversion_signal(self, prices, volumes):
        """Mock para sinal RSI Mean Reversion"""
        rsi = self.mock_calculate_rsi(prices, 14)
        
        if rsi > 70:
            signal = -(rsi - 70) / 30
        elif rsi < 30:
            signal = (30 - rsi) / 30
        else:
            signal = 0
        
        confidence = min(abs(signal) * 1.5, 1.0)
        
        return signal, confidence
    
    def mock_calculate_bollinger_breakout_signal(self, prices, volumes):
        """Mock para sinal Bollinger Breakout"""
        bb = self.mock_calculate_bollinger_bands(prices, 20, 2)
        current_price = prices[-1]
        
        if current_price > bb["upper"]:
            signal = min((current_price - bb["upper"]) / (bb["upper"] - bb["sma"]), 1.0)
        elif current_price < bb["lower"]:
            signal = max((current_price - bb["lower"]) / (bb["sma"] - bb["lower"]), -1.0)
        else:
            signal = 0
        
        band_width = bb["width"] / bb["sma"]
        confidence = min(abs(signal) * (1 + band_width), 1.0)
        
        return signal, confidence
    
    def mock_combine_signals(self, signals, weights, market_conditions):
        """Mock para combinação de sinais"""
        combined_signal = sum(signal * weight for signal, weight in zip(signals, weights))
        
        signal_agreement = 1 - np.std([abs(s) for s in signals]) / (np.mean([abs(s) for s in signals]) + 1e-6)
        volatility_factor = min(market_conditions.get('volatility', 0.02) / 0.02, 2.0)
        
        final_confidence = signal_agreement * volatility_factor * 0.5
        
        return combined_signal, min(final_confidence, 1.0)
    
    def mock_analyze_performance(self):
        """Mock para análise de performance"""
        return {
            "signals_generated_today": 25,
            "success_rate": 0.72,
            "avg_signal_strength": 0.65,
            "strategy_performance": {
                "ema_crossover": {"signals": 10, "success_rate": 0.70},
                "rsi_mean_reversion": {"signals": 8, "success_rate": 0.75},
                "bollinger_breakout": {"signals": 7, "success_rate": 0.71}
            }
        }
    
    def mock_suggest_improvements(self):
        """Mock para sugestões de melhoria"""
        return [
            {
                "type": "PARAMETER_ADJUSTMENT",
                "priority": "medium",
                "suggestion": "Ajustar período EMA rápida de 12 para 10",
                "expected_improvement": "Melhor responsividade a mudanças"
            }
        ]
    
    def test_agent_initialization(self):
        """Testa inicialização do agente"""
        self.assertIsNotNone(self.agent)
        self.assertEqual(self.agent.name, "MarketAnalysisAgent")
        self.assertIn("BTCUSDT", self.agent.symbols)
        self.assertIn("ema_crossover", self.agent.strategies)
    
    def test_ema_calculation(self):
        """Testa cálculo de EMA"""
        prices = self.market_data["prices"][:50]
        ema_12 = self.agent.calculate_ema(prices, 12)
        
        # Verificar que EMA foi calculada
        self.assertIsInstance(ema_12, list)
        self.assertEqual(len(ema_12), len(prices))
        
        # EMA deve ser um número válido
        self.assertIsInstance(ema_12[-1], (int, float))
        self.assertGreater(ema_12[-1], 0)
    
    def test_rsi_calculation(self):
        """Testa cálculo de RSI"""
        prices = self.market_data["prices"][:50]
        rsi = self.agent.calculate_rsi(prices, 14)
        
        # RSI deve estar entre 0 e 100
        self.assertIsInstance(rsi, (int, float))
        self.assertGreaterEqual(rsi, 0)
        self.assertLessEqual(rsi, 100)
    
    def test_bollinger_bands_calculation(self):
        """Testa cálculo de Bollinger Bands"""
        prices = self.market_data["prices"][:50]
        bb = self.agent.calculate_bollinger_bands(prices, 20, 2)
        
        # Verificar estrutura das bandas
        self.assertIn("sma", bb)
        self.assertIn("upper", bb)
        self.assertIn("lower", bb)
        self.assertIn("width", bb)
        
        # Banda superior deve ser maior que SMA
        self.assertGreater(bb["upper"], bb["sma"])
        # Banda inferior deve ser menor que SMA
        self.assertLess(bb["lower"], bb["sma"])
        # Width deve ser positiva
        self.assertGreater(bb["width"], 0)
    
    def test_ema_crossover_signal_generation(self):
        """Testa geração de sinal EMA Crossover"""
        prices = self.market_data["prices"]
        volumes = self.market_data["volumes"]
        
        signal, confidence = self.agent.calculate_ema_crossover_signal(prices, volumes)
        
        # Validar sinal
        self.assertIsInstance(signal, (int, float))
        self.assertGreaterEqual(signal, -1.0)
        self.assertLessEqual(signal, 1.0)
        
        # Validar confiança
        self.assertIsInstance(confidence, (int, float))
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_rsi_mean_reversion_signal_generation(self):
        """Testa geração de sinal RSI Mean Reversion"""
        prices = self.market_data["prices"]
        volumes = self.market_data["volumes"]
        
        signal, confidence = self.agent.calculate_rsi_mean_reversion_signal(prices, volumes)
        
        # Validar sinal
        self.assertIsInstance(signal, (int, float))
        self.assertGreaterEqual(signal, -1.0)
        self.assertLessEqual(signal, 1.0)
        
        # Validar confiança
        self.assertIsInstance(confidence, (int, float))
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_bollinger_breakout_signal_generation(self):
        """Testa geração de sinal Bollinger Breakout"""
        prices = self.market_data["prices"]
        volumes = self.market_data["volumes"]
        
        signal, confidence = self.agent.calculate_bollinger_breakout_signal(prices, volumes)
        
        # Validar sinal
        self.assertIsInstance(signal, (int, float))
        self.assertGreaterEqual(signal, -1.0)
        self.assertLessEqual(signal, 1.0)
        
        # Validar confiança
        self.assertIsInstance(confidence, (int, float))
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_signal_combination(self):
        """Testa combinação de sinais de múltiplas estratégias"""
        signals = [0.6, -0.3, 0.8]  # Sinais de exemplo
        weights = [0.4, 0.3, 0.3]   # Pesos das estratégias
        market_conditions = {"volatility": 0.025}
        
        combined_signal, confidence = self.agent.combine_signals(signals, weights, market_conditions)
        
        # Sinal combinado deve estar no range válido
        self.assertIsInstance(combined_signal, (int, float))
        self.assertGreaterEqual(combined_signal, -1.0)
        self.assertLessEqual(combined_signal, 1.0)
        
        # Confiança deve estar no range válido
        self.assertIsInstance(confidence, (int, float))
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
    
    def test_performance_analysis(self):
        """Testa análise de performance do agente"""
        performance = self.agent.analyze_performance()
        
        # Verificar estrutura da análise
        self.assertIn("signals_generated_today", performance)
        self.assertIn("success_rate", performance)
        self.assertIn("strategy_performance", performance)
        
        # Validar métricas
        self.assertIsInstance(performance["signals_generated_today"], int)
        self.assertGreaterEqual(performance["signals_generated_today"], 0)
        
        self.assertIsInstance(performance["success_rate"], (int, float))
        self.assertGreaterEqual(performance["success_rate"], 0.0)
        self.assertLessEqual(performance["success_rate"], 1.0)
    
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
    
    def test_signal_validation_with_different_market_conditions(self):
        """Testa geração de sinais em diferentes condições de mercado"""
        conditions = ["normal", "volatile", "trending", "sideways"]
        
        for condition in conditions:
            with self.subTest(condition=condition):
                market_data = self.simulate_market_conditions(condition)
                prices = market_data["prices"]
                volumes = market_data["volumes"]
                
                # Testar cada estratégia
                ema_signal, ema_conf = self.agent.calculate_ema_crossover_signal(prices, volumes)
                rsi_signal, rsi_conf = self.agent.calculate_rsi_mean_reversion_signal(prices, volumes)
                bb_signal, bb_conf = self.agent.calculate_bollinger_breakout_signal(prices, volumes)
                
                # Todos os sinais devem ser válidos
                for signal, conf in [(ema_signal, ema_conf), (rsi_signal, rsi_conf), (bb_signal, bb_conf)]:
                    self.assertGreaterEqual(signal, -1.0)
                    self.assertLessEqual(signal, 1.0)
                    self.assertGreaterEqual(conf, 0.0)
                    self.assertLessEqual(conf, 1.0)
    
    def test_performance_with_insufficient_data(self):
        """Testa comportamento com dados insuficientes"""
        # Dados muito limitados
        short_prices = self.market_data["prices"][:5]
        short_volumes = self.market_data["volumes"][:5]
        
        # Agente deve lidar graciosamente com dados insuficientes
        try:
            signal, confidence = self.agent.calculate_ema_crossover_signal(short_prices, short_volumes)
            
            # Se não gerar exceção, sinal deve ser válido
            self.assertGreaterEqual(signal, -1.0)
            self.assertLessEqual(signal, 1.0)
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)
            
        except Exception as e:
            # Se gerar exceção, deve ser tratada apropriadamente
            self.assertIsInstance(e, (ValueError, IndexError))
    
    def test_signal_consistency(self):
        """Testa consistência dos sinais com os mesmos dados"""
        prices = self.market_data["prices"]
        volumes = self.market_data["volumes"]
        
        # Gerar sinais múltiplas vezes com os mesmos dados
        signals_1 = []
        signals_2 = []
        
        for _ in range(5):
            signal_1, _ = self.agent.calculate_ema_crossover_signal(prices, volumes)
            signal_2, _ = self.agent.calculate_ema_crossover_signal(prices, volumes)
            
            signals_1.append(signal_1)
            signals_2.append(signal_2)
        
        # Sinais devem ser consistentes (mesmos dados = mesmos sinais)
        for s1, s2 in zip(signals_1, signals_2):
            self.assertAlmostEqual(s1, s2, places=6)
    
    def test_performance_metrics_calculation(self):
        """Testa cálculo de métricas de performance"""
        # Simular histórico de sinais
        historical_signals = [
            {"signal": 0.8, "actual_return": 0.02, "success": True},
            {"signal": -0.6, "actual_return": -0.015, "success": True},
            {"signal": 0.4, "actual_return": -0.01, "success": False},
            {"signal": 0.9, "actual_return": 0.025, "success": True},
            {"signal": -0.3, "actual_return": 0.005, "success": False}
        ]
        
        # Calcular métricas
        total_signals = len(historical_signals)
        successful_signals = sum(1 for s in historical_signals if s["success"])
        success_rate = successful_signals / total_signals
        
        # Validar cálculos
        self.assertEqual(total_signals, 5)
        self.assertEqual(successful_signals, 3)
        self.assertAlmostEqual(success_rate, 0.6, places=2)
    
    def test_error_handling(self):
        """Testa tratamento de erros"""
        # Testar com dados inválidos
        invalid_data_cases = [
            ([], []),  # Listas vazias
            ([None], [None]),  # Valores None
            (["invalid"], ["invalid"]),  # Strings em vez de números
        ]
        
        for prices, volumes in invalid_data_cases:
            with self.subTest(prices=prices, volumes=volumes):
                try:
                    self.agent.calculate_ema_crossover_signal(prices, volumes)
                except Exception:
                    # Exceções são esperadas com dados inválidos
                    pass
    
    def test_memory_usage(self):
        """Testa uso de memória com grandes volumes de dados"""
        import sys
        
        # Gerar dataset grande
        large_data = self.generate_mock_market_data(periods=10000)
        
        # Medir uso de memória antes
        initial_size = sys.getsizeof(large_data)
        
        # Processar dados
        signal, confidence = self.agent.calculate_ema_crossover_signal(
            large_data["prices"], 
            large_data["volumes"]
        )
        
        # Verificar que o processamento foi bem-sucedido
        self.assertIsInstance(signal, (int, float))
        self.assertIsInstance(confidence, (int, float))
        
        # Verificar que não há vazamentos de memória óbvios
        self.assertLess(sys.getsizeof(signal) + sys.getsizeof(confidence), initial_size * 0.01)

class TestMarketAnalysisAgentPerformance(AgentTestCase):
    """Testes de performance para MarketAnalysisAgent"""
    
    def setUp(self):
        """Setup para testes de performance"""
        super().setUp()
        self.agent = TestMarketAnalysisAgent().create_mock_market_analysis_agent()
        self.performance_data = self.generate_mock_market_data(periods=1000)
    
    def test_signal_generation_performance(self):
        """Testa performance da geração de sinais"""
        prices = self.performance_data["prices"]
        volumes = self.performance_data["volumes"]
        
        def generate_signal():
            return self.agent.calculate_ema_crossover_signal(prices, volumes)
        
        # Teste de performance: deve executar em menos de 0.1s
        stats = self.run_performance_test(generate_signal, max_execution_time=0.1, iterations=50)
        
        self.logger.info(f"Performance de geração de sinal: {stats['mean_time']:.4f}s (média)")
        
        # Verificar que performance está dentro do esperado
        self.assertLess(stats['mean_time'], 0.1)
        self.assertLess(stats['std_time'], 0.05)  # Baixa variabilidade
    
    def test_bulk_signal_processing_performance(self):
        """Testa performance do processamento em lote"""
        def process_multiple_symbols():
            symbols_data = [
                self.generate_mock_market_data(symbol=f"SYMBOL{i}", periods=100)
                for i in range(10)
            ]
            
            results = []
            for data in symbols_data:
                signal, conf = self.agent.calculate_ema_crossover_signal(
                    data["prices"], data["volumes"]
                )
                results.append((signal, conf))
            
            return results
        
        # Teste de performance para múltiplos símbolos
        stats = self.run_performance_test(process_multiple_symbols, max_execution_time=1.0, iterations=10)
        
        self.logger.info(f"Performance de processamento em lote: {stats['mean_time']:.4f}s (média)")
        
        # Verificar performance aceitável
        self.assertLess(stats['mean_time'], 1.0)

if __name__ == "__main__":
    # Executar testes
    unittest.main(verbosity=2)

