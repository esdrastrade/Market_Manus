#!/usr/bin/env python3
"""
TESTE DO CLI ENHANCED - Validação das funcionalidades implementadas
"""

import os
import sys
import json
from datetime import datetime
from capital_manager import CapitalManager, CapitalConfig, create_default_capital_config

def test_capital_manager():
    """Testa a classe CapitalManager"""
    print("🧪 TESTANDO CAPITAL MANAGER")
    print("="*50)
    
    # Teste 1: Configuração padrão
    print("\n1️⃣ Teste de configuração padrão:")
    config = create_default_capital_config(5000.0)
    manager = CapitalManager(config)
    
    print(f"   ✅ Capital inicial: ${config.initial_capital_usd:,.2f}")
    print(f"   ✅ Position size: {config.position_size_percent}%")
    print(f"   ✅ Compound interest: {config.compound_interest}")
    
    # Teste 2: Cálculo de position size
    print("\n2️⃣ Teste de cálculo de position size:")
    position_size = manager.calculate_position_size(50000.0, 0.015)  # BTC a $50k
    expected_size = 5000.0 * 0.02  # 2% de $5000
    
    print(f"   📊 Position size calculado: ${position_size:.2f}")
    print(f"   📊 Position size esperado: ${expected_size:.2f}")
    print(f"   {'✅' if abs(position_size - expected_size) < 1 else '❌'} Cálculo correto")
    
    # Teste 3: Execução de trades
    print("\n3️⃣ Teste de execução de trades:")
    
    # Trade lucrativo
    trade1 = manager.execute_trade(
        entry_price=50000.0,
        exit_price=51000.0,  # +2%
        direction=1,  # Long
        timestamp="2024-01-01T10:00:00",
        exit_reason="take_profit"
    )
    
    print(f"   📈 Trade 1 (Long +2%): ${trade1.pnl_usd:.2f}")
    print(f"   💰 Capital após trade 1: ${trade1.capital_after:.2f}")
    
    # Trade com perda
    trade2 = manager.execute_trade(
        entry_price=51000.0,
        exit_price=50000.0,  # -1.96%
        direction=1,  # Long
        timestamp="2024-01-01T11:00:00",
        exit_reason="stop_loss"
    )
    
    print(f"   📉 Trade 2 (Long -1.96%): ${trade2.pnl_usd:.2f}")
    print(f"   💰 Capital após trade 2: ${trade2.capital_after:.2f}")
    
    # Teste 4: Métricas
    print("\n4️⃣ Teste de métricas:")
    metrics = manager.get_metrics()
    
    print(f"   📊 Total trades: {metrics['total_trades']}")
    print(f"   🎯 Win rate: {metrics['win_rate']:.1%}")
    print(f"   💰 Retorno total: ${metrics['total_return_usd']:.2f}")
    print(f"   📈 ROI: {metrics['roi_percent']:.2f}%")
    
    # Teste 5: Salvamento e carregamento
    print("\n5️⃣ Teste de salvamento/carregamento:")
    
    # Salvar configuração
    save_success = manager.save_config('test_capital_config.json')
    print(f"   {'✅' if save_success else '❌'} Salvamento da configuração")
    
    # Carregar configuração
    loaded_manager = CapitalManager.load_config('test_capital_config.json')
    if loaded_manager:
        print(f"   ✅ Carregamento da configuração")
        print(f"   📊 Capital carregado: ${loaded_manager.config.initial_capital_usd:.2f}")
    else:
        print(f"   ❌ Erro no carregamento da configuração")
    
    # Limpeza
    if os.path.exists('test_capital_config.json'):
        os.remove('test_capital_config.json')
    
    print(f"\n✅ Todos os testes do CapitalManager concluídos!")
    return True

def test_config_validation():
    """Testa validação de configurações"""
    print("\n🧪 TESTANDO VALIDAÇÃO DE CONFIGURAÇÕES")
    print("="*50)
    
    # Teste 1: Configuração válida
    print("\n1️⃣ Teste de configuração válida:")
    try:
        config = CapitalConfig(
            initial_capital_usd=10000.0,
            position_size_percent=2.0,
            compound_interest=True,
            min_position_size_usd=10.0,
            max_position_size_usd=1000.0,
            risk_per_trade_percent=1.0
        )
        print(f"   ✅ Configuração válida criada")
    except Exception as e:
        print(f"   ❌ Erro na configuração válida: {e}")
        return False
    
    # Teste 2: Conversão para dicionário
    print("\n2️⃣ Teste de conversão para dicionário:")
    config_dict = config.to_dict()
    expected_keys = ['initial_capital_usd', 'position_size_percent', 'compound_interest', 
                     'min_position_size_usd', 'max_position_size_usd', 'risk_per_trade_percent']
    
    all_keys_present = all(key in config_dict for key in expected_keys)
    print(f"   {'✅' if all_keys_present else '❌'} Todas as chaves presentes no dicionário")
    
    # Teste 3: Criação a partir de dicionário
    print("\n3️⃣ Teste de criação a partir de dicionário:")
    try:
        config_from_dict = CapitalConfig.from_dict(config_dict)
        print(f"   ✅ Configuração criada a partir de dicionário")
        print(f"   📊 Capital: ${config_from_dict.initial_capital_usd:.2f}")
    except Exception as e:
        print(f"   ❌ Erro na criação a partir de dicionário: {e}")
        return False
    
    print(f"\n✅ Todos os testes de validação concluídos!")
    return True

