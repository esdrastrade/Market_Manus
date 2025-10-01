#!/usr/bin/env python3
"""
MARKET MANUS CLI COMPLETE - Sistema de Trading Completo
CLI robusto com Strategy Lab, Confluence Mode e persistência de capital
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/market_manus.log'),
        logging.StreamHandler()
    ]
)

# Criar diretório de logs
Path('logs').mkdir(exist_ok=True)

try:
    from strategy_contract import list_available_strategies, STRATEGY_REGISTRY_V2
    from bybit_provider import BybitDataProvider
    from capital_persistence import CapitalManager
    from strategy_lab import StrategyLab, BacktestConfig, ConfluenceMode
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("Certifique-se de que todos os módulos estão no mesmo diretório")
    sys.exit(1)


class MarketManusCompleteSystem:
    """
    Sistema completo Market Manus com CLI robusto
    
    Features:
    - Strategy Lab completo
    - Confluence Mode calibrado
    - Persistência de capital
    - Multi-seleção de estratégias
    - Dados reais da Bybit
    - Exportação de relatórios
    - UX aprimorada
    """
    
    def __init__(self):
        """Inicializa sistema completo"""
        self.logger = logging.getLogger(__name__)
        
        # Inicializar componentes
        try:
            self.data_provider = BybitDataProvider()
            self.capital_manager = CapitalManager()
            self.strategy_lab = StrategyLab(self.data_provider, self.capital_manager)
            
            # Estado da sessão
            self.current_symbol = self.capital_manager.settings.get('last_symbol', 'BTCUSDT')
            self.current_timeframe = self.capital_manager.settings.get('last_timeframe', '1h')
            self.selected_strategies = self.capital_manager.settings.get('last_strategies', ['rsi_mean_reversion'])
            self.confluence_mode = 'majority'
            self.min_strength = 0.3
            
            # Períodos pré-definidos
            self.predefined_periods = self._get_predefined_periods()
            
            self.logger.info("Market Manus Complete System inicializado")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar sistema: {e}")
            raise
    
    def _get_predefined_periods(self) -> Dict[str, Dict]:
        """Define períodos pré-configurados incluindo trimestrais"""
        now = datetime.now(timezone.utc)
        current_year = now.year
        
        return {
            '1': {'name': '7 dias', 'start': now - timedelta(days=7), 'end': now},
            '2': {'name': '30 dias', 'start': now - timedelta(days=30), 'end': now},
            '3': {'name': '90 dias', 'start': now - timedelta(days=90), 'end': now},
            '4': {'name': '6 meses', 'start': now - timedelta(days=180), 'end': now},
            '5': {'name': '1 ano', 'start': now - timedelta(days=365), 'end': now},
            '6': {'name': f'Q1 {current_year}', 'start': datetime(current_year, 1, 1, tzinfo=timezone.utc), 'end': datetime(current_year, 3, 31, tzinfo=timezone.utc)},
            '7': {'name': f'Q2 {current_year}', 'start': datetime(current_year, 4, 1, tzinfo=timezone.utc), 'end': datetime(current_year, 6, 30, tzinfo=timezone.utc)},
            '8': {'name': f'Q3 {current_year}', 'start': datetime(current_year, 7, 1, tzinfo=timezone.utc), 'end': datetime(current_year, 9, 30, tzinfo=timezone.utc)},
            '9': {'name': f'Q4 {current_year}', 'start': datetime(current_year, 10, 1, tzinfo=timezone.utc), 'end': datetime(current_year, 12, 31, tzinfo=timezone.utc)},
            '10': {'name': 'YTD (Year to Date)', 'start': datetime(current_year, 1, 1, tzinfo=timezone.utc), 'end': now}
        }
    
    def run(self):
        """Executa CLI principal"""
        try:
            self._show_welcome()
            
            while True:
                try:
                    self._show_main_menu()
                    choice = input("\\n🔢 Escolha uma opção: ").strip()
                    
                    if choice == '0':
                        self._save_session_state()
                        print("\\n👋 Obrigado por usar o Market Manus! Até logo!")
                        break
                    elif choice == '1':
                        self._strategy_lab_menu()
                    elif choice == '2':
                        self._confluence_mode_menu()
                    elif choice == '3':
                        self._capital_dashboard()
                    elif choice == '4':
                        self._connectivity_test()
                    elif choice == '5':
                        self._configuration_menu()
                    elif choice == '6':
                        self._reports_menu()
                    elif choice == '7':
                        self._system_status()
                    elif choice == '8':
                        self._help_menu()
                    else:
                        print("❌ Opção inválida! Tente novamente.")
                        
                except KeyboardInterrupt:
                    print("\\n\\n⚠️ Operação cancelada pelo usuário.")
                    continue
                except Exception as e:
                    self.logger.error(f"Erro no menu principal: {e}")
                    print(f"❌ Erro inesperado: {e}")
                    input("\\n📖 Pressione ENTER para continuar...")
                    
        except Exception as e:
            self.logger.error(f"Erro crítico no sistema: {e}")
            print(f"💥 Erro crítico: {e}")
    
    def _show_welcome(self):
        """Mostra tela de boas-vindas"""
        print("\\n" + "="*80)
        print("🚀 MARKET MANUS - SISTEMA DE TRADING COMPLETO v2.0")
        print("="*80)
        print("📊 Strategy Lab | 🎯 Confluence Mode | 💰 Capital Management")
        print("🔌 Dados Reais Bybit | 📈 Backtesting Honesto | 📋 Relatórios")
        print("="*80)
        
        # Mostrar status da conexão
        connection_status = self.data_provider.test_connection()
        if connection_status['status'] == 'connected':
            print(f"✅ Conectado à Bybit - Latência: {connection_status['latency_ms']}ms")
        else:
            print(f"⚠️ Problema de conexão: {connection_status.get('error', 'Desconhecido')}")
        
        # Mostrar resumo do capital
        capital_summary = self.capital_manager.get_capital_summary()
        print(f"💰 Capital: ${capital_summary['current_capital']:,.2f} | ROI: {capital_summary['roi']:+.2f}%")
        
        if capital_summary['drawdown_protection_active']:
            print("🛡️ PROTEÇÃO DE DRAWDOWN ATIVA")
        
        print("="*80)
    
    def _show_main_menu(self):
        """Mostra menu principal"""
        print("\\n🎛️ MENU PRINCIPAL")
        print("-" * 50)
        print("🧪 LABORATÓRIO:")
        print("   1️⃣  Strategy Lab - Testes Individuais")
        print("   2️⃣  Confluence Mode - Testes Combinados")
        print()
        print("💼 GESTÃO:")
        print("   3️⃣  Capital Dashboard")
        print("   4️⃣  Teste de Conectividade")
        print("   5️⃣  Configurações")
        print()
        print("📊 RELATÓRIOS:")
        print("   6️⃣  Relatórios e Exportação")
        print("   7️⃣  Status do Sistema")
        print("   8️⃣  Ajuda")
        print()
        print("   0️⃣  Sair")
        print("-" * 50)
    
    def _strategy_lab_menu(self):
        """Menu do Strategy Lab"""
        while True:
            print("\\n" + "="*80)
            print("🧪 STRATEGY LAB - LABORATÓRIO DE ESTRATÉGIAS")
            print("="*80)
            print("📊 CONFIGURAÇÃO ATUAL:")
            print(f"   🪙 Ativo: {self.current_symbol}")
            print(f"   ⏰ Timeframe: {self.current_timeframe}")
            print(f"   📈 Estratégias: {', '.join(self.selected_strategies)}")
            print(f"   💰 Capital: ${self.capital_manager.config.current_capital:,.2f}")
            print("-" * 80)
            print()
            print("🔧 CONFIGURAÇÃO:")
            print("   1️⃣  Selecionar Ativo")
            print("   2️⃣  Selecionar Timeframe")
            print("   3️⃣  Selecionar Estratégias")
            print("   4️⃣  Selecionar Período")
            print()
            print("🧪 TESTES:")
            print("   5️⃣  Teste de Estratégia Individual")
            print("   6️⃣  Comparar Múltiplas Estratégias")
            print("   7️⃣  Otimização de Parâmetros")
            print()
            print("📊 RESULTADOS:")
            print("   8️⃣  Visualizar Últimos Resultados")
            print("   9️⃣  Exportar Relatórios")
            print()
            print("   0️⃣  Voltar ao Menu Principal")
            print("-" * 80)
            
            choice = input("🔢 Escolha uma opção (0-9): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._select_symbol()
            elif choice == '2':
                self._select_timeframe()
            elif choice == '3':
                self._select_strategies()
            elif choice == '4':
                period = self._select_period()
                if period:
                    self.test_period = period
            elif choice == '5':
                self._run_single_strategy_test()
            elif choice == '6':
                self._run_strategy_comparison()
            elif choice == '7':
                self._parameter_optimization()
            elif choice == '8':
                self._show_last_results()
            elif choice == '9':
                self._export_strategy_reports()
            else:
                print("❌ Opção inválida!")
            
            if choice != '0':
                input("\\n📖 Pressione ENTER para continuar...")
    
    def _confluence_mode_menu(self):
        """Menu do Confluence Mode"""
        while True:
            print("\\n" + "="*80)
            print("🎯 CONFLUENCE MODE - SISTEMA DE CONFLUÊNCIA")
            print("="*80)
            print("📊 CONFIGURAÇÃO ATUAL:")
            print(f"   🪙 Ativo: {self.current_symbol}")
            print(f"   ⏰ Timeframe: {self.current_timeframe}")
            print(f"   📈 Estratégias: {', '.join(self.selected_strategies)} ({len(self.selected_strategies)})")
            print(f"   🎯 Modo Confluência: {self.confluence_mode.upper()}")
            print(f"   💪 Força Mínima: {self.min_strength:.1%}")
            print(f"   💰 Capital: ${self.capital_manager.config.current_capital:,.2f}")
            print("-" * 80)
            print()
            print("🔧 CONFIGURAÇÃO:")
            print("   1️⃣  Selecionar Ativo")
            print("   2️⃣  Selecionar Timeframe")
            print("   3️⃣  Selecionar Estratégias (Multi-seleção)")
            print("   4️⃣  Configurar Modo de Confluência")
            print("   5️⃣  Ajustar Força Mínima")
            print("   6️⃣  Selecionar Período")
            print()
            print("🧪 TESTES:")
            print("   7️⃣  Executar Backtest de Confluência")
            print("   8️⃣  Análise de Sinais em Tempo Real")
            print()
            print("📊 RESULTADOS:")
            print("   9️⃣  Visualizar Resultados")
            print("   🔟  Exportar Relatórios")
            print()
            print("   0️⃣  Voltar ao Menu Principal")
            print("-" * 80)
            
            choice = input("🔢 Escolha uma opção (0-10): ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._select_symbol()
            elif choice == '2':
                self._select_timeframe()
            elif choice == '3':
                self._select_strategies_multi()
            elif choice == '4':
                self._select_confluence_mode()
            elif choice == '5':
                self._adjust_min_strength()
            elif choice == '6':
                period = self._select_period()
                if period:
                    self.test_period = period
            elif choice == '7':
                self._run_confluence_backtest()
            elif choice == '8':
                self._real_time_signals_analysis()
            elif choice == '9':
                self._show_confluence_results()
            elif choice == '10':
                self._export_confluence_reports()
            else:
                print("❌ Opção inválida!")
            
            if choice != '0':
                input("\\n📖 Pressione ENTER para continuar...")
    
    def _select_symbol(self):
        """Seleção de ativo"""
        print("\\n🪙 SELEÇÃO DE ATIVO")
        print("=" * 50)
        
        # Símbolos populares
        popular_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
            'XRPUSDT', 'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'BCHUSDT'
        ]
        
        print("📊 Símbolos Populares:")
        for i, symbol in enumerate(popular_symbols, 1):
            try:
                price = self.data_provider.get_current_price(symbol)
                print(f"   {i:2d}️⃣  {symbol:<10} - ${price:>10,.2f}")
            except:
                print(f"   {i:2d}️⃣  {symbol:<10} - Indisponível")
        
        print(f"\\n   1️⃣1️⃣  Buscar outro símbolo")
        print(f"   0️⃣  Manter atual ({self.current_symbol})")
        
        choice = input("\\n🔢 Escolha um símbolo: ").strip()
        
        if choice == '0':
            return
        elif choice == '11':
            custom_symbol = input("Digite o símbolo (ex: BTCUSDT): ").strip().upper()
            if custom_symbol:
                try:
                    # Testar se símbolo existe
                    price = self.data_provider.get_current_price(custom_symbol)
                    self.current_symbol = custom_symbol
                    print(f"✅ Símbolo alterado para {custom_symbol} - ${price:,.2f}")
                except:
                    print(f"❌ Símbolo {custom_symbol} não encontrado!")
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(popular_symbols):
                    self.current_symbol = popular_symbols[idx]
                    price = self.data_provider.get_current_price(self.current_symbol)
                    print(f"✅ Símbolo alterado para {self.current_symbol} - ${price:,.2f}")
                else:
                    print("❌ Opção inválida!")
            except ValueError:
                print("❌ Entrada inválida!")
    
    def _select_timeframe(self):
        """Seleção de timeframe"""
        print("\\n⏰ SELEÇÃO DE TIMEFRAME")
        print("=" * 50)
        
        timeframes = [
            ('1m', '1 minuto'),
            ('5m', '5 minutos'),
            ('15m', '15 minutos'),
            ('30m', '30 minutos'),
            ('1h', '1 hora'),
            ('4h', '4 horas'),
            ('1d', '1 dia')
        ]
        
        print("📊 Timeframes Disponíveis:")
        for i, (tf, desc) in enumerate(timeframes, 1):
            marker = "✅" if tf == self.current_timeframe else "  "
            print(f"   {i}️⃣  {marker} {tf:<4} - {desc}")
        
        print(f"\\n   0️⃣  Manter atual ({self.current_timeframe})")
        
        choice = input("\\n🔢 Escolha um timeframe: ").strip()
        
        if choice == '0':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(timeframes):
                self.current_timeframe = timeframes[idx][0]
                print(f"✅ Timeframe alterado para {self.current_timeframe}")
            else:
                print("❌ Opção inválida!")
        except ValueError:
            print("❌ Entrada inválida!")
    
    def _select_strategies(self):
        """Seleção de estratégias (single)"""
        print("\\n📈 SELEÇÃO DE ESTRATÉGIA")
        print("=" * 50)
        
        strategies = list(STRATEGY_REGISTRY_V2.keys())
        
        print("📊 Estratégias Disponíveis:")
        for i, strategy_key in enumerate(strategies, 1):
            strategy_info = STRATEGY_REGISTRY_V2[strategy_key]
            marker = "✅" if strategy_key in self.selected_strategies else "  "
            print(f"   {i}️⃣  {marker} {strategy_info['description']}")
            print(f"       Risco: {strategy_info['risk_level']} | Timeframes: {', '.join(strategy_info['best_timeframes'])}")
        
        print(f"\\n   0️⃣  Manter atual")
        
        choice = input("\\n🔢 Escolha uma estratégia: ").strip()
        
        if choice == '0':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(strategies):
                self.selected_strategies = [strategies[idx]]
                print(f"✅ Estratégia selecionada: {STRATEGY_REGISTRY_V2[strategies[idx]]['description']}")
            else:
                print("❌ Opção inválida!")
        except ValueError:
            print("❌ Entrada inválida!")
    
    def _select_strategies_multi(self):
        """Seleção múltipla de estratégias"""
        print("\\n📈 SELEÇÃO MÚLTIPLA DE ESTRATÉGIAS")
        print("=" * 50)
        
        strategies = list(STRATEGY_REGISTRY_V2.keys())
        
        while True:
            print("\\n📊 Estratégias Disponíveis:")
            for i, strategy_key in enumerate(strategies, 1):
                strategy_info = STRATEGY_REGISTRY_V2[strategy_key]
                marker = "✅" if strategy_key in self.selected_strategies else "⬜"
                print(f"   {i:2d}️⃣  {marker} {strategy_info['description']}")
                print(f"        Risco: {strategy_info['risk_level']} | Timeframes: {', '.join(strategy_info['best_timeframes'])}")
            
            print(f"\\n📋 Selecionadas ({len(self.selected_strategies)}): {', '.join(self.selected_strategies)}")
            print("\\n🔧 OPÇÕES:")
            print("   A️⃣  Selecionar Todas")
            print("   C️⃣  Limpar Seleção")
            print("   0️⃣  Finalizar")
            
            choice = input("\\n🔢 Escolha estratégias (números) ou opção (A/C/0): ").strip().upper()
            
            if choice == '0':
                if len(self.selected_strategies) >= 2:
                    print(f"✅ {len(self.selected_strategies)} estratégias selecionadas para confluência")
                    break
                else:
                    print("❌ Confluência requer pelo menos 2 estratégias!")
                    continue
            elif choice == 'A':
                self.selected_strategies = strategies.copy()
                print("✅ Todas as estratégias selecionadas")
            elif choice == 'C':
                self.selected_strategies = []
                print("✅ Seleção limpa")
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(strategies):
                        strategy_key = strategies[idx]
                        if strategy_key in self.selected_strategies:
                            self.selected_strategies.remove(strategy_key)
                            print(f"➖ {strategy_key} removida")
                        else:
                            self.selected_strategies.append(strategy_key)
                            print(f"➕ {strategy_key} adicionada")
                    else:
                        print("❌ Número inválido!")
                except ValueError:
                    print("❌ Entrada inválida!")
    
    def _select_confluence_mode(self):
        """Seleção do modo de confluência"""
        print("\\n🎯 SELEÇÃO DO MODO DE CONFLUÊNCIA")
        print("=" * 50)
        
        modes = [
            ('unanimous', 'UNÂNIME - Todas devem concordar'),
            ('majority', 'MAIORIA - Maioria deve concordar'),
            ('any', 'QUALQUER - Qualquer uma pode gerar sinal'),
            ('weighted', 'PONDERADO - Sinais ponderados por força'),
            ('consensus', 'CONSENSO - Consenso forte (75%)'),
        ]
        
        print("🎯 Modos Disponíveis:")
        for i, (mode, desc) in enumerate(modes, 1):
            marker = "✅" if mode == self.confluence_mode else "  "
            print(f"   {i}️⃣  {marker} {desc}")
        
        print(f"\\n   0️⃣  Manter atual ({self.confluence_mode.upper()})")
        
        choice = input("\\n🔢 Escolha um modo: ").strip()
        
        if choice == '0':
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(modes):
                self.confluence_mode = modes[idx][0]
                print(f"✅ Modo alterado para {modes[idx][1]}")
            else:
                print("❌ Opção inválida!")
        except ValueError:
            print("❌ Entrada inválida!")
    
    def _adjust_min_strength(self):
        """Ajustar força mínima"""
        print("\\n💪 AJUSTAR FORÇA MÍNIMA")
        print("=" * 50)
        print(f"Força atual: {self.min_strength:.1%}")
        print("\\nA força mínima filtra sinais fracos (0% = todos, 100% = apenas os mais fortes)")
        
        try:
            new_strength = input("\\nDigite nova força mínima (0-100%): ").strip()
            if new_strength.endswith('%'):
                new_strength = new_strength[:-1]
            
            strength_value = float(new_strength) / 100
            
            if 0 <= strength_value <= 1:
                self.min_strength = strength_value
                print(f"✅ Força mínima alterada para {self.min_strength:.1%}")
            else:
                print("❌ Valor deve estar entre 0 e 100!")
        except ValueError:
            print("❌ Entrada inválida!")
    
    def _select_period(self) -> Optional[Dict]:
        """Seleção de período de teste"""
        print("\\n📅 SELEÇÃO DE PERÍODO")
        print("=" * 50)
        
        print("📊 Períodos Pré-definidos:")
        for key, period in self.predefined_periods.items():
            print(f"   {key:2s}️⃣  {period['name']}")
        
        print("\\n   1️⃣1️⃣  Período Personalizado")
        print("   0️⃣  Cancelar")
        
        choice = input("\\n🔢 Escolha um período: ").strip()
        
        if choice == '0':
            return None
        elif choice == '11':
            return self._custom_period()
        elif choice in self.predefined_periods:
            period = self.predefined_periods[choice]
            print(f"✅ Período selecionado: {period['name']}")
            return period
        else:
            print("❌ Opção inválida!")
            return None
    
    def _custom_period(self) -> Optional[Dict]:
        """Período personalizado"""
        print("\\n📅 PERÍODO PERSONALIZADO")
        print("=" * 50)
        
        try:
            start_str = input("Data de início (YYYY-MM-DD): ").strip()
            end_str = input("Data de fim (YYYY-MM-DD): ").strip()
            
            start_date = datetime.strptime(start_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end_date = datetime.strptime(end_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            
            if start_date >= end_date:
                print("❌ Data de início deve ser anterior à data de fim!")
                return None
            
            period = {
                'name': f'{start_str} até {end_str}',
                'start': start_date,
                'end': end_date
            }
            
            print(f"✅ Período personalizado: {period['name']}")
            return period
            
        except ValueError:
            print("❌ Formato de data inválido! Use YYYY-MM-DD")
            return None
    
    def _run_single_strategy_test(self):
        """Executar teste de estratégia individual"""
        if not self.selected_strategies:
            print("❌ Nenhuma estratégia selecionada!")
            return
        
        strategy_key = self.selected_strategies[0]
        
        print(f"\\n🧪 TESTE DE ESTRATÉGIA INDIVIDUAL: {strategy_key.upper()}")
        print("=" * 60)
        
        # Configurar período
        period = getattr(self, 'test_period', self.predefined_periods['2'])  # Padrão: 30 dias
        
        config = BacktestConfig(
            symbol=self.current_symbol,
            timeframe=self.current_timeframe,
            start_date=period['start'],
            end_date=period['end'],
            strategies=[strategy_key]
        )
        
        print(f"📊 Configuração:")
        print(f"   Ativo: {config.symbol}")
        print(f"   Timeframe: {config.timeframe}")
        print(f"   Período: {period['name']}")
        print(f"   Estratégia: {STRATEGY_REGISTRY_V2[strategy_key]['description']}")
        
        confirm = input("\\n▶️ Executar teste? (s/N): ").strip().lower()
        if confirm != 's':
            return
        
        try:
            print("\\n⏳ Executando backtest...")
            results = self.strategy_lab.test_single_strategy(strategy_key, config)
            
            # Mostrar resultados
            self._display_backtest_results(results)
            
            # Salvar resultados
            self.last_results = results
            
            # Perguntar sobre exportação
            export = input("\\n💾 Exportar resultados? (s/N): ").strip().lower()
            if export == 's':
                filepath = self.strategy_lab.export_results(results)
                print(f"✅ Resultados exportados para: {filepath}")
                
        except Exception as e:
            self.logger.error(f"Erro no teste individual: {e}")
            print(f"❌ Erro no teste: {e}")
    
    def _run_confluence_backtest(self):
        """Executar backtest de confluência"""
        if len(self.selected_strategies) < 2:
            print("❌ Confluência requer pelo menos 2 estratégias!")
            return
        
        print(f"\\n🎯 BACKTEST DE CONFLUÊNCIA")
        print("=" * 60)
        
        # Configurar período
        period = getattr(self, 'test_period', self.predefined_periods['2'])  # Padrão: 30 dias
        
        config = BacktestConfig(
            symbol=self.current_symbol,
            timeframe=self.current_timeframe,
            start_date=period['start'],
            end_date=period['end'],
            strategies=self.selected_strategies,
            confluence_mode=self.confluence_mode,
            min_strength=self.min_strength
        )
        
        print(f"📊 Configuração:")
        print(f"   Ativo: {config.symbol}")
        print(f"   Timeframe: {config.timeframe}")
        print(f"   Período: {period['name']}")
        print(f"   Estratégias: {', '.join(self.selected_strategies)} ({len(self.selected_strategies)})")
        print(f"   Modo: {self.confluence_mode.upper()}")
        print(f"   Força Mínima: {self.min_strength:.1%}")
        
        confirm = input("\\n▶️ Executar backtest? (s/N): ").strip().lower()
        if confirm != 's':
            return
        
        try:
            print("\\n⏳ Executando backtest de confluência...")
            results = self.strategy_lab.test_confluence(config)
            
            # Mostrar resultados
            self._display_confluence_results(results)
            
            # Salvar resultados
            self.last_confluence_results = results
            
            # Perguntar sobre exportação
            export = input("\\n💾 Exportar resultados? (s/N): ").strip().lower()
            if export == 's':
                filepath = self.strategy_lab.export_results(results)
                print(f"✅ Resultados exportados para: {filepath}")
                
        except Exception as e:
            self.logger.error(f"Erro no backtest de confluência: {e}")
            print(f"❌ Erro no backtest: {e}")
    
    def _display_backtest_results(self, results: Dict[str, Any]):
        """Exibe resultados de backtest"""
        summary = results['summary']
        
        print("\\n📊 RESULTADOS DO BACKTEST")
        print("=" * 50)
        print(f"💰 Capital Inicial: ${summary['initial_capital']:,.2f}")
        print(f"💰 Capital Final: ${summary['final_capital']:,.2f}")
        print(f"📈 Retorno Total: ${summary['total_return']:+,.2f}")
        print(f"📊 ROI: {summary['roi']:+.2f}%")
        print(f"📉 Drawdown Máximo: {summary['max_drawdown']:.2%}")
        print()
        print(f"🔢 Total de Trades: {summary['total_trades']}")
        print(f"✅ Trades Vencedores: {summary['winning_trades']}")
        print(f"❌ Trades Perdedores: {summary['losing_trades']}")
        print(f"🎯 Taxa de Acerto: {summary['win_rate']:.1f}%")
        print(f"💸 Total de Fees: ${summary['total_fees']:,.2f}")
        print()
        print(f"📊 Sharpe Ratio: {summary['sharpe_ratio']:.2f}")
        print(f"💪 Profit Factor: {summary['profit_factor']:.2f}")
        print(f"💚 Ganho Médio: ${summary['avg_win']:+,.2f}")
        print(f"💔 Perda Média: ${summary['avg_loss']:+,.2f}")
        
        # Mostrar proteção de drawdown se ativa
        if summary['max_drawdown'] >= 0.5:
            print("\\n🛡️ PROTEÇÃO DE DRAWDOWN ATIVADA!")
            print("   O teste foi interrompido por segurança.")
    
    def _display_confluence_results(self, results: Dict[str, Any]):
        """Exibe resultados de confluência"""
        self._display_backtest_results(results)
        
        # Mostrar resultados individuais
        if 'individual_results' in results:
            print("\\n📊 RESULTADOS INDIVIDUAIS DAS ESTRATÉGIAS")
            print("=" * 50)
            
            for strategy_key, individual in results['individual_results'].items():
                if 'error' not in individual:
                    strategy_name = STRATEGY_REGISTRY_V2[strategy_key]['description']
                    print(f"📈 {strategy_name}:")
                    print(f"   ROI: {individual['roi']:+.2f}% | Trades: {individual['total_trades']} | Win Rate: {individual['win_rate']:.1f}%")
    
    def _capital_dashboard(self):
        """Dashboard de capital"""
        print("\\n💰 CAPITAL DASHBOARD")
        print("=" * 50)
        
        summary = self.capital_manager.get_capital_summary()
        
        print(f"💰 Capital Inicial: ${summary['initial_capital']:,.2f}")
        print(f"💰 Capital Atual: ${summary['current_capital']:,.2f}")
        print(f"📈 Capital Pico: ${summary['peak_capital']:,.2f}")
        print(f"📊 P&L Total: ${summary['total_pnl']:+,.2f}")
        print(f"📊 ROI: {summary['roi']:+.2f}%")
        print()
        print(f"📉 Drawdown Atual: {summary['current_drawdown']:.2%}")
        print(f"📉 Drawdown Máximo: {summary['max_drawdown']:.2%}")
        
        if summary['drawdown_protection_active']:
            print("\\n🛡️ PROTEÇÃO DE DRAWDOWN ATIVA")
            print("   Trading suspenso por segurança")
        
        print()
        print(f"🔢 Total de Trades: {summary.get('total_trades', 0)}")
        print(f"✅ Trades Vencedores: {summary.get('winning_trades', 0)}")
        print(f"❌ Trades Perdedores: {summary.get('losing_trades', 0)}")
        print(f"🎯 Taxa de Acerto: {summary.get('win_rate', 0):.1f}%")
        print(f"💪 Profit Factor: {summary.get('profit_factor', 0):.2f}")
        
        # Mostrar trades recentes
        recent_trades = self.capital_manager.get_recent_trades(5)
        if recent_trades:
            print("\\n📋 TRADES RECENTES:")
            print("-" * 50)
            for trade in recent_trades:
                pnl_emoji = "💚" if trade.net_pnl > 0 else "💔"
                print(f"{pnl_emoji} {trade.symbol} {trade.side} - P&L: ${trade.net_pnl:+.2f} | {trade.timestamp.strftime('%d/%m %H:%M')}")
        
        # Menu de ações
        print("\\n🔧 AÇÕES:")
        print("   1️⃣  Configurar Capital")
        print("   2️⃣  Resetar Capital")
        print("   3️⃣  Desabilitar Proteção de Drawdown")
        print("   0️⃣  Voltar")
        
        choice = input("\\n🔢 Escolha uma ação: ").strip()
        
        if choice == '1':
            self._configure_capital()
        elif choice == '2':
            self._reset_capital()
        elif choice == '3':
            self._disable_drawdown_protection()
    
    def _configure_capital(self):
        """Configurar parâmetros de capital"""
        print("\\n⚙️ CONFIGURAÇÃO DE CAPITAL")
        print("=" * 50)
        
        config = self.capital_manager.config
        
        print(f"Configuração atual:")
        print(f"   Risco por trade: {config.risk_per_trade:.1%}")
        print(f"   Máximo por trade: ${config.max_per_trade:,.2f}")
        print(f"   Drawdown máximo: {config.max_drawdown:.1%}")
        print(f"   Modo position size: {config.position_size_mode}")
        
        # Permitir alterações
        try:
            new_risk = input(f"\\nNovo risco por trade (atual {config.risk_per_trade:.1%}): ").strip()
            if new_risk:
                if new_risk.endswith('%'):
                    new_risk = new_risk[:-1]
                risk_value = float(new_risk) / 100
                if 0.001 <= risk_value <= 0.1:  # Entre 0.1% e 10%
                    config.risk_per_trade = risk_value
                    print(f"✅ Risco alterado para {risk_value:.1%}")
                else:
                    print("❌ Risco deve estar entre 0.1% e 10%")
            
            new_max = input(f"\\nMáximo por trade (atual ${config.max_per_trade:,.2f}): ").strip()
            if new_max:
                max_value = float(new_max)
                if max_value > 0:
                    config.max_per_trade = max_value
                    print(f"✅ Máximo alterado para ${max_value:,.2f}")
            
            # Salvar configurações
            self.capital_manager._save_capital_config()
            print("\\n✅ Configurações salvas!")
            
        except ValueError:
            print("❌ Valores inválidos!")
    
    def _reset_capital(self):
        """Resetar capital"""
        print("\\n🔄 RESETAR CAPITAL")
        print("=" * 50)
        
        current_capital = self.capital_manager.config.current_capital
        print(f"Capital atual: ${current_capital:,.2f}")
        
        confirm = input("\\n⚠️ Tem certeza que deseja resetar o capital? (s/N): ").strip().lower()
        if confirm != 's':
            return
        
        try:
            new_capital = input("\\nNovo capital inicial: $").strip()
            capital_value = float(new_capital)
            
            if capital_value > 0:
                self.capital_manager.reset_capital(capital_value)
                print(f"✅ Capital resetado para ${capital_value:,.2f}")
            else:
                print("❌ Capital deve ser positivo!")
        except ValueError:
            print("❌ Valor inválido!")
    
    def _disable_drawdown_protection(self):
        """Desabilitar proteção de drawdown"""
        if not self.capital_manager.is_drawdown_protection_active:
            print("\\n✅ Proteção de drawdown já está desabilitada")
            return
        
        print("\\n⚠️ DESABILITAR PROTEÇÃO DE DRAWDOWN")
        print("=" * 50)
        print("ATENÇÃO: Isso pode resultar em perdas significativas!")
        
        confirm = input("\\nTem certeza? Digite 'CONFIRMO' para prosseguir: ").strip()
        if confirm == 'CONFIRMO':
            self.capital_manager.disable_drawdown_protection()
            print("✅ Proteção de drawdown desabilitada")
        else:
            print("❌ Operação cancelada")
    
    def _connectivity_test(self):
        """Teste de conectividade"""
        print("\\n🔌 TESTE DE CONECTIVIDADE")
        print("=" * 50)
        
        print("⏳ Testando conexão com Bybit...")
        
        connection_status = self.data_provider.test_connection()
        
        if connection_status['status'] == 'connected':
            print("✅ CONEXÃO ESTABELECIDA")
            print(f"   Servidor: {connection_status['server_time']}")
            print(f"   Latência: {connection_status['latency_ms']:.2f}ms")
            print(f"   Testnet: {'Sim' if connection_status['testnet'] else 'Não'}")
            
            # Testar preço atual
            try:
                print(f"\\n💰 Testando preços...")
                price = self.data_provider.get_current_price(self.current_symbol)
                print(f"✅ {self.current_symbol}: ${price:,.2f}")
            except Exception as e:
                print(f"❌ Erro ao obter preço: {e}")
            
            # Testar dados históricos
            try:
                print(f"\\n📊 Testando dados históricos...")
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=24)
                
                df = self.data_provider.fetch_klines(self.current_symbol, '1h', 
                                                   pd.Timestamp(start_time), pd.Timestamp(end_time))
                print(f"✅ Dados históricos: {len(df)} registros coletados")
            except Exception as e:
                print(f"❌ Erro nos dados históricos: {e}")
        else:
            print("❌ FALHA NA CONEXÃO")
            print(f"   Erro: {connection_status.get('error', 'Desconhecido')}")
            print("\\n🔧 Verificações:")
            print("   • Conexão com internet")
            print("   • Credenciais da API (se configuradas)")
            print("   • Firewall/Proxy")
    
    def _configuration_menu(self):
        """Menu de configurações"""
        print("\\n⚙️ CONFIGURAÇÕES")
        print("=" * 50)
        
        print("🔧 OPÇÕES:")
        print("   1️⃣  Configurar Credenciais API")
        print("   2️⃣  Configurações de Capital")
        print("   3️⃣  Configurações Gerais")
        print("   4️⃣  Limpar Cache")
        print("   5️⃣  Exportar Configurações")
        print("   6️⃣  Importar Configurações")
        print("   0️⃣  Voltar")
        
        choice = input("\\n🔢 Escolha uma opção: ").strip()
        
        if choice == '1':
            self._configure_api_credentials()
        elif choice == '2':
            self._configure_capital()
        elif choice == '3':
            self._general_settings()
        elif choice == '4':
            self._clear_cache()
        elif choice == '5':
            self._export_settings()
        elif choice == '6':
            self._import_settings()
    
    def _configure_api_credentials(self):
        """Configurar credenciais da API"""
        print("\\n🔑 CONFIGURAR CREDENCIAIS API")
        print("=" * 50)
        
        current_key = os.getenv('BYBIT_API_KEY', 'Não configurada')
        current_secret = os.getenv('BYBIT_API_SECRET', 'Não configurada')
        
        print(f"API Key atual: {current_key[:8]}..." if current_key != 'Não configurada' else "API Key: Não configurada")
        print(f"API Secret: {'Configurada' if current_secret != 'Não configurada' else 'Não configurada'}")
        
        print("\\n⚠️ IMPORTANTE:")
        print("   • Use apenas credenciais de TESTNET para testes")
        print("   • Nunca compartilhe suas credenciais")
        print("   • Configure permissões apenas para leitura")
        
        configure = input("\\n🔧 Configurar credenciais? (s/N): ").strip().lower()
        if configure != 's':
            return
        
        api_key = input("\\nAPI Key: ").strip()
        api_secret = input("API Secret: ").strip()
        testnet = input("Usar Testnet? (S/n): ").strip().lower() != 'n'
        
        if api_key and api_secret:
            # Salvar em arquivo .env
            env_file = Path('.env')
            env_content = f"""BYBIT_API_KEY={api_key}
