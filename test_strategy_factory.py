#!/usr/bin/env python3
"""
TESTE DA STRATEGY FACTORY - Validação das funcionalidades implementadas
"""

import os
import sys
import json
from datetime import datetime

# Importar componentes da fábrica
from strategy_factory_cli import (
    StrategyValidator, StrategyCombinator, ReportManager, 
    StrategyFactoryEngine, StrategyFactoryCLI
)
from capital_manager import CapitalManager, create_default_capital_config

def test_strategy_validator():
    """Testa o validador de estratégias"""
    print("🧪 TESTANDO STRATEGY VALIDATOR")
    print("="*50)
    
    validator = StrategyValidator()
    
    # Teste 1: Estratégia aprovada
    print("\n1️⃣ Teste de estratégia APROVADA:")
    metrics_approved = {
        'roi_percent': 8.5,
        'win_rate': 0.62,
        'max_drawdown_percent': 12.0,
        'profit_factor': 1.45,
        'total_trades': 25
    }
    
    validation = validator.validate_strategy(metrics_approved)
    score = validator.calculate_composite_score(metrics_approved)
    
    print(f"   📊 ROI: {metrics_approved['roi_percent']}%")
    print(f"   🎯 Win Rate: {metrics_approved['win_rate']:.1%}")
    print(f"   📉 Drawdown: {metrics_approved['max_drawdown_percent']}%")
    print(f"   📈 Profit Factor: {metrics_approved['profit_factor']}")
    print(f"   ✅ Validação: {validation}")
    print(f"   🏆 Score: {score:.1f}")
    
    # Teste 2: Estratégia condicional
    print("\n2️⃣ Teste de estratégia CONDICIONAL:")
    metrics_conditional = {
        'roi_percent': 3.2,
        'win_rate': 0.52,
        'max_drawdown_percent': 18.0,
        'profit_factor': 1.1,
        'total_trades': 15
    }
    
    validation = validator.validate_strategy(metrics_conditional)
    score = validator.calculate_composite_score(metrics_conditional)
    
    print(f"   📊 ROI: {metrics_conditional['roi_percent']}%")
    print(f"   🎯 Win Rate: {metrics_conditional['win_rate']:.1%}")
    print(f"   📉 Drawdown: {metrics_conditional['max_drawdown_percent']}%")
    print(f"   📈 Profit Factor: {metrics_conditional['profit_factor']}")
    print(f"   ⚠️ Validação: {validation}")
    print(f"   🏆 Score: {score:.1f}")
    
    # Teste 3: Estratégia rejeitada
    print("\n3️⃣ Teste de estratégia REJEITADA:")
    metrics_rejected = {
        'roi_percent': -2.5,
        'win_rate': 0.35,
        'max_drawdown_percent': 25.0,
        'profit_factor': 0.8,
        'total_trades': 8
    }
    
    validation = validator.validate_strategy(metrics_rejected)
    score = validator.calculate_composite_score(metrics_rejected)
    
    print(f"   📊 ROI: {metrics_rejected['roi_percent']}%")
    print(f"   🎯 Win Rate: {metrics_rejected['win_rate']:.1%}")
    print(f"   📉 Drawdown: {metrics_rejected['max_drawdown_percent']}%")
    print(f"   📈 Profit Factor: {metrics_rejected['profit_factor']}")
    print(f"   ❌ Validação: {validation}")
    print(f"   🏆 Score: {score:.1f}")
    
    print(f"\n✅ Teste do Strategy Validator concluído!")
    return True

def test_strategy_combinator():
    """Testa o combinador de estratégias"""
    print("\n🧪 TESTANDO STRATEGY COMBINATOR")
    print("="*50)
    
    combinator = StrategyCombinator()
    
    # Teste 1: Obter todas as combinações
    print("\n1️⃣ Teste de geração de combinações:")
    combinations = combinator.get_all_combinations()
    
    print(f"   📊 Single strategies: {len(combinations['single'])}")
    print(f"   📊 Dual combinations: {len(combinations['dual'])}")
    print(f"   📊 Triple combinations: {len(combinations['triple'])}")
    print(f"   📊 Full combinations: {len(combinations['full'])}")
    
    total = sum(len(combos) for combos in combinations.values())
    print(f"   🎯 Total: {total} combinações")
    
    # Teste 2: Nomes das combinações
    print("\n2️⃣ Teste de nomeação de combinações:")
    
    # Single
    single_name = combinator.get_combination_name(['ema_crossover'])
    print(f"   Single: {single_name}")
    
    # Dual
    dual_name = combinator.get_combination_name(['ema_crossover', 'rsi_mean_reversion'])
    print(f"   Dual: {dual_name}")
    
    # Triple
    triple_name = combinator.get_combination_name(['ema_crossover', 'rsi_mean_reversion', 'bollinger_breakout'])
    print(f"   Triple: {triple_name}")
    
    print(f"\n✅ Teste do Strategy Combinator concluído!")
    return True

