"""
Parabolic SAR (Stop and Reverse)
Seguidor de tendência baseado em aceleração e reversão
"""
import pandas as pd
from market_manus.core.signal import Signal


def parabolic_sar_signal(candles: pd.DataFrame, params: dict = None) -> Signal:
    """
    Parabolic SAR: Seguidor de tendência com reversões baseadas em aceleração
    Excelente confluência com CHoCH e BOS
    
    Args:
        candles: DataFrame com OHLC
        params: Parâmetros (af_start, af_step, af_max)
    
    Returns:
        Signal com direção e confidence
    """
    params = params or {}
    af_start = params.get('af_start', 0.02)
    af_step = params.get('af_step', 0.02)
    af_max = params.get('af_max', 0.2)
    
    if len(candles) < 5:
        return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:PSAR"], reasons=["Dados insuficientes"])
    
    high = candles['high'].values
    low = candles['low'].values
    close = candles['close'].values
    
    # Calcular Parabolic SAR
    psar = []
    bull = True
    af = af_start
    ep = high[0]
    hp = high[0]
    lp = low[0]
    
    for i in range(len(candles)):
        if i == 0:
            psar.append(low[i])
            continue
            
        psar_value = psar[-1] + af * (ep - psar[-1])
        
        # Reversão de bullish para bearish
        if bull:
            psar_value = min(psar_value, low[i-1])
            if i > 1:
                psar_value = min(psar_value, low[i-2])
                
            if low[i] < psar_value:
                bull = False
                psar_value = hp
                ep = lp
                af = af_start
        
        # Reversão de bearish para bullish
        else:
            psar_value = max(psar_value, high[i-1])
            if i > 1:
                psar_value = max(psar_value, high[i-2])
                
            if high[i] > psar_value:
                bull = True
                psar_value = lp
                ep = hp
                af = af_start
        
        psar.append(psar_value)
        
        # Atualizar extreme point e acceleration factor
        if bull:
            if high[i] > ep:
                ep = high[i]
                af = min(af + af_step, af_max)
            hp = max(hp, high[i])
        else:
            if low[i] < ep:
                ep = low[i]
                af = min(af + af_step, af_max)
            lp = min(lp, low[i])
    
    # Analisar sinal atual
    current_price = close[-1]
    current_psar = psar[-1]
    prev_psar = psar[-2] if len(psar) > 1 else current_psar
    
    # Distância do preço ao PSAR (confiança)
    distance_pct = abs(current_price - current_psar) / current_price
    
    # BUY: PSAR abaixo do preço (tendência de alta)
    if current_psar < current_price:
        # Detectar reversão recente (maior confiança)
        just_reversed = prev_psar > close[-2]
        confidence = min(0.6 + distance_pct * 20, 1.0)
        if just_reversed:
            confidence = min(confidence + 0.2, 1.0)
        
        return Signal(
            action="BUY",
            confidence=confidence,
            reasons=[f"PSAR bullish: SAR {current_psar:.2f} abaixo do preço {current_price:.2f}, tendência de alta confirmada"],
            tags=["CLASSIC:PSAR", "CLASSIC:PSAR_BULL"],
            meta={"psar": current_psar, "price": current_price, "distance_pct": distance_pct, "reversed": just_reversed}
        )
    
    # SELL: PSAR acima do preço (tendência de baixa)
    elif current_psar > current_price:
        just_reversed = prev_psar < close[-2]
        confidence = min(0.6 + distance_pct * 20, 1.0)
        if just_reversed:
            confidence = min(confidence + 0.2, 1.0)
        
        return Signal(
            action="SELL",
            confidence=confidence,
            reasons=[f"PSAR bearish: SAR {current_psar:.2f} acima do preço {current_price:.2f}, tendência de baixa confirmada"],
            tags=["CLASSIC:PSAR", "CLASSIC:PSAR_BEAR"],
            meta={"psar": current_psar, "price": current_price, "distance_pct": distance_pct, "reversed": just_reversed}
        )
    
    return Signal(action="HOLD", confidence=0.0, tags=["CLASSIC:PSAR"], reasons=["Preço em cima do PSAR"])
