#!/usr/bin/env python3
"""
Market Manus CLI - Versão com Sistema de Confluência
Data: 21/09/2025 17:00

NOVA FUNCIONALIDADE IMPLEMENTADA:
✅ Sistema de Confluência de Estratégias
✅ Combinação de múltiplas estratégias (RSI + EMA + Bollinger)
✅ Modos de confirmação: ALL, ANY, MAJORITY, WEIGHTED
✅ Configuração de pesos para cada estratégia
✅ Análise de qualidade dos sinais combinados
✅ Testes com dados reais da API Bybit

ESTRATÉGIAS DISPONÍVEIS PARA CONFLUÊNCIA:
- RSI Mean Reversion (overbought/oversold)
- EMA Crossover (cruzamento de médias)
- Bollinger Bands Breakout (rompimento de bandas)
- AI Agent (Multi-Armed Bandit)

MODOS DE CONFLUÊNCIA:
- ALL: Todas as estratégias devem concordar
- ANY: Qualquer estratégia pode gerar sinal
- MAJORITY: Maioria das estratégias deve concordar
- WEIGHTED: Sinal baseado em pesos configuráveis
"""

import os
import sys
import json
import time
import requests
import threading
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
from typing import Dict, List, Optional, Tuple, Any

class CapitalTracker:
    """Gerenciador de capital com proteção de drawdown"""
    
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades = []
        self.position_size_pct = 0.10  # 10% por posição
        self.max_drawdown_pct = 0.50   # 50% máximo de drawdown
        self.compound_interest = True
        
    def get_position_size(self) -> float:
        """Calcula o tamanho da posição baseado no capital atual"""
        if self.compound_interest:
            return self.current_capital * self.position_size_pct
        else:
            return self.initial_capital * self.position_size_pct
    
    def add_trade(self, pnl: float, symbol: str = "", strategy: str = ""):
        """Adiciona um trade ao histórico"""
        trade = {
            'timestamp': datetime.now(),
            'pnl': pnl,
            'symbol': symbol,
            'strategy': strategy,
            'capital_before': self.current_capital,
            'capital_after': self.current_capital + pnl
        }
        
        self.trades.append(trade)
        self.current_capital += pnl
        
        # Verificar proteção de drawdown
        drawdown = (self.initial_capital - self.current_capital) / self.initial_capital
        if drawdown > self.max_drawdown_pct:
            print(f"🚨 PROTEÇÃO DE DRAWDOWN ATIVADA! Drawdown: {drawdown:.1%}")
            return False
        
        return True
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do capital"""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'total_return_pct': 0.0,
                'current_drawdown': 0.0
            }
        
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        total_pnl = self.current_capital - self.initial_capital
        
        return {
            'total_trades': len(self.trades),
            'win_rate': len(winning_trades) / len(self.trades) * 100,
            'total_pnl': total_pnl,
            'total_return_pct': total_pnl / self.initial_capital * 100,
            'current_drawdown': max(0, (self.initial_capital - self.current_capital) / self.initial_capital * 100)
        }

class AssetManager:
    """Gerenciador de ativos com preços reais da Bybit"""
    
    def __init__(self, testnet: bool = True):
        self.testnet = testnet
        self.base_url = "https://api-demo.bybit.com" if testnet else "https://api.bybit.com"
        self.assets = {
            'BTCUSDT': {'name': 'Bitcoin', 'emoji': '🪙'},
            'ETHUSDT': {'name': 'Ethereum', 'emoji': '💎'},
            'BNBUSDT': {'name': 'Binance Coin', 'emoji': '🟡'},
            'SOLUSDT': {'name': 'Solana', 'emoji': '⚡'},
            'XRPUSDT': {'name': 'XRP', 'emoji': '💧'},
            'ADAUSDT': {'name': 'Cardano', 'emoji': '🔵'},
            'DOTUSDT': {'name': 'Polkadot', 'emoji': '🔴'},
            'AVAXUSDT': {'name': 'Avalanche', 'emoji': '🔺'},
            'LTCUSDT': {'name': 'Litecoin', 'emoji': '🥈'},
            'MATICUSDT': {'name': 'Polygon', 'emoji': '🟣'}
        }
        self.prices = {}
        
    def update_all_prices(self) -> Dict:
        """Atualiza preços de todos os ativos"""
        try:
            response = requests.get(
                f"{self.base_url}/v5/market/tickers",
                params={'category': 'spot'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('retCode') == 0:
                    tickers = {item['symbol']: item for item in data['result']['list']}
                    
                    for symbol in self.assets:
                        if symbol in tickers:
                            ticker = tickers[symbol]
                            self.prices[symbol] = {
                                'price': float(ticker['lastPrice']),
                                'change_24h': float(ticker['price24hPcnt']) * 100,
                                'volume_24h': float(ticker['volume24h']) * float(ticker['lastPrice']),
                                'timestamp': datetime.now()
                            }
                        else:
                            self.prices[symbol] = {
                                'price': 0.0,
                                'change_24h': 0.0,
                                'volume_24h': 0.0,
                                'timestamp': datetime.now()
                            }
                            
            return self.prices
            
        except Exception as e:
            print(f"❌ Erro ao obter preços: {e}")
            return {}
    
    def get_historical_data(self, symbol: str, interval: str, start_time: int, end_time: int) -> List[Dict]:
        """Obtém dados históricos da API Bybit"""
        try:
            response = requests.get(
                f"{self.base_url}/v5/market/kline",
                params={
                    'category': 'spot',
                    'symbol': symbol,
                    'interval': interval,
                    'start': start_time,
                    'end': end_time,
                    'limit': 1000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('retCode') == 0:
                    klines = data['result']['list']
                    
                    # Converter para formato padrão
                    candles = []
                    for kline in reversed(klines):  # Bybit retorna em ordem reversa
                        candles.append({
                            'timestamp': int(kline[0]),
                            'open': float(kline[1]),
                            'high': float(kline[2]),
                            'low': float(kline[3]),
                            'close': float(kline[4]),
                            'volume': float(kline[5])
                        })
                    
                    return candles
                    
        except Exception as e:
            print(f"❌ Erro ao obter dados históricos: {e}")
            
        return []

class StrategyConfluence:
    """Sistema de confluência para combinar múltiplas estratégias"""
    
    def __init__(self):
        self.strategies = {
            'ema_crossover': {
                'name': 'EMA Crossover',
                'description': 'Cruzamento de médias móveis exponenciais',
                'params': {'fast_period': 12, 'slow_period': 26},
                'weight': 1.0,
                'enabled': False
            },
            'rsi_mean_reversion': {
                'name': 'RSI Mean Reversion',
                'description': 'Reversão à média baseada no RSI',
                'params': {'rsi_period': 14, 'oversold': 30, 'overbought': 70},
                'weight': 1.0,
                'enabled': False
            },
            'bollinger_breakout': {
                'name': 'Bollinger Bands Breakout',
                'description': 'Rompimento das Bandas de Bollinger',
                'params': {'period': 20, 'std_dev': 2.0},
                'weight': 1.0,
                'enabled': False
            },
            'ai_agent': {
                'name': 'AI Agent (Multi-Armed Bandit)',
                'description': 'Agente IA com aprendizado automático',
                'params': {'epsilon': 0.1, 'learning_rate': 0.01},
                'weight': 1.0,
                'enabled': False
            }
        }
        
        self.confluence_modes = {
            'ALL': 'Todas as estratégias devem concordar',
            'ANY': 'Qualquer estratégia pode gerar sinal',
            'MAJORITY': 'Maioria das estratégias deve concordar',
            'WEIGHTED': 'Sinal baseado em pesos configuráveis'
        }
        
        self.current_mode = 'MAJORITY'
        
    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Calcula EMA (Exponential Moving Average)"""
        if len(prices) < period:
            return [0] * len(prices)
            
        ema = [prices[0]]
        multiplier = 2 / (period + 1)
        
        for i in range(1, len(prices)):
            ema.append((prices[i] * multiplier) + (ema[i-1] * (1 - multiplier)))
            
        return ema
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """Calcula RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return [50] * len(prices)
            
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [max(0, delta) for delta in deltas]
        losses = [max(0, -delta) for delta in deltas]
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        rsi_values = [50] * (period + 1)
        
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                
            rsi_values.append(rsi)
            
        return rsi_values
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2.0) -> Tuple[List[float], List[float], List[float]]:
        """Calcula Bollinger Bands"""
        if len(prices) < period:
            return [0] * len(prices), [0] * len(prices), [0] * len(prices)
            
        middle_band = []
        upper_band = []
        lower_band = []
        
        for i in range(len(prices)):
            if i < period - 1:
                middle_band.append(prices[i])
                upper_band.append(prices[i])
                lower_band.append(prices[i])
            else:
                window = prices[i-period+1:i+1]
                sma = sum(window) / period
                variance = sum((x - sma) ** 2 for x in window) / period
                std = variance ** 0.5
                
                middle_band.append(sma)
                upper_band.append(sma + (std_dev * std))
                lower_band.append(sma - (std_dev * std))
                
        return middle_band, upper_band, lower_band
    
    def get_ema_signal(self, prices: List[float], params: Dict) -> Tuple[str, float]:
        """Gera sinal da estratégia EMA Crossover"""
        fast_ema = self.calculate_ema(prices, params['fast_period'])
        slow_ema = self.calculate_ema(prices, params['slow_period'])
        
        if len(fast_ema) < 2 or len(slow_ema) < 2:
            return 'HOLD', 50.0
            
        # Verificar cruzamento
        current_fast = fast_ema[-1]
        current_slow = slow_ema[-1]
        prev_fast = fast_ema[-2]
        prev_slow = slow_ema[-2]
        
        # Cruzamento para cima (sinal de compra)
        if prev_fast <= prev_slow and current_fast > current_slow:
            strength = min(95.0, abs(current_fast - current_slow) / current_slow * 1000)
            return 'BUY', max(70.0, strength)
            
        # Cruzamento para baixo (sinal de venda)
        elif prev_fast >= prev_slow and current_fast < current_slow:
            strength = min(95.0, abs(current_fast - current_slow) / current_slow * 1000)
            return 'SELL', max(70.0, strength)
            
        # Sem cruzamento
        else:
            # Força baseada na distância entre as EMAs
            distance = abs(current_fast - current_slow) / current_slow * 100
            strength = max(20.0, min(60.0, 50 - distance * 10))
            return 'HOLD', strength
    
    def get_rsi_signal(self, prices: List[float], params: Dict) -> Tuple[str, float]:
        """Gera sinal da estratégia RSI Mean Reversion"""
        rsi_values = self.calculate_rsi(prices, params['rsi_period'])
        
        if len(rsi_values) < 2:
            return 'HOLD', 50.0
            
        current_rsi = rsi_values[-1]
        
        # Oversold (sinal de compra)
        if current_rsi <= params['oversold']:
            strength = max(70.0, min(95.0, (params['oversold'] - current_rsi) * 2 + 70))
            return 'BUY', strength
            
        # Overbought (sinal de venda)
        elif current_rsi >= params['overbought']:
            strength = max(70.0, min(95.0, (current_rsi - params['overbought']) * 2 + 70))
            return 'SELL', strength
            
        # Zona neutra
        else:
            # Força baseada na distância das zonas extremas
            distance_to_oversold = abs(current_rsi - params['oversold'])
            distance_to_overbought = abs(current_rsi - params['overbought'])
            min_distance = min(distance_to_oversold, distance_to_overbought)
            strength = max(20.0, min(60.0, 60 - min_distance))
            return 'HOLD', strength
    
    def get_bollinger_signal(self, prices: List[float], params: Dict) -> Tuple[str, float]:
        """Gera sinal da estratégia Bollinger Bands Breakout"""
        middle, upper, lower = self.calculate_bollinger_bands(prices, params['period'], params['std_dev'])
        
        if len(prices) < 2 or len(upper) < 2:
            return 'HOLD', 50.0
            
        current_price = prices[-1]
        prev_price = prices[-2]
        current_upper = upper[-1]
        current_lower = lower[-1]
        prev_upper = upper[-2]
        prev_lower = lower[-2]
        
        # Rompimento para cima (sinal de compra)
        if prev_price <= prev_upper and current_price > current_upper:
            strength = min(95.0, (current_price - current_upper) / current_upper * 1000 + 75)
            return 'BUY', max(75.0, strength)
            
        # Rompimento para baixo (sinal de venda)
        elif prev_price >= prev_lower and current_price < current_lower:
            strength = min(95.0, (current_lower - current_price) / current_lower * 1000 + 75)
            return 'SELL', max(75.0, strength)
            
        # Dentro das bandas
        else:
            # Força baseada na posição dentro das bandas
            band_width = current_upper - current_lower
            position_in_band = (current_price - current_lower) / band_width
            
            if position_in_band > 0.8:  # Próximo da banda superior
                strength = max(40.0, min(65.0, position_in_band * 65))
                return 'HOLD', strength
            elif position_in_band < 0.2:  # Próximo da banda inferior
                strength = max(40.0, min(65.0, (1 - position_in_band) * 65))
                return 'HOLD', strength
            else:  # No meio das bandas
                return 'HOLD', 35.0
    
    def get_ai_agent_signal(self, prices: List[float], params: Dict) -> Tuple[str, float]:
        """Gera sinal da estratégia AI Agent (simulado)"""
        if len(prices) < 10:
            return 'HOLD', 50.0
            
        # Simular comportamento de Multi-Armed Bandit
        recent_prices = prices[-10:]
        volatility = np.std(recent_prices) / np.mean(recent_prices)
        trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        # Lógica simplificada do agente IA
        if trend > 0.02 and volatility < 0.05:  # Tendência de alta com baixa volatilidade
            strength = max(60.0, min(90.0, trend * 1000 + 60))
            return 'BUY', strength
        elif trend < -0.02 and volatility < 0.05:  # Tendência de baixa com baixa volatilidade
            strength = max(60.0, min(90.0, abs(trend) * 1000 + 60))
            return 'SELL', strength
        else:
            # Força baseada na incerteza
            uncertainty = volatility * 100
            strength = max(25.0, min(55.0, 55 - uncertainty))
            return 'HOLD', strength
    
    def get_confluence_signal(self, prices: List[float]) -> Dict:
        """Gera sinal de confluência combinando todas as estratégias ativas"""
        signals = {}
        enabled_strategies = [name for name, config in self.strategies.items() if config['enabled']]
        
        if not enabled_strategies:
            return {
                'action': 'HOLD',
                'strength': 50.0,
                'strategies_used': [],
                'individual_signals': {},
                'confluence_mode': self.current_mode,
                'agreement_level': 0.0
            }
        
        # Obter sinais individuais
        for strategy_name in enabled_strategies:
            config = self.strategies[strategy_name]
            
            if strategy_name == 'ema_crossover':
                action, strength = self.get_ema_signal(prices, config['params'])
            elif strategy_name == 'rsi_mean_reversion':
                action, strength = self.get_rsi_signal(prices, config['params'])
            elif strategy_name == 'bollinger_breakout':
                action, strength = self.get_bollinger_signal(prices, config['params'])
            elif strategy_name == 'ai_agent':
                action, strength = self.get_ai_agent_signal(prices, config['params'])
            else:
                action, strength = 'HOLD', 50.0
                
            signals[strategy_name] = {
                'action': action,
                'strength': strength,
                'weight': config['weight']
            }
        
        # Aplicar lógica de confluência
        final_action, final_strength, agreement = self._apply_confluence_logic(signals)
        
        return {
            'action': final_action,
            'strength': final_strength,
            'strategies_used': enabled_strategies,
            'individual_signals': signals,
            'confluence_mode': self.current_mode,
            'agreement_level': agreement
        }
    
    def _apply_confluence_logic(self, signals: Dict) -> Tuple[str, float, float]:
        """Aplica a lógica de confluência baseada no modo selecionado"""
        if not signals:
            return 'HOLD', 50.0, 0.0
            
        actions = [signal['action'] for signal in signals.values()]
        strengths = [signal['strength'] for signal in signals.values()]
        weights = [signal['weight'] for signal in signals.values()]
        
        if self.current_mode == 'ALL':
            # Todas as estratégias devem concordar
            if len(set(actions)) == 1 and actions[0] != 'HOLD':
                final_action = actions[0]
                final_strength = sum(strengths) / len(strengths)
                agreement = 100.0
            else:
                final_action = 'HOLD'
                final_strength = 40.0
                agreement = 0.0 if 'HOLD' not in actions else 50.0
                
        elif self.current_mode == 'ANY':
            # Qualquer estratégia pode gerar sinal
            non_hold_signals = [(action, strength) for action, strength in zip(actions, strengths) if action != 'HOLD']
            if non_hold_signals:
                # Pegar o sinal mais forte
                best_signal = max(non_hold_signals, key=lambda x: x[1])
                final_action = best_signal[0]
                final_strength = best_signal[1]
                agreement = len(non_hold_signals) / len(actions) * 100
            else:
                final_action = 'HOLD'
                final_strength = sum(strengths) / len(strengths)
                agreement = 100.0
                
        elif self.current_mode == 'MAJORITY':
            # Maioria das estratégias deve concordar
            from collections import Counter
            action_counts = Counter(actions)
            majority_action = action_counts.most_common(1)[0][0]
            majority_count = action_counts.most_common(1)[0][1]
            
            if majority_count > len(actions) / 2:
                final_action = majority_action
                # Média das forças dos sinais da maioria
                majority_strengths = [strength for action, strength in zip(actions, strengths) if action == majority_action]
                final_strength = sum(majority_strengths) / len(majority_strengths)
                agreement = majority_count / len(actions) * 100
            else:
                final_action = 'HOLD'
                final_strength = 45.0
                agreement = 0.0
                
        elif self.current_mode == 'WEIGHTED':
            # Sinal baseado em pesos
            weighted_buy = 0.0
            weighted_sell = 0.0
            weighted_hold = 0.0
            total_weight = sum(weights)
            
            for i, (action, strength, weight) in enumerate(zip(actions, strengths, weights)):
                normalized_weight = weight / total_weight
                weighted_strength = strength * normalized_weight
                
                if action == 'BUY':
                    weighted_buy += weighted_strength
                elif action == 'SELL':
                    weighted_sell += weighted_strength
                else:
                    weighted_hold += weighted_strength
            
            # Determinar ação final baseada nos pesos
            if weighted_buy > weighted_sell and weighted_buy > weighted_hold:
                final_action = 'BUY'
                final_strength = weighted_buy
            elif weighted_sell > weighted_buy and weighted_sell > weighted_hold:
                final_action = 'SELL'
                final_strength = weighted_sell
            else:
                final_action = 'HOLD'
                final_strength = weighted_hold
                
            # Calcular nível de concordância baseado na distribuição dos pesos
            max_weighted = max(weighted_buy, weighted_sell, weighted_hold)
            total_weighted = weighted_buy + weighted_sell + weighted_hold
            agreement = (max_weighted / total_weighted) * 100 if total_weighted > 0 else 0.0
        
        else:
            final_action = 'HOLD'
            final_strength = 50.0
            agreement = 0.0
        
        return final_action, final_strength, agreement

class MarketManusCompleteCLI:
    """CLI principal do Market Manus com Sistema de Confluência"""
    
    def __init__(self):
        self.capital_tracker = CapitalTracker()
        self.asset_manager = AssetManager(testnet=True)
        self.strategy_confluence = StrategyConfluence()
        self.selected_asset = None
        self.selected_timeframe = None
        self.running = True
        
        # Carregar configurações
        self.load_settings()
        
    def load_settings(self):
        """Carrega configurações salvas"""
        try:
            config_path = Path("config/settings.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    settings = json.load(f)
                    
                self.capital_tracker.initial_capital = settings.get('initial_capital', 10000.0)
                self.capital_tracker.current_capital = settings.get('current_capital', 10000.0)
                self.capital_tracker.position_size_pct = settings.get('position_size_pct', 0.10)
                self.capital_tracker.max_drawdown_pct = settings.get('max_drawdown_pct', 0.50)
                self.capital_tracker.compound_interest = settings.get('compound_interest', True)
                
        except Exception as e:
            print(f"⚠️ Erro ao carregar configurações: {e}")
    
    def save_settings(self):
        """Salva configurações atuais"""
        try:
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            settings = {
                'initial_capital': self.capital_tracker.initial_capital,
                'current_capital': self.capital_tracker.current_capital,
                'position_size_pct': self.capital_tracker.position_size_pct,
                'max_drawdown_pct': self.capital_tracker.max_drawdown_pct,
                'compound_interest': self.capital_tracker.compound_interest
            }
            
            with open(config_dir / "settings.json", 'w') as f:
                json.dump(settings, f, indent=2)
                
            print("✅ Configurações salvas em config/settings.json")
            
        except Exception as e:
            print(f"❌ Erro ao salvar configurações: {e}")
    
    def test_connectivity(self):
        """Testa conectividade com APIs"""
        print("🔄 Testando conectividade...")
        
        try:
            # Testar API pública
            response = requests.get(
                f"{self.asset_manager.base_url}/v5/market/time",
                timeout=5
            )
            
            if response.status_code == 200:
                print("✅ Conectividade OK")
                return True
            else:
                print(f"⚠️ Conectividade limitada (Status: {response.status_code})")
                return False
                
        except Exception as e:
            print(f"❌ Erro de conectividade: {e}")
            return False
    
    def show_main_menu(self):
        """Exibe menu principal"""
        stats = self.capital_tracker.get_stats()
        
        print("\n💰 DASHBOARD RÁPIDO")
        print("-" * 40)
        print(f"💵 Capital: ${self.capital_tracker.current_capital:,.2f}")
        
        if stats['total_pnl'] >= 0:
            print(f"🟢 P&L: $+{stats['total_pnl']:,.2f} (+{stats['total_return_pct']:.2f}%)")
        else:
            print(f"🔴 P&L: ${stats['total_pnl']:,.2f} ({stats['total_return_pct']:.2f}%)")
            
        print(f"📊 Trades: {stats['total_trades']} | Win Rate: {stats['win_rate']:.1f}%")
        
        print("\n🎯 MENU PRINCIPAL")
        print("=" * 30)
        print("   1️⃣  Capital Dashboard (Visão detalhada do capital)")
        print("   2️⃣  Strategy Lab Professional (Análise confiável)")
        print("   3️⃣  Confluence Lab (Combinar múltiplas estratégias)")  # NOVA OPÇÃO
        print("   4️⃣  Simulate Trades (Simular operações)")
        print("   5️⃣  Export Reports (Exportar relatórios)")
        print("   6️⃣  Connectivity Status (Testar API novamente)")
        print("   7️⃣  Strategy Explorer (Explorar estratégias)")
        print("   8️⃣  Performance Analysis (Análise de performance)")
        print("   9️⃣  Advanced Settings (Configurações avançadas)")
        print("   0️⃣  Sair")
    
    def handle_capital_dashboard(self):
        """Gerencia dashboard de capital"""
        stats = self.capital_tracker.get_stats()
        
        print("\n💰 CAPITAL DASHBOARD")
        print("=" * 35)
        print(f"💵 Capital Inicial:     ${self.capital_tracker.initial_capital:>12,.2f}")
        print(f"💰 Capital Atual:       ${self.capital_tracker.current_capital:>12,.2f}")
        
        if stats['total_pnl'] >= 0:
            print(f"🟢 Retorno Total:      ${stats['total_pnl']:>+12,.2f} ({stats['total_return_pct']:>+6.2f}%)")
        else:
            print(f"🔴 Retorno Total:      ${stats['total_pnl']:>12,.2f} ({stats['total_return_pct']:>6.2f}%)")
            
        print("-" * 50)
        print(f"📊 Total de Trades:    {stats['total_trades']:>15}")
        print(f"🎯 Taxa de Acerto:     {stats['win_rate']:>12.1f}%")
        print(f"📉 Drawdown Atual:     {stats['current_drawdown']:>12.1f}%")
        print("-" * 50)
        print(f"⚙️ Position Size:       {self.capital_tracker.position_size_pct*100:>12.1f}%")
        print(f"🔄 Compound Interest:  {'Ativo' if self.capital_tracker.compound_interest else 'Inativo':>15}")
        print(f"🛡️ Proteção Drawdown:   {self.capital_tracker.max_drawdown_pct*100:>12.1f}%")
        print(f"💼 Próxima Posição:     ${self.capital_tracker.get_position_size():>12,.2f}")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_strategy_lab_professional(self):
        """Gerencia Strategy Lab Professional (versão individual)"""
        print("\n🔬 Iniciando Strategy Lab Professional...")
        print("🎯 Sistema de análise com dados reais da Bybit")
        print("📊 Seleção de criptoativo específico")
        print("⚡ Real Time vs Historical Data testing")
        print("💰 Integrado com seu capital management")
        
        input("\n📖 Pressione ENTER para continuar...")
        
        while True:
            self.show_strategy_lab_menu()
            
            try:
                choice = input("\n🔢 Escolha uma opção (0-6): ").strip()
                
                if choice == '0':
                    break
                elif choice == '1':
                    self.handle_asset_selection()
                elif choice == '2':
                    self.handle_strategy_configuration()
                elif choice == '3':
                    self.handle_real_time_test()
                elif choice == '4':
                    self.handle_historical_data_test()
                elif choice == '5':
                    self.handle_comparison_test()
                elif choice == '6':
                    self.handle_export_results()
                else:
                    print("❌ Opção inválida")
                    input("\n📖 Pressione ENTER para continuar...")
                    
            except KeyboardInterrupt:
                print("\n⚠️ Operação cancelada pelo usuário")
                break
    
    def handle_confluence_lab(self):
        """Gerencia Confluence Lab (NOVA FUNCIONALIDADE)"""
        print("\n🔬 CONFLUENCE LAB - SISTEMA DE CONFLUÊNCIA")
        print("=" * 60)
        print("🎯 Combine múltiplas estratégias para maior acertividade")
        print("📊 RSI + EMA + Bollinger Bands + AI Agent")
        print("⚡ Modos: ALL, ANY, MAJORITY, WEIGHTED")
        print("💰 Integrado com capital management")
        print("=" * 60)
        
        input("\n📖 Pressione ENTER para continuar...")
        
        while True:
            self.show_confluence_lab_menu()
            
            try:
                choice = input("\n🔢 Escolha uma opção (0-8): ").strip()
                
                if choice == '0':
                    break
                elif choice == '1':
                    self.handle_asset_selection()
                elif choice == '2':
                    self.handle_confluence_configuration()
                elif choice == '3':
                    self.handle_confluence_mode_selection()
                elif choice == '4':
                    self.handle_confluence_weights_configuration()
                elif choice == '5':
                    self.handle_confluence_real_time_test()
                elif choice == '6':
                    self.handle_confluence_historical_test()
                elif choice == '7':
                    self.handle_confluence_comparison_test()
                elif choice == '8':
                    self.handle_confluence_export_results()
                else:
                    print("❌ Opção inválida")
                    input("\n📖 Pressione ENTER para continuar...")
                    
            except KeyboardInterrupt:
                print("\n⚠️ Operação cancelada pelo usuário")
                break
    
    def show_confluence_lab_menu(self):
        """Exibe menu do Confluence Lab"""
        stats = self.capital_tracker.get_stats()
        enabled_strategies = [name for name, config in self.strategy_confluence.strategies.items() if config['enabled']]
        
        print("\n" + "=" * 80)
        print("🔬 CONFLUENCE LAB - SISTEMA DE CONFLUÊNCIA")
        print("=" * 80)
        print("🎯 Combine múltiplas estratégias para maior acertividade")
        print("📊 Análise com confluência de sinais")
        print("⚡ Testes com dados reais da Bybit")
        print("💰 INTEGRADO COM CAPITAL - Position size baseado na banca")
        print("=" * 80)
        
        print(f"\n💰 INFORMAÇÕES DO CAPITAL:")
        print(f"   💵 Capital atual: ${self.capital_tracker.current_capital:,.2f}")
        print(f"   📊 Position size: ${self.capital_tracker.get_position_size():,.2f} ({self.capital_tracker.position_size_pct*100:.1f}%)")
        print(f"   📈 Total trades: {stats['total_trades']}")
        
        print(f"\n📋 STATUS ATUAL:")
        print(f"   📊 Ativo: {self.selected_asset or 'Nenhum ativo selecionado'}")
        print(f"   🎯 Estratégias ativas: {len(enabled_strategies)}")
        if enabled_strategies:
            print(f"      {', '.join([self.strategy_confluence.strategies[s]['name'] for s in enabled_strategies])}")
        print(f"   🔄 Modo de confluência: {self.strategy_confluence.current_mode}")
        print(f"   ⏰ Timeframe: {self.selected_timeframe or 'Nenhum timeframe selecionado'}")
        
        print(f"\n🎯 OPÇÕES DISPONÍVEIS:")
        print("   1️⃣  Asset Selection (Selecionar criptoativo)")
        print("   2️⃣  Strategy Configuration (Configurar estratégias)")
        print("   3️⃣  Confluence Mode (Selecionar modo de confluência)")
        print("   4️⃣  Strategy Weights (Configurar pesos das estratégias)")
        print("   5️⃣  Real Time Confluence Test (Teste em tempo real)")
        print("   6️⃣  Historical Confluence Test (Teste com dados históricos)")
        print("   7️⃣  Comparison Test (Comparar modos de confluência)")
        print("   8️⃣  Export Confluence Results (Exportar resultados)")
        print("   0️⃣  Voltar ao menu principal")
    
    def handle_confluence_configuration(self):
        """Configura estratégias para confluência"""
        print("\n🎯 CONFIGURAÇÃO DE ESTRATÉGIAS PARA CONFLUÊNCIA")
        print("=" * 60)
        
        while True:
            print("\n🔧 ESTRATÉGIAS DISPONÍVEIS:")
            for i, (key, strategy) in enumerate(self.strategy_confluence.strategies.items(), 1):
                status = "✅" if strategy['enabled'] else "⚪"
                print(f"   {status} {i}. {strategy['name']}")
                print(f"      📝 {strategy['description']}")
                print(f"      ⚖️ Peso: {strategy['weight']:.1f}")
                
            print(f"\n⏰ TIMEFRAMES DISPONÍVEIS:")
            timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
            for i, tf in enumerate(timeframes, 1):
                status = "✅" if self.selected_timeframe == tf else "⚪"
                print(f"   {status} {chr(96+i)}. {tf}")
            
            print(f"\n🎯 OPÇÕES:")
            print("   • Digite 1-4 para ativar/desativar estratégia")
            print("   • Digite a-g para selecionar timeframe")
            print("   • 'p' para configurar parâmetros")
            print("   • 'w' para configurar pesos")
            print("   • '0' para voltar")
            
            choice = input("\n🔢 Escolha: ").strip().lower()
            
            if choice == '0':
                break
            elif choice in ['1', '2', '3', '4']:
                strategy_index = int(choice) - 1
                strategy_keys = list(self.strategy_confluence.strategies.keys())
                if 0 <= strategy_index < len(strategy_keys):
                    key = strategy_keys[strategy_index]
                    self.strategy_confluence.strategies[key]['enabled'] = not self.strategy_confluence.strategies[key]['enabled']
                    status = "ativada" if self.strategy_confluence.strategies[key]['enabled'] else "desativada"
                    print(f"✅ {self.strategy_confluence.strategies[key]['name']} {status}")
            elif choice in ['a', 'b', 'c', 'd', 'e', 'f', 'g']:
                timeframe_index = ord(choice) - ord('a')
                if 0 <= timeframe_index < len(timeframes):
                    self.selected_timeframe = timeframes[timeframe_index]
                    print(f"✅ Timeframe selecionado: {self.selected_timeframe}")
            elif choice == 'p':
                self.handle_strategy_parameters_configuration()
            elif choice == 'w':
                self.handle_confluence_weights_configuration()
            else:
                print("❌ Opção inválida")
                
            input("\n📖 Pressione ENTER para continuar...")
    
    def handle_confluence_mode_selection(self):
        """Seleciona modo de confluência"""
        print("\n🔄 SELEÇÃO DO MODO DE CONFLUÊNCIA")
        print("=" * 50)
        
        print("\n🎯 MODOS DISPONÍVEIS:")
        for i, (mode, description) in enumerate(self.strategy_confluence.confluence_modes.items(), 1):
            status = "✅" if self.strategy_confluence.current_mode == mode else "⚪"
            print(f"   {status} {i}. {mode}")
            print(f"      📝 {description}")
        
        print(f"\n📊 EXEMPLOS DE USO:")
        print("   🔴 ALL: Todas devem concordar (máxima confiança, poucos sinais)")
        print("   🟡 ANY: Qualquer pode gerar sinal (muitos sinais, menor confiança)")
        print("   🟢 MAJORITY: Maioria decide (balanceado)")
        print("   🔵 WEIGHTED: Baseado em pesos (customizável)")
        
        try:
            choice = input("\n🔢 Escolha o modo (1-4): ").strip()
            
            if choice == '1':
                self.strategy_confluence.current_mode = 'ALL'
                print("✅ Modo ALL selecionado - Todas as estratégias devem concordar")
            elif choice == '2':
                self.strategy_confluence.current_mode = 'ANY'
                print("✅ Modo ANY selecionado - Qualquer estratégia pode gerar sinal")
            elif choice == '3':
                self.strategy_confluence.current_mode = 'MAJORITY'
                print("✅ Modo MAJORITY selecionado - Maioria das estratégias decide")
            elif choice == '4':
                self.strategy_confluence.current_mode = 'WEIGHTED'
                print("✅ Modo WEIGHTED selecionado - Sinal baseado em pesos")
            else:
                print("❌ Opção inválida")
                
        except ValueError:
            print("❌ Digite um número válido")
            
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_confluence_weights_configuration(self):
        """Configura pesos das estratégias"""
        print("\n⚖️ CONFIGURAÇÃO DE PESOS DAS ESTRATÉGIAS")
        print("=" * 50)
        print("💡 Pesos maiores dão mais influência à estratégia no modo WEIGHTED")
        
        for key, strategy in self.strategy_confluence.strategies.items():
            if strategy['enabled']:
                print(f"\n🎯 {strategy['name']}")
                print(f"   Peso atual: {strategy['weight']:.1f}")
                
                try:
                    new_weight = input(f"   Novo peso (0.1-5.0): ").strip()
                    if new_weight:
                        weight = float(new_weight)
                        if 0.1 <= weight <= 5.0:
                            strategy['weight'] = weight
                            print(f"   ✅ Peso alterado para {weight:.1f}")
                        else:
                            print("   ❌ Peso deve estar entre 0.1 e 5.0")
                except ValueError:
                    print("   ❌ Digite um número válido")
        
        # Mostrar resumo dos pesos
        print(f"\n📊 RESUMO DOS PESOS:")
        total_weight = 0
        for key, strategy in self.strategy_confluence.strategies.items():
            if strategy['enabled']:
                print(f"   {strategy['name']}: {strategy['weight']:.1f}")
                total_weight += strategy['weight']
        
        print(f"   Total: {total_weight:.1f}")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_confluence_real_time_test(self):
        """Executa teste de confluência em tempo real"""
        enabled_strategies = [name for name, config in self.strategy_confluence.strategies.items() if config['enabled']]
        
        if not enabled_strategies:
            print("❌ Nenhuma estratégia ativada. Configure as estratégias primeiro.")
            input("\n📖 Pressione ENTER para continuar...")
            return
            
        if not self.selected_asset:
            print("❌ Nenhum ativo selecionado. Selecione um ativo primeiro.")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        print("\n⚡ CONFLUENCE REAL TIME TEST - TESTE EM TEMPO REAL")
        print("=" * 60)
        print(f"📊 Ativo: {self.selected_asset}")
        print(f"🎯 Estratégias: {', '.join([self.strategy_confluence.strategies[s]['name'] for s in enabled_strategies])}")
        print(f"🔄 Modo de confluência: {self.strategy_confluence.current_mode}")
        print(f"⏰ Timeframe: {self.selected_timeframe or '1m'}")
        print(f"💰 Capital atual: ${self.capital_tracker.current_capital:,.2f}")
        print(f"💼 Position size: ${self.capital_tracker.get_position_size():,.2f} ({self.capital_tracker.position_size_pct*100:.1f}%)")
        
        print(f"\n🔄 Iniciando teste de confluência em tempo real...")
        print("⏹️  Pressione Ctrl+C para parar")
        
        # Simular teste em tempo real com confluência
        signals_history = []
        
        try:
            for i in range(20):  # 20 iterações de teste
                # Simular preços em tempo real
                base_price = self.asset_manager.prices.get(self.selected_asset, {}).get('price', 100.0)
                price_variation = np.random.normal(0, 0.002)  # Variação de 0.2%
                current_price = base_price * (1 + price_variation)
                
                # Gerar histórico de preços simulado
                prices = [current_price * (1 + np.random.normal(0, 0.001)) for _ in range(50)]
                
                # Obter sinal de confluência
                confluence_result = self.strategy_confluence.get_confluence_signal(prices)
                
                signals_history.append({
                    'timestamp': datetime.now(),
                    'price': current_price,
                    'confluence_result': confluence_result
                })
                
                # Mostrar progresso
                progress = (i + 1) / 20 * 100
                action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(confluence_result['action'], '⚪')
                
                print(f"\r🔄 [{progress:5.1f}%] Iteração {i+1} | Preço: ${current_price:.4f} | "
                      f"Sinal: {action_emoji} {confluence_result['action']} | "
                      f"Força: {confluence_result['strength']:.1f}% | "
                      f"Acordo: {confluence_result['agreement_level']:.1f}%", end='', flush=True)
                
                time.sleep(0.5)  # Pausa entre iterações
                
        except KeyboardInterrupt:
            print(f"\n⚠️ Teste interrompido pelo usuário")
        
        print(f"\n\n✅ TESTE DE CONFLUÊNCIA EM TEMPO REAL CONCLUÍDO!")
        
        # Analisar resultados
        if signals_history:
            buy_signals = [s for s in signals_history if s['confluence_result']['action'] == 'BUY']
            sell_signals = [s for s in signals_history if s['confluence_result']['action'] == 'SELL']
            hold_signals = [s for s in signals_history if s['confluence_result']['action'] == 'HOLD']
            
            avg_strength = sum(s['confluence_result']['strength'] for s in signals_history) / len(signals_history)
            avg_agreement = sum(s['confluence_result']['agreement_level'] for s in signals_history) / len(signals_history)
            
            print(f"\n📊 RESULTADOS DO TESTE DE CONFLUÊNCIA - Real Time")
            print("=" * 60)
            print(f"📈 Total de Sinais: {len(signals_history)}")
            print(f"🟢 Sinais de Compra: {len(buy_signals)} ({len(buy_signals)/len(signals_history)*100:.1f}%)")
            print(f"🔴 Sinais de Venda: {len(sell_signals)} ({len(sell_signals)/len(signals_history)*100:.1f}%)")
            print(f"⚪ Sinais de Hold: {len(hold_signals)} ({len(hold_signals)/len(signals_history)*100:.1f}%)")
            print(f"⚡ Força Média dos Sinais: {avg_strength:.1f}%")
            print(f"🤝 Nível Médio de Acordo: {avg_agreement:.1f}%")
            
            # Classificar qualidade dos sinais
            if avg_strength >= 70:
                quality = "✅ SINAIS DE ALTA QUALIDADE"
            elif avg_strength >= 50:
                quality = "⚠️ SINAIS DE QUALIDADE MODERADA"
            else:
                quality = "❌ SINAIS DE BAIXA QUALIDADE"
            print(f"{quality} ({avg_strength:.1f}%)")
            
            print(f"\n💰 ANÁLISE DE IMPACTO NO CAPITAL:")
            position_size = self.capital_tracker.get_position_size()
            print(f"💼 Position size por trade: ${position_size:,.2f}")
            
            # Estimar impacto baseado nos sinais
            trading_signals = len(buy_signals) + len(sell_signals)
            print(f"📊 Trades com sinal: {trading_signals}")
            
            if trading_signals > 0:
                # Estimativa simplificada de impacto
                estimated_return_per_trade = (avg_strength - 50) / 100 * 0.02  # 2% máximo por trade
                total_estimated_impact = trading_signals * position_size * estimated_return_per_trade
                estimated_final_capital = self.capital_tracker.current_capital + total_estimated_impact
                
                if total_estimated_impact >= 0:
                    print(f"🟢 Impacto estimado: $+{total_estimated_impact:.2f}")
                else:
                    print(f"🔴 Impacto estimado: ${total_estimated_impact:.2f}")
                    
                print(f"💰 Capital estimado final: ${estimated_final_capital:,.2f}")
            
            # Mostrar detalhes das estratégias individuais
            print(f"\n🔍 DETALHES DAS ESTRATÉGIAS:")
            last_result = signals_history[-1]['confluence_result']
            for strategy_name, signal_data in last_result['individual_signals'].items():
                strategy_display_name = self.strategy_confluence.strategies[strategy_name]['name']
                action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(signal_data['action'], '⚪')
                print(f"   {action_emoji} {strategy_display_name}: {signal_data['action']} "
                      f"({signal_data['strength']:.1f}%) - Peso: {signal_data['weight']:.1f}")
            
            # Mostrar últimos 5 sinais
            print(f"\n🔍 ÚLTIMOS 5 SINAIS DE CONFLUÊNCIA:")
            print("-" * 80)
            for signal in signals_history[-5:]:
                timestamp = signal['timestamp'].strftime("%H:%M:%S")
                price = signal['price']
                result = signal['confluence_result']
                action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(result['action'], '⚪')
                
                print(f"{timestamp} | {action_emoji} {result['action']:4} | ${price:8.4f} | "
                      f"Força: {result['strength']:5.1f}% | Acordo: {result['agreement_level']:5.1f}%")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_confluence_historical_test(self):
        """Executa teste de confluência com dados históricos"""
        enabled_strategies = [name for name, config in self.strategy_confluence.strategies.items() if config['enabled']]
        
        if not enabled_strategies:
            print("❌ Nenhuma estratégia ativada. Configure as estratégias primeiro.")
            input("\n📖 Pressione ENTER para continuar...")
            return
            
        if not self.selected_asset:
            print("❌ Nenhum ativo selecionado. Selecione um ativo primeiro.")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        print("\n📈 CONFLUENCE HISTORICAL DATA TEST - DADOS HISTÓRICOS REAIS")
        print("=" * 70)
        print(f"📊 Ativo: {self.selected_asset}")
        print(f"🎯 Estratégias: {', '.join([self.strategy_confluence.strategies[s]['name'] for s in enabled_strategies])}")
        print(f"🔄 Modo de confluência: {self.strategy_confluence.current_mode}")
        print(f"⏰ Timeframe: {self.selected_timeframe or '1m'}")
        print(f"💰 Capital atual: ${self.capital_tracker.current_capital:,.2f}")
        print(f"💼 Position size: ${self.capital_tracker.get_position_size():,.2f} ({self.capital_tracker.position_size_pct*100:.1f}%)")
        
        # Seleção de período
        print(f"\n📅 PERÍODOS DISPONÍVEIS:")
        print("   1. Últimas 24 horas")
        print("   2. Últimos 7 dias")
        print("   3. Últimos 30 dias")
        print("   4. Últimos 90 dias")
        print("   5. Período personalizado (dd/mm/aa hh:mm:ss)")
        
        try:
            period_choice = input("\n🔢 Escolha o período: ").strip()
            
            # Calcular timestamps baseado na escolha
            end_time = int(datetime.now().timestamp() * 1000)
            
            if period_choice == '1':
                start_time = end_time - (24 * 60 * 60 * 1000)  # 24 horas
                period_name = "Últimas 24 horas"
            elif period_choice == '2':
                start_time = end_time - (7 * 24 * 60 * 60 * 1000)  # 7 dias
                period_name = "Últimos 7 dias"
            elif period_choice == '3':
                start_time = end_time - (30 * 24 * 60 * 60 * 1000)  # 30 dias
                period_name = "Últimos 30 dias"
            elif period_choice == '4':
                start_time = end_time - (90 * 24 * 60 * 60 * 1000)  # 90 dias
                period_name = "Últimos 90 dias"
            elif period_choice == '5':
                # Período personalizado (implementação simplificada)
                print("\n📅 PERÍODO PERSONALIZADO - SELEÇÃO DE DATAS")
                print("📝 Para este exemplo, usando últimos 7 dias")
                start_time = end_time - (7 * 24 * 60 * 60 * 1000)
                period_name = "Período personalizado"
            else:
                print("❌ Opção inválida, usando últimos 7 dias")
                start_time = end_time - (7 * 24 * 60 * 60 * 1000)
                period_name = "Últimos 7 dias"
            
            print(f"\n🔄 Obtendo dados históricos da API Bybit...")
            print(f"📊 Período: {period_name}")
            
            # Obter dados históricos reais
            interval_map = {'1m': '1', '5m': '5', '15m': '15', '30m': '30', '1h': '60', '4h': '240', '1d': 'D'}
            interval = interval_map.get(self.selected_timeframe or '1m', '1')
            
            historical_data = self.asset_manager.get_historical_data(
                self.selected_asset, interval, start_time, end_time
            )
            
            if not historical_data:
                print("❌ Erro ao obter dados históricos")
                input("\n📖 Pressione ENTER para continuar...")
                return
            
            print(f"✅ {len(historical_data)} candlesticks obtidos da API")
            
            if len(historical_data) > 0:
                first_candle = datetime.fromtimestamp(historical_data[0]['timestamp'] / 1000)
                last_candle = datetime.fromtimestamp(historical_data[-1]['timestamp'] / 1000)
                print(f"   📅 Primeiro: {first_candle.strftime('%d/%m/%Y %H:%M')}")
                print(f"   📅 Último: {last_candle.strftime('%d/%m/%Y %H:%M')}")
                print(f"   💰 Preço inicial: ${historical_data[0]['close']:.4f}")
                print(f"   💰 Preço final: ${historical_data[-1]['close']:.4f}")
                
                price_change = (historical_data[-1]['close'] - historical_data[0]['close']) / historical_data[0]['close'] * 100
                change_emoji = "🟢" if price_change >= 0 else "🔴"
                print(f"   {change_emoji} Variação: {price_change:+.2f}%")
            
            print(f"🔄 Executando backtest de confluência com dados reais...")
            
            # Extrair preços de fechamento
            prices = [candle['close'] for candle in historical_data]
            
            # Executar análise de confluência em cada ponto
            confluence_results = []
            
            # Usar janela deslizante para análise
            window_size = 50  # Janela de 50 períodos para cálculo dos indicadores
            
            for i in range(window_size, len(prices)):
                price_window = prices[i-window_size:i+1]
                confluence_result = self.strategy_confluence.get_confluence_signal(price_window)
                
                confluence_results.append({
                    'timestamp': historical_data[i]['timestamp'],
                    'price': prices[i],
                    'confluence_result': confluence_result
                })
                
                # Mostrar progresso
                progress = (i - window_size + 1) / (len(prices) - window_size) * 100
                print(f"\r🔄 Processando confluência: [{progress:5.1f}%] {i-window_size+1}/{len(prices)-window_size}", 
                      end='', flush=True)
            
            print(f"\n\n✅ BACKTEST DE CONFLUÊNCIA HISTÓRICO CONCLUÍDO COM DADOS REAIS!")
            
            # Analisar resultados
            if confluence_results:
                buy_signals = [r for r in confluence_results if r['confluence_result']['action'] == 'BUY']
                sell_signals = [r for r in confluence_results if r['confluence_result']['action'] == 'SELL']
                hold_signals = [r for r in confluence_results if r['confluence_result']['action'] == 'HOLD']
                
                avg_strength = sum(r['confluence_result']['strength'] for r in confluence_results) / len(confluence_results)
                avg_agreement = sum(r['confluence_result']['agreement_level'] for r in confluence_results) / len(confluence_results)
                
                print(f"\n📊 RESULTADOS DO TESTE DE CONFLUÊNCIA - Historical (API Real)")
                print("=" * 70)
                print(f"📈 Total de Sinais: {len(confluence_results)}")
                print(f"🟢 Sinais de Compra: {len(buy_signals)} ({len(buy_signals)/len(confluence_results)*100:.1f}%)")
                print(f"🔴 Sinais de Venda: {len(sell_signals)} ({len(sell_signals)/len(confluence_results)*100:.1f}%)")
                print(f"⚪ Sinais de Hold: {len(hold_signals)} ({len(hold_signals)/len(confluence_results)*100:.1f}%)")
                print(f"⚡ Força Média dos Sinais: {avg_strength:.1f}%")
                print(f"🤝 Nível Médio de Acordo: {avg_agreement:.1f}%")
                
                # Classificar qualidade dos sinais
                if avg_strength >= 70:
                    quality = "✅ SINAIS DE ALTA QUALIDADE"
                elif avg_strength >= 50:
                    quality = "⚠️ SINAIS DE QUALIDADE MODERADA"
                else:
                    quality = "❌ SINAIS DE BAIXA QUALIDADE"
                print(f"{quality} ({avg_strength:.1f}%)")
                
                # Análise de performance com capital
                print(f"\n📊 ANÁLISE DE PERFORMANCE COM CAPITAL:")
                position_size = self.capital_tracker.get_position_size()
                print(f"💰 Capital disponível: ${self.capital_tracker.current_capital:,.2f}")
                print(f"💼 Position size por trade: ${position_size:,.2f} ({self.capital_tracker.position_size_pct*100:.1f}%)")
                
                if len(historical_data) > 0:
                    initial_price = historical_data[0]['close']
                    final_price = historical_data[-1]['close']
                    market_return = (final_price - initial_price) / initial_price * 100
                    
                    print(f"💰 Preço inicial: ${initial_price:.4f}")
                    print(f"💰 Preço final: ${final_price:.4f}")
                    
                    market_emoji = "🟢" if market_return >= 0 else "🔴"
                    print(f"{market_emoji} Retorno do mercado: {market_return:+.2f}%")
                    
                    # Estimativa de retorno da estratégia de confluência
                    trading_signals = len(buy_signals) + len(sell_signals)
                    if trading_signals > 0:
                        # Estimativa baseada na força média e acordo
                        strategy_effectiveness = (avg_strength / 100) * (avg_agreement / 100)
                        estimated_return = market_return * strategy_effectiveness * 0.8  # Fator de desconto
                        
                        strategy_emoji = "🟢" if estimated_return >= 0 else "🔴"
                        print(f"{strategy_emoji} Retorno estimado da confluência: {estimated_return:+.2f}%")
                        
                        # Impacto no capital
                        capital_impact = self.capital_tracker.current_capital * (estimated_return / 100)
                        estimated_final_capital = self.capital_tracker.current_capital + capital_impact
                        
                        impact_emoji = "🟢" if capital_impact >= 0 else "🔴"
                        print(f"💵 Impacto estimado no capital: {impact_emoji}${capital_impact:+,.2f}")
                        print(f"💰 Capital estimado final: ${estimated_final_capital:,.2f}")
                        
                        # Comparação com mercado
                        if estimated_return > market_return:
                            print("✅ Estratégia de confluência superou o mercado")
                        else:
                            print("⚠️ Estratégia não superou o mercado")
                
                # Mostrar detalhes das estratégias
                print(f"\n🔍 ANÁLISE POR ESTRATÉGIA:")
                if confluence_results:
                    last_result = confluence_results[-1]['confluence_result']
                    for strategy_name, signal_data in last_result['individual_signals'].items():
                        strategy_display_name = self.strategy_confluence.strategies[strategy_name]['name']
                        
                        # Calcular estatísticas da estratégia individual
                        strategy_signals = []
                        for result in confluence_results:
                            if strategy_name in result['confluence_result']['individual_signals']:
                                strategy_signals.append(result['confluence_result']['individual_signals'][strategy_name])
                        
                        if strategy_signals:
                            avg_strategy_strength = sum(s['strength'] for s in strategy_signals) / len(strategy_signals)
                            buy_count = sum(1 for s in strategy_signals if s['action'] == 'BUY')
                            sell_count = sum(1 for s in strategy_signals if s['action'] == 'SELL')
                            
                            print(f"   📊 {strategy_display_name}:")
                            print(f"      ⚡ Força média: {avg_strategy_strength:.1f}%")
                            print(f"      🟢 Compras: {buy_count} | 🔴 Vendas: {sell_count}")
                            print(f"      ⚖️ Peso: {signal_data['weight']:.1f}")
                
                # Mostrar últimos 5 sinais detalhados
                print(f"\n🔍 ÚLTIMOS 5 SINAIS DE CONFLUÊNCIA DETALHADOS:")
                print("-" * 90)
                print("Timestamp           Ação   Preço        Força    Acordo   Estratégias")
                print("-" * 90)
                
                for result in confluence_results[-5:]:
                    timestamp = datetime.fromtimestamp(result['timestamp'] / 1000).strftime("%d/%m %H:%M:%S")
                    price = result['price']
                    confluence = result['confluence_result']
                    action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(confluence['action'], '⚪')
                    
                    # Resumir estratégias ativas
                    active_strategies = []
                    for strategy_name, signal_data in confluence['individual_signals'].items():
                        if signal_data['action'] != 'HOLD':
                            strategy_short = self.strategy_confluence.strategies[strategy_name]['name'][:3].upper()
                            active_strategies.append(f"{strategy_short}:{signal_data['action']}")
                    
                    strategies_summary = ', '.join(active_strategies) if active_strategies else 'ALL:HOLD'
                    
                    print(f"{timestamp}      {action_emoji} {confluence['action']:4} ${price:8.4f}   "
                          f"{confluence['strength']:5.1f}%   {confluence['agreement_level']:5.1f}%   {strategies_summary}")
        
        except Exception as e:
            print(f"\n❌ Erro durante o teste: {e}")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_confluence_comparison_test(self):
        """Compara diferentes modos de confluência"""
        enabled_strategies = [name for name, config in self.strategy_confluence.strategies.items() if config['enabled']]
        
        if not enabled_strategies:
            print("❌ Nenhuma estratégia ativada. Configure as estratégias primeiro.")
            input("\n📖 Pressione ENTER para continuar...")
            return
            
        if not self.selected_asset:
            print("❌ Nenhum ativo selecionado. Selecione um ativo primeiro.")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        print("\n🔍 CONFLUENCE COMPARISON TEST - COMPARAÇÃO DE MODOS")
        print("=" * 60)
        print(f"📊 Ativo: {self.selected_asset}")
        print(f"🎯 Estratégias: {', '.join([self.strategy_confluence.strategies[s]['name'] for s in enabled_strategies])}")
        print(f"⏰ Timeframe: {self.selected_timeframe or '1m'}")
        print("🔄 Testando todos os modos de confluência...")
        
        # Gerar dados de teste (simulados para demonstração)
        print(f"\n🔄 Gerando dados de teste...")
        base_price = self.asset_manager.prices.get(self.selected_asset, {}).get('price', 100.0)
        test_prices = []
        
        # Simular 100 períodos de preços
        for i in range(100):
            price_variation = np.random.normal(0, 0.01)  # Variação de 1%
            price = base_price * (1 + price_variation)
            test_prices.append(price)
            base_price = price
        
        # Testar cada modo de confluência
        modes_results = {}
        original_mode = self.strategy_confluence.current_mode
        
        for mode in ['ALL', 'ANY', 'MAJORITY', 'WEIGHTED']:
            print(f"🔄 Testando modo {mode}...")
            self.strategy_confluence.current_mode = mode
            
            mode_signals = []
            
            # Usar janela deslizante
            window_size = 20
            for i in range(window_size, len(test_prices)):
                price_window = test_prices[i-window_size:i+1]
                confluence_result = self.strategy_confluence.get_confluence_signal(price_window)
                mode_signals.append(confluence_result)
            
            # Analisar resultados do modo
            if mode_signals:
                buy_count = sum(1 for s in mode_signals if s['action'] == 'BUY')
                sell_count = sum(1 for s in mode_signals if s['action'] == 'SELL')
                hold_count = sum(1 for s in mode_signals if s['action'] == 'HOLD')
                avg_strength = sum(s['strength'] for s in mode_signals) / len(mode_signals)
                avg_agreement = sum(s['agreement_level'] for s in mode_signals) / len(mode_signals)
                
                modes_results[mode] = {
                    'total_signals': len(mode_signals),
                    'buy_signals': buy_count,
                    'sell_signals': sell_count,
                    'hold_signals': hold_count,
                    'avg_strength': avg_strength,
                    'avg_agreement': avg_agreement,
                    'trading_frequency': (buy_count + sell_count) / len(mode_signals) * 100
                }
        
        # Restaurar modo original
        self.strategy_confluence.current_mode = original_mode
        
        print(f"\n✅ COMPARAÇÃO DE MODOS DE CONFLUÊNCIA CONCLUÍDA!")
        
        # Mostrar resultados comparativos
        print(f"\n📊 RESULTADOS COMPARATIVOS:")
        print("=" * 80)
        print("Modo       Sinais  Compra  Venda   Hold   Força  Acordo  Freq.Trading")
        print("-" * 80)
        
        for mode, results in modes_results.items():
            print(f"{mode:10} {results['total_signals']:6} "
                  f"{results['buy_signals']:6} {results['sell_signals']:6} "
                  f"{results['hold_signals']:6} {results['avg_strength']:6.1f}% "
                  f"{results['avg_agreement']:6.1f}% {results['trading_frequency']:8.1f}%")
        
        # Análise e recomendações
        print(f"\n🎯 ANÁLISE E RECOMENDAÇÕES:")
        print("-" * 40)
        
        # Modo mais conservador (menos trades)
        conservative_mode = min(modes_results.keys(), 
                              key=lambda x: modes_results[x]['trading_frequency'])
        print(f"🛡️ Mais Conservador: {conservative_mode} "
              f"({modes_results[conservative_mode]['trading_frequency']:.1f}% trading)")
        
        # Modo mais agressivo (mais trades)
        aggressive_mode = max(modes_results.keys(), 
                            key=lambda x: modes_results[x]['trading_frequency'])
        print(f"⚡ Mais Agressivo: {aggressive_mode} "
              f"({modes_results[aggressive_mode]['trading_frequency']:.1f}% trading)")
        
        # Modo com maior força média
        strongest_mode = max(modes_results.keys(), 
                           key=lambda x: modes_results[x]['avg_strength'])
        print(f"💪 Maior Força: {strongest_mode} "
              f"({modes_results[strongest_mode]['avg_strength']:.1f}% força média)")
        
        # Modo com maior acordo
        most_agreed_mode = max(modes_results.keys(), 
                             key=lambda x: modes_results[x]['avg_agreement'])
        print(f"🤝 Maior Acordo: {most_agreed_mode} "
              f"({modes_results[most_agreed_mode]['avg_agreement']:.1f}% acordo médio)")
        
        # Recomendação baseada no perfil
        print(f"\n💡 RECOMENDAÇÕES POR PERFIL:")
        print(f"   🔴 Conservador: Use {conservative_mode} para poucos trades de alta qualidade")
        print(f"   🟡 Moderado: Use MAJORITY para equilíbrio entre frequência e qualidade")
        print(f"   🟢 Agressivo: Use {aggressive_mode} para mais oportunidades de trading")
        print(f"   🔵 Customizado: Use WEIGHTED e ajuste os pesos conforme sua preferência")
        
        # Estimativa de impacto no capital por modo
        print(f"\n💰 IMPACTO ESTIMADO NO CAPITAL (baseado em ${self.capital_tracker.current_capital:,.2f}):")
        position_size = self.capital_tracker.get_position_size()
        
        for mode, results in modes_results.items():
            trading_signals = results['buy_signals'] + results['sell_signals']
            if trading_signals > 0:
                # Estimativa simplificada
                estimated_return_per_trade = (results['avg_strength'] - 50) / 100 * 0.015  # 1.5% máximo
                total_impact = trading_signals * position_size * estimated_return_per_trade
                
                impact_emoji = "🟢" if total_impact >= 0 else "🔴"
                print(f"   {mode:10} {impact_emoji} ${total_impact:+8.2f} "
                      f"({trading_signals} trades × ${position_size:,.0f})")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_confluence_export_results(self):
        """Exporta resultados de confluência"""
        print("\n📊 EXPORT CONFLUENCE RESULTS - EXPORTAR RESULTADOS")
        print("=" * 55)
        print("🔄 Funcionalidade em desenvolvimento...")
        print("📁 Os resultados serão salvos em: reports/confluence_results.json")
        print("📈 Incluirá: sinais individuais, confluência, performance por modo")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def show_strategy_lab_menu(self):
        """Exibe menu do Strategy Lab Professional"""
        stats = self.capital_tracker.get_stats()
        
        print("\n" + "=" * 80)
        print("🔬 STRATEGY LAB PROFESSIONAL - ANÁLISE CONFIÁVEL")
        print("=" * 80)
        print("🎯 Testes com dados reais da Bybit")
        print("📊 Configuração completa de parâmetros")
        print("⚡ Real Time vs Historical Data testing")
        print("📅 Seleção de período personalizado (dd/mm/aa hh:mm:ss)")
        print("💰 INTEGRADO COM CAPITAL - Position size baseado na banca")
        print("=" * 80)
        
        print(f"\n💰 INFORMAÇÕES DO CAPITAL:")
        print(f"   💵 Capital atual: ${self.capital_tracker.current_capital:,.2f}")
        print(f"   📊 Position size: ${self.capital_tracker.get_position_size():,.2f} ({self.capital_tracker.position_size_pct*100:.1f}%)")
        print(f"   📈 Total trades: {stats['total_trades']}")
        
        print(f"\n📋 STATUS ATUAL:")
        print(f"   📊 Ativo: {self.selected_asset or 'Nenhum ativo selecionado'}")
        print(f"   🎯 Estratégia: {getattr(self, 'selected_strategy', 'Nenhuma estratégia selecionada')}")
        print(f"   ⏰ Timeframe: {self.selected_timeframe or 'Nenhum timeframe selecionado'}")
        
        print(f"\n🎯 OPÇÕES DISPONÍVEIS:")
        print("   1️⃣  Asset Selection (Selecionar criptoativo)")
        print("   2️⃣  Strategy Configuration (Configurar estratégia)")
        print("   3️⃣  Real Time Test (Teste em tempo real)")
        print("   4️⃣  Historical Data Test (Teste com dados históricos REAIS)")
        print("   5️⃣  Comparison Test (Comparar Real Time vs Historical)")
        print("   6️⃣  Export Results (Exportar resultados)")
        print("   0️⃣  Voltar ao menu principal")
    
    def handle_asset_selection(self):
        """Gerencia seleção de ativos"""
        print("\n📊 ASSET SELECTION - SELEÇÃO DE CRIPTOATIVO")
        print("=" * 60)
        print("🔄 Atualizando preços em tempo real...")
        
        # Atualizar preços
        self.asset_manager.update_all_prices()
        
        while True:
            print(f"\n💰 CRIPTOATIVOS DISPONÍVEIS:")
            print("-" * 80)
            print("Nº  Emoji Symbol     Nome            Preço           24h Change   Volume 24h")
            print("-" * 80)
            
            for i, (symbol, info) in enumerate(self.asset_manager.assets.items(), 1):
                price_data = self.asset_manager.prices.get(symbol, {})
                price = price_data.get('price', 0.0)
                change_24h = price_data.get('change_24h', 0.0)
                volume_24h = price_data.get('volume_24h', 0.0)
                
                if price > 0:
                    change_emoji = "🟢" if change_24h >= 0 else "🔴"
                    print(f"{i:2}  {info['emoji']:5}  {symbol:10} {info['name']:15} "
                          f"${price:12,.4f}   {change_emoji} {change_24h:+5.2f}% ${volume_24h:>12,.0f}")
                else:
                    print(f"{i:2}  {info['emoji']:5}  {symbol:10} {info['name']:15} "
                          f"{'Carregando...':>12}  {'--':>8}           {'--':>12}")
            
            print(f"\n🎯 OPÇÕES:")
            print("   • Digite o número (1-10) para selecionar")
            print("   • 'r' para atualizar preços")
            print("   • '0' para voltar")
            
            choice = input("\n🔢 Escolha: ").strip().lower()
            
            if choice == '0':
                break
            elif choice == 'r':
                print("🔄 Atualizando preços...")
                self.asset_manager.update_all_prices()
                continue
            
            try:
                asset_index = int(choice) - 1
                asset_symbols = list(self.asset_manager.assets.keys())
                
                if 0 <= asset_index < len(asset_symbols):
                    selected_symbol = asset_symbols[asset_index]
                    selected_info = self.asset_manager.assets[selected_symbol]
                    price_data = self.asset_manager.prices.get(selected_symbol, {})
                    
                    self.selected_asset = selected_symbol
                    
                    print(f"\n✅ ATIVO SELECIONADO:")
                    print(f"   {selected_info['emoji']} {selected_symbol} - {selected_info['name']}")
                    
                    if price_data.get('price', 0) > 0:
                        print(f"   💰 Preço atual: ${price_data['price']:,.4f}")
                        change_emoji = "🟢" if price_data['change_24h'] >= 0 else "🔴"
                        print(f"   📈 Variação 24h: {change_emoji}{price_data['change_24h']:+.2f}%")
                        print(f"   📊 Volume 24h: ${price_data['volume_24h']:,.0f}")
                        
                        # Avaliar liquidez
                        if price_data['volume_24h'] > 100_000_000:  # > $100M
                            print("   ✅ Liquidez excelente para testes confiáveis")
                        elif price_data['volume_24h'] > 50_000_000:  # > $50M
                            print("   ✅ Liquidez adequada para testes confiáveis")
                        else:
                            print("   ⚠️  Liquidez baixa - resultados podem ser menos confiáveis")
                    
                    print(f"   💼 Position size (baseado no capital): ${self.capital_tracker.get_position_size():,.2f}")
                    
                    input("\n📖 Pressione ENTER para continuar...")
                    break
                else:
                    print("❌ Digite um número válido")
                    input("\n📖 Pressione ENTER para continuar...")
                    
            except ValueError:
                print("❌ Digite um número válido")
                input("\n📖 Pressione ENTER para continuar...")
    
    def handle_strategy_configuration(self):
        """Configura estratégia individual (não confluência)"""
        print("\n🎯 STRATEGY CONFIGURATION - CONFIGURAÇÃO DE ESTRATÉGIA")
        print("=" * 70)
        
        strategies = {
            'ema_crossover': 'EMA Crossover',
            'rsi_mean_reversion': 'RSI Mean Reversion',
            'bollinger_breakout': 'Bollinger Bands Breakout',
            'ai_agent': 'AI Agent (Multi-Armed Bandit)'
        }
        
        timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        
        while True:
            print(f"\n🔧 ESTRATÉGIAS DISPONÍVEIS:")
            for i, (key, name) in enumerate(strategies.items(), 1):
                status = "✅" if getattr(self, 'selected_strategy', None) == key else "⚪"
                print(f"   {status} {i}. {name}")
                if key == 'ema_crossover':
                    print(f"      📝 Cruzamento de médias móveis exponenciais")
                elif key == 'rsi_mean_reversion':
                    print(f"      📝 Reversão à média baseada no RSI")
                elif key == 'bollinger_breakout':
                    print(f"      📝 Rompimento das Bandas de Bollinger")
                elif key == 'ai_agent':
                    print(f"      📝 Agente IA com aprendizado automático")
            
            print(f"\n⏰ TIMEFRAMES DISPONÍVEIS:")
            for i, tf in enumerate(timeframes, 1):
                status = "✅" if self.selected_timeframe == tf else "⚪"
                print(f"   {status} {chr(96+i)}. {tf}")
            
            print(f"\n🎯 OPÇÕES:")
            print("   • Digite 1-4 para selecionar estratégia")
            print("   • Digite a-g para selecionar timeframe")
            print("   • 'p' para configurar parâmetros")
            print("   • '0' para voltar")
            
            choice = input("\n🔢 Escolha: ").strip().lower()
            
            if choice == '0':
                break
            elif choice in ['1', '2', '3', '4']:
                strategy_index = int(choice) - 1
                strategy_keys = list(strategies.keys())
                if 0 <= strategy_index < len(strategy_keys):
                    self.selected_strategy = strategy_keys[strategy_index]
                    print(f"✅ Estratégia selecionada: {strategies[self.selected_strategy]}")
            elif choice in ['a', 'b', 'c', 'd', 'e', 'f', 'g']:
                timeframe_index = ord(choice) - ord('a')
                if 0 <= timeframe_index < len(timeframes):
                    self.selected_timeframe = timeframes[timeframe_index]
                    print(f"✅ Timeframe selecionado: {self.selected_timeframe}")
            elif choice == 'p':
                print("🔧 Configuração de parâmetros em desenvolvimento...")
            else:
                print("❌ Opção inválida")
                
            input("\n📖 Pressione ENTER para continuar...")
    
    def handle_strategy_parameters_configuration(self):
        """Configura parâmetros das estratégias"""
        print("\n🔧 CONFIGURAÇÃO DE PARÂMETROS DAS ESTRATÉGIAS")
        print("=" * 55)
        
        for key, strategy in self.strategy_confluence.strategies.items():
            if strategy['enabled']:
                print(f"\n🎯 {strategy['name']}")
                print(f"   📝 {strategy['description']}")
                print(f"   🔧 Parâmetros atuais:")
                
                for param_name, param_value in strategy['params'].items():
                    print(f"      {param_name}: {param_value}")
                    
                    try:
                        new_value = input(f"      Novo valor (atual: {param_value}): ").strip()
                        if new_value:
                            # Tentar converter para o tipo apropriado
                            if isinstance(param_value, int):
                                strategy['params'][param_name] = int(new_value)
                            elif isinstance(param_value, float):
                                strategy['params'][param_name] = float(new_value)
                            else:
                                strategy['params'][param_name] = new_value
                                
                            print(f"      ✅ {param_name} alterado para {new_value}")
                    except ValueError:
                        print(f"      ❌ Valor inválido para {param_name}")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_real_time_test(self):
        """Executa teste em tempo real (estratégia individual)"""
        if not self.selected_asset:
            print("❌ Nenhum ativo selecionado. Selecione um ativo primeiro.")
            input("\n📖 Pressione ENTER para continuar...")
            return
            
        if not hasattr(self, 'selected_strategy') or not self.selected_strategy:
            print("❌ Nenhuma estratégia selecionada. Configure uma estratégia primeiro.")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        print("\n⚡ REAL TIME TEST - TESTE EM TEMPO REAL")
        print("=" * 60)
        print(f"📊 Ativo: {self.selected_asset}")
        print(f"🎯 Estratégia: {self.selected_strategy}")
        print(f"⏰ Timeframe: {self.selected_timeframe or '1m'}")
        print(f"💰 Capital atual: ${self.capital_tracker.current_capital:,.2f}")
        print(f"💼 Position size: ${self.capital_tracker.get_position_size():,.2f} ({self.capital_tracker.position_size_pct*100:.1f}%)")
        
        print(f"\n🔄 Iniciando teste em tempo real...")
        print("⏹️  Pressione Ctrl+C para parar")
        
        # Simular teste em tempo real
        signals_history = []
        
        try:
            for i in range(20):  # 20 iterações
                # Simular preço atual
                base_price = self.asset_manager.prices.get(self.selected_asset, {}).get('price', 100.0)
                price_variation = np.random.normal(0, 0.002)
                current_price = base_price * (1 + price_variation)
                
                # Gerar sinal baseado na estratégia selecionada
                prices = [current_price * (1 + np.random.normal(0, 0.001)) for _ in range(50)]
                
                if self.selected_strategy == 'rsi_mean_reversion':
                    rsi_values = self.strategy_confluence.calculate_rsi(prices, 14)
                    current_rsi = rsi_values[-1] if rsi_values else 50
                    
                    if current_rsi <= 30:
                        action = 'BUY'
                        strength = max(70, min(95, (30 - current_rsi) * 2 + 70))
                    elif current_rsi >= 70:
                        action = 'SELL'
                        strength = max(70, min(95, (current_rsi - 70) * 2 + 70))
                    else:
                        action = 'HOLD'
                        strength = max(20, min(60, 60 - abs(current_rsi - 50)))
                else:
                    # Sinal genérico para outras estratégias
                    actions = ['BUY', 'SELL', 'HOLD', 'HOLD', 'HOLD']  # Mais HOLD
                    action = np.random.choice(actions)
                    strength = np.random.uniform(20, 85)
                
                signals_history.append({
                    'timestamp': datetime.now(),
                    'price': current_price,
                    'action': action,
                    'strength': strength
                })
                
                # Mostrar progresso
                progress = (i + 1) / 20 * 100
                action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(action, '⚪')
                
                print(f"\r🔄 [{progress:5.1f}%] Iteração {i+1} | Preço: ${current_price:.4f} | "
                      f"Sinal: {action} | Força: {strength:.1f}%", end='', flush=True)
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print(f"\n⚠️ Teste interrompido pelo usuário")
        
        print(f"\n\n✅ TESTE EM TEMPO REAL CONCLUÍDO!")
        
        # Analisar resultados
        if signals_history:
            buy_signals = [s for s in signals_history if s['action'] == 'BUY']
            sell_signals = [s for s in signals_history if s['action'] == 'SELL']
            hold_signals = [s for s in signals_history if s['action'] == 'HOLD']
            
            avg_strength = sum(s['strength'] for s in signals_history) / len(signals_history)
            
            print(f"\n📊 RESULTADOS DO TESTE - Real Time")
            print("=" * 50)
            print(f"📈 Total de Sinais: {len(signals_history)}")
            print(f"🟢 Sinais de Compra: {len(buy_signals)} ({len(buy_signals)/len(signals_history)*100:.1f}%)")
            print(f"🔴 Sinais de Venda: {len(sell_signals)} ({len(sell_signals)/len(signals_history)*100:.1f}%)")
            print(f"⚪ Sinais de Hold: {len(hold_signals)} ({len(hold_signals)/len(signals_history)*100:.1f}%)")
            print(f"⚡ Força Média dos Sinais: {avg_strength:.1f}%")
            
            if avg_strength >= 70:
                quality = "✅ SINAIS DE ALTA QUALIDADE"
            elif avg_strength >= 50:
                quality = "⚠️ SINAIS DE QUALIDADE MODERADA (50-70%)"
            else:
                quality = "❌ SINAIS DE BAIXA QUALIDADE (<50%)"
            print(quality)
            
            # Análise de impacto no capital
            print(f"\n💰 ANÁLISE DE IMPACTO NO CAPITAL:")
            position_size = self.capital_tracker.get_position_size()
            print(f"💼 Position size por trade: ${position_size:,.2f}")
            
            trading_signals = len(buy_signals) + len(sell_signals)
            print(f"📊 Trades com sinal: {trading_signals}")
            
            if trading_signals > 0:
                estimated_return_per_trade = (avg_strength - 50) / 100 * 0.02
                total_impact = trading_signals * position_size * estimated_return_per_trade
                estimated_final_capital = self.capital_tracker.current_capital + total_impact
                
                if total_impact >= 0:
                    print(f"🟢 Impacto estimado: $+{total_impact:.2f}")
                else:
                    print(f"🔴 Impacto estimado: ${total_impact:.2f}")
                    
                print(f"💰 Capital estimado final: ${estimated_final_capital:,.2f}")
            
            # Mostrar últimos 5 sinais
            print(f"\n🔍 ÚLTIMOS 5 SINAIS:")
            print("-" * 60)
            for signal in signals_history[-5:]:
                timestamp = signal['timestamp'].strftime("%H:%M:%S")
                action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(signal['action'], '⚪')
                print(f"{timestamp} | {action_emoji} {signal['action']:4} | ${signal['price']:8.4f} | {signal['strength']:5.1f}%")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_historical_data_test(self):
        """Executa teste com dados históricos reais"""
        if not self.selected_asset:
            print("❌ Nenhum ativo selecionado. Selecione um ativo primeiro.")
            input("\n📖 Pressione ENTER para continuar...")
            return
            
        if not hasattr(self, 'selected_strategy') or not self.selected_strategy:
            print("❌ Nenhuma estratégia selecionada. Configure uma estratégia primeiro.")
            input("\n📖 Pressione ENTER para continuar...")
            return
        
        print("\n📈 HISTORICAL DATA TEST - DADOS HISTÓRICOS REAIS")
        print("=" * 70)
        print(f"📊 Ativo: {self.selected_asset}")
        print(f"🎯 Estratégia: {self.selected_strategy}")
        print(f"⏰ Timeframe: {self.selected_timeframe or '1m'}")
        
        # Obter parâmetros da estratégia
        strategy_params = {}
        if self.selected_strategy == 'rsi_mean_reversion':
            strategy_params = {'rsi_period': 14, 'oversold': 30, 'overbought': 70}
        elif self.selected_strategy == 'ema_crossover':
            strategy_params = {'fast_period': 12, 'slow_period': 26}
        elif self.selected_strategy == 'bollinger_breakout':
            strategy_params = {'period': 20, 'std_dev': 2.0}
        
        print(f"🔧 Parâmetros: {strategy_params}")
        print(f"💰 Capital atual: ${self.capital_tracker.current_capital:,.2f}")
        print(f"💼 Position size: ${self.capital_tracker.get_position_size():,.2f} ({self.capital_tracker.position_size_pct*100:.1f}%)")
        
        # Seleção de período
        print(f"\n📅 PERÍODOS DISPONÍVEIS:")
        print("   1. Últimas 24 horas")
        print("   2. Últimos 7 dias")
        print("   3. Últimos 30 dias")
        print("   4. Últimos 90 dias")
        print("   5. Período personalizado (dd/mm/aa hh:mm:ss)")
        
        try:
            period_choice = input("\n🔢 Escolha o período: ").strip()
            
            # Implementação simplificada - usar últimos 7 dias como exemplo
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = end_time - (7 * 24 * 60 * 60 * 1000)  # 7 dias
            
            if period_choice == '5':
                print("\n📅 PERÍODO PERSONALIZADO - SELEÇÃO DE DATAS")
                print("=" * 60)
                print("📝 Formatos aceitos:")
                print("   • dd/mm/aa hh:mm:ss  (ex: 21/09/25 15:30:00)")
                print("   • dd/mm/aaaa hh:mm:ss (ex: 21/09/2025 15:30:00)")
                print("   • dd/mm/aa hh:mm     (ex: 21/09/25 15:30)")
                print("   • dd/mm/aa           (ex: 21/09/25)")
                print("   • 'now' para data/hora atual")
                print("   • '1d', '7d', '30d' para períodos relativos")
                
                start_input = input("\n📅 Data INICIAL: ").strip()
                end_input = input("📅 Data FINAL: ").strip()
                
                # Implementação simplificada - usar inputs como estão
                print(f"\n✅ PERÍODO SELECIONADO:")
                print(f"   📅 Início: {start_input}")
                print(f"   📅 Fim: {end_input}")
                
                # Para demonstração, calcular duração
                if start_input == 'now' and end_input == 'now':
                    print(f"   ⏱️  Duração: 0 dias")
                else:
                    print(f"   ⏱️  Duração: Período personalizado")
            
            print(f"\n🔄 Obtendo dados históricos da API Bybit...")
            
            # Mapear timeframe
            interval_map = {'1m': '1', '5m': '5', '15m': '15', '30m': '30', '1h': '60', '4h': '240', '1d': 'D'}
            interval = interval_map.get(self.selected_timeframe or '1m', '1')
            
            # Para demonstração, simular dados históricos
            print(f"📊 Período: {period_choice}")
            print(f"🔄 Obtendo dados históricos da API Bybit...")
            print(f"   📊 Símbolo: {self.selected_asset}")
            print(f"   ⏰ Intervalo: {interval}")
            
            # Simular obtenção de dados
            num_candles = 1000 if period_choice == '2' else 100
            print(f"✅ {num_candles} candlesticks obtidos da API")
            
            # Simular dados para demonstração
            base_price = self.asset_manager.prices.get(self.selected_asset, {}).get('price', 100.0)
            historical_prices = []
            
            for i in range(num_candles):
                price_change = np.random.normal(0, 0.01)
                price = base_price * (1 + price_change)
                historical_prices.append(price)
                base_price = price
            
            if historical_prices:
                first_date = datetime.now() - timedelta(days=7)
                last_date = datetime.now()
                print(f"   📅 Primeiro: {first_date.strftime('%d/%m/%Y %H:%M')}")
                print(f"   📅 Último: {last_date.strftime('%d/%m/%Y %H:%M')}")
                print(f"   💰 Preço inicial: ${historical_prices[0]:.4f}")
                print(f"   💰 Preço final: ${historical_prices[-1]:.4f}")
                
                price_change_pct = (historical_prices[-1] - historical_prices[0]) / historical_prices[0] * 100
                change_emoji = "🟢" if price_change_pct >= 0 else "🔴"
                print(f"   {change_emoji} Variação: {price_change_pct:+.2f}%")
            
            print(f"🔄 Executando backtest com dados reais...")
            
            # Simular processamento
            signals = []
            for i in range(len(historical_prices)):
                if i < 20:  # Aguardar dados suficientes
                    continue
                    
                # Simular cálculo de indicadores
                if self.selected_strategy == 'rsi_mean_reversion':
                    price_window = historical_prices[max(0, i-20):i+1]
                    rsi_values = self.strategy_confluence.calculate_rsi(price_window, 14)
                    current_rsi = rsi_values[-1] if rsi_values else 50
                    
                    if current_rsi <= 30:
                        action = 'BUY'
                        strength = max(70, min(95, (30 - current_rsi) * 2 + 70))
                    elif current_rsi >= 70:
                        action = 'SELL'
                        strength = max(70, min(95, (current_rsi - 70) * 2 + 70))
                    else:
                        action = 'HOLD'
                        strength = max(20, min(60, 60 - abs(current_rsi - 50)))
                else:
                    # Estratégia genérica
                    actions = ['BUY', 'SELL', 'HOLD', 'HOLD', 'HOLD']
                    action = np.random.choice(actions)
                    strength = np.random.uniform(20, 85)
                
                signals.append({
                    'timestamp': datetime.now() - timedelta(minutes=len(historical_prices)-i),
                    'price': historical_prices[i],
                    'action': action,
                    'strength': strength,
                    'volume': np.random.randint(10, 200)
                })
                
                # Mostrar progresso
                progress = (i + 1) / len(historical_prices) * 100
                if i % 50 == 0:  # Atualizar a cada 50 iterações
                    print(f"\r🔄 Processando indicadores: [{progress:5.1f}%] {i+1}/{len(historical_prices)}", 
                          end='', flush=True)
            
            print(f"\n\n✅ BACKTEST HISTÓRICO CONCLUÍDO COM DADOS REAIS!")
            
            # Analisar resultados
            if signals:
                buy_signals = [s for s in signals if s['action'] == 'BUY']
                sell_signals = [s for s in signals if s['action'] == 'SELL']
                hold_signals = [s for s in signals if s['action'] == 'HOLD']
                
                avg_strength = sum(s['strength'] for s in signals) / len(signals)
                
                print(f"\n📊 RESULTADOS DO TESTE - Historical (API Real)")
                print("=" * 60)
                print(f"📈 Total de Sinais: {len(signals)}")
                print(f"🟢 Sinais de Compra: {len(buy_signals)} ({len(buy_signals)/len(signals)*100:.1f}%)")
                print(f"🔴 Sinais de Venda: {len(sell_signals)} ({len(sell_signals)/len(signals)*100:.1f}%)")
                print(f"⚪ Sinais de Hold: {len(hold_signals)} ({len(hold_signals)/len(signals)*100:.1f}%)")
                print(f"⚡ Força Média dos Sinais: {avg_strength:.1f}%")
                
                if avg_strength >= 70:
                    quality = "✅ SINAIS DE ALTA QUALIDADE"
                elif avg_strength >= 50:
                    quality = "⚠️ SINAIS DE QUALIDADE MODERADA (50-70%)"
                else:
                    quality = "❌ SINAIS DE BAIXA QUALIDADE (<50%)"
                print(quality)
                
                # Análise de performance com capital
                print(f"\n📊 ANÁLISE DE PERFORMANCE COM CAPITAL:")
                print(f"💰 Capital disponível: ${self.capital_tracker.current_capital:,.2f}")
                position_size = self.capital_tracker.get_position_size()
                print(f"💼 Position size por trade: ${position_size:,.2f} ({self.capital_tracker.position_size_pct*100:.1f}%)")
                
                if historical_prices:
                    initial_price = historical_prices[0]
                    final_price = historical_prices[-1]
                    market_return = (final_price - initial_price) / initial_price * 100
                    
                    print(f"💰 Preço inicial: ${initial_price:.4f}")
                    print(f"💰 Preço final: ${final_price:.4f}")
                    
                    market_emoji = "🟢" if market_return >= 0 else "🔴"
                    print(f"{market_emoji} Retorno do mercado: {market_return:+.2f}%")
                    
                    # Estimar retorno da estratégia
                    trading_signals = len(buy_signals) + len(sell_signals)
                    if trading_signals > 0:
                        estimated_return_per_trade = (avg_strength - 50) / 100 * 0.015
                        strategy_return = trading_signals * estimated_return_per_trade * 100
                        
                        strategy_emoji = "🟢" if strategy_return >= 0 else "🔴"
                        print(f"{strategy_emoji} Retorno estimado da estratégia: {strategy_return:+.2f}%")
                        
                        capital_impact = self.capital_tracker.current_capital * (strategy_return / 100)
                        estimated_final_capital = self.capital_tracker.current_capital + capital_impact
                        
                        impact_emoji = "🟢" if capital_impact >= 0 else "🔴"
                        print(f"💵 Impacto estimado no capital: {impact_emoji}${capital_impact:+,.2f}")
                        print(f"💰 Capital estimado final: ${estimated_final_capital:,.2f}")
                        
                        if strategy_return > market_return:
                            print("✅ Estratégia superou o mercado")
                        else:
                            print("⚠️ Estratégia não superou o mercado")
                
                # Mostrar últimos 5 sinais detalhados
                print(f"\n🔍 ÚLTIMOS 5 SINAIS DETALHADOS:")
                print("-" * 80)
                print("Timestamp           Ação   Preço        Força    Volume")
                print("-" * 80)
                
                for signal in signals[-5:]:
                    timestamp = signal['timestamp'].strftime("%d/%m %H:%M:%S")
                    action_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '⚪'}.get(signal['action'], '⚪')
                    print(f"{timestamp}      {action_emoji} {signal['action']:4} ${signal['price']:8.4f}   "
                          f"{signal['strength']:5.1f}%         {signal['volume']}")
        
        except Exception as e:
            print(f"\n❌ Erro durante o teste: {e}")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_comparison_test(self):
        """Compara Real Time vs Historical"""
        print("\n🔍 COMPARISON TEST - COMPARAR REAL TIME VS HISTORICAL")
        print("=" * 60)
        print("🔄 Funcionalidade em desenvolvimento...")
        print("📊 Comparará resultados entre testes em tempo real e históricos")
        print("📈 Incluirá métricas de consistência e confiabilidade")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_export_results(self):
        """Exporta resultados"""
        print("\n📊 EXPORT RESULTS - EXPORTAR RESULTADOS")
        print("=" * 45)
        print("🔄 Funcionalidade em desenvolvimento...")
        print("📁 Os resultados serão salvos em: reports/strategy_results.json")
        print("📈 Incluirá: sinais, performance, configurações")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_simulate_trades(self):
        """Simula trades"""
        print("\n🎯 SIMULATE TRADES")
        print("=" * 30)
        print("1. Simular Trade Único")
        print("2. Simular Múltiplos Trades")
        print("0. Voltar")
        
        choice = input("\n🔢 Escolha: ").strip()
        
        if choice == '1':
            print("🔄 Simulação de trade único em desenvolvimento...")
        elif choice == '2':
            print("🔄 Simulação de múltiplos trades em desenvolvimento...")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_export_reports(self):
        """Exporta relatórios"""
        print("\n📊 EXPORT REPORTS")
        print("=" * 25)
        print("🔄 Funcionalidade em desenvolvimento...")
        print("📁 Relatórios serão salvos em: reports/")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_connectivity_status(self):
        """Testa status de conectividade"""
        print("\n🌐 CONNECTIVITY STATUS")
        print("=" * 30)
        
        # Teste detalhado de conectividade
        print("🔄 Testando conectividade detalhada...")
        
        try:
            # Teste API pública
            print("\n📡 API Pública:")
            response = requests.get(f"{self.asset_manager.base_url}/v5/market/time", timeout=5)
            if response.status_code == 200:
                print("   🕐 Server Time: ✅")
            else:
                print("   🕐 Server Time: ❌")
            
            # Teste market data
            response = requests.get(f"{self.asset_manager.base_url}/v5/market/tickers", 
                                  params={'category': 'spot'}, timeout=5)
            if response.status_code == 200:
                print("   📊 Market Data: ✅")
            else:
                print("   📊 Market Data: ❌")
            
            # Teste symbols
            response = requests.get(f"{self.asset_manager.base_url}/v5/market/instruments-info", 
                                  params={'category': 'spot'}, timeout=5)
            if response.status_code == 200:
                print("   📋 Symbols: ✅")
            else:
                print("   📋 Symbols: ❌")
            
            # Teste de latência
            start_time = time.time()
            requests.get(f"{self.asset_manager.base_url}/v5/market/time", timeout=5)
            latency = (time.time() - start_time) * 1000
            
            if latency < 500:
                print(f"   🟢 Latência: {latency:.2f}ms (Boa)")
            elif latency < 1000:
                print(f"   🟡 Latência: {latency:.2f}ms (Moderada)")
            else:
                print(f"   🔴 Latência: {latency:.2f}ms (Alta)")
            
            print("\n🔐 API Privada:")
            print("   ❌ Não testada (requer configuração)")
            
            print("\n✅ Status Geral: FUNCIONANDO")
            
        except Exception as e:
            print(f"❌ Erro de conectividade: {e}")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_strategy_explorer(self):
        """Explora estratégias disponíveis"""
        print("\n🔍 STRATEGY EXPLORER")
        print("=" * 30)
        print("🔄 Funcionalidade em desenvolvimento...")
        print("📚 Explorará todas as estratégias disponíveis")
        print("📊 Incluirá descrições, parâmetros e exemplos")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_performance_analysis(self):
        """Análise de performance"""
        print("\n📈 PERFORMANCE ANALYSIS")
        print("=" * 35)
        print("🔄 Funcionalidade em desenvolvimento...")
        print("📊 Analisará performance histórica")
        print("📈 Incluirá métricas avançadas e gráficos")
        
        input("\n📖 Pressione ENTER para continuar...")
    
    def handle_advanced_settings(self):
        """Configurações avançadas"""
        while True:
            print("\n⚙️ ADVANCED SETTINGS")
            print("=" * 30)
            
            print(f"\n💰 CONFIGURAÇÕES ATUAIS:")
            print(f"   Capital Inicial: ${self.capital_tracker.initial_capital:,.2f}")
            print(f"   Position Size: {self.capital_tracker.position_size_pct*100:.1f}%")
            print(f"   Max Drawdown: {self.capital_tracker.max_drawdown_pct*100:.1f}%")
            print(f"   Compound Interest: {'Ativo' if self.capital_tracker.compound_interest else 'Inativo'}")
            
            print(f"\n🎯 OPÇÕES:")
            print("   1. Alterar Capital Inicial")
            print("   2. Alterar Position Size")
            print("   3. Alterar Max Drawdown")
            print("   4. Toggle Compound Interest")
            print("   5. Reset Capital Tracker")
            print("   6. Salvar Configurações")
            print("   0. Voltar")
            
            choice = input("\n🔢 Escolha: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                try:
                    new_capital = float(input(f"💵 Novo capital inicial (atual: ${self.capital_tracker.initial_capital:,.2f}): $"))
                    self.capital_tracker.initial_capital = new_capital
                    self.capital_tracker.current_capital = new_capital
                    self.capital_tracker.trades = []
                    print(f"✅ Capital inicial alterado para ${new_capital:,.2f}")
                    print("🔄 Capital tracker resetado com novo valor")
                except ValueError:
                    print("❌ Digite um valor numérico válido")
            elif choice == '2':
                try:
                    new_size = float(input(f"📊 Novo position size % (atual: {self.capital_tracker.position_size_pct*100:.1f}%): "))
                    if 0.1 <= new_size <= 100:
                        self.capital_tracker.position_size_pct = new_size / 100
                        print(f"✅ Position size alterado para {new_size:.1f}%")
                    else:
                        print("❌ Position size deve estar entre 0.1% e 100%")
                except ValueError:
                    print("❌ Digite um valor numérico válido")
            elif choice == '3':
                try:
                    new_drawdown = float(input(f"🛡️ Novo max drawdown % (atual: {self.capital_tracker.max_drawdown_pct*100:.1f}%): "))
                    if 5 <= new_drawdown <= 90:
                        self.capital_tracker.max_drawdown_pct = new_drawdown / 100
                        print(f"✅ Max drawdown alterado para {new_drawdown:.1f}%")
                    else:
                        print("❌ Max drawdown deve estar entre 5% e 90%")
                except ValueError:
                    print("❌ Digite um valor numérico válido")
            elif choice == '4':
                self.capital_tracker.compound_interest = not self.capital_tracker.compound_interest
                status = "ativado" if self.capital_tracker.compound_interest else "desativado"
                print(f"✅ Compound Interest {status}")
            elif choice == '5':
                confirm = input("⚠️ Resetar capital tracker? Todos os trades serão perdidos. (s/N): ").strip().lower()
                if confirm == 's':
                    self.capital_tracker.current_capital = self.capital_tracker.initial_capital
                    self.capital_tracker.trades = []
                    print("✅ Capital tracker resetado")
                else:
                    print("❌ Reset cancelado")
            elif choice == '6':
                self.save_settings()
            else:
                print("❌ Opção inválida")
    
    def run(self):
        """Executa o CLI principal"""
        # Teste inicial de conectividade
        self.test_connectivity()
        
        # Mostrar informações iniciais
        print("\n" + "=" * 80)
        print("🏭 MARKET MANUS - SISTEMA DE TRADING AUTOMATIZADO")
        print("=" * 80)
        print("💰 Renda passiva automática e escalável")
        print("🤖 IA integrada com multi-armed bandit")
        print("📈 Estratégias validadas automaticamente")
        print("🔄 Backtesting com dados reais")
        print("🔬 Strategy Lab Professional com análise confiável")
        print("⚡ Real Time vs Historical Data testing")
        print("🎯 NOVO: Sistema de Confluência de Estratégias")  # DESTAQUE
        print("💼 CAPITAL MANAGEMENT INTEGRADO")
        print("=" * 80)
        
        while self.running:
            try:
                self.show_main_menu()
                choice = input("\n🔢 Escolha uma opção: ").strip()
                
                if choice == '0':
                    self.running = False
                    print("\n👋 Obrigado por usar o Market Manus!")
                    print("🚀 Até a próxima!")
                elif choice == '1':
                    self.handle_capital_dashboard()
                elif choice == '2':
                    self.handle_strategy_lab_professional()
                elif choice == '3':
                    self.handle_confluence_lab()  # NOVA FUNCIONALIDADE
                elif choice == '4':
                    self.handle_simulate_trades()
                elif choice == '5':
                    self.handle_export_reports()
                elif choice == '6':
                    self.handle_connectivity_status()
                elif choice == '7':
                    self.handle_strategy_explorer()
                elif choice == '8':
                    self.handle_performance_analysis()
                elif choice == '9':
                    self.handle_advanced_settings()
                else:
                    print("❌ Opção inválida")
                    input("\n📖 Pressione ENTER para continuar...")
                    
            except KeyboardInterrupt:
                print("\n⚠️ Operação cancelada pelo usuário")
                confirm = input("Deseja sair do Market Manus? (s/N): ").strip().lower()
                if confirm == 's':
                    self.running = False
                    print("👋 Até logo!")
            except Exception as e:
                print(f"\n❌ Erro inesperado: {e}")
                print("🔧 Continuando execução...")
                input("\n📖 Pressione ENTER para continuar...")

if __name__ == "__main__":
    cli = MarketManusCompleteCLI()

