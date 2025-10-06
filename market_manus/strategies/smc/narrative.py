"""
ICT Narrative Module - Pilar 3 do ICT Framework

Define a narrativa de mercado para contextualizar setups:
- Internal Range Liquidity: liquidez dentro do range (stops internos)
- External Range Liquidity: liquidez fora do range (stop hunt externo)
- Killzones: sessões de alta probabilidade (London, New York)
- HTF Context: confluência com timeframe superior
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from market_manus.core.signal import Signal


@dataclass
class MarketNarrative:
    """Narrativa de mercado atual"""
    liquidity_type: str  # INTERNAL, EXTERNAL, BALANCED
    liquidity_zones: List[Dict]
    killzone: Optional[str] = None
    htf_bias: Optional[str] = None
    strength: float = 0.0
    meta: Dict = field(default_factory=dict)


def detect_internal_range_liquidity(df: pd.DataFrame, lookback: int = 20) -> Dict:
    """
    Liquidez interna: stops dentro do range (support/resistance interno)
    
    Identifica:
    - Zonas de acumulação de stops (swing points internos)
    - Resting liquidity em fractals
    - Equal lows/highs dentro do range
    """
    if df is None or len(df) < lookback:
        return {"type": "NONE", "zones": [], "strength": 0.0}
    
    highs = df['high'].iloc[-lookback:]
    lows = df['low'].iloc[-lookback:]
    
    range_high = highs.max()
    range_low = lows.min()
    range_size = range_high - range_low
    
    if range_size == 0:
        return {"type": "NONE", "zones": [], "strength": 0.0}
    
    internal_zones = []
    tolerance = range_size * 0.005
    
    swing_highs = []
    swing_lows = []
    
    for i in range(2, len(highs) - 2):
        if (highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i-2] and
            highs.iloc[i] > highs.iloc[i+1] and highs.iloc[i] > highs.iloc[i+2]):
            swing_highs.append(highs.iloc[i])
        
        if (lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i-2] and
            lows.iloc[i] < lows.iloc[i+1] and lows.iloc[i] < lows.iloc[i+2]):
            swing_lows.append(lows.iloc[i])
    
    for sh in swing_highs:
        if range_low + range_size * 0.2 < sh < range_high - range_size * 0.2:
            cluster_count = sum(1 for other in swing_highs if abs(other - sh) <= tolerance)
            internal_zones.append({
                "level": sh,
                "type": "SELL_SIDE",
                "cluster_count": cluster_count,
                "location": "INTERNAL"
            })
    
    for sl in swing_lows:
        if range_low + range_size * 0.2 < sl < range_high - range_size * 0.2:
            cluster_count = sum(1 for other in swing_lows if abs(other - sl) <= tolerance)
            internal_zones.append({
                "level": sl,
                "type": "BUY_SIDE",
                "cluster_count": cluster_count,
                "location": "INTERNAL"
            })
    
    total_strength = sum(z['cluster_count'] for z in internal_zones)
    strength = min(total_strength / 10.0, 1.0)
    
    return {
        "type": "INTERNAL",
        "zones": internal_zones,
        "strength": strength,
        "range": (range_low, range_high)
    }


def detect_external_range_liquidity(df: pd.DataFrame, lookback: int = 20) -> Dict:
    """
    Liquidez externa: stops fora do range (targets de stop hunt)
    
    Identifica:
    - Highs/lows absolutos (external liquidity pools)
    - Equal highs/lows nos extremos
    - Draw on liquidity além do range
    """
    if df is None or len(df) < lookback:
        return {"type": "NONE", "zones": [], "strength": 0.0}
    
    highs = df['high'].iloc[-lookback:]
    lows = df['low'].iloc[-lookback:]
    
    range_high = highs.max()
    range_low = lows.min()
    range_size = range_high - range_low
    
    if range_size == 0:
        return {"type": "NONE", "zones": [], "strength": 0.0}
    
    external_zones = []
    tolerance = range_size * 0.003
    
    high_indices = [i for i, h in enumerate(highs) if abs(h - range_high) <= tolerance]
    low_indices = [i for i, l in enumerate(lows) if abs(l - range_low) <= tolerance]
    
    if len(high_indices) >= 2:
        external_zones.append({
            "level": range_high,
            "type": "SELL_SIDE",
            "location": "EXTERNAL_HIGH",
            "touch_count": len(high_indices),
            "is_equal": True
        })
    else:
        external_zones.append({
            "level": range_high,
            "type": "SELL_SIDE",
            "location": "EXTERNAL_HIGH",
            "touch_count": 1,
            "is_equal": False
        })
    
    if len(low_indices) >= 2:
        external_zones.append({
            "level": range_low,
            "type": "BUY_SIDE",
            "location": "EXTERNAL_LOW",
            "touch_count": len(low_indices),
            "is_equal": True
        })
    else:
        external_zones.append({
            "level": range_low,
            "type": "BUY_SIDE",
            "location": "EXTERNAL_LOW",
            "touch_count": 1,
            "is_equal": False
        })
    
    strength = 0.0
    for zone in external_zones:
        if zone['is_equal']:
            strength += 0.3
        if zone['touch_count'] >= 3:
            strength += 0.2
    
    strength = min(strength, 1.0)
    
    return {
        "type": "EXTERNAL",
        "zones": external_zones,
        "strength": strength,
        "range": (range_low, range_high)
    }


def detect_killzone(timestamp: Optional[datetime] = None) -> Dict:
    """
    Killzones ICT: sessões de alta probabilidade
    
    - London Killzone: 02:00-05:00 EST (07:00-10:00 UTC)
    - New York AM Killzone: 07:00-10:00 EST (12:00-15:00 UTC)
    - New York PM Killzone: 13:00-16:00 EST (18:00-21:00 UTC)
    
    Retorna zona ativa e força baseada em horário
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    utc_hour = timestamp.hour
    
    london_killzone = (7 <= utc_hour < 10)
    ny_am_killzone = (12 <= utc_hour < 15)
    ny_pm_killzone = (18 <= utc_hour < 21)
    
    if london_killzone:
        return {
            "active": True,
            "zone": "LONDON",
            "strength": 0.85,
            "description": "London Open Killzone (02:00-05:00 EST)",
            "bias": "VOLATILITY_EXPANSION"
        }
    
    if ny_am_killzone:
        return {
            "active": True,
            "zone": "NEW_YORK_AM",
            "strength": 0.9,
            "description": "New York AM Killzone (07:00-10:00 EST)",
            "bias": "DIRECTIONAL_MOVE"
        }
    
    if ny_pm_killzone:
        return {
            "active": True,
            "zone": "NEW_YORK_PM",
            "strength": 0.75,
            "description": "New York PM Killzone (13:00-16:00 EST)",
            "bias": "REVERSAL_SETUP"
        }
    
    return {
        "active": False,
        "zone": "NONE",
        "strength": 0.3,
        "description": "Outside killzones",
        "bias": "LOW_PROBABILITY"
    }


