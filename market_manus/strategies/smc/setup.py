"""
ICT Setup Module - Pilar 4 do ICT Framework

Constrói setups completos combinando Market Structure + Context + Narrative:
- Entry: ponto preciso de entrada baseado em confluência
- Stop-Loss: calculado em zonas seguras (abaixo OB, acima sweep)
- Target: níveis de saída com Risk:Reward mínimo
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Literal
from dataclasses import dataclass
from market_manus.core.signal import Signal
from market_manus.strategies.smc.market_structure import MarketStructureState
from market_manus.strategies.smc.context import MarketContext
from market_manus.strategies.smc.narrative import MarketNarrative


@dataclass
class ICTSetup:
    """Setup completo ICT"""
    entry_price: float
    stop_loss: float
    target: float
    direction: Literal["BUY", "SELL"]
    risk_reward: float
    confidence: float
    setup_type: str  # Ex: "CHoCH_OB_SWEEP", "BOS_FVG_ENTRY"
    components: List[str]
    meta: Dict
    
    def to_signal(self) -> Signal:
        """Converte setup para Signal"""
        return Signal(
            action=self.direction,
            confidence=self.confidence,
            reasons=[
                f"Setup: {self.setup_type}",
                f"Entry: ${self.entry_price:.2f}",
                f"SL: ${self.stop_loss:.2f}",
                f"TP: ${self.target:.2f}",
                f"R:R = 1:{self.risk_reward:.1f}"
            ],
            tags=["ICT:SETUP", f"ICT:{self.setup_type}", f"ICT:RR_{int(self.risk_reward)}"],
            meta={
                "entry": self.entry_price,
                "stop_loss": self.stop_loss,
                "target": self.target,
                "risk_reward": self.risk_reward,
                "components": self.components,
                **self.meta
            }
        )


class ICTSetupBuilder:
    """Construtor de setups ICT profissionais"""
    
    def __init__(self, min_rr: float = 2.0):
        self.min_rr = min_rr
    
    def build_choch_ob_sweep_setup(self, df: pd.DataFrame, structure_state: MarketStructureState,
                                    context: MarketContext, narrative: MarketNarrative) -> Optional[ICTSetup]:
        """
        Setup: CHoCH + Order Block + Liquidity Sweep
        
        Critérios:
        1. CHoCH confirmado (tendência revertida)
        2. Order Block FRESH disponível
        3. Liquidity Sweep recente
        4. Context favorável (não consolidação)
        5. Killzone ativo (opcional, mas aumenta conf)
        """
        if structure_state.last_choch is None:
            return None
        
        choch = structure_state.last_choch
        fresh_obs = [ob for ob in structure_state.order_blocks if ob['status'] == 'FRESH']
        
        if not fresh_obs:
            return None
        
        last_ob = fresh_obs[-1]
        
        if context.regime == "CONSOLIDATION":
            return None
        
        choch_type = choch['type']
        ob_type = last_ob['type']
        
        if choch_type == "BULLISH" and ob_type == "bullish":
            entry_price = last_ob['zone'][1]
            stop_loss = last_ob['zone'][0] - (last_ob['zone'][1] - last_ob['zone'][0]) * 0.1
            
            risk = entry_price - stop_loss
            target = entry_price + (risk * self.min_rr)
            
            base_confidence = 0.7
            
            if narrative.killzone:
                base_confidence += 0.1
            if narrative.htf_bias == "BULLISH":
                base_confidence += 0.1
            if context.regime == "IMPULSE":
                base_confidence += 0.05
            
            return ICTSetup(
                entry_price=entry_price,
                stop_loss=stop_loss,
                target=target,
                direction="BUY",
                risk_reward=self.min_rr,
                confidence=min(base_confidence, 1.0),
                setup_type="CHoCH_OB_SWEEP_BULL",
                components=["CHoCH_BULLISH", "ORDER_BLOCK_FRESH", f"CONTEXT_{context.regime}"],
                meta={
                    "choch_data": choch,
                    "ob_data": last_ob,
                    "killzone": narrative.killzone,
                    "htf_bias": narrative.htf_bias
                }
            )
        
        elif choch_type == "BEARISH" and ob_type == "bearish":
            entry_price = last_ob['zone'][0]
            stop_loss = last_ob['zone'][1] + (last_ob['zone'][1] - last_ob['zone'][0]) * 0.1
            
            risk = stop_loss - entry_price
            target = entry_price - (risk * self.min_rr)
            
            base_confidence = 0.7
            
            if narrative.killzone:
                base_confidence += 0.1
            if narrative.htf_bias == "BEARISH":
                base_confidence += 0.1
            if context.regime == "IMPULSE":
                base_confidence += 0.05
            
            return ICTSetup(
                entry_price=entry_price,
                stop_loss=stop_loss,
                target=target,
                direction="SELL",
                risk_reward=self.min_rr,
                confidence=min(base_confidence, 1.0),
                setup_type="CHoCH_OB_SWEEP_BEAR",
                components=["CHoCH_BEARISH", "ORDER_BLOCK_FRESH", f"CONTEXT_{context.regime}"],
                meta={
                    "choch_data": choch,
                    "ob_data": last_ob,
                    "killzone": narrative.killzone,
                    "htf_bias": narrative.htf_bias
                }
            )
        
        return None
    
    def build_bos_fvg_setup(self, df: pd.DataFrame, structure_state: MarketStructureState,
                            context: MarketContext, narrative: MarketNarrative) -> Optional[ICTSetup]:
        """
        Setup: BOS + Fair Value Gap + Retest
        
        Critérios:
        1. BOS confirmado (continuação)
        2. FVG presente no contexto
        3. Preço retestando FVG
        4. Impulso confirmado
        """
        if structure_state.last_bos is None or not context.fvg_present:
            return None
        
        bos = structure_state.last_bos
        
        if context.regime != "IMPULSE":
            return None
        
        fvg_zone = context.meta.get('fvg_zone')
        if not fvg_zone:
            return None
        
        current_price = df['close'].iat[-1]
        fvg_low, fvg_high = fvg_zone
        
        is_retesting = fvg_low <= current_price <= fvg_high
        
        if not is_retesting:
            return None
        
        if bos['type'] == "BULLISH":
            entry_price = (fvg_low + fvg_high) / 2
            stop_loss = fvg_low - (fvg_high - fvg_low) * 0.2
            
            risk = entry_price - stop_loss
            target = entry_price + (risk * self.min_rr)
            
            base_confidence = 0.75
            
            if narrative.htf_bias == "BULLISH":
                base_confidence += 0.15
            if narrative.liquidity_type == "EXTERNAL":
                base_confidence += 0.05
            
            return ICTSetup(
                entry_price=entry_price,
                stop_loss=stop_loss,
                target=target,
                direction="BUY",
                risk_reward=self.min_rr,
                confidence=min(base_confidence, 1.0),
                setup_type="BOS_FVG_RETEST_BULL",
                components=["BOS_BULLISH", "FVG_RETEST", "IMPULSE_CONTEXT"],
                meta={
                    "bos_data": bos,
                    "fvg_zone": fvg_zone,
                    "htf_bias": narrative.htf_bias
                }
            )
        
        elif bos['type'] == "BEARISH":
            entry_price = (fvg_low + fvg_high) / 2
            stop_loss = fvg_high + (fvg_high - fvg_low) * 0.2
            
            risk = stop_loss - entry_price
            target = entry_price - (risk * self.min_rr)
            
            base_confidence = 0.75
            
            if narrative.htf_bias == "BEARISH":
                base_confidence += 0.15
            if narrative.liquidity_type == "EXTERNAL":
                base_confidence += 0.05
            
            return ICTSetup(
                entry_price=entry_price,
                stop_loss=stop_loss,
                target=target,
                direction="SELL",
                risk_reward=self.min_rr,
                confidence=min(base_confidence, 1.0),
                setup_type="BOS_FVG_RETEST_BEAR",
                components=["BOS_BEARISH", "FVG_RETEST", "IMPULSE_CONTEXT"],
                meta={
                    "bos_data": bos,
                    "fvg_zone": fvg_zone,
                    "htf_bias": narrative.htf_bias
                }
            )
        
        return None
    
    def build_sweep_ob_entry_setup(self, df: pd.DataFrame, structure_state: MarketStructureState,
                                    context: MarketContext, narrative: MarketNarrative) -> Optional[ICTSetup]:
        """
        Setup: Liquidity Sweep + Order Block Entry
        
        Critérios:
        1. Sweep de liquidez recente
        2. Order Block alinhado com sweep
        3. Entry model (engulfing/rejection candle)
        """
        fresh_obs = [ob for ob in structure_state.order_blocks if ob['status'] == 'FRESH']
        
        if not fresh_obs:
            return None
        
        if narrative.liquidity_type != "EXTERNAL":
            return None
        
        last_ob = fresh_obs[-1]
        
        current_low = df['low'].iloc[-3:].min()
        current_high = df['high'].iloc[-3:].max()
        
        sweep_detected = False
        sweep_type = None
        
        for liq_zone in narrative.liquidity_zones:
            if liq_zone['location'] == 'EXTERNAL_LOW' and current_low <= liq_zone['level']:
                sweep_detected = True
                sweep_type = "BULLISH"
                break
            elif liq_zone['location'] == 'EXTERNAL_HIGH' and current_high >= liq_zone['level']:
                sweep_detected = True
                sweep_type = "BEARISH"
                break
        
        if not sweep_detected:
            return None
        
        if sweep_type == "BULLISH" and last_ob['type'] == "bullish":
            entry_price = last_ob['zone'][1]
            stop_loss = last_ob['zone'][0] - (last_ob['zone'][1] - last_ob['zone'][0]) * 0.15
            
            risk = entry_price - stop_loss
            target = entry_price + (risk * self.min_rr)
            
            base_confidence = 0.8
            
            if narrative.killzone:
                base_confidence += 0.1
            
            return ICTSetup(
                entry_price=entry_price,
                stop_loss=stop_loss,
                target=target,
                direction="BUY",
                risk_reward=self.min_rr,
                confidence=min(base_confidence, 1.0),
                setup_type="SWEEP_OB_ENTRY_BULL",
                components=["LIQUIDITY_SWEEP", "ORDER_BLOCK_FRESH", "EXTERNAL_LIQUIDITY"],
                meta={
                    "ob_data": last_ob,
                    "sweep_type": sweep_type,
                    "liquidity_zones": narrative.liquidity_zones
                }
            )
        
        elif sweep_type == "BEARISH" and last_ob['type'] == "bearish":
            entry_price = last_ob['zone'][0]
            stop_loss = last_ob['zone'][1] + (last_ob['zone'][1] - last_ob['zone'][0]) * 0.15
            
            risk = stop_loss - entry_price
            target = entry_price - (risk * self.min_rr)
            
            base_confidence = 0.8
            
            if narrative.killzone:
                base_confidence += 0.1
            
            return ICTSetup(
                entry_price=entry_price,
                stop_loss=stop_loss,
                target=target,
                direction="SELL",
                risk_reward=self.min_rr,
                confidence=min(base_confidence, 1.0),
                setup_type="SWEEP_OB_ENTRY_BEAR",
                components=["LIQUIDITY_SWEEP", "ORDER_BLOCK_FRESH", "EXTERNAL_LIQUIDITY"],
                meta={
                    "ob_data": last_ob,
                    "sweep_type": sweep_type,
                    "liquidity_zones": narrative.liquidity_zones
                }
            )
        
        return None
    
    def build_bos_basic_setup(self, df: pd.DataFrame, structure_state: MarketStructureState,
                              context: MarketContext, narrative: MarketNarrative) -> Optional[ICTSetup]:
        """
        Setup básico: BOS + Context (fallback quando setups complexos não estão disponíveis)
        
        Critérios:
        1. BOS confirmado
        2. Context não-consolidação
        3. SL baseado em swing high/low recente
        """
        if structure_state.last_bos is None:
            return None
        
        if context.regime == "CONSOLIDATION":
            return None
        
        bos = structure_state.last_bos
        current_price = df['close'].iat[-1]
        
        lookback = 10
        recent_high = df['high'].iloc[-lookback:].max()
        recent_low = df['low'].iloc[-lookback:].min()
        
        if bos['type'] == "BULLISH":
            entry_price = current_price
            stop_loss = recent_low * 0.998
            
            risk = entry_price - stop_loss
            target = entry_price + (risk * self.min_rr)
            
            base_confidence = 0.6
            
            if narrative.htf_bias == "BULLISH":
                base_confidence += 0.1
            if context.regime == "IMPULSE":
                base_confidence += 0.1
            if narrative.killzone:
                base_confidence += 0.05
            
            return ICTSetup(
                entry_price=entry_price,
                stop_loss=stop_loss,
                target=target,
                direction="BUY",
                risk_reward=self.min_rr,
                confidence=min(base_confidence, 1.0),
                setup_type="BOS_BASIC_BULL",
                components=["BOS_BULLISH", f"CONTEXT_{context.regime}"],
                meta={
                    "bos_data": bos,
                    "setup_level": "BASIC",
                    "htf_bias": narrative.htf_bias
                }
            )
        
        elif bos['type'] == "BEARISH":
            entry_price = current_price
            stop_loss = recent_high * 1.002
            
            risk = stop_loss - entry_price
            target = entry_price - (risk * self.min_rr)
            
            base_confidence = 0.6
            
            if narrative.htf_bias == "BEARISH":
                base_confidence += 0.1
            if context.regime == "IMPULSE":
                base_confidence += 0.1
            if narrative.killzone:
                base_confidence += 0.05
            
            return ICTSetup(
                entry_price=entry_price,
                stop_loss=stop_loss,
                target=target,
                direction="SELL",
                risk_reward=self.min_rr,
                confidence=min(base_confidence, 1.0),
                setup_type="BOS_BASIC_BEAR",
                components=["BOS_BEARISH", f"CONTEXT_{context.regime}"],
                meta={
                    "bos_data": bos,
                    "setup_level": "BASIC",
                    "htf_bias": narrative.htf_bias
                }
            )
        
        return None
    
    def get_best_setup(self, df: pd.DataFrame, structure_state: MarketStructureState,
                       context: MarketContext, narrative: MarketNarrative) -> Optional[ICTSetup]:
        """
        Retorna o melhor setup disponível baseado em:
        - Confiança
        - Risk:Reward
        - Confluência de componentes
        
        Ordem de prioridade (melhor → básico):
        1. CHoCH + OB + Sweep (premium setup)
        2. BOS + FVG + Retest (confluence setup)
        3. Sweep + OB Entry (liquidity setup)
        4. BOS + Context (basic setup - fallback)
        """
        setups = []
        
        choch_setup = self.build_choch_ob_sweep_setup(df, structure_state, context, narrative)
        if choch_setup:
            setups.append(choch_setup)
        
        bos_setup = self.build_bos_fvg_setup(df, structure_state, context, narrative)
        if bos_setup:
            setups.append(bos_setup)
        
        sweep_setup = self.build_sweep_ob_entry_setup(df, structure_state, context, narrative)
        if sweep_setup:
            setups.append(sweep_setup)
        
        basic_setup = self.build_bos_basic_setup(df, structure_state, context, narrative)
        if basic_setup:
            setups.append(basic_setup)
        
        if not setups:
            return None
        
        best_setup = max(setups, key=lambda s: s.confidence * (1 + s.risk_reward / 10))
        
        return best_setup
