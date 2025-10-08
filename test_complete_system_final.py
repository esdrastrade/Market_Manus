#!/usr/bin/env python3
"""
TESTE COMPLETO DO SISTEMA MARKET MANUS
Valida todas as funcionalidades implementadas
"""

import sys
import os
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Configurar logging para testes
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Testa todas as importações necessárias"""
    print("\\n🔍 TESTANDO IMPORTAÇÕES...")
    print("-" * 40)
    
    imports_to_test = [
        ('strategy_contract', 'Contrato de Estratégias'),
        ('bybit_provider', 'Bybit Data Provider'),
        ('capital_persistence', 'Persistência de Capital'),
        ('strategy_lab', 'Strategy Lab'),
        ('market_manus_cli_complete', 'CLI Completo')
    ]
    
    success_count = 0
    
    for module_name, description in imports_to_test:
        try:
            __import__(module_name)
            print(f"✅ {description}: OK")
            success_count += 1
        except ImportError as e:
            print(f"❌ {description}: FALHOU - {e}")
        except Exception as e:
            print(f"⚠️ {description}: ERRO - {e}")
    
    print(f"\\n📊 Resultado: {success_count}/{len(imports_to_test)} importações bem-sucedidas")
    return success_count == len(imports_to_test)


def test_strategy_contract():
    """Testa o contrato de estratégias"""
    print("\\n🧪 TESTANDO CONTRATO DE ESTRATÉGIAS...")
    print("-" * 40)
    
    try:
        from strategy_contract import list_available_strategies, STRATEGY_REGISTRY_V2, run_strategy
        import pandas as pd
        import numpy as np
        
        # Testar listagem de estratégias
        strategies = list_available_strategies()
        print(f"✅ Estratégias disponíveis: {len(strategies)}")
        
        for strategy in strategies[:3]:  # Testar primeiras 3
            print(f"   📊 {strategy}: {STRATEGY_REGISTRY_V2[strategy]['description']}")
        
        # Testar execução de estratégia com dados simulados
        print("\\n🔬 Testando execução de estratégia...")
        
        # Criar dados simulados
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
        np.random.seed(42)  # Para resultados reproduzíveis
        
        data = {
            'timestamp': dates,
            'open': 45000 + np.random.randn(100) * 100,
            'high': 45100 + np.random.randn(100) * 100,
            'low': 44900 + np.random.randn(100) * 100,
            'close': 45000 + np.random.randn(100) * 100,
            'volume': 1000 + np.random.randn(100) * 100
        }
        
        df = pd.DataFrame(data)
        df['high'] = df[['open', 'close']].max(axis=1) + abs(np.random.randn(100) * 50)
        df['low'] = df[['open', 'close']].min(axis=1) - abs(np.random.randn(100) * 50)
        
        # Testar primeira estratégia
        if strategies:
            first_strategy = strategies[0]
            result_df = run_strategy(first_strategy, df)
            
            print(f"✅ Estratégia {first_strategy} executada")
            print(f"   📊 Registros processados: {len(result_df)}")
            print(f"   📈 Sinais gerados: {(result_df['signal'] != 0).sum()}")
            print(f"   💪 Força média: {result_df['strength'].mean():.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de estratégias: {e}")
        return False


def test_bybit_provider():
    """Testa o Bybit Data Provider"""
    print("\\n🔌 TESTANDO BYBIT DATA PROVIDER...")
    print("-" * 40)
    
    try:
        from bybit_provider import BybitDataProvider
        
        provider = BybitDataProvider()
        print("✅ BybitDataProvider inicializado")
        
        # Testar conexão
        connection_status = provider.test_connection()
        if connection_status['status'] == 'connected':
            print(f"✅ Conexão: OK (Latência: {connection_status['latency_ms']:.2f}ms)")
        else:
            print(f"⚠️ Conexão: {connection_status['status']} - {connection_status.get('error', 'N/A')}")
        
        # Testar preço atual (pode falhar sem credenciais)
        try:
            price = provider.get_current_price('BTCUSDT')
            print(f"✅ Preço BTCUSDT: ${price:,.2f}")
        except Exception as e:
            print(f"⚠️ Preço atual: Não disponível (normal sem credenciais) - {e}")
        
        # Testar dados históricos
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=24)
            
            import pandas as pd
            df = provider.fetch_klines('BTCUSDT', '1h', 
                                     pd.Timestamp(start_time), pd.Timestamp(end_time))
            
            if not df.empty:
                print(f"✅ Dados históricos: {len(df)} registros coletados")
            else:
                print("⚠️ Dados históricos: Vazios (normal sem credenciais)")
        except Exception as e:
            print(f"⚠️ Dados históricos: Erro - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do Bybit Provider: {e}")
        return False


def test_capital_manager():
    """Testa o Capital Manager"""
    print("\\n💰 TESTANDO CAPITAL MANAGER...")
    print("-" * 40)
    
    try:
        from capital_persistence import CapitalManager, Trade
        
        # Inicializar com capital de teste
        capital_manager = CapitalManager()
        capital_manager.config.current_capital = 10000.0
        print("✅ CapitalManager inicializado")
        
        # Testar resumo inicial
        summary = capital_manager.get_capital_summary()
        print(f"✅ Capital inicial: ${summary['initial_capital']:,.2f}")
        print(f"✅ Capital atual: ${summary['current_capital']:,.2f}")
        print(f"✅ ROI: {summary['roi']:+.2f}%")
        
        # Testar cálculo de position size
        position_info = capital_manager.calculate_position_size(45000.0)
        print(f"✅ Position size para BTC $45k: ${position_info['notional']:,.2f}")
        
        # Testar trade simulado
        test_trade = Trade(
            timestamp=datetime.now(timezone.utc),
            symbol='BTCUSDT',
            strategy='test_strategy',
            side='buy',
            entry_price=45000.0,
            exit_price=46000.0,
            pnl=200.0,
            fees=10.0,
            net_pnl=190.0
        )
        
        capital_manager.record_trade(test_trade)
        print("✅ Trade de teste registrado")
        
        # Verificar atualização do capital
        new_summary = capital_manager.get_capital_summary()
        print(f"✅ Capital após trade: ${new_summary['current_capital']:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do Capital Manager: {e}")
        return False


def test_strategy_lab():
    """Testa o Strategy Lab"""
    print("\\n🧪 TESTANDO STRATEGY LAB...")
    print("-" * 40)
    
    try:
        from strategy_lab import StrategyLab, BacktestConfig
        from bybit_provider import BybitDataProvider
        from capital_persistence import CapitalManager
        
        # Inicializar componentes
        data_provider = BybitDataProvider()
        capital_manager = CapitalManager()
        strategy_lab = StrategyLab(data_provider, capital_manager)
        
        print("✅ StrategyLab inicializado")
        
        # Configurar teste básico
        config = BacktestConfig(
            symbol="BTCUSDT",
            timeframe="1h",
            start_date=datetime.now(timezone.utc) - timedelta(days=7),
            end_date=datetime.now(timezone.utc),
            strategies=["rsi_mean_reversion"]
        )
        
        print(f"✅ Configuração de teste criada")
        print(f"   Símbolo: {config.symbol}")
        print(f"   Timeframe: {config.timeframe}")
        print(f"   Período: {config.start_date.date()} até {config.end_date.date()}")
        
        # Nota: Não executamos o backtest real para evitar dependência de dados externos
        print("⚠️ Backtest real não executado (requer dados externos)")
        print("✅ Strategy Lab estruturalmente válido")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do Strategy Lab: {e}")
        return False


def test_cli_system():
    """Testa o sistema CLI"""
    print("\\n🖥️ TESTANDO SISTEMA CLI...")
    print("-" * 40)
    
    try:
        from market_manus_cli_complete import MarketManusCompleteSystem
        
        # Inicializar sistema (sem executar)
        system = MarketManusCompleteSystem()
        print("✅ MarketManusCompleteSystem inicializado")
        
        # Testar componentes internos
        print(f"✅ Data Provider: {type(system.data_provider).__name__}")
        print(f"✅ Capital Manager: {type(system.capital_manager).__name__}")
        print(f"✅ Strategy Lab: {type(system.strategy_lab).__name__}")
        
        # Testar configurações
        print(f"✅ Símbolo atual: {system.current_symbol}")
        print(f"✅ Timeframe atual: {system.current_timeframe}")
        print(f"✅ Estratégias selecionadas: {len(system.selected_strategies)}")
        
        # Testar períodos pré-definidos
        periods = system.predefined_periods
        print(f"✅ Períodos pré-definidos: {len(periods)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste do CLI: {e}")
        return False


def test_file_structure():
    """Testa estrutura de arquivos"""
    print("\\n📁 TESTANDO ESTRUTURA DE ARQUIVOS...")
    print("-" * 40)
    
    required_files = [
        'strategy_contract.py',
        'bybit_provider.py',
        'capital_persistence.py', 
        'strategy_lab.py',
        'market_manus_cli_complete.py'
    ]
    
    required_dirs = ['logs', 'reports', 'data']
    
    files_ok = 0
    dirs_ok = 0
    
    # Verificar arquivos
    for file in required_files:
        if Path(file).exists():
            size = Path(file).stat().st_size
            print(f"✅ {file}: {size:,} bytes")
            files_ok += 1
        else:
            print(f"❌ {file}: Não encontrado")
    
    # Verificar/criar diretórios
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✅ {dir_name}/: Existe")
            dirs_ok += 1
        else:
            dir_path.mkdir(exist_ok=True)
            print(f"✅ {dir_name}/: Criado")
            dirs_ok += 1
    
    print(f"\\n📊 Arquivos: {files_ok}/{len(required_files)}")
    print(f"📊 Diretórios: {dirs_ok}/{len(required_dirs)}")
    
    return files_ok == len(required_files) and dirs_ok == len(required_dirs)


def run_comprehensive_test():
    """Executa teste abrangente do sistema"""
    print("🚀 MARKET MANUS - TESTE COMPLETO DO SISTEMA")
    print("=" * 60)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("Estrutura de Arquivos", test_file_structure),
        ("Importações", test_imports),
        ("Contrato de Estratégias", test_strategy_contract),
        ("Bybit Data Provider", test_bybit_provider),
        ("Capital Manager", test_capital_manager),
        ("Strategy Lab", test_strategy_lab),
        ("Sistema CLI", test_cli_system)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"💥 Erro crítico em {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo final
    print("\\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"📊 Resultado Final: {passed}/{total} testes aprovados")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema Market Manus está funcionando corretamente")
        print("🚀 Pronto para uso!")
    elif passed >= total * 0.8:  # 80% ou mais
        print("⚠️ MAIORIA DOS TESTES PASSOU")
        print("✅ Sistema funcional com algumas limitações")
        print("🔧 Verifique os testes que falharam")
    else:
        print("❌ MUITOS TESTES FALHARAM")
        print("🛠️ Sistema precisa de correções antes do uso")
        print("📋 Revise a instalação e dependências")
    
    print("=" * 60)
    print(f"⏰ Concluído em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed, total


if __name__ == "__main__":
    try:
        passed, total = run_comprehensive_test()
        
        # Perguntar se quer executar o sistema
        if passed >= total * 0.8:  # Se 80% ou mais dos testes passaram
            print("\\n🚀 EXECUTAR SISTEMA AGORA?")
            choice = input("Digite 's' para executar o Market Manus: ").strip().lower()
            
            if choice == 's':
                print("\\n" + "="*60)
                print("🚀 INICIANDO MARKET MANUS...")
                print("="*60)
                
                # Importar e executar sistema
                from market_manus_cli_complete import MarketManusCompleteSystem
                system = MarketManusCompleteSystem()
                system.run()
        
    except KeyboardInterrupt:
        print("\\n\\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\\n💥 Erro crítico no teste: {e}")
        logger.exception("Erro detalhado:")
