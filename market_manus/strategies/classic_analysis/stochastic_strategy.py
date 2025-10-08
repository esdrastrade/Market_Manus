"""
Stochastic Oscillator Strategy Module
Stochastic %K and %D Oscillator Strategy
Data: 24/09/2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional

class StochasticStrategy:
    """Estratégia Stochastic Oscillator (%K e %D)"""
    
    def __init__(self, k_period: int = 14, d_period: int = 3, oversold: float = 20, overbought: float = 80):
        self.k_period = k_period
        self.d_period = d_period
        self.oversold = oversold
        self.overbought = overbought
        self.name = "Stochastic"
        self.description = "Stochastic Oscillator %K and %D"
        self.emoji = "📈"
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """
        Calcula os valores de Stochastic %K e %D.

        Usa ``min_periods`` para garantir que o cálculo só inicie após
        ``k_period`` barras e lida com divisões por zero quando o preço
        permanece constante (em vez de produzir infinidades, assume-se um
        valor neutro de 50).

        Args:
            high: Série de preços máximos.
            low: Série de preços mínimos.
            close: Série de preços de fechamento.

        Returns:
            Tuple[pd.Series, pd.Series]: séries para %K e %D.
        """
        # Calcular mínimas e máximas com períodos mínimos adequados
        lowest_low = low.rolling(window=self.k_period, min_periods=self.k_period).min()
        highest_high = high.rolling(window=self.k_period, min_periods=self.k_period).max()

        # Denominador e cálculo do %K; se denom = 0 assume valor neutro (50)
        denom = highest_high - lowest_low
        k_percent = 100 * ((close - lowest_low) / denom)
        k_percent = k_percent.where(denom != 0, 50.0)

        # %D é a média de %K com min_periods igual ao período de suavização
        d_percent = k_percent.rolling(window=self.d_period, min_periods=self.d_period).mean()

        return k_percent, d_percent
    
    def generate_signals(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """
        Gera sinais de trading baseados no Stochastic
        
        Returns:
            pd.Series: 1 para compra, -1 para venda, 0 para neutro
        """
        k_percent, d_percent = self.calculate_stochastic(high, low, close)
        
        signals = pd.Series(0, index=close.index)
        
        # Sinal de compra: %K < oversold (mercado oversold)
        buy_condition = k_percent < self.oversold
        signals.loc[buy_condition] = 1
        
        # Sinal de venda: %K > overbought (mercado overbought)
        sell_condition = k_percent > self.overbought
        signals.loc[sell_condition] = -1
        
        # Sinal adicional: Cruzamento de %K e %D
        # Compra quando %K cruza acima de %D em região oversold
        k_cross_above_d = (k_percent > d_percent) & (k_percent.shift(1) <= d_percent.shift(1))
        oversold_cross_buy = k_cross_above_d & (k_percent < 50)
        signals.loc[oversold_cross_buy] = 1
        
        # Venda quando %K cruza abaixo de %D em região overbought
        k_cross_below_d = (k_percent < d_percent) & (k_percent.shift(1) >= d_percent.shift(1))
        overbought_cross_sell = k_cross_below_d & (k_percent > 50)
        signals.loc[overbought_cross_sell] = -1
        
        return signals
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Analisa o DataFrame e retorna informações da estratégia
        
        Args:
            df: DataFrame com colunas ['open', 'high', 'low', 'close', 'volume']
            
        Returns:
            Dict: Informações da análise
        """
        required_columns = ['high', 'low', 'close']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"DataFrame deve conter coluna '{col}'")
        
        high = df['high']
        low = df['low']
        close = df['close']
        
        k_percent, d_percent = self.calculate_stochastic(high, low, close)
        signals = self.generate_signals(high, low, close)
        
        # Adicionar ao DataFrame
        df = df.copy()
        df['stoch_k'] = k_percent
        df['stoch_d'] = d_percent
        df['stoch_signal'] = signals
        
        # Estatísticas atuais
        current_k = k_percent.iloc[-1]
        current_d = d_percent.iloc[-1]
        current_price = close.iloc[-1]
        
        # Determinar condição atual
        if current_k < self.oversold:
            current_condition = "OVERSOLD"
            current_action = "COMPRA"
        elif current_k > self.overbought:
            current_condition = "OVERBOUGHT"
            current_action = "VENDA"
        else:
            current_condition = "NEUTRO"
            if current_k > current_d:
                current_action = "BULLISH"
            else:
                current_action = "BEARISH"
        
        # Contar sinais
        buy_signals = len(signals[signals == 1])
        sell_signals = len(signals[signals == -1])
        
        # Análise de momentum
        momentum_analysis = self._analyze_momentum(k_percent, d_percent)
        
        return {
            'strategy_name': self.name,
            'parameters': {
                'k_period': self.k_period,
                'd_period': self.d_period,
                'oversold': self.oversold,
                'overbought': self.overbought
            },
            'current_values': {
                'price': current_price,
                'stoch_k': current_k,
                'stoch_d': current_d,
                'condition': current_condition,
                'action': current_action
            },
            'signals': {
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'total_signals': buy_signals + sell_signals
            },
            'momentum': momentum_analysis,
            'dataframe': df
        }
    
    def _analyze_momentum(self, k_percent: pd.Series, d_percent: pd.Series) -> Dict:
        """Analisa momentum baseado no Stochastic"""
        recent_k = k_percent.tail(10)
        recent_d = d_percent.tail(10)
        
        # Tendência do %K
        k_slope = (recent_k.iloc[-1] - recent_k.iloc[0]) / len(recent_k)
        k_trend = "RISING" if k_slope > 0 else "FALLING"
        
        # Tendência do %D
        d_slope = (recent_d.iloc[-1] - recent_d.iloc[0]) / len(recent_d)
        d_trend = "RISING" if d_slope > 0 else "FALLING"
        
        # Força do momentum
        k_strength = abs(k_slope)
        if k_strength > 2:
            momentum_strength = "STRONG"
        elif k_strength > 1:
            momentum_strength = "MODERATE"
        else:
            momentum_strength = "WEAK"
        
        # Divergência entre %K e %D
        k_d_divergence = abs(recent_k.iloc[-1] - recent_d.iloc[-1])
        divergence_level = "HIGH" if k_d_divergence > 10 else "LOW"
        
        return {
            'k_trend': k_trend,
            'd_trend': d_trend,
            'momentum_strength': momentum_strength,
            'k_slope': k_slope,
            'd_slope': d_slope,
            'k_d_divergence': k_d_divergence,
            'divergence_level': divergence_level
        }
    
    def get_strategy_info(self) -> Dict:
        """Retorna informações da estratégia"""
        return {
            'name': self.name,
            'description': self.description,
            'emoji': self.emoji,
            'type': 'Oscillator',
            'parameters': {
                'k_period': {
                    'value': self.k_period,
                    'description': 'Período para cálculo do %K',
                    'range': '5-25'
                },
                'd_period': {
                    'value': self.d_period,
                    'description': 'Período para suavização (%D)',
                    'range': '3-10'
                },
                'oversold': {
                    'value': self.oversold,
                    'description': 'Nível de oversold',
                    'range': '10-30'
                },
                'overbought': {
                    'value': self.overbought,
                    'description': 'Nível de overbought',
                    'range': '70-90'
                }
            },
            'signals': {
                'buy': '%K < oversold ou %K cruza acima de %D',
                'sell': '%K > overbought ou %K cruza abaixo de %D'
            },
            'best_markets': ['Ranging', 'Sideways'],
            'timeframes': ['5m', '15m', '30m', '1h', '4h']
        }
