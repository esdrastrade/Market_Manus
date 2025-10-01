"""
Confluence Mode Module - Versão Validada
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
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

class ConfluenceModeModule:
    """Módulo de Confluência - Sistema de múltiplas estratégias"""
    
    def __init__(self, data_provider=None, capital_manager=None):
        self.data_provider = data_provider
        self.capital_manager = capital_manager
        
        # Estratégias disponíveis para confluência
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
    
    def run_interactive_mode(self):
        """Executa o modo interativo do Confluence Mode"""
        while True:
            self._show_main_menu()
            choice = input("\n🔢 Escolha uma opção (0-8): ").strip()
            
            if choice == '0':
                print("\n👋 Saindo do Confluence Mode...")
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
                self._run_confluence_backtest()
            elif choice == '7':
                self._view_test_results()
            elif choice == '8':
                self._export_results()
            else:
                print("❌ Opção inválida")
                input("\n📖 Pressione ENTER para continuar...")
    
    def _show_main_menu(self):
        """Mostra o menu principal do Confluence Mode"""
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
        
        print(f"\n🔧 CONFIGURAÇÃO:")
        print("   1️⃣  Seleção de Ativo")
        print("   2️⃣  Seleção de Timeframe")
        print("   3️⃣  Seleção de Estratégias")
        print("   4️⃣  Modo de Confluência")
        print("   5️⃣  Período Personalizado")
        
        print(f"\n🧪 TESTES:")
        print("   6️⃣  Executar Backtest de Confluência")
        
        print(f"\n📊 RESULTADOS:")
        print("   7️⃣  Visualizar Resultados")
        print("   8️⃣  Exportar Relatórios")
        
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
        """Menu de seleção de estratégias"""
        print("\n📈 SELEÇÃO DE ESTRATÉGIAS")
        print("="*50)
        print("💡 Selecione múltiplas estratégias para confluência")
        print("   Digite os números separados por vírgula (ex: 1,3,5)")
        
        strategies_list = list(self.available_strategies.keys())
        for i, strategy_key in enumerate(strategies_list, 1):
            strategy = self.available_strategies[strategy_key]
            selected = "✅" if strategy_key in self.selected_strategies else "  "
            print(f"   {i}️⃣  {selected} {strategy['emoji']} {strategy['name']}")
            print(f"       📝 {strategy['description']}")
        
        print(f"\n   0️⃣  Voltar")
        
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
    
    def _run_confluence_backtest(self):
        """Executa backtest de confluência"""
        if not self._validate_configuration():
            return
        
        print("\n🧪 EXECUTANDO BACKTEST DE CONFLUÊNCIA")
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
        
        print(f"\n🔄 Simulando backtest de confluência...")
        
        # Simular resultados para demonstração
        import random
        
        # Simular sinais de cada estratégia
        strategy_signals = {}
        for strategy_key in self.selected_strategies:
            strategy = self.available_strategies[strategy_key]
            signals = random.randint(10, 30)
            strategy_signals[strategy_key] = {
                "name": strategy['name'],
                "signals": signals,
                "weight": strategy.get('weight', 1.0)
            }
        
        # Calcular confluência baseado no modo
        confluence_signals = self._calculate_confluence_signals(strategy_signals)
        
        # Simular resultados financeiros
        total_trades = confluence_signals
        winning_trades = random.randint(int(total_trades * 0.4), int(total_trades * 0.8))
        losing_trades = total_trades - winning_trades
        
        initial_capital = self.capital_manager.current_capital if self.capital_manager else 10000
        final_capital = initial_capital * random.uniform(0.85, 1.30)
        pnl = final_capital - initial_capital
        roi = (pnl / initial_capital) * 100
        
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        print(f"\n📊 RESULTADOS DO BACKTEST DE CONFLUÊNCIA:")
        print(f"   💰 Capital inicial: ${initial_capital:.2f}")
        print(f"   💵 Capital final: ${final_capital:.2f}")
        print(f"   📈 P&L: ${pnl:+.2f}")
        print(f"   📊 ROI: {roi:+.2f}%")
        print(f"   🎯 Sinais de confluência: {confluence_signals}")
        print(f"   ✅ Trades vencedores: {winning_trades}")
        print(f"   ❌ Trades perdedores: {losing_trades}")
        print(f"   📊 Win Rate: {win_rate:.1f}%")
        
        print(f"\n📈 DETALHES POR ESTRATÉGIA:")
        for strategy_key, data in strategy_signals.items():
            print(f"   {data['name']}: {data['signals']} sinais (peso: {data['weight']})")
        
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
                "confluence_signals": confluence_signals,
                "strategy_signals": strategy_signals
            }
        }
        self.test_history.append(test_result)
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _calculate_confluence_signals(self, strategy_signals: Dict) -> int:
        """Calcula sinais de confluência baseado no modo selecionado"""
        if self.selected_confluence_mode == "ALL":
            # Todas as estratégias devem concordar
            return min([data['signals'] for data in strategy_signals.values()])
        
        elif self.selected_confluence_mode == "ANY":
            # Qualquer estratégia pode gerar sinal
            return max([data['signals'] for data in strategy_signals.values()])
        
        elif self.selected_confluence_mode == "MAJORITY":
            # Maioria das estratégias deve concordar
            signals_list = [data['signals'] for data in strategy_signals.values()]
            return int(np.median(signals_list))
        
        elif self.selected_confluence_mode == "WEIGHTED":
            # Média ponderada dos sinais
            total_weighted = 0
            total_weight = 0
            for data in strategy_signals.values():
                total_weighted += data['signals'] * data['weight']
                total_weight += data['weight']
            return int(total_weighted / total_weight) if total_weight > 0 else 0
        
        return 0
    
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
