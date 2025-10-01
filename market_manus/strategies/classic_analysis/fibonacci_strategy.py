"""
Fibonacci Retracement Strategy Module
Fibonacci Retracement Levels Strategy
Data: 24/09/2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional

class FibonacciStrategy:
    """Estratégia Fibonacci Retracement"""
    
    def __init__(self, lookback_period: int = 50, tolerance_pct: float = 0.5):
        self.lookback_period = lookback_period
        self.tolerance_pct = tolerance_pct  # Tolerância para considerar toque no nível
        self.name = "Fibonacci"
        self.description = "Fibonacci Retracement Levels"
        self.emoji = "🔢"
        
        # Níveis de Fibonacci padrão
        self.fib_levels = {
            0.0: "0.0%",
            0.236: "23.6%",
            0.382: "38.2%",
            0.500: "50.0%",
            0.618: "61.8%",
            0.786: "78.6%",
            1.0: "100.0%"
        }
    
    def calculate_fibonacci_levels(self, high_price: float, low_price: float) -> Dict[str, float]:
        """
        Calcula níveis de Fibonacci Retracement
        
        Args:
            high_price: Preço máximo do período
            low_price: Preço mínimo do período
            
        Returns:
            Dict: Níveis de Fibonacci com suas descrições
        """
        price_range = high_price - low_price
        
        levels = {}
        for level, description in self.fib_levels.items():
            # Para retracement, calculamos a partir do topo
            fib_price = high_price - (level * price_range)
            levels[description] = fib_price
        
        return levels
    
    def find_swing_points(self, high: pd.Series, low: pd.Series, window: int = 5) -> Tuple[pd.Series, pd.Series]:
        """
        Encontra pontos de swing (máximas e mínimas locais)
        
        Args:
            high: Série de preços máximos
            low: Série de preços mínimos
            window: Janela para identificar swing points
            
        Returns:
            Tuple[pd.Series, pd.Series]: (swing_highs, swing_lows)
        """
        swing_highs = pd.Series(np.nan, index=high.index)
        swing_lows = pd.Series(np.nan, index=low.index)
        
        for i in range(window, len(high) - window):
            # Swing High: máximo local
            if high.iloc[i] == high.iloc[i-window:i+window+1].max():
                swing_highs.iloc[i] = high.iloc[i]
            
            # Swing Low: mínimo local
            if low.iloc[i] == low.iloc[i-window:i+window+1].min():
                swing_lows.iloc[i] = low.iloc[i]
        
        return swing_highs, swing_lows
    
    def generate_signals(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """
        Gera sinais baseados em Fibonacci Retracement
        
        Returns:
            pd.Series: 1 para compra, -1 para venda, 0 para neutro
        """
        signals = pd.Series(0, index=close.index)
        
        # Usar período de lookback para análise
        for i in range(self.lookback_period, len(close)):
            # Obter dados do período
            period_high = high.iloc[i-self.lookback_period:i].max()
            period_low = low.iloc[i-self.lookback_period:i].min()
            current_price = close.iloc[i]
            
            # Calcular níveis de Fibonacci
            fib_levels = self.calculate_fibonacci_levels(period_high, period_low)
            
            # Verificar proximidade aos níveis de suporte/resistência
            tolerance = (period_high - period_low) * (self.tolerance_pct / 100)
            
            # Níveis de suporte (potenciais compras)
            support_levels = [fib_levels["61.8%"], fib_levels["50.0%"], fib_levels["38.2%"]]
            
            # Níveis de resistência (potenciais vendas)
            resistance_levels = [fib_levels["23.6%"], fib_levels["0.0%"]]
            
            # Sinal de compra: preço próximo a níveis de suporte
            for support in support_levels:
                if abs(current_price - support) <= tolerance:
                    signals.iloc[i] = 1
                    break
            
            # Sinal de venda: preço próximo a níveis de resistência
            for resistance in resistance_levels:
                if abs(current_price - resistance) <= tolerance:
                    signals.iloc[i] = -1
                    break
        
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
        
        # Calcular níveis de Fibonacci para o período completo
        period_high = high.max()
        period_low = low.min()
        current_price = close.iloc[-1]
        
        fib_levels = self.calculate_fibonacci_levels(period_high, period_low)
        signals = self.generate_signals(high, low, close)
        
        # Encontrar swing points
        swing_highs, swing_lows = self.find_swing_points(high, low)
        
        # Adicionar ao DataFrame
        df = df.copy()
        df['fib_signal'] = signals
        df['swing_high'] = swing_highs
        df['swing_low'] = swing_lows
        
        # Análise de posição atual
        position_analysis = self._analyze_current_position(current_price, fib_levels)
        
        # Análise de níveis próximos
        nearby_levels = self._find_nearby_levels(current_price, fib_levels)
        
        # Contar sinais
        buy_signals = len(signals[signals == 1])
        sell_signals = len(signals[signals == -1])
        
        return {
            'strategy_name': self.name,
            'parameters': {
                'lookback_period': self.lookback_period,
                'tolerance_pct': self.tolerance_pct
            },
            'price_range': {
                'high': period_high,
                'low': period_low,
                'current': current_price,
                'range': period_high - period_low
            },
            'fibonacci_levels': fib_levels,
            'current_analysis': position_analysis,
            'nearby_levels': nearby_levels,
            'signals': {
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'total_signals': buy_signals + sell_signals
            },
            'swing_points': {
                'swing_highs': swing_highs.dropna().to_dict(),
                'swing_lows': swing_lows.dropna().to_dict()
            },
            'dataframe': df
        }
    
    def _analyze_current_position(self, current_price: float, fib_levels: Dict[str, float]) -> Dict:
        """Analisa posição atual em relação aos níveis de Fibonacci"""
        # Ordenar níveis por preço
        sorted_levels = sorted(fib_levels.items(), key=lambda x: x[1], reverse=True)
        
        # Encontrar posição atual
        position_info = {
            'between_levels': None,
            'nearest_support': None,
            'nearest_resistance': None,
            'position_percentage': 0
        }
        
        for i, (level_name, level_price) in enumerate(sorted_levels):
            if current_price >= level_price:
                if i > 0:
                    upper_level = sorted_levels[i-1]
                    position_info['between_levels'] = f"Entre {level_name} e {upper_level[0]}"
                    position_info['nearest_resistance'] = upper_level
                else:
                    position_info['between_levels'] = f"Acima de {level_name}"
                
                position_info['nearest_support'] = (level_name, level_price)
                break
        
        # Calcular percentual da posição no range
        total_range = fib_levels["0.0%"] - fib_levels["100.0%"]
        if total_range > 0:
            position_info['position_percentage'] = ((current_price - fib_levels["100.0%"]) / total_range) * 100
        
        return position_info
    
    def _find_nearby_levels(self, current_price: float, fib_levels: Dict[str, float], max_distance_pct: float = 5.0) -> Dict:
        """Encontra níveis próximos ao preço atual"""
        nearby = {'support': [], 'resistance': []}
        
        price_range = fib_levels["0.0%"] - fib_levels["100.0%"]
        max_distance = price_range * (max_distance_pct / 100)
        
        for level_name, level_price in fib_levels.items():
            distance = abs(current_price - level_price)
            
            if distance <= max_distance:
                level_info = {
                    'level': level_name,
                    'price': level_price,
                    'distance': distance,
                    'distance_pct': (distance / price_range) * 100
                }
                
                if level_price < current_price:
                    nearby['support'].append(level_info)
                elif level_price > current_price:
                    nearby['resistance'].append(level_info)
        
        # Ordenar por proximidade
        nearby['support'].sort(key=lambda x: x['distance'])
        nearby['resistance'].sort(key=lambda x: x['distance'])
        
        return nearby
    
    def get_strategy_info(self) -> Dict:
        """Retorna informações da estratégia"""
        return {
            'name': self.name,
            'description': self.description,
            'emoji': self.emoji,
            'type': 'Support/Resistance',
            'parameters': {
                'lookback_period': {
                    'value': self.lookback_period,
                    'description': 'Período para identificar máximas/mínimas',
                    'range': '20-100'
                },
                'tolerance_pct': {
                    'value': self.tolerance_pct,
                    'description': 'Tolerância para toque nos níveis (%)',
                    'range': '0.1-2.0'
                }
            },
            'fibonacci_levels': {
                '0.0%': 'Máxima do período (resistência forte)',
                '23.6%': 'Primeiro nível de retracement',
                '38.2%': 'Retracement moderado',
                '50.0%': 'Meio do range (psicológico)',
                '61.8%': 'Golden ratio (nível importante)',
                '78.6%': 'Retracement profundo',
                '100.0%': 'Mínima do período (suporte forte)'
            },
            'signals': {
                'buy': 'Preço próximo aos níveis 38.2%, 50.0% ou 61.8%',
                'sell': 'Preço próximo aos níveis 23.6% ou 0.0%'
            },
            'best_markets': ['Trending', 'Retracement'],
            'timeframes': ['1h', '4h', '1d', '1w']
        }
