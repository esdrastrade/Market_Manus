"""
ICT Context Module - Pilar 2 do ICT Framework

Classifica o contexto de mercado para filtrar setups:
- Consolidation: mercado lateral (ADX < 20, ATR baixo)
- Impulse: movimento forte direcional (ADX > 25, BOS recente)
- Reversal: mudança de tendência (CHoCH + divergência)
- Fair Value Gap: imbalances como contexto de entrada
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from dataclasses import dataclass, field
from market_manus.core.signal import Signal


@dataclass
class MarketContext:
    """Contexto de mercado atual"""
    regime: str  # CONSOLIDATION, IMPULSE, REVERSAL
    strength: float  # 0.0 - 1.0
    adx: float
    atr: float
    trend_direction: Optional[str] = None
    fvg_present: bool = False
    meta: Dict = field(default_factory=dict)


def detect_consolidation(df: pd.DataFrame, adx_threshold: float = 20, 
                         atr_threshold: float = 0.5) -> MarketContext:
    """
    Detecta consolidação:
    - ADX < 20 (sem tendência definida)
    - ATR abaixo da média (baixa volatilidade)
    - Range estreito
    """
    if df is None or len(df) < 14:
        return MarketContext(regime="UNKNOWN", strength=0.0, adx=0.0, atr=0.0)
    
    adx = calculate_adx(df, period=14)
    atr = calculate_atr(df, period=14)
    atr_ma = atr.mean()
    
    current_adx = adx.iat[-1] if not pd.isna(adx.iat[-1]) else 0
    current_atr = atr.iat[-1] if not pd.isna(atr.iat[-1]) else 0
    
    is_consolidating = current_adx < adx_threshold and current_atr < atr_ma * atr_threshold
    
    if is_consolidating:
        strength = 1.0 - (current_adx / adx_threshold)
        
        return MarketContext(
            regime="CONSOLIDATION",
            strength=min(strength, 1.0),
            adx=current_adx,
            atr=current_atr,
            meta={
                "atr_vs_avg": current_atr / atr_ma if atr_ma > 0 else 0,
                "range_high": df['high'].iloc[-20:].max(),
                "range_low": df['low'].iloc[-20:].min()
            }
        )
    
    return MarketContext(regime="NOT_CONSOLIDATION", strength=0.0, adx=current_adx, atr=current_atr)


def detect_impulse(df: pd.DataFrame, adx_threshold: float = 25, 
                   displacement_threshold: float = 0.015) -> MarketContext:
    """
    Detecta movimento impulsivo:
    - ADX > 25 (tendência forte)
    - Displacement recente > 1.5%
    - Volume acima da média
    """
    if df is None or len(df) < 14:
        return MarketContext(regime="UNKNOWN", strength=0.0, adx=0.0, atr=0.0)
    
    adx = calculate_adx(df, period=14)
    current_adx = adx.iat[-1] if not pd.isna(adx.iat[-1]) else 0
    
    highs = df['high']
    lows = df['low']
    closes = df['close']
    volumes = df['volume'] if 'volume' in df.columns else pd.Series([1.0] * len(df))
    
    recent_high = highs.iloc[-5:].max()
    recent_low = lows.iloc[-5:].min()
    displacement = (recent_high - recent_low) / recent_low if recent_low > 0 else 0
    
    avg_volume = volumes.iloc[-20:].mean()
    recent_volume = volumes.iloc[-5:].mean()
    volume_surge = recent_volume / avg_volume if avg_volume > 0 else 1.0
    
    is_impulse = (current_adx > adx_threshold and 
                  displacement > displacement_threshold and 
                  volume_surge > 1.1)
    
    if is_impulse:
        last_close = closes.iat[-1]
        ma_20 = closes.iloc[-20:].mean()
        trend_direction = "BULLISH" if last_close > ma_20 else "BEARISH"
        
        adx_strength = min((current_adx - adx_threshold) / 30, 1.0)
        displacement_strength = min(displacement / displacement_threshold, 1.0)
        strength = (adx_strength + displacement_strength) / 2
        
        return MarketContext(
            regime="IMPULSE",
            strength=min(strength, 1.0),
            adx=current_adx,
            atr=calculate_atr(df, period=14).iat[-1],
            trend_direction=trend_direction,
            meta={
                "displacement": displacement,
                "volume_surge": volume_surge,
                "recent_high": recent_high,
                "recent_low": recent_low
            }
        )
    
    return MarketContext(regime="NOT_IMPULSE", strength=0.0, adx=current_adx, atr=0.0)


def detect_reversal(df: pd.DataFrame, rsi_divergence: bool = True) -> MarketContext:
    """
    Detecta reversão:
    - Divergência RSI (opcional)
    - Mudança na estrutura de mercado
    - Volume climático
    """
    if df is None or len(df) < 20:
        return MarketContext(regime="UNKNOWN", strength=0.0, adx=0.0, atr=0.0)
    
    closes = df['close']
    highs = df['high']
    lows = df['low']
    volumes = df['volume'] if 'volume' in df.columns else pd.Series([1.0] * len(df))
    
    rsi = calculate_rsi(closes, period=14)
    
    recent_price_high_idx = highs.iloc[-10:].idxmax()
    recent_price_low_idx = lows.iloc[-10:].idxmin()
    
    has_bearish_divergence = False
    has_bullish_divergence = False
    
    if rsi_divergence and not rsi.empty:
        if recent_price_high_idx == highs.iloc[-10:].index[-1]:
            prev_high_idx = highs.iloc[-20:-10].idxmax()
            if highs.loc[recent_price_high_idx] > highs.loc[prev_high_idx]:
                if rsi.loc[recent_price_high_idx] < rsi.loc[prev_high_idx]:
                    has_bearish_divergence = True
        
        if recent_price_low_idx == lows.iloc[-10:].index[-1]:
            prev_low_idx = lows.iloc[-20:-10].idxmin()
            if lows.loc[recent_price_low_idx] < lows.loc[prev_low_idx]:
                if rsi.loc[recent_price_low_idx] > rsi.loc[prev_low_idx]:
                    has_bullish_divergence = True
    
    avg_volume = volumes.iloc[-30:].mean()
    current_volume = volumes.iat[-1]
    is_climax = current_volume > avg_volume * 2.0
    
    ma_short = closes.iloc[-10:].mean()
    ma_long = closes.iloc[-20:].mean()
    structure_change = (closes.iat[-1] < ma_short < ma_long) or (closes.iat[-1] > ma_short > ma_long)
    
    if has_bearish_divergence or has_bullish_divergence or (is_climax and structure_change):
        reversal_type = "BEARISH" if has_bearish_divergence or (structure_change and closes.iat[-1] < ma_short) else "BULLISH"
        
        strength = 0.5
        if has_bearish_divergence or has_bullish_divergence:
            strength += 0.3
        if is_climax:
            strength += 0.2
        
        return MarketContext(
            regime="REVERSAL",
            strength=min(strength, 1.0),
            adx=calculate_adx(df, period=14).iat[-1],
            atr=calculate_atr(df, period=14).iat[-1],
            trend_direction=reversal_type,
            meta={
                "divergence": "BEARISH" if has_bearish_divergence else ("BULLISH" if has_bullish_divergence else "NONE"),
                "climax_volume": is_climax,
                "volume_ratio": current_volume / avg_volume if avg_volume > 0 else 1.0
            }
        )
    
    return MarketContext(regime="NOT_REVERSAL", strength=0.0, adx=0.0, atr=0.0)


def detect_fvg_context(df: pd.DataFrame) -> MarketContext:
    """
    Fair Value Gap como contexto (não sinal):
    - FVG 3-candle (candle 1 e 3, não 2 consecutivos)
    - Tracking de retest
    - Zona de entrada preferencial
    """
    if df is None or len(df) < 3:
        return MarketContext(regime="NO_FVG", strength=0.0, adx=0.0, atr=0.0, fvg_present=False)
    
    gaps = []
    
    for i in range(2, len(df)):
        candle_1_high = df['high'].iat[i-2]
        candle_1_low = df['low'].iat[i-2]
        candle_3_high = df['high'].iat[i]
        candle_3_low = df['low'].iat[i]
        
        if candle_3_low > candle_1_high:
            gap_size = candle_3_low - candle_1_high
            gaps.append({
                "type": "bullish",
                "gap": (candle_1_high, candle_3_low),
                "size": gap_size,
                "index": i,
                "retested": False
            })
        
        elif candle_3_high < candle_1_low:
            gap_size = candle_1_low - candle_3_high
            gaps.append({
                "type": "bearish",
                "gap": (candle_3_high, candle_1_low),
                "size": gap_size,
                "index": i,
                "retested": False
            })
    
    for gap in gaps:
        gap_low, gap_high = gap['gap']
        for i in range(gap['index'] + 1, len(df)):
            if df['low'].iat[i] <= gap_high and df['high'].iat[i] >= gap_low:
                gap['retested'] = True
                break
    
    fresh_gaps = [g for g in gaps if not g['retested']]
    
    if fresh_gaps:
        last_gap = fresh_gaps[-1]
        avg_range = df['high'].sub(df['low']).mean()
        strength = min(last_gap['size'] / avg_range, 1.0) if avg_range > 0 else 0.5
        
        return MarketContext(
            regime="FVG_PRESENT",
            strength=strength,
            adx=0.0,
            atr=0.0,
            fvg_present=True,
            trend_direction="BULLISH" if last_gap['type'] == "bullish" else "BEARISH",
            meta={
                "fvg_type": last_gap['type'],
                "fvg_zone": last_gap['gap'],
                "fvg_size": last_gap['size'],
                "total_fresh_gaps": len(fresh_gaps)
            }
        )
    
    return MarketContext(regime="NO_FVG", strength=0.0, adx=0.0, atr=0.0, fvg_present=False)


def get_market_context(df: pd.DataFrame) -> MarketContext:
    """
    Retorna o contexto dominante de mercado priorizando:
    1. Reversal (mais crítico)
    2. Impulse (oportunidade)
    3. Consolidation (evitar)
    """
    reversal_ctx = detect_reversal(df)
    if reversal_ctx.regime == "REVERSAL":
        fvg_ctx = detect_fvg_context(df)
        reversal_ctx.fvg_present = fvg_ctx.fvg_present
        if fvg_ctx.fvg_present:
            reversal_ctx.meta.update(fvg_ctx.meta)
        return reversal_ctx
    
    impulse_ctx = detect_impulse(df)
    if impulse_ctx.regime == "IMPULSE":
        fvg_ctx = detect_fvg_context(df)
        impulse_ctx.fvg_present = fvg_ctx.fvg_present
        if fvg_ctx.fvg_present:
            impulse_ctx.meta.update(fvg_ctx.meta)
        return impulse_ctx
    
    consolidation_ctx = detect_consolidation(df)
    if consolidation_ctx.regime == "CONSOLIDATION":
        return consolidation_ctx
    
    return MarketContext(regime="UNDEFINED", strength=0.0, adx=0.0, atr=0.0)


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calcula ADX (Average Directional Index)"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = tr.rolling(window=period).mean()
    
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    
    return adx


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calcula ATR (Average True Range)"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calcula RSI (Relative Strength Index)"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi
