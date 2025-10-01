"""
Smart Money Concepts (SMC) pattern detection with Signal output.
Detectores: BOS, CHoCH, Order Blocks, FVG, Liquidity Sweep, Inducement, Premium/Discount.
"""

import numpy as np
import pandas as pd
from typing import Optional
from market_manus.core.signal import Signal

# ==================== DETECTORES SMC (retornam Signal) ====================

def detect_bos(df: pd.DataFrame, min_displacement: float = 0.001) -> Signal:
    """
    Break of Structure: continuação de tendência após rompimento de swing high/low.
    Confidence baseado em: tamanho do deslocamento e volume relativo.
    """
    if df is None or len(df) < 2:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:BOS"], reasons=["Dados insuficientes"])

    highs = df['high']
    lows = df['low']
    closes = df['close']
    
    last_swing_high = highs.iloc[:-1].max()
    last_swing_low = lows.iloc[:-1].min()
    current_close = closes.iat[-1]
    
    # Calcula displacement (deslocamento) em %
    price_range = last_swing_high - last_swing_low
    if price_range == 0:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:BOS"], reasons=["Range zero"])
    
    # BOS de alta
    if current_close > last_swing_high:
        displacement = (current_close - last_swing_high) / price_range
        confidence = min(0.5 + displacement * 10, 1.0)  # Escala baseada em deslocamento
        
        if displacement >= min_displacement:
            return Signal(
                action="BUY",
                confidence=confidence,
                reasons=[f"BOS de alta: rompeu swing high {last_swing_high:.2f}, displacement {displacement:.3f}"],
                tags=["SMC:BOS", "SMC:BOS_BULL"],
                meta={"swing_high": last_swing_high, "displacement": displacement, "close": current_close}
            )
    
    # BOS de baixa
    if current_close < last_swing_low:
        displacement = (last_swing_low - current_close) / price_range
        confidence = min(0.5 + displacement * 10, 1.0)
        
        if displacement >= min_displacement:
            return Signal(
                action="SELL",
                confidence=confidence,
                reasons=[f"BOS de baixa: rompeu swing low {last_swing_low:.2f}, displacement {displacement:.3f}"],
                tags=["SMC:BOS", "SMC:BOS_BEAR"],
                meta={"swing_low": last_swing_low, "displacement": displacement, "close": current_close}
            )
    
    return Signal(action="HOLD", confidence=0.0, tags=["SMC:BOS"], reasons=["Sem BOS detectado"])


def detect_choch(df: pd.DataFrame) -> Signal:
    """
    Change of Character: inversão quando sequência de topos/fundos muda.
    Requer pelo menos 2 swings na direção original antes do CHoCH.
    """
    if df is None or len(df) < 3:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:CHOCH"], reasons=["Dados insuficientes"])

    highs = df['high']
    lows = df['low']
    closes = df['close']
    
    # Identifica higher highs e lower lows
    highs_idx = [i for i in range(1, len(df)) if closes.iat[i] > highs.iloc[:i].max()]
    lows_idx = [i for i in range(1, len(df)) if closes.iat[i] < lows.iloc[:i].min()]
    
    had_uptrend = len(highs_idx) >= 2  # Pelo menos 2 higher highs
    had_downtrend = len(lows_idx) >= 2  # Pelo menos 2 lower lows
    
    # CHoCH requer inversão: uptrend → downtrend ou downtrend → uptrend
    if had_uptrend and lows_idx and lows_idx[-1] > (highs_idx[-1] if highs_idx else 0):
        # Estava em uptrend, agora fez lower low
        confidence = 0.6 + (len(highs_idx) * 0.1)  # Mais confiança com mais confirmações
        return Signal(
            action="SELL",
            confidence=min(confidence, 1.0),
            reasons=[f"CHoCH: uptrend inverteu para downtrend após {len(highs_idx)} higher highs"],
            tags=["SMC:CHOCH", "SMC:CHOCH_BEARISH"],
            meta={"previous_trend": "UP", "highs_count": len(highs_idx), "lows_count": len(lows_idx)}
        )
    
    if had_downtrend and highs_idx and highs_idx[-1] > (lows_idx[-1] if lows_idx else 0):
        # Estava em downtrend, agora fez higher high
        confidence = 0.6 + (len(lows_idx) * 0.1)
        return Signal(
            action="BUY",
            confidence=min(confidence, 1.0),
            reasons=[f"CHoCH: downtrend inverteu para uptrend após {len(lows_idx)} lower lows"],
            tags=["SMC:CHOCH", "SMC:CHOCH_BULLISH"],
            meta={"previous_trend": "DOWN", "highs_count": len(highs_idx), "lows_count": len(lows_idx)}
        )
    
    return Signal(action="HOLD", confidence=0.0, tags=["SMC:CHOCH"], reasons=["Sem CHoCH detectado"])