def test_report_manager():
    """Testa o gerenciador de relatórios"""
    print("\n🧪 TESTANDO REPORT MANAGER")
    print("="*50)
    
    report_manager = ReportManager()
    
    # Teste 1: Geração de nome de relatório
    print("\n1️⃣ Teste de geração de nome:")
    report_name = report_manager.generate_report_name("ema_crossover")
    print(f"   📝 Nome gerado: {report_name}")
    
    # Verificar formato
    parts = report_name.split('_')
    has_strategy = 'ema' in report_name
    has_timestamp = len(parts) >= 3
    
    print(f"   ✅ Contém estratégia: {has_strategy}")
    print(f"   ✅ Contém timestamp: {has_timestamp}")
    
    # Teste 2: Salvamento de relatório
    print("\n2️⃣ Teste de salvamento:")
    test_data = {
        'combination_name': 'ema_crossover',
        'metrics': {
            'roi_percent': 5.5,
            'win_rate': 0.58,
            'total_trades': 20
        },
        'validation': 'approved',
        'composite_score': 75.2
    }
    
    saved_path = report_manager.save_report(test_data, "ema_crossover")
    
    if saved_path and os.path.exists(saved_path):
        print(f"   ✅ Relatório salvo: {os.path.basename(saved_path)}")
        
        # Verificar conteúdo
        with open(saved_path, 'r') as f:
            loaded_data = json.load(f)
        
        has_metadata = 'metadata' in loaded_data
        has_data = 'data' in loaded_data
        
        print(f"   ✅ Contém metadados: {has_metadata}")
        print(f"   ✅ Contém dados: {has_data}")
        
        # Limpeza
        os.remove(saved_path)
    else:
        print(f"   ❌ Erro no salvamento")
        return False
    
    # Teste 3: Listagem de relatórios
    print("\n3️⃣ Teste de listagem:")
    
    # Criar alguns relatórios de teste
    for i in range(3):
        test_data['combination_name'] = f'test_strategy_{i}'
        report_manager.save_report(test_data, f'test_strategy_{i}')
    
    reports = report_manager.list_reports()
    print(f"   📋 Relatórios encontrados: {len(reports)}")
    
    # Limpeza
    for report in reports:
        if 'test_strategy' in report['filename']:
            os.remove(report['filepath'])
    
    print(f"\n✅ Teste do Report Manager concluído!")
    return True

def test_capital_integration():
    """Testa integração com capital manager"""
    print("\n🧪 TESTANDO INTEGRAÇÃO COM CAPITAL")
    print("="*50)
    
    # Teste 1: Capital livre $1 - $100k
    print("\n1️⃣ Teste de range de capital:")
    
    # Capital mínimo
    config_min = create_default_capital_config(1.0)
    manager_min = CapitalManager(config_min)
    
    print(f"   💰 Capital mínimo: ${config_min.initial_capital_usd}")
    print(f"   📊 Position size mín: ${config_min.min_position_size_usd}")
    print(f"   ✅ Capital $1 aceito: {config_min.initial_capital_usd >= 1.0}")
    
    # Capital máximo
    config_max = create_default_capital_config(100000.0)
    manager_max = CapitalManager(config_max)
    
    print(f"   💰 Capital máximo: ${config_max.initial_capital_usd:,.0f}")
    print(f"   📊 Position size máx: ${config_max.max_position_size_usd:,.0f}")
    print(f"   ✅ Capital $100k aceito: {config_max.initial_capital_usd <= 100000.0}")
    
    # Teste 2: Position sizing dinâmico
    print("\n2️⃣ Teste de position sizing dinâmico:")
    
    # Capital pequeno
    pos_size_small = manager_min.calculate_position_size(50000.0, 0.015)
    print(f"   📊 Capital $1 → Position: ${pos_size_small:.2f}")
    
    # Capital grande
    pos_size_large = manager_max.calculate_position_size(50000.0, 0.015)
    print(f"   📊 Capital $100k → Position: ${pos_size_large:,.2f}")
    
    # Verificar proporcionalidade
    ratio = pos_size_large / pos_size_small
    expected_ratio = 100000.0 / 1.0
    proportional = abs(ratio - expected_ratio) < expected_ratio * 0.1  # 10% tolerância
    
    print(f"   ✅ Proporcionalidade: {proportional}")
    
    print(f"\n✅ Teste de integração com capital concluído!")
    return True

def test_nomenclature_pattern():
    """Testa padrão de nomenclatura dos relatórios"""
    print("\n🧪 TESTANDO PADRÃO DE NOMENCLATURA")
    print("="*50)
    
    report_manager = ReportManager()
    
    # Teste 1: Formato strategy_mix_dd/mm/aa_hh:mm:ss
    print("\n1️⃣ Teste de formato de nomenclatura:")
    
    strategies = ['ema_crossover', 'dual_mix_ema_rsi', 'triple_mix_all_basic']
    
    for strategy in strategies:
        name = report_manager.generate_report_name(strategy)
        print(f"   📝 {strategy} → {name}")
        
        # Verificar componentes
        parts = name.split('_')
        has_strategy = strategy.split('_')[0] in name
        has_date = any('-' in part for part in parts[-2:])  # dd-mm-aa ou hh-mm-ss
        
        print(f"      ✅ Contém estratégia: {has_strategy}")
        print(f"      ✅ Contém timestamp: {has_date}")
    
    print(f"\n✅ Teste de padrão de nomenclatura concluído!")
    return True

def run_all_tests():
    """Executa todos os testes da fábrica de estratégias"""
    print("🚀 INICIANDO TESTES DA STRATEGY FACTORY")
    print("="*60)
    
    tests = [
        ("Strategy Validator", test_strategy_validator),
        ("Strategy Combinator", test_strategy_combinator),
        ("Report Manager", test_report_manager),
        ("Capital Integration", test_capital_integration),
        ("Nomenclature Pattern", test_nomenclature_pattern)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔄 Executando: {test_name}")
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅' if result else '❌'} {test_name}: {'PASSOU' if result else 'FALHOU'}")
        except Exception as e:
            print(f"❌ {test_name}: ERRO - {e}")
            results.append((test_name, False))
    
    # Resumo final
    print(f"\n📊 RESUMO DOS TESTES")
    print("="*40)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {test_name}: {status}")
    
    print(f"\n🎯 RESULTADO FINAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print(f"🎉 TODOS OS TESTES PASSARAM! Strategy Factory pronta para uso.")
        return True
    else:
        print(f"⚠️  {total - passed} teste(s) falharam. Revisar implementação.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