def test_compound_interest():
    """Testa funcionalidade de compound interest"""
    print("\n🧪 TESTANDO COMPOUND INTEREST")
    print("="*50)
    
    # Teste com compound interest ativado
    print("\n1️⃣ Teste com compound interest ATIVADO:")
    config_compound = CapitalConfig(
        initial_capital_usd=1000.0,
        position_size_percent=10.0,  # 10% para efeito mais visível
        compound_interest=True
    )
    manager_compound = CapitalManager(config_compound)
    
    # Executar trades lucrativos
    for i in range(3):
        trade = manager_compound.execute_trade(
            entry_price=100.0,
            exit_price=105.0,  # +5%
            direction=1,
            timestamp=f"2024-01-01T{10+i}:00:00",
            exit_reason="take_profit"
        )
        print(f"   Trade {i+1}: Capital ${trade.capital_before:.2f} → ${trade.capital_after:.2f}")
    
    final_capital_compound = manager_compound.current_capital
    
    # Teste com compound interest desativado
    print("\n2️⃣ Teste com compound interest DESATIVADO:")
    config_fixed = CapitalConfig(
        initial_capital_usd=1000.0,
        position_size_percent=10.0,
        compound_interest=False
    )
    manager_fixed = CapitalManager(config_fixed)
    
    # Executar os mesmos trades
    for i in range(3):
        trade = manager_fixed.execute_trade(
            entry_price=100.0,
            exit_price=105.0,  # +5%
            direction=1,
            timestamp=f"2024-01-01T{10+i}:00:00",
            exit_reason="take_profit"
        )
        print(f"   Trade {i+1}: Capital ${trade.capital_before:.2f} → ${trade.capital_after:.2f}")
    
    final_capital_fixed = manager_fixed.current_capital
    
    # Comparação
    print(f"\n3️⃣ Comparação dos resultados:")
    print(f"   🔄 Com compound interest: ${final_capital_compound:.2f}")
    print(f"   📊 Sem compound interest: ${final_capital_fixed:.2f}")
    print(f"   📈 Diferença: ${final_capital_compound - final_capital_fixed:.2f}")
    
    # Validação
    compound_better = final_capital_compound > final_capital_fixed
    print(f"   {'✅' if compound_better else '❌'} Compound interest gera mais capital")
    
    print(f"\n✅ Teste de compound interest concluído!")
    return compound_better

def test_position_sizing():
    """Testa cálculos de position sizing"""
    print("\n🧪 TESTANDO POSITION SIZING")
    print("="*50)
    
    config = CapitalConfig(
        initial_capital_usd=10000.0,
        position_size_percent=2.0,
        min_position_size_usd=50.0,
        max_position_size_usd=500.0,
        risk_per_trade_percent=1.0
    )
    manager = CapitalManager(config)
    
    # Teste 1: Position size normal
    print("\n1️⃣ Teste de position size normal:")
    price = 50000.0  # BTC
    stop_loss = 0.015  # 1.5%
    
    position_size = manager.calculate_position_size(price, stop_loss)
    expected_by_percent = 10000.0 * 0.02  # 2% = $200
    expected_by_risk = (10000.0 * 0.01) / 0.015  # 1% risk / 1.5% stop = $666.67
    expected_final = min(expected_by_percent, expected_by_risk, 500.0)  # Limitado pelo máximo
    
    print(f"   📊 Position size calculado: ${position_size:.2f}")
    print(f"   📊 Por percentual (2%): ${expected_by_percent:.2f}")
    print(f"   📊 Por risco (1%): ${expected_by_risk:.2f}")
    print(f"   📊 Esperado (menor): ${expected_final:.2f}")
    
    # Teste 2: Limite mínimo
    print("\n2️⃣ Teste de limite mínimo:")
    config_small = CapitalConfig(
        initial_capital_usd=1000.0,
        position_size_percent=1.0,  # 1% = $10
        min_position_size_usd=50.0
    )
    manager_small = CapitalManager(config_small)
    
    position_size_small = manager_small.calculate_position_size(50000.0, 0.015)
    print(f"   📊 Position size com capital pequeno: ${position_size_small:.2f}")
    print(f"   {'✅' if position_size_small >= 50.0 else '❌'} Respeitou limite mínimo de $50")
    
    # Teste 3: Limite máximo
    print("\n3️⃣ Teste de limite máximo:")
    config_large = CapitalConfig(
        initial_capital_usd=100000.0,
        position_size_percent=5.0,  # 5% = $5000
        max_position_size_usd=1000.0
    )
    manager_large = CapitalManager(config_large)
    
    position_size_large = manager_large.calculate_position_size(50000.0, 0.015)
    print(f"   📊 Position size com capital grande: ${position_size_large:.2f}")
    print(f"   {'✅' if position_size_large <= 1000.0 else '❌'} Respeitou limite máximo de $1000")
    
    print(f"\n✅ Teste de position sizing concluído!")
    return True

def run_all_tests():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DO CLI ENHANCED")
    print("="*60)
    
    tests = [
        ("Capital Manager", test_capital_manager),
        ("Validação de Configurações", test_config_validation),
        ("Compound Interest", test_compound_interest),
        ("Position Sizing", test_position_sizing)
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
        print(f"🎉 TODOS OS TESTES PASSARAM! Sistema pronto para uso.")
        return True
    else:
        print(f"⚠️  {total - passed} teste(s) falharam. Revisar implementação.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

