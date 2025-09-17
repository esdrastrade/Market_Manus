"""
Signal Helpers para AI Agent Strategy
Funções auxiliares para geração de sinais de trading

Sub-estratégias implementadas:
- EMA Crossover: Cruzamento de médias móveis exponenciais
- RSI Mean Reversion: Reversão à média com RSI
- Breakout: Rompimento de máximas/mínimas

Características:
- Sinais padronizados (-1, 0, 1)
- Tratamento robusto de dados faltantes
- Parâmetros configuráveis
- Otimizado para performance
"""

import logging
import warnings
from typing import Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


class SignalHelpers:
    """
    Classe com funções auxiliares para geração de sinais

    Todas as funções retornam Series com valores:
    - 1: Sinal de compra (Long)
    - 0: Sem posição (Neutro)
    - -1: Sinal de venda (Short)
    """

    @staticmethod
    def validate_data(df: pd.DataFrame, required_cols: list) -> bool:
        """
        Valida se DataFrame tem colunas necessárias

        Args:
            df: DataFrame a validar
            required_cols: Lista de colunas obrigatórias

        Returns:
            True se dados são válidos
        """
        if df.empty:
            logger.warning("DataFrame vazio")
            return False

        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"Colunas faltando: {missing_cols}")
            return False

        # Verificar se há dados suficientes
        if len(df) < 10:
            logger.warning(f"Dados insuficientes: {len(df)} barras")
            return False

        return True

    @staticmethod
    def ema_crossover(
        df: pd.DataFrame, fast: int, slow: int, volume_filter: bool = False
    ) -> pd.Series:
        """
        Estratégia EMA Crossover

        Sinal de compra quando EMA rápida cruza acima da EMA lenta
        Sinal de venda quando EMA rápida cruza abaixo da EMA lenta

        Args:
            df: DataFrame com dados OHLCV
            fast: Período da EMA rápida
            slow: Período da EMA lenta
            volume_filter: Se True, aplica filtro de volume

        Returns:
            Series com sinais (-1, 0, 1)
        """
        try:
            # Validar dados
            required_cols = ["close"]
            if volume_filter:
                required_cols.append("volume")

            if not SignalHelpers.validate_data(df, required_cols):
                return pd.Series(0, index=df.index)

            # Validar parâmetros
            if fast >= slow:
                logger.warning(f"EMA rápida ({fast}) deve ser menor que lenta ({slow})")
                return pd.Series(0, index=df.index)

            if fast < 2 or slow < 2:
                logger.warning("Períodos de EMA devem ser >= 2")
                return pd.Series(0, index=df.index)

            # Calcular EMAs
            ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
            ema_slow = df["close"].ewm(span=slow, adjust=False).mean()

            # Detectar cruzamentos
            signals = pd.Series(0, index=df.index)

            # Sinal quando EMA rápida está acima da lenta
            signals[ema_fast > ema_slow] = 1
            signals[ema_fast < ema_slow] = -1

            # Filtro de volume (opcional)
            if volume_filter and "volume" in df.columns:
                volume_ma = df["volume"].rolling(window=20).mean()
                low_volume_mask = df["volume"] < (volume_ma * 0.5)
                signals[low_volume_mask] = 0

            # Suavizar sinais (evitar ruído)
            signals = SignalHelpers._smooth_signals(signals, window=3)

            logger.debug(
                f"EMA Crossover: fast={fast}, slow={slow}, signals={signals.value_counts().to_dict()}"
            )

            return signals

        except Exception as e:
            logger.error(f"Erro na EMA Crossover: {e}")
            return pd.Series(0, index=df.index)

    @staticmethod
    def rsi_mean_reversion(
        df: pd.DataFrame, period: int, lo: float, hi: float, smoothing: int = 3
    ) -> pd.Series:
        """
        Estratégia RSI Mean Reversion

        Sinal de compra quando RSI < lo (oversold)
        Sinal de venda quando RSI > hi (overbought)

        Args:
            df: DataFrame com dados OHLCV
            period: Período do RSI
            lo: Limite inferior (oversold)
            hi: Limite superior (overbought)
            smoothing: Janela de suavização

        Returns:
            Series com sinais (-1, 0, 1)
        """
        try:
            # Validar dados
            if not SignalHelpers.validate_data(df, ["close"]):
                return pd.Series(0, index=df.index)

            # Validar parâmetros
            if period < 2:
                logger.warning("Período do RSI deve ser >= 2")
                return pd.Series(0, index=df.index)

            if lo >= hi:
                logger.warning(
                    f"Limite inferior ({lo}) deve ser menor que superior ({hi})"
                )
                return pd.Series(0, index=df.index)

            if lo < 0 or hi > 100:
                logger.warning("Limites do RSI devem estar entre 0 e 100")
                return pd.Series(0, index=df.index)

            # Calcular RSI
            rsi = SignalHelpers._calculate_rsi(df["close"], period)

            # Gerar sinais
            signals = pd.Series(0, index=df.index)
            signals[rsi < lo] = 1  # Oversold -> Buy
            signals[rsi > hi] = -1  # Overbought -> Sell

            # Suavizar sinais
            if smoothing > 1:
                signals = SignalHelpers._smooth_signals(signals, window=smoothing)

            logger.debug(
                f"RSI Mean Reversion: period={period}, lo={lo}, hi={hi}, signals={signals.value_counts().to_dict()}"
            )

            return signals

        except Exception as e:
            logger.error(f"Erro na RSI Mean Reversion: {e}")
            return pd.Series(0, index=df.index)

    @staticmethod
    def breakout(
        df: pd.DataFrame, lookback: int, buffer_bps: float, volume_filter: bool = True
    ) -> pd.Series:
        """
        Estratégia Breakout

        Sinal de compra quando preço rompe máxima do período + buffer
        Sinal de venda quando preço rompe mínima do período - buffer

        Args:
            df: DataFrame com dados OHLCV
            lookback: Período para calcular máximas/mínimas
            buffer_bps: Buffer em basis points para confirmar rompimento
            volume_filter: Se True, aplica filtro de volume

        Returns:
            Series com sinais (-1, 0, 1)
        """
        try:
            # Validar dados
            required_cols = ["high", "low", "close"]
            if volume_filter:
                required_cols.append("volume")

            if not SignalHelpers.validate_data(df, required_cols):
                return pd.Series(0, index=df.index)

            # Validar parâmetros
            if lookback < 2:
                logger.warning("Lookback deve ser >= 2")
                return pd.Series(0, index=df.index)

            if buffer_bps < 0:
                logger.warning("Buffer deve ser >= 0")
                return pd.Series(0, index=df.index)

            # Calcular máximas e mínimas móveis
            high_max = df["high"].rolling(window=lookback).max()
            low_min = df["low"].rolling(window=lookback).min()

            # Aplicar buffer
            buffer_multiplier = 1 + (buffer_bps / 10000)
            breakout_high = high_max * buffer_multiplier
            breakout_low = low_min / buffer_multiplier

            # Gerar sinais
            signals = pd.Series(0, index=df.index)

            # Breakout para cima
            signals[df["high"] > breakout_high] = 1

            # Breakout para baixo
            signals[df["low"] < breakout_low] = -1

            # Filtro de volume
            if volume_filter and "volume" in df.columns:
                volume_ma = df["volume"].rolling(window=lookback).mean()
                # Exigir volume acima da média para confirmar breakout
                high_volume_mask = df["volume"] > volume_ma
                signals[~high_volume_mask] = 0

            # Evitar sinais consecutivos (hold position)
            signals = SignalHelpers._remove_consecutive_signals(signals)

            logger.debug(
                f"Breakout: lookback={lookback}, buffer={buffer_bps}bps, signals={signals.value_counts().to_dict()}"
            )

            return signals

        except Exception as e:
            logger.error(f"Erro na estratégia Breakout: {e}")
            return pd.Series(0, index=df.index)

    @staticmethod
    def bollinger_bands_breakout(
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        volume_filter: bool = True,
    ) -> pd.Series:
        """
        Estratégia Bollinger Bands Breakout

        Sinal de compra quando preço rompe banda superior
        Sinal de venda quando preço rompe banda inferior

        Args:
            df: DataFrame com dados OHLCV
            period: Período para média móvel
            std_dev: Número de desvios padrão
            volume_filter: Se True, aplica filtro de volume

        Returns:
            Series com sinais (-1, 0, 1)
        """
        try:
            # Validar dados
            required_cols = ["close"]
            if volume_filter:
                required_cols.append("volume")

            if not SignalHelpers.validate_data(df, required_cols):
                return pd.Series(0, index=df.index)

            # Validar parâmetros
            if period < 2:
                logger.warning("Período deve ser >= 2")
                return pd.Series(0, index=df.index)

            if std_dev <= 0:
                logger.warning("Desvio padrão deve ser > 0")
                return pd.Series(0, index=df.index)

            # Calcular Bollinger Bands
            sma = df["close"].rolling(window=period).mean()
            std = df["close"].rolling(window=period).std()

            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)

            # Gerar sinais
            signals = pd.Series(0, index=df.index)

            # Breakout das bandas
            signals[df["close"] > upper_band] = 1  # Breakout superior
            signals[df["close"] < lower_band] = -1  # Breakout inferior

            # Filtro de volume
            if volume_filter and "volume" in df.columns:
                volume_ma = df["volume"].rolling(window=period).mean()
                high_volume_mask = df["volume"] > volume_ma
                signals[~high_volume_mask] = 0

            # Suavizar sinais
            signals = SignalHelpers._smooth_signals(signals, window=2)

            logger.debug(
                f"Bollinger Breakout: period={period}, std={std_dev}, signals={signals.value_counts().to_dict()}"
            )

            return signals

        except Exception as e:
            logger.error(f"Erro na Bollinger Bands: {e}")
            return pd.Series(0, index=df.index)

    @staticmethod
    def macd_crossover(
        df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> pd.Series:
        """
        Estratégia MACD Crossover

        Sinal de compra quando MACD cruza acima da linha de sinal
        Sinal de venda quando MACD cruza abaixo da linha de sinal

        Args:
            df: DataFrame com dados OHLCV
            fast: Período da EMA rápida
            slow: Período da EMA lenta
            signal: Período da linha de sinal

        Returns:
            Series com sinais (-1, 0, 1)
        """
        try:
            # Validar dados
            if not SignalHelpers.validate_data(df, ["close"]):
                return pd.Series(0, index=df.index)

            # Validar parâmetros
            if fast >= slow:
                logger.warning(f"EMA rápida ({fast}) deve ser menor que lenta ({slow})")
                return pd.Series(0, index=df.index)

            # Calcular MACD
            ema_fast = df["close"].ewm(span=fast).mean()
            ema_slow = df["close"].ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()

            # Gerar sinais
            signals = pd.Series(0, index=df.index)
            signals[macd_line > signal_line] = 1
            signals[macd_line < signal_line] = -1

            # Suavizar sinais
            signals = SignalHelpers._smooth_signals(signals, window=2)

            logger.debug(
                f"MACD: fast={fast}, slow={slow}, signal={signal}, signals={signals.value_counts().to_dict()}"
            )

            return signals

        except Exception as e:
            logger.error(f"Erro na MACD: {e}")
            return pd.Series(0, index=df.index)

    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int) -> pd.Series:
        """
        Calcula RSI (Relative Strength Index)

        Args:
            prices: Series com preços
            period: Período do RSI

        Returns:
            Series com valores do RSI
        """
        try:
            # Calcular mudanças de preço
            delta = prices.diff()

            # Separar ganhos e perdas
            gains = delta.where(delta > 0, 0)
            losses = -delta.where(delta < 0, 0)

            # Calcular médias móveis exponenciais
            avg_gains = gains.ewm(span=period, adjust=False).mean()
            avg_losses = losses.ewm(span=period, adjust=False).mean()

            # Calcular RS e RSI
            rs = avg_gains / avg_losses
            rsi = 100 - (100 / (1 + rs))

            # Tratar valores inválidos
            rsi = rsi.fillna(50)  # Valor neutro para NaN
            rsi = rsi.clip(0, 100)  # Garantir range [0, 100]

            return rsi

        except Exception as e:
            logger.error(f"Erro no cálculo do RSI: {e}")
            return pd.Series(50, index=prices.index)  # Valor neutro

    @staticmethod
    def _smooth_signals(signals: pd.Series, window: int) -> pd.Series:
        """
        Suaviza sinais para reduzir ruído

        Args:
            signals: Series com sinais
            window: Janela de suavização

        Returns:
            Series com sinais suavizados
        """
        if window <= 1:
            return signals

        try:
            # Aplicar filtro de mediana para remover ruído
            smoothed = signals.rolling(window=window, center=True).median()

            # Preencher valores NaN
            smoothed = smoothed.fillna(signals)

            # Garantir valores inteiros
            smoothed = smoothed.round().astype(int)

            return smoothed

        except Exception as e:
            logger.warning(f"Erro na suavização: {e}")
            return signals

    @staticmethod
    def _remove_consecutive_signals(signals: pd.Series) -> pd.Series:
        """
        Remove sinais consecutivos iguais (mantém apenas o primeiro)

        Args:
            signals: Series com sinais

        Returns:
            Series com sinais filtrados
        """
        try:
            filtered = signals.copy()

            # Manter apenas mudanças de sinal
            changes = signals != signals.shift(1)
            filtered[~changes] = 0

            return filtered

        except Exception as e:
            logger.warning(f"Erro na remoção de sinais consecutivos: {e}")
            return signals

    @staticmethod
    def combine_signals(signals_list: list, method: str = "majority") -> pd.Series:
        """
        Combina múltiplos sinais usando diferentes métodos

        Args:
            signals_list: Lista de Series com sinais
            method: Método de combinação ('majority', 'unanimous', 'average')

        Returns:
            Series com sinais combinados
        """
        try:
            if not signals_list:
                raise ValueError("Lista de sinais vazia")

            # Garantir que todos têm o mesmo índice
            index = signals_list[0].index
            for signals in signals_list[1:]:
                if not signals.index.equals(index):
                    raise ValueError("Sinais devem ter o mesmo índice")

            # Combinar sinais
            if method == "majority":
                # Voto majoritário
                combined = pd.DataFrame(signals_list).T
                combined_signals = combined.mode(axis=1)[0]

            elif method == "unanimous":
                # Todos devem concordar
                combined = pd.DataFrame(signals_list).T
                # Se todos concordam, usar o sinal; senão, neutro
                unanimous_mask = (combined == combined.iloc[:, 0:1].values).all(axis=1)
                combined_signals = pd.Series(0, index=index)
                combined_signals[unanimous_mask] = combined.iloc[:, 0][unanimous_mask]

            elif method == "average":
                # Média dos sinais
                combined = pd.DataFrame(signals_list).T
                combined_signals = combined.mean(axis=1).round().astype(int)

            else:
                raise ValueError(f"Método não suportado: {method}")

            # Garantir valores válidos
            combined_signals = combined_signals.clip(-1, 1)

            logger.debug(
                f"Sinais combinados ({method}): {combined_signals.value_counts().to_dict()}"
            )

            return combined_signals

        except Exception as e:
            logger.error(f"Erro na combinação de sinais: {e}")
            return pd.Series(0, index=signals_list[0].index if signals_list else [])


