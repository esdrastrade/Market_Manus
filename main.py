#!/usr/bin/env python3
"""
MARKET MANUS - SISTEMA PRINCIPAL INTEGRADO
==========================================
Data: 30/09/2025
Versão: 2.0.0 - Completamente Integrado

Ponto de entrada do Market Manus.

Regras:
- A classe de CLI (MarketManusCompleteCLI) não aceita injeção de dependências no __init__.
- Ela se auto-inicializa (Data Provider, Strategy Manager, etc.).
- Portanto, o main não deve passar kwargs ao instanciá-la.
"""

import sys
import traceback
from pathlib import Path

# -----------------------------------------------------------------------------
# PATHS
# -----------------------------------------------------------------------------
project_root = Path(__file__).parent
market_manus_path = project_root / "market_manus"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(market_manus_path))

# -----------------------------------------------------------------------------
# BANNER
# -----------------------------------------------------------------------------
def print_banner():
    print("🚀 MARKET MANUS - SISTEMA INTEGRADO")
    from datetime import datetime
    print(f"Data: {datetime.now().strftime('%d/%m/%Y')} | Versão: 2.0.0")
    print("=" * 60)

# -----------------------------------------------------------------------------
# IMPORTS DINÂMICOS
# -----------------------------------------------------------------------------
def import_modules():
    modules = {}

    # CLI
    try:
        from market_manus.cli.market_manus_cli_2025_09_30 import MarketManusCompleteCLI
        modules["cli_class"] = MarketManusCompleteCLI
        print("✅ CLI Principal carregado: market_manus_cli_2025_09_30.py")
    except Exception as e:
        print(f"⚠️ Erro ao importar CLI principal: {e}")
        modules["cli_class"] = None
        print("❌ Nenhum CLI encontrado!")

    # Strategy Manager
    try:
        from market_manus.strategies.strategy_manager_integrated import StrategyManagerIntegrated
        modules["strategy_manager_class"] = StrategyManagerIntegrated
        print("✅ Strategy Manager carregado: strategy_manager_integrated.py")
    except Exception as e:
        print(f"⚠️ Erro ao importar Strategy Manager: {e}")
        modules["strategy_manager_class"] = None
        print("❌ Nenhum Strategy Manager encontrado!")

    # Data Provider
    try:
        from market_manus.data_providers.bybit_real_data_provider_fixed import BybitRealDataProvider
        modules["data_provider_class"] = BybitRealDataProvider
        print("✅ Data Provider carregado: bybit_real_data_provider_fixed.py")
    except Exception as e:
        print(f"⚠️ Erro ao importar Data Provider: {e}")
        modules["data_provider_class"] = None
        print("❌ Nenhum Data Provider encontrado!")

    # Confluence Mode
    try:
        from market_manus.confluence_mode.confluence_mode_module import ConfluenceModeModule
        modules["confluence_mode_class"] = ConfluenceModeModule
        print("✅ Confluence Mode carregado: confluence_mode_module.py")
    except Exception as e:
        print(f"⚠️ Erro ao importar Confluence Mode: {e}")
        modules["confluence_mode_class"] = None

    # Strategy Lab
    try:
        from market_manus.strategy_lab.strategy_lab_professional import StrategyLabProfessional
        modules["strategy_lab_class"] = StrategyLabProfessional
        print("✅ Strategy Lab carregado: strategy_lab_professional.py")
    except Exception as e:
        print(f"⚠️ Erro ao importar Strategy Lab: {e}")
        modules["strategy_lab_class"] = None

    # Capital Manager
    try:
        from market_manus.core.capital_manager import CapitalManager
        modules["capital_manager_class"] = CapitalManager
        print("✅ Capital Manager carregado: capital_manager.py")
    except Exception as e:
        print(f"⚠️ Erro ao importar Capital Manager: {e}")
        modules["capital_manager_class"] = None

    return modules

# -----------------------------------------------------------------------------
# INSTÂNCIAS PARA DIAGNÓSTICO / FALLBACK
# -----------------------------------------------------------------------------
def initialize_system(modules):
    components = {}

    # Data Provider
    if modules.get("data_provider_class"):
        try:
            dp = modules["data_provider_class"]()
            components["data_provider"] = dp
            print("✅ Data Provider inicializado")
        except Exception as e:
            print(f"⚠️ Erro ao inicializar Data Provider: {e}")
            components["data_provider"] = None
    else:
        components["data_provider"] = None

    # Capital Manager
    if modules.get("capital_manager_class"):
        try:
            cm = modules["capital_manager_class"]()
            components["capital_manager"] = cm
            print("✅ Capital Manager inicializado")
        except Exception as e:
            print(f"⚠️ Erro ao inicializar Capital Manager: {e}")
            components["capital_manager"] = None
    else:
        components["capital_manager"] = None

    # Strategy Manager (para listar estratégias no fallback)
    if modules.get("strategy_manager_class"):
        try:
            sm = modules["strategy_manager_class"]()
            components["strategy_manager"] = sm
            print("✅ Strategy Manager inicializado")
        except Exception as e:
            print(f"⚠️ Erro ao inicializar Strategy Manager: {e}")
            components["strategy_manager"] = None
    else:
        components["strategy_manager"] = None

    # Confluence Mode (opcional – útil no fallback para status)
    if modules.get("confluence_mode_class"):
        try:
            cmode = modules["confluence_mode_class"](
                data_provider=components.get("data_provider"),
                capital_manager=components.get("capital_manager"),
                strategy_manager=components.get("strategy_manager"),
            )
            components["confluence_mode"] = cmode
            print("✅ Confluence Mode inicializado")
        except Exception as e:
            print(f"⚠️ Erro ao inicializar Confluence Mode: {e}")
            components["confluence_mode"] = None
    else:
        components["confluence_mode"] = None

    # Strategy Lab (opcional – útil no fallback para status)
    if modules.get("strategy_lab_class"):
        try:
            slab = modules["strategy_lab_class"](
                data_provider=components.get("data_provider"),
                capital_manager=components.get("capital_manager"),
                strategy_manager=components.get("strategy_manager"),
            )
            components["strategy_lab"] = slab
            print("✅ Strategy Lab inicializado")
        except Exception as e:
            print(f"⚠️ Erro ao inicializar Strategy Lab: {e}")
            components["strategy_lab"] = None
    else:
        components["strategy_lab"] = None

    return components