def detect_order_blocks(df: pd.DataFrame, min_range: float = 0) -> Signal:
    """
    Order Block: última vela de acumulação/distribuição antes do rompimento.
    Zona preferencial de entrada/stop loss.
    """
    obs = []
    curr_max = df['high'].iat[0]
    curr_min = df['low'].iat[0]

    for i in range(1, len(df)):
        h, l, o, c = df['high'].iat[i], df['low'].iat[i], df['open'].iat[i], df['close'].iat[i]
        prev_h, prev_l, prev_o, prev_c = df['high'].iat[i-1], df['low'].iat[i-1], df['open'].iat[i-1], df['close'].iat[i-1]

        # Bullish OB: BOS confirmado + candle anterior bearish
        if c > curr_max and df['close'].iat[i] > curr_max:
            if prev_c < prev_o and abs(prev_h - prev_l) >= min_range:
                obs.append({"index": i-1, "type": "bullish", "zone": (prev_l, prev_h), "strength": abs(prev_h - prev_l)})
            curr_max = h

        # Bearish OB: BOS confirmado + candle anterior bullish
        if c < curr_min and df['close'].iat[i] < curr_min:
            if prev_c > prev_o and abs(prev_h - prev_l) >= min_range:
                obs.append({"index": i-1, "type": "bearish", "zone": (prev_l, prev_h), "strength": abs(prev_h - prev_l)})
            curr_min = l

    if not obs:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:OB"], reasons=["Nenhum Order Block detectado"])
    
    # Pega o OB mais recente
    last_ob = obs[-1]
    ob_type = last_ob["type"]
    zone = last_ob["zone"]
    strength = last_ob["strength"]
    
    # Confidence baseado na força (tamanho) do OB
    avg_range = df['high'].sub(df['low']).mean()
    confidence = min(0.5 + (strength / avg_range) * 0.3, 1.0) if avg_range > 0 else 0.5
    
    action = "BUY" if ob_type == "bullish" else "SELL"
    return Signal(
        action=action,
        confidence=confidence,
        reasons=[f"Order Block {ob_type} detectado na zona {zone[0]:.2f}-{zone[1]:.2f}, strength {strength:.4f}"],
        tags=["SMC:OB", f"SMC:OB_{ob_type.upper()}"],
        meta={"ob_type": ob_type, "zone_low": zone[0], "zone_high": zone[1], "strength": strength, "index": last_ob["index"]}
    )


def detect_fvg(df: pd.DataFrame) -> Signal:
    """
    Fair Value Gap: gap entre corpos/sombras de 3 velas consecutivas.
    Zona de reprecificação (imbalance).
    """
    gaps = []
    if df is None or len(df) < 3:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:FVG"], reasons=["Dados insuficientes"])

    highs = df['high']
    lows = df['low']

    for i in range(1, len(df)):
        prev_h = highs.iat[i-1]
        prev_l = lows.iat[i-1]
        curr_h = highs.iat[i]
        curr_l = lows.iat[i]

        # Gap de alta: mínima atual > máxima anterior
        if curr_l > prev_h:
            gap_size = curr_l - prev_h
            gaps.append({"type": "bullish", "gap": (prev_h, curr_l), "size": gap_size, "index": i})

        # Gap de baixa: máxima atual < mínima anterior
        elif curr_h < prev_l:
            gap_size = prev_l - curr_h
            gaps.append({"type": "bearish", "gap": (curr_h, prev_l), "size": gap_size, "index": i})

    if not gaps:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:FVG"], reasons=["Nenhum FVG detectado"])
    
    # Pega o FVG mais recente
    last_fvg = gaps[-1]
    fvg_type = last_fvg["type"]
    gap = last_fvg["gap"]
    size = last_fvg["size"]
    
    # Confidence baseado no tamanho do gap
    avg_range = df['high'].sub(df['low']).mean()
    confidence = min(0.4 + (size / avg_range) * 0.4, 1.0) if avg_range > 0 else 0.4
    
    action = "BUY" if fvg_type == "bullish" else "SELL"
    return Signal(
        action=action,
        confidence=confidence,
        reasons=[f"FVG {fvg_type} detectado: gap {gap[0]:.2f}-{gap[1]:.2f}, tamanho {size:.4f}"],
        tags=["SMC:FVG", f"SMC:FVG_{fvg_type.upper()}"],
        meta={"fvg_type": fvg_type, "gap_low": gap[0], "gap_high": gap[1], "size": size, "index": last_fvg["index"]}
    )


