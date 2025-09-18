#!/usr/bin/env python3
"""
Market Manus - Ponto de Entrada Principal
Sistema de Trading Automatizado para Criptoativos
"""

import sys
import os
from pathlib import Path

# Adicionar src ao path para imports
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def main():
    """Funcao principal"""
    try:
        # Tentar importar CLI principal
        from market_manus.cli.market_manus_cli_complete_final import main as cli_main
        
        cli_main()
        
        except ImportError:
        # Fallback para CLI existente
        try:
            from src.cli.market_manus_cli_complete_final import main as fallback_main
            fallback_main()
        except ImportError:
            print("Erro: Nao foi possivel encontrar o CLI principal")
            print("Verifique se a estrutura do projeto esta correta")
            sys.exit(1)

if __name__ == "__main__":
    main()