def detect_htf_context(df_ltf: pd.DataFrame, df_htf: Optional[pd.DataFrame] = None) -> Dict:
    """
    Higher Timeframe Context: confluência com TF superior
    
    Se df_htf fornecido:
    - Compara tendência HTF com LTF
    - Valida se LTF está em premium/discount do HTF
    - Verifica alinhamento de estrutura
    
    Se df_htf None:
    - Usa resampling do LTF para simular HTF
    """
    if df_ltf is None or len(df_ltf) < 50:
        return {"bias": "UNKNOWN", "alignment": False, "strength": 0.0}
    
    if df_htf is None:
        htf_closes = df_ltf['close'].iloc[::4]
        htf_highs = df_ltf['high'].iloc[::4]
        htf_lows = df_ltf['low'].iloc[::4]
    else:
        if len(df_htf) < 20:
            return {"bias": "UNKNOWN", "alignment": False, "strength": 0.0}
        htf_closes = df_htf['close']
        htf_highs = df_htf['high']
        htf_lows = df_htf['low']
    
    htf_ma_fast = htf_closes.iloc[-10:].mean()
    htf_ma_slow = htf_closes.iloc[-20:].mean()
    
    htf_bias = "BULLISH" if htf_ma_fast > htf_ma_slow else "BEARISH"
    
    htf_range_high = htf_highs.iloc[-20:].max()
    htf_range_low = htf_lows.iloc[-20:].min()
    htf_midpoint = (htf_range_high + htf_range_low) / 2
    
    ltf_current = df_ltf['close'].iat[-1]
    
    is_premium = ltf_current > htf_midpoint
    is_discount = ltf_current < htf_midpoint
    
    ltf_ma_fast = df_ltf['close'].iloc[-10:].mean()
    ltf_ma_slow = df_ltf['close'].iloc[-20:].mean()
    ltf_bias = "BULLISH" if ltf_ma_fast > ltf_ma_slow else "BEARISH"
    
    alignment = (htf_bias == ltf_bias)
    
    optimal_entry = (
        (htf_bias == "BULLISH" and is_discount) or
        (htf_bias == "BEARISH" and is_premium)
    )
    
    strength = 0.5
    if alignment:
        strength += 0.3
    if optimal_entry:
        strength += 0.2
    
    return {
        "bias": htf_bias,
        "alignment": alignment,
        "optimal_entry": optimal_entry,
        "strength": min(strength, 1.0),
        "ltf_location": "PREMIUM" if is_premium else "DISCOUNT",
        "htf_range": (htf_range_low, htf_range_high),
        "htf_midpoint": htf_midpoint
    }


