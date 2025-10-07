"""
Menu UI para Combinações Recomendadas
Sistema visual para seleção de combinações pré-definidas
"""
from rich.table import Table
from rich.console import Console
from market_manus.confluence_mode.recommended_combinations import RecommendedCombinations


def display_recommended_combinations_menu(confluence_module):
    """
    Exibe menu completo de combinações recomendadas
    
    Args:
        confluence_module: Instância do ConfluenceModeModule
    
    Returns:
        bool: True se selecionou combinação, False para voltar
    """
    console = Console()
    all_combos = RecommendedCombinations.get_all_combinations()
    
    while True:
        print("\n" + "="*80)
        print("✨ COMBINAÇÕES RECOMENDADAS - WIN RATE 70-80%+")
        print("="*80)
        print("\n💡 Combinações profissionais otimizadas para diferentes condições de mercado")
        print(f"📊 Total: {RecommendedCombinations.get_total_combinations()} combinações disponíveis\n")
        
        print("🎯 CATEGORIAS:")
        print("   1️⃣  📈 Trending Markets (3 combinações)")
        print("   2️⃣  📊 Ranging Markets (3 combinações)")
        print("   3️⃣  ⚡ Scalping (3 combinações)")
        print("   4️⃣  🔄 Reversal (3 combinações)")
        print("   5️⃣  💥 Breakout (3 combinações)")
        print("   6️⃣  🏦 Institutional/Smart Money (3 combinações)")
        print("   7️⃣  💎 High Confidence Ultra (4 combinações)")
        print("\n   8️⃣  📋 Ver TODAS as 22 combinações")
        print("   0️⃣  Voltar")
        
        choice = input("\n🔢 Escolha uma categoria (0-8): ").strip()
        
        if choice == '0':
            return False
        elif choice == '1':
            if _select_from_category(confluence_module, all_combos['trending'], "TRENDING MARKETS", console):
                return True
        elif choice == '2':
            if _select_from_category(confluence_module, all_combos['ranging'], "RANGING MARKETS", console):
                return True
        elif choice == '3':
            if _select_from_category(confluence_module, all_combos['scalping'], "SCALPING", console):
                return True
        elif choice == '4':
            if _select_from_category(confluence_module, all_combos['reversal'], "REVERSAL", console):
                return True
        elif choice == '5':
            if _select_from_category(confluence_module, all_combos['breakout'], "BREAKOUT", console):
                return True
        elif choice == '6':
            if _select_from_category(confluence_module, all_combos['institutional'], "INSTITUTIONAL/SMART MONEY", console):
                return True
        elif choice == '7':
            if _select_from_category(confluence_module, all_combos['high_confidence'], "HIGH CONFIDENCE ULTRA", console):
                return True
        elif choice == '8':
            if _view_all_combinations(confluence_module, all_combos, console):
                return True
        else:
            print("❌ Opção inválida")
            input("\n📖 Pressione ENTER para continuar...")


