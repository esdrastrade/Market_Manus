#!/usr/bin/env python3
"""
MARKET MANUS - MAIN INTEGRADO COMPLETO
Sistema de Trading com TODAS as estratégias integradas
"""

import sys
import os
from pathlib import Path

# Adicionar paths necessários
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "market_manus"))
sys.path.insert(0, str(current_dir / "market_manus" / "cli"))
sys.path.insert(0, str(current_dir / "market_manus" / "strategies"))
sys.path.insert(0, str(current_dir / "market_manus" / "confluence_mode"))
sys.path.insert(0, str(current_dir / "market_manus" / "strategy_lab"))

def main():
    """
    Ponto de entrada principal do Market Manus
    Integra TODAS as estratégias e módulos do usuário
    """
    
    print("🚀 MARKET MANUS - Sistema de Trading Integrado Completo")
    print("=" * 70)
    
    # Tentar importar o CLI principal do usuário
    try:
        from market_manus_cli import MarketManusCompleteSystem
        
        print("✅ CLI principal carregado com sucesso!")
        print("📊 Funcionalidades: Strategy Lab | Confluence Mode | Capital Management")
        print("🔌 Dados: Bybit API Real | Estratégias Integradas | Relatórios")
        print("=" * 70)
        
        # Executar sistema
        system = MarketManusCompleteSystem()
        system.run()
        
    except ImportError as e:
        print(f"⚠️ Erro de importação do CLI principal: {e}")
        print("\\n🔄 Tentando sistema alternativo...")
        
        # Fallback para sistema alternativo
        try:
            from market_manus.cli.market_manus_cli import MarketManusCompleteSystem
            
            print("✅ Sistema alternativo carregado!")
            system = MarketManusCompleteSystem()
            system.run()
            
        except ImportError:
            print("❌ Sistema alternativo não disponível")
            print("\\n🔄 Tentando sistema básico integrado...")
            run_integrated_system()
    
    except Exception as e:
        print(f"💥 Erro crítico: {e}")
        print("\\n🛠️ Executando diagnóstico...")
        run_diagnostic()


def run_integrated_system():
    """
    Sistema básico integrado que funciona com as estratégias do usuário
    """
    print("\\n🚀 SISTEMA BÁSICO INTEGRADO")
    print("=" * 50)
    
    try:
        # Importar componentes necessários
        from strategy_manager_enhanced import StrategyManager
        from confluence_mode_module import ConfluenceModeManager
        from strategy_lab_professional import StrategyLabProfessional
        
        print("✅ Componentes carregados com sucesso!")
        
        # Inicializar sistema básico
        strategy_manager = StrategyManager()
        
        # Menu principal básico
        while True:
            print("\\n" + "="*60)
            print("🎛️ MARKET MANUS - MENU PRINCIPAL")
            print("="*60)
            print("🧪 LABORATÓRIO:")
            print("   1️⃣  Strategy Lab Professional")
            print("   2️⃣  Confluence Mode")
            print("\\n💼 GESTÃO:")
            print("   3️⃣  Listar Estratégias")
            print("   4️⃣  Status do Sistema")
            print("\\n   0️⃣  Sair")
            print("-"*60)
            
            choice = input("\\n🔢 Escolha uma opção: ").strip()
            
            if choice == "0":
                print("\\n👋 Obrigado por usar o Market Manus!")
                break
            elif choice == "1":
                run_strategy_lab(strategy_manager)
            elif choice == "2":
                run_confluence_mode(strategy_manager)
            elif choice == "3":
                list_strategies(strategy_manager)
            elif choice == "4":
                show_system_status()
            else:
                print("❌ Opção inválida! Tente novamente.")
    
    except Exception as e:
        print(f"❌ Erro no sistema integrado: {e}")
        print("\\n🛠️ Executando diagnóstico...")
        run_diagnostic()


def run_strategy_lab(strategy_manager):
    """
    Executa o Strategy Lab Professional
    """
    print("\\n🧪 STRATEGY LAB PROFESSIONAL")
    print("="*50)
    
    try:
        # Listar estratégias disponíveis
        strategies = strategy_manager.get_available_strategies()
        
        print(f"📊 Estratégias disponíveis: {len(strategies)}")
        for i, strategy in enumerate(strategies, 1):
            info = strategy_manager.get_strategy_info(strategy)
            print(f"   {i}️⃣  {info.get('name', strategy)}")
            print(f"       Tipo: {info.get('type', 'N/A')} | Risco: {info.get('risk_level', 'N/A')}")
        
        print("\\n🔧 OPÇÕES:")
        print("   T️⃣  Testar Estratégia Individual")
        print("   C️⃣  Comparar Estratégias")
        print("   0️⃣  Voltar")
        
        choice = input("\\n🔢 Escolha uma opção: ").strip().lower()
        
        if choice == "t":
            test_individual_strategy(strategy_manager, strategies)
        elif choice == "c":
            compare_strategies(strategy_manager, strategies)
        elif choice == "0":
            return
        else:
            print("❌ Opção inválida!")
    
    except Exception as e:
        print(f"❌ Erro no Strategy Lab: {e}")