def detect_liquidity_zones(df: pd.DataFrame, min_touches: int = 2, tol: float = 1e-5) -> dict:
    """Detecta zonas de liquidez (níveis tocados múltiplas vezes)"""
    counts = {}
    for price in list(df['high']) + list(df['low']):
        counts[price] = counts.get(price, 0) + 1

    zones = {}
    for price, cnt in counts.items():
        found = next((z for z in zones if abs(z - price) <= tol), None)
        if found:
            zones[found] += cnt
        else:
            zones[price] = cnt

    return {z: c for z, c in zones.items() if c >= min_touches}


def detect_liquidity_sweep(df: pd.DataFrame, body_ratio: float = 0.5, tol: float = 1e-5) -> Signal:
    """
    Liquidity Sweep: pavio que varre máxima/mínima e fecha de volta.
    Sinaliza armadilha (retail trap) e possível reversão.
    """
    zones = list(detect_liquidity_zones(df).keys())
    if not zones:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:SWEEP"], reasons=["Sem zonas de liquidez"])
    
    sweeps = []
    highs = df['high']
    lows = df['low']
    closes = df['close']
    opens = df['open']
    
    for i in range(1, len(df)):
        h, l, o, c = highs.iat[i], lows.iat[i], opens.iat[i], closes.iat[i]
        rng = h - l
        body = abs(c - o)
        
        if rng == 0:
            continue
        if body / rng > body_ratio:
            continue  # Exige sombra grande
        
        for z in zones:
            # Sweep buy-side: fura acima e fecha abaixo
            if h > z + tol and c < z - tol:
                wick_size = h - max(o, c)
                sweeps.append({"index": i, "level": z, "direction": "up", "type": "bearish", "wick_size": wick_size})
            
            # Sweep sell-side: fura abaixo e fecha acima
            if l < z - tol and c > z + tol:
                wick_size = min(o, c) - l
                sweeps.append({"index": i, "level": z, "direction": "down", "type": "bullish", "wick_size": wick_size})
    
    if not sweeps:
        return Signal(action="HOLD", confidence=0.0, tags=["SMC:SWEEP"], reasons=["Nenhum sweep detectado"])
    
    # Pega o sweep mais recente
    last_sweep = sweeps[-1]
    sweep_type = last_sweep["type"]
    level = last_sweep["level"]
    wick_size = last_sweep["wick_size"]
    
    # Confidence baseado no tamanho do pavio
    avg_range = df['high'].sub(df['low']).mean()
    confidence = min(0.5 + (wick_size / avg_range) * 0.3, 1.0) if avg_range > 0 else 0.5
    
    action = "BUY" if sweep_type == "bullish" else "SELL"
    return Signal(
        action=action,
        confidence=confidence,
        reasons=[f"Liquidity sweep {sweep_type}: varreu nível {level:.2f}, pavio {wick_size:.4f}"],
        tags=["SMC:SWEEP", f"SMC:SWEEP_{sweep_type.upper()}"],
        meta={"sweep_type": sweep_type, "level": level, "wick_size": wick_size, "direction": last_sweep["direction"]}
    )


# ==================== SMCDetector CLASS ====================