# -----------------------------------------------------------------------------
# EXECUÇÃO DO CLI
# -----------------------------------------------------------------------------
def run_cli(modules, components):
    """
    Importante: MarketManusCompleteCLI NÃO aceita kwargs no __init__.
    Portanto, instancie sem argumentos.
    """
    cli_class = modules.get("cli_class")

    if cli_class:
        try:
            cli = cli_class()            # <<< sem kwargs
            print("\n🎯 INICIANDO INTERFACE CLI.")
            print("=" * 50)
            cli.run()
            return True
        except Exception as e:
            print(f"❌ Erro ao executar CLI principal: {e}")
            print("➡️  Usando fallback básico.")
            return _fallback_basic_cli(components)
    else:
        print("⚠️ CLI principal não disponível. Executando CLI básico...")
        return _fallback_basic_cli(components)

# -----------------------------------------------------------------------------
# FALLBACK BÁSICO
# -----------------------------------------------------------------------------
def _fallback_basic_cli(components):
    while True:
        print("\n" + "=" * 60)
        print("🎯 MARKET MANUS - CLI BÁSICO")
        print("=" * 60)
        print("📊 OPÇÕES DISPONÍVEIS:")
        print("   1️⃣  Status do Sistema")
        print("   2️⃣  Listar Estratégias")
        print("   3️⃣  Informações de Capital")
        print("   4️⃣  Teste de Conectividade")
        print("   0️⃣  Sair")
        print("-" * 60)

        try:
            choice = input("🔢 Escolha uma opção: ").strip()

            if choice == "0":
                print("\n👋 Encerrando Market Manus...")
                break
            elif choice == "1":
                show_system_status(components)
            elif choice == "2":
                list_strategies(components)
            elif choice == "3":
                show_capital_info(components)
            elif choice == "4":
                test_connectivity(components)
            else:
                print("❌ Opção inválida!")
        except KeyboardInterrupt:
            print("\n\n👋 Encerrando Market Manus...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

    return True

# -----------------------------------------------------------------------------
# AUXILIARES DO FALLBACK
# -----------------------------------------------------------------------------
def show_system_status(components):
    print("\n📊 STATUS DO SISTEMA")
    print("=" * 40)
    for name, component in components.items():
        status = "✅ Ativo" if component else "❌ Inativo"
        print(f"   {name.replace('_', ' ').title()}: {status}")

def list_strategies(components):
    print("\n📈 ESTRATÉGIAS DISPONÍVEIS")
    print("=" * 40)
    sm = components.get("strategy_manager")
    if not sm:
        print("❌ Strategy Manager não disponível")
        return
    try:
        strategies = sm.get_available_strategies()
        if not strategies:
            print("⚠️ Nenhuma estratégia registrada.")
            return
        for i, st in enumerate(strategies, 1):
            print(f"   {i}️⃣  {st}")
    except Exception as e:
        print(f"❌ Erro ao listar estratégias: {e}")

def show_capital_info(components):
    print("\n💰 INFORMAÇÕES DE CAPITAL")
    print("=" * 40)
    cm = components.get("capital_manager")
    if not cm:
        print("❌ Capital Manager não disponível")
        return
    try:
        info = cm.get_summary() if hasattr(cm, "get_summary") else {}
        if info:
            for k, v in info.items():
                print(f"   {k}: {v}")
        else:
            print("ℹ️  Capital Manager ativo (sem resumo detalhado).")
    except Exception as e:
        print(f"❌ Erro ao obter informações de capital: {e}")

def test_connectivity(components):
    print("\n🔌 TESTE DE CONECTIVIDADE")
    print("=" * 40)
    dp = components.get("data_provider")
    if not dp:
        print("❌ Data Provider não disponível")
        return
    try:
        ok = False
        if hasattr(dp, "ping"):
            ok = dp.ping()
        elif hasattr(dp, "get_current_price"):
            _ = dp.get_current_price("BTCUSDT")
            ok = True
        print("✅ Conectividade OK" if ok else "⚠️ Não foi possível validar conectividade")
    except Exception as e:
        print(f"❌ Erro ao testar conectividade: {e}")

# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
def main():
    print_banner()
    print("\n📦 CARREGANDO MÓDULOS...")
    modules = import_modules()

    print("\n⚙️ INICIALIZANDO COMPONENTES...")
    components = initialize_system(modules)

    print("\n🚀 INICIALIZANDO MARKET MANUS...")
    print("=" * 50)
    run_cli(modules, components)

if __name__ == "__main__":
    main()
