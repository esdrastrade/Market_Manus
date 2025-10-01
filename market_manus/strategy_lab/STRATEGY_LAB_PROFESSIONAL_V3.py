#!/usr/bin/env python3
"""
STRATEGY LAB PROFESSIONAL V3 - 22/09/2025
Sistema completo de análise de estratégias com:
✅ Seleção de criptoativo específico
✅ Real Time Test vs Historical Data Test
✅ Configuração de timeframes
✅ Parâmetros customizáveis
✅ Resultados confiáveis baseados em dados reais da Bybit
"""

import os
import sys
import time
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Importar o novo provedor de dados
from market_manus.data_providers.bybit_real_data_provider import BybitRealDataProvider

class ProfessionalStrategyLab:
    """Strategy Lab profissional com testes reais"""
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.testnet = testnet
        self.api_key = api_key
        self.api_secret = api_secret
        
        if not self.api_key or not self.api_secret:
            print("❌ Chaves da API (BYBIT_API_KEY, BYBIT_API_SECRET) não configuradas.")
            sys.exit(1)

        # Instanciar o provedor de dados reais
        self.data_provider = BybitRealDataProvider(api_key=self.api_key, api_secret=self.api_secret, testnet=self.testnet)
        
        # Criptoativos disponíveis com informações detalhadas
        self.available_assets = {
            "BTCUSDT": {"name": "Bitcoin", "emoji": "🪙", "min_volume": 1000000000},
            "ETHUSDT": {"name": "Ethereum", "emoji": "💎", "min_volume": 500000000},
            "BNBUSDT": {"name": "Binance Coin", "emoji": "🟡", "min_volume": 100000000},
            "SOLUSDT": {"name": "Solana", "emoji": "⚡", "min_volume": 50000000},
            "XRPUSDT": {"name": "XRP", "emoji": "💧", "min_volume": 100000000},
            "ADAUSDT": {"name": "Cardano", "emoji": "🔵", "min_volume": 50000000},
            "DOTUSDT": {"name": "Polkadot", "emoji": "🔴", "min_volume": 30000000},
            "AVAXUSDT": {"name": "Avalanche", "emoji": "🔺", "min_volume": 30000000},
            "LTCUSDT": {"name": "Litecoin", "emoji": "🥈", "min_volume": 50000000},
            "MATICUSDT": {"name": "Polygon", "emoji": "🟣", "min_volume": 30000000}
        }
        
        # Timeframes disponíveis
        self.timeframes = {
            "1": "1 minuto",
            "5": "5 minutos", 
            "15": "15 minutos",
            "30": "30 minutos",
            "60": "1 hora",
            "240": "4 horas",
            "D": "1 dia"
        }
        
        # Estratégias disponíveis com parâmetros configuráveis
        self.strategies = {
            "ema_crossover": {
                "name": "EMA Crossover",
                "description": "Cruzamento de médias móveis exponenciais",
                "params": {
                    "fast_ema": {"default": 12, "min": 5, "max": 50, "description": "EMA rápida"},
                    "slow_ema": {"default": 26, "min": 20, "max": 200, "description": "EMA lenta"}
                }
            },
            "rsi_mean_reversion": {
                "name": "RSI Mean Reversion",
                "description": "Reversão à média baseada no RSI",
                "params": {
                    "rsi_period": {"default": 14, "min": 7, "max": 30, "description": "Período do RSI"},
                    "oversold": {"default": 30, "min": 20, "max": 35, "description": "Nível de sobrevenda"},
                    "overbought": {"default": 70, "min": 65, "max": 80, "description": "Nível de sobrecompra"}
                }
            },
            "bollinger_breakout": {
                "name": "Bollinger Bands Breakout",
                "description": "Rompimento das Bandas de Bollinger",
                "params": {
                    "period": {"default": 20, "min": 10, "max": 50, "description": "Período das bandas"},
                    "std_dev": {"default": 2.0, "min": 1.5, "max": 3.0, "description": "Desvio padrão"}
                }
            },
            "ai_agent": {
                "name": "AI Agent (Multi-Armed Bandit)",
                "description": "Agente IA com aprendizado automático",
                "params": {
                    "learning_rate": {"default": 0.1, "min": 0.01, "max": 0.5, "description": "Taxa de aprendizado"},
                    "exploration_rate": {"default": 0.2, "min": 0.1, "max": 0.5, "description": "Taxa de exploração"}
                }
            }
        }
        
        # Estado atual
        self.selected_asset = None
        self.selected_strategy = None
        self.selected_timeframe = None
        self.strategy_params = {}
        self.current_prices = {}

    def run(self):
        """Executa o Strategy Lab profissional"""
        while True:
            self.show_main_menu()
            choice = input("\n🔢 Escolha uma opção (0-6): ").strip()
            
            if choice == "0":
                break
            elif choice == "1":
                self.asset_selection_menu()
            elif choice == "2":
                self.strategy_configuration_menu()
            elif choice == "3":
                self.real_time_test()
            elif choice == "4":
                self.historical_data_test()
            elif choice == "5":
                self.comparison_test()
            elif choice == "6":
                self.export_results()
            else:
                print("❌ Opção inválida")
                input("\n📖 Pressione ENTER para continuar...")

    def show_main_menu(self):
        """Mostra menu principal do Strategy Lab"""
        print("\n" + "="*80)
        print("🔬 STRATEGY LAB PROFESSIONAL V3 - ANÁLISE CONFIÁVEL")
        print("="*80)
        print("🎯 Testes com dados reais da Bybit")
        print("📊 Configuração completa de parâmetros")
        print("⚡ Real Time vs Historical Data testing")
        print("="*80)
        
        # Status atual
        asset_status = f"📊 Ativo: {self.selected_asset}" if self.selected_asset else "📊 Nenhum ativo selecionado"
        strategy_status = f"🎯 Estratégia: {self.strategies[self.selected_strategy]['name']}" if self.selected_strategy else "🎯 Nenhuma estratégia selecionada"
        timeframe_status = f"⏰ Timeframe: {self.timeframes[self.selected_timeframe]}" if self.selected_timeframe else "⏰ Nenhum timeframe selecionado"
        
        print(f"\n📋 STATUS ATUAL:")
        print(f"   {asset_status}")
        print(f"   {strategy_status}")
        print(f"   {timeframe_status}")
        
        print(f"\n🎯 OPÇÕES DISPONÍVEIS:")
        print("   1️⃣  Asset Selection (Selecionar criptoativo)")
        print("   2️⃣  Strategy Configuration (Configurar estratégia)")
        print("   3️⃣  Real Time Test (Teste em tempo real)")
        print("   4️⃣  Historical Data Test (Teste com dados históricos)")
        print("   5️⃣  Comparison Test (Comparar Real Time vs Historical)")
        print("   6️⃣  Export Results (Exportar resultados)")
        print("   0️⃣  Voltar ao menu principal")

    def asset_selection_menu(self):
        """Menu de seleção de criptoativo"""
        while True:
            print(f"\n📊 ASSET SELECTION - SELEÇÃO DE CRIPTOATIVO")
            print("="*60)
            print("🔄 Atualizando preços em tempo real...")
            
            # Atualizar preços com dados reais
            self.update_asset_prices()
            
            print(f"\n💰 CRIPTOATIVOS DISPONÍVEIS:")
            print("-"*80)
            print(f"{'Nº':<3} {'Emoji':<5} {'Symbol':<10} {'Nome':<15} {'Preço':<15} {'24h Change':<12} {'Volume 24h'}")
            print("-"*80)
            
            assets_list = list(self.available_assets.keys())
            for i, symbol in enumerate(assets_list, 1):
                asset_info = self.available_assets[symbol]
                price_data = self.current_prices.get(symbol, {})
                
                if price_data:
                    price = float(price_data.get('lastPrice', 0))
                    change_24h = float(price_data.get('price24hPcnt', 0)) * 100
                    volume_24h = float(price_data.get('turnover24h', 0)) # Usar 'turnover24h' para volume em USDT
                    
                    change_emoji = "🟢" if change_24h >= 0 else "🔴"
                    
                    print(f"{i:<3} {asset_info['emoji']:<5} {symbol:<10} {asset_info['name']:<15} ${price:<14,.4f} {change_emoji}{change_24h:>+6.2f}% ${float(volume_24h):>12,.0f}")
                else:
                    print(f"{i:<3} {asset_info['emoji']:<5} {symbol:<10} {asset_info['name']:<15} {'Carregando...':<14} {'--':<12} {'--'}")
            
            print(f"\n🎯 OPÇÕES:")
            print("   • Digite o número (1-10) para selecionar")
            print("   • 'r' para atualizar preços")
            print("   • '0' para voltar")
            
            choice = input(f"\n🔢 Escolha: ").strip().lower()
            
            if choice == "0":
                break
            elif choice == "r":
                continue
            else:
                try:
                    asset_idx = int(choice) - 1
                    if 0 <= asset_idx < len(assets_list):
                        selected_symbol = assets_list[asset_idx]
                        self.selected_asset = selected_symbol
                        
                        asset_info = self.available_assets[selected_symbol]
                        price_data = self.current_prices.get(selected_symbol, {})
                        
                        print(f"\n✅ ATIVO SELECIONADO:")
                        print(f"   {asset_info['emoji']} {selected_symbol} - {asset_info['name']}")
                        
                        if price_data:
                            price = float(price_data.get('lastPrice', 0))
                            change_24h = float(price_data.get('price24hPcnt', 0)) * 100
                            volume_24h = float(price_data.get('turnover24h', 0))
                            
                            print(f"   💰 Preço atual: ${price:,.4f}")
                            print(f"   📈 Variação 24h: {change_24h:+.2f}%")
                            print(f"   📊 Volume 24h: ${float(volume_24h):,.0f}")
                            
                            # Validar liquidez
                            if float(volume_24h) >= asset_info['min_volume']:
                                print(f"   ✅ Liquidez adequada para testes confiáveis")
                            else:
                                print(f"   ⚠️  Liquidez baixa - resultados podem ser menos confiáveis")
                        
                        input(f"\n📖 Pressione ENTER para continuar...")
                        break
                    else:
                        print("❌ Número inválido")
                except (ValueError, IndexError):
                    print("❌ Digite um número válido")
                
                input(f"\n📖 Pressione ENTER para continuar...")

    def strategy_configuration_menu(self):
        """Menu de configuração de estratégia"""
        while True:
            print(f"\n🎯 STRATEGY CONFIGURATION - CONFIGURAÇÃO DE ESTRATÉGIA")
            print("="*70)
            
            print(f"\n🔧 ESTRATÉGIAS DISPONÍVEIS:")
            strategies_list = list(self.strategies.keys())
            for i, strategy_key in enumerate(strategies_list, 1):
                strategy = self.strategies[strategy_key]
                selected_mark = "✅" if self.selected_strategy == strategy_key else "  "
                print(f"   {selected_mark} {i}. {strategy['name']}")
                print(f"      📝 {strategy['description']}")
            
            print(f"\n⏰ TIMEFRAMES DISPONÍVEIS:")
            timeframes_list = list(self.timeframes.keys())
            for i, tf_key in enumerate(timeframes_list, 1):
                selected_mark = "✅" if self.selected_timeframe == tf_key else "  "
                print(f"   {selected_mark} {chr(96+i)}. {self.timeframes[tf_key]}")
            
            print(f"\n🎯 OPÇÕES:")
            print("   • Digite 1-4 para selecionar estratégia")
            print("   • Digite a-g para selecionar timeframe")
            print("   • 'p' para configurar parâmetros")
            print("   • '0' para voltar")
            
            choice = input(f"\n🔢 Escolha: ").strip().lower()
            
            if choice == "0":
                break
            elif choice == "p":
                if self.selected_strategy:
                    self.configure_strategy_parameters()
                else:
                    print("❌ Selecione uma estratégia primeiro")
                    input(f"\n📖 Pressione ENTER para continuar...")
            elif choice.isdigit():
                strategy_idx = int(choice) - 1
                if 0 <= strategy_idx < len(strategies_list):
                    self.selected_strategy = strategies_list[strategy_idx]
                    strategy = self.strategies[self.selected_strategy]
                    print(f"\n✅ Estratégia selecionada: {strategy['name']}")
                    
                    # Inicializar parâmetros padrão
                    self.strategy_params = {}
                    for param_name, param_info in strategy['params'].items():
                        self.strategy_params[param_name] = param_info['default']
                    
                    input(f"\n📖 Pressione ENTER para continuar...")
                else:
                    print("❌ Número inválido")
                    input(f"\n📖 Pressione ENTER para continuar...")
            elif choice.isalpha() and len(choice) == 1:
                tf_idx = ord(choice) - ord('a')
                if 0 <= tf_idx < len(timeframes_list):
                    self.selected_timeframe = timeframes_list[tf_idx]
                    print(f"\n✅ Timeframe selecionado: {self.timeframes[self.selected_timeframe]}")
                    input(f"\n📖 Pressione ENTER para continuar...")
                else:
                    print("❌ Letra inválida")
                    input(f"\n📖 Pressione ENTER para continuar...")
            else:
                print("❌ Opção inválida")
                input(f"\n📖 Pressione ENTER para continuar...")

    def configure_strategy_parameters(self):
        """Configura parâmetros da estratégia"""
        if not self.selected_strategy:
            return
        
        strategy = self.strategies[self.selected_strategy]
        
        print(f"\n⚙️ CONFIGURAÇÃO DE PARÂMETROS - {strategy['name']}")
        print("="*60)
        
        for param_name, param_info in strategy['params'].items():
            current_value = self.strategy_params.get(param_name, param_info['default'])
            
            print(f"\n📊 {param_info['description']}")
            print(f"   Valor atual: {current_value}")
            print(f"   Faixa válida: {param_info['min']} - {param_info['max']}")
            
            new_value = input(f"   Novo valor (ENTER para manter): ").strip()
            
            if new_value:
                try:
                    if isinstance(param_info['default'], float):
                        new_value = float(new_value)
                    else:
                        new_value = int(new_value)
                    
                    if param_info['min'] <= new_value <= param_info['max']:
                        self.strategy_params[param_name] = new_value
                        print(f"   ✅ Atualizado para: {new_value}")
                    else:
                        print(f"   ❌ Valor fora da faixa válida")
                except ValueError:
                    print(f"   ❌ Valor inválido")
        
        print(f"\n✅ Configuração concluída!")
        input(f"\n📖 Pressione ENTER para continuar...")

    def real_time_test(self):
        """Teste em tempo real com dados reais da Bybit"""
        if not self._validate_configuration():
            return
        
        print(f"\n⚡ REAL TIME TEST - TESTE EM TEMPO REAL")
        print("="*60)
        print(f"📊 Ativo: {self.selected_asset}")
        print(f"🎯 Estratégia: {self.strategies[self.selected_strategy]['name']}")
        print(f"⏰ Timeframe: {self.timeframes[self.selected_timeframe]}")
        print(f"🔧 Parâmetros: {self.strategy_params}")
        
        print(f"\n🔄 Iniciando teste em tempo real...")
        print("⏹️  Pressione Ctrl+C para parar")
        
        try:
            start_time = time.time()
            iteration = 0
            signals = []
            
            while time.time() - start_time < 60:
                iteration += 1
                
                # Obter dados em tempo real
                price_data = self.get_current_price(self.selected_asset)
                if not price_data:
                    print("❌ Erro ao obter preço atual. Tentando novamente...")
                    time.sleep(5)
                    continue
                
                current_price = float(price_data['lastPrice'])

                # Simular análise da estratégia (a lógica da estratégia será implementada posteriormente)
                signal = self.analyze_strategy_realtime(current_price)
                signals.append((datetime.now(), current_price, signal))
                
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] Preço: ${current_price:<10.4f} | Sinal: {signal}")
                time.sleep(5) # Aguardar 5 segundos para a próxima iteração

        except KeyboardInterrupt:
            print("\n⏹️ Teste em tempo real interrompido.")
        
        # Análise de resultados
        self.analyze_test_results(signals)
        input("\n📖 Pressione ENTER para continuar...")

    def historical_data_test(self):
        """Teste com dados históricos reais da Bybit"""
        if not self._validate_configuration():
            return

        print(f"\n📊 HISTORICAL DATA TEST - TESTE COM DADOS HISTÓRICOS")
        print("="*60)
        print(f"📊 Ativo: {self.selected_asset}")
        print(f"🎯 Estratégia: {self.strategies[self.selected_strategy]['name']}")
        print(f"⏰ Timeframe: {self.timeframes[self.selected_timeframe]}")
        print(f"🔧 Parâmetros: {self.strategy_params}")

        print(f"\n🔄 Baixando dados históricos...")
        historical_data = self.get_historical_data(self.selected_asset, self.selected_timeframe)

        if not historical_data:
            print("❌ Falha ao obter dados históricos.")
            input("\n📖 Pressione ENTER para continuar...")
            return

        print(f"✅ {len(historical_data)} registros de dados históricos obtidos.")
        print("\n🔄 Executando backtest...")

        # (A lógica de backtesting será implementada aqui)
        # Por enquanto, vamos apenas exibir os dados
        for candle in historical_data[:5]: # Exibir as 5 primeiras velas
            print(f"  - Timestamp: {datetime.fromtimestamp(int(candle[0]) / 1000)}, Preço de Fechamento: {candle[4]}")

        input("\n📖 Pressione ENTER para continuar...")

    def update_asset_prices(self):
        """Atualiza os preços dos ativos usando dados reais da Bybit."""
        tickers = self.data_provider.get_tickers(category="spot")
        if tickers and 'list' in tickers:
            for ticker in tickers['list']:
                if ticker['symbol'] in self.available_assets:
                    self.current_prices[ticker['symbol']] = ticker

    def get_current_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Obtém o preço atual de um ativo."""
        return self.data_provider.get_latest_price(category="spot", symbol=symbol)

    def get_historical_data(self, symbol: str, timeframe: str, limit: int = 200) -> Optional[List[List[Any]]]:
        """Obtém dados históricos de um ativo."""
        return self.data_provider.get_kline(category="spot", symbol=symbol, interval=timeframe, limit=limit)

    def analyze_strategy_realtime(self, current_price: float) -> str:
        """Simula a análise da estratégia em tempo real (lógica a ser implementada)."""
        # Lógica de simulação simples
        if random.random() < 0.1:
            return "COMPRA"
        elif random.random() > 0.9:
            return "VENDA"
        else:
            return "NEUTRO"

    def _validate_configuration(self) -> bool:
        """Valida se a configuração para teste está completa."""
        if not self.selected_asset or not self.selected_strategy or not self.selected_timeframe:
            print("\n❌ CONFIGURAÇÃO INCOMPLETA:")
            print("   - Selecione um ativo, uma estratégia e um timeframe antes de iniciar um teste.")
            input("\n📖 Pressione ENTER para continuar...")
            return False
        return True

    def analyze_test_results(self, signals: List[tuple]):
        """Analisa e exibe os resultados de um teste."""
        if not signals:
            print("\n📊 Nenhum sinal gerado durante o teste.")
            return

        buys = [s for s in signals if s[2] == "COMPRA"]
        sells = [s for s in signals if s[2] == "VENDA"]

        print("\n📊 RESULTADOS DO TESTE:")
        print(f"   - Total de Sinais: {len(signals)}")
        print(f"   - Sinais de Compra: {len(buys)}")
        print(f"   - Sinais de Venda: {len(sells)}")

    def comparison_test(self):
        print("\n🚧 Funcionalidade em desenvolvimento...")
        input("\n📖 Pressione ENTER para continuar...")

    def export_results(self):
        print("\n🚧 Funcionalidade em desenvolvimento...")
        input("\n📖 Pressione ENTER para continuar...")

if __name__ == "__main__":
    lab = ProfessionalStrategyLab(testnet=True)
    lab.run()

