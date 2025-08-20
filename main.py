#!/usr/bin/env python3
"""
MARKET MANUS - Strategy Factory
Ponto de entrada principal do sistema
"""

import sys
import os

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Função principal do sistema"""
    try:
        from cli.strategy_factory_cli_v2 import StrategyFactoryCLIV2
        
        print("🏭 Iniciando Market Manus Strategy Factory...")
        cli = StrategyFactoryCLIV2()
        cli.run()
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("💡 Certifique-se de que todos os módulos estão instalados")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Programa interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
