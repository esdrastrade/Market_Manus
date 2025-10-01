"""
Signal data model - Contrato padronizado para todos os sinais (SMC + Classic)
"""

from dataclasses import dataclass, field
from typing import Literal
from datetime import datetime

@dataclass
class Signal:
    """
    Modelo padronizado de sinal para SMC e estratégias clássicas.
    
    Attributes:
        action: Ação recomendada - "BUY", "SELL" ou "HOLD"
        confidence: Confiança no sinal [0.0 a 1.0]
        reasons: Lista de razões explicando por que o sinal surgiu
        tags: Tags de identificação (ex.: ["SMC:BOS", "CLASSIC:MACD_CROSSUP"])
        meta: Metadados adicionais (preço, timeframe, símbolo, valores de indicadores)
        timestamp: Timestamp do sinal (Unix timestamp ou ISO string)
    """
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float
    reasons: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)
    timestamp: int | str | None = None
    
    def __post_init__(self):
        """Valida os campos após inicialização"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence deve estar entre 0.0 e 1.0, recebido: {self.confidence}")
        
        if self.action not in ["BUY", "SELL", "HOLD"]:
            raise ValueError(f"Action deve ser BUY, SELL ou HOLD, recebido: {self.action}")
        
        if self.timestamp is None:
            self.timestamp = int(datetime.now().timestamp())
    
    def get_direction(self) -> int:
        """Retorna direção numérica: +1 para BUY, -1 para SELL, 0 para HOLD"""
        if self.action == "BUY":
            return 1
        elif self.action == "SELL":
            return -1
        else:
            return 0
    
    def to_dict(self) -> dict:
        """Converte signal para dict para serialização"""
        return {
            "action": self.action,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "tags": self.tags,
            "meta": self.meta,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Signal':
        """Cria Signal a partir de dict"""
        return cls(
            action=data["action"],
            confidence=data["confidence"],
            reasons=data.get("reasons", []),
            tags=data.get("tags", []),
            meta=data.get("meta", {}),
            timestamp=data.get("timestamp")
        )
    
    def __repr__(self) -> str:
        """Representação string legível"""
        return f"Signal(action={self.action}, confidence={self.confidence:.2f}, tags={self.tags})"
