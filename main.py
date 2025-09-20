#!/usr/bin/env python3
"""
Market Manus - Sistema de Trading Automatizado para Criptoativos
Ponto de Entrada Principal

Autor: Esdras
Versão: 2.0
Data: Janeiro 2025
"""

import sys
import os
from pathlib import Path

def main():
    """
    Função principal do Market Manus
    Carrega e executa o CLI principal do sistema
    """
    
    # Banner de inicialização
    print("🏭 MARKET MANUS - SISTEMA DE TRADING AUTOMATIZADO")
    print("=" * 60)
    print("💰 Renda passiva automática e escalável")
    print("🤖 IA integrada com multi-armed bandit")
    print("📈 Estratégias validadas automaticamente")
    print("🔄 Backtesting com dados reais")
    print("=" * 60)
    print()
    
    # Configurar path do projeto
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    try:
        # Importar CLI principal da estrutura correta
        print("🔄 Carregando Market Manus CLI...")
        
        # CORREÇÃO: Importar a classe MarketManusCompleteCLI em vez da função main
        from market_manus.cli.market_manus_cli_complete_final import MarketManusCompleteCLI
        
        print("✅ CLI carregado com sucesso!")
        print("🚀 Iniciando sistema...")
        print()
        
        # Criar instância e executar CLI principal
        cli = MarketManusCompleteCLI()
        cli.run()
        
    except ImportError as e:
        print(f"❌ Erro ao importar CLI principal: {e}")
        print()
        print("🔍 DIAGNÓSTICO DO PROBLEMA:")
        print("-" * 40)
        
        # Verificar estrutura do projeto
        cli_path = project_root / "market_manus" / "cli" / "market_manus_cli_complete_final.py"
        market_manus_path = project_root / "market_manus"
        
        if not market_manus_path.exists():
            print("❌ Pasta 'market_manus/' não encontrada")
            print("📁 Estrutura esperada:")
            print("   scalping-trading-system/")
            print("   ├── main.py")
            print("   └── market_manus/")
            print("       ├── cli/")
            print("       ├── core/")
            print("       ├── strategies/")
            print("       └── agents/")
            
        elif not cli_path.exists():
            print("❌ Arquivo CLI não encontrado")
            print(f"📄 Esperado em: {cli_path}")
            print("🔍 Arquivos encontrados em market_manus/cli/:")
            cli_dir = project_root / "market_manus" / "cli"
            if cli_dir.exists():
                for file in cli_dir.glob("*.py"):
                    print(f"   - {file.name}")
            else:
                print("   (pasta cli/ não existe)")
                
        else:
            print("✅ Estrutura do projeto parece correta")
            print("❌ Problema pode ser dependências faltando")
            print()
            print("💡 SOLUÇÕES POSSÍVEIS:")
            print("1. Instalar dependências:")
            print("   pip install -r requirements.txt")
            print()
            print("2. Verificar se está no diretório correto:")
            print(f"   Diretório atual: {project_root}")
            print()
            print("3. Verificar permissões de arquivo")
            print("4. Verificar se o arquivo CLI tem a classe MarketManusCompleteCLI")
        
        print()
        print("🛠️ PARA OBTER AJUDA:")
        print("- Verifique o README.md")
        print("- Consulte docs/troubleshooting.md")
        print("- Execute: python -c 'import sys; print(sys.path)'")
        
        sys.exit(1)
        
    except KeyboardInterrupt:
        print()
        print("⏹️ Market Manus interrompido pelo usuário")
        print("👋 Até logo!")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        print("🔧 Entre em contato com o suporte se o problema persistir")
        print(f"📍 Erro em: {type(e).__name__}")
        sys.exit(1)

if __name__ == "__main__":
    main()