BYBIT_API_SECRET={api_secret}
BYBIT_TESTNET={'true' if testnet else 'false'}
"""
            
            with open(env_file, 'w') as f:
                f.write(env_content)
            
            print("\\n✅ Credenciais salvas em .env")
            print("⚠️ Reinicie o sistema para aplicar as alterações")
        else:
            print("❌ Credenciais inválidas!")
    
    def _system_status(self):
        """Status do sistema"""
        print("\\n📊 STATUS DO SISTEMA")
        print("=" * 50)
        
        # Status da conexão
        connection_status = self.data_provider.test_connection()
        status_emoji = "✅" if connection_status['status'] == 'connected' else "❌"
        print(f"{status_emoji} Conexão Bybit: {connection_status['status']}")
        
        if connection_status['status'] == 'connected':
            print(f"   Latência: {connection_status['latency_ms']:.2f}ms")
        
        # Status do capital
        capital_summary = self.capital_manager.get_capital_summary()
        protection_emoji = "🛡️" if capital_summary['drawdown_protection_active'] else "✅"
        print(f"{protection_emoji} Capital: ${capital_summary['current_capital']:,.2f} (ROI: {capital_summary['roi']:+.2f}%)")
        
        # Configuração atual
        print(f"\\n🔧 CONFIGURAÇÃO ATUAL:")
        print(f"   Ativo: {self.current_symbol}")
        print(f"   Timeframe: {self.current_timeframe}")
        print(f"   Estratégias: {len(self.selected_strategies)} selecionadas")
        print(f"   Modo Confluência: {self.confluence_mode.upper()}")
        
        # Estatísticas de uso
        print(f"\\n📊 ESTATÍSTICAS:")
        print(f"   Total de Trades: {capital_summary.get('total_trades', 0)}")
        print(f"   Taxa de Acerto: {capital_summary.get('win_rate', 0):.1f}%")
        print(f"   Profit Factor: {capital_summary.get('profit_factor', 0):.2f}")
        
        # Informações do sistema
        print(f"\\n💻 SISTEMA:")
        print(f"   Estratégias Disponíveis: {len(STRATEGY_REGISTRY_V2)}")
        print(f"   Cache de Dados: {len(self.strategy_lab._data_cache)} entradas")
        print(f"   Diretório de Relatórios: {self.strategy_lab.reports_dir}")
    
    def _help_menu(self):
        """Menu de ajuda"""
        print("\\n📖 AJUDA - MARKET MANUS")
        print("=" * 50)
        
        print("🧪 STRATEGY LAB:")
        print("   • Teste estratégias individuais com dados reais")
        print("   • Compare múltiplas estratégias")
        print("   • Otimize parâmetros")
        print("   • Exporte relatórios detalhados")
        print()
        print("🎯 CONFLUENCE MODE:")
        print("   • Combine múltiplas estratégias")
        print("   • 5 modos de confluência disponíveis")
        print("   • Ajuste força mínima dos sinais")
        print("   • Análise em tempo real")
        print()
        print("💰 CAPITAL MANAGEMENT:")
        print("   • Tracking automático de P&L")
        print("   • Proteção contra drawdown (50%)")
        print("   • Position sizing inteligente")
        print("   • Histórico completo de trades")
        print()
        print("🔌 DADOS REAIS:")
        print("   • Integração com API Bybit")
        print("   • Cache inteligente")
        print("   • Rate limiting respeitoso")
        print("   • Suporte a testnet")
        print()
        print("📊 RELATÓRIOS:")
        print("   • Exportação em JSON")
        print("   • Métricas avançadas (Sharpe, Profit Factor)")
        print("   • Comparações detalhadas")
        print("   • Histórico de capital")
        
        print("\\n🆘 SUPORTE:")
        print("   • Logs detalhados em logs/market_manus.log")
        print("   • Configurações salvas automaticamente")
        print("   • Backup de dados em SQLite")
        
        input("\\n📖 Pressione ENTER para continuar...")
    
    def _save_session_state(self):
        """Salva estado da sessão"""
        self.capital_manager.update_settings(
            last_symbol=self.current_symbol,
            last_timeframe=self.current_timeframe,
            last_strategies=self.selected_strategies
        )
        self.logger.info("Estado da sessão salvo")
    
    # Métodos auxiliares para funcionalidades ainda não implementadas
    def _run_strategy_comparison(self):
        """Comparar múltiplas estratégias"""
        print("\\n🔄 Funcionalidade em desenvolvimento...")
        print("Use o Confluence Mode para testar múltiplas estratégias")
    
    def _parameter_optimization(self):
        """Otimização de parâmetros"""
        print("\\n🔄 Funcionalidade em desenvolvimento...")
        print("Otimização de parâmetros será implementada em versão futura")
    
    def _show_last_results(self):
        """Mostrar últimos resultados"""
        if hasattr(self, 'last_results'):
            self._display_backtest_results(self.last_results)
        else:
            print("\\n❌ Nenhum resultado disponível. Execute um teste primeiro.")
    
    def _export_strategy_reports(self):
        """Exportar relatórios de estratégias"""
        print("\\n💾 Exportação disponível após executar testes")
    
    def _real_time_signals_analysis(self):
        """Análise de sinais em tempo real"""
        print("\\n🔄 Funcionalidade em desenvolvimento...")
        print("Análise em tempo real será implementada em versão futura")
    
    def _show_confluence_results(self):
        """Mostrar resultados de confluência"""
        if hasattr(self, 'last_confluence_results'):
            self._display_confluence_results(self.last_confluence_results)
        else:
            print("\\n❌ Nenhum resultado de confluência disponível. Execute um backtest primeiro.")
    
    def _export_confluence_reports(self):
        """Exportar relatórios de confluência"""
        print("\\n💾 Exportação disponível após executar backtests")
    
    def _reports_menu(self):
        """Menu de relatórios"""
        print("\\n📊 RELATÓRIOS E EXPORTAÇÃO")
        print("=" * 50)
        print("🔄 Funcionalidade em desenvolvimento...")
        print("Relatórios detalhados serão implementados em versão futura")
    
    def _general_settings(self):
        """Configurações gerais"""
        print("\\n⚙️ CONFIGURAÇÕES GERAIS")
        print("=" * 50)
        print("🔄 Funcionalidade em desenvolvimento...")
    
    def _clear_cache(self):
        """Limpar cache"""
        self.strategy_lab._data_cache.clear()
        print("\\n✅ Cache limpo!")
    
    def _export_settings(self):
        """Exportar configurações"""
        print("\\n💾 EXPORTAR CONFIGURAÇÕES")
        print("=" * 50)
        print("🔄 Funcionalidade em desenvolvimento...")
    
    def _import_settings(self):
        """Importar configurações"""
        print("\\n📥 IMPORTAR CONFIGURAÇÕES")
        print("=" * 50)
        print("🔄 Funcionalidade em desenvolvimento...")


def main():
    """Função principal"""
    try:
        system = MarketManusCompleteSystem()
        system.run()
    except KeyboardInterrupt:
        print("\\n\\n⚠️ Sistema interrompido pelo usuário")
    except Exception as e:
        logging.error(f"Erro crítico: {e}")
        print(f"💥 Erro crítico: {e}")
        print("Verifique os logs para mais detalhes")


if __name__ == "__main__":
    main()
