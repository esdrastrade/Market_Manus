#!/usr/bin/env python3

import os
import sys
from pathlib import Path

def main():
    """Ponto de entrada principal do Market Manus"""
    
    print("🏭 MARKET MANUS - SISTEMA DE TRADING AUTOMATIZADO")
    print("=" * 60)
    print("💰 Renda passiva automática e escalável")
    print("🤖 IA integrada com multi-armed bandit")
    print("📈 Estratégias validadas automaticamente")
    print("🔄 Backtesting com dados reais")
    print("🔬 Strategy Lab Professional integrado")
    print("💼 Capital Management com proteção de drawdown")
    print("=" * 60)
    
    # Verificar diretório do projeto
    project_dir = Path(__file__).parent.absolute()
    print(f"📁 Diretório do projeto: {project_dir}")
    
    try:
        # Tentar importar o CLI mais recente (versão 21/09/25 16:30)
        print("🔄 Carregando Market Manus CLI...")
        
        # Adicionar diretório do projeto ao path
        sys.path.insert(0, str(project_dir))
        
        # Verificar se a estrutura existe
        cli_file = project_dir / "market_manus" / "cli" / "market_manus_cli_complete_final.py"
        
        if not cli_file.exists():
            print(f"❌ Arquivo CLI não encontrado: {cli_file}")
            print("\n🔧 INSTRUÇÕES PARA CORRIGIR:")
            print("1. Copie o conteúdo de market_manus_cli_21_09_25_1630.py")
            print("2. Cole em market_manus/cli/market_manus_cli_complete_final.py")
            print("3. Execute novamente: python main.py")
            return
        
        # Importar e executar CLI
        from market_manus.cli.market_manus_cli_complete_final import MarketManusCompleteCLI
        
        print("✅ CLI integrado carregado com sucesso!")
        
        # Verificar se Strategy Lab Professional está disponível
        try:
            cli_instance = MarketManusCompleteCLI()
            if hasattr(cli_instance, 'professional_strategy_lab'):
                print("✅ Strategy Lab Professional ativo!")
                print("✅ Historical Data Test com dados reais da API!")
                print("✅ Capital Management integrado!")
            else:
                print("⚠️  Strategy Lab básico - atualize para versão Professional")
        except Exception as e:
            print(f"⚠️  Aviso na inicialização: {e}")
        
        print("🚀 Iniciando Market Manus...")
        print()
        
        # Executar CLI principal
        cli = MarketManusCompleteCLI()
        cli.run()
        
    except ImportError as e:
        print(f"❌ Erro ao importar CLI principal: {e}")
        print("\n🔍 DIAGNÓSTICO DO PROBLEMA:")
        print("-" * 40)
        
        # Verificar estrutura do projeto
        market_manus_dir = project_dir / "market_manus"
        cli_dir = market_manus_dir / "cli"
        
        if not market_manus_dir.exists():
            print("❌ Diretório market_manus/ não encontrado")
        elif not cli_dir.exists():
            print("❌ Diretório market_manus/cli/ não encontrado")
        elif not cli_file.exists():
            print("❌ Arquivo market_manus_cli_complete_final.py não encontrado")
        else:
            print("✅ Estrutura do projeto parece correta")
            print("❌ Problema pode ser dependências faltando")
        
        print("\n💡 SOLUÇÕES POSSÍVEIS:")
        print("1. Instalar dependências:")
        print("   pip install -r requirements.txt")
        print()
        print("2. Verificar se está no diretório correto:")
        print(f"   Diretório atual: {project_dir}")
        print()
        print("3. Atualizar CLI para versão mais recente:")
        print("   Copie market_manus_cli_21_09_25_1630.py para market_manus/cli/market_manus_cli_complete_final.py")
        print()
        print("4. Verificar permissões de arquivo")
        
        print("\n🛠️ PARA OBTER AJUDA:")
        print("- Verifique o README.md")
        print("- Consulte docs/troubleshooting.md")
        print("- Execute: python -c 'import sys; print(sys.path)'")
        
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        print("🔧 Verifique se todas as dependências estão instaladas")
        print("📖 Consulte a documentação para mais informações")
        
        # Debug info
        print(f"\n🔍 INFORMAÇÕES DE DEBUG:")
        print(f"Python: {sys.version}")
        print(f"Diretório: {project_dir}")
        print(f"Path: {sys.path[:3]}...")  # Primeiros 3 paths


if __name__ == "__main__":
    main()