class SMCDetector:
    """
    Detector unificado de Smart Money Concepts.
    Gera sinais de BOS, CHoCH, Order Blocks, FVG e Liquidity Sweeps.
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.min_displacement = self.config.get('min_displacement', 0.001)
        self.min_ob_range = self.config.get('min_ob_range', 0)
        self.body_ratio = self.config.get('body_ratio', 0.5)
    
    def generate_signals(self, candles: pd.DataFrame, ctx: dict = None) -> list[Signal]:
        """
        Gera todos os sinais SMC para o conjunto de candles.
        
        Args:
            candles: DataFrame com OHLCV
            ctx: Contexto adicional (símbolo, timeframe, etc)
        
        Returns:
            Lista de Signal de todos os detectores
        """
        signals = []
        
        # BOS
        bos_signal = detect_bos(candles, self.min_displacement)
        if bos_signal.action != "HOLD":
            signals.append(bos_signal)
        
        # CHoCH
        choch_signal = detect_choch(candles)
        if choch_signal.action != "HOLD":
            signals.append(choch_signal)
        
        # Order Blocks
        ob_signal = detect_order_blocks(candles, self.min_ob_range)
        if ob_signal.action != "HOLD":
            signals.append(ob_signal)
        
        # FVG
        fvg_signal = detect_fvg(candles)
        if fvg_signal.action != "HOLD":
            signals.append(fvg_signal)
        
        # Liquidity Sweep
        sweep_signal = detect_liquidity_sweep(candles, self.body_ratio)
        if sweep_signal.action != "HOLD":
            signals.append(sweep_signal)
        
        return signals


# ==================== CONFLUENCE ENGINE ====================

class ConfluenceEngine:
    """
    Motor de confluência: combina sinais SMC + Classic com score ponderado.
    Aplica filtros de regime (ADX, ATR, volatilidade) e decide BUY/SELL/HOLD.
    """
    
    def __init__(self, detectors: dict, weights: dict, regime_cfg: dict):
        """
        Args:
            detectors: Dict {nome: callable} de detectores
            weights: Dict {nome: peso} para cada detector
            regime_cfg: Config de regime (adx_min, atr_min, bb_width_min)
        """
        self.detectors = detectors
        self.weights = weights
        self.regime_cfg = regime_cfg
        self.buy_threshold = regime_cfg.get('buy_threshold', 0.5)
        self.sell_threshold = regime_cfg.get('sell_threshold', -0.5)
        self.conflict_penalty = regime_cfg.get('conflict_penalty', 0.3)
    
    def _calculate_regime_filters(self, candles: pd.DataFrame) -> dict:
        """Calcula indicadores de regime: ADX, ATR, BB width"""
        from market_manus.strategies.classic_analysis import calculate_adx, calculate_atr, calculate_bollinger_bands
        
        regime = {}
        
        try:
            # ADX
            adx, plus_di, minus_di = calculate_adx(candles, period=14)
            regime['adx'] = adx.iloc[-1] if len(adx) > 0 else 0
            regime['plus_di'] = plus_di.iloc[-1] if len(plus_di) > 0 else 0
            regime['minus_di'] = minus_di.iloc[-1] if len(minus_di) > 0 else 0
            
            # ATR
            atr = calculate_atr(candles, period=14)
            regime['atr'] = atr.iloc[-1] if len(atr) > 0 else 0
            
            # Bollinger width
            upper, middle, lower = calculate_bollinger_bands(candles['close'], period=20, std_dev=2)
            if len(middle) > 0 and middle.iloc[-1] > 0:
                regime['bb_width'] = (upper.iloc[-1] - lower.iloc[-1]) / middle.iloc[-1]
            else:
                regime['bb_width'] = 0
        except Exception as e:
            print(f"Erro ao calcular filtros de regime: {e}")
            regime = {'adx': 0, 'atr': 0, 'bb_width': 0, 'plus_di': 0, 'minus_di': 0}
        
        return regime
    
    def evaluate(self, candles: pd.DataFrame, ctx: dict) -> Signal:
        """
        Avalia todos os detectores e retorna decisão final de confluência.
        Aplica filtros de regime (ADX, ATR, BB width) para validar sinais.
        
        Returns:
            Signal final com score agregado e razões de suporte
        """
        # Calcula filtros de regime
        regime = self._calculate_regime_filters(candles)
        
        # Extrai thresholds de regime
        adx_min = self.regime_cfg.get('adx_min', 0)
        adx_max = self.regime_cfg.get('adx_max', 100)
        atr_min = self.regime_cfg.get('atr_min', 0)
        bb_width_min = self.regime_cfg.get('bb_width_min', 0)
        
        # Valida regime antes de processar sinais
        regime_valid = True
        regime_reasons = []
        
        if regime['adx'] < adx_min:
            regime_valid = False
            regime_reasons.append(f"ADX muito baixo: {regime['adx']:.1f} < {adx_min} (tendência fraca)")
        
        if regime['adx'] > adx_max:
            regime_reasons.append(f"ADX muito alto: {regime['adx']:.1f} > {adx_max} (mercado sobrecomprado)")
        
        if regime['atr'] < atr_min:
            regime_valid = False
            regime_reasons.append(f"ATR muito baixo: {regime['atr']:.4f} < {atr_min} (volatilidade insuficiente)")
        
        if regime['bb_width'] < bb_width_min:
            regime_valid = False
            regime_reasons.append(f"BB width muito baixo: {regime['bb_width']:.4f} < {bb_width_min} (mercado travado)")
        
        if not regime_valid:
            return Signal(
                action="HOLD",
                confidence=0.0,
                reasons=["Regime desfavorável"] + regime_reasons,
                tags=["CONFLUENCE:REGIME_FILTER"],
                meta={"regime": regime}
            )
        
        all_signals = []
        
        # Chama todos os detectores
        for name, detector_fn in self.detectors.items():
            try:
                signal = detector_fn()
                if signal and signal.action != "HOLD":
                    all_signals.append((name, signal))
            except Exception as e:
                print(f"Erro em detector {name}: {e}")
        
        if not all_signals:
            return Signal(
                action="HOLD",
                confidence=0.0,
                reasons=["Nenhum sinal detectado"],
                tags=["CONFLUENCE:HOLD"]
            )
        
        # Calcula score ponderado
        score = 0.0
        buy_count = 0
        sell_count = 0
        reasons = []
        tags = []
        
        for name, signal in all_signals:
            weight = self.weights.get(name, 1.0)
            direction = signal.get_direction()
            contribution = weight * signal.confidence * direction
            score += contribution
            
            if direction > 0:
                buy_count += 1
            elif direction < 0:
                sell_count += 1
            
            reasons.append(f"{name}: {signal.action} (conf={signal.confidence:.2f}, contrib={contribution:+.3f})")
            tags.extend(signal.tags)
        
        # Penaliza conflitos
        if buy_count > 0 and sell_count > 0:
            conflict = min(buy_count, sell_count)
            penalty = conflict * self.conflict_penalty
            score = score * (1 - penalty)
            reasons.append(f"Conflito detectado: {buy_count} BUY vs {sell_count} SELL, penalidade {penalty:.2f}")
        
        # Decisão final
        if score >= self.buy_threshold:
            action = "BUY"
            confidence = min(abs(score), 1.0)
        elif score <= self.sell_threshold:
            action = "SELL"
            confidence = min(abs(score), 1.0)
        else:
            action = "HOLD"
            confidence = 0.0
        
        return Signal(
            action=action,
            confidence=confidence,
            reasons=reasons,
            tags=list(set(tags)) + [f"CONFLUENCE:{action}"],
            meta={
                "score": score,
                "buy_count": buy_count,
                "sell_count": sell_count,
                "signal_count": len(all_signals),
                "ctx": ctx
            }
        )


# ==================== FUNÇÃO PÚBLICA DE CONFLUÊNCIA ====================

def confluence_decision(candles: pd.DataFrame, symbol: str, timeframe: str, config: dict) -> Signal:
    """
    Função principal de decisão de confluência.
    Orquestra SMCDetector + detectores clássicos via ConfluenceEngine.
    
    Args:
        candles: DataFrame OHLCV
        symbol: Símbolo (ex: "BTCUSDT")
        timeframe: Timeframe (ex: "5m")
        config: Configuração completa (pesos, regime, toggles)
    
    Returns:
        Signal final de confluência
    """
    ctx = {"symbol": symbol, "timeframe": timeframe}
    
    # Inicializa SMC
    smc_config = config.get("smc", {})
    smc = SMCDetector(smc_config)
    
    # Monta dict de detectores (SMC primeiro)
    detectors = {}
    
    if config.get("use_smc", True):
        # Adiciona detectores SMC individuais
        detectors["SMC:BOS"] = lambda: detect_bos(candles, smc.min_displacement)
        detectors["SMC:CHoCH"] = lambda: detect_choch(candles)
        detectors["SMC:OB"] = lambda: detect_order_blocks(candles, smc.min_ob_range)
        detectors["SMC:FVG"] = lambda: detect_fvg(candles)
        detectors["SMC:SWEEP"] = lambda: detect_liquidity_sweep(candles, smc.body_ratio)
    
    # Adiciona detectores clássicos
    if config.get("use_classic", True):
        from market_manus.strategies.classic_analysis import (
            ema_crossover_signal, macd_signal, rsi_signal, bollinger_signal,
            adx_signal, stochastic_signal, fibonacci_signal
        )
        
        detectors["CLASSIC:EMA"] = lambda: ema_crossover_signal(candles, config.get("ema", {}))
        detectors["CLASSIC:MACD"] = lambda: macd_signal(candles, config.get("macd", {}))
        detectors["CLASSIC:RSI"] = lambda: rsi_signal(candles, config.get("rsi", {}))
        detectors["CLASSIC:BB"] = lambda: bollinger_signal(candles, config.get("bb", {}))
        detectors["CLASSIC:ADX"] = lambda: adx_signal(candles, config.get("adx", {}))
        detectors["CLASSIC:STOCH"] = lambda: stochastic_signal(candles, config.get("stoch", {}))
        detectors["CLASSIC:FIB"] = lambda: fibonacci_signal(candles, config.get("fib", {}))
    
    # Monta ConfluenceEngine
    weights = config.get("weights", {})
    regime_cfg = config.get("regime", {})
    
    engine = ConfluenceEngine(detectors, weights, regime_cfg)
    
    # Avalia e retorna decisão final
    return engine.evaluate(candles, ctx)
