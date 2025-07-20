#!/usr/bin/env python3
"""
CLI de Backtesting Integrado - Versão 2.0
Interface de linha de comando para backtesting profissional
Integra todos os agentes e configurações de risco
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import traceback

# Adicionar diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Imports dos agentes
from agents.backtesting_agent_v5 import BacktestingAgentV5
from agents.risk_management_agent import RiskManagementAgent
from agents.market_analysis_agent import MarketAnalysisAgent
from agents.orchestrator_agent import OrchestratorAgent

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BacktestCLI:
    """Interface CLI para backtesting integrado"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Inicializar agentes
        self.backtesting_agent = BacktestingAgentV5()
        self.risk_agent = RiskManagementAgent()
        self.market_agent = MarketAnalysisAgent()
        self.orchestrator = OrchestratorAgent()
        
        # Carregar configurações integradas
        self.risk_params = self.load_risk_parameters()
        self.trading_config = self.load_trading_config()
        self.backtest_config = self.load_backtest_config()
        
        self.logger.info("BacktestCLI inicializado com integração completa")
    
    def load_risk_parameters(self) -> Dict[str, Any]:
        """Carregar parâmetros de risco do arquivo JSON"""
        try:
            with open('config/risk_parameters.json', 'r') as f:
                config = json.load(f)
                return config.get('risk_management', {})
        except FileNotFoundError:
            self.logger.warning("Arquivo risk_parameters.json não encontrado, usando valores padrão")
            return {
                "max_position_size": 0.10,
                "stop_loss_percentage": 0.02,
                "take_profit_percentage": 0.04,
                "max_daily_loss": 0.05,
                "max_drawdown": 0.15,
                "risk_per_trade": 0.01
            }
    
    def load_trading_config(self) -> Dict[str, Any]:
        """Carregar configurações de trading"""
        try:
            with open('config/trading_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def load_backtest_config(self) -> Dict[str, Any]:
        """Carregar configurações de backtesting"""
        try:
            with open('config/backtesting_config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "symbols": ["BTCUSDT", "ETHUSDT"],
                "strategies": ["ema_crossover", "rsi_mean_reversion"],
                "timeframes": ["5", "15", "30"]
            }
    
    def show_header(self):
        """Exibir cabeçalho do CLI"""
        print("\n" + "="*60)
        print("🚀 BACKTEST CLI - SISTEMA DE TRADING AUTOMATIZADO v2.0")
        print("="*60)
        print("📊 Interface de Linha de Produção para Backtesting")
        print("⚡ Dados reais da API V5 Bybit")
        print("🎯 Validação de estratégias profissional")
        print("🛡️ Gestão de risco integrada")
        print("="*60)
    
    def show_main_menu(self):
        """Exibir menu principal"""
        print("\n📋 OPÇÕES DISPONÍVEIS:")
        print("   1️⃣  Backtesting Rápido (configuração automática)")
        print("   2️⃣  Backtesting Personalizado (configuração manual)")
        print("   3️⃣  Backtesting de Cenários (bull/bear/sideways)")
        print("   4️⃣  Análise de Performance Histórica")
        print("   5️⃣  Configurações do Sistema")
        print("   6️⃣  Ajuda e Documentação")
        print("   7️⃣  Backtesting Expert (controle granular)")
        print("   0️⃣  Sair")
    
    async def run(self):
        """Executar CLI principal"""
        self.show_header()
        
        while True:
            try:
                self.show_main_menu()
                
                choice = input("\n🎯 Escolha uma opção: ").strip()
                
                if choice == "0":
                    print("\n👋 Obrigado por usar o Backtest CLI!")
                    print("🚀 Boa sorte com seus trades!")
                    break
                elif choice == "1":
                    await self.run_quick_backtesting()
                elif choice == "2":
                    await self.run_custom_backtesting()
                elif choice == "3":
                    await self.run_scenario_backtesting()
                elif choice == "4":
                    await self.run_performance_analysis()
                elif choice == "5":
                    self.show_system_config()
                elif choice == "6":
                    self.show_help()
                elif choice == "7":
                    await self.run_expert_backtesting()
                else:
                    print("❌ Opção inválida. Tente novamente.")
                
                if choice != "0":
                    input("\n⏸️  Pressione Enter para continuar...")
            
            except KeyboardInterrupt:
                print("\n\n👋 Saindo do sistema...")
                break
            except Exception as e:
                print(f"\n❌ Erro inesperado: {e}")
                self.logger.error(f"Erro no CLI: {e}")
                input("\n⏸️  Pressione Enter para continuar...")
    
    async def run_quick_backtesting(self):
        """Backtesting rápido com configuração automática"""
        print("\n🚀 BACKTESTING RÁPIDO")
        print("Configuração automática otimizada para resultados rápidos")
        
        # Configuração automática com gestão de risco
        config = {
            'symbols': ['BTCUSDT', 'ETHUSDT'],
            'strategies': ['ema_crossover', 'rsi_mean_reversion'],
            'timeframe': '15',  # Mudado de 5 para 15 (menos ruído)
            'start_date': '2024-01-01',
            'end_date': '2024-03-31',
            'initial_capital': 10000,
            'risk_params': self.risk_params  # Integração com risk_parameters.json
        }
        
        print(f"\n📋 CONFIGURAÇÃO AUTOMÁTICA:")
        print(f"   Símbolos: {', '.join(config['symbols'])}")
        print(f"   Estratégias: {', '.join(config['strategies'])}")
        print(f"   Timeframe: {config['timeframe']} minutos")
        print(f"   Período: {config['start_date']} a {config['end_date']}")
        print(f"   Capital: ${config['initial_capital']:,}")
        print(f"   Position Size: {self.risk_params['max_position_size']*100:.1f}%")
        print(f"   Stop Loss: {self.risk_params['stop_loss_percentage']*100:.1f}%")
        
        confirm = input("\n✅ Confirmar execução? (s/N): ").lower()
        if confirm != 's':
            print("❌ Execução cancelada.")
            return
        
        await self.execute_backtest_suite(config)
    
    async def run_expert_backtesting(self):
        """Backtesting com controle granular de parâmetros"""
        print("\n🔬 BACKTESTING EXPERT - CONTROLE GRANULAR")
        print("Configuração detalhada de todos os parâmetros")
        
        config = {}
        
        # Configurações básicas
        config['symbol'] = self.select_symbol_expert()
        config['timeframe'] = self.select_timeframe_expert()
        config['start_date'], config['end_date'] = self.select_period_expert()
        config['strategy'] = self.select_strategy_expert()
        config['initial_capital'] = self.select_capital_expert()
        
        # Parâmetros de risco (NOVO)
        config['risk_params'] = self.configure_risk_expert()
        
        # Parâmetros da estratégia (NOVO)
        config['strategy_params'] = self.configure_strategy_expert(config['strategy'])
        
        # Executar com configuração completa
        await self.execute_expert_backtest(config)
    
    def select_symbol_expert(self) -> str:
        """Seleção de símbolo para modo expert"""
        symbols = self.backtest_config.get('symbols', ['BTCUSDT', 'ETHUSDT'])
        
        print(f"\n📈 SELEÇÃO DE SÍMBOLO:")
        for i, symbol in enumerate(symbols, 1):
            print(f"   {i}. {symbol}")
        
        while True:
            try:
                choice = int(input(f"Escolha o símbolo (1-{len(symbols)}): "))
                if 1 <= choice <= len(symbols):
                    return symbols[choice-1]
                else:
                    print(f"❌ Escolha entre 1 e {len(symbols)}")
            except ValueError:
                print("❌ Digite um número válido")
    
    def select_timeframe_expert(self) -> str:
        """Seleção de timeframe para modo expert"""
        timeframes = self.backtest_config.get('timeframes', ['5', '15', '30', '60'])
        
        print(f"\n⏰ SELEÇÃO DE TIMEFRAME:")
        for i, tf in enumerate(timeframes, 1):
            tf_name = f"{tf} minutos" if tf.isdigit() else tf
            print(f"   {i}. {tf_name}")
        
        while True:
            try:
                choice = int(input(f"Escolha o timeframe (1-{len(timeframes)}): "))
                if 1 <= choice <= len(timeframes):
                    return timeframes[choice-1]
                else:
                    print(f"❌ Escolha entre 1 e {len(timeframes)}")
            except ValueError:
                print("❌ Digite um número válido")
    
    def select_period_expert(self) -> tuple:
        """Seleção de período para modo expert"""
        print(f"\n📅 SELEÇÃO DE PERÍODO:")
        print("   1. Período personalizado")
        print("   2. Q1 2024 (Jan-Mar)")
        print("   3. Q2 2024 (Abr-Jun)")
        print("   4. Q3 2024 (Jul-Set)")
        print("   5. Q4 2024 (Out-Dez)")
        print("   6. Ano completo 2024")
        
        while True:
            try:
                choice = int(input("Escolha o período (1-6): "))
                if choice == 1:
                    start = input("Data de início (YYYY-MM-DD): ")
                    end = input("Data de fim (YYYY-MM-DD): ")
                    return start, end
                elif choice == 2:
                    return "2024-01-01", "2024-03-31"
                elif choice == 3:
                    return "2024-04-01", "2024-06-30"
                elif choice == 4:
                    return "2024-07-01", "2024-09-30"
                elif choice == 5:
                    return "2024-10-01", "2024-12-31"
                elif choice == 6:
                    return "2024-01-01", "2024-12-31"
                else:
                    print("❌ Escolha entre 1 e 6")
            except ValueError:
                print("❌ Digite um número válido")
    
    def select_strategy_expert(self) -> str:
        """Seleção de estratégia para modo expert"""
        strategies = self.backtest_config.get('strategies', ['ema_crossover', 'rsi_mean_reversion'])
        
        print(f"\n🧠 SELEÇÃO DE ESTRATÉGIA:")
        for i, strategy in enumerate(strategies, 1):
            strategy_name = strategy.replace('_', ' ').title()
            print(f"   {i}. {strategy_name}")
        
        while True:
            try:
                choice = int(input(f"Escolha a estratégia (1-{len(strategies)}): "))
                if 1 <= choice <= len(strategies):
                    return strategies[choice-1]
                else:
                    print(f"❌ Escolha entre 1 e {len(strategies)}")
            except ValueError:
                print("❌ Digite um número válido")
    
    def select_capital_expert(self) -> float:
        """Seleção de capital inicial para modo expert"""
        print(f"\n💰 CAPITAL INICIAL:")
        
        while True:
            try:
                capital = float(input("Capital inicial (USD, padrão 10000): ") or 10000)
                if 1000 <= capital <= 1000000:
                    return capital
                else:
                    print("❌ Capital deve estar entre $1,000 e $1,000,000")
            except ValueError:
                print("❌ Digite um número válido")
    
    def configure_risk_expert(self) -> Dict[str, Any]:
        """Configurar parâmetros de risco detalhadamente"""
        print("\n🛡️ CONFIGURAÇÃO DE RISCO:")
        
        risk_config = {}
        
        # Position sizing
        while True:
            try:
                pos_size = float(input(f"Position size (% do capital, atual: {self.risk_params['max_position_size']*100:.1f}%): ") or self.risk_params['max_position_size']*100)
                if 1 <= pos_size <= 25:
                    risk_config['max_position_size'] = pos_size / 100
                    break
                else:
                    print("❌ Position size deve estar entre 1% e 25%")
            except ValueError:
                print("❌ Digite um número válido")
        
        # Stop loss
        while True:
            try:
                stop_loss = float(input(f"Stop loss (% por trade, atual: {self.risk_params['stop_loss_percentage']*100:.1f}%): ") or self.risk_params['stop_loss_percentage']*100)
                if 0.5 <= stop_loss <= 10:
                    risk_config['stop_loss_percentage'] = stop_loss / 100
                    break
                else:
                    print("❌ Stop loss deve estar entre 0.5% e 10%")
            except ValueError:
                print("❌ Digite um número válido")
        
        # Take profit
        while True:
            try:
                take_profit = float(input(f"Take profit (% por trade, atual: {self.risk_params['take_profit_percentage']*100:.1f}%): ") or self.risk_params['take_profit_percentage']*100)
                if risk_config['stop_loss_percentage']*100 <= take_profit <= 20:
                    risk_config['take_profit_percentage'] = take_profit / 100
                    break
                else:
                    print(f"❌ Take profit deve estar entre {risk_config['stop_loss_percentage']*100:.1f}% e 20%")
            except ValueError:
                print("❌ Digite um número válido")
        
        # Max daily loss
        while True:
            try:
                daily_loss = float(input(f"Perda máxima diária (%, atual: {self.risk_params['max_daily_loss']*100:.1f}%): ") or self.risk_params['max_daily_loss']*100)
                if 1 <= daily_loss <= 15:
                    risk_config['max_daily_loss'] = daily_loss / 100
                    break
                else:
                    print("❌ Perda diária deve estar entre 1% e 15%")
            except ValueError:
                print("❌ Digite um número válido")
        
        return risk_config
    
    def configure_strategy_expert(self, strategy: str) -> Dict[str, Any]:
        """Configurar parâmetros específicos da estratégia"""
        print(f"\n⚙️ CONFIGURAÇÃO DA ESTRATÉGIA: {strategy.replace('_', ' ').title()}")
        
        strategy_config = {}
        
        if 'ema' in strategy.lower():
            # Parâmetros EMA Crossover
            while True:
                try:
                    fast_ema = int(input("Fast EMA period (padrão 21): ") or 21)
                    if 5 <= fast_ema <= 50:
                        strategy_config['fast_period'] = fast_ema
                        break
                    else:
                        print("❌ Fast EMA deve estar entre 5 e 50")
                except ValueError:
                    print("❌ Digite um número válido")
            
            while True:
                try:
                    slow_ema = int(input("Slow EMA period (padrão 50): ") or 50)
                    if fast_ema < slow_ema <= 200:
                        strategy_config['slow_period'] = slow_ema
                        break
                    else:
                        print(f"❌ Slow EMA deve estar entre {fast_ema+1} e 200")
                except ValueError:
                    print("❌ Digite um número válido")
        
        elif 'rsi' in strategy.lower():
            # Parâmetros RSI Mean Reversion
            while True:
                try:
                    rsi_period = int(input("RSI period (padrão 14): ") or 14)
                    if 5 <= rsi_period <= 30:
                        strategy_config['rsi_period'] = rsi_period
                        break
                    else:
                        print("❌ RSI period deve estar entre 5 e 30")
                except ValueError:
                    print("❌ Digite um número válido")
            
            while True:
                try:
                    oversold = int(input("RSI oversold level (padrão 25): ") or 25)
                    if 10 <= oversold <= 40:
                        strategy_config['oversold'] = oversold
                        break
                    else:
                        print("❌ Oversold deve estar entre 10 e 40")
                except ValueError:
                    print("❌ Digite um número válido")
            
            while True:
                try:
                    overbought = int(input("RSI overbought level (padrão 75): ") or 75)
                    if 60 <= overbought <= 90 and overbought > oversold + 20:
                        strategy_config['overbought'] = overbought
                        break
                    else:
                        print(f"❌ Overbought deve estar entre 60 e 90, e > {oversold + 20}")
                except ValueError:
                    print("❌ Digite um número válido")
        
        return strategy_config
    
    async def execute_expert_backtest(self, config: Dict[str, Any]):
        """Executar backtesting expert com configuração completa"""
        print("\n🔄 INICIANDO BACKTESTING EXPERT...")
        print("="*50)
        
        try:
            # Configurar backtesting com parâmetros personalizados
            backtest_config = {
                'symbol': config['symbol'],
                'strategy': config['strategy'],
                'start_date': config['start_date'],
                'end_date': config['end_date'],
                'timeframe': config['timeframe'],
                'initial_capital': config['initial_capital'],
                'risk_params': config['risk_params'],
                'strategy_params': config.get('strategy_params', {}),
                'commission': 0.001
            }
            
            print(f"🔧 Inicializando BacktestingAgent...")
            
            # Executar backtesting
            result = await self.backtesting_agent.run_backtest(backtest_config)
            
            if result['status'] == 'success':
                self.display_backtest_results(result, config['symbol'], config['strategy'])
                
                # Salvar relatório
                report_path = self.save_backtest_report(result, "expert")
                print(f"\n💾 Relatório salvo: {report_path}")
            else:
                print(f"❌ Erro durante backtesting: {result.get('error', 'Desconhecido')}")
        
        except Exception as e:
            print(f"❌ Erro durante execução: {e}")
            self.logger.error(f"Erro no backtesting expert: {e}")
    
    async def execute_backtest_suite(self, config: Dict[str, Any]):
        """Executar suite de backtesting"""
        print("\n🔄 INICIANDO BACKTESTING...")
        print("="*50)
        
        try:
            results = {}
            total_tests = len(config['symbols']) * len(config['strategies'])
            current_test = 0
            
            for symbol in config['symbols']:
                results[symbol] = {}
                
                for strategy in config['strategies']:
                    current_test += 1
                    print(f"\n📈 SÍMBOLO: {symbol}")
                    print(f"   🧠 Estratégia: {strategy} ({current_test}/{total_tests})")
                    
                    # Configurar teste individual
                    test_config = {
                        'symbol': symbol,
                        'strategy': strategy,
                        'start_date': config['start_date'],
                        'end_date': config['end_date'],
                        'timeframe': config['timeframe'],
                        'initial_capital': config['initial_capital'],
                        'risk_params': config['risk_params'],
                        'commission': 0.001
                    }
                    
                    # Executar backtesting
                    result = await self.backtesting_agent.run_backtest(test_config)
                    results[symbol][strategy] = result
                    
                    if result['status'] == 'success':
                        perf = result['performance']
                        print(f"      💰 Retorno: {perf['total_return']:.2%}")
                        print(f"      🎯 Win Rate: {perf['win_rate']:.1%}")
                        print(f"      📊 Trades: {perf['total_trades']}")
                        print(f"      📉 Drawdown: {perf['max_drawdown']:.2%}")
                    else:
                        print(f"      ❌ Erro: {result.get('error', 'Desconhecido')}")
            
            # Análise comparativa
            self.display_comparative_analysis(results)
            
            # Salvar relatório
            report_path = self.save_backtest_report(results, "quick")
            print(f"\n💾 Relatório salvo: {report_path}")
        
        except Exception as e:
            print(f"❌ Erro durante execução: {e}")
            self.logger.error(f"Erro na suite de backtesting: {e}")
    
    def display_backtest_results(self, result: Dict[str, Any], symbol: str, strategy: str):
        """Exibir resultados de backtesting individual"""
        if result['status'] != 'success':
            print(f"❌ Erro: {result.get('error', 'Desconhecido')}")
            return
        
        perf = result['performance']
        
        print(f"\n📊 RESULTADOS - {symbol} {strategy.replace('_', ' ').title()}")
        print("="*50)
        print(f"💰 Capital Inicial: ${perf['initial_capital']:,.2f}")
        print(f"💰 Capital Final: ${perf['final_capital']:,.2f}")
        print(f"📈 Retorno Total: {perf['total_return']:.2%}")
        print(f"📊 Total de Trades: {perf['total_trades']}")
        print(f"✅ Trades Vencedores: {perf['winning_trades']}")
        print(f"❌ Trades Perdedores: {perf['losing_trades']}")
        print(f"🎯 Win Rate: {perf['win_rate']:.1%}")
        print(f"📉 Max Drawdown: {perf['max_drawdown']:.2%}")
        print(f"📊 Sharpe Ratio: {perf['sharpe_ratio']:.2f}")
        print(f"💹 Profit Factor: {perf['profit_factor']:.2f}")
        
        # Análise de risco
        risk_params = result.get('risk_params_used', {})
        if risk_params:
            print(f"\n🛡️ PARÂMETROS DE RISCO UTILIZADOS:")
            print(f"   Position Size: {risk_params.get('max_position_size', 0)*100:.1f}%")
            print(f"   Stop Loss: {risk_params.get('stop_loss_percentage', 0)*100:.1f}%")
            print(f"   Take Profit: {risk_params.get('take_profit_percentage', 0)*100:.1f}%")
        
        # Recomendações
        self.display_recommendations(perf)
    
    def display_comparative_analysis(self, results: Dict[str, Any]):
        """Exibir análise comparativa dos resultados"""
        print(f"\n🏆 ANÁLISE COMPARATIVA")
        print("="*50)
        
        best_performance = None
        best_return = -float('inf')
        
        all_results = []
        
        for symbol, symbol_results in results.items():
            for strategy, result in symbol_results.items():
                if result['status'] == 'success':
                    perf = result['performance']
                    result_data = {
                        'symbol': symbol,
                        'strategy': strategy,
                        'return': perf['total_return'],
                        'win_rate': perf['win_rate'],
                        'drawdown': perf['max_drawdown'],
                        'trades': perf['total_trades']
                    }
                    all_results.append(result_data)
                    
                    if perf['total_return'] > best_return:
                        best_return = perf['total_return']
                        best_performance = result_data
        
        if best_performance:
            print(f"🥇 Melhor Performance: {best_performance['strategy'].replace('_', ' ').title()} em {best_performance['symbol']}")
            print(f"   Retorno: {best_performance['return']:.2%}")
            print(f"   Win Rate: {best_performance['win_rate']:.1%}")
            print(f"   Drawdown: {best_performance['drawdown']:.2%}")
        
        # Estatísticas gerais
        if all_results:
            avg_return = sum(r['return'] for r in all_results) / len(all_results)
            avg_win_rate = sum(r['win_rate'] for r in all_results) / len(all_results)
            avg_drawdown = sum(r['drawdown'] for r in all_results) / len(all_results)
            
            print(f"\n📊 ESTATÍSTICAS GERAIS:")
            print(f"   Retorno Médio: {avg_return:.2%}")
            print(f"   Win Rate Médio: {avg_win_rate:.1%}")
            print(f"   Drawdown Médio: {avg_drawdown:.2%}")
        
        # Recomendações gerais
        self.display_general_recommendations(all_results)
    
    def display_recommendations(self, performance: Dict[str, Any]):
        """Exibir recomendações baseadas na performance"""
        print(f"\n💡 RECOMENDAÇÕES:")
        
        total_return = performance['total_return']
        win_rate = performance['win_rate']
        max_drawdown = performance['max_drawdown']
        
        if total_return > 0.15:  # >15%
            print("✅ EXCELENTE: Performance excepcional - Prosseguir para Demo Trading")
        elif total_return > 0.05:  # 5-15%
            print("✅ BOM: Performance satisfatória - Considerar otimização de parâmetros")
        elif total_return > -0.05:  # -5% a 5%
            print("⚠️ NEUTRO: Performance neutra - Revisar estratégia e parâmetros")
        else:  # <-5%
            print("❌ RUIM: Performance negativa - Otimização crítica necessária")
        
        if win_rate > 0.6:
            print("✅ Win rate consistente")
        elif win_rate > 0.4:
            print("⚠️ Win rate moderado - Melhorar precisão dos sinais")
        else:
            print("❌ Win rate baixo - Revisar lógica da estratégia")
        
        if max_drawdown < 0.1:
            print("✅ Risco controlado adequadamente")
        elif max_drawdown < 0.2:
            print("⚠️ Drawdown moderado - Monitorar gestão de risco")
        else:
            print("❌ Drawdown elevado - Revisar gestão de risco urgentemente")
    
    def display_general_recommendations(self, results: List[Dict[str, Any]]):
        """Exibir recomendações gerais"""
        if not results:
            return
        
        print(f"\n💡 RECOMENDAÇÕES GERAIS:")
        
        positive_results = [r for r in results if r['return'] > 0]
        
        if len(positive_results) >= len(results) * 0.7:
            print("✅ SISTEMA PROMISSOR: Maioria dos testes positivos")
            print("🎯 Próximo passo: Demo Trading com capital virtual")
        elif len(positive_results) >= len(results) * 0.4:
            print("⚠️ SISTEMA MODERADO: Resultados mistos")
            print("🔧 Próximo passo: Otimização de parâmetros")
        else:
            print("❌ SISTEMA NECESSITA OTIMIZAÇÃO: Poucos resultados positivos")
            print("🛠️ Próximo passo: Revisão completa das estratégias")
    
    def save_backtest_report(self, results: Dict[str, Any], test_type: str) -> str:
        """Salvar relatório de backtesting"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_report_{test_type}_{timestamp}.json"
        
        report = {
            "timestamp": timestamp,
            "test_type": test_type,
            "results": results,
            "risk_parameters": self.risk_params,
            "system_config": {
                "cli_version": "2.0",
                "integration_enabled": True,
                "risk_management": True
            }
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            return filename
        except Exception as e:
            self.logger.error(f"Erro ao salvar relatório: {e}")
            return "Erro ao salvar"
    
    async def run_custom_backtesting(self):
        """Backtesting personalizado"""
        print("\n🎯 BACKTESTING PERSONALIZADO")
        print("Configuração manual dos parâmetros principais")
        # Implementação simplificada - pode ser expandida
        await self.run_quick_backtesting()
    
    async def run_scenario_backtesting(self):
        """Backtesting de cenários"""
        print("\n📊 BACKTESTING DE CENÁRIOS")
        print("Teste em diferentes condições de mercado")
        # Implementação simplificada - pode ser expandida
        await self.run_quick_backtesting()
    
    async def run_performance_analysis(self):
        """Análise de performance histórica"""
        print("\n📈 ANÁLISE DE PERFORMANCE HISTÓRICA")
        print("Análise de relatórios anteriores")
        print("⚠️ Funcionalidade em desenvolvimento")
    
    def show_system_config(self):
        """Exibir configurações do sistema"""
        print("\n⚙️ CONFIGURAÇÕES DO SISTEMA")
        print("="*40)
        print(f"CLI Versão: 2.0")
        print(f"Integração: Completa")
        print(f"Agentes Carregados: 4")
        print(f"Risk Management: ✅ Ativo")
        print(f"Position Size: {self.risk_params['max_position_size']*100:.1f}%")
        print(f"Stop Loss: {self.risk_params['stop_loss_percentage']*100:.1f}%")
        print(f"Max Daily Loss: {self.risk_params['max_daily_loss']*100:.1f}%")
    
    def show_help(self):
        """Exibir ajuda e documentação"""
        print("\n📚 AJUDA E DOCUMENTAÇÃO")
        print("="*40)
        print("🚀 Backtesting Rápido: Configuração automática otimizada")
        print("🎯 Backtesting Personalizado: Configuração manual básica")
        print("📊 Backtesting de Cenários: Teste em bull/bear/sideways")
        print("🔬 Backtesting Expert: Controle granular de parâmetros")
        print("📈 Análise de Performance: Histórico de relatórios")
        print("⚙️ Configurações: Status do sistema")
        print("\n🛡️ GESTÃO DE RISCO INTEGRADA:")
        print("   • Position sizing limitado")
        print("   • Stop loss automático")
        print("   • Limite de perda diária")
        print("   • Drawdown máximo controlado")

async def main():
    """Função principal"""
    try:
        cli = BacktestCLI()
        await cli.run()
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        logging.error(f"Erro crítico no CLI: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

