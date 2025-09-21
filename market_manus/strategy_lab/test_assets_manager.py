#!/usr/bin/env python3
"""
Teste simples do Assets Manager
"""

import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.getcwd())

try:
    from market_manus.strategy_lab.assets_manager import AssetManager
    
    print("🧪 TESTANDO ASSETS MANAGER")
    print("=" * 40)
    
    # Inicializar manager
    manager = AssetManager(testnet=True)
    print("✅ AssetManager inicializado")
    
    # Testar conexão
    print("🔄 Testando conexão com Bybit...")
    prices = manager.update_all_prices()
    print(f"✅ Preços obtidos para {len(prices)} ativos")
    
    # Mostrar alguns preços
    print("\n📊 PREÇOS ATUAIS:")
    count = 0
    for symbol, data in prices.items():
        if count < 5:  # Mostrar apenas 5 primeiros
            price = data['price']
            change = data['change_24h']
            emoji = "🟢" if change >= 0 else "🔴"
            print(f"{emoji} {symbol}: ${price:,.4f} ({change:+.2f}%)")
            count += 1
    
    # Testar seleção automática
    print("\n🎯 TESTANDO SELEÇÃO AUTOMÁTICA:")
    selected = manager.parse_selection("1,2,4")  # BTC, ETH, SOL
    print(f"✅ Selecionados: {selected}")
    
    # Validar liquidez
    if selected:
        print("\n💧 VALIDANDO LIQUIDEZ:")
        liquidity = manager.validate_assets_liquidity(selected)
        for symbol, data in liquidity.items():
            status = "✅" if data['valid'] else "❌"
            volume = data['volume_24h_usdt']
            score = data['liquidity_score']
            print(f"{status} {symbol}: ${volume:,.0f} (Score: {score:.1f}/10)")
    
    print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
    
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    print("💡 Certifique-se de que o arquivo assets_manager.py está em market_manus/strategy_lab/")
except Exception as e:
    print(f"❌ Erro: {e}")

input("\n📖 Pressione ENTER para continuar...")
