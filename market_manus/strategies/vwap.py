"""
VWAP (Volume Weighted Average Price)
Preço médio ponderado pelo volume - identifica valor justo e compra institucional
"""
import pandas as pd
import numpy as np
from market_manus.core.signal import Signal


def vwap_signal(candles: pd.DataFrame, params: dict = None) -> Signal:
    """
    VWAP: Volume Weighted Average Price
    Identifica se preço está acima/abaixo do valor justo institucional
    Excelente confluência com SMC (detecta compra institucional)
    
    Args:
        candles: DataFrame com OHLCV
        params: Parâmetros (session_start_hour para VWAP diário)
    
    Returns:
        Signal com direção e confidence
    """
    params = params or {}
    deviation_threshold = params.get('deviation_threshold', 0.005)  # 0.5% desvio
    
    if len(candles) < 20:
        return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:VWAP"], reasons=["Dados insuficientes"])
    
    # Calcular VWAP
    typical_price = (candles['high'] + candles['low'] + candles['close']) / 3
    vwap = (typical_price * candles['volume']).cumsum() / candles['volume'].cumsum()
    
    # Calcular desvio padrão do VWAP
    variance = ((typical_price - vwap) ** 2 * candles['volume']).cumsum() / candles['volume'].cumsum()
    std_dev = np.sqrt(variance)
    
    current_price = candles['close'].iloc[-1]
    current_vwap = vwap.iloc[-1]
    current_std = std_dev.iloc[-1]
    
    # Calcular distância em % e número de desvios padrão
    distance_pct = (current_price - current_vwap) / current_vwap
    num_std_devs = (current_price - current_vwap) / current_std if current_std > 0 else 0
    
    # Análise de momentum de volume
    recent_volume = candles['volume'].iloc[-5:].mean()
    avg_volume = candles['volume'].mean()
    volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1.0
    
    # BUY: Preço abaixo do VWAP (desconto institucional)
    if distance_pct < -deviation_threshold:
        # Maior confiança se volume está aumentando (institucionais comprando)
        confidence = min(0.5 + abs(num_std_devs) * 0.15, 1.0)
        if volume_ratio > 1.3:  # Volume 30% acima da média
            confidence = min(confidence + 0.2, 1.0)
        
        return Signal(
            action="BUY",
            confidence=confidence,
            reasons=[
                f"Preço {abs(distance_pct):.2%} ABAIXO do VWAP ({current_vwap:.2f})",
                f"Oportunidade institucional: {abs(num_std_devs):.2f} desvios padrão abaixo",
                f"Volume ratio: {volume_ratio:.2f}x"
            ],
            tags=["CLASSIC:VWAP", "CLASSIC:VWAP_DISCOUNT"],
            meta={
                "vwap": current_vwap,
                "price": current_price,
                "distance_pct": distance_pct,
                "num_std_devs": num_std_devs,
                "volume_ratio": volume_ratio
            }
        )
    
    # SELL: Preço acima do VWAP (prêmio institucional)
    elif distance_pct > deviation_threshold:
        confidence = min(0.5 + abs(num_std_devs) * 0.15, 1.0)
        if volume_ratio > 1.3:
            confidence = min(confidence + 0.2, 1.0)
        
        return Signal(
            action="SELL",
            confidence=confidence,
            reasons=[
                f"Preço {distance_pct:.2%} ACIMA do VWAP ({current_vwap:.2f})",
                f"Sobrevalorizado: {num_std_devs:.2f} desvios padrão acima",
                f"Volume ratio: {volume_ratio:.2f}x"
            ],
            tags=["CLASSIC:VWAP", "CLASSIC:VWAP_PREMIUM"],
            meta={
                "vwap": current_vwap,
                "price": current_price,
                "distance_pct": distance_pct,
                "num_std_devs": num_std_devs,
                "volume_ratio": volume_ratio
            }
        )
    
    return Signal(
        action="HOLD",
        confidence=0.0,
        tags=["CLASSIC:VWAP"],
        reasons=[f"Preço próximo ao VWAP (fair value): distância {distance_pct:.2%}"]
    )


def vwap_volume_combo_signal(candles: pd.DataFrame, params: dict = None) -> Signal:
    """
    VWAP + Volume Combo: Detecta desequilíbrio institucional
    Combina VWAP com análise de volume para identificar smart money
    """
    params = params or {}
    
    if len(candles) < 20:
        return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:VWAP_VOL"], reasons=["Dados insuficientes"])
    
    # Obter sinal VWAP base
    vwap_sig = vwap_signal(candles, params)
    
    # Análise de volume avançada
    volumes = candles['volume'].values
    recent_vol = volumes[-10:].mean()
    avg_vol = volumes.mean()
    vol_spike = recent_vol / avg_vol if avg_vol > 0 else 1.0
    
    # Detectar volume clusters (acumulação institucional)
    volume_increasing = volumes[-3] < volumes[-2] < volumes[-1]
    
    # Detectar divergência preço-volume
    price_change = candles['close'].iloc[-1] - candles['close'].iloc[-10]
    price_up = price_change > 0
    
    # Confluência VWAP + Volume
    if vwap_sig.action in ["BUY", "SELL"]:
        boost_confidence = 0.0
        extra_reasons = []
        
        # Volume spike confirma sinal
        if vol_spike > 1.5:
            boost_confidence += 0.15
            extra_reasons.append(f"Volume spike {vol_spike:.2f}x confirma movimento institucional")
        
        # Volume crescente indica continuação
        if volume_increasing:
            boost_confidence += 0.1
            extra_reasons.append("Volume crescente em 3 candles (acumulação)")
        
        # Divergência bullish: preço cai mas volume aumenta (compra institucional disfarçada)
        if vwap_sig.action == "BUY" and not price_up and vol_spike > 1.3:
            boost_confidence += 0.2
            extra_reasons.append("Divergência bullish: preço baixo + volume alto = smart money comprando")
        
        # Divergência bearish: preço sobe mas volume aumenta (distribuição institucional)
        if vwap_sig.action == "SELL" and price_up and vol_spike > 1.3:
            boost_confidence += 0.2
            extra_reasons.append("Divergência bearish: preço alto + volume alto = smart money vendendo")
        
        if boost_confidence > 0:
            new_confidence = min(vwap_sig.confidence + boost_confidence, 1.0)
            return Signal(
                action=vwap_sig.action,
                confidence=new_confidence,
                reasons=vwap_sig.reasons + extra_reasons,
                tags=["CLASSIC:VWAP_VOL", f"CLASSIC:VWAP_VOL_{vwap_sig.action}"],
                meta={
                    **vwap_sig.meta,
                    "vol_spike": vol_spike,
                    "volume_increasing": volume_increasing,
                    "smart_money_detected": boost_confidence >= 0.2
                }
            )
    
    return vwap_sig
