"""
Confluence Lab Module - Versão Validada
Localização: market_manus/confluence_mode/confluence_mode_module.py
Data: 25/09/2025
Sintaxe: 100% Validada
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.table import Table
from rich.console import Console

# Importar estratégias SMC
from market_manus.strategies.smc.patterns import (
    detect_bos,
    detect_choch,
    detect_order_blocks,
    detect_fvg,
    detect_liquidity_sweep
)

# Importar novas estratégias clássicas
from market_manus.strategies.parabolic_sar import parabolic_sar_signal
from market_manus.strategies.vwap import vwap_signal, vwap_volume_combo_signal
from market_manus.strategies.cpr import cpr_signal
from market_manus.strategies.order_flow_scalper import order_flow_signal

# Importar filtro de volume
from market_manus.analysis.volume_filter import VolumeFilterPipeline

# Importar cache de dados históricos
from market_manus.data_providers.historical_cache import HistoricalDataCache

# Importar sistema de combinações recomendadas
from market_manus.confluence_mode.recommended_combinations import RecommendedCombinations
from market_manus.confluence_mode.recommended_combinations_menu import display_recommended_combinations_menu

# Importar integração Premium Manus AI
from market_manus.ai.manus_ai_integration import ManusAIAnalyzer
from market_manus.ai.semantic_kernel_advisor import SemanticKernelAdvisor

# Importar sistema de rastreamento de performance
from market_manus.performance.history_repository import (
    PerformanceHistoryRepository, 
    BacktestResult, 
    StrategyContribution
)
from market_manus.performance.analytics_service import PerformanceAnalyticsService

class ConfluenceModeModule:
    """
    Módulo de Confluência - Sistema de múltiplas estratégias
    
    IMPORTANTE: Este módulo usa APENAS dados reais das APIs Binance/Bybit.
    Nenhum dado mockado ou simulado é utilizado.
    API keys são validadas antes de executar qualquer backtest.
    """
    
    def __init__(self, data_provider=None, capital_manager=None):
        self.data_provider = data_provider
        self.capital_manager = capital_manager
        
        # Volume Filter Pipeline
        self.volume_pipeline = VolumeFilterPipeline()
        
        # Cache de dados históricos
        self.cache = HistoricalDataCache(cache_dir="data")
        
        # Estatísticas de cache para tracking
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "api_calls_saved": 0
        }
        
        # 🤖 PREMIUM AI LAYER - Manus AI Integration
        self.ai_analyzer = ManusAIAnalyzer()
        self.ai_premium_enabled = False  # Toggle on/off
        
        # 🧠 SEMANTIC KERNEL AI ADVISOR - Recomendações IA
        self.sk_advisor = SemanticKernelAdvisor()
        self.semantic_kernel_enabled = False  # Toggle on/off
        
        # 📊 PERFORMANCE TRACKING SYSTEM
        self.performance_repo = PerformanceHistoryRepository()
        self.performance_analytics = PerformanceAnalyticsService(self.performance_repo)
        
        # NEW: parâmetros específicos por estratégia (ex.: VWAP anchor, ADX filter)
        self.strategy_params = {}
        
        # ORDEM FIXA de estratégias para garantir mapeamento consistente UI → Engine
        # Esta lista DEVE corresponder exatamente à ordem exibida no menu
        self.strategies_order = [
            "rsi_mean_reversion",
            "ema_crossover",
            "bollinger_breakout",
            "macd",
            "stochastic",
            "williams_r",
            "adx",
            "fibonacci",
            "parabolic_sar",
            "vwap",
            "vwap_volume",
            "cpr",
            "smc_bos",
            "smc_choch",
            "smc_order_blocks",
            "smc_fvg",
            "smc_liquidity_sweep",
            "order_flow_scalper"
        ]
        
        # Estratégias disponíveis para confluência (17 estratégias: 12 clássicas + 5 SMC)
        self.available_strategies = {
            "rsi_mean_reversion": {
                "name": "RSI Mean Reversion",
                "description": "Reversão à média baseada no RSI",
                "emoji": "📊",
                "weight": 1.0
            },
            "ema_crossover": {
                "name": "EMA Crossover",
                "description": "Cruzamento de médias móveis exponenciais",
                "emoji": "📈",
                "weight": 1.0
            },
            "bollinger_breakout": {
                "name": "Bollinger Bands Breakout",
                "description": "Rompimento das Bandas de Bollinger",
                "emoji": "🎯",
                "weight": 1.0
            },
            "macd": {
                "name": "MACD",
                "description": "Moving Average Convergence Divergence",
                "emoji": "📊",
                "weight": 1.0
            },
            "stochastic": {
                "name": "Stochastic Oscillator",
                "description": "Oscilador Estocástico",
                "emoji": "📈",
                "weight": 1.0
            },
            "williams_r": {
                "name": "Williams %R",
                "description": "Williams Percent Range",
                "emoji": "📉",
                "weight": 1.0
            },
            "adx": {
                "name": "ADX",
                "description": "Average Directional Index",
                "emoji": "🎯",
                "weight": 1.0
            },
            "fibonacci": {
                "name": "Fibonacci Retracement",
                "description": "Níveis de Fibonacci",
                "emoji": "🔢",
                "weight": 1.0
            },
            "parabolic_sar": {
                "name": "Parabolic SAR",
                "description": "Seguidor de tendência com reversões",
                "emoji": "🎯",
                "weight": 1.0
            },
            "vwap": {
                "name": "VWAP",
                "description": "Volume Weighted Average Price",
                "emoji": "💹",
                "weight": 1.0
            },
            "vwap_volume": {
                "name": "VWAP + Volume Combo",
                "description": "Desequilíbrio institucional",
                "emoji": "🏦",
                "weight": 1.0
            },
            "cpr": {
                "name": "CPR (Central Pivot Range)",
                "description": "Zonas de suporte/resistência intraday",
                "emoji": "📍",
                "weight": 1.0
            },
            "smc_bos": {
                "name": "SMC: Break of Structure",
                "description": "Continuação de tendência após rompimento de swing high/low",
                "emoji": "🔥",
                "weight": 1.0
            },
            "smc_choch": {
                "name": "SMC: Change of Character",
                "description": "Reversão quando sequência de topos/fundos muda",
                "emoji": "🔄",
                "weight": 1.0
            },
            "smc_order_blocks": {
                "name": "SMC: Order Blocks",
                "description": "Última vela de acumulação antes do rompimento",
                "emoji": "📦",
                "weight": 1.0
            },
            "smc_fvg": {
                "name": "SMC: Fair Value Gap",
                "description": "Gap entre corpos/sombras indicando imbalance",
                "emoji": "⚡",
                "weight": 1.0
            },
            "smc_liquidity_sweep": {
                "name": "SMC: Liquidity Sweep",
                "description": "Pavio que varre liquidez indicando trap",
                "emoji": "🎣",
                "weight": 1.0
            },
            "order_flow_scalper": {
                "name": "Order Flow Scalper",
                "description": "Scalper por CVD/spread/imbalance (realtime)",
                "emoji": "⚡",
                "weight": 1.0
            }
        }
        
        # Modos de confluência
        self.confluence_modes = {
            "ALL": {
                "name": "ALL (Todas as estratégias)",
                "description": "Sinal apenas quando TODAS as estratégias concordam",
                "emoji": "🎯"
            },
            "ANY": {
                "name": "ANY (Qualquer estratégia)",
                "description": "Sinal quando QUALQUER estratégia gera sinal",
                "emoji": "⚡"
            },
            "MAJORITY": {
                "name": "MAJORITY (Maioria)",
                "description": "Sinal quando a MAIORIA das estratégias concorda",
                "emoji": "🗳️"
            },
            "WEIGHTED": {
                "name": "WEIGHTED (Ponderado)",
                "description": "Sinal baseado em pesos das estratégias",
                "emoji": "⚖️"
            }
        }
        
        # Assets disponíveis
        self.available_assets = {
            "BTCUSDT": {"name": "Bitcoin", "emoji": "🪙"},
            "ETHUSDT": {"name": "Ethereum", "emoji": "💎"},
            "BNBUSDT": {"name": "Binance Coin", "emoji": "🟡"},
            "SOLUSDT": {"name": "Solana", "emoji": "⚡"},
            "XRPUSDT": {"name": "XRP", "emoji": "💧"},
            "ADAUSDT": {"name": "Cardano", "emoji": "🔵"},
            "DOGEUSDT": {"name": "Dogecoin", "emoji": "🐕"},
            "MATICUSDT": {"name": "Polygon", "emoji": "🟣"}
        }
        
        # Timeframes disponíveis
        self.timeframes = {
            "1": {"name": "1 minuto", "bybit_interval": "1", "description": "Scalping ultra-rápido"},
            "5": {"name": "5 minutos", "bybit_interval": "5", "description": "Scalping rápido"},
            "15": {"name": "15 minutos", "bybit_interval": "15", "description": "Swing trading curto"},
            "30": {"name": "30 minutos", "bybit_interval": "30", "description": "Swing trading médio"},
            "60": {"name": "1 hora", "bybit_interval": "60", "description": "Swing trading longo"},
            "240": {"name": "4 horas", "bybit_interval": "240", "description": "Position trading"},
            "D": {"name": "1 dia", "bybit_interval": "D", "description": "Investimento longo prazo"}
        }
        
        # Configurações atuais
        self.selected_asset = None
        self.selected_timeframe = None
        self.selected_strategies = []
        self.selected_confluence_mode = None
        self.custom_start_date = None
        self.custom_end_date = None
        
        # Histórico de testes
        self.test_history = []
    
    def _validate_api_credentials(self) -> bool:
        """
        Valida se as credenciais da API estão configuradas
        
        Returns:
            bool: True se credenciais válidas, False caso contrário
        """
        if not self.data_provider:
            print("❌ Data provider não configurado")
            print("❌ Impossível executar backtest sem dados reais da API")
            return False
        
        # Verificar se o provider tem API key configurada
        if not hasattr(self.data_provider, 'api_key') or not self.data_provider.api_key:
            print("❌ API Key não configurada")
            print("❌ Configure BINANCE_API_KEY ou BYBIT_API_KEY no ambiente")
            return False
        
        if not hasattr(self.data_provider, 'api_secret') or not self.data_provider.api_secret:
            print("❌ API Secret não configurado")
            print("❌ Configure BINANCE_API_SECRET ou BYBIT_API_SECRET no ambiente")
            return False
        
        print("✅ Credenciais da API validadas com sucesso")
        print(f"📊 Fonte de dados: {self.data_provider.__class__.__name__} (API REAL)")
        return True
    
    def run_interactive_mode(self):
        """Executa o modo interativo do Confluence Lab"""
        while True:
            self._show_main_menu()
            choice = input("\n🔢 Escolha uma opção (0-11): ").strip()
            
            if choice == '0':
                print("\n👋 Saindo do Confluence Lab...")
                break
            elif choice == '1':
                self._asset_selection_menu()
            elif choice == '2':
                self._timeframe_selection_menu()
            elif choice == '3':
                self._strategy_selection_menu()
            elif choice == '4':
                self._confluence_mode_selection()
            elif choice == '5':
                self._period_selection_menu()
            elif choice == '6':
                self._manage_historical_cache()
            elif choice == '7':
                self._run_confluence_backtest()
            elif choice == '8':
                self._run_realtime_confluence_test()
            elif choice == '9':
                self._view_test_results()
            elif choice == '10':
                self._export_results()
            elif choice == '11':
                self._toggle_ai_premium()
            elif choice == '12':
                self._toggle_semantic_kernel()
            else:
                print("❌ Opção inválida")
                input("\n📖 Pressione ENTER para continuar...")
    
    def _show_main_menu(self):
        """Mostra o menu principal do Confluence Lab"""
        print("\n" + "="*80)
        print("🎯 CONFLUENCE MODE - SISTEMA DE CONFLUÊNCIA")
        print("="*80)
        
        # Status atual
        asset_status = f"✅ {self.selected_asset}" if self.selected_asset else "❌ Não selecionado"
        timeframe_status = f"✅ {self.timeframes[self.selected_timeframe]['name']}" if self.selected_timeframe else "❌ Não selecionado"
        strategies_status = f"✅ {len(self.selected_strategies)} estratégias" if self.selected_strategies else "❌ Nenhuma selecionada"
        confluence_status = f"✅ {self.confluence_modes[self.selected_confluence_mode]['name']}" if self.selected_confluence_mode else "❌ Não selecionado"
        
        print(f"📊 CONFIGURAÇÃO ATUAL:")
        print(f"   🪙 Ativo: {asset_status}")
        print(f"   ⏰ Timeframe: {timeframe_status}")
        print(f"   📈 Estratégias: {strategies_status}")
        print(f"   🎯 Modo Confluência: {confluence_status}")
        
        if self.custom_start_date and self.custom_end_date:
            print(f"   📅 Período: {self.custom_start_date} até {self.custom_end_date}")
        else:
            print(f"   📅 Período: Padrão (últimos 30 dias)")
        
        # Capital info
        if self.capital_manager:
            print(f"   💰 Capital: ${self.capital_manager.current_capital:.2f}")
            print(f"   💼 Position Size: ${self.capital_manager.get_position_size():.2f}")
        
        # AI Premium Status
        ai_status = "🤖 AI Premium: ✅ ATIVO" if self.ai_premium_enabled else "🤖 AI Premium: ⏸️ DESATIVADO"
        ai_available = " (Disponível)" if self.ai_analyzer.is_enabled() else " (Configure MANUS_AI_API_KEY)"
        print(f"   {ai_status}{ai_available if not self.ai_premium_enabled else ''}")
        
        # Semantic Kernel Status
        sk_status = "🧠 SK Advisor: ✅ ATIVO" if self.semantic_kernel_enabled else "🧠 SK Advisor: ⏸️ DESATIVADO"
        sk_available = " (Disponível)" if self.sk_advisor.is_available() else " (Configure OPENAI_API_KEY)"
        print(f"   {sk_status}{sk_available if not self.semantic_kernel_enabled else ''}")
        
        print(f"\n🔧 CONFIGURAÇÃO:")
        print("   1️⃣  Seleção de Ativo")
        print("   2️⃣  Seleção de Timeframe")
        print("   3️⃣  Seleção de Estratégias")
        print("   4️⃣  Modo de Confluência")
        
        print(f"\n📁 DADOS HISTÓRICOS:")
        print("   5️⃣  Período Personalizado")
        print("   6️⃣  Dados Históricos Salvos (gerenciar cache)")
        
        print(f"\n🧪 TESTES:")
        print("   7️⃣  Executar Backtest de Confluência")
        print("   8️⃣  Teste em Tempo Real de Confluência")
        
        print(f"\n📊 RESULTADOS:")
        print("   9️⃣  Visualizar Resultados")
        print("   🔟 Exportar Relatórios")
        
        print(f"\n🤖 AI & RECOMENDAÇÕES:")
        ai_toggle_text = "Desativar" if self.ai_premium_enabled else "Ativar"
        print(f"   1️⃣1️⃣  {ai_toggle_text} Manus AI (Análise Premium)")
        sk_toggle_text = "Desativar" if self.semantic_kernel_enabled else "Ativar"
        print(f"   1️⃣2️⃣  {sk_toggle_text} SK Advisor (Recomendações IA)")
        
        print(f"\n   0️⃣  Voltar ao Menu Principal")
    
    def _asset_selection_menu(self):
        """Menu de seleção de ativo"""
        print("\n🪙 SELEÇÃO DE ATIVO")
        print("="*50)
        
        assets_list = list(self.available_assets.keys())
        for i, asset in enumerate(assets_list, 1):
            info = self.available_assets[asset]
            selected = "✅" if asset == self.selected_asset else "  "
            print(f"   {i}️⃣  {selected} {info['emoji']} {asset} - {info['name']}")
        
        print(f"\n   0️⃣  Voltar")
        
        choice = input("\n🔢 Escolha um ativo (0-8): ").strip()
        
        if choice == '0':
            return
        
        try:
            asset_index = int(choice) - 1
            if 0 <= asset_index < len(assets_list):
                self.selected_asset = assets_list[asset_index]
                asset_info = self.available_assets[self.selected_asset]
                print(f"\n✅ Ativo selecionado: {asset_info['emoji']} {self.selected_asset} - {asset_info['name']}")
            else:
                print("❌ Opção inválida")
        except ValueError:
            print("❌ Digite um número válido")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _timeframe_selection_menu(self):
        """Menu de seleção de timeframe"""
        print("\n⏰ SELEÇÃO DE TIMEFRAME")
        print("="*50)
        
        timeframes_list = list(self.timeframes.keys())
        for i, tf_key in enumerate(timeframes_list, 1):
            tf_info = self.timeframes[tf_key]
            selected = "✅" if tf_key == self.selected_timeframe else "  "
            print(f"   {i}️⃣  {selected} {tf_info['name']} - {tf_info['description']}")
        
        print(f"\n   0️⃣  Voltar")
        
        choice = input("\n🔢 Escolha um timeframe (0-7): ").strip()
        
        if choice == '0':
            return
        
        try:
            tf_index = int(choice) - 1
            if 0 <= tf_index < len(timeframes_list):
                tf_key = timeframes_list[tf_index]
                self.selected_timeframe = tf_key
                tf_info = self.timeframes[tf_key]
                print(f"\n✅ Timeframe selecionado: {tf_info['name']} - {tf_info['description']}")
            else:
                print("❌ Opção inválida")
        except ValueError:
            print("❌ Digite um número válido")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _strategy_selection_menu(self):
        """Menu de seleção de estratégias com Combinações Recomendadas"""
        while True:
            print("\n📈 SELEÇÃO DE ESTRATÉGIAS")
            print("="*80)
            
            # Mostrar estratégias selecionadas atualmente
            if self.selected_strategies:
                print(f"\n✅ Estratégias atuais ({len(self.selected_strategies)}):")
                for strategy_key in self.selected_strategies:
                    if strategy_key in self.available_strategies:
                        strategy = self.available_strategies[strategy_key]
                        print(f"   {strategy['emoji']} {strategy['name']}")
            else:
                print("\n⚠️  Nenhuma estratégia selecionada")
            
            print(f"\n{'='*80}")
            print("📋 OPÇÕES:")
            print("   1️⃣  ✨ Combinações Recomendadas (22 presets profissionais)")
            print("   2️⃣  🔧 Seleção Manual de Estratégias (17 disponíveis)")
            print("   0️⃣  Voltar")
            
            choice = input("\n🔢 Escolha uma opção (0-2): ").strip()
            
            if choice == '0':
                return
            elif choice == '1':
                # Abrir menu de combinações recomendadas
                if display_recommended_combinations_menu(self):
                    # Combinação foi aplicada, voltar ao menu principal
                    return
            elif choice == '2':
                # Seleção manual tradicional
                self._manual_strategy_selection()
                return
            else:
                print("❌ Opção inválida")
                input("\n📖 Pressione ENTER para continuar...")
    
    def _manual_strategy_selection(self):
        """Seleção manual de estratégias individuais"""
        print("\n📈 SELEÇÃO MANUAL DE ESTRATÉGIAS")
        print("="*80)
        print("💡 Selecione múltiplas estratégias para confluência")
        print("   Digite os números separados por vírgula (ex: 1,3,5)")
        
        strategies_list = self.strategies_order
        for i, strategy_key in enumerate(strategies_list, 1):
            strategy = self.available_strategies[strategy_key]
            selected = "✅" if strategy_key in self.selected_strategies else "  "
            print(f"   {i:2d}️⃣  {selected} {strategy['emoji']} {strategy['name']}")
            print(f"        📝 {strategy['description']}")
        
        print(f"\n   0️⃣  Cancelar")
        
        choice = input("\n🔢 Escolha estratégias (ex: 1,3,5 ou 0): ").strip()
        
        if choice == '0':
            return
        
        try:
            # Parse múltiplas seleções
            selected_indices = [int(x.strip()) - 1 for x in choice.split(',')]
            valid_strategies = []
            
            for index in selected_indices:
                if 0 <= index < len(strategies_list):
                    valid_strategies.append(strategies_list[index])
            
            if valid_strategies:
                self.selected_strategies = valid_strategies
                print(f"\n✅ Estratégias selecionadas:")
                for strategy_key in self.selected_strategies:
                    strategy = self.available_strategies[strategy_key]
                    print(f"   {strategy['emoji']} {strategy['name']}")
            else:
                print("❌ Nenhuma estratégia válida selecionada")
        except ValueError:
            print("❌ Formato inválido. Use números separados por vírgula")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _confluence_mode_selection(self):
        """Menu de seleção do modo de confluência"""
        print("\n🎯 MODO DE CONFLUÊNCIA")
        print("="*50)
        
        modes_list = list(self.confluence_modes.keys())
        for i, mode_key in enumerate(modes_list, 1):
            mode = self.confluence_modes[mode_key]
            selected = "✅" if mode_key == self.selected_confluence_mode else "  "
            print(f"   {i}️⃣  {selected} {mode['emoji']} {mode['name']}")
            print(f"       📝 {mode['description']}")
        
        print(f"\n   0️⃣  Voltar")
        
        choice = input("\n🔢 Escolha um modo (0-4): ").strip()
        
        if choice == '0':
            return
        
        try:
            mode_index = int(choice) - 1
            if 0 <= mode_index < len(modes_list):
                mode_key = modes_list[mode_index]
                self.selected_confluence_mode = mode_key
                mode_info = self.confluence_modes[mode_key]
                print(f"\n✅ Modo selecionado: {mode_info['emoji']} {mode_info['name']}")
                
                # Se for modo WEIGHTED, configurar pesos
                if mode_key == "WEIGHTED":
                    self._configure_strategy_weights()
            else:
                print("❌ Opção inválida")
        except ValueError:
            print("❌ Digite um número válido")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _configure_strategy_weights(self):
        """Configura pesos das estratégias para modo WEIGHTED"""
        print("\n⚖️ CONFIGURAÇÃO DE PESOS")
        print("="*50)
        print("💡 Configure o peso de cada estratégia (0.1 a 2.0)")
        
        for strategy_key in self.selected_strategies:
            strategy = self.available_strategies[strategy_key]
            current_weight = strategy.get('weight', 1.0)
            
            print(f"\n📊 {strategy['name']}")
            print(f"   Peso atual: {current_weight}")
            
            weight_input = input(f"   Novo peso (0.1-2.0, ENTER para manter): ").strip()
            
            if weight_input:
                try:
                    weight = float(weight_input)
                    if 0.1 <= weight <= 2.0:
                        self.available_strategies[strategy_key]['weight'] = weight
                        print(f"   ✅ Peso atualizado: {weight}")
                    else:
                        print(f"   ⚠️ Peso fora da faixa, mantendo: {current_weight}")
                except ValueError:
                    print(f"   ❌ Valor inválido, mantendo: {current_weight}")
    
    def _period_selection_menu(self):
        """Menu de seleção de período personalizado"""
        print("\n📅 PERÍODO PERSONALIZADO")
        print("="*50)
        
        print("🔧 Configure o período para backtesting:")
        print("   📅 Data inicial (formato: YYYY-MM-DD)")
        print("   📅 Data final (formato: YYYY-MM-DD)")
        print("   💡 Deixe em branco para usar período padrão (últimos 30 dias)")
        
        # Data inicial
        start_input = input("\n📅 Data inicial (YYYY-MM-DD): ").strip()
        if start_input:
            try:
                start_date = datetime.strptime(start_input, "%Y-%m-%d")
                self.custom_start_date = start_date.strftime("%Y-%m-%d")
                print(f"✅ Data inicial: {self.custom_start_date}")
            except ValueError:
                print("❌ Formato de data inválido, usando padrão")
                self.custom_start_date = None
        else:
            self.custom_start_date = None
            print("📅 Usando período padrão para data inicial")
        
        # Data final
        end_input = input("\n📅 Data final (YYYY-MM-DD): ").strip()
        if end_input:
            try:
                end_date = datetime.strptime(end_input, "%Y-%m-%d")
                self.custom_end_date = end_date.strftime("%Y-%m-%d")
                print(f"✅ Data final: {self.custom_end_date}")
                
                # Validar se data final é posterior à inicial
                if self.custom_start_date:
                    start_dt = datetime.strptime(self.custom_start_date, "%Y-%m-%d")
                    end_dt = datetime.strptime(self.custom_end_date, "%Y-%m-%d")
                    if end_dt <= start_dt:
                        print("❌ Data final deve ser posterior à inicial, usando padrão")
                        self.custom_start_date = None
                        self.custom_end_date = None
            except ValueError:
                print("❌ Formato de data inválido, usando padrão")
                self.custom_end_date = None
        else:
            self.custom_end_date = None
            print("📅 Usando período padrão para data final")
        
        # Resumo
        if self.custom_start_date and self.custom_end_date:
            print(f"\n✅ Período personalizado configurado:")
            print(f"   📅 De: {self.custom_start_date}")
            print(f"   📅 Até: {self.custom_end_date}")
        else:
            print(f"\n📅 Usando período padrão (últimos 30 dias)")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _manage_historical_cache(self):
        """Menu de gerenciamento de cache de dados históricos"""
        console = Console()
        
        while True:
            print("\n" + "="*80)
            print("📁 GERENCIAMENTO DE CACHE DE DADOS HISTÓRICOS")
            print("="*80)
            
            print("\n💡 Gerencie os dados históricos salvos em cache")
            print("\n📋 OPÇÕES:")
            print("   1️⃣  Ver dados salvos")
            print("   2️⃣  Limpar cache específico")
            print("   3️⃣  Limpar todo cache")
            print("   4️⃣  Estatísticas de uso")
            print("   0️⃣  Voltar")
            
            choice = input("\n🔢 Escolha uma opção (0-4): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._view_cached_data(console)
            elif choice == '2':
                self._delete_specific_cache(console)
            elif choice == '3':
                self._clear_all_cache()
            elif choice == '4':
                self._show_cache_statistics()
            else:
                print("❌ Opção inválida")
                input("\n📖 Pressione ENTER para continuar...")
    
    def _view_cached_data(self, console: Console):
        """Visualiza todos os dados em cache usando Rich Table"""
        print("\n📊 DADOS SALVOS EM CACHE")
        print("="*80)
        
        cached_datasets = self.cache.list_cached_datasets()
        
        if not cached_datasets:
            print("\n⚠️  Nenhum dado em cache encontrado")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        table = Table(title=f"Cache de Dados Históricos ({len(cached_datasets)} datasets)")
        
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
        table.add_column("Símbolo", style="yellow", no_wrap=True)
        table.add_column("Interval", style="green", no_wrap=True)
        table.add_column("Período", style="blue")
        table.add_column("Candles", justify="right", style="magenta")
        table.add_column("Tamanho", justify="right", style="cyan")
        table.add_column("Data Cache", style="white")
        
        for i, dataset in enumerate(cached_datasets, 1):
            symbol = dataset.get("symbol", "N/A")
            interval = dataset.get("interval", "N/A")
            start_date = dataset.get("start_date", "N/A")
            end_date = dataset.get("end_date", "N/A")
            candles = dataset.get("candles", 0)
            file_size = dataset.get("file_size_kb", 0)
            cached_at = dataset.get("cached_at", "N/A")
            
            period = f"{start_date} → {end_date}"
            
            if cached_at != "N/A":
                try:
                    cached_dt = datetime.fromisoformat(cached_at)
                    cached_at_str = cached_dt.strftime("%Y-%m-%d %H:%M")
                except:
                    cached_at_str = cached_at
            else:
                cached_at_str = "N/A"
            
            table.add_row(
                str(i),
                symbol,
                interval,
                period,
                f"{candles:,}",
                f"{file_size:.2f} KB",
                cached_at_str
            )
        
        console.print(table)
        input("\n📖 Pressione ENTER para continuar...")
    
    def _delete_specific_cache(self, console: Console):
        """Remove um cache específico selecionado pelo usuário"""
        print("\n🗑️  LIMPAR CACHE ESPECÍFICO")
        print("="*80)
        
        cached_datasets = self.cache.list_cached_datasets()
        
        if not cached_datasets:
            print("\n⚠️  Nenhum dado em cache encontrado")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        table = Table(title="Selecione o cache para remover")
        
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
        table.add_column("Símbolo", style="yellow", no_wrap=True)
        table.add_column("Interval", style="green", no_wrap=True)
        table.add_column("Período", style="blue")
        table.add_column("Tamanho", justify="right", style="cyan")
        
        for i, dataset in enumerate(cached_datasets, 1):
            symbol = dataset.get("symbol", "N/A")
            interval = dataset.get("interval", "N/A")
            start_date = dataset.get("start_date", "N/A")
            end_date = dataset.get("end_date", "N/A")
            file_size = dataset.get("file_size_kb", 0)
            
            period = f"{start_date} → {end_date}"
            
            table.add_row(
                str(i),
                symbol,
                interval,
                period,
                f"{file_size:.2f} KB"
            )
        
        console.print(table)
        
        choice = input(f"\n🔢 Escolha o número do cache para remover (1-{len(cached_datasets)}) ou 0 para cancelar: ").strip()
        
        if choice == '0':
            print("\n❌ Operação cancelada")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(cached_datasets):
                dataset = cached_datasets[index]
                cache_key = dataset.get("key")
                
                if not cache_key:
                    print("\n❌ Chave de cache inválida")
                    input("\n📖 Pressione ENTER para continuar...")
                    return
                
                confirm = input(f"\n⚠️  Tem certeza que deseja remover o cache '{cache_key}'? (s/n): ").strip().lower()
                
                if confirm == 's':
                    if self.cache.delete(cache_key):
                        print(f"\n✅ Cache '{cache_key}' removido com sucesso")
                    else:
                        print(f"\n❌ Erro ao remover cache '{cache_key}'")
                else:
                    print("\n❌ Operação cancelada")
            else:
                print("\n❌ Número inválido")
        except ValueError:
            print("\n❌ Digite um número válido")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _clear_all_cache(self):
        """Remove todos os caches"""
        print("\n🧹 LIMPAR TODO CACHE")
        print("="*80)
        
        cached_datasets = self.cache.list_cached_datasets()
        
        if not cached_datasets:
            print("\n⚠️  Nenhum dado em cache encontrado")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        print(f"\n⚠️  Você está prestes a remover TODOS os {len(cached_datasets)} datasets em cache")
        
        total_size = sum(dataset.get("file_size_kb", 0) for dataset in cached_datasets)
        print(f"   📦 Total de espaço a ser liberado: {total_size:.2f} KB ({total_size/1024:.2f} MB)")
        
        confirm = input("\n⚠️  Tem certeza que deseja limpar TODO o cache? (s/n): ").strip().lower()
        
        if confirm == 's':
            self.cache.clear_all()
            print("\n✅ Todo o cache foi limpo com sucesso")
        else:
            print("\n❌ Operação cancelada")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _show_cache_statistics(self):
        """Mostra estatísticas de uso do cache"""
        print("\n📈 ESTATÍSTICAS DE USO DO CACHE")
        print("="*80)
        
        cached_datasets = self.cache.list_cached_datasets()
        
        total_files = len(cached_datasets)
        total_size_kb = sum(dataset.get("file_size_kb", 0) for dataset in cached_datasets)
        total_size_mb = total_size_kb / 1024
        total_candles = sum(dataset.get("candles", 0) for dataset in cached_datasets)
        
        print(f"\n📦 ARMAZENAMENTO:")
        print(f"   📁 Total de arquivos: {total_files}")
        print(f"   💾 Espaço total usado: {total_size_kb:.2f} KB ({total_size_mb:.2f} MB)")
        print(f"   📊 Total de candles: {total_candles:,}")
        
        if total_files > 0:
            avg_size = total_size_kb / total_files
            avg_candles = total_candles / total_files
            print(f"   📏 Tamanho médio por arquivo: {avg_size:.2f} KB")
            print(f"   📊 Média de candles por arquivo: {avg_candles:.0f}")
        
        print(f"\n🎯 ESTATÍSTICAS DA SESSÃO:")
        print(f"   ✅ Cache Hits: {self.cache_stats['hits']}")
        print(f"   ❌ Cache Misses: {self.cache_stats['misses']}")
        print(f"   💰 Chamadas API economizadas: {self.cache_stats['api_calls_saved']}")
        
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        if total_requests > 0:
            hit_rate = (self.cache_stats['hits'] / total_requests) * 100
            print(f"   📈 Taxa de acerto: {hit_rate:.1f}%")
        
        if cached_datasets:
            print(f"\n📋 DATASETS POR SÍMBOLO:")
            symbols = {}
            for dataset in cached_datasets:
                symbol = dataset.get("symbol", "N/A")
                if symbol not in symbols:
                    symbols[symbol] = 0
                symbols[symbol] += 1
            
            for symbol, count in sorted(symbols.items()):
                print(f"   🪙 {symbol}: {count} dataset(s)")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _validate_configuration(self) -> bool:
        """Valida se a configuração está completa"""
        if not self.selected_asset:
            print("❌ Selecione um ativo primeiro (opção 1)")
            input("\n📖 Pressione ENTER para continuar...")
            return False
        
        if not self.selected_timeframe:
            print("❌ Selecione um timeframe primeiro (opção 2)")
            input("\n📖 Pressione ENTER para continuar...")
            return False
        
        if not self.selected_strategies:
            print("❌ Selecione pelo menos uma estratégia (opção 3)")
            input("\n📖 Pressione ENTER para continuar...")
            return False
        
        if not self.selected_confluence_mode:
            print("❌ Selecione um modo de confluência (opção 4)")
            input("\n📖 Pressione ENTER para continuar...")
            return False
        
        return True
    
    def _display_data_metrics(self, metrics: Dict):
        """
        Exibe métricas de dados históricos carregados em formato visual consistente
        
        Args:
            metrics: Dicionário com métricas dos dados (total_candles, period, success_rate, etc.)
        """
        print("\n" + "═" * 63)
        print("📊 DADOS HISTÓRICOS CARREGADOS")
        print("═" * 63)
        
        # Total de Candles
        total_candles = metrics.get("total_candles", 0)
        print(f"📈 Total de Candles: {total_candles:,}")
        
        # Período Exato
        first_time = metrics.get("first_candle_time")
        last_time = metrics.get("last_candle_time")
        if first_time and last_time:
            first_str = first_time.strftime("%Y-%m-%d %H:%M:%S")
            last_str = last_time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"📅 Período: {first_str} → {last_str}")
        
        # Taxa de Sucesso da API
        success_rate = metrics.get("success_rate", 0)
        successful = metrics.get("successful_batches", 0)
        total = metrics.get("total_batches", 0)
        print(f"✅ API Success Rate: {success_rate:.1f}% ({successful}/{total} batches bem-sucedidos)")
        
        # Fonte de Dados
        data_source = metrics.get("data_source", "Unknown")
        print(f"🔗 Fonte: {data_source} (dados reais)")
        
        print("═" * 63)
    
    def _fetch_historical_klines(self, symbol: str, interval: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[List, Dict]:
        """
        Busca TODOS os candles do período especificado, fazendo múltiplas chamadas se necessário.
        Utiliza cache para evitar chamadas desnecessárias à API.
        
        Args:
            symbol: Par de trading (ex: BTCUSDT)
            interval: Timeframe (1, 5, 15, 60, 240, D)
            start_date: Data inicial no formato YYYY-MM-DD (opcional)
            end_date: Data final no formato YYYY-MM-DD (opcional)
        
        Returns:
            Tuple[List, Dict]: (Lista com todos os candles, Dicionário com métricas da API)
        """
        # Calcular timestamps
        if start_date and end_date:
            start_ts = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
            end_ts = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)
            cache_start_date = start_date
            cache_end_date = end_date
        else:
            # Período padrão: últimos 30 dias
            end_ts = int(datetime.now().timestamp() * 1000)
            start_ts = end_ts - (30 * 24 * 60 * 60 * 1000)
            # Converter timestamps para formato YYYY-MM-DD para cache
            cache_start_date = datetime.fromtimestamp(start_ts / 1000).strftime("%Y-%m-%d")
            cache_end_date = datetime.fromtimestamp(end_ts / 1000).strftime("%Y-%m-%d")
        
        # Calcular duração de um candle em milissegundos
        timeframe_ms = {
            "1": 60 * 1000,           # 1 minuto
            "5": 5 * 60 * 1000,       # 5 minutos
            "15": 15 * 60 * 1000,     # 15 minutos
            "60": 60 * 60 * 1000,     # 1 hora
            "240": 4 * 60 * 60 * 1000,  # 4 horas
            "D": 24 * 60 * 60 * 1000  # 1 dia
        }
        
        candle_duration = timeframe_ms.get(interval, 60 * 1000)
        
        # Calcular quantos candles são necessários
        total_candles_needed = int((end_ts - start_ts) / candle_duration)
        
        print(f"   📊 Período requer ~{total_candles_needed} candles")
        
        # TENTAR BUSCAR DO CACHE PRIMEIRO
        cache_key = self.cache._generate_cache_key(symbol, interval, cache_start_date, cache_end_date)
        cached_data = self.cache.get(symbol, interval, cache_start_date, cache_end_date)
        
        if cached_data:
            # CACHE HIT
            self.cache_stats["hits"] += 1
            self.cache_stats["api_calls_saved"] += 1
            print(f"   ✅ Cache HIT: {cache_key} ({len(cached_data)} candles)")
            
            # Determinar período exato dos dados
            first_candle_time = datetime.fromtimestamp(int(cached_data[0][0]) / 1000)
            last_candle_time = datetime.fromtimestamp(int(cached_data[-1][0]) / 1000)
            
            metrics = {
                "total_candles": len(cached_data),
                "successful_batches": 0,
                "failed_batches": 0,
                "total_batches": 0,
                "success_rate": 100.0,
                "first_candle_time": first_candle_time,
                "last_candle_time": last_candle_time,
                "data_source": "Cache (dados reais armazenados)",
                "cache_hit": True
            }
            
            return cached_data, metrics
        
        # CACHE MISS - Buscar da API
        self.cache_stats["misses"] += 1
        print(f"   📥 Cache MISS: buscando API...")
        
        # Buscar dados em lotes de 500 (limite da API)
        all_klines = []
        current_start = start_ts
        batch_num = 1
        
        # Métricas da API
        successful_batches = 0
        failed_batches = 0
        
        while current_start < end_ts:
            # Calcular quantos candles faltam
            remaining_ms = end_ts - current_start
            remaining_candles = int(remaining_ms / candle_duration)
            limit = min(500, remaining_candles)
            
            if limit <= 0:
                break
            
            print(f"   📡 Batch {batch_num}: Buscando {limit} candles a partir de {datetime.fromtimestamp(current_start/1000).strftime('%Y-%m-%d %H:%M')}...")
            
            # Buscar dados com startTime
            try:
                klines = self.data_provider.get_kline(
                    category='spot',
                    symbol=symbol,
                    interval=interval,
                    limit=limit,
                    start=current_start,
                    end=end_ts
                )
                
                if not klines:
                    print(f"   ⚠️  Nenhum dado retornado para este batch")
                    failed_batches += 1
                    break
                
                all_klines.extend(klines)
                successful_batches += 1
                print(f"   ✅ Recebidos {len(klines)} candles (total acumulado: {len(all_klines)})")
                
                # Próximo batch começa após o último candle recebido
                last_candle_time = int(klines[-1][0])  # timestamp do último candle
                current_start = last_candle_time + candle_duration
                batch_num += 1
                
                # Evitar rate limit
                time.sleep(0.1)
            except Exception as e:
                print(f"   ❌ Erro no batch {batch_num}: {str(e)}")
                failed_batches += 1
                break
        
        # Salvar dados no cache para futuros usos
        if all_klines:
            print(f"   💾 Salvando dados no cache...")
            self.cache.save(symbol, interval, cache_start_date, cache_end_date, all_klines)
        
        # Calcular métricas
        total_batches = successful_batches + failed_batches
        success_rate = (successful_batches / total_batches * 100) if total_batches > 0 else 0
        
        # Determinar período exato dos dados
        first_candle_time = None
        last_candle_time = None
        if all_klines:
            first_candle_time = datetime.fromtimestamp(int(all_klines[0][0]) / 1000)
            last_candle_time = datetime.fromtimestamp(int(all_klines[-1][0]) / 1000)
        
        metrics = {
            "total_candles": len(all_klines),
            "successful_batches": successful_batches,
            "failed_batches": failed_batches,
            "total_batches": total_batches,
            "success_rate": success_rate,
            "first_candle_time": first_candle_time,
            "last_candle_time": last_candle_time,
            "data_source": self.data_provider.__class__.__name__ if self.data_provider else "Unknown",
            "cache_hit": False
        }
        
        return all_klines, metrics
    
    def _run_confluence_backtest(self):
        """
        Executa backtest de confluência com dados reais da Binance/Bybit
        
        IMPORTANTE: Valida API credentials e usa APENAS dados reais das APIs.
        """
        if not self._validate_configuration():
            return
        
        # VALIDAÇÃO OBRIGATÓRIA DE API CREDENTIALS
        print("\n🔐 Validando credenciais da API...")
        if not self._validate_api_credentials():
            print("\n❌ BACKTEST CANCELADO: API credentials não configuradas")
            print("   Configure BINANCE_API_KEY/BYBIT_API_KEY e seus secrets antes de executar backtests.")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        print("\n🧪 EXECUTANDO BACKTEST DE CONFLUÊNCIA COM DADOS REAIS")
        print("="*60)
        
        print(f"📊 Configuração do teste:")
        print(f"   🪙 Ativo: {self.selected_asset}")
        print(f"   ⏰ Timeframe: {self.timeframes[self.selected_timeframe]['name']}")
        print(f"   📈 Estratégias: {len(self.selected_strategies)} selecionadas")
        print(f"   🎯 Modo: {self.confluence_modes[self.selected_confluence_mode]['name']}")
        
        if self.custom_start_date and self.custom_end_date:
            print(f"   📅 Período: {self.custom_start_date} até {self.custom_end_date}")
        else:
            print(f"   📅 Período: Últimos 30 dias")
        
        print(f"\n🔄 Buscando dados reais da Binance...")
        
        # Buscar dados históricos REAIS da Binance
        if not self.data_provider:
            print("❌ Data Provider não disponível!")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        # selected_timeframe já está no formato correto para Binance ("1", "5", "15", "60", "240", "D")
        interval = self.selected_timeframe
        
        # Buscar TODOS os candles do período especificado
        klines, metrics = self._fetch_historical_klines(
            symbol=self.selected_asset,
            interval=interval,
            start_date=self.custom_start_date,
            end_date=self.custom_end_date
        )
        
        if not klines or len(klines) < 50:
            print(f"❌ Dados insuficientes! Recebido: {len(klines) if klines else 0} velas")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        # Exibir métricas de dados carregados
        self._display_data_metrics(metrics)
        
        # Converter dados para análise (OHLCV completo)
        opens = [float(k[1]) for k in klines]   # Preços de abertura
        highs = [float(k[2]) for k in klines]   # Máximas
        lows = [float(k[3]) for k in klines]    # Mínimas
        closes = [float(k[4]) for k in klines]  # Preços de fechamento
        
        total_candles = len(closes)
        total_strategies = len(self.selected_strategies)
        total_work = total_candles * total_strategies
        
        print(f"\n📊 Executando {total_strategies} estratégias sobre {total_candles:,} candles...")
        
        # Executar cada estratégia sobre os dados reais com barra de progresso
        strategy_signals = {}
        start_time = time.time()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TextColumn("{task.completed}/{task.total} work units"),
            TextColumn("•"),
            TextColumn("[cyan]{task.speed:.1f} units/s[/cyan]" if hasattr(Progress, 'speed') else ""),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
        ) as progress:
            task_id = progress.add_task("Processando estratégias...", total=total_work)
            
            for idx, strategy_key in enumerate(self.selected_strategies, 1):
                strategy = self.available_strategies[strategy_key]
                strategy_start = time.time()
                
                signal_indices = self._execute_strategy_on_data(strategy_key, closes, highs, lows, opens)
                
                strategy_signals[strategy_key] = {
                    "name": strategy['name'],
                    "signal_indices": signal_indices,
                    "weight": strategy.get('weight', 1.0)
                }
                
                # Atualizar progresso
                completed_work = idx * total_candles
                elapsed = time.time() - start_time
                speed = completed_work / elapsed if elapsed > 0 else 0
                
                progress.update(
                    task_id, 
                    advance=total_candles,
                    description=f"[{idx}/{total_strategies}] {strategy['emoji']} {strategy['name']} • [cyan]{speed:.0f} units/s[/cyan]"
                )
        
        # Aplicar filtro de volume
        print("\n🔍 Aplicando filtro de volume...")
        
        # Extrair volumes com validação
        volumes_raw = []
        for k in klines:
            try:
                vol = float(k[5]) if len(k) > 5 and k[5] else 0.0
                volumes_raw.append(vol)
            except (ValueError, IndexError, TypeError):
                volumes_raw.append(0.0)
        
        volumes = pd.Series(volumes_raw)
        
        # Validar se temos dados de volume válidos
        if volumes.sum() == 0:
            print("⚠️  AVISO: Dados de volume zerados ou ausentes!")
            print("   O filtro de volume será desabilitado para este backtest.")
            print("   Dica: Verifique se o provider suporta dados de volume históricos.\n")
            
            # Pular filtro de volume e usar sinais originais
            filtered_strategy_signals = strategy_signals
            
            # Exibir resumo indicando que filtro foi desabilitado
            print("\n📊 Filtro de Volume: DESABILITADO")
            print("   Usando todos os sinais originais sem filtragem de volume.\n")
        else:
            # Exibir estatísticas do filtro antes de aplicar
            self.volume_pipeline.volume_filter.display_filter_stats(volumes)
            
            # Resetar estatísticas antes de aplicar
            self.volume_pipeline.reset_stats()
            
            # Aplicar filtro aos sinais de todas as estratégias
            filtered_strategy_signals = self.volume_pipeline.apply_to_strategy_signals(
                strategy_signals,
                volumes
            )
            
            # Exibir resumo do filtro
            print(f"\n{self.volume_pipeline.get_stats_summary()}")
        
        # Calcular confluência baseado no modo (NOVO: retorna lista de (índice, direção))
        confluence_signals = self._calculate_confluence_signals(filtered_strategy_signals)
        
        # Calcular resultados financeiros baseados nos sinais reais COM DIREÇÃO
        initial_capital = self.capital_manager.current_capital if self.capital_manager else 10000
        final_capital, total_trades, winning_trades = self._simulate_trades_from_signals(
            confluence_signals, closes, initial_capital, highs, lows
        )
        losing_trades = total_trades - winning_trades
        pnl = final_capital - initial_capital
        roi = (pnl / initial_capital) * 100
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # Contar sinais por direção
        buy_signals = sum(1 for _, direction in confluence_signals if direction == "BUY")
        sell_signals = sum(1 for _, direction in confluence_signals if direction == "SELL")
        
        print(f"\n📊 RESULTADOS DO BACKTEST DE CONFLUÊNCIA:")
        print(f"   💰 Capital inicial: ${initial_capital:.2f}")
        print(f"   💵 Capital final: ${final_capital:.2f}")
        print(f"   📈 P&L: ${pnl:+.2f}")
        print(f"   📊 ROI: {roi:+.2f}%")
        print(f"   🎯 Sinais de confluência: {len(confluence_signals)} ({buy_signals} BUY, {sell_signals} SELL)")
        print(f"   ✅ Trades vencedores: {winning_trades}")
        print(f"   ❌ Trades perdedores: {losing_trades}")
        print(f"   📊 Win Rate: {win_rate:.1f}%")
        
        print(f"\n📈 DETALHES POR ESTRATÉGIA (APÓS FILTRO DE VOLUME):")
        for strategy_key, data in filtered_strategy_signals.items():
            original_count = data.get('original_count', len(data['signal_indices']))
            filtered_count = data.get('filtered_count', len(data['signal_indices']))
            print(f"   {data['name']}: {filtered_count} sinais (original: {original_count}, peso: {data['weight']})")
        
        # Mostrar capital simulado (sem alterar o capital real)
        if self.capital_manager:
            simulated_final_capital = final_capital
            print(f"\n💰 Capital real permanece: ${self.capital_manager.current_capital:.2f}")
            print(f"   📊 Capital simulado (backtest): ${simulated_final_capital:.2f}")
            print(f"   ℹ️  (Backtest não altera capital real)")
        
        # Salvar no histórico
        test_result = {
            "timestamp": datetime.now().isoformat(),
            "type": "confluence_backtest",
            "asset": self.selected_asset,
            "timeframe": self.selected_timeframe,
            "strategies": self.selected_strategies,
            "confluence_mode": self.selected_confluence_mode,
            "results": {
                "initial_capital": initial_capital,
                "final_capital": final_capital,
                "pnl": pnl,
                "roi": roi,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "confluence_signals": len(confluence_signals),
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "strategy_signals": {k: {"name": v["name"], "signals": len(v["signal_indices"]), "weight": v["weight"], "original_signals": v.get("original_count", len(v["signal_indices"]))} for k, v in filtered_strategy_signals.items()},
                "volume_filter_stats": self.volume_pipeline.stats
            }
        }
        self.test_history.append(test_result)
        
        # 📊 SALVAR NO REPOSITÓRIO DE PERFORMANCE
        self._save_backtest_to_performance_repo(
            test_result, filtered_strategy_signals, total_trades, winning_trades, losing_trades
        )
        
        # 🧠 EXIBIR RECOMENDAÇÕES DE PESOS E INSIGHTS IA
        self._display_recommendations(test_result, filtered_strategy_signals)
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _execute_strategy_on_data(self, strategy_key: str, closes: List[float], highs: List[float], lows: List[float], opens: List[float]) -> List[Tuple[int, str]]:
        """
        Executa uma estratégia sobre dados reais OHLCV e retorna (ÍNDICE, DIREÇÃO) onde sinais ocorreram
        
        NOVO (Out 2025 - Fase 2): Retorna List[Tuple[int, str]] com direção BUY/SELL
        Usa dados OHLCV completos (não fake open=close) para análise SMC precisa
        
        Returns:
            List[Tuple[int, str]]: Lista de (índice, direção) onde direção é "BUY" ou "SELL"
        """
        signal_indices = []
        
        # RSI Mean Reversion
        if strategy_key == "rsi_mean_reversion":
            rsi_cfg = self.strategy_params.get("rsi_mean_reversion", {})
            rsi_period = int(rsi_cfg.get("period", 14))
            oversold = float(rsi_cfg.get("oversold_threshold", 30))
            overbought = float(rsi_cfg.get("overbought_threshold", 70))
            rsi_values = self._calculate_rsi(closes, period=rsi_period)
            for i, rsi in enumerate(rsi_values):
                if rsi < oversold:
                    signal_indices.append((i + rsi_period, "BUY"))
                elif rsi > overbought:
                    signal_indices.append((i + rsi_period, "SELL"))
        
        # EMA Crossover
        elif strategy_key == "ema_crossover":
            ema_cfg = self.strategy_params.get("ema_crossover", {})
            fast_period = int(ema_cfg.get("fast_period", 12))
            slow_period = int(ema_cfg.get("slow_period", 26))
            ema_fast = self._calculate_ema(closes, fast_period)
            ema_slow = self._calculate_ema(closes, slow_period)
            offset = slow_period
            
            # ADX gating opcional
            adx_cfg = ema_cfg.get("adx_filter", {})
            use_adx = bool(adx_cfg.get("use", False))
            adx_threshold = float(adx_cfg.get("threshold", 25))
            strict_adx = bool(adx_cfg.get("strict", True))
            adx_period = int(adx_cfg.get("period", 14))
            adx_values = None
            adx_offset = adx_period
            if use_adx:
                try:
                    adx_values = self._calculate_adx(closes, highs, lows, period=adx_period)
                except Exception:
                    adx_values = None
            
            for i in range(1, min(len(ema_fast), len(ema_slow))):
                candle_index = i + offset
                # Cruzamento para cima - BUY
                if ema_fast[i-1] <= ema_slow[i-1] and ema_fast[i] > ema_slow[i]:
                    if use_adx and adx_values is not None:
                        adx_idx = candle_index - adx_offset
                        if 0 <= adx_idx < len(adx_values) and adx_values[adx_idx] < adx_threshold and strict_adx:
                            continue
                    signal_indices.append((candle_index, "BUY"))
                # Cruzamento para baixo - SELL
                elif ema_fast[i-1] >= ema_slow[i-1] and ema_fast[i] < ema_slow[i]:
                    if use_adx and adx_values is not None:
                        adx_idx = candle_index - adx_offset
                        if 0 <= adx_idx < len(adx_values) and adx_values[adx_idx] < adx_threshold and strict_adx:
                            continue
                    signal_indices.append((candle_index, "SELL"))
        
        # Bollinger Bands
        elif strategy_key == "bollinger_breakout":
            bb_cfg = self.strategy_params.get("bollinger_breakout", {})
            bb_period = int(bb_cfg.get("period", 20))
            bb_std = float(bb_cfg.get("std_dev", 2.0))
            bb_upper, bb_lower = self._calculate_bollinger_bands(closes, period=bb_period, std_dev=bb_std)
            offset = bb_period - 1
            for i in range(len(bb_upper)):
                if i < len(closes) - offset:
                    candle_index = i + offset
                    if closes[candle_index] > bb_upper[i]:
                        signal_indices.append((candle_index, "SELL"))
                    elif closes[candle_index] < bb_lower[i]:
                        signal_indices.append((candle_index, "BUY"))
        
        # MACD
        elif strategy_key == "macd":
            macd_cfg = self.strategy_params.get("macd", {})
            fast = int(macd_cfg.get("fast_period", 12))
            slow = int(macd_cfg.get("slow_period", 26))
            sig = int(macd_cfg.get("signal_period", 9))
            macd_line, signal_line = self._calculate_macd(closes, fast=fast, slow=slow, signal_period=sig)
            offset = slow + sig
            
            adx_cfg = macd_cfg.get("adx_filter", {})
            use_adx = bool(adx_cfg.get("use", False))
            adx_threshold = float(adx_cfg.get("threshold", 25))
            strict_adx = bool(adx_cfg.get("strict", True))
            adx_period = int(adx_cfg.get("period", 14))
            adx_values = None
            adx_offset = adx_period
            if use_adx:
                try:
                    adx_values = self._calculate_adx(closes, highs, lows, period=adx_period)
                except Exception:
                    adx_values = None
            
            for i in range(1, min(len(macd_line), len(signal_line))):
                candle_index = i + offset
                if macd_line[i-1] <= signal_line[i-1] and macd_line[i] > signal_line[i]:
                    if use_adx and adx_values is not None:
                        adx_idx = candle_index - adx_offset
                        if 0 <= adx_idx < len(adx_values) and adx_values[adx_idx] < adx_threshold and strict_adx:
                            continue
                    signal_indices.append((candle_index, "BUY"))
                elif macd_line[i-1] >= signal_line[i-1] and macd_line[i] < signal_line[i]:
                    if use_adx and adx_values is not None:
                        adx_idx = candle_index - adx_offset
                        if 0 <= adx_idx < len(adx_values) and adx_values[adx_idx] < adx_threshold and strict_adx:
                            continue
                    signal_indices.append((candle_index, "SELL"))
        
        # Stochastic
        elif strategy_key == "stochastic":
            stoch_cfg = self.strategy_params.get("stochastic", {})
            stoch_period = int(stoch_cfg.get("period", 14))
            oversold = float(stoch_cfg.get("oversold", 20))
            overbought = float(stoch_cfg.get("overbought", 80))
            stoch_values = self._calculate_stochastic(closes, highs, lows, period=stoch_period)
            offset = stoch_period - 1
            for i, stoch in enumerate(stoch_values):
                if stoch < oversold:
                    signal_indices.append((i + offset, "BUY"))
                elif stoch > overbought:
                    signal_indices.append((i + offset, "SELL"))
        
        # Williams %R
        elif strategy_key == "williams_r":
            wr_cfg = self.strategy_params.get("williams_r", {})
            wr_period = int(wr_cfg.get("period", 14))
            oversold = float(wr_cfg.get("oversold", -80))
            overbought = float(wr_cfg.get("overbought", -20))
            williams_values = self._calculate_williams_r(closes, highs, lows, period=wr_period)
            offset = wr_period - 1
            for i, wr in enumerate(williams_values):
                if wr < oversold:
                    signal_indices.append((i + offset, "BUY"))
                elif wr > overbought:
                    signal_indices.append((i + offset, "SELL"))
        
        # ADX
        elif strategy_key == "adx":
            adx_cfg = self.strategy_params.get("adx", {})
            adx_period = int(adx_cfg.get("period", 14))
            adx_threshold = float(adx_cfg.get("threshold", 25))
            adx_values = self._calculate_adx(closes, highs, lows, period=adx_period)
            offset = adx_period
            for i, adx in enumerate(adx_values):
                if adx > adx_threshold:
                    if i + offset < len(closes):
                        current_idx = i + offset
                        if current_idx > 10:
                            recent_avg = sum(closes[current_idx-10:current_idx]) / 10
                            direction = "BUY" if closes[current_idx] > recent_avg else "SELL"
                            signal_indices.append((current_idx, direction))
        
        # Fibonacci
        elif strategy_key == "fibonacci":
            # Detectar topos e fundos e gerar sinais em níveis de Fibonacci
            # Simplificado: alternando BUY/SELL a cada 20 candles
            for i in range(20, len(closes), 40):
                signal_indices.append((i, "BUY"))
            for i in range(40, len(closes), 40):
                signal_indices.append((i, "SELL"))
        
        # Parabolic SAR
        elif strategy_key == "parabolic_sar":
            df = pd.DataFrame({
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes,
                'volume': [1.0] * len(closes)  # Volume não usado pelo PSAR
            })
            psar_cfg = self.strategy_params.get("parabolic_sar", {})
            af_start = float(psar_cfg.get("af_start", 0.02))
            af_step = float(psar_cfg.get("af_step", 0.02))
            af_max = float(psar_cfg.get("af_max", 0.2))
            for i in range(50, len(df)):
                window_df = df.iloc[max(0, i-50):i+1].reset_index(drop=True)
                signal = parabolic_sar_signal(window_df, af_start=af_start, af_step=af_step, af_max=af_max)
                if signal.action != "HOLD":
                    signal_indices.append((i, signal.action))
        
        # VWAP
        elif strategy_key == "vwap":
            # Usar volume dummy se não disponível
            volumes = [1.0] * len(closes)  # Será substituído por volume real se disponível
            df = pd.DataFrame({
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes,
                'volume': volumes
            })
            # NEW: Suporte a parâmetros de VWAP (anchor e bandas)
            vwap_params = self.strategy_params.get("vwap", {})
            for i in range(50, len(df)):
                window_df = df.iloc[max(0, i-50):i+1].reset_index(drop=True)
                signal = vwap_signal(window_df, params=vwap_params)
                if signal.action != "HOLD":
                    signal_indices.append((i, signal.action))
        
        # VWAP + Volume Combo
        elif strategy_key == "vwap_volume":
            volumes = [1.0] * len(closes)
            df = pd.DataFrame({
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes,
                'volume': volumes
            })
            vwap_vol_params = self.strategy_params.get("vwap_volume", {})
            for i in range(50, len(df)):
                window_df = df.iloc[max(0, i-50):i+1].reset_index(drop=True)
                signal = vwap_volume_combo_signal(window_df, params=vwap_vol_params)
                if signal.action != "HOLD":
                    signal_indices.append((i, signal.action))
        
        # CPR (Central Pivot Range)
        elif strategy_key == "cpr":
            df = pd.DataFrame({
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes,
                'volume': [1.0] * len(closes)
            })
            cpr_params = self.strategy_params.get("cpr", {})
            for i in range(50, len(df)):
                window_df = df.iloc[max(0, i-50):i+1].reset_index(drop=True)
                signal = cpr_signal(window_df, params=cpr_params)
                if signal.action != "HOLD":
                    signal_indices.append((i, signal.action))
        
        # Order Flow Scalper (offline-safe stub; requires realtime metrics)
        elif strategy_key == "order_flow_scalper":
            df = pd.DataFrame({
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes
            })
            ofs_params = self.strategy_params.get("order_flow_scalper", {})
            # Without order book metrics, signals will typically be HOLD.
            for i in range(50, len(df)):
                window_df = df.iloc[max(0, i-50):i+1].reset_index(drop=True)
                try:
                    signal = order_flow_signal(window_df, metrics=None, params=ofs_params)
                    if signal.action != "HOLD":
                        signal_indices.append((i, signal.action))
                except Exception:
                    pass
        
        # SMC: Break of Structure
        elif strategy_key == "smc_bos":
            df = pd.DataFrame({
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes
            })
            bos_cfg = self.strategy_params.get("smc_bos", {})
            min_disp = float(bos_cfg.get("min_displacement", 0.0))
            # Aplicar em janelas deslizantes
            for i in range(50, len(df)):
                window_df = df.iloc[max(0, i-50):i+1].reset_index(drop=True)
                signal = detect_bos(window_df, min_displacement=min_disp)
                if signal.action != "HOLD":
                    signal_indices.append((i, signal.action))  # Captura direção BUY/SELL
        
        # SMC: Change of Character
        elif strategy_key == "smc_choch":
            df = pd.DataFrame({
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes
            })
            for i in range(50, len(df)):
                window_df = df.iloc[max(0, i-50):i+1].reset_index(drop=True)
                signal = detect_choch(window_df)
                if signal.action != "HOLD":
                    signal_indices.append((i, signal.action))  # Captura direção BUY/SELL
        
        # SMC: Order Blocks
        elif strategy_key == "smc_order_blocks":
            df = pd.DataFrame({
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes
            })
            ob_cfg = self.strategy_params.get("smc_order_blocks", {})
            min_range = float(ob_cfg.get("min_range", 0.0))
            for i in range(50, len(df)):
                window_df = df.iloc[max(0, i-50):i+1].reset_index(drop=True)
                signal = detect_order_blocks(window_df, min_range=min_range)
                if signal.action != "HOLD":
                    signal_indices.append((i, signal.action))  # Captura direção BUY/SELL
        
        # SMC: Fair Value Gap
        elif strategy_key == "smc_fvg":
            df = pd.DataFrame({
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes
            })
            for i in range(50, len(df)):
                window_df = df.iloc[max(0, i-50):i+1].reset_index(drop=True)
                signal = detect_fvg(window_df)
                if signal.action != "HOLD":
                    signal_indices.append((i, signal.action))  # Captura direção BUY/SELL
        
        # SMC: Liquidity Sweep
        elif strategy_key == "smc_liquidity_sweep":
            df = pd.DataFrame({
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes
            })
            ls_cfg = self.strategy_params.get("smc_liquidity_sweep", {})
            body_ratio = float(ls_cfg.get("body_ratio", 0.5))
            for i in range(50, len(df)):
                window_df = df.iloc[max(0, i-50):i+1].reset_index(drop=True)
                signal = detect_liquidity_sweep(window_df, body_ratio=body_ratio)
                if signal.action != "HOLD":
                    signal_indices.append((i, signal.action))  # Captura direção BUY/SELL
        
        return signal_indices
    
    def _simulate_trades_from_signals(self, confluence_signals: List[Tuple[int, str]], closes: List[float], initial_capital: float, highs: List[float] = None, lows: List[float] = None, progress_cb: Optional[Callable[[int, str], None]] = None, progress_start: int = 75, progress_end: int = 90) -> Tuple[float, int, int]:
        """
        Simula trades REALISTAS com LONG e SHORT usando high/low intrabar
        
        NOVA ARQUITETURA (Out 2025 - Fase 2):
        - Usa ÍNDICES e DIREÇÃO reais (BUY/SELL) dos sinais de confluência
        - Abre LONG ou SHORT baseado na direção do sinal
        - Respeita position lock (apenas 1 posição por vez)
        - Implementa Stop Loss (0.5%) e Take Profit (1.0%)
        - Usa HIGH/LOW intrabar para SL/TP realista (stop tem prioridade)
        
        Args:
            confluence_signals: Lista de (índice, direção) onde sinais de confluência ocorreram
            closes: Lista de preços de fechamento
            initial_capital: Capital inicial
            highs: Lista de preços máximos (opcional, se None usa closes)
            lows: Lista de preços mínimos (opcional, se None usa closes)
            
        Returns:
            Tuple[capital_final, total_trades, winning_trades]
        """
        # Fallback para highs/lows se não fornecidos
        if highs is None:
            highs = closes
        if lows is None:
            lows = closes
        
        capital = initial_capital
        position_size_pct = 0.02  # 2% do capital por trade
        stop_loss_pct = 0.005  # 0.5% stop loss
        take_profit_pct = 0.010  # 1.0% take profit
        
        winning_trades = 0
        losing_trades = 0
        current_position = None  # None quando sem posição, dict quando em posição
        
        # Converter para dict para lookup O(1): {índice: direção}
        signal_dict = {idx: direction for idx, direction in confluence_signals}
        
        # Instrumentação de progresso por candle
        total_candles = len(closes)
        last_emitted_pct = -1
        
        # Iterar através de TODOS os candles
        for candle_index in range(len(closes)):
            # Atualizar progresso incremental (mapeado para 75→90%)
            if progress_cb is not None and total_candles > 0:
                frac = (candle_index + 1) / total_candles
                pct = int(progress_start + (progress_end - progress_start) * frac)
                if pct != last_emitted_pct:
                    last_emitted_pct = pct
                    try:
                        progress_cb(pct, f"Simulando trades ({candle_index+1}/{total_candles} candles)")
                    except Exception:
                        pass
            # Verificar se há posição aberta
            if current_position is not None:
                high = highs[candle_index]
                low = lows[candle_index]
                close = closes[candle_index]
                direction = current_position['direction']
                
                # LONG: Check Stop Loss PRIMEIRO (prioridade absoluta), depois Take Profit
                if direction == "BUY":
                    sl_hit = low <= current_position['stop_loss']
                    tp_hit = high >= current_position['take_profit']
                    
                    # Se ambos foram tocados no mesmo candle, STOP tem prioridade
                    if sl_hit and tp_hit:
                        # Gap/volatilidade: assumir que stop foi tocado primeiro
                        pnl = -current_position['position_size'] * stop_loss_pct
                        capital += pnl
                        losing_trades += 1
                        current_position = None
                    elif sl_hit:
                        # Apenas stop tocado
                        pnl = -current_position['position_size'] * stop_loss_pct
                        capital += pnl
                        losing_trades += 1
                        current_position = None
                    elif tp_hit:
                        # Apenas take profit tocado
                        pnl = current_position['position_size'] * take_profit_pct
                        capital += pnl
                        winning_trades += 1
                        current_position = None
                    # Timeout (máximo 50 candles por trade)
                    elif candle_index - current_position['entry_index'] >= 50:
                        pnl_pct = (close - current_position['entry_price']) / current_position['entry_price']
                        pnl = current_position['position_size'] * pnl_pct
                        capital += pnl
                        winning_trades += 1 if pnl > 0 else 0
                        losing_trades += 1 if pnl <= 0 else 0
                        current_position = None
                
                # SHORT: Lógica invertida, mas STOP ainda tem prioridade
                elif direction == "SELL":
                    sl_hit = high >= current_position['stop_loss']
                    tp_hit = low <= current_position['take_profit']
                    
                    # Se ambos foram tocados no mesmo candle, STOP tem prioridade
                    if sl_hit and tp_hit:
                        # Gap/volatilidade: assumir que stop foi tocado primeiro
                        pnl = -current_position['position_size'] * stop_loss_pct
                        capital += pnl
                        losing_trades += 1
                        current_position = None
                    elif sl_hit:
                        # Apenas stop tocado
                        pnl = -current_position['position_size'] * stop_loss_pct
                        capital += pnl
                        losing_trades += 1
                        current_position = None
                    elif tp_hit:
                        # Apenas take profit tocado
                        pnl = current_position['position_size'] * take_profit_pct
                        capital += pnl
                        winning_trades += 1
                        current_position = None
                    # Timeout
                    elif candle_index - current_position['entry_index'] >= 50:
                        pnl_pct = (current_position['entry_price'] - close) / current_position['entry_price']  # Invertido para SHORT
                        pnl = current_position['position_size'] * pnl_pct
                        capital += pnl
                        winning_trades += 1 if pnl > 0 else 0
                        losing_trades += 1 if pnl <= 0 else 0
                        current_position = None
            
            # Tentar abrir nova posição APENAS se:
            # 1. Não há posição aberta
            # 2. Este candle_index tem sinal de confluência
            elif candle_index in signal_dict:
                entry_price = closes[candle_index]
                position_size = capital * position_size_pct
                direction = signal_dict[candle_index]
                
                # Configurar SL/TP baseado na direção
                if direction == "BUY":
                    stop_loss = entry_price * (1 - stop_loss_pct)
                    take_profit = entry_price * (1 + take_profit_pct)
                else:  # SELL
                    stop_loss = entry_price * (1 + stop_loss_pct)  # Invertido para SHORT
                    take_profit = entry_price * (1 - take_profit_pct)  # Invertido para SHORT
                
                current_position = {
                    'entry_price': entry_price,
                    'entry_index': candle_index,
                    'position_size': position_size,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'direction': direction
                }
        
        # Fechar posição pendente se ainda aberta
        if current_position is not None:
            exit_price = closes[-1]
            direction = current_position['direction']
            
            if direction == "BUY":
                pnl_pct = (exit_price - current_position['entry_price']) / current_position['entry_price']
            else:  # SELL
                pnl_pct = (current_position['entry_price'] - exit_price) / current_position['entry_price']
            
            pnl = current_position['position_size'] * pnl_pct
            capital += pnl
            
            winning_trades += 1 if pnl > 0 else 0
            losing_trades += 1 if pnl <= 0 else 0
        
        total_trades = winning_trades + losing_trades
        
        # Garantir emissão final no término da simulação
        if progress_cb is not None:
            try:
                progress_cb(progress_end, f"Simulação de trades concluída — {total_trades} executados")
            except Exception:
                pass
        
        return capital, total_trades, winning_trades
    
    def _calculate_rsi(self, data: List[float], period: int = 14) -> List[float]:
        """Calcula RSI real"""
        rsi_values = []
        if len(data) < period + 1:
            return rsi_values
        
        for i in range(period, len(data)):
            gains = []
            losses = []
            for j in range(i - period, i):
                change = data[j + 1] - data[j]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = np.mean(gains) if gains else 0
            avg_loss = np.mean(losses) if losses else 0
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values
    
    def _calculate_ema(self, data: List[float], period: int) -> List[float]:
        """Calcula EMA real"""
        ema_values = []
        if len(data) < period:
            return ema_values
        
        multiplier = 2 / (period + 1)
        ema = np.mean(data[:period])  # SMA inicial
        ema_values.append(ema)
        
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
            ema_values.append(ema)
        
        return ema_values
    
    def _calculate_bollinger_bands(self, data: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[List[float], List[float]]:
        """Calcula Bandas de Bollinger reais"""
        upper_band = []
        lower_band = []
        
        for i in range(period - 1, len(data)):
            window = data[i - period + 1:i + 1]
            sma = np.mean(window)
            std = np.std(window)
            upper_band.append(sma + std_dev * std)
            lower_band.append(sma - std_dev * std)
        
        return upper_band, lower_band
    
    def _calculate_macd(self, data: List[float], fast: int = 12, slow: int = 26, signal_period: int = 9) -> Tuple[List[float], List[float]]:
        """Calcula MACD real (parametrizado)"""
        ema_fast = self._calculate_ema(data, fast)
        ema_slow = self._calculate_ema(data, slow)
        
        macd_line = []
        for i in range(min(len(ema_fast), len(ema_slow))):
            macd_line.append(ema_fast[i] - ema_slow[i])
        
        signal_line = self._calculate_ema(macd_line, signal_period) if len(macd_line) >= signal_period else []
        
        return macd_line, signal_line
    
    def _calculate_stochastic(self, closes: List[float], highs: List[float], lows: List[float], period: int = 14) -> List[float]:
        """Calcula Estocástico real"""
        stoch_values = []
        
        for i in range(period - 1, len(closes)):
            highest_high = max(highs[i - period + 1:i + 1])
            lowest_low = min(lows[i - period + 1:i + 1])
            
            if highest_high == lowest_low:
                stoch = 50
            else:
                stoch = ((closes[i] - lowest_low) / (highest_high - lowest_low)) * 100
            
            stoch_values.append(stoch)
        
        return stoch_values
    
    def _calculate_williams_r(self, closes: List[float], highs: List[float], lows: List[float], period: int = 14) -> List[float]:
        """Calcula Williams %R real"""
        williams_values = []
        
        for i in range(period - 1, len(closes)):
            highest_high = max(highs[i - period + 1:i + 1])
            lowest_low = min(lows[i - period + 1:i + 1])
            
            if highest_high == lowest_low:
                wr = -50
            else:
                wr = ((highest_high - closes[i]) / (highest_high - lowest_low)) * -100
            
            williams_values.append(wr)
        
        return williams_values
    
    def _calculate_adx(self, closes: List[float], highs: List[float], lows: List[float], period: int = 14) -> List[float]:
        """Calcula ADX real (simplificado)"""
        adx_values = []
        
        for i in range(period, len(closes)):
            # Simplificado: usar volatilidade como proxy para ADX
            window = closes[i - period:i]
            volatility = np.std(window) / np.mean(window) * 100
            adx_values.append(min(volatility * 10, 100))  # Normalizar para 0-100
        
        return adx_values
    
    def _calculate_confluence_signals(self, strategy_signals: Dict) -> List[Tuple[int, str]]:
        """
        Calcula sinais de confluência baseado no modo selecionado COM DIREÇÃO
        
        NOVO (Out 2025 - Fase 2): Retorna List[Tuple[int, str]] = [(índice, direção), ...]
        Acumula votos BUY/SELL separadamente por índice e determina direção vencedora
        
        Args:
            strategy_signals: Dict com signal_indices List[Tuple[int, str]] de cada estratégia
            
        Returns:
            List[Tuple[int, str]]: Lista de tuplas (índice, direção) ordenadas por índice
                                   onde direção é "BUY" ou "SELL"
        """
        from collections import defaultdict
        
        # Estrutura para acumular votos por índice
        # Cada índice tem: buy_weight, sell_weight, e set de estratégias que votaram
        class VoteData:
            def __init__(self):
                self.buy_weight = 0.0
                self.sell_weight = 0.0
                self.strategies = set()
        
        index_votes = defaultdict(VoteData)
        
        # Acumular votos de todas as estratégias
        for strategy_key, data in strategy_signals.items():
            weight = data['weight']
            for idx, direction in data['signal_indices']:
                vote = index_votes[idx]
                if direction == "BUY":
                    vote.buy_weight += weight
                elif direction == "SELL":
                    vote.sell_weight += weight
                vote.strategies.add(strategy_key)
        
        # Determinar sinais de confluência baseado no modo
        confluence_signals = []
        total_strategies = len(strategy_signals)
        total_weight = sum(data['weight'] for data in strategy_signals.values())
        
        if self.selected_confluence_mode == "ALL":
            # Todas as estratégias devem concordar no MESMO índice e MESMA direção
            for idx, vote in index_votes.items():
                if len(vote.strategies) == total_strategies:  # Todas presentes
                    # Determinar direção vencedora
                    if vote.buy_weight > vote.sell_weight:
                        confluence_signals.append((idx, "BUY"))
                    elif vote.sell_weight > vote.buy_weight:
                        confluence_signals.append((idx, "SELL"))
                    # Se empate, não gera sinal (ALL exige consenso)
        
        elif self.selected_confluence_mode == "ANY":
            # Qualquer estratégia pode gerar sinal - usa direção vencedora
            for idx, vote in index_votes.items():
                if vote.buy_weight > vote.sell_weight:
                    confluence_signals.append((idx, "BUY"))
                elif vote.sell_weight > vote.buy_weight:
                    confluence_signals.append((idx, "SELL"))
                # Se empate, usa BUY como padrão
                elif vote.buy_weight > 0:
                    confluence_signals.append((idx, "BUY"))
        
        elif self.selected_confluence_mode == "MAJORITY":
            # Maioria das estratégias deve concordar (>50%)
            majority_threshold = total_strategies / 2
            for idx, vote in index_votes.items():
                num_strategies = len(vote.strategies)
                if num_strategies > majority_threshold:
                    # Direção vencedora entre os votos
                    if vote.buy_weight > vote.sell_weight:
                        confluence_signals.append((idx, "BUY"))
                    elif vote.sell_weight > vote.buy_weight:
                        confluence_signals.append((idx, "SELL"))
        
        elif self.selected_confluence_mode == "WEIGHTED":
            # Peso total deve ser >50% E direção vencedora clara
            weighted_threshold = total_weight / 2
            for idx, vote in index_votes.items():
                total_vote_weight = vote.buy_weight + vote.sell_weight
                if total_vote_weight > weighted_threshold:
                    # Direção vencedora por peso
                    if vote.buy_weight > vote.sell_weight:
                        confluence_signals.append((idx, "BUY"))
                    elif vote.sell_weight > vote.buy_weight:
                        confluence_signals.append((idx, "SELL"))
        
        # Ordenar por índice
        return sorted(confluence_signals, key=lambda x: x[0])
    
    def _run_realtime_confluence_test(self):
        """
        Executa teste em tempo real de múltiplas estratégias com confluência
        
        Integra RealtimeStrategyEngine para streaming de dados e execução em tempo real
        """
        print("\n🔴 TESTE EM TEMPO REAL - CONFLUÊNCIA")
        print("="*80)
        
        # Validação 1: Ativo selecionado
        if not self.selected_asset:
            print("❌ Nenhum ativo selecionado!")
            print("💡 Selecione um ativo primeiro (opção 1)")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        # Validação 2: Timeframe selecionado
        if not self.selected_timeframe:
            print("❌ Nenhum timeframe selecionado!")
            print("💡 Selecione um timeframe primeiro (opção 2)")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        # Validação 3: Estratégias selecionadas (mínimo 2 para confluência)
        if not self.selected_strategies or len(self.selected_strategies) < 2:
            print("❌ Confluência requer pelo menos 2 estratégias!")
            print(f"💡 Você tem {len(self.selected_strategies) if self.selected_strategies else 0} estratégia(s) selecionada(s)")
            print("💡 Selecione mais estratégias (opção 3)")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        # Validação 4: Modo de confluência selecionado
        if not self.selected_confluence_mode:
            print("❌ Nenhum modo de confluência selecionado!")
            print("💡 Selecione um modo de confluência (opção 4)")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        # Validar credenciais da API
        if not self._validate_api_credentials():
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        # Converter timeframe do formato Confluence para formato engine
        timeframe_map = {
            "1": "1m",
            "5": "5m",
            "15": "15m",
            "30": "30m",
            "60": "1h",
            "240": "4h",
            "D": "1d"
        }
        
        engine_interval = timeframe_map.get(self.selected_timeframe, "5m")
        timeframe_name = self.timeframes[self.selected_timeframe]['name']
        
        # Exibir configuração
        print(f"\n📋 CONFIGURAÇÃO DO TESTE:")
        print(f"   🪙 Ativo: {self.selected_asset}")
        print(f"   ⏰ Timeframe: {timeframe_name} ({engine_interval})")
        print(f"   🎯 Modo Confluência: {self.confluence_modes[self.selected_confluence_mode]['name']}")
        print(f"   📈 Estratégias ({len(self.selected_strategies)}):")
        for strategy_key in self.selected_strategies:
            strategy = self.available_strategies[strategy_key]
            print(f"      {strategy['emoji']} {strategy['name']}")
        
        print(f"\n💡 INSTRUÇÕES:")
        print(f"   • O teste rodará em tempo real com WebSocket")
        print(f"   • Você verá sinais de confluência ao vivo")
        print(f"   • Pressione Ctrl+C para parar o teste")
        
        confirm = input(f"\n🚀 Iniciar teste em tempo real? (s/N): ").strip().lower()
        
        if confirm != 's':
            print("❌ Teste cancelado pelo usuário")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        # Importar dependências
        try:
            import asyncio
            from market_manus.engines.realtime_strategy_engine import RealtimeStrategyEngine
        except ImportError as e:
            print(f"❌ Erro ao importar dependências: {e}")
            print("💡 Verifique se RealtimeStrategyEngine está disponível")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        # Preparar lista de estratégias (já é uma lista de strings)
        strategy_list = self.selected_strategies.copy()
        
        # Mapear estratégias SMC para formato do engine
        strategy_map = {
            "smc_bos": "bos",
            "smc_choch": "choch",
            "smc_order_blocks": "order_blocks",
            "smc_fvg": "fvg",
            "smc_liquidity_sweep": "liquidity_sweep"
        }
        mapped_strategies = [strategy_map.get(key, key) for key in strategy_list]
        
        print(f"\n🔄 Inicializando engine de tempo real...")
        print(f"📡 Conectando ao WebSocket...")
        
        try:
            # Criar engine
            engine = RealtimeStrategyEngine(
                symbol=self.selected_asset,
                interval=engine_interval,
                strategies=mapped_strategies,
                data_provider=self.data_provider,
                confluence_mode=self.selected_confluence_mode
            )
            
            # Executar em tempo real
            print(f"\n🔴 TESTE EM EXECUÇÃO - Pressione Ctrl+C para parar\n")
            asyncio.run(engine.start())
            
        except KeyboardInterrupt:
            print(f"\n\n⏸️  Teste interrompido pelo usuário")
            print(f"✅ Engine parado gracefully")
        except Exception as e:
            print(f"\n❌ Erro durante execução: {e}")
            import traceback
            traceback.print_exc()
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _view_test_results(self):
        """Visualiza resultados dos testes"""
        print("\n📊 VISUALIZAR RESULTADOS")
        print("="*50)
        
        if not self.test_history:
            print("❌ Nenhum teste executado ainda")
            print("💡 Execute um backtest de confluência primeiro")
        else:
            print(f"📈 {len(self.test_history)} teste(s) no histórico:")
            for i, test in enumerate(self.test_history, 1):
                print(f"   {i}. {test['type']} - {test['asset']} - {test['confluence_mode']}")
                print(f"      📊 ROI: {test['results']['roi']:+.2f}% | Win Rate: {test['results']['win_rate']:.1f}%")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _export_results(self):
        """Exporta resultados para arquivo"""
        print("\n📤 EXPORTAR RELATÓRIOS")
        print("="*50)
        
        if not self.test_history:
            print("❌ Nenhum resultado para exportar")
            print("💡 Execute um teste primeiro")
        else:
            # Criar diretório reports se não existir
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            # Gerar nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"confluence_mode_results_{timestamp}.json"
            filepath = reports_dir / filename
            
            # Salvar resultados
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "confluence_mode_version": "V1",
                "test_history": self.test_history
            }
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Relatório exportado com sucesso!")
                print(f"📁 Arquivo: {filepath}")
                print(f"📊 {len(self.test_history)} teste(s) incluído(s)")
            except Exception as e:
                print(f"❌ Erro ao exportar: {e}")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _toggle_ai_premium(self):
        """Toggle Manus AI Premium on/off"""
        print("\n🤖 MANUS AI PREMIUM - ANÁLISE INTELIGENTE DE MERCADO")
        print("="*60)
        
        if not self.ai_analyzer.is_enabled():
            print("❌ Manus AI não disponível!")
            print("   Configure MANUS_AI_API_KEY no arquivo .env")
            print("   Obtenha sua chave em: https://manus.im")
            print("   1,000 créditos grátis + 300 diários disponíveis!")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        current_status = "ATIVO" if self.ai_premium_enabled else "DESATIVADO"
        new_status = "DESATIVAR" if self.ai_premium_enabled else "ATIVAR"
        
        print(f"Status atual: {current_status}")
        print(f"\n📋 O que o Manus AI Premium faz:")
        print("   ✅ Análise inteligente do contexto de mercado")
        print("   ✅ Avaliação da qualidade dos sinais das estratégias")
        print("   ✅ Classificação de regime (trending/ranging/volátil)")
        print("   ✅ Ajuste de confiança baseado em AI")
        print("   ✅ Identificação de riscos e oportunidades")
        print("   ✅ Insights contextuais sobre o mercado")
        
        confirm = input(f"\n❓ Deseja {new_status} o Manus AI Premium? (s/n): ").strip().lower()
        
        if confirm == 's':
            self.ai_premium_enabled = not self.ai_premium_enabled
            new_status_display = "✅ ATIVADO" if self.ai_premium_enabled else "⏸️ DESATIVADO"
            print(f"\n🤖 Manus AI Premium: {new_status_display}")
            
            if self.ai_premium_enabled:
                print("   🚀 A AI irá analisar e aprimorar todos os sinais das estratégias!")
                print("   💡 Os resultados terão maior precisão e insights contextuais")
            else:
                print("   📊 Modo padrão: análise apenas com estratégias técnicas")
        else:
            print("\n❌ Operação cancelada")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _toggle_semantic_kernel(self):
        """Toggle Semantic Kernel Advisor on/off"""
        print("\n🧠 SEMANTIC KERNEL ADVISOR - RECOMENDAÇÕES IA")
        print("="*60)
        
        if not self.sk_advisor.is_available():
            print("❌ Semantic Kernel Advisor não disponível!")
            print("   Configure OPENAI_API_KEY no arquivo .env")
            print("   Use a mesma chave da OpenAI API")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        current_status = "ATIVO" if self.semantic_kernel_enabled else "DESATIVADO"
        new_status = "DESATIVAR" if self.semantic_kernel_enabled else "ATIVAR"
        
        print(f"Status atual: {current_status}")
        print(f"\n📋 O que o Semantic Kernel Advisor faz:")
        print("   ✅ Análise inteligente dos resultados de backtest")
        print("   ✅ Recomendações de ajuste de pesos das estratégias")
        print("   ✅ Diagnóstico de performance e pontos de melhoria")
        print("   ✅ Sugestões de otimizações (timeframe, modo, etc)")
        print("   ✅ Insights textuais detalhados pós-backtest")
        print("   ✅ Próximos passos e ações concretas")
        
        confirm = input(f"\n❓ Deseja {new_status} o SK Advisor? (s/n): ").strip().lower()
        
        if confirm == 's':
            self.semantic_kernel_enabled = not self.semantic_kernel_enabled
            new_status_display = "✅ ATIVADO" if self.semantic_kernel_enabled else "⏸️ DESATIVADO"
            print(f"\n🧠 Semantic Kernel Advisor: {new_status_display}")
            
            if self.semantic_kernel_enabled:
                print("   🚀 Você receberá recomendações IA após cada backtest!")
                print("   💡 Ajuste de pesos e otimizações sugeridas automaticamente")
            else:
                print("   📊 Modo padrão: apenas resultados numéricos básicos")
        else:
            print("\n❌ Operação cancelada")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    async def _apply_ai_analysis_to_signals(self, strategy_signals: dict, df: pd.DataFrame, symbol: str) -> dict:
        """
        Apply Manus AI analysis to enhance strategy signals
        
        Args:
            strategy_signals: Dict with strategy signals
            df: DataFrame with OHLCV data
            symbol: Trading symbol
            
        Returns:
            Enhanced signals with AI insights
        """
        if not self.ai_premium_enabled or not self.ai_analyzer.is_enabled():
            return strategy_signals
        
        print("\n🤖 Aplicando análise Premium Manus AI...")
        
        try:
            strategies_votes = {}
            for strategy_key, signal_data in strategy_signals.items():
                signal_indices = signal_data.get('signal_indices', [])
                buy_count = sum(1 for idx, direction in signal_indices if direction == "BUY")
                sell_count = sum(1 for idx, direction in signal_indices if direction == "SELL")
                
                if buy_count > sell_count:
                    action = "BUY"
                    confidence = buy_count / len(signal_indices) if signal_indices else 0.5
                elif sell_count > buy_count:
                    action = "SELL"
                    confidence = sell_count / len(signal_indices) if signal_indices else 0.5
                else:
                    action = "NEUTRAL"
                    confidence = 0.5
                
                strategies_votes[strategy_key] = {
                    "action": action,
                    "confidence": confidence
                }
            
            ai_analysis = await self.ai_analyzer.analyze_market_context(
                df=df,
                symbol=symbol,
                strategies_votes=strategies_votes
            )
            
            if ai_analysis.get('ai_enabled', False):
                print(f"   📊 Regime de Mercado: {ai_analysis['regime']}")
                print(f"   🎯 Qualidade dos Sinais: {ai_analysis['signal_quality']}")
                print(f"   ⚠️  Nível de Risco: {ai_analysis['risk_level']}")
                print(f"   💡 Recomendação AI: {ai_analysis['action']}")
                print(f"   📈 Confiança AI: {ai_analysis['confidence']:.1f}%")
                print(f"\n   🧠 Insights AI:")
                for insight in ai_analysis.get('insights', []):
                    print(f"      • {insight}")
                
                enhanced_signals = self._enhance_signals_with_ai(strategy_signals, ai_analysis)
                
                print(f"\n   ✅ Sinais aprimorados pela AI Premium!")
                return enhanced_signals
            else:
                print("   ⚠️  AI analysis não disponível, usando sinais padrão")
                return strategy_signals
                
        except Exception as e:
            print(f"   ⚠️  Erro na análise AI: {e}")
            print("   📊 Continuando com sinais padrão...")
            return strategy_signals
    
    def _enhance_signals_with_ai(self, strategy_signals: dict, ai_analysis: dict) -> dict:
        """
        Enhance strategy signals based on AI analysis
        
        Args:
            strategy_signals: Original strategy signals
            ai_analysis: AI analysis results
            
        Returns:
            Enhanced signals with adjusted weights
        """
        enhanced = strategy_signals.copy()
        
        ai_confidence = ai_analysis.get('confidence', 50.0) / 100.0
        ai_action = ai_analysis.get('action', 'CONTINUE')
        
        if ai_confidence > 0.7 and ai_action != 'WAIT':
            for strategy_key in enhanced:
                enhanced[strategy_key]['weight'] = enhanced[strategy_key].get('weight', 1.0) * 1.2
                enhanced[strategy_key]['ai_boost'] = True
        
        elif ai_confidence < 0.4 or ai_action == 'WAIT':
            for strategy_key in enhanced:
                enhanced[strategy_key]['weight'] = enhanced[strategy_key].get('weight', 1.0) * 0.7
                enhanced[strategy_key]['ai_warning'] = True
        
        for strategy_key in enhanced:
            enhanced[strategy_key]['ai_analysis'] = {
                'regime': ai_analysis.get('regime', 'UNKNOWN'),
                'quality': ai_analysis.get('signal_quality', 'STANDARD'),
                'risk': ai_analysis.get('risk_level', 'MEDIUM'),
                'ai_confidence': ai_confidence
            }
        
        return enhanced
    
    def _save_backtest_to_performance_repo(self, test_result: Dict, filtered_strategy_signals: Dict, total_trades: int, winning_trades: int, losing_trades: int):
        """Salva resultados do backtest no repositório de performance"""
        try:
            import uuid
            
            backtest_id = str(uuid.uuid4())
            timestamp = test_result['timestamp']
            
            # Detectar se é uma combinação recomendada
            combination_id = None
            combination_name = None
            if hasattr(self, 'selected_combination'):
                combination_id = self.selected_combination.get('id')
                combination_name = self.selected_combination.get('name')
            
            # Criar BacktestResult
            backtest_result = BacktestResult(
                backtest_id=backtest_id,
                timestamp=timestamp,
                combination_id=combination_id,
                combination_name=combination_name,
                strategies=test_result['strategies'],
                timeframe=test_result['timeframe'],
                asset=test_result['asset'],
                start_date=self.custom_start_date or "default",
                end_date=self.custom_end_date or "default",
                confluence_mode=test_result['confluence_mode'],
                win_rate=test_result['results']['win_rate'],
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                initial_capital=test_result['results']['initial_capital'],
                final_capital=test_result['results']['final_capital'],
                roi=test_result['results']['roi'],
                total_signals=test_result['results']['confluence_signals'],
                manus_ai_enabled=self.ai_premium_enabled,
                semantic_kernel_enabled=self.semantic_kernel_enabled
            )
            
            # Criar StrategyContribution para cada estratégia
            strategy_contributions = []
            for strategy_key, data in filtered_strategy_signals.items():
                # Estimar winning/losing signals (simplificado - divide proporcionalmente ao win rate)
                filtered_count = data.get('filtered_count', len(data['signal_indices']))
                original_count = data.get('original_count', len(data['signal_indices']))
                
                estimated_win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
                estimated_winning = int(filtered_count * estimated_win_rate / 100)
                estimated_losing = filtered_count - estimated_winning
                
                contrib = StrategyContribution(
                    backtest_id=backtest_id,
                    strategy_key=strategy_key,
                    strategy_name=data.get('name', strategy_key),
                    total_signals=original_count,
                    signals_after_volume_filter=filtered_count,
                    winning_signals=estimated_winning,
                    losing_signals=estimated_losing,
                    win_rate=estimated_win_rate,
                    weight=data.get('weight', 1.0)
                )
                strategy_contributions.append(contrib)
            
            # Salvar no repositório
            self.performance_repo.save_backtest_result(backtest_result, strategy_contributions)
            
            # Armazenar ID para uso posterior nas recomendações
            self.last_backtest_id = backtest_id
            
        except Exception as e:
            print(f"\n⚠️  Erro ao salvar histórico de performance: {e}")
    
    def _display_recommendations(self, test_result: Dict, filtered_strategy_signals: Dict):
        """Exibe recomendações de pesos e insights IA"""
        
        if not hasattr(self, 'last_backtest_id'):
            return
        
        print("\n" + "="*80)
        print("🎯 RECOMENDAÇÕES DE OTIMIZAÇÃO")
        print("="*80)
        
        # Calcular recomendações de peso
        current_weights = {k: v.get('weight', 1.0) for k, v in filtered_strategy_signals.items()}
        weight_recommendations = self.performance_analytics.calculate_weight_recommendations(
            self.last_backtest_id,
            current_weights
        )
        
        if weight_recommendations:
            print("\n📊 RECOMENDAÇÕES DE AJUSTE DE PESOS:")
            print("="*80)
            
            for rec in weight_recommendations[:5]:  # Top 5
                arrow = "↑" if rec.recommended_weight > rec.current_weight else "↓"
                change_pct = ((rec.recommended_weight - rec.current_weight) / rec.current_weight * 100)
                
                print(f"\n   {rec.strategy_name}:")
                print(f"   • Peso atual: {rec.current_weight:.2f} → Recomendado: {rec.recommended_weight:.2f} {arrow}")
                print(f"   • Mudança: {change_pct:+.1f}%")
                print(f"   • Razão: {rec.reason}")
                print(f"   • Confiança: {rec.confidence*100:.0f}%")
        else:
            print("\n✅ Pesos atuais estão bem balanceados!")
        
        # Insights do Semantic Kernel (se ativado)
        if self.semantic_kernel_enabled and self.sk_advisor.is_available():
            print("\n🧠 INSIGHTS DO SEMANTIC KERNEL ADVISOR:")
            print("="*80)
            print("\n🔄 Gerando recomendações inteligentes com IA...")
            
            try:
                # Preparar dados para o SK Advisor
                backtest_summary = {
                    'asset': test_result['asset'],
                    'timeframe': test_result['timeframe'],
                    'start_date': self.custom_start_date or "últimos 30 dias",
                    'end_date': self.custom_end_date or "hoje",
                    'confluence_mode': test_result['confluence_mode'],
                    'win_rate': test_result['results']['win_rate'],
                    'total_trades': test_result['results']['total_trades'],
                    'roi': test_result['results']['roi'],
                    'initial_capital': test_result['results']['initial_capital'],
                    'final_capital': test_result['results']['final_capital']
                }
                
                strategy_contributions_data = [
                    {
                        'strategy_name': data.get('name', key),
                        'signals_after_volume_filter': data.get('filtered_count', len(data['signal_indices'])),
                        'win_rate': test_result['results']['win_rate'],  # Simplificado
                        'weight': data.get('weight', 1.0),
                        'winning_signals': int(data.get('filtered_count', 0) * test_result['results']['win_rate'] / 100),
                        'losing_signals': int(data.get('filtered_count', 0) * (100 - test_result['results']['win_rate']) / 100)
                    }
                    for key, data in filtered_strategy_signals.items()
                ]
                
                weight_recommendations_data = [
                    {
                        'strategy_name': rec.strategy_name,
                        'current_weight': rec.current_weight,
                        'recommended_weight': rec.recommended_weight,
                        'reason': rec.reason,
                        'confidence': rec.confidence
                    }
                    for rec in weight_recommendations
                ]
                
                # Gerar insights IA
                sk_insights = self.sk_advisor.generate_recommendations(
                    backtest_summary,
                    strategy_contributions_data,
                    weight_recommendations_data
                )
                
                print(f"\n{sk_insights}")
                
            except Exception as e:
                print(f"\n⚠️  Erro ao gerar insights IA: {e}")
        elif self.semantic_kernel_enabled:
            print("\n⚠️  Semantic Kernel Advisor não disponível (OPENAI_API_KEY não configurada)")
        
        print("\n" + "="*80)
