def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def fng_to_score(value_0_100: float) -> float:
    return clamp01(value_0_100/100.0)

def pct_to_score(pct: float) -> float:
    return clamp01((pct + 10.0)/20.0)

def volume_to_score(vol_usd: float) -> float:
    import math
    return clamp01(min(1.0, math.log10(max(1.0, vol_usd))/10.0))
