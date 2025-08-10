#!/usr/bin/env python3
"""
STRATEGY FACTORY CLI V2 - Fábrica de Estratégias Melhorada
Sistema de Trading Automatizado com controle completo de período e Strategy Lab consolidado
"""

import asyncio
import json
import logging
import os
import sys
import time
import itertools
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Importar componentes existentes
from capital_manager import CapitalManager, CapitalConfig, create_default_capital_config
from backtest_cli_enhanced import BybitAPIV5RealData, RealDataIndicators, RealDataStrategyEngine
from test_configuration_manager import TestConfigurationManager, TestConfiguration

# Importar componentes da versão anterior
from strategy_factory_cli import (
    StrategyValidator, StrategyCombinator, ReportManager, StrategyFactoryEngine
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategy_factory_v2.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StrategyFactoryEngineV2(StrategyFactoryEngine):
    """Engine melhorado da fábrica de estratégias com controle de configuração"""
    
    def __init__(self):
        super().__init__()
        self.test_config_manager = TestConfigurationManager()
    
    def test_strategy_combination_with_config(self, strategies: List[str], test_config: TestConfiguration, 
                                            capital_manager: CapitalManager) -> Dict:
        """Testa uma combinação de estratégias com configuração personalizada"""
        try:
            combination_name = self.combinator.get_combination_name(strategies)
            
            print(f"\n🔄 Testando: {combination_name}")
            print(f"   📊 Estratégias: {', '.join(strategies)}")
            print(f"   📊 Símbolo: {test_config.symbol}")
            print(f"   ⏰ Timeframe: {test_config.timeframe}")
            print(f"   📅 Período: {test_config.period_name}")
            print(f"   💰 Capital: ${capital_manager.config.initial_capital_usd:,.2f}")
            
            start_time = time.time()
            
            # 1. Obter dados históricos com configuração personalizada
            historical_data = self.api_client.get_historical_klines(
                test_config.symbol, test_config.timeframe, 
                test_config.start_date, test_config.end_date
            )
            
            # 2. Reset do capital manager
            capital_manager.reset_capital()
            
            # 3. Aplicar estratégias e combinar sinais
            combined_signals = self._combine_strategy_signals(strategies, historical_data)
            
            # 4. Simular trades
            self._simulate_trades_with_capital(combined_signals, capital_manager)
            
            # 5. Obter métricas
            metrics = capital_manager.get_metrics()
            
            # 6. Validar estratégia
            validation = self.validator.validate_strategy(metrics)
            score = self.validator.calculate_composite_score(metrics)
            
            execution_time = time.time() - start_time
            
            result = {
                'combination_name': combination_name,
                'strategies': strategies,
                'test_config': test_config.to_dict(),
                'metrics': metrics,
                'validation': validation,
                'composite_score': score,
                'execution_time': execution_time,
                'data_points': len(historical_data),
                'capital_config': capital_manager.config.to_dict()
            }
            
            # Status visual
            status_emoji = {
                'approved': '✅',
                'conditional': '⚠️',
                'rejected': '❌'
            }
            
            print(f"   {status_emoji[validation]} {validation.upper()}: Score {score:.1f}")
            print(f"   💰 ROI: {metrics['roi_percent']:+.2f}% | Win Rate: {metrics['win_rate']:.1%}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro no teste de combinação: {e}")
            return {'error': str(e)}

class StrategyFactoryCLIV2:
    """CLI melhorado da Fábrica de Estratégias"""
    
    def __init__(self):
        try:
            self.factory_engine = StrategyFactoryEngineV2()
            self.test_config_manager = TestConfigurationManager()
            
            # Carregar configuração de capital
            self.capital_manager = CapitalManager.load_config()
            if self.capital_manager is None:
                config = create_default_capital_config(10000.0)
                self.capital_manager = CapitalManager(config)
                print("💰 Usando configuração padrão de capital: $10,000")
            else:
                print(f"💰 Configuração de capital carregada: ${self.capital_manager.config.initial_capital_usd:,.2f}")
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            sys.exit(1)
    
    def display_header(self):
        """Exibe cabeçalho da fábrica"""
        print("\n" + "="*80)
        print("🏭 STRATEGY FACTORY CLI V2 - FÁBRICA DE ESTRATÉGIAS MELHORADA")
        print("="*80)
        print("✅ Conectado à API Bybit configurada")
        print("🎛️ Controle completo de período, timeframe e símbolo")
        print("🔬 Strategy Lab consolidado (single + multiple tests)")
        print("💰 Capital livre de $1 - $100,000")
        print("📈 Relatórios padronizados com nomenclatura específica")
        print("🎯 Sweet spot finder para otimização")
        print("="*80)
    
    def display_main_menu(self):
        """Exibe menu principal melhorado"""
        print("\n🏭 FÁBRICA DE ESTRATÉGIAS - MENU PRINCIPAL")
        print("="*60)
        print("   1️⃣  Configurar Capital ($1 - $100,000)")
        print("   2️⃣  Strategy Lab (Single + Multiple Tests)")
        print("   3️⃣  Análise de Performance (Sweet Spot Finder)")
        print("   4️⃣  Histórico de Testes")
        print("   5️⃣  Ranking de Estratégias")
        print("   6️⃣  Exportar Relatórios")
        print("   7️⃣  Configurações Avançadas")
        print("   🔍  Listar Estratégias Disponíveis")
        print("   0️⃣  Sair")
        print()
    
    def configure_capital(self):
        """Configurar capital inicial ($1 - $100,000)"""
        print("\n💰 CONFIGURAÇÃO DE CAPITAL INICIAL")
        print("="*50)
        
        current_config = self.capital_manager.config
        print(f"\n📊 CONFIGURAÇÃO ATUAL:")
        print(f"   💰 Capital inicial: ${current_config.initial_capital_usd:,.2f}")
        print(f"   📊 Position size: {current_config.position_size_percent}%")
        print(f"   🔄 Compound interest: {'Sim' if current_config.compound_interest else 'Não'}")
        
        print(f"\n🔧 NOVA CONFIGURAÇÃO:")
        
        # Capital inicial ($1 - $100,000)
        while True:
            try:
                capital_input = input(f"💰 Capital inicial em USD ($1 - $100,000): ").strip()
                if not capital_input:
                    initial_capital = current_config.initial_capital_usd
                    break
                
                initial_capital = float(capital_input)
                if initial_capital < 1.0:
                    print("❌ Capital mínimo: $1")
                    continue
                if initial_capital > 100000.0:
                    print("❌ Capital máximo: $100,000")
                    continue
                break
            except ValueError:
                print("❌ Digite um valor numérico válido")
        
        # Position size
        while True:
            try:
                pos_input = input(f"📊 Position size em % do capital (0.1% - 10%): ").strip()
                if not pos_input:
                    position_size_percent = current_config.position_size_percent
                    break
                
                position_size_percent = float(pos_input)
                if position_size_percent < 0.1:
                    print("❌ Position size mínimo: 0.1%")
                    continue
                if position_size_percent > 10:
                    print("❌ Position size máximo: 10%")
                    continue
                break
            except ValueError:
                print("❌ Digite um valor numérico válido")
        
        # Compound interest
        compound_input = input(f"🔄 Usar compound interest? (s/N): ").strip().lower()
        compound_interest = compound_input == 's'
        
        # Criar nova configuração
        new_config = CapitalConfig(
            initial_capital_usd=initial_capital,
            position_size_percent=position_size_percent,
            compound_interest=compound_interest,
            min_position_size_usd=max(1.0, initial_capital * 0.001),
            max_position_size_usd=min(initial_capital * 0.1, 10000.0),
            risk_per_trade_percent=1.0
        )
        
        # Mostrar resumo
        print(f"\n📋 RESUMO DA NOVA CONFIGURAÇÃO:")
        print(f"   💰 Capital inicial: ${new_config.initial_capital_usd:,.2f}")
        print(f"   📊 Position size: {new_config.position_size_percent}%")
        print(f"   🔄 Compound interest: {'Sim' if new_config.compound_interest else 'Não'}")
        
        # Confirmar
        confirm = input(f"\n✅ Salvar esta configuração? (s/N): ").strip().lower()
        if confirm == 's':
            self.capital_manager = CapitalManager(new_config)
            if self.capital_manager.save_config():
                print(f"✅ Configuração salva com sucesso!")
            else:
                print(f"⚠️  Configuração aplicada mas não foi possível salvar")
        else:
            print(f"❌ Configuração cancelada")
    
    def strategy_lab(self):
        """Strategy Lab consolidado - Single + Multiple Tests"""
        print("\n🔬 STRATEGY LAB - LABORATÓRIO DE ESTRATÉGIAS")
        print("="*60)
        
        print(f"\n🧪 TIPOS DE TESTE:")
        print(f"   1️⃣ Single Test (Uma estratégia)")
        print(f"   2️⃣ Multiple Test (Combinações de estratégias)")
        print(f"   3️⃣ Validation Suite (Todas as combinações)")
        
        while True:
            try:
                choice = input(f"\n🔬 Escolha o tipo de teste (1-3): ").strip()
                if choice in ['1', '2', '3']:
                    break
                else:
                    print("❌ Escolha entre 1 e 3")
            except ValueError:
                print("❌ Digite um número válido")
        
        if choice == '1':
            self._single_test()
        elif choice == '2':
            self._multiple_test()
        elif choice == '3':
            self._validation_suite()
    
    def _single_test(self):
        """Teste de uma única estratégia"""
        print("\n🎯 SINGLE TEST - TESTE DE ESTRATÉGIA ÚNICA")
        print("="*60)
        
        # Selecionar estratégia
        strategies = list(self.factory_engine.strategy_engine.strategies.keys())
        print(f"\n🎯 ESTRATÉGIAS DISPONÍVEIS:")
        for i, strategy in enumerate(strategies, 1):
            config = self.factory_engine.strategy_engine.strategy_configs[strategy]
            print(f"   {i}. {config['name']}")
        
        while True:
            try:
                choice = input(f"\n📊 Escolha uma estratégia (1-{len(strategies)}): ").strip()
                strategy_idx = int(choice) - 1
                if 0 <= strategy_idx < len(strategies):
                    selected_strategy = strategies[strategy_idx]
                    break
                else:
                    print(f"❌ Escolha entre 1 e {len(strategies)}")
            except ValueError:
                print("❌ Digite um número válido")
        
        # Configurar teste
        test_config = self.test_config_manager.configure_test()
        if test_config is None:
            return
        
        # Confirmar execução
        print(f"\n📊 RESUMO DO TESTE:")
        print(f"   🎯 Estratégia: {selected_strategy}")
        print(f"   📊 Símbolo: {test_config.symbol}")
        print(f"   ⏰ Timeframe: {test_config.timeframe}")
        print(f"   📅 Período: {test_config.period_name}")
        print(f"   💰 Capital: ${self.capital_manager.config.initial_capital_usd:,.2f}")
        
        confirm = input(f"\n✅ Executar teste? (s/N): ").strip().lower()
        if confirm != 's':
            return
        
        # Executar teste
        print(f"\n🔄 Executando teste...")
        result = self.factory_engine.test_strategy_combination_with_config(
            [selected_strategy], test_config, self.capital_manager
        )
        
        if 'error' in result:
            print(f"❌ Erro: {result['error']}")
            return
        
        # Salvar relatório
        report_path = self.factory_engine.report_manager.save_report(result, selected_strategy)
        
        # Exibir resultados
        self._display_test_results(result)
        
        if report_path:
            print(f"\n💾 Relatório salvo: {os.path.basename(report_path)}")
    
    def _multiple_test(self):
        """Teste de múltiplas estratégias"""
        print("\n🔄 MULTIPLE TEST - TESTE DE COMBINAÇÕES")
        print("="*60)
        
        # Mostrar combinações disponíveis
        combinations = self.factory_engine.combinator.get_all_combinations()
        
        print(f"\n🧪 TIPOS DE COMBINAÇÕES:")
        print(f"   1️⃣ Dual Combinations ({len(combinations['dual'])} opções)")
        print(f"   2️⃣ Triple Combinations ({len(combinations['triple'])} opções)")
        print(f"   3️⃣ Full Combination ({len(combinations['full'])} opções)")
        print(f"   4️⃣ Combinação Personalizada")
        
        while True:
            try:
                choice = input(f"\n🔬 Escolha o tipo de combinação (1-4): ").strip()
                if choice in ['1', '2', '3', '4']:
                    break
                else:
                    print("❌ Escolha entre 1 e 4")
            except ValueError:
                print("❌ Digite um número válido")
        
        # Selecionar combinação específica
        if choice == '1':
            selected_combinations = self._select_from_combinations(combinations['dual'], "Dual Combinations")
        elif choice == '2':
            selected_combinations = self._select_from_combinations(combinations['triple'], "Triple Combinations")
        elif choice == '3':
            selected_combinations = combinations['full']
        elif choice == '4':
            selected_combinations = self._create_custom_combination()
        
        if not selected_combinations:
            return
        
        # Configurar teste
        test_config = self.test_config_manager.configure_test()
        if test_config is None:
            return
        
        # Confirmar execução
        print(f"\n📊 RESUMO DO TESTE:")
        print(f"   🧪 Combinações selecionadas: {len(selected_combinations)}")
        print(f"   📊 Símbolo: {test_config.symbol}")
        print(f"   ⏰ Timeframe: {test_config.timeframe}")
        print(f"   📅 Período: {test_config.period_name}")
        print(f"   💰 Capital: ${self.capital_manager.config.initial_capital_usd:,.2f}")
        
        confirm = input(f"\n✅ Executar teste? (s/N): ").strip().lower()
        if confirm != 's':
            return
        
        # Executar testes
        print(f"\n🔄 Executando {len(selected_combinations)} teste(s)...")
        results = []
        
        for i, combination in enumerate(selected_combinations, 1):
            print(f"\n📊 Teste {i}/{len(selected_combinations)}")
            
            result = self.factory_engine.test_strategy_combination_with_config(
                combination, test_config, self.capital_manager
            )
            
            if 'error' not in result:
                results.append(result)
                
                # Salvar relatório individual
                combination_name = self.factory_engine.combinator.get_combination_name(combination)
                self.factory_engine.report_manager.save_report(result, combination_name)
        
        # Análise comparativa
        if results:
            self._display_comparative_analysis(results)
    
    def _validation_suite(self):
        """Suite de validação completa"""
        print("\n🎯 VALIDATION SUITE - VALIDAÇÃO COMPLETA")
        print("="*60)
        
        combinations = self.factory_engine.combinator.get_all_combinations()
        all_combinations = []
        
        # Coletar todas as combinações
        for combo_type, combos in combinations.items():
            all_combinations.extend(combos)
        
        print(f"\n📊 ESCOPO DA VALIDAÇÃO:")
        print(f"   🎯 Total de combinações: {len(all_combinations)}")
        print(f"   📊 Single strategies: {len(combinations['single'])}")
        print(f"   📊 Dual combinations: {len(combinations['dual'])}")
        print(f"   📊 Triple combinations: {len(combinations['triple'])}")
        print(f"   📊 Full combinations: {len(combinations['full'])}")
        
        # Configurar teste
        test_config = self.test_config_manager.configure_test()
        if test_config is None:
            return
        
        # Estimativa de tempo
        estimated_time = len(all_combinations) * 30  # 30s por teste
        print(f"\n⚙️ CONFIGURAÇÃO:")
        print(f"   📊 Símbolo: {test_config.symbol}")
        print(f"   ⏰ Timeframe: {test_config.timeframe}")
        print(f"   📅 Período: {test_config.period_name}")
        print(f"   💰 Capital: ${self.capital_manager.config.initial_capital_usd:,.2f}")
        print(f"   ⏱️ Tempo estimado: {estimated_time//60}min {estimated_time%60}s")
        
        confirm = input(f"\n✅ Executar validação completa? (s/N): ").strip().lower()
        if confirm != 's':
            return
        
        # Executar validação completa
        print(f"\n🔄 Iniciando validação completa...")
        results = []
        approved = []
        conditional = []
        rejected = []
        
        for i, combination in enumerate(all_combinations, 1):
            print(f"\n📊 Validando {i}/{len(all_combinations)}: {combination}")
            
            result = self.factory_engine.test_strategy_combination_with_config(
                combination, test_config, self.capital_manager
            )
            
            if 'error' not in result:
                results.append(result)
                
                # Classificar resultado
                validation = result['validation']
                if validation == 'approved':
                    approved.append(result)
                elif validation == 'conditional':
                    conditional.append(result)
                else:
                    rejected.append(result)
                
                # Salvar relatório
                combination_name = self.factory_engine.combinator.get_combination_name(combination)
                self.factory_engine.report_manager.save_report(result, combination_name)
        
        # Relatório final da validação
        self._display_validation_summary(results, approved, conditional, rejected)
    
    def sweet_spot_finder(self):
        """Encontra sweet spots nas estratégias"""
        print("\n🎯 SWEET SPOT FINDER - ANÁLISE DE PERFORMANCE")
        print("="*60)
        
        # Verificar se há relatórios para analisar
        reports = self.factory_engine.report_manager.list_reports()
        
        if not reports:
            print("📭 Nenhum teste encontrado para análise.")
            print("💡 Execute alguns testes primeiro usando o Strategy Lab.")
            return
        
        print(f"\n📊 DADOS DISPONÍVEIS:")
        print(f"   📋 {len(reports)} teste(s) encontrado(s)")
        
        # Carregar dados dos relatórios
        valid_results = []
        for report in reports:
            try:
                with open(report['filepath'], 'r') as f:
                    data = json.load(f)
                
                if 'data' in data and 'metrics' in data['data']:
                    valid_results.append(data['data'])
            except Exception as e:
                logger.warning(f"Erro ao carregar {report['filename']}: {e}")
        
        if not valid_results:
            print("❌ Nenhum resultado válido encontrado.")
            return
        
        print(f"   ✅ {len(valid_results)} resultado(s) válido(s) carregado(s)")
        
        # Análise de sweet spots
        print(f"\n🔍 ANALISANDO SWEET SPOTS...")
        
        # Ordenar por score composto
        scored_results = []
        for result in valid_results:
            score = self.factory_engine.validator.calculate_composite_score(result['metrics'])
            scored_results.append((result, score))
        
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # Top 5 sweet spots
        print(f"\n🏆 TOP 5 SWEET SPOTS:")
        for i, (result, score) in enumerate(scored_results[:5], 1):
            metrics = result['metrics']
            combination_name = result.get('combination_name', 'Unknown')
            validation = result.get('validation', 'Unknown')
            test_config = result.get('test_config', {})
            
            status_emoji = {
                'approved': '✅',
                'conditional': '⚠️',
                'rejected': '❌'
            }
            
            emoji = status_emoji.get(validation, '❓')
            
            print(f"\n   {i}. {emoji} {combination_name} (Score: {score:.1f})")
            print(f"      💰 ROI: {metrics['roi_percent']:+.2f}%")
            print(f"      🎯 Win Rate: {metrics['win_rate']:.1%}")
            print(f"      📈 Profit Factor: {metrics['profit_factor']:.2f}")
            print(f"      📉 Max Drawdown: {metrics['max_drawdown_percent']:.1f}%")
            print(f"      📊 Trades: {metrics['total_trades']}")
            if test_config:
                print(f"      📊 Config: {test_config.get('symbol', 'N/A')} {test_config.get('timeframe', 'N/A')}")
        
        # Recomendação final
        if scored_results:
            best_overall = scored_results[0][0]
            print(f"\n🎯 RECOMENDAÇÃO SWEET SPOT:")
            print(f"   🏆 {best_overall['combination_name']}")
            print(f"   📊 Score Composto: {scored_results[0][1]:.1f}/100")
            print(f"   ✅ Status: {best_overall['validation'].upper()}")
        
        input(f"\n📱 Pressione Enter para continuar...")
    
    def list_available_strategies(self):
        """Lista todas as estratégias disponíveis"""
        print("\n📋 ESTRATÉGIAS DISPONÍVEIS NO PROJETO MARKET_MANUS")
        print("="*70)
        
        print(f"\n🎯 ESTRATÉGIAS BÁSICAS (Implementadas):")
        strategies = self.factory_engine.strategy_engine.strategy_configs
        for i, (key, config) in enumerate(strategies.items(), 1):
            print(f"   {i}. {config['name']}")
            print(f"      📝 {config['description']}")
            print(f"      ⚠️ Risco: {config['risk_level']}")
            print(f"      📊 Timeframes: {', '.join(config['best_timeframes'])}")
            print(f"      🎯 Condições: {config['market_conditions']}")
            print()
        
        print(f"🔬 COMBINAÇÕES POSSÍVEIS:")
        combinations = self.factory_engine.combinator.get_all_combinations()
        total_combinations = sum(len(combos) for combos in combinations.values())
        
        print(f"   📊 Single strategies: {len(combinations['single'])} combinações")
        print(f"   📊 Dual combinations: {len(combinations['dual'])} combinações")
        print(f"   📊 Triple combinations: {len(combinations['triple'])} combinações")
        print(f"   📊 Full combinations: {len(combinations['full'])} combinações")
        print(f"   🎯 TOTAL: {total_combinations} combinações possíveis")
        
        input(f"\n📱 Pressione Enter para continuar...")
    
    def _show_test_history(self):
        """Mostra histórico de testes"""
        print("\n📊 HISTÓRICO DE TESTES")
        print("="*50)
        
        reports = self.factory_engine.report_manager.list_reports()
        
        if not reports:
            print("📭 Nenhum teste realizado ainda.")
            return
        
        print(f"\n📋 {len(reports)} teste(s) encontrado(s):")
        
        for i, report in enumerate(reports[:10], 1):  # Mostrar últimos 10
            status_emoji = {
                'approved': '✅',
                'conditional': '⚠️',
                'rejected': '❌',
                'Unknown': '❓'
            }
            
            emoji = status_emoji.get(report['validation'], '❓')
            timestamp = report['timestamp'][:19] if report['timestamp'] != 'Unknown' else 'Unknown'
            
            print(f"   {i}. {emoji} {report['strategy_mix']}")
            print(f"      📅 {timestamp}")
            print(f"      📁 {report['filename']}")
            print()
        
        if len(reports) > 10:
            print(f"   ... e mais {len(reports) - 10} teste(s)")
        
        input(f"\n📱 Pressione Enter para continuar...")
    
    # Métodos auxiliares (reutilizados da versão anterior)
    def _select_from_combinations(self, combinations: List, title: str) -> List:
        """Seleciona combinações específicas de uma lista"""
        print(f"\n🔬 {title.upper()}:")
        
        for i, combo in enumerate(combinations, 1):
            combo_name = self.factory_engine.combinator.get_combination_name(combo)
            print(f"   {i}. {combo_name} ({', '.join(combo)})")
        
        print(f"   A. Todas as {len(combinations)} combinações")
        
        while True:
            choice = input(f"\n📊 Escolha (1-{len(combinations)} ou A): ").strip()
            
            if choice.upper() == 'A':
                return combinations
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(combinations):
                    return [combinations[idx]]
                else:
                    print(f"❌ Escolha entre 1 e {len(combinations)} ou A")
            except ValueError:
                print("❌ Digite um número válido ou A")
    
    def _create_custom_combination(self) -> List:
        """Cria combinação personalizada de estratégias"""
        print(f"\n🎨 COMBINAÇÃO PERSONALIZADA:")
        
        strategies = list(self.factory_engine.strategy_engine.strategies.keys())
        print(f"\n🎯 ESTRATÉGIAS DISPONÍVEIS:")
        for i, strategy in enumerate(strategies, 1):
            print(f"   {i}. {strategy}")
        
        selected = []
        print(f"\n💡 Digite os números das estratégias separados por vírgula (ex: 1,2,3)")
        
        while True:
            choice = input(f"📊 Estratégias: ").strip()
            
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                
                if all(0 <= idx < len(strategies) for idx in indices):
                    selected = [strategies[idx] for idx in indices]
                    break
                else:
                    print(f"❌ Todos os números devem estar entre 1 e {len(strategies)}")
            except ValueError:
                print("❌ Digite números separados por vírgula (ex: 1,2,3)")
        
        print(f"\n✅ Combinação selecionada: {', '.join(selected)}")
        return [selected]
    
    def _display_test_results(self, result: Dict):
        """Exibe resultados de um teste individual"""
        metrics = result['metrics']
        test_config = result.get('test_config', {})
        
        print(f"\n📊 RESULTADOS DO TESTE")
        print("="*50)
        
        # Status de validação
        validation = result['validation']
        status_emoji = {
            'approved': '✅ APROVADA',
            'conditional': '⚠️ CONDICIONAL',
            'rejected': '❌ REJEITADA'
        }
        
        print(f"🎯 Estratégia: {result['combination_name']}")
        print(f"📊 Status: {status_emoji[validation]}")
        print(f"🏆 Score: {result['composite_score']:.1f}/100")
        
        # Configuração do teste
        print(f"\n⚙️ CONFIGURAÇÃO:")
        print(f"   📊 Símbolo: {test_config.get('symbol', 'N/A')}")
        print(f"   ⏰ Timeframe: {test_config.get('timeframe', 'N/A')}")
        print(f"   📅 Período: {test_config.get('period_name', 'N/A')}")
        
        # Métricas principais
        print(f"\n💰 PERFORMANCE:")
        print(f"   💰 Capital inicial: ${metrics['initial_capital_usd']:,.2f}")
        print(f"   💰 Capital final: ${metrics['final_capital_usd']:,.2f}")
        print(f"   📈 ROI: {metrics['roi_percent']:+.2f}%")
        print(f"   🎯 Win Rate: {metrics['win_rate']:.1%}")
        print(f"   📈 Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"   📉 Max Drawdown: {metrics['max_drawdown_percent']:.1f}%")
        print(f"   📊 Total Trades: {metrics['total_trades']}")
    
    def _display_comparative_analysis(self, results: List[Dict]):
        """Exibe análise comparativa de múltiplos resultados"""
        print(f"\n📊 ANÁLISE COMPARATIVA")
        print("="*60)
        
        # Ordenar por score
        results.sort(key=lambda x: x['composite_score'], reverse=True)
        
        print(f"\n🏆 RANKING POR PERFORMANCE:")
        for i, result in enumerate(results, 1):
            metrics = result['metrics']
            validation = result['validation']
            
            status_emoji = {
                'approved': '✅',
                'conditional': '⚠️',
                'rejected': '❌'
            }
            
            emoji = status_emoji[validation]
            
            print(f"\n   {i}. {emoji} {result['combination_name']}")
            print(f"      🏆 Score: {result['composite_score']:.1f}")
            print(f"      💰 ROI: {metrics['roi_percent']:+.2f}%")
            print(f"      🎯 Win Rate: {metrics['win_rate']:.1%}")
            print(f"      📊 Trades: {metrics['total_trades']}")
        
        # Estatísticas gerais
        approved = [r for r in results if r['validation'] == 'approved']
        conditional = [r for r in results if r['validation'] == 'conditional']
        rejected = [r for r in results if r['validation'] == 'rejected']
        
        print(f"\n📊 RESUMO GERAL:")
        print(f"   ✅ Aprovadas: {len(approved)}")
        print(f"   ⚠️ Condicionais: {len(conditional)}")
        print(f"   ❌ Rejeitadas: {len(rejected)}")
        print(f"   📊 Total testado: {len(results)}")
        
        if approved:
            best = approved[0]
            print(f"\n🏆 MELHOR ESTRATÉGIA:")
            print(f"   🎯 {best['combination_name']}")
            print(f"   🏆 Score: {best['composite_score']:.1f}")
            print(f"   💰 ROI: {best['metrics']['roi_percent']:+.2f}%")
    
    def _display_validation_summary(self, results: List[Dict], approved: List[Dict], 
                                  conditional: List[Dict], rejected: List[Dict]):
        """Exibe resumo da validação completa"""
        print(f"\n📊 RESUMO DA VALIDAÇÃO COMPLETA")
        print("="*60)
        
        print(f"\n🎯 RESULTADOS GERAIS:")
        print(f"   📊 Total testado: {len(results)}")
        print(f"   ✅ Aprovadas: {len(approved)} ({len(approved)/len(results)*100:.1f}%)")
        print(f"   ⚠️ Condicionais: {len(conditional)} ({len(conditional)/len(results)*100:.1f}%)")
        print(f"   ❌ Rejeitadas: {len(rejected)} ({len(rejected)/len(results)*100:.1f}%)")
        
        if approved:
            print(f"\n✅ TOP 3 ESTRATÉGIAS APROVADAS:")
            approved.sort(key=lambda x: x['composite_score'], reverse=True)
            
            for i, result in enumerate(approved[:3], 1):
                metrics = result['metrics']
                print(f"\n   {i}. {result['combination_name']}")
                print(f"      🏆 Score: {result['composite_score']:.1f}")
                print(f"      💰 ROI: {metrics['roi_percent']:+.2f}%")
                print(f"      🎯 Win Rate: {metrics['win_rate']:.1%}")
                print(f"      📈 Profit Factor: {metrics['profit_factor']:.2f}")
        
        print(f"\n💡 RECOMENDAÇÃO:")
        if approved:
            best = approved[0]
            print(f"   🏆 Use: {best['combination_name']}")
            print(f"   📊 Melhor score geral: {best['composite_score']:.1f}")
        elif conditional:
            best = max(conditional, key=lambda x: x['composite_score'])
            print(f"   ⚠️ Considere: {best['combination_name']}")
            print(f"   📊 Melhor entre condicionais: {best['composite_score']:.1f}")
        else:
            print(f"   ❌ Nenhuma estratégia recomendada")
            print(f"   💡 Considere ajustar parâmetros ou período de teste")
        
        input(f"\n📱 Pressione Enter para continuar...")
    
    def run(self):
        """Executa o CLI principal"""
        self.display_header()
        
        while True:
            self.display_main_menu()
            
            try:
                choice = input("🔢 Escolha uma opção: ").strip()
                
                if choice == '0':
                    print("\n👋 Obrigado por usar a Strategy Factory V2!")
                    break
                
                elif choice == '1':
                    self.configure_capital()
                
                elif choice == '2':
                    self.strategy_lab()
                
                elif choice == '3':
                    self.sweet_spot_finder()
                
                elif choice == '4':
                    self._show_test_history()
                
                elif choice == '5':
                    print("\n🚧 Ranking de Estratégias em desenvolvimento...")
                
                elif choice == '6':
                    print("\n🚧 Exportar Relatórios em desenvolvimento...")
                
                elif choice == '7':
                    print("\n🚧 Configurações Avançadas em desenvolvimento...")
                
                elif choice.lower() in ['🔍', 'list', 'l']:
                    self.list_available_strategies()
                
                else:
                    print("❌ Opção inválida. Tente novamente.")
                
            except KeyboardInterrupt:
                print("\n\n👋 Saindo...")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")

if __name__ == "__main__":
    try:
        cli = StrategyFactoryCLIV2()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)

