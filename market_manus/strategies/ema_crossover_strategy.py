"""
EMA Crossover Strategy
"""
import pandas as pd

def calculate_ema(prices, period):
    return prices.ewm(span=period, adjust=False).mean()

def ema_crossover_strategy(klines: pd.DataFrame, params: dict):
    """Generate signals for EMA Crossover strategy."""
    short_period = params.get('short', 9)
    long_period = params.get('long', 21)

    klines['ema_short'] = calculate_ema(klines['close'], short_period)
    klines['ema_long'] = calculate_ema(klines['close'], long_period)

    klines['signal'] = 0
    klines.loc[klines['ema_short'] > klines['ema_long'], 'signal'] = 1
    klines.loc[klines['ema_short'] < klines['ema_long'], 'signal'] = -1

    klines['position'] = klines['signal'].diff()

    return klines
