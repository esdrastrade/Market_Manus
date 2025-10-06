"""
ICT Market Structure Module - Pilar 1 do ICT Framework

Implementa detectores aprimorados de estrutura de mercado seguindo metodologia ICT:
- BOS (Break of Structure) com validação de volume
- CHoCH (Change of Character) com validação de contexto BOS
- Order Blocks com status de mitigação (fresh vs mitigated)
- Liquidity Sweep com zonas premium/discount
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from market_manus.core.signal import Signal


@dataclass
class MarketStructureState:
    """Estado da estrutura de mercado"""
    last_bos: Optional[Dict] = None
    last_choch: Optional[Dict] = None
    order_blocks: List[Dict] = field(default_factory=list)
    liquidity_zones: List[Dict] = field(default_factory=list)
    trend_direction: str = "NEUTRAL"


def detect_bos_advanced(df: pd.DataFrame, state: MarketStructureState, 
                        min_displacement: float = 0.001, volume_threshold: float = 1.2) -> Tuple[Signal, MarketStructureState]:
    """
    BOS Aprimorado com:
    - Validação de volume relativo (>1.2x média)
    - Tracking de displacement
    - Estado persistente para CHoCH validation
    
    Melhoria conforme análise: adiciona volume como parte da confiança
    """
    if df is None or len(df) < 10:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:BOS"], reasons=["Dados insuficientes"]), state
    
    highs = df['high']
    lows = df['low']
    closes = df['close']
    volumes = df['volume'] if 'volume' in df.columns else pd.Series([1.0] * len(df))
    
    last_swing_high = highs.iloc[-10:-1].max()
    last_swing_low = lows.iloc[-10:-1].min()
    current_close = closes.iat[-1]
    current_volume = volumes.iat[-1]
    avg_volume = volumes.iloc[-20:].mean() if len(volumes) >= 20 else volumes.mean()
    
    price_range = last_swing_high - last_swing_low
    if price_range == 0:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:BOS"], reasons=["Range zero"]), state
    
    volume_factor = min(current_volume / avg_volume, 2.0) if avg_volume > 0 else 1.0
    
    if current_close > last_swing_high:
        displacement = (current_close - last_swing_high) / price_range
        
        if displacement >= min_displacement:
            base_confidence = min(0.4 + displacement * 5, 0.85)
            
            volume_boost = 0.0
            if volume_factor >= volume_threshold:
                volume_boost = min((volume_factor - 1.0) * 0.15, 0.15)
            
            confidence = min(base_confidence + volume_boost, 1.0)
            
            bos_data = {
                "type": "BULLISH",
                "swing_high": last_swing_high,
                "displacement": displacement,
                "close": current_close,
                "volume_factor": volume_factor,
                "index": len(df) - 1
            }
            state.last_bos = bos_data
            state.trend_direction = "BULLISH"
            
            return Signal(
                action="BUY",
                confidence=confidence,
                reasons=[
                    f"BOS Bullish: rompeu {last_swing_high:.2f}",
                    f"Displacement: {displacement:.2%}",
                    f"Volume: {volume_factor:.1f}x média" + (" ✓" if volume_factor >= volume_threshold else "")
                ],
                tags=["SMC:BOS", "SMC:BOS_BULL", "ICT:MARKET_STRUCTURE"],
                meta={**bos_data, "confidence_breakdown": {"displacement": base_confidence, "volume": volume_boost}}
            ), state
    
    if current_close < last_swing_low:
        displacement = (last_swing_low - current_close) / price_range
        
        if displacement >= min_displacement:
            base_confidence = min(0.4 + displacement * 5, 0.85)
            
            volume_boost = 0.0
            if volume_factor >= volume_threshold:
                volume_boost = min((volume_factor - 1.0) * 0.15, 0.15)
            
            confidence = min(base_confidence + volume_boost, 1.0)
            
            bos_data = {
                "type": "BEARISH",
                "swing_low": last_swing_low,
                "displacement": displacement,
                "close": current_close,
                "volume_factor": volume_factor,
                "index": len(df) - 1
            }
            state.last_bos = bos_data
            state.trend_direction = "BEARISH"
            
            return Signal(
                action="SELL",
                confidence=confidence,
                reasons=[
                    f"BOS Bearish: rompeu {last_swing_low:.2f}",
                    f"Displacement: {displacement:.2%}",
                    f"Volume: {volume_factor:.1f}x média" + (" ✓" if volume_factor >= volume_threshold else "")
                ],
                tags=["SMC:BOS", "SMC:BOS_BEAR", "ICT:MARKET_STRUCTURE"],
                meta={**bos_data, "confidence_breakdown": {"displacement": base_confidence, "volume": volume_boost}}
            ), state
    
    return Signal(action="HOLD", confidence=0.0, tags=["SMC:BOS"], reasons=["Sem BOS detectado"]), state


def detect_choch_advanced(df: pd.DataFrame, state: MarketStructureState) -> Tuple[Signal, MarketStructureState]:
    """
    CHoCH Aprimorado com:
    - Validação de BOS prévia (evita falsos positivos)
    - Verificação de invalidação de BOS
    - Contexto de tendência anterior
    
    Melhoria conforme análise: CHoCH requer estrutura BOS prévia
    """
    if df is None or len(df) < 5 or state.last_bos is None:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:CHOCH"], 
                     reasons=["Sem BOS prévio" if state.last_bos is None else "Dados insuficientes"]), state
    
    highs = df['high']
    lows = df['low']
    closes = df['close']
    
    bos_index = state.last_bos.get('index', 0)
    recent_candles = min(len(df) - bos_index - 1, 10)
    
    if recent_candles < 2:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:CHOCH"], reasons=["Aguardando confirmação"]), state
    
    recent_highs = highs.iloc[bos_index:].tolist()
    recent_lows = lows.iloc[bos_index:].tolist()
    
    was_bullish = state.last_bos['type'] == "BULLISH"
    was_bearish = state.last_bos['type'] == "BEARISH"
    
    if was_bullish:
        swing_high_before_choch = max(recent_highs[:-1]) if len(recent_highs) > 1 else recent_highs[0]
        current_close = closes.iat[-1]
        
        if current_close < min(recent_lows[-3:-1]) if len(recent_lows) >= 3 else recent_lows[0]:
            confidence = 0.65 + (recent_candles * 0.05)
            
            choch_data = {
                "type": "BEARISH",
                "previous_trend": "BULLISH",
                "invalidated_bos": state.last_bos,
                "swing_high": swing_high_before_choch,
                "index": len(df) - 1
            }
            state.last_choch = choch_data
            state.trend_direction = "REVERSAL_BEAR"
            
            return Signal(
                action="SELL",
                confidence=min(confidence, 1.0),
                reasons=[
                    f"CHoCH Bearish: tendência bullish invalidada",
                    f"BOS anterior @ {state.last_bos.get('swing_high', 0):.2f} rompido",
                    f"Confirmação após {recent_candles} candles"
                ],
                tags=["SMC:CHOCH", "SMC:CHOCH_BEARISH", "ICT:MARKET_STRUCTURE"],
                meta=choch_data
            ), state
    
    if was_bearish:
        swing_low_before_choch = min(recent_lows[:-1]) if len(recent_lows) > 1 else recent_lows[0]
        current_close = closes.iat[-1]
        
        if current_close > max(recent_highs[-3:-1]) if len(recent_highs) >= 3 else recent_highs[0]:
            confidence = 0.65 + (recent_candles * 0.05)
            
            choch_data = {
                "type": "BULLISH",
                "previous_trend": "BEARISH",
                "invalidated_bos": state.last_bos,
                "swing_low": swing_low_before_choch,
                "index": len(df) - 1
            }
            state.last_choch = choch_data
            state.trend_direction = "REVERSAL_BULL"
            
            return Signal(
                action="BUY",
                confidence=min(confidence, 1.0),
                reasons=[
                    f"CHoCH Bullish: tendência bearish invalidada",
                    f"BOS anterior @ {state.last_bos.get('swing_low', 0):.2f} rompido",
                    f"Confirmação após {recent_candles} candles"
                ],
                tags=["SMC:CHOCH", "SMC:CHOCH_BULLISH", "ICT:MARKET_STRUCTURE"],
                meta=choch_data
            ), state
    
    return Signal(action="HOLD", confidence=0.0, tags=["SMC:CHOCH"], reasons=["Sem CHoCH detectado"]), state


def detect_order_blocks_advanced(df: pd.DataFrame, state: MarketStructureState, 
                                  min_range: float = 0) -> Tuple[Signal, MarketStructureState]:
    """
    Order Blocks Aprimorado com:
    - Validação de BOS causador
    - Status: FRESH (intacto) vs MITIGATED (já tocado)
    - Verificação de volume e engolfamento
    
    Melhoria conforme análise: OB deve causar BOS + tracking de mitigação
    """
    if df is None or len(df) < 5:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:OB"], reasons=["Dados insuficientes"]), state
    
    obs = []
    curr_max = df['high'].iat[0]
    curr_min = df['low'].iat[0]
    volumes = df['volume'] if 'volume' in df.columns else pd.Series([1.0] * len(df))
    avg_volume = volumes.mean()
    
    for i in range(1, len(df)):
        h, l, o, c = df['high'].iat[i], df['low'].iat[i], df['open'].iat[i], df['close'].iat[i]
        prev_h, prev_l, prev_o, prev_c = df['high'].iat[i-1], df['low'].iat[i-1], df['open'].iat[i-1], df['close'].iat[i-1]
        prev_vol = volumes.iat[i-1]
        curr_vol = volumes.iat[i]
        
        if c > curr_max:
            caused_bos = c > df['high'].iloc[:i].max()
            
            if prev_c < prev_o and abs(prev_h - prev_l) >= min_range:
                volume_factor = prev_vol / avg_volume if avg_volume > 0 else 1.0
                is_engulfing = (c > prev_h and o < prev_l)
                
                obs.append({
                    "index": i-1,
                    "type": "bullish",
                    "zone": (prev_l, prev_h),
                    "strength": abs(prev_h - prev_l),
                    "caused_bos": caused_bos,
                    "volume_factor": volume_factor,
                    "is_engulfing": is_engulfing,
                    "status": "FRESH"
                })
            curr_max = h
        
        if c < curr_min:
            caused_bos = c < df['low'].iloc[:i].min()
            
            if prev_c > prev_o and abs(prev_h - prev_l) >= min_range:
                volume_factor = prev_vol / avg_volume if avg_volume > 0 else 1.0
                is_engulfing = (c < prev_l and o > prev_h)
                
                obs.append({
                    "index": i-1,
                    "type": "bearish",
                    "zone": (prev_l, prev_h),
                    "strength": abs(prev_h - prev_l),
                    "caused_bos": caused_bos,
                    "volume_factor": volume_factor,
                    "is_engulfing": is_engulfing,
                    "status": "FRESH"
                })
            curr_min = l
    
    for ob in obs:
        ob_zone_low, ob_zone_high = ob['zone']
        for i in range(ob['index'] + 1, len(df)):
            if df['low'].iat[i] <= ob_zone_high and df['high'].iat[i] >= ob_zone_low:
                ob['status'] = "MITIGATED"
                break
    
    fresh_obs = [ob for ob in obs if ob['status'] == "FRESH"]
    
    if not fresh_obs:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:OB"], 
                     reasons=["Nenhum OB FRESH detectado"]), state
    
    last_ob = fresh_obs[-1]
    ob_type = last_ob["type"]
    zone = last_ob["zone"]
    strength = last_ob["strength"]
    caused_bos = last_ob["caused_bos"]
    volume_factor = last_ob["volume_factor"]
    is_engulfing = last_ob["is_engulfing"]
    
    avg_range = df['high'].sub(df['low']).mean()
    base_confidence = min(0.4 + (strength / avg_range) * 0.2, 0.7) if avg_range > 0 else 0.4
    
    bos_boost = 0.15 if caused_bos else 0.0
    volume_boost = min((volume_factor - 1.0) * 0.1, 0.1) if volume_factor > 1.0 else 0.0
    engulf_boost = 0.05 if is_engulfing else 0.0
    
    confidence = min(base_confidence + bos_boost + volume_boost + engulf_boost, 1.0)
    
    state.order_blocks.append(last_ob)
    if len(state.order_blocks) > 50:
        state.order_blocks = state.order_blocks[-50:]
    
    action = "BUY" if ob_type == "bullish" else "SELL"
    return Signal(
        action=action,
        confidence=confidence,
        reasons=[
            f"Order Block {ob_type.upper()} FRESH @ {zone[0]:.2f}-{zone[1]:.2f}",
            f"Causou BOS: {'SIM' if caused_bos else 'NÃO'}",
            f"Volume: {volume_factor:.1f}x" + (" + Engolfamento" if is_engulfing else "")
        ],
        tags=["SMC:OB", f"SMC:OB_{ob_type.upper()}", "SMC:OB_FRESH", "ICT:MARKET_STRUCTURE"],
        meta={
            **last_ob,
            "confidence_breakdown": {
                "base": base_confidence,
                "bos": bos_boost,
                "volume": volume_boost,
                "engulfing": engulf_boost
            }
        }
    ), state


def detect_liquidity_sweep_advanced(df: pd.DataFrame, state: MarketStructureState,
                                     body_ratio: float = 0.5) -> Tuple[Signal, MarketStructureState]:
    """
    Liquidity Sweep Aprimorado com:
    - Detecção de igualdades (equal highs/lows)
    - Zonas premium/discount (50% range)
    - Draw on liquidity
    
    Melhoria conforme análise: considera localização premium/discount
    """
    if df is None or len(df) < 10:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:SWEEP"], reasons=["Dados insuficientes"]), state
    
    highs = df['high']
    lows = df['low']
    closes = df['close']
    opens = df['open']
    
    range_high = highs.max()
    range_low = lows.min()
    midpoint = (range_high + range_low) / 2
    
    equal_highs = []
    equal_lows = []
    tolerance = (range_high - range_low) * 0.002
    
    for i in range(len(df) - 1):
        if abs(highs.iat[i] - highs.iat[i+1]) <= tolerance:
            equal_highs.append(highs.iat[i])
        if abs(lows.iat[i] - lows.iat[i+1]) <= tolerance:
            equal_lows.append(lows.iat[i])
    
    liquidity_zones = list(set(equal_highs + equal_lows))
    state.liquidity_zones = [{"level": lz, "type": "equal_high" if lz in equal_highs else "equal_low"} 
                             for lz in liquidity_zones]
    
    sweeps = []
    
    for i in range(1, len(df)):
        h, l, o, c = highs.iat[i], lows.iat[i], opens.iat[i], closes.iat[i]
        rng = h - l
        body = abs(c - o)
        
        if rng == 0 or body / rng > body_ratio:
            continue
        
        for lz in liquidity_zones:
            if h > lz and c < lz:
                wick_size = h - max(o, c)
                is_premium = lz > midpoint
                
                sweeps.append({
                    "index": i,
                    "level": lz,
                    "direction": "up",
                    "type": "bearish",
                    "wick_size": wick_size,
                    "zone": "PREMIUM" if is_premium else "DISCOUNT",
                    "is_equal_high": lz in equal_highs
                })
            
            if l < lz and c > lz:
                wick_size = min(o, c) - l
                is_discount = lz < midpoint
                
                sweeps.append({
                    "index": i,
                    "level": lz,
                    "direction": "down",
                    "type": "bullish",
                    "wick_size": wick_size,
                    "zone": "DISCOUNT" if is_discount else "PREMIUM",
                    "is_equal_low": lz in equal_lows
                })
    
    if not sweeps:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:SWEEP"], reasons=["Nenhum sweep detectado"]), state
    
    last_sweep = sweeps[-1]
    sweep_type = last_sweep["type"]
    level = last_sweep["level"]
    wick_size = last_sweep["wick_size"]
    zone = last_sweep["zone"]
    is_equal = last_sweep.get("is_equal_high", False) or last_sweep.get("is_equal_low", False)
    
    avg_range = df['high'].sub(df['low']).mean()
    base_confidence = min(0.45 + (wick_size / avg_range) * 0.25, 0.75) if avg_range > 0 else 0.45
    
    zone_boost = 0.0
    if (sweep_type == "bullish" and zone == "DISCOUNT") or (sweep_type == "bearish" and zone == "PREMIUM"):
        zone_boost = 0.1
    
    equal_boost = 0.1 if is_equal else 0.0
    
    confidence = min(base_confidence + zone_boost + equal_boost, 1.0)
    
    action = "BUY" if sweep_type == "bullish" else "SELL"
    return Signal(
        action=action,
        confidence=confidence,
        reasons=[
            f"Liquidity Sweep {sweep_type.upper()} @ {level:.2f}",
            f"Zona: {zone}" + (" (optimal)" if zone_boost > 0 else ""),
            f"Equal {'High' if last_sweep.get('is_equal_high') else 'Low'}" if is_equal else "Single level"
        ],
        tags=["SMC:SWEEP", f"SMC:SWEEP_{sweep_type.upper()}", f"SMC:ZONE_{zone}", "ICT:MARKET_STRUCTURE"],
        meta={
            **last_sweep,
            "confidence_breakdown": {
                "base": base_confidence,
                "zone": zone_boost,
                "equal": equal_boost
            }
        }
    ), state
