#!/usr/bin/env python3
"""
RSI MEAN REVERSION STRATEGY - Estratégia de Reversão à Média com RSI
Estratégia modular para o Market Manus Strategy Factory
"""

from typing import Dict, List
from src.core.base_strategy import BaseStrategy, StrategyConfig


class RSIMeanReversionStrategy(BaseStrategy):
    """Estratégia de reversão à média baseada no RSI"""
    
    def __init__(self, rsi_period: int = 14, oversold: float = 30, overbought: float = 70):
        """
        Inicializa estratégia RSI Mean Reversion
        
        Args:
            rsi_period: Período do RSI (padrão: 14)
            oversold: Nível de sobrevenda (padrão: 30)
            overbought: Nível de sobrecompra (padrão: 70)
        """
        config = StrategyConfig(
            name="RSI Mean Reversion",
            description="Reversão à média com RSI em dados históricos reais",
            risk_level="low",
            best_timeframes=["5m", "15m", "30m"],
            market_conditions="Lateral",
            params={
                "rsi_period": rsi_period,
                "oversold": oversold,
                "overbought": overbought
            }
        )
        super().__init__(config)
    
    def calculate_signals(self, data: List[Dict]) -> List[Dict]:
        """
        Calcula sinais da estratégia RSI Mean Reversion
        
        Args:
            data: Lista de dados OHLCV
            
        Returns:
            Lista de dados com sinais adicionados
        """
        if len(data) < self.config.params["rsi_period"] + 1:
            return self._add_empty_signals(data)
        
        closes = [float(d['close']) for d in data]
        
        # Calcular RSI
        rsi_values = self._calculate_rsi(closes, self.config.params["rsi_period"])
        
        # Gerar sinais
        signals = []
        for i, d in enumerate(data):
            signal = 0
            strength = 0.0
            rsi = rsi_values[i]
            
            # Long: RSI oversold (reversão para cima)
            if rsi < self.config.params["oversold"]:
                signal = 1
                strength = (self.config.params["oversold"] - rsi) / self.config.params["oversold"]
            
            # Short: RSI overbought (reversão para baixo)
            elif rsi > self.config.params["overbought"]:
                signal = -1
                strength = (rsi - self.config.params["overbought"]) / (100 - self.config.params["overbought"])
            
            # Adicionar dados do sinal
            signals.append({
                **d,
                'signal': signal,
                'signal_strength': min(strength, 1.0),
                'rsi': rsi,
                'strategy': 'rsi_mean_reversion'
            })
        
        return signals
    
    def _calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """Calcula RSI (Relative Strength Index)"""
        if len(prices) < period + 1:
            return [50] * len(prices)
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [max(delta, 0) for delta in deltas]
        losses = [abs(min(delta, 0)) for delta in deltas]
        
        rsi_values = [50] * len(prices)
        
        # Primeira média
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        for i in range(period, len(deltas)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi_values[i + 1] = 100
            else:
                rs = avg_gain / avg_loss
                rsi_values[i + 1] = 100 - (100 / (1 + rs))
        
        return rsi_values
    
    def get_strategy_info(self) -> Dict:
        """Retorna informações detalhadas da estratégia"""
        return {
            **super().get_strategy_info(),
            "indicators": ["RSI"],
            "entry_conditions": {
                "long": f"RSI < {self.config.params['oversold']} (sobrevenda)",
                "short": f"RSI > {self.config.params['overbought']} (sobrecompra)"
            },
            "exit_conditions": {
                "long": f"RSI > {100 - self.config.params['oversold']} ou stop loss",
                "short": f"RSI < {self.config.params['overbought']} ou stop loss"
            },
            "strengths": [
                "Excelente para mercados laterais",
                "Identifica pontos de reversão",
                "Baixo risco em condições normais",
                "Sinais claros de entrada"
            ],
            "weaknesses": [
                "Pode ficar 'preso' em tendências fortes",
                "RSI pode permanecer em extremos por muito tempo",
                "Menos efetivo em mercados muito voláteis",
                "Requer confirmação adicional em breakouts"
            ]
        }


# Factory function para compatibilidade
def create_rsi_mean_reversion_strategy(rsi_period: int = 14, oversold: float = 30, overbought: float = 70) -> RSIMeanReversionStrategy:
    """Cria instância da estratégia RSI Mean Reversion"""
    return RSIMeanReversionStrategy(rsi_period, oversold, overbought)


# Configuração padrão para registro no sistema
STRATEGY_CONFIG = {
    'key': 'rsi_mean_reversion',
    'class': RSIMeanReversionStrategy,
    'factory': create_rsi_mean_reversion_strategy,
    'default_params': {
        'rsi_period': 14,
        'oversold': 30,
        'overbought': 70
    }
}

