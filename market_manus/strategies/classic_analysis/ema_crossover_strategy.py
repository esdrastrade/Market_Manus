"""
EMA Crossover Strategy
"""
import pandas as pd

def calculate_ema(prices, period):
    return prices.ewm(span=period, adjust=False).mean()

def ema_crossover_strategy(klines: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Gera sinais baseados no cruzamento de EMAs.

    Calcula duas médias móveis exponenciais (EMAs) com períodos diferentes e
    determina o sinal quando a EMA curta cruza acima ou abaixo da EMA longa.
    Um parâmetro opcional ``hysteresis`` define uma banda neutra relativa
    à EMA longa para reduzir falsos cruzamentos (ex.: 0.001 = 0,1%).
    A coluna ``entry`` indica as entradas quando ocorre uma mudança de sinal.

    Args:
        klines: DataFrame com coluna 'close' contendo os preços.
        params: Dicionário com ``short``, ``long`` e opcional ``hysteresis``.

    Returns:
        DataFrame com colunas adicionais: ``ema_short``, ``ema_long``,
        ``signal`` e ``entry``.
    """
    short_period = int(params.get('short', 9))
    long_period = int(params.get('long', 21))
    hysteresis = float(params.get('hysteresis', 0.0))

    df = klines.copy()
    df['ema_short'] = calculate_ema(df['close'], short_period)
    df['ema_long'] = calculate_ema(df['close'], long_period)

    # Condições de crossover com histerese
    up_condition = df['ema_short'] > df['ema_long'] * (1 + hysteresis)
    down_condition = df['ema_short'] < df['ema_long'] * (1 - hysteresis)

    df['signal'] = 0
    df.loc[up_condition, 'signal'] = 1
    df.loc[down_condition, 'signal'] = -1

    df['entry'] = df['signal'].diff().fillna(0)

    return df
