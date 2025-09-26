"""
RSI Mean Reversion Strategy
"""
import pandas as pd

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def rsi_mean_reversion_strategy(klines: pd.DataFrame, params: dict):
    """Generate signals for RSI Mean Reversion strategy."""
    rsi_period = params.get("period", 14)
    buy_threshold = params.get("buy_th", 30)
    sell_threshold = params.get("sell_th", 70)

    klines["rsi"] = calculate_rsi(klines["close"], rsi_period)

    klines["signal"] = 0
    klines.loc[klines["rsi"] < buy_threshold, "signal"] = 1
    klines.loc[klines["rsi"] > sell_threshold, "signal"] = -1

    klines["position"] = klines["signal"].diff()

    return klines
