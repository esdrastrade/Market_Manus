"""
MACD Strategy Module
Moving Average Convergence Divergence Strategy
Data: 24/09/2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional

class MACDStrategy:
    """Estratégia MACD (Moving Average Convergence Divergence)"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.name = "MACD"
        self.description = "Moving Average Convergence Divergence"
        self.emoji = "📊"
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calcula EMA (Exponential Moving Average)"""
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calcula MACD, Signal Line e Histogram
        
        Returns:
            Tuple[pd.Series, pd.Series, pd.Series]: (macd_line, signal_line, histogram)
        """
        # Calcular EMAs
        ema_fast = self.calculate_ema(prices, self.fast_period)
        ema_slow = self.calculate_ema(prices, self.slow_period)
        
        # MACD Line = EMA rápida - EMA lenta
        macd_line = ema_fast - ema_slow
        
        # Signal Line = EMA da MACD Line
        signal_line = self.calculate_ema(macd_line, self.signal_period)
        
        # Histogram = MACD Line - Signal Line
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def generate_signals(self, prices: pd.Series) -> pd.Series:
        """
        Gera sinais de trading baseados no MACD
        
        Returns:
            pd.Series: 1 para compra, -1 para venda, 0 para neutro
        """
        macd_line, signal_line, histogram = self.calculate_macd(prices)
        
        signals = pd.Series(0, index=prices.index)
        
        # Sinal de compra: MACD cruza acima da Signal Line
        buy_condition = (macd_line > signal_line) & (macd_line.shift(1) <= signal_line.shift(1))
        signals.loc[buy_condition] = 1
        
        # Sinal de venda: MACD cruza abaixo da Signal Line
        sell_condition = (macd_line < signal_line) & (macd_line.shift(1) >= signal_line.shift(1))
        signals.loc[sell_condition] = -1
        
        return signals
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Analisa o DataFrame e retorna informações da estratégia
        
        Args:
            df: DataFrame com colunas ['open', 'high', 'low', 'close', 'volume']
            
        Returns:
            Dict: Informações da análise
        """
        if 'close' not in df.columns:
            raise ValueError("DataFrame deve conter coluna 'close'")
        
        prices = df['close']
        macd_line, signal_line, histogram = self.calculate_macd(prices)
        signals = self.generate_signals(prices)
        
        # Adicionar ao DataFrame
        df = df.copy()
        df['macd'] = macd_line
        df['signal_line'] = signal_line
        df['histogram'] = histogram
        df['macd_signal'] = signals
        
        # Estatísticas
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_histogram = histogram.iloc[-1]
        current_price = prices.iloc[-1]
        
        # Determinar sinal atual
        if current_macd > current_signal:
            current_trend = "BULLISH"
            current_action = "COMPRA"
        elif current_macd < current_signal:
            current_trend = "BEARISH"
            current_action = "VENDA"
        else:
            current_trend = "NEUTRO"
            current_action = "AGUARDAR"
        
        # Contar sinais
        buy_signals = len(signals[signals == 1])
        sell_signals = len(signals[signals == -1])
        
        # Análise de divergência
        divergence_analysis = self._analyze_divergence(prices, macd_line)
        
        return {
            'strategy_name': self.name,
            'parameters': {
                'fast_period': self.fast_period,
                'slow_period': self.slow_period,
                'signal_period': self.signal_period
            },
            'current_values': {
                'price': current_price,
                'macd': current_macd,
                'signal_line': current_signal,
                'histogram': current_histogram,
                'trend': current_trend,
                'action': current_action
            },
            'signals': {
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'total_signals': buy_signals + sell_signals
            },
            'divergence': divergence_analysis,
            'dataframe': df
        }
    
    def _analyze_divergence(self, prices: pd.Series, macd_line: pd.Series) -> Dict:
        """Analisa divergências entre preço e MACD"""
        # Simplificado - análise básica de divergência
        recent_prices = prices.tail(20)
        recent_macd = macd_line.tail(20)
        
        price_trend = "UP" if recent_prices.iloc[-1] > recent_prices.iloc[0] else "DOWN"
        macd_trend = "UP" if recent_macd.iloc[-1] > recent_macd.iloc[0] else "DOWN"
        
        if price_trend != macd_trend:
            divergence_type = "BEARISH" if price_trend == "UP" else "BULLISH"
            has_divergence = True
        else:
            divergence_type = "NONE"
            has_divergence = False
        
        return {
            'has_divergence': has_divergence,
            'type': divergence_type,
            'price_trend': price_trend,
            'macd_trend': macd_trend
        }
    
    def get_strategy_info(self) -> Dict:
        """Retorna informações da estratégia"""
        return {
            'name': self.name,
            'description': self.description,
            'emoji': self.emoji,
            'type': 'Momentum',
            'parameters': {
                'fast_period': {
                    'value': self.fast_period,
                    'description': 'Período da EMA rápida',
                    'range': '5-20'
                },
                'slow_period': {
                    'value': self.slow_period,
                    'description': 'Período da EMA lenta',
                    'range': '20-50'
                },
                'signal_period': {
                    'value': self.signal_period,
                    'description': 'Período da linha de sinal',
                    'range': '5-15'
                }
            },
            'signals': {
                'buy': 'MACD cruza acima da Signal Line',
                'sell': 'MACD cruza abaixo da Signal Line'
            },
            'best_markets': ['Trending', 'High Volume'],
            'timeframes': ['15m', '30m', '1h', '4h', '1d']
        }