def create_sample_signals(df: pd.DataFrame, strategy: str, **params) -> pd.Series:
    """
    Função de conveniência para gerar sinais de uma estratégia

    Args:
        df: DataFrame com dados OHLCV
        strategy: Nome da estratégia
        **params: Parâmetros da estratégia

    Returns:
        Series com sinais
    """
    if strategy == "ema_cross":
        return SignalHelpers.ema_crossover(df, **params)
    elif strategy == "rsi_mr":
        return SignalHelpers.rsi_mean_reversion(df, **params)
    elif strategy == "breakout":
        return SignalHelpers.breakout(df, **params)
    elif strategy == "bollinger":
        return SignalHelpers.bollinger_bands_breakout(df, **params)
    elif strategy == "macd":
        return SignalHelpers.macd_crossover(df, **params)
    else:
        logger.warning(f"Estratégia não reconhecida: {strategy}")
        return pd.Series(0, index=df.index)


if __name__ == "__main__":
    # Teste básico dos signal helpers
    print("📊 Signal Helpers - Teste Básico")

    # Criar dados sintéticos
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=500, freq="1H")

    base_price = 50000
    returns = np.random.normal(0, 0.02, 500)
    prices = base_price * (1 + returns).cumprod()

    data = pd.DataFrame(
        {
            "open": prices * (1 + np.random.normal(0, 0.001, 500)),
            "high": prices * (1 + np.abs(np.random.normal(0, 0.005, 500))),
            "low": prices * (1 - np.abs(np.random.normal(0, 0.005, 500))),
            "close": prices,
            "volume": np.random.uniform(100, 1000, 500),
        },
        index=dates,
    )

    # Garantir consistência OHLC
    data["high"] = data[["open", "high", "close"]].max(axis=1)
    data["low"] = data[["open", "low", "close"]].min(axis=1)

    print(f"✅ Dados criados: {len(data)} barras")

    # Testar estratégias
    strategies_to_test = [
        ("EMA Crossover", "ema_cross", {"fast": 12, "slow": 26}),
        ("RSI Mean Reversion", "rsi_mr", {"period": 14, "lo": 30, "hi": 70}),
        ("Breakout", "breakout", {"lookback": 20, "buffer_bps": 2}),
        ("Bollinger Bands", "bollinger", {"period": 20, "std_dev": 2.0}),
        ("MACD", "macd", {"fast": 12, "slow": 26, "signal": 9}),
    ]

    print(f"\n🔄 Testando estratégias:")

    all_signals = []
    for name, strategy, params in strategies_to_test:
        signals = create_sample_signals(data, strategy, **params)
        all_signals.append(signals)

        signal_counts = signals.value_counts().to_dict()
        print(
            f"   {name}: Long={signal_counts.get(1, 0)}, "
            f"Short={signal_counts.get(-1, 0)}, "
            f"Neutro={signal_counts.get(0, 0)}"
        )

    # Testar combinação de sinais
    print(f"\n🔄 Testando combinação de sinais:")

    combined_majority = SignalHelpers.combine_signals(all_signals, method="majority")
    combined_unanimous = SignalHelpers.combine_signals(all_signals, method="unanimous")

    maj_counts = combined_majority.value_counts().to_dict()
    una_counts = combined_unanimous.value_counts().to_dict()

    print(
        f"   Majority: Long={maj_counts.get(1, 0)}, Short={maj_counts.get(-1, 0)}, Neutro={maj_counts.get(0, 0)}"
    )
    print(
        f"   Unanimous: Long={una_counts.get(1, 0)}, Short={una_counts.get(-1, 0)}, Neutro={una_counts.get(0, 0)}"
    )

    print("\n✅ Teste concluído com sucesso!")
