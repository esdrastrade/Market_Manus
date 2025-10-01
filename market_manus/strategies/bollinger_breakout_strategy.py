"""
Bollinger Bands Breakout Strategy
"""
import pandas as pd

def calculate_bollinger_bands(prices, period=20, std=2.0):
    rolling_mean = prices.rolling(window=period).mean()
    rolling_std = prices.rolling(window=period).std()
    upper_band = rolling_mean + (rolling_std * std)
    lower_band = rolling_mean - (rolling_std * std)
    return upper_band, lower_band

def bollinger_breakout_strategy(klines: pd.DataFrame, params: dict):
    """Generate signals for Bollinger Bands Breakout strategy."""
    period = params.get("period", 20)
    std = params.get("std", 2.0)

    klines["upper_band"], klines["lower_band"] = calculate_bollinger_bands(
        klines["close"], period, std
    )

    klines["signal"] = 0
    klines.loc[klines["close"] > klines["upper_band"], "signal"] = 1
    klines.loc[klines["close"] < klines["lower_band"], "signal"] = -1

    klines["position"] = klines["signal"].diff()

    return klines
