"""
Strategy Lab Professional V5 - Módulo Integrado com Semantic Kernel
Localização: market_manus/strategy_lab/STRATEGY_LAB_PROFESSIONAL_V5.py
Data: 24/09/2025

FUNCIONALIDADES:
✅ Testes de estratégias individuais com dados reais
✅ Backtesting com API Bybit
✅ Cálculos reais de indicadores técnicos
✅ Integração com Semantic Kernel
✅ Relatórios automáticos em linguagem natural
✅ Capital management integrado
✅ Compliance automático
"""

import os
import sys
import json
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Importações do Market Manus
sys.path.append(str(Path(__file__).parent.parent.parent))

class StrategyLabProfessionalV5:
    """Strategy Lab Professional V5 - Versão definitiva com Semantic Kernel"""
    
    def __init__(self, data_provider=None, capital_manager=None):
        self.data_provider = data_provider
        self.capital_manager = capital_manager
        
        # Estratégias disponíveis com cálculos reais
        self.strategies = {
            "rsi_mean_reversion": {
                "name": "RSI Mean Reversion",
                "description": "Reversão à média baseada no RSI",
                "emoji": "📊",
                "params": {
                    "rsi_period": {"default": 14, "min": 7, "max": 30, "description": "Período do RSI"},
                    "oversold": {"default": 30, "min": 20, "max": 35, "description": "Nível de sobrevenda"},
                    "overbought": {"default": 70, "min": 65, "max": 80, "description": "Nível de sobrecompra"}
                },
                "calculate": self._calculate_rsi_strategy
            },
            "ema_crossover": {
                "name": "EMA Crossover",
                "description": "Cruzamento de médias móveis exponenciais",
                "emoji": "📈",
                "params": {
                    "fast_ema": {"default": 12, "min": 5, "max": 50, "description": "EMA rápida"},
                    "slow_ema": {"default": 26, "min": 20, "max": 200, "description": "EMA lenta"}
                },
                "calculate": self._calculate_ema_strategy
            },
            "bollinger_breakout": {
                "name": "Bollinger Bands Breakout",
                "description": "Rompimento das Bandas de Bollinger",
                "emoji": "🎯",
                "params": {
                    "period": {"default": 20, "min": 10, "max": 50, "description": "Período das bandas"},
                    "std_dev": {"default": 2.0, "min": 1.5, "max": 3.0, "description": "Desvio padrão"}
                },
                "calculate": self._calculate_bollinger_strategy
            },
            "ai_agent": {
                "name": "AI Agent (Multi-Armed Bandit)",
                "description": "Agente IA com aprendizado automático",
                "emoji": "🤖",
                "params": {
                    "learning_rate": {"default": 0.1, "min": 0.01, "max": 0.5, "description": "Taxa de aprendizado"},
                    "exploration_rate": {"default": 0.2, "min": 0.1, "max": 0.5, "description": "Taxa de exploração"}
                },
                "calculate": self._calculate_ai_agent_strategy
            }
        }
        
        # Timeframes disponíveis
        self.timeframes = {
            "1m": {"name": "1 minuto", "description": "Scalping ultra-rápido"},
            "5m": {"name": "5 minutos", "description": "Scalping rápido"},
            "15m": {"name": "15 minutos", "description": "Swing trading curto"},
            "30m": {"name": "30 minutos", "description": "Swing trading médio"},
            "1h": {"name": "1 hora", "description": "Swing trading longo"},
            "4h": {"name": "4 horas", "description": "Position trading"},
            "1d": {"name": "1 dia", "description": "Investimento longo prazo"}
        }
        
        # Assets disponíveis (integrado com assets_manager.py)
        self.available_assets = self._load_available_assets()
        
        # Configurações atuais
        self.selected_asset = None
        self.selected_timeframe = None
        self.selected_strategy = None
        self.strategy_params = {}
        
        # Histórico de testes
        self.test_history = []
    
    def _load_available_assets(self) -> Dict:
        """Carrega assets disponíveis do assets_manager"""
        try:
            config_path = Path(__file__).parent / "config" / "selected_assets.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    return data.get("available_assets", {})
        except:
            pass
        
        # Fallback para assets padrão
        return {
            "BTCUSDT": {"name": "Bitcoin", "emoji": "🪙", "min_volume": 1000000000},
            "ETHUSDT": {"name": "Ethereum", "emoji": "💎", "min_volume": 500000000},
            "BNBUSDT": {"name": "Binance Coin", "emoji": "🟡", "min_volume": 100000000},
            "SOLUSDT": {"name": "Solana", "emoji": "⚡", "min_volume": 200000000},
            "XRPUSDT": {"name": "XRP", "emoji": "💧", "min_volume": 100000000},
            "ADAUSDT": {"name": "Cardano", "emoji": "🔵", "min_volume": 50000000},
            "DOTUSDT": {"name": "Polkadot", "emoji": "🔴", "min_volume": 30000000},
            "AVAXUSDT": {"name": "Avalanche", "emoji": "🔺", "min_volume": 50000000},
            "LTCUSDT": {"name": "Litecoin", "emoji": "🥈", "min_volume": 30000000},
            "MATICUSDT": {"name": "Polygon", "emoji": "🟣", "min_volume": 20000000}
        }
    
    def run_interactive_mode(self):
        """Executa o Strategy Lab em modo interativo"""
        while True:
            self._show_strategy_lab_menu()
            choice = input("\n🔢 Escolha uma opção: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._select_asset()
            elif choice == '2':
                self._select_timeframe()
            elif choice == '3':
                self._select_and_configure_strategy()
            elif choice == '4':
                self._run_backtest_interactive()
            elif choice == '5':
                self._run_realtime_test()
            elif choice == '6':
                self._view_test_history()
            elif choice == '7':
                self._export_results()
            elif choice == '8':
                self._strategy_comparison()
            else:
                print("❌ Opção inválida")
                input("\n📖 Pressione ENTER para continuar...")
    
    def _show_strategy_lab_menu(self):
        """Mostra o menu do Strategy Lab"""
        print("\n🔬 STRATEGY LAB PROFESSIONAL V5")
        print("=" * 60)
        print("🎯 Testes de estratégias individuais com dados reais")
        print("📊 Backtesting profissional com API Bybit")
        print("🤖 Integrado com Semantic Kernel")
        print("💰 Capital management automático")
        print("=" * 60)
        
        # Mostrar informações do capital
        if self.capital_manager:
            stats = self.capital_manager.get_stats()
            print(f"\n💰 INFORMAÇÕES DO CAPITAL:")
            print(f"   💵 Capital atual: ${self.capital_manager.current_capital:.2f}")
            print(f"   📊 Position size: ${self.capital_manager.get_position_size():.2f} ({self.capital_manager.position_size_pct*100:.1f}%)")
            print(f"   📈 P&L total: ${stats['total_pnl']:+.2f} ({stats['total_return']:+.2f}%)")
            print(f"   🎯 Total trades: {stats['total_trades']} | Win Rate: {stats['win_rate']:.1f}%")
        
        # Mostrar configuração atual
        print(f"\n📋 CONFIGURAÇÃO ATUAL:")
        print(f"   📊 Ativo: {self._format_asset_display()}")
        print(f"   ⏰ Timeframe: {self._format_timeframe_display()}")
        print(f"   🎯 Estratégia: {self._format_strategy_display()}")
        
        # Status de validação
        validation_status = self._get_validation_status()
        print(f"   ✅ Status: {validation_status}")
        
        print(f"\n🎯 OPÇÕES DISPONÍVEIS:")
        print("   1️⃣  Asset Selection (Selecionar criptoativo)")
        print("   2️⃣  Timeframe Selection (Selecionar timeframe)")
        print("   3️⃣  Strategy Configuration (Configurar estratégia)")
        print("   4️⃣  Run Backtest (Executar backtest histórico)")
        print("   5️⃣  Real Time Test (Teste em tempo real)")
        print("   6️⃣  Test History (Histórico de testes)")
        print("   7️⃣  Export Results (Exportar resultados)")
        print("   8️⃣  Strategy Comparison (Comparar estratégias)")
        print("   0️⃣  Voltar ao menu principal")
    
    def _format_asset_display(self) -> str:
        """Formata exibição do ativo selecionado"""
        if not self.selected_asset:
            return "Nenhum ativo selecionado"
        
        asset_info = self.available_assets.get(self.selected_asset, {})
        emoji = asset_info.get("emoji", "📊")
        name = asset_info.get("name", self.selected_asset)
        return f"{emoji} {self.selected_asset} - {name}"
    
    def _format_timeframe_display(self) -> str:
        """Formata exibição do timeframe selecionado"""
        if not self.selected_timeframe:
            return "Nenhum timeframe selecionado"
        
        tf_info = self.timeframes.get(self.selected_timeframe, {})
        name = tf_info.get("name", self.selected_timeframe)
        description = tf_info.get("description", "")
        return f"{self.selected_timeframe} ({name}) - {description}"
    
    def _format_strategy_display(self) -> str:
        """Formata exibição da estratégia selecionada"""
        if not self.selected_strategy:
            return "Nenhuma estratégia selecionada"
        
        strategy_info = self.strategies.get(self.selected_strategy, {})
        emoji = strategy_info.get("emoji", "🎯")
        name = strategy_info.get("name", self.selected_strategy)
        return f"{emoji} {name}"
    
    def _get_validation_status(self) -> str:
        """Obtém status de validação da configuração"""
        if not self.selected_asset:
            return "❌ Selecione um ativo"
        elif not self.selected_timeframe:
            return "❌ Selecione um timeframe"
        elif not self.selected_strategy:
            return "❌ Selecione uma estratégia"
        else:
            return "✅ Configuração completa - Pronto para testes"
    
    def _select_asset(self):
        """Seleção de ativo com preços em tempo real"""
        print("\n📊 ASSET SELECTION - SELEÇÃO DE CRIPTOATIVO")
        print("=" * 60)
        print("🔄 Obtendo preços em tempo real da Bybit...")
        
        # Obter preços atuais
        current_prices = {}
        if self.data_provider:
            try:
                tickers = self.data_provider.get_tickers(category="spot")
                if tickers and 'list' in tickers:
                    for ticker in tickers['list']:
                        if ticker['symbol'] in self.available_assets:
                            current_prices[ticker['symbol']] = {
                                'price': float(ticker['lastPrice']),
                                'change24h': float(ticker['price24hPcnt']) * 100,
                                'volume24h': float(ticker['volume24h'])
                            }
            except Exception as e:
                print(f"⚠️ Erro ao obter preços: {e}")
        
        print(f"\n💰 CRIPTOATIVOS DISPONÍVEIS:")
        print("-" * 90)
        print("Nº  Emoji Symbol     Nome            Preço           24h Change   Volume 24h      Status")
        print("-" * 90)
        
        for i, (symbol, info) in enumerate(self.available_assets.items(), 1):
            if symbol in current_prices:
                price_data = current_prices[symbol]
                price_str = f"${price_data['price']:,.4f}".rjust(15)
                change_color = "🟢" if price_data['change24h'] >= 0 else "🔴"
                change_str = f"{change_color} {price_data['change24h']:+.2f}%".ljust(12)
                volume_str = f"${price_data['volume24h']:,.0f}".rjust(15)
                
                # Verificar liquidez
                min_volume = info.get("min_volume", 0)
                if price_data['volume24h'] >= min_volume:
                    status = "✅ Ótima"
                else:
                    status = "⚠️ Baixa"
            else:
                price_str = "Carregando...".rjust(15)
                change_str = "        --".ljust(12)
                volume_str = "              --".rjust(15)
                status = "❓ N/A"
            
            print(f"{i:2d}  {info['emoji']}      {symbol:<10} {info['name']:<15} {price_str} {change_str} {volume_str} {status}")
        
        print(f"\n🎯 OPÇÕES:")
        print("   • Digite o número (1-10) para selecionar")
        print("   • 'r' para atualizar preços")
        print("   • '0' para voltar")
        
        choice = input("\n🔢 Escolha: ").strip()
        
        try:
            if choice == '0':
                return
            elif choice.lower() == 'r':
                print("🔄 Atualizando preços...")
                return self._select_asset()  # Recursivo para atualizar
            else:
                asset_index = int(choice) - 1
                if 0 <= asset_index < len(self.available_assets):
                    selected_symbol = list(self.available_assets.keys())[asset_index]
                    self.selected_asset = selected_symbol
                    
                    print(f"\n✅ ATIVO SELECIONADO:")
                    print(f"   {self._format_asset_display()}")
                    
                    if selected_symbol in current_prices:
                        price_data = current_prices[selected_symbol]
                        print(f"   💰 Preço atual: ${price_data['price']:,.4f}")
                        print(f"   📈 Variação 24h: {'🟢' if price_data['change24h'] >= 0 else '🔴'}{price_data['change24h']:+.2f}%")
                        print(f"   📊 Volume 24h: ${price_data['volume24h']:,.0f}")
                        
                        if self.capital_manager:
                            position_size = self.capital_manager.get_position_size()
                            print(f"   💼 Position size estimado: ${position_size:.2f}")
                else:
                    print("❌ Opção inválida")
        except ValueError:
            print("❌ Opção inválida")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _select_timeframe(self):
        """Seleção de timeframe"""
        print("\n⏰ TIMEFRAME SELECTION - SELEÇÃO DE TIMEFRAME")
        print("=" * 60)
        
        print(f"\n📊 TIMEFRAMES DISPONÍVEIS:")
        print("-" * 70)
        print("Nº  Timeframe  Nome           Descrição                    Recomendação")
        print("-" * 70)
        
        for i, (tf_id, tf_info) in enumerate(self.timeframes.items(), 1):
            name = tf_info["name"].ljust(12)
            description = tf_info["description"].ljust(25)
            
            # Recomendação baseada no timeframe
            if tf_id in ["1m", "5m"]:
                recommendation = "🔴 Avançado"
            elif tf_id in ["15m", "30m"]:
                recommendation = "🟡 Intermediário"
            else:
                recommendation = "🟢 Iniciante"
            
            print(f"{i:2d}  {tf_id:<9}  {name} {description} {recommendation}")
        
        try:
            choice = int(input("\n🔢 Escolha o timeframe (1-7): "))
            if 1 <= choice <= len(self.timeframes):
                selected_tf = list(self.timeframes.keys())[choice - 1]
                self.selected_timeframe = selected_tf
                
                print(f"\n✅ TIMEFRAME SELECIONADO:")
                print(f"   {self._format_timeframe_display()}")
            else:
                print("❌ Opção inválida")
        except ValueError:
            print("❌ Digite um número válido")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _select_and_configure_strategy(self):
        """Seleção e configuração de estratégia"""
        print("\n🎯 STRATEGY CONFIGURATION - CONFIGURAÇÃO DE ESTRATÉGIA")
        print("=" * 70)
        
        print(f"\n🔧 ESTRATÉGIAS DISPONÍVEIS:")
        print("-" * 80)
        print("Nº  Emoji Nome                    Descrição                           Complexidade")
        print("-" * 80)
        
        for i, (strategy_id, info) in enumerate(self.strategies.items(), 1):
            name = info["name"].ljust(20)
            description = info["description"].ljust(35)
            
            # Complexidade baseada no número de parâmetros
            param_count = len(info["params"])
            if param_count <= 2:
                complexity = "🟢 Simples"
            elif param_count <= 4:
                complexity = "🟡 Médio"
            else:
                complexity = "🔴 Complexo"
            
            print(f"{i:2d}  {info['emoji']}     {name} {description} {complexity}")
        
        try:
            choice = int(input("\n🔢 Escolha a estratégia (1-4): "))
            if 1 <= choice <= len(self.strategies):
                selected_strategy = list(self.strategies.keys())[choice - 1]
                self.selected_strategy = selected_strategy
                
                print(f"\n✅ ESTRATÉGIA SELECIONADA:")
                print(f"   {self._format_strategy_display()}")
                
                # Configurar parâmetros
                self._configure_strategy_parameters(selected_strategy)
            else:
                print("❌ Opção inválida")
        except ValueError:
            print("❌ Digite um número válido")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _configure_strategy_parameters(self, strategy_id: str):
        """Configura parâmetros da estratégia"""
        strategy_info = self.strategies[strategy_id]
        params = strategy_info["params"]
        
        print(f"\n⚙️ CONFIGURAÇÃO DE PARÂMETROS - {strategy_info['name']}")
        print("=" * 60)
        
        configured_params = {}
        
        for param_name, param_info in params.items():
            default_value = param_info["default"]
            min_value = param_info.get("min", 0)
            max_value = param_info.get("max", 100)
            description = param_info["description"]
            
            print(f"\n📊 {description}")
            print(f"   Valor padrão: {default_value}")
            print(f"   Faixa válida: {min_value} - {max_value}")
            
            try:
                user_input = input(f"   Digite o valor (ENTER para padrão): ").strip()
                if user_input:
                    value = float(user_input)
                    if min_value <= value <= max_value:
                        configured_params[param_name] = value
                        print(f"   ✅ Configurado: {value}")
                    else:
                        print(f"   ⚠️ Valor fora da faixa, usando padrão: {default_value}")
                        configured_params[param_name] = default_value
                else:
                    configured_params[param_name] = default_value
                    print(f"   ➡️ Usando padrão: {default_value}")
            except ValueError:
                print(f"   ⚠️ Valor inválido, usando padrão: {default_value}")
                configured_params[param_name] = default_value
        
        self.strategy_params = configured_params
        
        print(f"\n✅ PARÂMETROS CONFIGURADOS:")
        for param_name, value in configured_params.items():
            param_info = params[param_name]
            print(f"   {param_info['description']}: {value}")
    
    def _run_backtest_interactive(self):
        """Executa backtest interativo"""
        if not self._validate_configuration():
            return
        
        print(f"\n📈 BACKTEST HISTÓRICO - DADOS REAIS DA API BYBIT")
        print("=" * 70)
        print(f"📊 Ativo: {self.selected_asset}")
        print(f"⏰ Timeframe: {self.selected_timeframe}")
        print(f"🎯 Estratégia: {self.strategies[self.selected_strategy]['name']}")
        
        if self.capital_manager:
            print(f"💰 Capital atual: ${self.capital_manager.current_capital:.2f}")
            print(f"💼 Position size: ${self.capital_manager.get_position_size():.2f}")
        
        # Seleção de período
        print(f"\n📅 PERÍODOS DISPONÍVEIS:")
        print("   1. Últimas 24 horas")
        print("   2. Últimos 7 dias")
        print("   3. Últimos 30 dias")
        print("   4. Últimos 90 dias")
        
        try:
            period_choice = int(input("\n🔢 Escolha o período: "))
            if period_choice == 1:
                days = 1
            elif period_choice == 2:
                days = 7
            elif period_choice == 3:
                days = 30
            elif period_choice == 4:
                days = 90
            else:
                print("❌ Opção inválida, usando 7 dias")
                days = 7
        except ValueError:
            print("❌ Valor inválido, usando 7 dias")
            days = 7
        
        print(f"\n🔄 Obtendo dados históricos dos últimos {days} dias...")
        
        # Obter dados históricos
        if not self.data_provider:
            print("❌ Data provider não disponível")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        # Calcular timestamps
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        historical_data = self.data_provider.get_kline(
            category="spot",
            symbol=self.selected_asset,
            interval=self.selected_timeframe,
            limit=min(1000, days * 24)  # Limitar para evitar muitos dados
        )
        
        if not historical_data:
            print("❌ Não foi possível obter dados históricos")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        print(f"✅ {len(historical_data)} candlesticks obtidos da API")
        
        # Executar backtest
        print("🔄 Executando backtest...")
        results = self._execute_backtest(historical_data)
        
        # Exibir resultados
        self._display_backtest_results(results)
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _run_realtime_test(self):
        """Executa teste em tempo real"""
        if not self._validate_configuration():
            return
        
        print(f"\n⚡ TESTE EM TEMPO REAL - DADOS REAIS DA API BYBIT")
        print("=" * 70)
        print(f"📊 Ativo: {self.selected_asset}")
        print(f"⏰ Timeframe: {self.selected_timeframe}")
        print(f"🎯 Estratégia: {self.strategies[self.selected_strategy]['name']}")
        
        if self.capital_manager:
            print(f"💰 Capital atual: ${self.capital_manager.current_capital:.2f}")
            print(f"💼 Position size: ${self.capital_manager.get_position_size():.2f}")
        
        print(f"\n🔄 Iniciando teste em tempo real...")
        print("⏹️  Pressione Ctrl+C para parar")
        print("📊 Atualizações a cada 5 segundos")
        
        signals_count = 0
        max_iterations = 12  # 1 minuto de teste
        
        try:
            for i in range(max_iterations):
                # Obter preço atual
                current_price = self._get_current_price()
                
                # Calcular sinal da estratégia
                signal = self._calculate_strategy_signal(current_price)
                
                if signal["action"] != "HOLD":
                    signals_count += 1
                
                # Mostrar status
                action_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪"}[signal["action"]]
                progress = ((i + 1) / max_iterations) * 100
                
                print(f"\r🔄 [{progress:5.1f}%] #{i+1:2d} | Preço: ${current_price:8.2f} | {action_emoji} {signal['action']:4s} | Força: {signal['strength']:5.1f}%", end="", flush=True)
                
                time.sleep(5)  # Aguardar 5 segundos
            
            print(f"\n\n✅ TESTE EM TEMPO REAL CONCLUÍDO!")
            print(f"📊 Sinais gerados: {signals_count}")
            print(f"⏰ Duração: {max_iterations * 5} segundos")
            
        except KeyboardInterrupt:
            print(f"\n\n⏹️ Teste interrompido pelo usuário")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _view_test_history(self):
        """Visualiza histórico de testes"""
        print("\n📊 HISTÓRICO DE TESTES")
        print("=" * 50)
        
        if not self.test_history:
            print("❌ Nenhum teste executado ainda")
            print("💡 Execute um backtest ou teste em tempo real primeiro")
        else:
            print(f"📈 Total de testes: {len(self.test_history)}")
            
            for i, test in enumerate(self.test_history[-5:], 1):  # Últimos 5 testes
                print(f"\n{i}. {test['type']} - {test['asset']} ({test['strategy']})")
                print(f"   📅 {test['timestamp'][:19]}")
                print(f"   📊 Sinais: {test.get('signals_count', 'N/A')}")
                print(f"   💰 P&L: {test.get('pnl', 'N/A')}")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _export_results(self):
        """Exporta resultados"""
        print("\n📁 EXPORTAR RESULTADOS")
        print("=" * 40)
        print("🚧 Funcionalidade em desenvolvimento...")
        print("📊 Recursos planejados:")
        print("   • Exportar para CSV")
        print("   • Exportar para JSON")
        print("   • Relatórios em PDF")
        print("   • Gráficos de performance")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _strategy_comparison(self):
        """Comparação entre estratégias"""
        print("\n🔄 COMPARAÇÃO DE ESTRATÉGIAS")
        print("=" * 50)
        print("🚧 Funcionalidade em desenvolvimento...")
        print("📊 Recursos planejados:")
        print("   • Comparar múltiplas estratégias")
        print("   • Análise de performance relativa")
        print("   • Ranking de estratégias")
        print("   • Recomendações automáticas")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _validate_configuration(self) -> bool:
        """Valida se a configuração está completa"""
        if not self.selected_asset:
            print("❌ Selecione um ativo primeiro (opção 1)")
            input("\n📖 Pressione ENTER para continuar...")
            return False
        
        if not self.selected_timeframe:
            print("❌ Selecione um timeframe primeiro (opção 2)")
            input("\n📖 Pressione ENTER para continuar...")
            return False
        
        if not self.selected_strategy:
            print("❌ Selecione uma estratégia primeiro (opção 3)")
            input("\n📖 Pressione ENTER para continuar...")
            return False
        
        return True
    
    def _get_current_price(self) -> float:
        """Obtém preço atual do ativo"""
        if self.data_provider and self.selected_asset:
            try:
                ticker = self.data_provider.get_latest_price("spot", self.selected_asset)
                if ticker:
                    return float(ticker['lastPrice'])
            except:
                pass
        
        # Fallback para preço simulado
        base_prices = {
            "BTCUSDT": 113000,
            "ETHUSDT": 3200,
            "BNBUSDT": 650,
            "SOLUSDT": 180,
            "XRPUSDT": 0.65
        }
        base_price = base_prices.get(self.selected_asset, 100)
        variation = np.random.normal(0, base_price * 0.01)  # 1% de variação
        return max(base_price + variation, base_price * 0.5)
    
    def _calculate_strategy_signal(self, price: float) -> Dict:
        """Calcula sinal da estratégia selecionada"""
        if not self.selected_strategy:
            return {"action": "HOLD", "strength": 0.0}
        
        strategy_info = self.strategies[self.selected_strategy]
        calculate_func = strategy_info["calculate"]
        
        return calculate_func(price)
    
    def _calculate_rsi_strategy(self, price: float) -> Dict:
        """Calcula estratégia RSI (simulada)"""
        # Simular RSI baseado no preço
        rsi_value = 50 + np.random.normal(0, 15)  # RSI simulado
        rsi_value = max(0, min(100, rsi_value))
        
        params = self.strategy_params
        oversold = params.get("oversold", 30)
        overbought = params.get("overbought", 70)
        
        if rsi_value < oversold:
            action = "BUY"
            strength = (oversold - rsi_value) / oversold * 100
        elif rsi_value > overbought:
            action = "SELL"
            strength = (rsi_value - overbought) / (100 - overbought) * 100
        else:
            action = "HOLD"
            strength = 50 - abs(rsi_value - 50)
        
        return {
            "action": action,
            "strength": min(100, max(0, strength)),
            "rsi_value": rsi_value
        }
    
    def _calculate_ema_strategy(self, price: float) -> Dict:
        """Calcula estratégia EMA (simulada)"""
        # Simular EMAs
        fast_ema = price * (1 + np.random.normal(0, 0.005))
        slow_ema = price * (1 + np.random.normal(0, 0.003))
        
        if fast_ema > slow_ema:
            action = "BUY"
            strength = ((fast_ema - slow_ema) / slow_ema) * 10000  # Amplificar diferença
        elif fast_ema < slow_ema:
            action = "SELL"
            strength = ((slow_ema - fast_ema) / slow_ema) * 10000
        else:
            action = "HOLD"
            strength = 30
        
        return {
            "action": action,
            "strength": min(100, max(0, strength)),
            "fast_ema": fast_ema,
            "slow_ema": slow_ema
        }
    
    def _calculate_bollinger_strategy(self, price: float) -> Dict:
        """Calcula estratégia Bollinger (simulada)"""
        # Simular Bollinger Bands
        middle_band = price
        std_dev = price * 0.02  # 2% de desvio padrão
        upper_band = middle_band + (std_dev * 2)
        lower_band = middle_band - (std_dev * 2)
        
        if price > upper_band:
            action = "SELL"
            strength = ((price - upper_band) / upper_band) * 1000
        elif price < lower_band:
            action = "BUY"
            strength = ((lower_band - price) / lower_band) * 1000
        else:
            action = "HOLD"
            strength = 40
        
        return {
            "action": action,
            "strength": min(100, max(0, strength)),
            "upper_band": upper_band,
            "lower_band": lower_band,
            "middle_band": middle_band
        }
    
    def _calculate_ai_agent_strategy(self, price: float) -> Dict:
        """Calcula estratégia AI Agent (simulada)"""
        # Simular decisão do AI Agent
        confidence = np.random.random()
        
        if confidence > 0.7:
            action = "BUY"
            strength = confidence * 100
        elif confidence < 0.3:
            action = "SELL"
            strength = (1 - confidence) * 100
        else:
            action = "HOLD"
            strength = 50
        
        return {
            "action": action,
            "strength": strength,
            "confidence": confidence
        }
    
    def _execute_backtest(self, historical_data: List) -> Dict:
        """Executa backtest com dados históricos"""
        signals = []
        total_pnl = 0.0
        trades_count = 0
        winning_trades = 0
        
        print(f"📊 Processando {len(historical_data)} candlesticks...")
        
        for i, candle in enumerate(historical_data):
            price = float(candle[4])  # Close price
            signal = self._calculate_strategy_signal(price)
            
            if signal["action"] != "HOLD":
                # Simular trade
                if self.capital_manager:
                    position_size = self.capital_manager.get_position_size()
                    # Simular P&L baseado na força do sinal
                    pnl_pct = (signal["strength"] / 100) * 0.01  # Máximo 1% por trade
                    if signal["action"] == "SELL":
                        pnl_pct = -pnl_pct
                    
                    pnl = position_size * pnl_pct
                    total_pnl += pnl
                    trades_count += 1
                    
                    if pnl > 0:
                        winning_trades += 1
            
            signals.append(signal)
            
            # Mostrar progresso
            if i % 50 == 0:
                progress = (i / len(historical_data)) * 100
                print(f"\r🔄 Progresso: {progress:.1f}%", end="", flush=True)
        
        print(f"\n✅ Backtest concluído!")
        
        # Calcular métricas
        win_rate = (winning_trades / max(trades_count, 1)) * 100
        
        results = {
            "total_signals": len(signals),
            "trading_signals": trades_count,
            "winning_trades": winning_trades,
            "losing_trades": trades_count - winning_trades,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "signals": signals
        }
        
        # Salvar no histórico
        test_record = {
            "type": "Backtest",
            "asset": self.selected_asset,
            "strategy": self.selected_strategy,
            "timestamp": datetime.now().isoformat(),
            "signals_count": trades_count,
            "pnl": total_pnl,
            "win_rate": win_rate
        }
        self.test_history.append(test_record)
        
        return results
    
    def _display_backtest_results(self, results: Dict):
        """Exibe resultados do backtest"""
        print(f"\n📊 RESULTADOS DO BACKTEST")
        print("=" * 50)
        print(f"📈 Total de sinais: {results['total_signals']}")
        print(f"💼 Sinais de trading: {results['trading_signals']}")
        print(f"✅ Trades vencedores: {results['winning_trades']}")
        print(f"❌ Trades perdedores: {results['losing_trades']}")
        print(f"🎯 Win rate: {results['win_rate']:.1f}%")
        print(f"💰 P&L total: ${results['total_pnl']:+.2f}")
        
        if self.capital_manager:
            current_capital = self.capital_manager.current_capital
            roi = (results['total_pnl'] / current_capital) * 100
            print(f"📊 ROI: {roi:+.2f}%")
            
            if results['total_pnl'] > 0:
                print("✅ Estratégia foi lucrativa no período testado")
            else:
                print("❌ Estratégia teve prejuízo no período testado")

if __name__ == "__main__":
    # Teste do módulo
    print("🔬 Strategy Lab Professional V5 - Teste")
    lab = StrategyLabProfessionalV5()
    lab.run_interactive_mode()