def run_confluence_mode(strategy_manager):
    """
    Executa o Confluence Mode
    """
    print("\\n🎯 CONFLUENCE MODE")
    print("="*50)
    
    try:
        strategies = strategy_manager.get_available_strategies()
        
        print(f"📊 Estratégias disponíveis para confluência: {len(strategies)}")
        
        # Seleção múltipla de estratégias
        selected = []
        print("\\n📋 Selecione estratégias (digite números separados por vírgula):")
        
        for i, strategy in enumerate(strategies, 1):
            info = strategy_manager.get_strategy_info(strategy)
            print(f"   {i}️⃣  {info.get('name', strategy)}")
        
        selection = input("\\n🔢 Estratégias (ex: 1,2,3): ").strip()
        
        if selection:
            indices = [int(x.strip()) - 1 for x in selection.split(",") if x.strip().isdigit()]
            selected = [strategies[i] for i in indices if 0 <= i < len(strategies)]
        
        if len(selected) >= 2:
            print(f"\\n✅ {len(selected)} estratégias selecionadas para confluência:")
            for strategy in selected:
                info = strategy_manager.get_strategy_info(strategy)
                print(f"   📊 {info.get('name', strategy)}")
            
            print("\\n🎯 Modos de confluência disponíveis:")
            print("   1️⃣  UNANIMOUS - Todas devem concordar")
            print("   2️⃣  MAJORITY - Maioria deve concordar")
            print("   3️⃣  ANY - Qualquer uma pode gerar sinal")
            
            mode_choice = input("\\n🔢 Escolha o modo: ").strip()
            modes = {"1": "UNANIMOUS", "2": "MAJORITY", "3": "ANY"}
            mode = modes.get(mode_choice, "MAJORITY")
            
            print(f"\\n✅ Modo selecionado: {mode}")
            print("\\n🔄 Executando análise de confluência...")
            print("⚠️ Funcionalidade em desenvolvimento - dados simulados")
            
            # Simular resultado
            print("\\n📊 RESULTADO DA CONFLUÊNCIA:")
            print(f"   Estratégias: {len(selected)}")
            print(f"   Modo: {mode}")
            print(f"   Sinais gerados: 12")
            print(f"   Confluência detectada: 8 vezes")
            print(f"   Taxa de confluência: 66.7%")
        else:
            print("❌ Selecione pelo menos 2 estratégias para confluência!")
    
    except Exception as e:
        print(f"❌ Erro no Confluence Mode: {e}")


