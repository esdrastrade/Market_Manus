#!/usr/bin/env python3
"""
EMA CROSSOVER STRATEGY - Estratégia de Cruzamento de Médias Móveis Exponenciais
Estratégia modular para o Market Manus Strategy Factory
"""

from typing import Dict, List

from src.core.base_strategy import BaseStrategy, StrategyConfig


class EMACrossoverStrategy(BaseStrategy):
    """Estratégia de cruzamento de médias móveis exponenciais"""

    def __init__(
        self, fast_ema: int = 12, slow_ema: int = 26, volume_filter: bool = True
    ):
        """
        Inicializa estratégia EMA Crossover

        Args:
            fast_ema: Período da EMA rápida (padrão: 12)
            slow_ema: Período da EMA lenta (padrão: 26)
            volume_filter: Usar filtro de volume (padrão: True)
        """
        config = StrategyConfig(
            name="EMA Crossover",
            description="Cruzamento de médias móveis exponenciais com dados históricos reais",
            risk_level="medium",
            best_timeframes=["15m", "30m", "1h"],
            market_conditions="Tendencial",
            params={
                "fast_ema": fast_ema,
                "slow_ema": slow_ema,
                "volume_filter": volume_filter,
            },
        )
        super().__init__(config)

    def calculate_signals(self, data: List[Dict]) -> List[Dict]:
        """
        Calcula sinais da estratégia EMA Crossover

        Args:
            data: Lista de dados OHLCV

        Returns:
            Lista de dados com sinais adicionados
        """
        if len(data) < max(
            self.config.params["fast_ema"], self.config.params["slow_ema"]
        ):
            return self._add_empty_signals(data)

        closes = [float(d["close"]) for d in data]
        volumes = [float(d["volume"]) for d in data]

        # Calcular EMAs
        fast_ema = self._calculate_ema(closes, self.config.params["fast_ema"])
        slow_ema = self._calculate_ema(closes, self.config.params["slow_ema"])

        # Calcular filtro de volume se habilitado
        volume_ma = (
            self._calculate_volume_filter(volumes)
            if self.config.params["volume_filter"]
            else None
        )

        # Gerar sinais
        signals = []
        for i, d in enumerate(data):
            signal = 0
            strength = 0.0

            if i > 0 and fast_ema[i] > 0 and slow_ema[i] > 0:
                # Verificar filtro de volume
                volume_ok = True
                if self.config.params["volume_filter"] and volume_ma and i > 0:
                    volume_ok = volumes[i] > volume_ma[i] * 1.1

                # Long: EMA rápida cruza acima da lenta
                if (
                    fast_ema[i] > slow_ema[i]
                    and fast_ema[i - 1] <= slow_ema[i - 1]
                    and volume_ok
                ):
                    signal = 1
                    strength = min(abs(fast_ema[i] - slow_ema[i]) / closes[i], 1.0)

                # Short: EMA rápida cruza abaixo da lenta
                elif (
                    fast_ema[i] < slow_ema[i]
                    and fast_ema[i - 1] >= slow_ema[i - 1]
                    and volume_ok
                ):
                    signal = -1
                    strength = min(abs(fast_ema[i] - slow_ema[i]) / closes[i], 1.0)

            # Adicionar dados do sinal
            signal_data = {
                **d,
                "signal": signal,
                "signal_strength": strength,
                "fast_ema": fast_ema[i],
                "slow_ema": slow_ema[i],
                "strategy": "ema_crossover",
            }

            if volume_ma:
                signal_data["volume_ma"] = volume_ma[i]

            signals.append(signal_data)

        return signals

    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Calcula média móvel exponencial"""
        if len(prices) < period:
            return [prices[0] if prices else 0] * len(prices)

        multiplier = 2 / (period + 1)
        ema_values = [0] * len(prices)

        # Primeira EMA é a média simples
        ema_values[period - 1] = sum(prices[:period]) / period

        # Calcular EMA para o resto
        for i in range(period, len(prices)):
            ema_values[i] = (prices[i] * multiplier) + (
                ema_values[i - 1] * (1 - multiplier)
            )

        # Preencher valores iniciais
        for i in range(period - 1):
            ema_values[i] = ema_values[period - 1]

        return ema_values

    def _calculate_volume_filter(self, volumes: List[float]) -> List[float]:
        """Calcula filtro de volume (média móvel de 20 períodos)"""
        volume_ma = []
        for i in range(len(volumes)):
            if i < 20:
                volume_ma.append(sum(volumes[: i + 1]) / (i + 1))
            else:
                volume_ma.append(sum(volumes[i - 19 : i + 1]) / 20)
        return volume_ma

    def get_strategy_info(self) -> Dict:
        """Retorna informações detalhadas da estratégia"""
        return {
            **super().get_strategy_info(),
            "indicators": ["EMA Fast", "EMA Slow", "Volume MA"],
            "entry_conditions": {
                "long": "EMA rápida cruza acima da EMA lenta + volume > média",
                "short": "EMA rápida cruza abaixo da EMA lenta + volume > média",
            },
            "exit_conditions": {
                "long": "EMA rápida cruza abaixo da EMA lenta",
                "short": "EMA rápida cruza acima da EMA lenta",
            },
            "strengths": [
                "Boa para mercados em tendência",
                "Sinais claros de entrada/saída",
                "Filtro de volume reduz falsos sinais",
            ],
            "weaknesses": [
                "Pode gerar whipsaws em mercados laterais",
                "Sinais atrasados em reversões rápidas",
                "Dependente de volume para confirmação",
            ],
        }


# Factory function para compatibilidade
def create_ema_crossover_strategy(
    fast_ema: int = 12, slow_ema: int = 26, volume_filter: bool = True
) -> EMACrossoverStrategy:
    """Cria instância da estratégia EMA Crossover"""
    return EMACrossoverStrategy(fast_ema, slow_ema, volume_filter)


# Configuração padrão para registro no sistema
STRATEGY_CONFIG = {
    "key": "ema_crossover",
    "class": EMACrossoverStrategy,
    "factory": create_ema_crossover_strategy,
    "default_params": {"fast_ema": 12, "slow_ema": 26, "volume_filter": True},
}
