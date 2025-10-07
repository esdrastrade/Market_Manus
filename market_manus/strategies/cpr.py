"""
CPR (Central Pivot Range)
Define zonas de suporte/resistência intraday
Útil para scalping e confluência com BOS e Order Blocks
"""
import pandas as pd
from market_manus.core.signal import Signal


def calculate_pivot_points(prev_high: float, prev_low: float, prev_close: float) -> dict:
    """Calcula Pivot Points clássicos"""
    pivot = (prev_high + prev_low + prev_close) / 3
    
    return {
        'pivot': pivot,
        'bc': (prev_high + prev_low) / 2,  # Bottom Central
        'tc': (pivot - (prev_high + prev_low) / 2) + pivot,  # Top Central
        'r1': (2 * pivot) - prev_low,
        'r2': pivot + (prev_high - prev_low),
        'r3': prev_high + 2 * (pivot - prev_low),
        's1': (2 * pivot) - prev_high,
        's2': pivot - (prev_high - prev_low),
        's3': prev_low - 2 * (prev_high - pivot)
    }


def cpr_signal(candles: pd.DataFrame, params: dict = None) -> Signal:
    """
    CPR (Central Pivot Range): Zonas de suporte/resistência intraday
    Identifica zonas de consolidação e breakouts
    
    Args:
        candles: DataFrame com OHLC
        params: Parâmetros (sensitivity)
    
    Returns:
        Signal com direção e confidence
    """
    params = params or {}
    sensitivity = params.get('sensitivity', 0.002)  # 0.2% tolerância
    
    if len(candles) < 2:
        return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:CPR"], reasons=["Dados insuficientes"])
    
    # Usar o candle anterior como referência para calcular pivots
    prev_candle = candles.iloc[-2]
    prev_high = prev_candle['high']
    prev_low = prev_candle['low']
    prev_close = prev_candle['close']
    
    pivots = calculate_pivot_points(prev_high, prev_low, prev_close)
    
    current_price = candles['close'].iloc[-1]
    current_high = candles['high'].iloc[-1]
    current_low = candles['low'].iloc[-1]
    
    # Calcular CPR width (distância entre TC e BC)
    cpr_width = pivots['tc'] - pivots['bc']
    cpr_width_pct = cpr_width / pivots['pivot']
    
    # Classificar CPR
    if cpr_width_pct < 0.001:  # < 0.1%
        cpr_type = "Narrow CPR (alta volatilidade esperada)"
        volatility_boost = 0.2
    elif cpr_width_pct > 0.005:  # > 0.5%
        cpr_type = "Wide CPR (consolidação)"
        volatility_boost = -0.1
    else:
        cpr_type = "Normal CPR"
        volatility_boost = 0.0
    
    # Detectar posição do preço em relação ao CPR
    tolerance = current_price * sensitivity
    
    # BREAKOUT ACIMA do CPR
    if current_price > pivots['tc'] + tolerance:
        # Verificar força do breakout
        breakout_strength = (current_price - pivots['tc']) / cpr_width if cpr_width > 0 else 1.0
        confidence = min(0.6 + min(breakout_strength, 1.0) * 0.3 + volatility_boost, 1.0)
        
        # Níveis de resistência como targets
        next_target = pivots['r1']
        if current_price > pivots['r1']:
            next_target = pivots['r2']
        if current_price > pivots['r2']:
            next_target = pivots['r3']
        
        return Signal(
            action="BUY",
            confidence=confidence,
            reasons=[
                f"Breakout ACIMA do CPR (TC: {pivots['tc']:.2f})",
                f"{cpr_type} - força do breakout: {breakout_strength:.2f}",
                f"Próximo target: R{1 if next_target == pivots['r1'] else 2 if next_target == pivots['r2'] else 3} = {next_target:.2f}"
            ],
            tags=["CLASSIC:CPR", "CLASSIC:CPR_BREAKOUT_BULL"],
            meta={
                "pivot": pivots['pivot'],
                "tc": pivots['tc'],
                "bc": pivots['bc'],
                "cpr_width_pct": cpr_width_pct,
                "breakout_strength": breakout_strength,
                "next_resistance": next_target,
                "all_pivots": pivots
            }
        )
    
    # BREAKOUT ABAIXO do CPR
    elif current_price < pivots['bc'] - tolerance:
        breakout_strength = (pivots['bc'] - current_price) / cpr_width if cpr_width > 0 else 1.0
        confidence = min(0.6 + min(breakout_strength, 1.0) * 0.3 + volatility_boost, 1.0)
        
        # Níveis de suporte como targets
        next_target = pivots['s1']
        if current_price < pivots['s1']:
            next_target = pivots['s2']
        if current_price < pivots['s2']:
            next_target = pivots['s3']
        
        return Signal(
            action="SELL",
            confidence=confidence,
            reasons=[
                f"Breakout ABAIXO do CPR (BC: {pivots['bc']:.2f})",
                f"{cpr_type} - força do breakout: {breakout_strength:.2f}",
                f"Próximo target: S{1 if next_target == pivots['s1'] else 2 if next_target == pivots['s2'] else 3} = {next_target:.2f}"
            ],
            tags=["CLASSIC:CPR", "CLASSIC:CPR_BREAKOUT_BEAR"],
            meta={
                "pivot": pivots['pivot'],
                "tc": pivots['tc'],
                "bc": pivots['bc'],
                "cpr_width_pct": cpr_width_pct,
                "breakout_strength": breakout_strength,
                "next_support": next_target,
                "all_pivots": pivots
            }
        )
    
    # DENTRO DO CPR (zona de consolidação)
    elif pivots['bc'] <= current_price <= pivots['tc']:
        return Signal(
            action="HOLD",
            confidence=0.0,
            tags=["CLASSIC:CPR", "CLASSIC:CPR_INSIDE"],
            reasons=[
                f"Preço DENTRO do CPR ({pivots['bc']:.2f} - {pivots['tc']:.2f})",
                f"{cpr_type}",
                "Aguardando breakout para sinal claro"
            ],
            meta={
                "pivot": pivots['pivot'],
                "tc": pivots['tc'],
                "bc": pivots['bc'],
                "cpr_width_pct": cpr_width_pct,
                "all_pivots": pivots
            }
        )
    
    return Signal(
        action="HOLD",
        confidence=0.0,
        tags=["CLASSIC:CPR"],
        reasons=["Preço próximo ao CPR, sem sinal claro"]
    )
