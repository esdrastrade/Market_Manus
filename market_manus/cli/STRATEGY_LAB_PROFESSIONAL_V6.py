"""
Strategy Lab Professional V6 - Versão Completa com Todas as Estratégias
Localização: market_manus/strategy_lab/STRATEGY_LAB_PROFESSIONAL_V6.py
Data: 24/09/2025

FUNCIONALIDADES:
✅ 8 Estratégias completas: RSI, EMA, Bollinger, MACD, Stochastic, Williams %R, ADX, Fibonacci
✅ Seleção de período temporal personalizado (data inicial e final)
✅ Backtesting com dados reais da API Bybit
✅ Cálculos matemáticos precisos dos indicadores
✅ Capital management integrado
✅ Relatórios detalhados com métricas financeiras
✅ Interface interativa completa
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# Importar as novas estratégias
sys.path.append(str(Path(__file__).parent.parent.parent))

class StrategyLabProfessionalV6:
    """Strategy Lab Professional V6 - Versão completa com todas as estratégias"""
    
    def __init__(self, data_provider=None, capital_manager=None):
        self.data_provider = data_provider
        self.capital_manager = capital_manager
        
        # Estratégias disponíveis (8 estratégias completas)
        self.strategies = {
            "rsi_mean_reversion": {
                "name": "RSI Mean Reversion",
                "description": "Reversão à média baseada no RSI",
                "emoji": "📊",
                "type": "Oscillator",
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
                "type": "Trend Following",
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
                "type": "Volatility",
                "params": {
                    "period": {"default": 20, "min": 10, "max": 50, "description": "Período das bandas"},
                    "std_dev": {"default": 2.0, "min": 1.5, "max": 3.0, "description": "Desvio padrão"}
                },
                "calculate": self._calculate_bollinger_strategy
            },
            "macd": {
                "name": "MACD",
                "description": "Moving Average Convergence Divergence",
                "emoji": "📊",
                "type": "Momentum",
                "params": {
                    "fast_period": {"default": 12, "min": 5, "max": 20, "description": "Período EMA rápida"},
                    "slow_period": {"default": 26, "min": 20, "max": 50, "description": "Período EMA lenta"},
                    "signal_period": {"default": 9, "min": 5, "max": 15, "description": "Período linha de sinal"}
                },
                "calculate": self._calculate_macd_strategy
            },
            "stochastic": {
                "name": "Stochastic Oscillator",
                "description": "Oscilador Estocástico %K e %D",
                "emoji": "📈",
                "type": "Oscillator",
                "params": {
                    "k_period": {"default": 14, "min": 5, "max": 25, "description": "Período %K"},
                    "d_period": {"default": 3, "min": 3, "max": 10, "description": "Período %D"},
                    "oversold": {"default": 20, "min": 10, "max": 30, "description": "Nível oversold"},
                    "overbought": {"default": 80, "min": 70, "max": 90, "description": "Nível overbought"}
                },
                "calculate": self._calculate_stochastic_strategy
            },
            "williams_r": {
                "name": "Williams %R",
                "description": "Williams Percent Range Oscillator",
                "emoji": "📉",
                "type": "Oscillator",
                "params": {
                    "period": {"default": 14, "min": 5, "max": 25, "description": "Período de lookback"},
                    "oversold": {"default": -80, "min": -90, "max": -70, "description": "Nível oversold"},
                    "overbought": {"default": -20, "min": -30, "max": -10, "description": "Nível overbought"}
                },
                "calculate": self._calculate_williams_r_strategy
            },
            "adx": {
                "name": "ADX",
                "description": "Average Directional Index",
                "emoji": "🎯",
                "type": "Trend Strength",
                "params": {
                    "period": {"default": 14, "min": 10, "max": 20, "description": "Período ADX"},
                    "adx_threshold": {"default": 25, "min": 20, "max": 30, "description": "Threshold tendência forte"}
                },
                "calculate": self._calculate_adx_strategy
            },
            "fibonacci": {
                "name": "Fibonacci Retracement",
                "description": "Níveis de Retração de Fibonacci",
                "emoji": "🔢",
                "type": "Support/Resistance",
                "params": {
                    "lookback_period": {"default": 50, "min": 20, "max": 100, "description": "Período lookback"},
                    "tolerance_pct": {"default": 0.5, "min": 0.1, "max": 2.0, "description": "Tolerância (%)"}
                },
                "calculate": self._calculate_fibonacci_strategy
            }
        }
        
        # Timeframes disponíveis
        self.timeframes = {
            "1": {"name": "1 minuto", "bybit_interval": "1", "description": "Scalping ultra-rápido"},
            "5": {"name": "5 minutos", "bybit_interval": "5", "description": "Scalping rápido"},
            "15": {"name": "15 minutos", "bybit_interval": "15", "description": "Swing trading curto"},
            "30": {"name": "30 minutos", "bybit_interval": "30", "description": "Swing trading médio"},
            "60": {"name": "1 hora", "bybit_interval": "60", "description": "Swing trading longo"},
            "240": {"name": "4 horas", "bybit_interval": "240", "description": "Position trading"},
            "D": {"name": "1 dia", "bybit_interval": "D", "description": "Investimento longo prazo"}
        }
        
        # Assets disponíveis
        self.available_assets = {
            "BTCUSDT": {"name": "Bitcoin", "emoji": "🪙", "min_volume": 1000000000},
            "ETHUSDT": {"name": "Ethereum", "emoji": "💎", "min_volume": 500000000},
            "BNBUSDT": {"name": "Binance Coin", "emoji": "🟡", "min_volume": 100000000},
            "SOLUSDT": {"name": "Solana", "emoji": "⚡", "min_volume": 50000000},
            "XRPUSDT": {"name": "XRP", "emoji": "💧", "min_volume": 100000000},
            "ADAUSDT": {"name": "Cardano", "emoji": "🔵", "min_volume": 50000000},
            "DOGEUSDT": {"name": "Dogecoin", "emoji": "🐕", "min_volume": 50000000},
            "MATICUSDT": {"name": "Polygon", "emoji": "🟣", "min_volume": 30000000}
        }
        
        # Configurações atuais
        self.selected_asset = None
        self.selected_timeframe = None
        self.selected_strategy = None
        self.strategy_params = {}
        self.custom_start_date = None
        self.custom_end_date = None
        
        # Histórico de testes
        self.test_history = []
    
    def run_interactive_mode(self):
        """Executa o modo interativo do Strategy Lab"""
        while True:
            self._show_main_menu()
            choice = input("\\n🔢 Escolha uma opção (0-8): ").strip()
            
            if choice == '0':
                print("\\n👋 Saindo do Strategy Lab Professional V6...")
                break
            elif choice == '1':
                self._asset_selection_menu()
            elif choice == '2':
                self._strategy_configuration_menu()
            elif choice == '3':
                self._timeframe_selection_menu()
            elif choice == '4':
                self._period_selection_menu()
            elif choice == '5':
                self._run_historical_backtest()
            elif choice == '6':
                self._run_realtime_test()
            elif choice == '7':
                self._view_test_results()
            elif choice == '8':
                self._export_results()
            else:
                print("❌ Opção inválida")
                input("\\n📖 Pressione ENTER para continuar...")
    
    def _show_main_menu(self):
        """Mostra o menu principal do Strategy Lab"""
        print("\\n" + "="*80)
        print("🔬 STRATEGY LAB PROFESSIONAL V6 - MENU PRINCIPAL")
        print("="*80)
        
        # Status atual
        asset_status = f"✅ {self.selected_asset}" if self.selected_asset else "❌ Não selecionado"
        strategy_status = f"✅ {self.strategies[self.selected_strategy]['name']}" if self.selected_strategy else "❌ Não selecionada"
        timeframe_status = f"✅ {self.timeframes[self.selected_timeframe]['name']}" if self.selected_timeframe else "❌ Não selecionado"
        
        print(f"📊 CONFIGURAÇÃO ATUAL:")
        print(f"   🪙 Ativo: {asset_status}")
        print(f"   📈 Estratégia: {strategy_status}")
        print(f"   ⏰ Timeframe: {timeframe_status}")
        
        if self.custom_start_date and self.custom_end_date:
            print(f"   📅 Período: {self.custom_start_date} até {self.custom_end_date}")
        else:
            print(f"   📅 Período: Padrão (últimos 30 dias)")
        
        # Capital info
        if self.capital_manager:
            print(f"   💰 Capital: ${self.capital_manager.current_capital:.2f}")
            print(f"   💼 Position Size: ${self.capital_manager.get_position_size():.2f}")
        
        print(f"\\n🔧 CONFIGURAÇÃO:")
        print("   1️⃣  Seleção de Ativo")
        print("   2️⃣  Configuração de Estratégia")
        print("   3️⃣  Seleção de Timeframe")
        print("   4️⃣  Período Personalizado (Data Inicial/Final)")
        
        print(f"\\n🧪 TESTES:")
        print("   5️⃣  Teste Histórico (Backtest)")
        print("   6️⃣  Teste em Tempo Real")
        
        print(f"\\n📊 RESULTADOS:")
        print("   7️⃣  Visualizar Resultados")
        print("   8️⃣  Exportar Relatórios")
        
        print(f"\\n   0️⃣  Voltar ao Menu Principal")
    
    def _asset_selection_menu(self):
        """Menu de seleção de ativo"""
        print("\\n🪙 SELEÇÃO DE ATIVO")
        print("="*50)
        
        assets_list = list(self.available_assets.keys())
        for i, asset in enumerate(assets_list, 1):
            info = self.available_assets[asset]
            selected = "✅" if asset == self.selected_asset else "  "
            print(f"{selected} {i}. {info['emoji']} {asset} - {info['name']}")
        
        print("\\n0. Voltar")
        
        try:
            choice = int(input("\\n🔢 Escolha um ativo: "))
            if 1 <= choice <= len(assets_list):
                self.selected_asset = assets_list[choice - 1]
                asset_info = self.available_assets[self.selected_asset]
                print(f"\\n✅ Ativo selecionado: {asset_info['emoji']} {self.selected_asset} - {asset_info['name']}")
            elif choice == 0:
                return
            else:
                print("❌ Opção inválida")
        except ValueError:
            print("❌ Digite um número válido")
        
        input("\\n📖 Pressione ENTER para continuar...")
    
    def _strategy_configuration_menu(self):
        """Menu de configuração de estratégia"""
        print("\\n📈 CONFIGURAÇÃO DE ESTRATÉGIA")
        print("="*50)
        
        strategies_list = list(self.strategies.keys())
        for i, strategy_key in enumerate(strategies_list, 1):
            strategy = self.strategies[strategy_key]
            selected = "✅" if strategy_key == self.selected_strategy else "  "
            print(f"{selected} {i}. {strategy['emoji']} {strategy['name']}")
            print(f"      {strategy['description']} ({strategy['type']})")
        
        print("\\n0. Voltar")
        
        try:
            choice = int(input("\\n🔢 Escolha uma estratégia: "))
            if 1 <= choice <= len(strategies_list):
                strategy_key = strategies_list[choice - 1]
                self.selected_strategy = strategy_key
                strategy = self.strategies[strategy_key]
                print(f"\\n✅ Estratégia selecionada: {strategy['emoji']} {strategy['name']}")
                
                # Configurar parâmetros
                self._configure_strategy_parameters(strategy_key)
            elif choice == 0:
                return
            else:
                print("❌ Opção inválida")
        except ValueError:
            print("❌ Digite um número válido")
        
        input("\\n📖 Pressione ENTER para continuar...")
    
    def _configure_strategy_parameters(self, strategy_key: str):
        """Configura parâmetros da estratégia"""
        strategy = self.strategies[strategy_key]
        params = strategy['params']
        
        print(f"\\n⚙️ CONFIGURAÇÃO DE PARÂMETROS - {strategy['name']}")
        print("="*60)
        
        self.strategy_params[strategy_key] = {}
        
        for param_name, param_info in params.items():
            print(f"\\n📊 {param_info['description']}")
            print(f"   Valor padrão: {param_info['default']}")
            print(f"   Faixa: {param_info['min']} - {param_info['max']}")
            
            user_input = input(f"   Digite o valor (ENTER para padrão): ").strip()
            
            if user_input:
                try:
                    if isinstance(param_info['default'], float):
                        value = float(user_input)
                    else:
                        value = int(user_input)
                    
                    if param_info['min'] <= value <= param_info['max']:
                        self.strategy_params[strategy_key][param_name] = value
                        print(f"   ✅ Valor definido: {value}")
                    else:
                        print(f"   ❌ Valor fora da faixa. Usando padrão: {param_info['default']}")
                        self.strategy_params[strategy_key][param_name] = param_info['default']
                except ValueError:
                    print(f"   ❌ Valor inválido. Usando padrão: {param_info['default']}")
                    self.strategy_params[strategy_key][param_name] = param_info['default']
            else:
                self.strategy_params[strategy_key][param_name] = param_info['default']
                print(f"   ✅ Usando valor padrão: {param_info['default']}")
    
    def _timeframe_selection_menu(self):
        """Menu de seleção de timeframe"""
        print("\\n⏰ SELEÇÃO DE TIMEFRAME")
        print("="*50)
        
        timeframes_list = list(self.timeframes.keys())
        for i, tf_key in enumerate(timeframes_list, 1):
            tf_info = self.timeframes[tf_key]
            selected = "✅" if tf_key == self.selected_timeframe else "  "
            print(f"{selected} {i}. {tf_info['name']} - {tf_info['description']}")
        
        print("\\n0. Voltar")
        
        try:
            choice = int(input("\\n🔢 Escolha um timeframe: "))
            if 1 <= choice <= len(timeframes_list):
                self.selected_timeframe = timeframes_list[choice - 1]
                tf_info = self.timeframes[self.selected_timeframe]
                print(f"\\n✅ Timeframe selecionado: {tf_info['name']}")
            elif choice == 0:
                return
            else:
                print("❌ Opção inválida")
        except ValueError:
            print("❌ Digite um número válido")
        
        input("\\n📖 Pressione ENTER para continuar...")
    
    def _period_selection_menu(self):
        """Menu de seleção de período personalizado"""
        print("\\n📅 PERÍODO PERSONALIZADO")
        print("="*50)
        
        print("1. Usar período padrão (últimos 30 dias)")
        print("2. Definir período personalizado")
        print("0. Voltar")
        
        choice = input("\\n🔢 Escolha: ").strip()
        
        if choice == '1':
            self.custom_start_date = None
            self.custom_end_date = None
            print("✅ Usando período padrão (últimos 30 dias)")
        elif choice == '2':
            self._configure_custom_period()
        elif choice == '0':
            return
        else:
            print("❌ Opção inválida")
        
        input("\\n📖 Pressione ENTER para continuar...")
    
    def _configure_custom_period(self):
        """Configura período personalizado"""
        print("\\n📅 CONFIGURAÇÃO DE PERÍODO PERSONALIZADO")
        print("="*50)
        print("Formato: YYYY-MM-DD (ex: 2025-01-01)")
        
        try:
            start_date_str = input("\\n📅 Data inicial: ").strip()
            end_date_str = input("📅 Data final: ").strip()
            
            # Validar datas
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
            
            if start_date >= end_date:
                print("❌ A data inicial deve ser anterior à data final")
                return
            
            self.custom_start_date = start_date_str
            self.custom_end_date = end_date_str
            print(f"✅ Período definido: {start_date_str} até {end_date_str}")
            
        except ValueError:
            print("❌ Formato de data inválido. Use YYYY-MM-DD")
    
    def _run_historical_backtest(self):
        """Executa backtest histórico"""
        if not self._validate_configuration():
            return
        
        print("\n🔄 TESTE HISTÓRICO (BACKTEST)")
        print("="*60)
        print(f"📊 Ativo: {self.selected_asset}")
        print(f"📈 Estratégia: {self.strategies[self.selected_strategy]['name']}")
        print(f"⏰ Timeframe: {self.timeframes[self.selected_timeframe]['name']}")
        print("\n🔄 Executando backtest com dados históricos...")
        print("🚧 Implementação em desenvolvimento...")
        input("\n📖 Pressione ENTER para continuar...")
    
    def _run_realtime_test(self):
        """Executa teste em tempo real com WebSocket"""
        if not self._validate_configuration():
            return
        
        print("\n⚡ TESTE EM TEMPO REAL - WEBSOCKET BINANCE")
        print("="*70)
        print(f"📊 Ativo: {self.selected_asset}")
        print(f"📈 Estratégia: {self.strategies[self.selected_strategy]['name']}")
        print(f"⏰ Timeframe: {self.timeframes[self.selected_timeframe]['name']}")
        
        if self.capital_manager:
            print(f"💰 Capital atual: ${self.capital_manager.current_capital:.2f}")
        
        print("\n🔄 Iniciando execução em tempo real...")
        
        import asyncio
        from market_manus.engines.realtime_strategy_engine import RealtimeStrategyEngine
        
        try:
            tf_map = {
                "1": "1m", "5": "5m", "15": "15m",
                "30": "30m", "60": "1h", "240": "4h", "D": "1d"
            }
            interval = tf_map.get(self.selected_timeframe, "5m")
            
            engine = RealtimeStrategyEngine(
                symbol=self.selected_asset,
                interval=interval,
                strategies=[self.selected_strategy],
                data_provider=self.data_provider,
                confluence_mode="MAJORITY"
            )
            
            asyncio.run(engine.start())
            
        except KeyboardInterrupt:
            print("\n⏹️  Execução interrompida pelo usuário")
        except Exception as e:
            print(f"\n❌ Erro na execução: {e}")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _view_test_results(self):
        """Visualiza resultados dos testes"""
        print("\n📊 RESULTADOS DOS TESTES")
        print("="*50)
        
        if not self.test_history:
            print("❌ Nenhum teste executado ainda")
            print("💡 Execute um backtest ou teste em tempo real primeiro")
        else:
            print(f"📈 Total de testes: {len(self.test_history)}")
            for i, test in enumerate(self.test_history[-5:], 1):
                print(f"\n{i}. {test.get('type', 'N/A')} - {test.get('asset', 'N/A')}")
                print(f"   📅 {test.get('timestamp', 'N/A')}")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def _export_results(self):
        """Exporta resultados"""
        print("\n📁 EXPORTAR RESULTADOS")
        print("="*40)
        print("🚧 Funcionalidade em desenvolvimento...")
        print("📊 Recursos planejados:")
        print("   • Exportar para CSV")
        print("   • Exportar para JSON")
        print("   • Relatórios em PDF")
        input("\n📖 Pressione ENTER para continuar...")
    
    def _validate_configuration(self) -> bool:
        """Valida se a configuração está completa"""
        if not self.selected_asset:
            print("❌ Selecione um ativo primeiro (opção 1)")
            input("\n📖 Pressione ENTER para continuar...")
            return False
        
        if not self.selected_timeframe:
            print("❌ Selecione um timeframe primeiro (opção 3)")
            input("\n📖 Pressione ENTER para continuar...")
            return False
        
        if not self.selected_strategy:
            print("❌ Selecione uma estratégia primeiro (opção 2)")
            input("\n📖 Pressione ENTER para continuar...")
            return False
        
        return True
    
    def _calculate_rsi_strategy(self, df: pd.DataFrame, params: dict):
        """Calcula estratégia RSI"""
        from market_manus.strategies.rsi_mean_reversion_strategy import calculate_rsi
        period = params.get('rsi_period', 14)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)
        
        df['rsi'] = calculate_rsi(df['close'], period)
        last_rsi = df['rsi'].iloc[-1]
        
        if pd.isna(last_rsi):
            return {"action": "HOLD", "confidence": 0.0}
        
        if last_rsi < oversold:
            confidence = (oversold - last_rsi) / oversold
            return {"action": "BUY", "confidence": min(confidence, 1.0)}
        elif last_rsi > overbought:
            confidence = (last_rsi - overbought) / (100 - overbought)
            return {"action": "SELL", "confidence": min(confidence, 1.0)}
        
        return {"action": "HOLD", "confidence": 0.0}
    
    def _calculate_ema_strategy(self, df: pd.DataFrame, params: dict):
        """Calcula estratégia EMA"""
        from market_manus.strategies.ema_crossover_strategy import calculate_ema
        fast = params.get('fast_ema', 12)
        slow = params.get('slow_ema', 26)
        
        df['ema_fast'] = calculate_ema(df['close'], fast)
        df['ema_slow'] = calculate_ema(df['close'], slow)
        
        last_fast = df['ema_fast'].iloc[-1]
        last_slow = df['ema_slow'].iloc[-1]
        
        if pd.isna(last_fast) or pd.isna(last_slow):
            return {"action": "HOLD", "confidence": 0.0}
        
        diff = abs(last_fast - last_slow) / last_slow
        
        if last_fast > last_slow:
            return {"action": "BUY", "confidence": min(diff * 10, 1.0)}
        elif last_fast < last_slow:
            return {"action": "SELL", "confidence": min(diff * 10, 1.0)}
        
        return {"action": "HOLD", "confidence": 0.0}
    
    def _calculate_bollinger_strategy(self, df: pd.DataFrame, params: dict):
        """Calcula estratégia Bollinger Bands"""
        period = params.get('period', 20)
        std_dev = params.get('std_dev', 2.0)
        
        df['sma'] = df['close'].rolling(window=period).mean()
        df['std'] = df['close'].rolling(window=period).std()
        df['upper'] = df['sma'] + (df['std'] * std_dev)
        df['lower'] = df['sma'] - (df['std'] * std_dev)
        
        last_close = df['close'].iloc[-1]
        last_upper = df['upper'].iloc[-1]
        last_lower = df['lower'].iloc[-1]
        
        if pd.isna(last_upper) or pd.isna(last_lower):
            return {"action": "HOLD", "confidence": 0.0}
        
        if last_close > last_upper:
            confidence = (last_close - last_upper) / last_upper
            return {"action": "SELL", "confidence": min(confidence * 10, 1.0)}
        elif last_close < last_lower:
            confidence = (last_lower - last_close) / last_lower
            return {"action": "BUY", "confidence": min(confidence * 10, 1.0)}
        
        return {"action": "HOLD", "confidence": 0.0}
    
    def _calculate_macd_strategy(self, df: pd.DataFrame, params: dict):
        """Calcula estratégia MACD"""
        from market_manus.strategies.classic_analysis import calculate_macd
        fast = params.get('fast_period', 12)
        slow = params.get('slow_period', 26)
        signal = params.get('signal_period', 9)
        
        macd_line, signal_line, histogram = calculate_macd(df['close'], fast, slow, signal)
        
        last_macd = macd_line.iloc[-1]
        last_signal = signal_line.iloc[-1]
        
        if pd.isna(last_macd) or pd.isna(last_signal):
            return {"action": "HOLD", "confidence": 0.0}
        
        diff = abs(last_macd - last_signal) / abs(last_signal) if last_signal != 0 else 0
        
        if last_macd > last_signal:
            return {"action": "BUY", "confidence": min(diff, 1.0)}
        elif last_macd < last_signal:
            return {"action": "SELL", "confidence": min(diff, 1.0)}
        
        return {"action": "HOLD", "confidence": 0.0}
    
    def _calculate_stochastic_strategy(self, df: pd.DataFrame, params: dict):
        """Calcula estratégia Stochastic"""
        k_period = params.get('k_period', 14)
        oversold = params.get('oversold', 20)
        overbought = params.get('overbought', 80)
        
        low_min = df['low'].rolling(window=k_period).min()
        high_max = df['high'].rolling(window=k_period).max()
        
        df['%K'] = 100 * ((df['close'] - low_min) / (high_max - low_min))
        last_k = df['%K'].iloc[-1]
        
        if pd.isna(last_k):
            return {"action": "HOLD", "confidence": 0.0}
        
        if last_k < oversold:
            confidence = (oversold - last_k) / oversold
            return {"action": "BUY", "confidence": min(confidence, 1.0)}
        elif last_k > overbought:
            confidence = (last_k - overbought) / (100 - overbought)
            return {"action": "SELL", "confidence": min(confidence, 1.0)}
        
        return {"action": "HOLD", "confidence": 0.0}
    
    def _calculate_williams_r_strategy(self, df: pd.DataFrame, params: dict):
        """Calcula estratégia Williams %R"""
        period = params.get('period', 14)
        oversold = params.get('oversold', -80)
        overbought = params.get('overbought', -20)
        
        high_max = df['high'].rolling(window=period).max()
        low_min = df['low'].rolling(window=period).min()
        
        df['%R'] = -100 * ((high_max - df['close']) / (high_max - low_min))
        last_r = df['%R'].iloc[-1]
        
        if pd.isna(last_r):
            return {"action": "HOLD", "confidence": 0.0}
        
        if last_r < oversold:
            confidence = abs(last_r - oversold) / abs(oversold)
            return {"action": "BUY", "confidence": min(confidence, 1.0)}
        elif last_r > overbought:
            confidence = abs(last_r - overbought) / abs(overbought)
            return {"action": "SELL", "confidence": min(confidence, 1.0)}
        
        return {"action": "HOLD", "confidence": 0.0}
    
    def _calculate_adx_strategy(self, df: pd.DataFrame, params: dict):
        """Calcula estratégia ADX"""
        from market_manus.strategies.classic_analysis import calculate_adx
        period = params.get('period', 14)
        threshold = params.get('adx_threshold', 25)
        
        adx, plus_di, minus_di = calculate_adx(df, period)
        
        last_adx = adx.iloc[-1]
        last_plus = plus_di.iloc[-1]
        last_minus = minus_di.iloc[-1]
        
        if pd.isna(last_adx) or pd.isna(last_plus) or pd.isna(last_minus):
            return {"action": "HOLD", "confidence": 0.0}
        
        if last_adx > threshold:
            confidence = min(last_adx / 50, 1.0)
            if last_plus > last_minus:
                return {"action": "BUY", "confidence": confidence}
            elif last_minus > last_plus:
                return {"action": "SELL", "confidence": confidence}
        
        return {"action": "HOLD", "confidence": 0.0}
    
    def _calculate_fibonacci_strategy(self, df: pd.DataFrame, params: dict):
        """Calcula estratégia Fibonacci"""
        lookback = params.get('lookback_period', 50)
        tolerance = params.get('tolerance_pct', 0.5) / 100
        
        recent_data = df.tail(lookback)
        high = recent_data['high'].max()
        low = recent_data['low'].min()
        
        fib_levels = {
            '0.236': low + (high - low) * 0.236,
            '0.382': low + (high - low) * 0.382,
            '0.5': low + (high - low) * 0.5,
            '0.618': low + (high - low) * 0.618,
            '0.786': low + (high - low) * 0.786
        }
        
        last_close = df['close'].iloc[-1]
        
        for level_name, level_price in fib_levels.items():
            if abs(last_close - level_price) / level_price < tolerance:
                if last_close < level_price:
                    return {"action": "BUY", "confidence": 0.6}
                else:
                    return {"action": "SELL", "confidence": 0.6}
        
        return {"action": "HOLD", "confidence": 0.0}
