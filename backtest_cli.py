#!/usr/bin/env python3
"""
Backtest CLI - Interface de Linha de Comando Interativa
Sistema de Backtesting para Linha de Produção

Uso:
    python backtest_cli.py

Funcionalidades:
- Interface interativa com perguntas inteligentes
- Validação de dados em tempo real
- Execução automatizada de backtesting
- Relatórios detalhados
- Sugestões baseadas em resultados
"""

import os
import sys
import json
import asyncio
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

# Adicionar diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agents.backtesting_agent_v5 import BacktestingAgentV5
except ImportError:
    print("❌ Erro: Não foi possível importar BacktestingAgentV5")
    print("   Verifique se o arquivo agents/backtesting_agent_v5.py existe")
    sys.exit(1)

class BacktestCLI:
    """Interface de linha de comando para backtesting"""
    
    def __init__(self):
        self.agent = None
        self.config = {}
        self.available_symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT',
            'SOLUSDT', 'DOTUSDT', 'DOGEUSDT', 'AVAXUSDT', 'MATICUSDT'
        ]
        self.available_strategies = [
            'ema_crossover', 'rsi_mean_reversion', 'bollinger_breakout'
        ]
        self.available_timeframes = [
            '1', '3', '5', '15', '30', '60', '120', '240', '360', '720', 'D'
        ]
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('backtest_cli.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def print_header(self):
        """Imprimir cabeçalho do CLI"""
        print("\n" + "="*60)
        print("🚀 BACKTEST CLI - SISTEMA DE TRADING AUTOMATIZADO")
        print("="*60)
        print("📊 Interface de Linha de Produção para Backtesting")
        print("⚡ Dados reais da API V5 Bybit")
        print("🎯 Validação de estratégias profissional")
        print("="*60 + "\n")
    
    def print_menu(self):
        """Imprimir menu principal"""
        print("📋 OPÇÕES DISPONÍVEIS:")
        print("   1️⃣  Backtesting Rápido (configuração automática)")
        print("   2️⃣  Backtesting Personalizado (configuração manual)")
        print("   3️⃣  Backtesting de Cenários (bull/bear/sideways)")
        print("   4️⃣  Análise de Performance Histórica")
        print("   5️⃣  Configurações do Sistema")
        print("   6️⃣  Ajuda e Documentação")
        print("   0️⃣  Sair")
        print()
    
    def get_user_input(self, prompt: str, options: List[str] = None, 
                      default: str = None, validator=None) -> str:
        """
        Obter entrada do usuário com validação
        
        Args:
            prompt: Texto do prompt
            options: Lista de opções válidas
            default: Valor padrão
            validator: Função de validação customizada
        
        Returns:
            Entrada validada do usuário
        """
        
        while True:
            if default:
                user_input = input(f"{prompt} [{default}]: ").strip()
                if not user_input:
                    user_input = default
            else:
                user_input = input(f"{prompt}: ").strip()
            
            if not user_input:
                print("❌ Entrada não pode estar vazia. Tente novamente.")
                continue
            
            if options and user_input not in options:
                print(f"❌ Opção inválida. Escolha entre: {', '.join(options)}")
                continue
            
            if validator:
                try:
                    if not validator(user_input):
                        print("❌ Entrada inválida. Tente novamente.")
                        continue
                except Exception as e:
                    print(f"❌ Erro de validação: {e}")
                    continue
            
            return user_input
    
    def validate_date(self, date_str: str) -> bool:
        """Validar formato de data"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            print("❌ Formato de data inválido. Use YYYY-MM-DD")
            return False
    
    def validate_capital(self, capital_str: str) -> bool:
        """Validar capital inicial"""
        try:
            capital = float(capital_str)
            if capital <= 0:
                print("❌ Capital deve ser maior que zero")
                return False
            if capital < 100:
                print("⚠️  Capital muito baixo. Recomendado mínimo $100")
            return True
        except ValueError:
            print("❌ Capital deve ser um número válido")
            return False
    
    def get_symbol_selection(self) -> List[str]:
        """Obter seleção de símbolos"""
        print("\n📈 SELEÇÃO DE ATIVOS:")
        print("Símbolos disponíveis:")
        for i, symbol in enumerate(self.available_symbols, 1):
            print(f"   {i:2d}. {symbol}")
        
        print("\nOpções:")
        print("   • Digite números separados por vírgula (ex: 1,2,3)")
        print("   • Digite 'all' para todos os símbolos")
        print("   • Digite 'top5' para os 5 principais")
        
        while True:
            selection = input("\n🎯 Escolha os símbolos: ").strip().lower()
            
            if selection == 'all':
                return self.available_symbols
            elif selection == 'top5':
                return self.available_symbols[:5]
            else:
                try:
                    indices = [int(x.strip()) for x in selection.split(',')]
                    symbols = []
                    for idx in indices:
                        if 1 <= idx <= len(self.available_symbols):
                            symbols.append(self.available_symbols[idx-1])
                        else:
                            print(f"❌ Índice {idx} inválido")
                            break
                    else:
                        if symbols:
                            return symbols
                except ValueError:
                    print("❌ Formato inválido. Use números separados por vírgula")
    
    def get_strategy_selection(self) -> List[str]:
        """Obter seleção de estratégias"""
        print("\n🧠 SELEÇÃO DE ESTRATÉGIAS:")
        strategies_info = {
            'ema_crossover': 'EMA Crossover - Cruzamento de médias móveis',
            'rsi_mean_reversion': 'RSI Mean Reversion - Reversão à média',
            'bollinger_breakout': 'Bollinger Breakout - Rompimento de bandas'
        }
        
        for i, (strategy, description) in enumerate(strategies_info.items(), 1):
            print(f"   {i}. {strategy}: {description}")
        
        print("\nOpções:")
        print("   • Digite números separados por vírgula (ex: 1,2)")
        print("   • Digite 'all' para todas as estratégias")
        
        while True:
            selection = input("\n🎯 Escolha as estratégias: ").strip().lower()
            
            if selection == 'all':
                return self.available_strategies
            else:
                try:
                    indices = [int(x.strip()) for x in selection.split(',')]
                    strategies = []
                    for idx in indices:
                        if 1 <= idx <= len(self.available_strategies):
                            strategies.append(self.available_strategies[idx-1])
                        else:
                            print(f"❌ Índice {idx} inválido")
                            break
                    else:
                        if strategies:
                            return strategies
                except ValueError:
                    print("❌ Formato inválido. Use números separados por vírgula")
    
    def get_timeframe_selection(self) -> str:
        """Obter seleção de timeframe"""
        print("\n⏰ SELEÇÃO DE TIMEFRAME:")
        timeframe_info = {
            '1': '1 minuto', '3': '3 minutos', '5': '5 minutos',
            '15': '15 minutos', '30': '30 minutos', '60': '1 hora',
            '120': '2 horas', '240': '4 horas', '360': '6 horas',
            '720': '12 horas', 'D': '1 dia'
        }
        
        for tf, description in timeframe_info.items():
            print(f"   {tf:3s}: {description}")
        
        print("\n💡 Recomendações:")
        print("   • Scalping: 1, 3, 5 minutos")
        print("   • Day Trading: 15, 30, 60 minutos")
        print("   • Swing Trading: 240, 360, D")
        
        return self.get_user_input(
            "\n🎯 Escolha o timeframe",
            options=self.available_timeframes,
            default='5'
        )
    
    def get_date_range(self) -> tuple:
        """Obter período de datas"""
        print("\n📅 PERÍODO DE BACKTESTING:")
        
        # Sugerir períodos pré-definidos
        print("Períodos sugeridos:")
        today = datetime.now()
        
        periods = {
            '1': ('2025-01-01', '2025-03-01', 'Bull Market (Jan-Mar 2025)'),
            '2': ('2025-03-01', '2025-05-01', 'Bear Market (Mar-Mai 2025)'),
            '3': ('2025-05-01', '2025-07-01', 'Sideways Market (Mai-Jul 2025)'),
            '4': ('2024-01-01', '2024-12-31', 'Ano completo 2024'),
            '5': ('custom', 'custom', 'Período personalizado')
        }
        
        for key, (start, end, desc) in periods.items():
            print(f"   {key}. {desc}")
        
        choice = self.get_user_input(
            "\n🎯 Escolha o período",
            options=list(periods.keys()),
            default='1'
        )
        
        if choice != '5':
            start_date, end_date, _ = periods[choice]
            return start_date, end_date
        else:
            print("\n📅 PERÍODO PERSONALIZADO:")
            start_date = self.get_user_input(
                "Data de início (YYYY-MM-DD)",
                validator=self.validate_date
            )
            end_date = self.get_user_input(
                "Data de fim (YYYY-MM-DD)",
                validator=self.validate_date
            )
            
            # Validar que end_date > start_date
            if datetime.strptime(end_date, '%Y-%m-%d') <= datetime.strptime(start_date, '%Y-%m-%d'):
                print("❌ Data de fim deve ser posterior à data de início")
                return self.get_date_range()
            
            return start_date, end_date
    
    def get_capital_amount(self) -> float:
        """Obter valor do capital inicial"""
        print("\n💰 CAPITAL INICIAL:")
        print("Sugestões:")
        print("   • Teste: $1,000 - $5,000")
        print("   • Validação: $5,000 - $10,000")
        print("   • Produção: $10,000+")
        
        capital_str = self.get_user_input(
            "\n🎯 Capital inicial (USD)",
            default='10000',
            validator=self.validate_capital
        )
        
        return float(capital_str)
    
    async def run_quick_backtest(self):
        """Executar backtesting rápido com configuração automática"""
        print("\n🚀 BACKTESTING RÁPIDO")
        print("Configuração automática otimizada para resultados rápidos")
        
        # Configuração automática
        config = {
            'symbols': ['BTCUSDT', 'ETHUSDT'],
            'strategies': ['ema_crossover', 'rsi_mean_reversion'],
            'timeframe': '5',
            'start_date': '2025-01-01',
            'end_date': '2025-03-01',
            'initial_capital': 10000
        }
        
        print(f"\n📋 CONFIGURAÇÃO AUTOMÁTICA:")
        print(f"   Símbolos: {', '.join(config['symbols'])}")
        print(f"   Estratégias: {', '.join(config['strategies'])}")
        print(f"   Timeframe: {config['timeframe']} minutos")
        print(f"   Período: {config['start_date']} a {config['end_date']}")
        print(f"   Capital: ${config['initial_capital']:,}")
        
        confirm = input("\n✅ Confirmar execução? (s/N): ").strip().lower()
        if confirm not in ['s', 'sim', 'y', 'yes']:
            print("❌ Backtesting cancelado")
            return
        
        await self.execute_backtest(config)
    
    async def run_custom_backtest(self):
        """Executar backtesting personalizado"""
        print("\n🎛️  BACKTESTING PERSONALIZADO")
        print("Configure todos os parâmetros manualmente")
        
        # Obter configurações do usuário
        symbols = self.get_symbol_selection()
        strategies = self.get_strategy_selection()
        timeframe = self.get_timeframe_selection()
        start_date, end_date = self.get_date_range()
        capital = self.get_capital_amount()
        
        config = {
            'symbols': symbols,
            'strategies': strategies,
            'timeframe': timeframe,
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': capital
        }
        
        # Mostrar resumo
        print(f"\n📋 RESUMO DA CONFIGURAÇÃO:")
        print(f"   Símbolos: {', '.join(config['symbols'])}")
        print(f"   Estratégias: {', '.join(config['strategies'])}")
        print(f"   Timeframe: {config['timeframe']}")
        print(f"   Período: {config['start_date']} a {config['end_date']}")
        print(f"   Capital: ${config['initial_capital']:,}")
        
        total_tests = len(symbols) * len(strategies)
        print(f"\n🔢 Total de testes: {total_tests}")
        
        confirm = input("\n✅ Confirmar execução? (s/N): ").strip().lower()
        if confirm not in ['s', 'sim', 'y', 'yes']:
            print("❌ Backtesting cancelado")
            return
        
        await self.execute_backtest(config)
    
    async def run_scenario_backtest(self):
        """Executar backtesting de cenários"""
        print("\n🎭 BACKTESTING DE CENÁRIOS")
        print("Teste estratégias em diferentes condições de mercado")
        
        scenarios = {
            '1': {
                'name': 'bull_market',
                'start_date': '2025-01-01',
                'end_date': '2025-03-01',
                'description': 'Mercado em Alta - Bitcoin $42k → $73k'
            },
            '2': {
                'name': 'bear_market',
                'start_date': '2025-03-01',
                'end_date': '2025-05-01',
                'description': 'Mercado em Baixa - Bitcoin $73k → $56k'
            },
            '3': {
                'name': 'sideways_market',
                'start_date': '2025-05-01',
                'end_date': '2025-07-01',
                'description': 'Mercado Lateral - Bitcoin $56k ↔ $62k'
            },
            '4': {
                'name': 'all_scenarios',
                'description': 'Todos os cenários'
            }
        }
        
        print("\n📊 CENÁRIOS DISPONÍVEIS:")
        for key, scenario in scenarios.items():
            print(f"   {key}. {scenario['description']}")
        
        choice = self.get_user_input(
            "\n🎯 Escolha o cenário",
            options=list(scenarios.keys()),
            default='4'
        )
        
        # Configuração básica
        symbols = ['BTCUSDT', 'ETHUSDT']
        strategies = ['ema_crossover', 'rsi_mean_reversion']
        timeframe = '5'
        capital = 10000
        
        if choice == '4':
            # Executar todos os cenários
            for scenario_key in ['1', '2', '3']:
                scenario = scenarios[scenario_key]
                print(f"\n🎬 EXECUTANDO: {scenario['description']}")
                
                config = {
                    'symbols': symbols,
                    'strategies': strategies,
                    'timeframe': timeframe,
                    'start_date': scenario['start_date'],
                    'end_date': scenario['end_date'],
                    'initial_capital': capital,
                    'scenario_name': scenario['name']
                }
                
                await self.execute_backtest(config)
        else:
            # Executar cenário específico
            scenario = scenarios[choice]
            config = {
                'symbols': symbols,
                'strategies': strategies,
                'timeframe': timeframe,
                'start_date': scenario['start_date'],
                'end_date': scenario['end_date'],
                'initial_capital': capital,
                'scenario_name': scenario['name']
            }
            
            await self.execute_backtest(config)
    
    async def execute_backtest(self, config: Dict[str, Any]):
        """Executar backtesting com configuração fornecida"""
        try:
            print(f"\n🔄 INICIANDO BACKTESTING...")
            print("="*50)
            
            # Inicializar agente se necessário
            if not self.agent:
                print("🔧 Inicializando BacktestingAgent...")
                self.agent = BacktestingAgentV5()
                print("✅ Agent inicializado com sucesso!")
            
            results = {}
            total_tests = len(config['symbols']) * len(config['strategies'])
            current_test = 0
            
            # Executar testes
            for symbol in config['symbols']:
                print(f"\n📈 SÍMBOLO: {symbol}")
                symbol_results = {}
                
                for strategy in config['strategies']:
                    current_test += 1
                    print(f"\n   🧠 Estratégia: {strategy} ({current_test}/{total_tests})")
                    
                    test_config = {
                        'symbol': symbol,
                        'strategy': strategy,
                        'start_date': config['start_date'],
                        'end_date': config['end_date'],
                        'timeframe': config['timeframe'],
                        'initial_capital': config['initial_capital']
                    }
                    
                    try:
                        result = await self.agent.run_backtest(test_config)
                        
                        if result['status'] == 'success':
                            perf = result['performance']
                            print(f"      💰 Retorno: {perf['total_return']:.2%}")
                            print(f"      🎯 Win Rate: {perf['win_rate']:.1%}")
                            print(f"      📊 Trades: {perf['total_trades']}")
                            print(f"      📉 Drawdown: {perf['max_drawdown']:.2%}")
                            
                            symbol_results[strategy] = perf
                        else:
                            print(f"      ❌ Erro: {result['error']}")
                            symbol_results[strategy] = {'error': result['error']}
                    
                    except Exception as e:
                        print(f"      ❌ Exceção: {e}")
                        symbol_results[strategy] = {'error': str(e)}
                
                results[symbol] = symbol_results
            
            # Gerar relatório
            self.generate_report(results, config)
            
        except Exception as e:
            print(f"❌ Erro durante execução: {e}")
            self.logger.error(f"Erro durante backtesting: {e}")
    
    def generate_report(self, results: Dict[str, Any], config: Dict[str, Any]):
        """Gerar relatório dos resultados"""
        print("\n" + "="*60)
        print("📊 RELATÓRIO DE RESULTADOS")
        print("="*60)
        
        # Resumo por símbolo
        for symbol, symbol_data in results.items():
            print(f"\n📈 {symbol}:")
            
            for strategy, perf in symbol_data.items():
                if 'error' in perf:
                    print(f"   ❌ {strategy}: {perf['error']}")
                else:
                    print(f"   ✅ {strategy}:")
                    print(f"      Retorno: {perf['total_return']:.2%}")
                    print(f"      Win Rate: {perf['win_rate']:.1%}")
                    print(f"      Trades: {perf['total_trades']}")
                    print(f"      Drawdown: {perf['max_drawdown']:.2%}")
        
        # Análise comparativa
        print(f"\n" + "="*60)
        print("🏆 ANÁLISE COMPARATIVA")
        print("="*60)
        
        best_strategy = None
        best_return = -float('inf')
        all_results = []
        
        for symbol, symbol_data in results.items():
            for strategy, perf in symbol_data.items():
                if 'error' not in perf:
                    all_results.append({
                        'symbol': symbol,
                        'strategy': strategy,
                        'return': perf['total_return'],
                        'win_rate': perf['win_rate'],
                        'trades': perf['total_trades'],
                        'drawdown': perf['max_drawdown']
                    })
                    
                    if perf['total_return'] > best_return:
                        best_return = perf['total_return']
                        best_strategy = f"{strategy} em {symbol}"
        
        if all_results:
            # Melhor performance
            print(f"🥇 Melhor Performance: {best_strategy}")
            print(f"   Retorno: {best_return:.2%}")
            
            # Estatísticas gerais
            avg_return = sum(r['return'] for r in all_results) / len(all_results)
            avg_win_rate = sum(r['win_rate'] for r in all_results) / len(all_results)
            avg_drawdown = sum(r['drawdown'] for r in all_results) / len(all_results)
            
            print(f"\n📊 Estatísticas Gerais:")
            print(f"   Retorno Médio: {avg_return:.2%}")
            print(f"   Win Rate Médio: {avg_win_rate:.1%}")
            print(f"   Drawdown Médio: {avg_drawdown:.2%}")
        
        # Recomendações
        print(f"\n" + "="*60)
        print("💡 RECOMENDAÇÕES")
        print("="*60)
        
        if all_results:
            if best_return > 0.1:  # 10%
                print("✅ RECOMENDAÇÃO: Prosseguir para Demo Trading")
                print("   📈 Performance satisfatória detectada")
                print("   🎯 Próximo passo: Validação em tempo real")
            elif best_return > 0.05:  # 5%
                print("⚠️  RECOMENDAÇÃO: Otimizar parâmetros")
                print("   📊 Performance moderada")
                print("   🔧 Ajustar estratégias antes do Demo Trading")
            else:
                print("❌ RECOMENDAÇÃO: Revisar estratégias")
                print("   📉 Performance abaixo do esperado")
                print("   🔄 Considerar outras abordagens")
        
        # Salvar relatório
        self.save_report(results, config)
    
    def save_report(self, results: Dict[str, Any], config: Dict[str, Any]):
        """Salvar relatório em arquivo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"backtest_report_{timestamp}.json"
        
        report_data = {
            'timestamp': timestamp,
            'config': config,
            'results': results,
            'summary': {
                'total_tests': len(config['symbols']) * len(config['strategies']),
                'period': f"{config['start_date']} to {config['end_date']}",
                'capital': config['initial_capital']
            }
        }
        
        os.makedirs('reports', exist_ok=True)
        filepath = os.path.join('reports', filename)
        
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n💾 Relatório salvo: {filepath}")
    
    def show_help(self):
        """Mostrar ajuda e documentação"""
        print("\n📚 AJUDA E DOCUMENTAÇÃO")
        print("="*50)
        
        help_text = """
🎯 COMO USAR O BACKTEST CLI:

1. BACKTESTING RÁPIDO:
   • Configuração automática otimizada
   • Ideal para testes iniciais
   • Símbolos: BTC, ETH
   • Estratégias: EMA Crossover, RSI Mean Reversion

2. BACKTESTING PERSONALIZADO:
   • Configure todos os parâmetros
   • Escolha símbolos, estratégias, período
   • Controle total sobre os testes

3. BACKTESTING DE CENÁRIOS:
   • Teste em condições específicas de mercado
   • Bull Market, Bear Market, Sideways
   • Validação robusta das estratégias

📊 INTERPRETAÇÃO DOS RESULTADOS:

• RETORNO: Percentual de lucro/prejuízo
• WIN RATE: Porcentagem de trades vencedores
• TRADES: Número total de operações
• DRAWDOWN: Maior perda consecutiva

🎯 CRITÉRIOS DE APROVAÇÃO:

• Retorno > 5%: Performance aceitável
• Win Rate > 55%: Consistência boa
• Drawdown < 15%: Risco controlado

💡 PRÓXIMOS PASSOS:

1. Performance boa → Demo Trading
2. Performance moderada → Otimização
3. Performance ruim → Revisar estratégias

🔧 ARQUIVOS GERADOS:

• reports/: Relatórios detalhados em JSON
• backtest_cli.log: Log de execução
• results/: Resultados individuais dos agentes
        """
        
        print(help_text)
    
    async def main_loop(self):
        """Loop principal da interface"""
        self.print_header()
        
        while True:
            self.print_menu()
            
            choice = input("🎯 Escolha uma opção: ").strip()
            
            if choice == '0':
                print("\n👋 Obrigado por usar o Backtest CLI!")
                print("🚀 Boa sorte com seus trades!")
                break
            elif choice == '1':
                await self.run_quick_backtest()
            elif choice == '2':
                await self.run_custom_backtest()
            elif choice == '3':
                await self.run_scenario_backtest()
            elif choice == '4':
                print("\n📈 ANÁLISE DE PERFORMANCE HISTÓRICA")
                print("🚧 Funcionalidade em desenvolvimento...")
            elif choice == '5':
                print("\n⚙️  CONFIGURAÇÕES DO SISTEMA")
                print("🚧 Funcionalidade em desenvolvimento...")
            elif choice == '6':
                self.show_help()
            else:
                print("❌ Opção inválida. Tente novamente.")
            
            if choice != '0':
                input("\n⏸️  Pressione Enter para continuar...")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Backtest CLI - Sistema de Trading Automatizado')
    parser.add_argument('--version', action='version', version='Backtest CLI v1.0')
    parser.add_argument('--debug', action='store_true', help='Ativar modo debug')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        cli = BacktestCLI()
        asyncio.run(cli.main_loop())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrompido pelo usuário")
        print("👋 Até logo!")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        logging.error(f"Erro inesperado: {e}")

if __name__ == "__main__":
    main()

