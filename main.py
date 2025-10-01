"""
Market Manus - Main Entry Point V6 Completo e Corrigido
Localização: main.py (raiz do projeto)
Data: 24/09/2025
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório do projeto ao sys.path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Importações do Market Manus
try:
    from market_manus.data_providers.binance_data_provider import BinanceDataProvider
    from market_manus.core.capital_manager import CapitalManager
    from market_manus.strategy_lab.STRATEGY_LAB_PROFESSIONAL_V6 import StrategyLabProfessionalV6
    from market_manus.confluence_mode.confluence_mode_module import ConfluenceModeModule
except ImportError as e:
    print(f"❌ Erro na importação: {e}")
    print("📁 Verifique se a estrutura de diretórios está correta:")
    print("   market_manus/strategy_lab/STRATEGY_LAB_PROFESSIONAL_V6.py")
    print("   market_manus/confluence_mode/confluence_mode_module.py")
    print("   market_manus/data_providers/binance_data_provider.py")
    print("   market_manus/core/capital_manager.py")
    sys.exit(1)

class MarketManusMain:
    """Classe principal do Market Manus"""
    
    def __init__(self):
        # Configurar APIs - Binance tem prioridade
        self.api_key = os.getenv("BINANCE_API_KEY", "")
        self.api_secret = os.getenv("BINANCE_API_SECRET", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        
        # Validar credenciais
        if not self.api_key or not self.api_secret:
            print("❌ Credenciais da API Binance não configuradas!")
            print("💡 Configure as variáveis de ambiente:")
            print("   BINANCE_API_KEY=sua_chave_aqui")
            print("   BINANCE_API_SECRET=seu_segredo_aqui")
            sys.exit(1)
        
        # Inicializar componentes
        self.data_provider = BinanceDataProvider(
            api_key=self.api_key,
            api_secret=self.api_secret,
            testnet=False
        )
        
        self.capital_manager = CapitalManager(
            initial_capital=10000.0,
            position_size_pct=0.02
        )
        
        self.strategy_lab = StrategyLabProfessionalV6(
            data_provider=self.data_provider,
            capital_manager=self.capital_manager
        )
        
        self.confluence_mode = ConfluenceModeModule(
            data_provider=self.data_provider,
            capital_manager=self.capital_manager
        )
        
        # Status de conectividade
        self.connectivity_status = self._test_connectivity()
    
    def _test_connectivity(self) -> bool:
        """Testa conectividade com a API Binance"""
        try:
            result = self.data_provider.test_connection()
            return result is True
        except Exception:
            return False
    
    def run(self):
        """Executa o sistema principal"""
        self._show_welcome()
        
        while True:
            self._show_main_menu()
            choice = input("\n🔢 Escolha uma opção (0-6): ").strip()
            
            if choice == '0':
                self._show_goodbye()
                break
            elif choice == '1':
                self._run_strategy_lab()
            elif choice == '2':
                self._run_confluence_mode()
            elif choice == '3':
                self._run_ai_assistant()
            elif choice == '4':
                self._show_capital_dashboard()
            elif choice == '5':
                self._show_connectivity_status()
            elif choice == '6':
                self._show_settings()
            else:
                print("❌ Opção inválida")
                input("\n📖 Pressione ENTER para continuar...")
    
    def _show_welcome(self):
        """Mostra tela de boas-vindas"""
        print("\n" + "=" * 80)
        print("     🏭 MARKET MANUS - SISTEMA DE TRADING AUTOMATIZADO V6.0")
        print("=" * 80)
        print("🎯 Sistema modular com Strategy Lab V6 e Confluence Mode")
        print("📊 8 estratégias: RSI, EMA, Bollinger, MACD, Stochastic, Williams %R, ADX, Fibonacci")
        print("📅 Seleção de período personalizado")
        print("💰 Capital management automático")
        print("🔗 Data Provider: Binance API")
        print("=" * 80)
        
        # Status inicial
        print(f"\n🔄 INICIALIZANDO SISTEMA...")
        print(f"✅ Data Provider: {'Conectado' if self.connectivity_status else 'Desconectado'}")
        print(f"✅ Capital Manager: Inicializado (${self.capital_manager.current_capital:.2f})")
        print(f"✅ Strategy Lab V6: Carregado (8 estratégias)")
        print(f"✅ Confluence Mode: Carregado")
        
        if self.openai_api_key:
            print(f"✅ OpenAI API: Configurada")
        else:
            print(f"⚠️ OpenAI API: Não configurada")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _show_main_menu(self):
        """Mostra o menu principal"""
        stats = self.capital_manager.get_stats()
        
        print("\n🎯 MARKET MANUS - MENU PRINCIPAL V6")
        print("=" * 60)
        
        # Resumo financeiro
        print(f"💰 RESUMO FINANCEIRO:")
        print(f"   💵 Capital atual: ${self.capital_manager.current_capital:.2f}")
        print(f"   📊 Position size: ${self.capital_manager.get_position_size():.2f}")
        print(f"   📈 P&L total: ${stats['total_pnl']:+.2f}")
        print(f"   🎯 Total trades: {stats['total_trades']} | Win Rate: {stats['win_rate']:.1f}%")
        
        # Status de conectividade
        connectivity_emoji = "🟢" if self.connectivity_status else "🔴"
        connectivity_text = "Online" if self.connectivity_status else "Offline"
        print(f"   🌐 Status API: {connectivity_emoji} {connectivity_text}")
        
        print(f"\n🎯 MÓDULOS PRINCIPAIS:")
        print("   1️⃣  Strategy Lab Professional V6 (8 estratégias)")
        print("   2️⃣  Confluence Mode (Sistema de confluência)")
        
        print(f"\n🤖 RECURSOS AVANÇADOS:")
        print("   3️⃣  Assistente IA (Semantic Kernel)")
        
        print(f"\n⚙️ CONFIGURAÇÕES:")
        print("   4️⃣  Capital Dashboard")
        print("   5️⃣  Connectivity Status")
        print("   6️⃣  Settings")
        
        print(f"\n   0️⃣  Sair do sistema")
    
    def _run_strategy_lab(self):
        """Executa o Strategy Lab Professional V6"""
        print("\n🔬 INICIANDO STRATEGY LAB PROFESSIONAL V6...")
        print("📊 8 estratégias disponíveis:")
        print("   • RSI Mean Reversion")
        print("   • EMA Crossover") 
        print("   • Bollinger Bands Breakout")
        print("   • MACD")
        print("   • Stochastic Oscillator")
        print("   • Williams %R")
        print("   • ADX")
        print("   • Fibonacci Retracement")
        
        try:
            self.strategy_lab.run_interactive_mode()
        except Exception as e:
            print(f"❌ Erro no Strategy Lab: {e}")
            input("\n📖 Pressione ENTER para continuar...")
    
    def _run_confluence_mode(self):
        """Executa o Confluence Mode"""
        print("\n🎯 INICIANDO CONFLUENCE MODE...")
        
        try:
            self.confluence_mode.run_interactive_mode()
        except Exception as e:
            print(f"❌ Erro no Confluence Mode: {e}")
            input("\n📖 Pressione ENTER para continuar...")
    
    def _run_ai_assistant(self):
        """Executa o Assistente IA"""
        print("\n🤖 ASSISTENTE IA - SEMANTIC KERNEL")
        print("=" * 50)
        print("🚧 Funcionalidade em desenvolvimento...")
        print("📊 Recursos planejados:")
        print("   • Comandos em linguagem natural")
        print("   • Integração com todas as 8 estratégias")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _show_capital_dashboard(self):
        """Mostra o dashboard de capital"""
        print("\n💰 CAPITAL DASHBOARD")
        print("=" * 50)
        
        stats = self.capital_manager.get_stats()
        
        print(f"📊 INFORMAÇÕES DO CAPITAL:")
        print(f"   💵 Capital inicial: ${self.capital_manager.initial_capital:.2f}")
        print(f"   💰 Capital atual: ${self.capital_manager.current_capital:.2f}")
        print(f"   📈 P&L total: ${stats['total_pnl']:+.2f}")
        print(f"   📊 Retorno total: {stats['total_return']:+.2f}%")
        print(f"   🎯 Total de trades: {stats['total_trades']}")
        print(f"   📊 Win rate: {stats['win_rate']:.1f}%")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _show_connectivity_status(self):
        """Mostra status de conectividade"""
        print("\n🌐 CONNECTIVITY STATUS")
        print("=" * 50)
        
        print("🔄 Testando conectividade...")
        
        # Testar Binance API
        binance_status = self._test_connectivity()
        binance_emoji = "🟢" if binance_status else "🔴"
        binance_text = "Conectado" if binance_status else "Desconectado"
        
        print(f"\n📊 BINANCE API:")
        print(f"   Status: {binance_emoji} {binance_text}")
        print(f"   Endpoint: {self.data_provider.base_url}")
        print(f"   API Key: {self.api_key[:10]}...")
        
        if binance_status:
            try:
                tickers = self.data_provider.get_tickers(category="spot")
                if tickers and 'list' in tickers:
                    print(f"   ✅ {len(tickers['list'])} pares disponíveis")
            except Exception:
                print(f"   ⚠️ Erro ao obter dados")
        
        # OpenAI API
        print(f"\n🤖 OPENAI API:")
        if self.openai_api_key:
            print(f"   Status: 🟡 Configurada")
            print(f"   API Key: {self.openai_api_key[:10]}...")
        else:
            print(f"   Status: ❌ Não configurada")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _show_settings(self):
        """Mostra configurações do sistema"""
        print("\n⚙️ SETTINGS - CONFIGURAÇÕES")
        print("=" * 50)
        
        print(f"🔧 CONFIGURAÇÕES ATUAIS:")
        print(f"   🌐 Binance Testnet: {'Sim' if self.data_provider.testnet else 'Não'}")
        print(f"   💰 Capital inicial: ${self.capital_manager.initial_capital:.2f}")
        print(f"   💼 Position size: {self.capital_manager.position_size_pct*100:.1f}%")
        print(f"   🤖 OpenAI API: {'Configurada' if self.openai_api_key else 'Não configurada'}")
        
        print(f"\n📁 ESTRUTURA:")
        print(f"   📂 Projeto: {project_root}")
        print(f"   📂 Strategy Lab: market_manus/strategy_lab/")
        print(f"   📂 Confluence Mode: market_manus/confluence_mode/")
        print(f"   📂 Data Providers: market_manus/data_providers/")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _show_goodbye(self):
        """Mostra mensagem de despedida"""
        print("\n" + "=" * 60)
        print("👋 OBRIGADO POR USAR O MARKET MANUS!")
        print("=" * 60)
        print("💰 Sistema de trading automatizado")
        print("📊 8 estratégias profissionais")
        print("🎯 Dados reais da API Binance")
        print("=" * 60)
        print("🚀 Até a próxima!")

def main():
    """Função principal"""
    try:
        app = MarketManusMain()
        app.run()
    except KeyboardInterrupt:
        print("\n\n⏹️ Sistema interrompido pelo usuário")
        print("👋 Obrigado por usar o Market Manus!")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