def _select_from_category(confluence_module, combinations, category_name, console):
    """Exibe combinações de uma categoria específica"""
    while True:
        print("\n" + "="*80)
        print(f"📁 CATEGORIA: {category_name}")
        print("="*80)
        
        for combo in combinations:
            # Buscar win rate histórico se timeframe selecionado
            historical_info = ""
            if hasattr(confluence_module, 'selected_timeframe') and confluence_module.selected_timeframe:
                timeframe = confluence_module.selected_timeframe
                combo_id = str(combo['id'])
                win_rate_data = confluence_module.performance_analytics.get_combination_win_rate(
                    combo_id, timeframe, days=30
                )
                if win_rate_data['has_data']:
                    historical_info = f"\n       📈 Histórico (30d): {win_rate_data['win_rate']:.1f}% ({win_rate_data['total_trades']} trades)"
            
            print(f"\n   {combo['id']:2d}. {combo['name']}")
            print(f"       📊 Win Rate Target: {combo['target_win_rate']}{historical_info}")
            print(f"       ⏰ Timeframes: {', '.join(combo['best_timeframes'])}")
            print(f"       🎯 Modo: {combo['mode']}")
            print(f"       📝 {combo['description']}")
            print(f"       💡 {combo['why_it_works']}")
            print(f"       🔧 Estratégias ({len(combo['strategies'])}): {', '.join(combo['strategies'])}")
        
        print(f"\n   0️⃣  Voltar")
        
        choice = input(f"\n🔢 Digite o ID da combinação para aplicar (0 para voltar): ").strip()
        
        if choice == '0':
            return False
        
        try:
            combo_id = int(choice)
            selected_combo = None
            for combo in combinations:
                if combo['id'] == combo_id:
                    selected_combo = combo
                    break
            
            if selected_combo:
                _apply_combination(confluence_module, selected_combo)
                return True
            else:
                print("❌ ID inválido para esta categoria")
                input("\n📖 Pressione ENTER para continuar...")
        except ValueError:
            print("❌ Digite um número válido")
            input("\n📖 Pressione ENTER para continuar...")


def _view_all_combinations(confluence_module, all_combos, console):
    """Exibe TODAS as 22 combinações em formato compacto"""
    print("\n" + "="*80)
    print("📋 TODAS AS 22 COMBINAÇÕES RECOMENDADAS")
    print("="*80)
    
    for category_name, combos in all_combos.items():
        print(f"\n{'='*80}")
        print(f"📁 {category_name.upper()} ({len(combos)} combinações)")
        print(f"{'='*80}")
        
        for combo in combos:
            print(f"\n   {combo['id']:2d}. {combo['name']}")
            print(f"       📊 {combo['target_win_rate']} | ⏰ {', '.join(combo['best_timeframes'])} | 🎯 {combo['mode']}")
            print(f"       {combo['description']}")
    
    print(f"\n{'='*80}")
    choice = input(f"\n🔢 Digite o ID da combinação (1-22) para aplicar (0 para voltar): ").strip()
    
    if choice == '0':
        return False
    
    try:
        combo_id = int(choice)
        selected_combo = RecommendedCombinations.get_combination_by_id(combo_id)
        
        if selected_combo:
            _apply_combination(confluence_module, selected_combo)
            return True
        else:
            print(f"❌ ID {combo_id} não encontrado")
            input("\n📖 Pressione ENTER para continuar...")
            return False
    except ValueError:
        print("❌ Digite um número válido")
        input("\n📖 Pressione ENTER para continuar...")
        return False


def _apply_combination(confluence_module, combination):
    """Aplica uma combinação selecionada ao módulo de confluência"""
    print(f"\n{'='*80}")
    print(f"✅ APLICANDO COMBINAÇÃO: {combination['name']}")
    print(f"{'='*80}")
    
    # Aplicar estratégias
    confluence_module.selected_strategies = combination['strategies']
    
    # Aplicar modo de confluência
    confluence_module.selected_confluence_mode = combination['mode']
    
    # Armazenar combinação selecionada para tracking no repositório
    confluence_module.selected_combination = {
        'id': str(combination['id']),
        'name': combination['name']
    }
    
    print(f"\n✅ Estratégias configuradas ({len(combination['strategies'])}):")
    for strategy_key in combination['strategies']:
        if strategy_key in confluence_module.available_strategies:
            strategy = confluence_module.available_strategies[strategy_key]
            print(f"   {strategy['emoji']} {strategy['name']}")
    
    print(f"\n✅ Modo de confluência: {combination['mode']}")
    print(f"📊 Win Rate esperado: {combination['target_win_rate']}")
    print(f"⏰ Timeframes recomendados: {', '.join(combination['best_timeframes'])}")
    print(f"\n💡 {combination['why_it_works']}")
    
    input("\n📖 Pressione ENTER para continuar...")