def get_market_narrative(df: pd.DataFrame, timestamp: Optional[datetime] = None, 
                         df_htf: Optional[pd.DataFrame] = None) -> MarketNarrative:
    """
    Retorna narrativa completa de mercado combinando:
    - Liquidez (internal vs external)
    - Killzone ativa
    - HTF bias
    """
    internal_liq = detect_internal_range_liquidity(df)
    external_liq = detect_external_range_liquidity(df)
    killzone = detect_killzone(timestamp)
    htf_context = detect_htf_context(df, df_htf)
    
    if external_liq['strength'] > internal_liq['strength']:
        liquidity_type = "EXTERNAL"
        liquidity_zones = external_liq['zones']
        liquidity_strength = external_liq['strength']
    elif internal_liq['strength'] > 0.3:
        liquidity_type = "INTERNAL"
        liquidity_zones = internal_liq['zones']
        liquidity_strength = internal_liq['strength']
    else:
        liquidity_type = "BALANCED"
        liquidity_zones = internal_liq['zones'] + external_liq['zones']
        liquidity_strength = (internal_liq['strength'] + external_liq['strength']) / 2
    
    overall_strength = (liquidity_strength + killzone['strength'] + htf_context['strength']) / 3
    
    return MarketNarrative(
        liquidity_type=liquidity_type,
        liquidity_zones=liquidity_zones,
        killzone=killzone['zone'] if killzone['active'] else None,
        htf_bias=htf_context['bias'],
        strength=overall_strength,
        meta={
            "killzone_info": killzone,
            "htf_info": htf_context,
            "internal_liq_strength": internal_liq['strength'],
            "external_liq_strength": external_liq['strength']
        }
    )


def get_judas_swing_narrative(df: pd.DataFrame) -> Optional[Dict]:
    """
    Judas Swing Detection: movimento falso no início da sessão
    
    - Primeiro movimento vai em uma direção
    - Reversal rápido capturando stops
    - Setup de alta probabilidade na direção oposta
    """
    if df is None or len(df) < 10:
        return None
    
    first_5_high = df['high'].iloc[:5].max()
    first_5_low = df['low'].iloc[:5].min()
    first_5_close = df['close'].iloc[4]
    
    initial_direction = "UP" if first_5_close > df['open'].iloc[0] else "DOWN"
    
    if initial_direction == "UP":
        swept_high = df['high'].iloc[5:10].max() > first_5_high
        reversed_low = df['close'].iloc[-1] < first_5_low
        
        if swept_high and reversed_low:
            return {
                "detected": True,
                "type": "BEARISH_JUDAS",
                "fake_direction": "UP",
                "real_direction": "DOWN",
                "swept_level": first_5_high,
                "strength": 0.8
            }
    else:
        swept_low = df['low'].iloc[5:10].min() < first_5_low
        reversed_high = df['close'].iloc[-1] > first_5_high
        
        if swept_low and reversed_high:
            return {
                "detected": True,
                "type": "BULLISH_JUDAS",
                "fake_direction": "DOWN",
                "real_direction": "UP",
                "swept_level": first_5_low,
                "strength": 0.8
            }
    
    return None
