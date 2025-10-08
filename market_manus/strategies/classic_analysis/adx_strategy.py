"""
ADX Strategy Module
Average Directional Index Strategy
Data: 24/09/2025
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional

class ADXStrategy:
    """Estratégia ADX (Average Directional Index)"""
    
    def __init__(self, period: int = 14, adx_threshold: float = 25):
        self.period = period
        self.adx_threshold = adx_threshold
        self.name = "ADX"
        self.description = "Average Directional Index"
        self.emoji = "🎯"
    
    def calculate_true_range(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """Calcula True Range"""
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return true_range
    
    def calculate_directional_movement(self, high: pd.Series, low: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """Calcula Directional Movement (+DM e -DM)"""
        high_diff = high - high.shift(1)
        low_diff = low.shift(1) - low
        
        # +DM: movimento direcional positivo
        plus_dm = pd.Series(np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0), index=high.index)
        
        # -DM: movimento direcional negativo
        minus_dm = pd.Series(np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0), index=high.index)
        
        return plus_dm, minus_dm
    
    def calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calcula ADX, +DI e -DI usando a suavização de Wilder (EWMA).

        A metodologia padrão do ADX utiliza médias exponenciais com
        ``alpha=1/period`` para suavizar o True Range e o movimento direcional
        positivo/negativo. Este método é preferível a uma simples média móvel
        para refletir melhor a dinâmica do mercado.

        Args:
            high: Série de preços máximos.
            low: Série de preços mínimos.
            close: Série de preços de fechamento.

        Returns:
            Tupla contendo (adx, plus_di, minus_di).
        """
        # Calcular True Range e Directional Movement
        tr = self.calculate_true_range(high, low, close)
        plus_dm, minus_dm = self.calculate_directional_movement(high, low)

        # Suavização exponencial (Wilder) com alpha=1/period
        alpha = 1 / self.period
        tr_smooth = tr.ewm(alpha=alpha, min_periods=self.period, adjust=False).mean()
        plus_dm_smooth = plus_dm.ewm(alpha=alpha, min_periods=self.period, adjust=False).mean()
        minus_dm_smooth = minus_dm.ewm(alpha=alpha, min_periods=self.period, adjust=False).mean()

        # Calcular Directional Indicators; evitar divisão por zero
        plus_di = 100 * (plus_dm_smooth / tr_smooth)
        minus_di = 100 * (minus_dm_smooth / tr_smooth)
        # Substituir NaNs ou inf com zeros
        plus_di = plus_di.replace([np.inf, -np.inf], np.nan).fillna(0)
        minus_di = minus_di.replace([np.inf, -np.inf], np.nan).fillna(0)

        # Calcular DX (Directional Index) e ADX (EWMA do DX)
        dx_denominator = plus_di + minus_di
        dx = 100 * (plus_di - minus_di).abs() / dx_denominator.where(dx_denominator != 0, np.nan)
        dx = dx.replace([np.inf, -np.inf], np.nan).fillna(0)
        adx = dx.ewm(alpha=alpha, min_periods=self.period, adjust=False).mean()

        return adx, plus_di, minus_di
    
    def generate_signals(self, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """
        Gera sinais de trading baseados no ADX
        
        Returns:
            pd.Series: 1 para compra, -1 para venda, 0 para neutro
        """
        adx, plus_di, minus_di = self.calculate_adx(high, low, close)
        
        signals = pd.Series(0, index=close.index)
        
        # Sinal de compra: ADX > threshold E +DI > -DI (tendência de alta forte)
        buy_condition = (adx > self.adx_threshold) & (plus_di > minus_di)
        signals.loc[buy_condition] = 1
        
        # Sinal de venda: ADX > threshold E -DI > +DI (tendência de baixa forte)
        sell_condition = (adx > self.adx_threshold) & (minus_di > plus_di)
        signals.loc[sell_condition] = -1
        
        # Sinais adicionais baseados em cruzamentos de DI
        # Compra quando +DI cruza acima de -DI com ADX crescente
        di_cross_up = (plus_di > minus_di) & (plus_di.shift(1) <= minus_di.shift(1))
        adx_rising = adx > adx.shift(1)
        strong_buy = di_cross_up & adx_rising & (adx > self.adx_threshold * 0.8)
        signals.loc[strong_buy] = 1
        
        # Venda quando -DI cruza acima de +DI com ADX crescente
        di_cross_down = (minus_di > plus_di) & (minus_di.shift(1) <= plus_di.shift(1))
        strong_sell = di_cross_down & adx_rising & (adx > self.adx_threshold * 0.8)
        signals.loc[strong_sell] = -1
        
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
        
        adx, plus_di, minus_di = self.calculate_adx(high, low, close)
        signals = self.generate_signals(high, low, close)
        
        # Adicionar ao DataFrame
        df = df.copy()
        df['adx'] = adx
        df['plus_di'] = plus_di
        df['minus_di'] = minus_di
        df['adx_signal'] = signals
        
        # Estatísticas atuais
        current_adx = adx.iloc[-1]
        current_plus_di = plus_di.iloc[-1]
        current_minus_di = minus_di.iloc[-1]
        current_price = close.iloc[-1]
        
        # Determinar força da tendência
        if current_adx > self.adx_threshold * 1.5:
            trend_strength = "MUITO FORTE"
        elif current_adx > self.adx_threshold:
            trend_strength = "FORTE"
        elif current_adx > self.adx_threshold * 0.7:
            trend_strength = "MODERADA"
        else:
            trend_strength = "FRACA"
        
        # Determinar direção da tendência
        if current_plus_di > current_minus_di:
            trend_direction = "ALTA"
            current_action = "COMPRA" if current_adx > self.adx_threshold else "AGUARDAR"
        elif current_minus_di > current_plus_di:
            trend_direction = "BAIXA"
            current_action = "VENDA" if current_adx > self.adx_threshold else "AGUARDAR"
        else:
            trend_direction = "LATERAL"
            current_action = "AGUARDAR"
        
        # Contar sinais
        buy_signals = len(signals[signals == 1])
        sell_signals = len(signals[signals == -1])
        
        # Análise de momentum da tendência
        trend_analysis = self._analyze_trend_momentum(adx, plus_di, minus_di)
        
        return {
            'strategy_name': self.name,
            'parameters': {
                'period': self.period,
                'adx_threshold': self.adx_threshold
            },
            'current_values': {
                'price': current_price,
                'adx': current_adx,
                'plus_di': current_plus_di,
                'minus_di': current_minus_di,
                'trend_strength': trend_strength,
                'trend_direction': trend_direction,
                'action': current_action
            },
            'signals': {
                'buy_signals': buy_signals,
                'sell_signals': sell_signals,
                'total_signals': buy_signals + sell_signals
            },
            'trend_analysis': trend_analysis,
            'dataframe': df
        }
    
    def _analyze_trend_momentum(self, adx: pd.Series, plus_di: pd.Series, minus_di: pd.Series) -> Dict:
        """Analisa momentum da tendência"""
        recent_adx = adx.tail(10)
        recent_plus_di = plus_di.tail(10)
        recent_minus_di = minus_di.tail(10)
        
        # Tendência do ADX
        adx_slope = (recent_adx.iloc[-1] - recent_adx.iloc[0]) / len(recent_adx)
        adx_trend = "CRESCENTE" if adx_slope > 0 else "DECRESCENTE"
        
        # Força do momentum
        if abs(adx_slope) > 1:
            momentum_strength = "FORTE"
        elif abs(adx_slope) > 0.5:
            momentum_strength = "MODERADO"
        else:
            momentum_strength = "FRACO"
        
        # Análise de divergência entre DIs
        di_spread = abs(recent_plus_di.iloc[-1] - recent_minus_di.iloc[-1])
        if di_spread > 20:
            di_divergence = "ALTA"
        elif di_spread > 10:
            di_divergence = "MODERADA"
        else:
            di_divergence = "BAIXA"
        
        # Estabilidade da tendência
        adx_volatility = recent_adx.std()
        if adx_volatility < 2:
            trend_stability = "ESTÁVEL"
        elif adx_volatility < 5:
            trend_stability = "MODERADA"
        else:
            trend_stability = "INSTÁVEL"
        
        return {
            'adx_trend': adx_trend,
            'adx_slope': adx_slope,
            'momentum_strength': momentum_strength,
            'di_divergence': di_divergence,
            'di_spread': di_spread,
            'trend_stability': trend_stability,
            'adx_volatility': adx_volatility
        }
    
    def get_strategy_info(self) -> Dict:
        """Retorna informações da estratégia"""
        return {
            'name': self.name,
            'description': self.description,
            'emoji': self.emoji,
            'type': 'Trend Strength',
            'parameters': {
                'period': {
                    'value': self.period,
                    'description': 'Período para cálculo do ADX',
                    'range': '10-20'
                },
                'adx_threshold': {
                    'value': self.adx_threshold,
                    'description': 'Threshold para tendência forte',
                    'range': '20-30'
                }
            },
            'signals': {
                'buy': 'ADX > threshold E +DI > -DI',
                'sell': 'ADX > threshold E -DI > +DI'
            },
            'interpretation': {
                'adx_levels': {
                    '0-25': 'Tendência fraca ou lateral',
                    '25-50': 'Tendência forte',
                    '50-75': 'Tendência muito forte',
                    '75-100': 'Tendência extremamente forte'
                },
                'directional_indicators': {
                    '+DI > -DI': 'Pressão compradora dominante',
                    '-DI > +DI': 'Pressão vendedora dominante'
                }
            },
            'best_markets': ['Trending', 'Breakout'],
            'timeframes': ['15m', '30m', '1h', '4h', '1d']
        }
