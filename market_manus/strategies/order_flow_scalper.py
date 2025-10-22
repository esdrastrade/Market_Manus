"""
Order Flow Scalper Strategy
Usa métricas de microestrutura (CVD, spread, imbalance, book L2) para gerar sinais.
"""

from typing import Dict, Optional
import pandas as pd
from market_manus.core.signal import Signal


def _compute_atr(df: pd.DataFrame, period: int = 14) -> float:
    if df is None or df.empty or len(df) < period + 1:
        return 0.0
    high = df['high']
    low = df['low']
    close = df['close']
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean().iloc[-1]
    return float(atr) if pd.notna(atr) else 0.0


def order_flow_signal(df: pd.DataFrame, metrics: Optional[Dict] = None, params: Optional[Dict] = None) -> Signal:
    """
    Gera Signal baseado em Order Flow.
    Regras:
    - Gate de spread: evita sinais quando spread está alto
    - Direção pela combinação de imbalance e delta do CVD
    - Confiança ponderada por força do desequilíbrio e delta do CVD
    - Filtro de volatilidade via ATR (evita em volatilidade extrema)
    """
    params = params or {}
    metrics = metrics or {}

    last_close = float(df['close'].iloc[-1]) if df is not None and not df.empty else metrics.get('best_ask') or metrics.get('best_bid') or 0.0
    spread = metrics.get('spread')
    imbalance = metrics.get('imbalance')
    cvd = metrics.get('cvd')
    cvd_prev = metrics.get('cvd_prev', cvd)
    cvd_delta = (cvd - cvd_prev) if (cvd is not None and cvd_prev is not None) else None

    # Parâmetros
    max_spread_pct = params.get('max_spread_pct', 0.0005)  # 0.05%
    imbalance_threshold = params.get('imbalance_threshold', 0.2)  # 20%
    atr_period = params.get('atr_period', 14)
    atr_gate_multiplier = params.get('atr_gate_multiplier', 4.0)  # evita se ATR > X * spread

    # Valida dados mínimos
    reasons = []
    tags = ["ORDER_FLOW", "SCALPER"]

    if spread is None or last_close <= 0:
        return Signal(action="HOLD", confidence=0.0, reasons=["Dados insuficientes de preço/spread"], tags=tags, meta={"spread": spread, "price": last_close})

    # Gate de spread
    max_allowed_spread = last_close * max_spread_pct
    if spread > max_allowed_spread:
        reasons.append(f"Spread alto ({spread:.6f} > {max_allowed_spread:.6f})")
        return Signal(action="HOLD", confidence=0.0, reasons=reasons or ["Spread alto"], tags=tags, meta={"spread": spread, "price": last_close})

    # Filtro de volatilidade com ATR
    atr = _compute_atr(df, period=atr_period) if df is not None and not df.empty else 0.0
    if atr > 0 and spread > 0 and atr > atr_gate_multiplier * spread:
        reasons.append(f"ATR elevado ({atr:.6f} > {atr_gate_multiplier:.1f}×spread)")
        return Signal(action="HOLD", confidence=0.0, reasons=reasons, tags=tags, meta={"atr": atr, "spread": spread})

    # Direção: imbalance + cvd_delta
    if imbalance is None or cvd_delta is None:
        return Signal(action="HOLD", confidence=0.0, reasons=["Sem imbalance/CVD delta"], tags=tags, meta={"imbalance": imbalance, "cvd_delta": cvd_delta})

    # Confiança: combinação de força do desequilíbrio e magnitude do delta CVD
    # Normalizações simples
    imbalance_strength = max(0.0, min(abs(imbalance), 1.0))  # 0..1
    # CVD delta normalizado pelo volume relativo estimado (heurístico)
    vol_norm = params.get('cvd_norm_qty', 1000.0)
    cvd_strength = max(0.0, min(abs(cvd_delta) / vol_norm, 1.0))

    base_confidence = (0.6 * imbalance_strength) + (0.4 * cvd_strength)
    # Boost quando spread muito baixo
    if spread < max_allowed_spread / 2:
        base_confidence = min(1.0, base_confidence * 1.15)

    action = "HOLD"
    if imbalance > imbalance_threshold and cvd_delta > 0:
        action = "BUY"
        reasons.append(f"Desequilíbrio comprador {imbalance:.2f} e CVD↑ {cvd_delta:.2f}")
        tags.append("IMBALANCE_LONG")
    elif imbalance < -imbalance_threshold and cvd_delta < 0:
        action = "SELL"
        reasons.append(f"Desequilíbrio vendedor {imbalance:.2f} e CVD↓ {cvd_delta:.2f}")
        tags.append("IMBALANCE_SHORT")
    else:
        reasons.append("Condições insuficientes de desequilíbrio/delta")

    confidence = base_confidence if action != "HOLD" else 0.0

    meta = {
        "price": last_close,
        "spread": spread,
        "imbalance": imbalance,
        "cvd": cvd,
        "cvd_delta": cvd_delta,
        "atr": atr,
    }

    return Signal(action=action, confidence=confidence, reasons=reasons, tags=tags, meta=meta)


# Registro opcional para gerenciadores dinâmicos
STRATEGY_CONFIG = {
    "key": "order_flow_scalper",
    "name": "Order Flow Scalper",
    "type": "microstructure",
    "risk_level": "high",
    "timeframes": ["1m", "3m", "5m"],
    "description": "Scalper baseado em CVD, spread e order book imbalance",
    "calculate": order_flow_signal,
}