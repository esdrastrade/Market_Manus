"""
Classic Analysis - Adaptador para estratégias clássicas retornarem Signal padronizado.
Converte EMA, MACD, RSI, Bollinger, ADX, Stochastic, Fibonacci para formato Signal.
"""

import pandas as pd
import numpy as np
from market_manus.core.signal import Signal

# ==================== INDICADORES TÉCNICOS ====================

def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """Calcula EMA (Exponential Moving Average)"""
    return prices.ewm(span=period, adjust=False).mean()

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calcula RSI (Relative Strength Index)"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices: pd.Series, fast=12, slow=26, signal=9):
    """Calcula MACD (Moving Average Convergence Divergence)"""
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(prices: pd.Series, period=20, std_dev=2):
    """Calcula Bollinger Bands"""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower

def calculate_adx(df: pd.DataFrame, period=14):
    """Calcula ADX (Average Directional Index)"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    
    return adx, plus_di, minus_di

def calculate_stochastic(df: pd.DataFrame, period=14, smooth_k=3, smooth_d=3):
    """Calcula Stochastic Oscillator"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()
    
    k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    k = k.rolling(window=smooth_k).mean()
    d = k.rolling(window=smooth_d).mean()
    
    return k, d

def calculate_atr(df: pd.DataFrame, period=14):
    """Calcula ATR (Average True Range)"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr

# ==================== ESTRATÉGIAS RETORNANDO SIGNAL ====================

def ema_crossover_signal(candles: pd.DataFrame, params: dict = None) -> Signal:
    """
    EMA Crossover: cruzamento EMA rápida > lenta = BUY; lenta > rápida = SELL.
    Confidence baseado em distância/ângulo entre EMAs.
    """
    params = params or {}
    fast_period = params.get('fast_period', 9)
    slow_period = params.get('slow_period', 21)
    
    closes = candles['close']
    ema_fast = calculate_ema(closes, fast_period)
    ema_slow = calculate_ema(closes, slow_period)
    
    if len(ema_fast) < 2 or len(ema_slow) < 2:
        return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:EMA"], reasons=["Dados insuficientes"])
    
    # Verifica cruzamento
    prev_fast, prev_slow = ema_fast.iloc[-2], ema_slow.iloc[-2]
    curr_fast, curr_slow = ema_fast.iloc[-1], ema_slow.iloc[-1]
    
    # Crossover bullish: fast cruza acima de slow
    if prev_fast <= prev_slow and curr_fast > curr_slow:
        distance_pct = abs(curr_fast - curr_slow) / curr_slow
        confidence = min(0.5 + distance_pct * 10, 1.0)
        return Signal(
            action="BUY",
            confidence=confidence,
            reasons=[f"EMA crossover bullish: EMA{fast_period} cruza acima EMA{slow_period}, distância {distance_pct:.3%}"],
            tags=["CLASSIC:EMA", "CLASSIC:EMA_CROSSUP"],
            meta={"ema_fast": curr_fast, "ema_slow": curr_slow, "distance_pct": distance_pct}
        )
    
    # Crossover bearish: fast cruza abaixo de slow
    if prev_fast >= prev_slow and curr_fast < curr_slow:
        distance_pct = abs(curr_fast - curr_slow) / curr_slow
        confidence = min(0.5 + distance_pct * 10, 1.0)
        return Signal(
            action="SELL",
            confidence=confidence,
            reasons=[f"EMA crossover bearish: EMA{fast_period} cruza abaixo EMA{slow_period}, distância {distance_pct:.3%}"],
            tags=["CLASSIC:EMA", "CLASSIC:EMA_CROSSDOWN"],
            meta={"ema_fast": curr_fast, "ema_slow": curr_slow, "distance_pct": distance_pct}
        )
    
    return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:EMA"], reasons=["Sem cruzamento"])


def macd_signal(candles: pd.DataFrame, params: dict = None) -> Signal:
    """
    MACD: linha MACD cruza acima/abaixo signal line.
    Confidence aumenta com histograma expandindo.
    """
    params = params or {}
    fast = params.get('fast', 12)
    slow = params.get('slow', 26)
    signal_period = params.get('signal', 9)
    
    closes = candles['close']
    macd_line, signal_line, histogram = calculate_macd(closes, fast, slow, signal_period)
    
    if len(macd_line) < 2:
        return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:MACD"], reasons=["Dados insuficientes"])
    
    prev_macd, prev_signal = macd_line.iloc[-2], signal_line.iloc[-2]
    curr_macd, curr_signal = macd_line.iloc[-1], signal_line.iloc[-1]
    curr_hist = histogram.iloc[-1]
    
    # Crossover bullish
    if prev_macd <= prev_signal and curr_macd > curr_signal:
        hist_strength = abs(curr_hist) / closes.iloc[-1] * 100  # Histograma em % do preço
        confidence = min(0.5 + hist_strength * 5, 1.0)
        return Signal(
            action="BUY",
            confidence=confidence,
            reasons=[f"MACD crossover bullish: MACD cruza acima signal, histograma {curr_hist:.4f}"],
            tags=["CLASSIC:MACD", "CLASSIC:MACD_CROSSUP"],
            meta={"macd": curr_macd, "signal": curr_signal, "histogram": curr_hist}
        )
    
    # Crossover bearish
    if prev_macd >= prev_signal and curr_macd < curr_signal:
        hist_strength = abs(curr_hist) / closes.iloc[-1] * 100
        confidence = min(0.5 + hist_strength * 5, 1.0)
        return Signal(
            action="SELL",
            confidence=confidence,
            reasons=[f"MACD crossover bearish: MACD cruza abaixo signal, histograma {curr_hist:.4f}"],
            tags=["CLASSIC:MACD", "CLASSIC:MACD_CROSSDOWN"],
            meta={"macd": curr_macd, "signal": curr_signal, "histogram": curr_hist}
        )
    
    return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:MACD"], reasons=["Sem cruzamento"])


def rsi_signal(candles: pd.DataFrame, params: dict = None) -> Signal:
    """
    RSI: sobrecomprado/sobrevendido e saídas dessas zonas.
    Confidence aumenta com distância dos extremos.
    """
    params = params or {}
    period = params.get('period', 14)
    oversold = params.get('oversold', 30)
    overbought = params.get('overbought', 70)
    
    closes = candles['close']
    rsi = calculate_rsi(closes, period)
    
    if len(rsi) < 2:
        return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:RSI"], reasons=["Dados insuficientes"])
    
    prev_rsi = rsi.iloc[-2]
    curr_rsi = rsi.iloc[-1]
    
    # Saindo de oversold (reversão bullish)
    if prev_rsi <= oversold and curr_rsi > oversold:
        distance_from_extreme = (curr_rsi - oversold) / (50 - oversold)  # Normaliza 0-1
        confidence = min(0.4 + distance_from_extreme * 0.4, 1.0)
        return Signal(
            action="BUY",
            confidence=confidence,
            reasons=[f"RSI saindo de oversold: {prev_rsi:.1f} → {curr_rsi:.1f}"],
            tags=["CLASSIC:RSI", "CLASSIC:RSI_OVERSOLD_EXIT"],
            meta={"rsi": curr_rsi, "oversold": oversold}
        )
    
    # Saindo de overbought (reversão bearish)
    if prev_rsi >= overbought and curr_rsi < overbought:
        distance_from_extreme = (overbought - curr_rsi) / (overbought - 50)
        confidence = min(0.4 + distance_from_extreme * 0.4, 1.0)
        return Signal(
            action="SELL",
            confidence=confidence,
            reasons=[f"RSI saindo de overbought: {prev_rsi:.1f} → {curr_rsi:.1f}"],
            tags=["CLASSIC:RSI", "CLASSIC:RSI_OVERBOUGHT_EXIT"],
            meta={"rsi": curr_rsi, "overbought": overbought}
        )
    
    return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:RSI"], reasons=[f"RSI neutro: {curr_rsi:.1f}"])


def bollinger_signal(candles: pd.DataFrame, params: dict = None) -> Signal:
    """
    Bollinger Bands: rompimentos + largura (volatilidade) + mean reversion.
    """
    params = params or {}
    period = params.get('period', 20)
    std_dev = params.get('std_dev', 2)
    
    closes = candles['close']
    upper, middle, lower = calculate_bollinger_bands(closes, period, std_dev)
    
    if len(upper) < 2:
        return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:BB"], reasons=["Dados insuficientes"])
    
    curr_close = closes.iloc[-1]
    curr_upper = upper.iloc[-1]
    curr_lower = lower.iloc[-1]
    curr_middle = middle.iloc[-1]
    
    width = (curr_upper - curr_lower) / curr_middle
    
    # Breakout acima (bullish)
    if curr_close > curr_upper:
        confidence = min(0.5 + width * 2, 1.0)
        return Signal(
            action="BUY",
            confidence=confidence,
            reasons=[f"BB breakout acima: preço {curr_close:.2f} > banda superior {curr_upper:.2f}, width {width:.3f}"],
            tags=["CLASSIC:BB", "CLASSIC:BB_BREAKOUT_UP"],
            meta={"close": curr_close, "upper": curr_upper, "middle": curr_middle, "lower": curr_lower, "width": width}
        )
    
    # Breakout abaixo (bearish)
    if curr_close < curr_lower:
        confidence = min(0.5 + width * 2, 1.0)
        return Signal(
            action="SELL",
            confidence=confidence,
            reasons=[f"BB breakout abaixo: preço {curr_close:.2f} < banda inferior {curr_lower:.2f}, width {width:.3f}"],
            tags=["CLASSIC:BB", "CLASSIC:BB_BREAKOUT_DOWN"],
            meta={"close": curr_close, "upper": curr_upper, "middle": curr_middle, "lower": curr_lower, "width": width}
        )
    
    return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:BB"], reasons=["Preço dentro das bandas"])


def adx_signal(candles: pd.DataFrame, params: dict = None) -> Signal:
    """
    ADX: filtro de tendência (força > limiar) e sinais com +DI/-DI.
    """
    params = params or {}
    period = params.get('period', 14)
    adx_threshold = params.get('adx_threshold', 25)
    
    adx, plus_di, minus_di = calculate_adx(candles, period)
    
    if len(adx) < 2:
        return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:ADX"], reasons=["Dados insuficientes"])
    
    curr_adx = adx.iloc[-1]
    curr_plus_di = plus_di.iloc[-1]
    curr_minus_di = minus_di.iloc[-1]
    
    # ADX acima threshold indica tendência forte
    if curr_adx >= adx_threshold:
        if curr_plus_di > curr_minus_di:
            confidence = min(0.4 + (curr_adx / 100) * 0.4, 1.0)
            return Signal(
                action="BUY",
                confidence=confidence,
                reasons=[f"ADX tendência forte bullish: ADX {curr_adx:.1f}, +DI {curr_plus_di:.1f} > -DI {curr_minus_di:.1f}"],
                tags=["CLASSIC:ADX", "CLASSIC:ADX_STRONG_UP"],
                meta={"adx": curr_adx, "plus_di": curr_plus_di, "minus_di": curr_minus_di}
            )
        else:
            confidence = min(0.4 + (curr_adx / 100) * 0.4, 1.0)
            return Signal(
                action="SELL",
                confidence=confidence,
                reasons=[f"ADX tendência forte bearish: ADX {curr_adx:.1f}, -DI {curr_minus_di:.1f} > +DI {curr_plus_di:.1f}"],
                tags=["CLASSIC:ADX", "CLASSIC:ADX_STRONG_DOWN"],
                meta={"adx": curr_adx, "plus_di": curr_plus_di, "minus_di": curr_minus_di}
            )
    
    return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:ADX"], reasons=[f"ADX fraco: {curr_adx:.1f} < {adx_threshold}"])


def stochastic_signal(candles: pd.DataFrame, params: dict = None) -> Signal:
    """
    Stochastic: %K cruza %D em extremos (oversold/overbought).
    """
    params = params or {}
    period = params.get('period', 14)
    oversold = params.get('oversold', 20)
    overbought = params.get('overbought', 80)
    
    k, d = calculate_stochastic(candles, period)
    
    if len(k) < 2:
        return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:STOCH"], reasons=["Dados insuficientes"])
    
    prev_k, prev_d = k.iloc[-2], d.iloc[-2]
    curr_k, curr_d = k.iloc[-1], d.iloc[-1]
    
    # Crossover bullish em oversold
    if prev_k <= prev_d and curr_k > curr_d and curr_k < oversold:
        confidence = min(0.5 + (oversold - curr_k) / oversold * 0.3, 1.0)
        return Signal(
            action="BUY",
            confidence=confidence,
            reasons=[f"Stochastic crossover bullish em oversold: %K {curr_k:.1f} cruza %D {curr_d:.1f}"],
            tags=["CLASSIC:STOCH", "CLASSIC:STOCH_CROSSUP"],
            meta={"k": curr_k, "d": curr_d, "oversold": oversold}
        )
    
    # Crossover bearish em overbought
    if prev_k >= prev_d and curr_k < curr_d and curr_k > overbought:
        confidence = min(0.5 + (curr_k - overbought) / (100 - overbought) * 0.3, 1.0)
        return Signal(
            action="SELL",
            confidence=confidence,
            reasons=[f"Stochastic crossover bearish em overbought: %K {curr_k:.1f} cruza %D {curr_d:.1f}"],
            tags=["CLASSIC:STOCH", "CLASSIC:STOCH_CROSSDOWN"],
            meta={"k": curr_k, "d": curr_d, "overbought": overbought}
        )
    
    return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:STOCH"], reasons=["Sem crossover em extremos"])


def fibonacci_signal(candles: pd.DataFrame, params: dict = None) -> Signal:
    """
    Fibonacci: níveis de retração como suporte/resistência.
    """
    params = params or {}
    lookback = params.get('lookback', 50)
    
    if len(candles) < lookback:
        return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:FIB"], reasons=["Dados insuficientes"])
    
    recent = candles.tail(lookback)
    swing_high = recent['high'].max()
    swing_low = recent['low'].min()
    curr_close = candles['close'].iloc[-1]
    
    # Níveis Fibonacci
    diff = swing_high - swing_low
    fib_382 = swing_high - diff * 0.382
    fib_500 = swing_high - diff * 0.500
    fib_618 = swing_high - diff * 0.618
    
    # Preço próximo de nível Fibonacci (suporte/resistência)
    tolerance = diff * 0.02  # 2% de tolerância
    
    # Próximo de 0.618 (forte suporte)
    if abs(curr_close - fib_618) < tolerance:
        confidence = 0.6
        return Signal(
            action="BUY",
            confidence=confidence,
            reasons=[f"Preço {curr_close:.2f} próximo de Fib 0.618 ({fib_618:.2f}), suporte forte"],
            tags=["CLASSIC:FIB", "CLASSIC:FIB_618"],
            meta={"fib_618": fib_618, "fib_500": fib_500, "fib_382": fib_382, "close": curr_close}
        )
    
    # Próximo de 0.382 (resistência)
    if abs(curr_close - fib_382) < tolerance:
        confidence = 0.5
        return Signal(
            action="SELL",
            confidence=confidence,
            reasons=[f"Preço {curr_close:.2f} próximo de Fib 0.382 ({fib_382:.2f}), resistência"],
            tags=["CLASSIC:FIB", "CLASSIC:FIB_382"],
            meta={"fib_618": fib_618, "fib_500": fib_500, "fib_382": fib_382, "close": curr_close}
        )
    
    return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:FIB"], reasons=["Preço longe de níveis Fib"])


# ==================== REGISTRY DE ESTRATÉGIAS ====================

CLASSIC_STRATEGIES = {
    "EMA": ema_crossover_signal,
    "MACD": macd_signal,
    "RSI": rsi_signal,
    "BB": bollinger_signal,
    "ADX": adx_signal,
    "STOCH": stochastic_signal,
    "FIB": fibonacci_signal
}

def get_classic_signal(strategy_name: str, candles: pd.DataFrame, params: dict = None) -> Signal:
    """
    Obtém signal de uma estratégia clássica pelo nome.
    
    Args:
        strategy_name: Nome da estratégia (EMA, MACD, RSI, BB, ADX, STOCH, FIB)
        candles: DataFrame OHLCV
        params: Parâmetros específicos da estratégia
    
    Returns:
        Signal padronizado
    """
    if strategy_name not in CLASSIC_STRATEGIES:
        raise ValueError(f"Estratégia {strategy_name} não encontrada. Disponíveis: {list(CLASSIC_STRATEGIES.keys())}")
    
    strategy_fn = CLASSIC_STRATEGIES[strategy_name]
    return strategy_fn(candles, params)