def test_individual_strategy(strategy_manager, strategies):
    """
    Testa uma estratégia individual
    """
    print("\\n🧪 TESTE DE ESTRATÉGIA INDIVIDUAL")
    print("="*50)
    
    try:
        print("📊 Selecione uma estratégia:")
        for i, strategy in enumerate(strategies, 1):
            info = strategy_manager.get_strategy_info(strategy)
            print(f"   {i}️⃣  {info.get('name', strategy)}")
        
        choice = input("\\n🔢 Escolha uma estratégia: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(strategies):
            selected_strategy = strategies[int(choice) - 1]
            info = strategy_manager.get_strategy_info(selected_strategy)
            
            print(f"\\n✅ Estratégia selecionada: {info.get('name', selected_strategy)}")
            print(f"   Tipo: {info.get('type', 'N/A')}")
            print(f"   Risco: {info.get('risk_level', 'N/A')}")
            print(f"   Timeframes: {', '.join(info.get('timeframes', ['N/A']))}")
            
            print("\\n🔄 Executando teste...")
            print("⚠️ Funcionalidade em desenvolvimento - dados simulados")
            
            # Simular resultado
            print("\\n📊 RESULTADO DO TESTE:")
            print(f"   Capital inicial: $10,000.00")
            print(f"   Capital final: $10,847.50")
            print(f"   ROI: +8.48%")
            print(f"   Trades: 23")
            print(f"   Win rate: 65.2%")
            print(f"   Drawdown máximo: 12.3%")
        else:
            print("❌ Seleção inválida!")
    
    except Exception as e:
        print(f"❌ Erro no teste individual: {e}")


def compare_strategies(strategy_manager, strategies):
    """
    Compara múltiplas estratégias
    """
    print("\\n📊 COMPARAÇÃO DE ESTRATÉGIAS")
    print("="*50)
    
    try:
        print("📋 Selecione estratégias para comparar (digite números separados por vírgula):")
        
        for i, strategy in enumerate(strategies, 1):
            info = strategy_manager.get_strategy_info(strategy)
            print(f"   {i}️⃣  {info.get('name', strategy)}")
        
        selection = input("\\n🔢 Estratégias (ex: 1,2,3): ").strip()
        
        if selection:
            indices = [int(x.strip()) - 1 for x in selection.split(",") if x.strip().isdigit()]
            selected = [strategies[i] for i in indices if 0 <= i < len(strategies)]
            
            if len(selected) >= 2:
                print(f"\\n✅ Comparando {len(selected)} estratégias:")
                
                print("\\n📊 RESULTADOS DA COMPARAÇÃO:")
                print("-" * 60)
                print(f"{'Estratégia':<25} {'ROI':<10} {'Trades':<8} {'Win Rate':<10}")
                print("-" * 60)
                
                # Simular resultados
                import random
                for strategy in selected:
                    info = strategy_manager.get_strategy_info(strategy)
                    name = info.get('name', strategy)[:24]
                    roi = f"+{random.uniform(5, 15):.1f}%"
                    trades = random.randint(15, 35)
                    win_rate = f"{random.uniform(55, 75):.1f}%"
                    
                    print(f"{name:<25} {roi:<10} {trades:<8} {win_rate:<10}")
                
                print("-" * 60)
                print("⚠️ Dados simulados - funcionalidade em desenvolvimento")
            else:
                print("❌ Selecione pelo menos 2 estratégias para comparar!")
        else:
            print("❌ Nenhuma estratégia selecionada!")
    
    except Exception as e:
        print(f"❌ Erro na comparação: {e}")


def list_strategies(strategy_manager):
    """
    Lista todas as estratégias disponíveis
    """
    print("\\n📊 ESTRATÉGIAS DISPONÍVEIS")
    print("="*50)
    
    try:
        strategies = strategy_manager.get_available_strategies()
        
        print(f"Total de estratégias: {len(strategies)}")
        print()
        
        for i, strategy in enumerate(strategies, 1):
            info = strategy_manager.get_strategy_info(strategy)
            
            print(f"{i}️⃣  📊 {info.get('name', strategy)}")
            print(f"    Tipo: {info.get('type', 'N/A')}")
            print(f"    Risco: {info.get('risk_level', 'N/A')}")
            print(f"    Timeframes: {', '.join(info.get('timeframes', ['N/A']))}")
            print(f"    Descrição: {info.get('description', 'N/A')}")
            print()
    
    except Exception as e:
        print(f"❌ Erro ao listar estratégias: {e}")


def show_system_status():
    """
    Mostra o status do sistema
    """
    print("\\n📊 STATUS DO SISTEMA")
    print("="*50)
    
    try:
        print("✅ Sistema: Market Manus Integrado")
        print("✅ Versão: 2.0 - Integração Completa")
        print("✅ Python:", sys.version.split()[0])
        
        # Verificar módulos
        modules = [
            'strategy_manager_enhanced',
            'confluence_mode_module', 
            'strategy_lab_professional',
            'base_strategy',
            'rsi_mean_reversion_strategy',
            'ema_crossover_strategy',
            'bollinger_breakout_strategy',
            'macd_strategy',
            'stochastic_strategy',
            'adx_strategy',
            'fibonacci_strategy'
        ]
        
        print("\\n📦 Módulos:")
        for module in modules:
            try:
                __import__(module)
                print(f"   ✅ {module}")
            except ImportError:
                print(f"   ❌ {module}")
        
        # Verificar diretórios
        print("\\n📁 Estrutura:")
        dirs = ['logs', 'reports', 'data', 'market_manus/strategies']
        for dir_name in dirs:
            if Path(dir_name).exists():
                print(f"   ✅ {dir_name}/")
            else:
                print(f"   ❌ {dir_name}/")
        
        print("\\n🔌 Conectividade:")
        print("   ⚠️ Bybit API: Não testado (configure credenciais)")
        
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")


def run_diagnostic():
    """
    Executa diagnóstico completo do sistema
    """
    print("\\n🔍 DIAGNÓSTICO DO SISTEMA")
    print("=" * 50)
    
    # Verificar Python
    print(f"🐍 Python: {sys.version}")
    
    # Verificar dependências básicas
    required_packages = ['pandas', 'numpy', 'requests']
    
    print("\\n📦 Dependências:")
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - Execute: pip install {package}")
    
    # Verificar estrutura de arquivos
    print("\\n📁 Estrutura do Projeto:")
    required_files = [
        'market_manus/strategies/strategy_manager_enhanced.py',
        'market_manus/confluence_mode/confluence_mode_module.py',
        'market_manus/strategy_lab/strategy_lab_professional.py',
        'market_manus/cli/market_manus_cli.py'
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
    
    # Verificar estratégias
    print("\\n📊 Estratégias:")
    strategy_files = [
        'market_manus/strategies/base_strategy.py',
        'market_manus/strategies/rsi_mean_reversion_strategy.py',
        'market_manus/strategies/ema_crossover_strategy.py',
        'market_manus/strategies/bollinger_breakout_strategy.py',
        'market_manus/strategies/macd_strategy.py',
        'market_manus/strategies/stochastic_strategy.py',
        'market_manus/strategies/adx_strategy.py',
        'market_manus/strategies/fibonacci_strategy.py'
    ]
    
    for file_path in strategy_files:
        if Path(file_path).exists():
            print(f"   ✅ {Path(file_path).name}")
        else:
            print(f"   ❌ {Path(file_path).name}")
    
    print("\\n✅ Diagnóstico concluído!")
    input("\\n📖 Pressione ENTER para continuar...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\\n\\n⚠️ Sistema interrompido pelo usuário")
    except Exception as e:
        print(f"\\n💥 Erro fatal: {e}")
        print("Verifique os logs para mais detalhes")
