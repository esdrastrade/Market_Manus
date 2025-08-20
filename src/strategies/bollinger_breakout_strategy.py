#!/usr/bin/env python3
"""
BOLLINGER BREAKOUT STRATEGY - Estratégia de Rompimento de Bandas de Bollinger
Estratégia modular para o Market Manus Strategy Factory
"""

from typing import Dict, List, Tuple
from src.core.base_strategy import BaseStrategy, StrategyConfig


class BollingerBreakoutStrategy(BaseStrategy):
    """Estratégia de rompimento de bandas de Bollinger"""
    
    def __init__(self, bb_period: int = 20, bb_std: float = 2.0, volume_filter: bool = True):
        """
        Inicializa estratégia Bollinger Breakout
        
        Args:
            bb_period: Período das Bandas de Bollinger (padrão: 20)
            bb_std: Desvio padrão das bandas (padrão: 2.0)
            volume_filter: Usar filtro de volume (padrão: True)
        """
        config = StrategyConfig(
            name="Bollinger Breakout",
            description="Rompimento de bandas de Bollinger com dados históricos reais",
            risk_level="high",
            best_timeframes=["15m", "1h", "4h"],
            market_conditions="Volátil",
            params={
                "bb_period": bb_period,
                "bb_std": bb_std,
                "volume_filter": volume_filter
            }
        )
        super().__init__(config)
    
    def calculate_signals(self, data: List[Dict]) -> List[Dict]:
        """
        Calcula sinais da estratégia Bollinger Breakout
        
        Args:
            data: Lista de dados OHLCV
            
        Returns:
            Lista de dados com sinais adicionados
        """
        if len(data) < self.config.params["bb_period"]:
            return self._add_empty_signals(data)
        
        closes = [float(d['close']) for d in data]
        volumes = [float(d['volume']) for d in data]
        
        # Calcular Bandas de Bollinger
        middle, upper, lower = self._calculate_bollinger_bands(
            closes, 
            self.config.params["bb_period"], 
            self.config.params["bb_std"]
        )
        
        # Calcular filtro de volume se habilitado
        volume_ma = self._calculate_volume_filter(volumes) if self.config.params["volume_filter"] else None
        
        # Gerar sinais
        signals = []
        for i, d in enumerate(data):
            signal = 0
            strength = 0.0
            
            if i > 0:
                # Verificar filtro de volume
                volume_ok = True
                if self.config.params["volume_filter"] and volume_ma:
                    volume_ok = volumes[i] > volume_ma[i] * 1.2
                
                # Long: Preço rompe banda superior (breakout para cima)
                if (closes[i] > upper[i] and 
                    closes[i-1] <= upper[i-1] and 
                    volume_ok):
                    signal = 1
                    band_width = (upper[i] - lower[i]) / middle[i]
                    strength = min(band_width, 1.0)
                
                # Short: Preço rompe banda inferior (breakout para baixo)
                elif (closes[i] < lower[i] and 
                      closes[i-1] >= lower[i-1] and 
                      volume_ok):
                    signal = -1
                    band_width = (upper[i] - lower[i]) / middle[i]
                    strength = min(band_width, 1.0)
            
            # Adicionar dados do sinal
            signal_data = {
                **d,
                'signal': signal,
                'signal_strength': strength,
                'bb_upper': upper[i],
                'bb_middle': middle[i],
                'bb_lower': lower[i],
                'strategy': 'bollinger_breakout'
            }
            
            if volume_ma:
                signal_data['volume_ma'] = volume_ma[i]
            
            signals.append(signal_data)
        
        return signals
    
    def _calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2) -> Tuple[List[float], List[float], List[float]]:
        """Calcula Bandas de Bollinger"""
        if len(prices) < period:
            return [prices[0]] * len(prices), [prices[0]] * len(prices), [prices[0]] * len(prices)
        
        middle = []  # SMA
        upper = []
        lower = []
        
        for i in range(len(prices)):
            if i < period - 1:
                window = prices[:i+1]
            else:
                window = prices[i-period+1:i+1]
            
            sma = sum(window) / len(window)
            
            # Calcular desvio padrão
            variance = sum((x - sma) ** 2 for x in window) / len(window)
            std = variance ** 0.5
            
            middle.append(sma)
            upper.append(sma + (std_dev * std))
            lower.append(sma - (std_dev * std))
        
        return middle, upper, lower
    
    def _calculate_volume_filter(self, volumes: List[float]) -> List[float]:
        """Calcula filtro de volume (média móvel de 20 períodos)"""
        volume_ma = []
        for i in range(len(volumes)):
            if i < 20:
                volume_ma.append(sum(volumes[:i+1]) / (i+1))
            else:
                volume_ma.append(sum(volumes[i-19:i+1]) / 20)
        return volume_ma
    
    def get_strategy_info(self) -> Dict:
        """Retorna informações detalhadas da estratégia"""
        return {
            **super().get_strategy_info(),
            "indicators": ["Bollinger Bands", "Volume MA"],
            "entry_conditions": {
                "long": "Preço rompe banda superior + volume > 120% da média",
                "short": "Preço rompe banda inferior + volume > 120% da média"
            },
            "exit_conditions": {
                "long": "Preço retorna para dentro das bandas ou stop loss",
                "short": "Preço retorna para dentro das bandas ou stop loss"
            },
            "strengths": [
                "Excelente para capturar breakouts",
                "Adapta-se à volatilidade do mercado",
                "Filtro de volume confirma movimentos",
                "Boa para mercados em expansão"
            ],
            "weaknesses": [
                "Pode gerar falsos breakouts",
                "Alto risco em mercados laterais",
                "Requer gestão rigorosa de risco",
                "Sensível a configuração de parâmetros"
            ]
        }


# Factory function para compatibilidade
def create_bollinger_breakout_strategy(bb_period: int = 20, bb_std: float = 2.0, volume_filter: bool = True) -> BollingerBreakoutStrategy:
    """Cria instância da estratégia Bollinger Breakout"""
    return BollingerBreakoutStrategy(bb_period, bb_std, volume_filter)


# Configuração padrão para registro no sistema
STRATEGY_CONFIG = {
    'key': 'bollinger_breakout',
    'class': BollingerBreakoutStrategy,
    'factory': create_bollinger_breakout_strategy,
    'default_params': {
        'bb_period': 20,
        'bb_std': 2.0,
        'volume_filter': True
    }
}

