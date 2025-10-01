"""
RSI Mean Reversion Strategy
"""
import pandas as pd

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calcula o Índice de Força Relativa (RSI) utilizando suavização de Wilder.

    A abordagem de Wilder usa médias móveis exponenciais (EWMA) para
    suavizar ganhos e perdas, fornecendo um cálculo mais estável do RSI.
    ``min_periods`` é definido para o período para evitar NaNs prolongados.

    Args:
        prices: Série de preços de fechamento.
        period: Período utilizado no cálculo.

    Returns:
        Série com os valores do RSI (0–100).
    """
    delta = prices.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    # EWMA com alpha=1/period (equivalente à suavização de Wilder)
    roll_up = up.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    roll_down = down.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = roll_up / roll_down
    rsi = 100 - (100 / (1 + rs))
    return rsi

def rsi_mean_reversion_strategy(klines: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Gera sinais de trading utilizando o RSI para reversão à média.

    O sinal é ``+1`` quando o RSI cai abaixo do limiar de compra (sobrevendido)
    e ``-1`` quando sobe acima do limiar de venda (sobrecomprado). A coluna
    ``entry`` marca as transições de posição.

    Args:
        klines: DataFrame com coluna 'close' contendo os preços.
        params: Dicionário com ``period``, ``buy_th`` e ``sell_th``.

    Returns:
        DataFrame com colunas adicionais: ``rsi``, ``signal`` e ``entry``.
    """
    rsi_period = int(params.get("period", 14))
    buy_threshold = float(params.get("buy_th", 30))
    sell_threshold = float(params.get("sell_th", 70))

    df = klines.copy()
    df["rsi"] = calculate_rsi(df["close"], rsi_period)

    df["signal"] = 0
    df.loc[df["rsi"] < buy_threshold, "signal"] = 1
    df.loc[df["rsi"] > sell_threshold, "signal"] = -1

    df["entry"] = df["signal"].diff().fillna(0)

    return df
