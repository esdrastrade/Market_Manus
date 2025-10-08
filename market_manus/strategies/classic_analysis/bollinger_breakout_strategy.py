"""
Bollinger Bands Breakout Strategy
"""
import pandas as pd

def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std: float = 2.0) -> tuple[pd.Series, pd.Series]:
    """Calcula as bandas de Bollinger para uma série de preços.

    Utiliza ``min_periods=period`` para que o cálculo só seja realizado após
    haver dados suficientes e evita retornos enviesados nas primeiras barras.

    Args:
        prices: Série de preços de fechamento.
        period: Número de períodos da média móvel.
        std: Multiplicador do desvio-padrão.

    Returns:
        Uma tupla (upper_band, lower_band) com as bandas superior e inferior.
    """
    rolling_mean = prices.rolling(window=period, min_periods=period).mean()
    rolling_std = prices.rolling(window=period, min_periods=period).std()
    upper_band = rolling_mean + (rolling_std * std)
    lower_band = rolling_mean - (rolling_std * std)
    return upper_band, lower_band

def bollinger_breakout_strategy(klines: pd.DataFrame, params: dict) -> pd.DataFrame:
    """Gera sinais de trading baseados nas Bandas de Bollinger.

    A estratégia marca um sinal de ``+1`` quando o preço de fechamento ultrapassa
    a banda superior (possível continuação de alta) e ``-1`` quando cai abaixo
    da banda inferior (possível continuação de baixa). A coluna ``entry`` indica
    as entradas e saídas (mudanças de sinal) com base no ``diff`` da coluna
    ``signal``.

    Args:
        klines: DataFrame com coluna 'close' contendo os preços.
        params: Dicionário de parâmetros com ``period`` e ``std``.

    Returns:
        DataFrame com colunas adicionais: ``upper_band``, ``lower_band``,
        ``signal`` e ``entry``.
    """
    period = int(params.get("period", 20))
    std = float(params.get("std", 2.0))

    # Trabalhar sobre uma cópia para não modificar o DataFrame original
    df = klines.copy()
    df["upper_band"], df["lower_band"] = calculate_bollinger_bands(
        df["close"], period, std
    )

    # Gerar sinais de breakout: +1 acima da banda superior, -1 abaixo da inferior
    df["signal"] = 0
    df.loc[df["close"] > df["upper_band"], "signal"] = 1
    df.loc[df["close"] < df["lower_band"], "signal"] = -1

    # Entradas (mudanças de posição)
    df["entry"] = df["signal"].diff().fillna(0)

    return df
