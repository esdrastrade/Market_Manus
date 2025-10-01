"""
Confluence Mode Module - VERSÃO CORRIGIDA FINAL
Sistema de confluência para análise de múltiplas estratégias
"""

import os
import json
import zipfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class ConfluenceModeManager:
    """
    Gerenciador do modo de confluência - VERSÃO CORRIGIDA FINAL
    """
    
    def __init__(self, data_provider, capital_manager, strategy_manager):
        self.data_provider = data_provider
        self.capital_manager = capital_manager
        self.strategy_manager = strategy_manager
        
        # Configurações padrão
        self.selected_asset = None
        self.selected_timeframe = None
        self.selected_strategies = []
        self.confluence_mode = 'MAJORITY'
        self.strategy_weights = {}
        self.start_date = None
        self.end_date = None
        
        # Assets disponíveis
        self.available_assets = {
            'BTCUSDT': {'name': 'Bitcoin', 'emoji': '🪙'},
            'ETHUSDT': {'name': 'Ethereum', 'emoji': '💎'},
            'BNBUSDT': {'name': 'Binance Coin', 'emoji': '🟡'},
            'SOLUSDT': {'name': 'Solana', 'emoji': '⚡'},
            'XRPUSDT': {'name': 'XRP', 'emoji': '💧'},
            'ADAUSDT': {'name': 'Cardano', 'emoji': '🔵'},
            'DOGEUSDT': {'name': 'Dogecoin', 'emoji': '🐕'},
            'MATICUSDT': {'name': 'Polygon', 'emoji': '🟣'}
        }
        
        # Timeframes disponíveis
        self.available_timeframes = {
            '1m': '1 minuto',
            '5m': '5 minutos', 
            '15m': '15 minutos',
            '30m': '30 minutos',
            '1h': '1 hora',
            '4h': '4 horas',
            '1d': '1 dia'
        }
        
        # Modos de confluência
        self.confluence_modes = {
            'ALL': 'Todas as estratégias devem concordar',
            'ANY': 'Qualquer estratégia pode gerar sinal',
            'MAJORITY': 'Maioria das estratégias deve concordar',
            'WEIGHTED': 'Voto ponderado baseado em pesos'
        }
    
    def display_header(self):
        """Exibe cabeçalho do Confluence Mode"""
        print("\n" + "="*80)
        print("🎯 CONFLUENCE MODE - SISTEMA DE CONFLUÊNCIA")
        print("="*80)
        
        # Status atual
        print("📊 CONFIGURAÇÃO ATUAL:")
        asset_status = f"✅ {self.selected_asset}" if self.selected_asset else "❌ Não selecionado"
        print(f"   🪙 Ativo: {asset_status}")
        
        timeframe_status = f"✅ {self.available_timeframes.get(self.selected_timeframe, self.selected_timeframe)}" if self.selected_timeframe else "❌ Não selecionado"
        print(f"   ⏰ Timeframe: {timeframe_status}")
        
        strategies_status = f"✅ {len(self.selected_strategies)} selecionadas" if self.selected_strategies else "❌ Nenhuma selecionada"
        print(f"   📈 Estratégias: {strategies_status}")
        
        print(f"   🎯 Modo Confluência: ✅ {self.confluence_mode}")
        
        if self.start_date and self.end_date:
            print(f"   📅 Período: {self.start_date.strftime('%Y-%m-%d')} até {self.end_date.strftime('%Y-%m-%d')}")
        else:
            print(f"   📅 Período: Padrão (últimos 30 dias)")
        
        # Capital
        try:
            capital_info = self.capital_manager.get_capital_summary()
            print(f"   💰 Capital: ${capital_info['current_capital']:,.2f}")
            print(f"   💼 Position Size: ${capital_info['current_capital'] * capital_info['position_size_percent'] / 100:,.2f}")
        except:
            print(f"   💰 Capital: $10,000.00")
            print(f"   💼 Position Size: $200.00")
        
        print("-"*80)
    
    def display_main_menu(self):
        """Exibe menu principal do Confluence Mode"""
        print("\n🔧 CONFIGURAÇÃO:")
        print("   1️⃣  Seleção de Ativo")
        print("   2️⃣  Seleção de Timeframe")
        print("   3️⃣  Seleção de Estratégias")
        print("   4️⃣  Modo de Confluência")
        print("   5️⃣  Período Personalizado")
        print("   6️⃣  Configuração de Capital")
        
        print("\n🧪 TESTES:")
        print("   7️⃣  Executar Backtest de Confluência")
        
        print("\n📊 RESULTADOS:")
        print("   8️⃣  Visualizar Resultados")
        print("   9️⃣  Exportar Relatórios")
        
        print("\n   0️⃣  Voltar ao Menu Principal")
        print("-"*80)
    
    def strategy_selection_menu(self):
        """Menu de seleção de estratégias - VERSÃO CORRIGIDA FINAL"""
        print("\n📈 SELEÇÃO DE ESTRATÉGIAS")
        print("="*50)
        
        try:
            # Obter lista de estratégias disponíveis
            available_strategies = self.strategy_manager.get_strategy_list()
            
            print(f"📊 Estratégias Disponíveis ({len(available_strategies)}):\n")
            
            # Exibir cada estratégia individualmente
            for i, strategy_name in enumerate(available_strategies, 1):
                selected = "✅" if strategy_name in self.selected_strategies else "  "
                
                # CORREÇÃO FINAL: Chamar get_strategy_display_info para cada estratégia
                try:
                    info = self.strategy_manager.get_strategy_display_info(strategy_name)
                    print(f"{selected} {i}️⃣  {info['emoji']} {info['display_name']}")
                    print(f"      Tipo: {info['type']} | Risco: {info.get('risk_level', 'medium').title()}")
                    print(f"      Timeframes: {', '.join(info.get('best_timeframes', ['15m', '30m']))}")
                    print("")
                except Exception as e:
                    # Fallback robusto para estratégias sem display_info
                    try:
                        description = self.strategy_manager.get_strategy_description(strategy_name)
                        print(f"{selected} {i}️⃣  📊 {strategy_name}")
                        print(f"      {description}")
                        print(f"      Tipo: Trading | Configurável: ✅")
                        print("")
                    except:
                        print(f"{selected} {i}️⃣  📊 {strategy_name}")
                        print(f"      Estratégia de trading disponível")
                        print(f"      Tipo: Trading | Status: Ativo")
                        print("")
            
            print(f"📊 Estratégias selecionadas: {len(self.selected_strategies)}")
            if self.selected_strategies:
                print(f"✅ Selecionadas: {', '.join(self.selected_strategies)}")
            
            print("\n🔧 OPÇÕES:")
            print("   A️⃣  Selecionar Todas")
            print("   C️⃣  Limpar Seleção")
            print("   0️⃣  Voltar")
            
            choice = input("\n🔢 Escolha uma opção: ").strip().upper()
            
            if choice == '0':
                return
            elif choice == 'A':
                self.selected_strategies = available_strategies.copy()
                print(f"✅ Todas as {len(available_strategies)} estratégias selecionadas")
            elif choice == 'C':
                self.selected_strategies = []
                print("✅ Seleção limpa")
            else:
                try:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(available_strategies):
                        strategy_name = available_strategies[choice_num - 1]
                        
                        # Obter nome de exibição da estratégia
                        try:
                            info = self.strategy_manager.get_strategy_display_info(strategy_name)
                            display_name = info['display_name']
                        except:
                            display_name = strategy_name
                        
                        if strategy_name in self.selected_strategies:
                            self.selected_strategies.remove(strategy_name)
                            print(f"❌ {display_name} removida")
                        else:
                            self.selected_strategies.append(strategy_name)
                            print(f"✅ {display_name} adicionada")
                    else:
                        print("❌ Opção inválida")
                except ValueError:
                    print("❌ Opção inválida")
                    
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            print("\n🔧 Usando estratégias básicas como fallback...")
            
            # Fallback com estratégias básicas
            basic_strategies = ['RSI_MEAN_REVERSION', 'EMA_CROSSOVER', 'BOLLINGER_BREAKOUT', 'MACD']
            
            print("📊 Estratégias Básicas Disponíveis:")
            for i, strategy in enumerate(basic_strategies, 1):
                selected = "✅" if strategy in self.selected_strategies else "  "
                print(f"{selected} {i}️⃣  📊 {strategy}")
                print(f"      Estratégia de trading básica")
                print("")
            
            print("\n🔧 OPÇÕES:")
            print("   A️⃣  Selecionar Todas")
            print("   C️⃣  Limpar Seleção")
            print("   0️⃣  Voltar")
            
            choice = input("\n🔢 Escolha uma opção: ").strip().upper()
            
            if choice == 'A':
                self.selected_strategies = basic_strategies.copy()
                print(f"✅ Todas as {len(basic_strategies)} estratégias selecionadas")
            elif choice == 'C':
                self.selected_strategies = []
                print("✅ Seleção limpa")
            elif choice.isdigit():
                choice_num = int(choice)
                if 1 <= choice_num <= len(basic_strategies):
                    strategy_name = basic_strategies[choice_num - 1]
                    if strategy_name in self.selected_strategies:
                        self.selected_strategies.remove(strategy_name)
                        print(f"❌ {strategy_name} removida")
                    else:
                        self.selected_strategies.append(strategy_name)
                        print(f"✅ {strategy_name} adicionada")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    # Outros métodos do ConfluenceModeManager...
    def asset_selection_menu(self):
        """Menu de seleção de ativo"""
        print("\n🪙 SELEÇÃO DE ATIVO")
        print("="*50)
        
        for i, (symbol, info) in enumerate(self.available_assets.items(), 1):
            selected = "✅" if symbol == self.selected_asset else "  "
            print(f"{selected} {i}️⃣  {info['emoji']} {symbol} - {info['name']}")
        
        print("\n0️⃣  Voltar")
        
        try:
            choice = input("\n🔢 Escolha um ativo (0-8): ").strip()
            
            if choice == '0':
                return
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(self.available_assets):
                asset_symbol = list(self.available_assets.keys())[choice_num - 1]
                self.selected_asset = asset_symbol
                asset_info = self.available_assets[asset_symbol]
                print(f"✅ Ativo selecionado: {asset_info['emoji']} {asset_symbol}")
            else:
                print("❌ Opção inválida")
                
        except ValueError:
            print("❌ Opção inválida")
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def timeframe_selection_menu(self):
        """Menu de seleção de timeframe"""
        print("\n⏰ SELEÇÃO DE TIMEFRAME")
        print("="*50)
        
        for i, (tf, description) in enumerate(self.available_timeframes.items(), 1):
            selected = "✅" if tf == self.selected_timeframe else "  "
            print(f"{selected} {i}️⃣  {tf} - {description}")
        
        print("\n0️⃣  Voltar")
        
        try:
            choice = input("\n🔢 Escolha um timeframe (0-7): ").strip()
            
            if choice == '0':
                return
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(self.available_timeframes):
                timeframe = list(self.available_timeframes.keys())[choice_num - 1]
                self.selected_timeframe = timeframe
                print(f"✅ Timeframe selecionado: {self.available_timeframes[timeframe]}")
            else:
                print("❌ Opção inválida")
                
        except ValueError:
            print("❌ Opção inválida")
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def run(self):
        """Loop principal do Confluence Mode"""
        while True:
            try:
                self.display_header()
                self.display_main_menu()
                
                choice = input("🔢 Escolha uma opção (0-9): ").strip()
                
                if choice == '0':
                    break
                elif choice == '1':
                    self.asset_selection_menu()
                elif choice == '2':
                    self.timeframe_selection_menu()
                elif choice == '3':
                    self.strategy_selection_menu()
                elif choice == '4':
                    print("\n🎯 Modo de confluência: Em desenvolvimento")
                    input("\n📖 Pressione ENTER para continuar...")
                elif choice == '5':
                    print("\n📅 Período personalizado: Em desenvolvimento")
                    input("\n📖 Pressione ENTER para continuar...")
                elif choice == '6':
                    print("\n💰 Configuração de capital: Em desenvolvimento")
                    input("\n📖 Pressione ENTER para continuar...")
                elif choice == '7':
                    print("\n🧪 Backtest de confluência: Em desenvolvimento")
                    input("\n📖 Pressione ENTER para continuar...")
                elif choice == '8':
                    print("\n📊 Visualizar resultados: Em desenvolvimento")
                    input("\n📖 Pressione ENTER para continuar...")
                elif choice == '9':
                    print("\n📤 Exportar relatórios: Em desenvolvimento")
                    input("\n📖 Pressione ENTER para continuar...")
                else:
                    print("❌ Opção inválida. Escolha entre 0-9.")
                    input("\n📖 Pressione ENTER para continuar...")
                
            except KeyboardInterrupt:
                print("\n\n⏹️ Confluence Mode interrompido pelo usuário")
                break
            except Exception as e:
                print(f"\n❌ Erro inesperado: {e}")
                input("\n📖 Pressione ENTER para continuar...")

# Manter compatibilidade com código existente
class ConfluenceModeModule:
    """Classe de compatibilidade"""
    def __init__(self, data_provider, capital_manager, strategy_manager):
        self.manager = ConfluenceModeManager(data_provider, capital_manager, strategy_manager)
    
    def run(self):
        return self.manager.run()

if __name__ == "__main__":
    print("🎯 Confluence Mode Module - VERSÃO CORRIGIDA FINAL")
    print("Este módulo deve ser importado pelo sistema principal")
