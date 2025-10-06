"""
ConfluenceEngine Adapter - WS1 Task 1 (Fase 2)

Adapter que mapeia estratégias atuais (SMC + clássicas) para o ConfluenceEngine.
Permite shadow-mode validation e migração gradual.

Arquitetura:
- Converte strategy functions (que recebem arrays) em detectores (callables sem args)
- Mapeia config atual para regime_cfg do ConfluenceEngine
- Feature flag: ENABLE_NEW_CONFLUENCE_ENGINE
"""

import pandas as pd
from typing import Dict, Callable, List, Optional
from market_manus.core.signal import Signal
from market_manus.strategies.smc.patterns import ConfluenceEngine

# Feature flag para rollout controlado
ENABLE_NEW_CONFLUENCE_ENGINE = False


class ConfluenceEngineAdapter:
    """
    Adapter para migração gradual do sistema de confluência.
    
    Converte estratégias atuais em formato compatível com ConfluenceEngine:
    - SMC strategies: detect_bos, detect_choch, detect_order_blocks, detect_fvg, detect_liquidity_sweep
    - Classic strategies: RSI, EMA, Bollinger, MACD, Stochastic, Williams, ADX, Fibonacci
    """
    
    def __init__(self, strategy_configs: Dict, df: pd.DataFrame):
        """
        Args:
            strategy_configs: Dict com estratégias selecionadas e seus pesos
                              Formato: {"strategy_key": {"weight": float, "enabled": bool}}
            df: DataFrame OHLCV completo para análise
        """
        self.strategy_configs = strategy_configs
        self.df = df
        self.detectors = {}
        self.weights = {}
        
        self._build_detectors()
    
    def _build_detectors(self):
        """
        Constrói dict de detectores e pesos a partir das estratégias configuradas.
        
        Cada detector é um callable sem argumentos que retorna Signal,
        capturando df e parâmetros via closure.
        """
        for strategy_key, config in self.strategy_configs.items():
            if not config.get('enabled', True):
                continue
            
            weight = config.get('weight', 1.0)
            detector_fn = self._create_detector(strategy_key)
            
            if detector_fn:
                self.detectors[strategy_key] = detector_fn
                self.weights[strategy_key] = weight
    
    def _create_detector(self, strategy_key: str) -> Optional[Callable[[], Signal]]:
        """
        Cria detector callable para estratégia específica.
        
        Detectores SMC já retornam Signal, estratégias clássicas precisam de wrapping.
        """
        df = self.df
        
        # SMC Strategies
        if strategy_key == "smc_bos":
            from market_manus.strategies.smc.patterns import detect_bos
            return lambda: detect_bos(df)
        
        elif strategy_key == "smc_choch":
            from market_manus.strategies.smc.patterns import detect_choch
            return lambda: detect_choch(df)
        
        elif strategy_key == "smc_order_blocks":
            from market_manus.strategies.smc.patterns import detect_order_blocks
            return lambda: detect_order_blocks(df)
        
        elif strategy_key == "smc_fvg":
            from market_manus.strategies.smc.patterns import detect_fvg
            return lambda: detect_fvg(df)
        
        elif strategy_key == "smc_liquidity_sweep":
            from market_manus.strategies.smc.patterns import detect_liquidity_sweep
            return lambda: detect_liquidity_sweep(df)
        
        # Classic Strategies - wrapping necessário
        elif strategy_key == "rsi":
            return lambda: self._wrap_classic_strategy("RSI", self._detect_rsi_signal())
        
        elif strategy_key == "ema_cross":
            return lambda: self._wrap_classic_strategy("EMA Cross", self._detect_ema_signal())
        
        elif strategy_key == "bollinger":
            return lambda: self._wrap_classic_strategy("Bollinger", self._detect_bollinger_signal())
        
        elif strategy_key == "macd":
            return lambda: self._wrap_classic_strategy("MACD", self._detect_macd_signal())
        
        elif strategy_key == "stochastic":
            return lambda: self._wrap_classic_strategy("Stochastic", self._detect_stochastic_signal())
        
        elif strategy_key == "williams_r":
            return lambda: self._wrap_classic_strategy("Williams %R", self._detect_williams_signal())
        
        elif strategy_key == "adx":
            return lambda: self._wrap_classic_strategy("ADX", self._detect_adx_signal())
        
        elif strategy_key == "fibonacci":
            return lambda: self._wrap_classic_strategy("Fibonacci", self._detect_fibonacci_signal())
        
        return None
    
    def _wrap_classic_strategy(self, name: str, signal_data: Dict) -> Signal:
        """
        Converte resultado de estratégia clássica em Signal.
        
        Args:
            name: Nome da estratégia
            signal_data: Dict com {"action": str, "confidence": float, "reason": str}
        """
        if not signal_data or signal_data.get("action") == "HOLD":
            return Signal(action="HOLD", confidence=0.0, tags=[f"CLASSIC:{name}"], reasons=["Sem sinal"])
        
        return Signal(
            action=signal_data["action"],
            confidence=signal_data.get("confidence", 0.5),
            reasons=[signal_data.get("reason", f"{name} sinal")],
            tags=[f"CLASSIC:{name}", f"CLASSIC:{name}_{signal_data['action']}"],
            meta={"strategy": name}
        )
    
    def _detect_rsi_signal(self) -> Dict:
        """RSI: oversold (<30) = BUY, overbought (>70) = SELL"""
        from market_manus.strategies.classic_analysis import calculate_rsi
        
        rsi = calculate_rsi(self.df['close'], period=14)
        if len(rsi) == 0:
            return {"action": "HOLD"}
        
        current_rsi = rsi.iloc[-1]
        
        if current_rsi < 30:
            return {
                "action": "BUY",
                "confidence": 0.5 + (30 - current_rsi) / 60,
                "reason": f"RSI oversold: {current_rsi:.1f}"
            }
        elif current_rsi > 70:
            return {
                "action": "SELL",
                "confidence": 0.5 + (current_rsi - 70) / 60,
                "reason": f"RSI overbought: {current_rsi:.1f}"
            }
        
        return {"action": "HOLD"}
    
    def _detect_ema_signal(self) -> Dict:
        """EMA Cross: EMA rápida cruza EMA lenta"""
        from market_manus.strategies.classic_analysis import calculate_ema
        
        ema_fast = calculate_ema(self.df['close'], period=9)
        ema_slow = calculate_ema(self.df['close'], period=21)
        
        if len(ema_fast) < 2 or len(ema_slow) < 2:
            return {"action": "HOLD"}
        
        current_fast = ema_fast.iloc[-1]
        prev_fast = ema_fast.iloc[-2]
        current_slow = ema_slow.iloc[-1]
        prev_slow = ema_slow.iloc[-2]
        
        if prev_fast <= prev_slow and current_fast > current_slow:
            return {
                "action": "BUY",
                "confidence": 0.6,
                "reason": "EMA bullish crossover"
            }
        elif prev_fast >= prev_slow and current_fast < current_slow:
            return {
                "action": "SELL",
                "confidence": 0.6,
                "reason": "EMA bearish crossover"
            }
        
        return {"action": "HOLD"}
    
    def _detect_bollinger_signal(self) -> Dict:
        """Bollinger Bands: price abaixo lower band = BUY, acima upper = SELL"""
        from market_manus.strategies.classic_analysis import calculate_bollinger_bands
        
        upper, middle, lower = calculate_bollinger_bands(self.df['close'], period=20, std_dev=2)
        
        if len(upper) == 0:
            return {"action": "HOLD"}
        
        current_price = self.df['close'].iloc[-1]
        current_upper = upper.iloc[-1]
        current_lower = lower.iloc[-1]
        
        if current_price < current_lower:
            return {
                "action": "BUY",
                "confidence": 0.6,
                "reason": f"Price below lower BB: {current_price:.2f} < {current_lower:.2f}"
            }
        elif current_price > current_upper:
            return {
                "action": "SELL",
                "confidence": 0.6,
                "reason": f"Price above upper BB: {current_price:.2f} > {current_upper:.2f}"
            }
        
        return {"action": "HOLD"}
    
    def _detect_macd_signal(self) -> Dict:
        """MACD: crossover da linha de sinal"""
        from market_manus.strategies.classic_analysis import calculate_macd
        
        macd_line, signal_line, histogram = calculate_macd(self.df['close'])
        
        if len(macd_line) < 2 or len(signal_line) < 2:
            return {"action": "HOLD"}
        
        current_macd = macd_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        current_signal = signal_line.iloc[-1]
        prev_signal = signal_line.iloc[-2]
        
        if prev_macd <= prev_signal and current_macd > current_signal:
            return {
                "action": "BUY",
                "confidence": 0.6,
                "reason": "MACD bullish crossover"
            }
        elif prev_macd >= prev_signal and current_macd < current_signal:
            return {
                "action": "SELL",
                "confidence": 0.6,
                "reason": "MACD bearish crossover"
            }
        
        return {"action": "HOLD"}
    
    def _detect_stochastic_signal(self) -> Dict:
        """Stochastic: %K cruza %D em zona oversold/overbought"""
        from market_manus.strategies.classic_analysis import calculate_stochastic
        
        k, d = calculate_stochastic(self.df, k_period=14, d_period=3)
        
        if len(k) < 2 or len(d) < 2:
            return {"action": "HOLD"}
        
        current_k = k.iloc[-1]
        prev_k = k.iloc[-2]
        current_d = d.iloc[-1]
        prev_d = d.iloc[-2]
        
        if prev_k <= prev_d and current_k > current_d and current_k < 20:
            return {
                "action": "BUY",
                "confidence": 0.6,
                "reason": f"Stochastic bullish cross in oversold: %K={current_k:.1f}"
            }
        elif prev_k >= prev_d and current_k < current_d and current_k > 80:
            return {
                "action": "SELL",
                "confidence": 0.6,
                "reason": f"Stochastic bearish cross in overbought: %K={current_k:.1f}"
            }
        
        return {"action": "HOLD"}
    
    def _detect_williams_signal(self) -> Dict:
        """Williams %R: oversold (< -80) = BUY, overbought (> -20) = SELL"""
        from market_manus.strategies.classic_analysis import calculate_williams_r
        
        wr = calculate_williams_r(self.df, period=14)
        
        if len(wr) == 0:
            return {"action": "HOLD"}
        
        current_wr = wr.iloc[-1]
        
        if current_wr < -80:
            return {
                "action": "BUY",
                "confidence": 0.5 + (80 + current_wr) / -40,
                "reason": f"Williams %R oversold: {current_wr:.1f}"
            }
        elif current_wr > -20:
            return {
                "action": "SELL",
                "confidence": 0.5 + (current_wr + 20) / 40,
                "reason": f"Williams %R overbought: {current_wr:.1f}"
            }
        
        return {"action": "HOLD"}
    
    def _detect_adx_signal(self) -> Dict:
        """ADX: trend strength com DI+ vs DI-"""
        from market_manus.strategies.classic_analysis import calculate_adx
        
        adx, plus_di, minus_di = calculate_adx(self.df, period=14)
        
        if len(adx) == 0:
            return {"action": "HOLD"}
        
        current_adx = adx.iloc[-1]
        current_plus = plus_di.iloc[-1]
        current_minus = minus_di.iloc[-1]
        
        if current_adx > 25:
            if current_plus > current_minus:
                return {
                    "action": "BUY",
                    "confidence": min(0.4 + current_adx / 100, 0.8),
                    "reason": f"Strong uptrend: ADX={current_adx:.1f}, +DI={current_plus:.1f}"
                }
            elif current_minus > current_plus:
                return {
                    "action": "SELL",
                    "confidence": min(0.4 + current_adx / 100, 0.8),
                    "reason": f"Strong downtrend: ADX={current_adx:.1f}, -DI={current_minus:.1f}"
                }
        
        return {"action": "HOLD"}
    
    def _detect_fibonacci_signal(self) -> Dict:
        """Fibonacci: retracement levels como suporte/resistência"""
        highs = self.df['high']
        lows = self.df['low']
        closes = self.df['close']
        
        if len(self.df) < 20:
            return {"action": "HOLD"}
        
        swing_high = highs.iloc[-20:].max()
        swing_low = lows.iloc[-20:].min()
        current_price = closes.iloc[-1]
        
        fib_range = swing_high - swing_low
        if fib_range == 0:
            return {"action": "HOLD"}
        
        fib_382 = swing_high - 0.382 * fib_range
        fib_618 = swing_high - 0.618 * fib_range
        
        tolerance = fib_range * 0.01
        
        if abs(current_price - fib_618) < tolerance:
            return {
                "action": "BUY",
                "confidence": 0.65,
                "reason": f"Price at Fib 0.618: {current_price:.2f}"
            }
        elif abs(current_price - fib_382) < tolerance:
            return {
                "action": "BUY",
                "confidence": 0.55,
                "reason": f"Price at Fib 0.382: {current_price:.2f}"
            }
        
        return {"action": "HOLD"}
    
    @staticmethod
    def build_regime_config(market_context_config: Optional[Dict] = None) -> Dict:
        """
        Converte config de market context para regime_cfg do ConfluenceEngine.
        
        Args:
            market_context_config: Config opcional do market context analyzer
        
        Returns:
            Dict com thresholds para ConfluenceEngine
        """
        if not market_context_config:
            market_context_config = {}
        
        return {
            'adx_min': market_context_config.get('adx_min', 15),
            'adx_max': market_context_config.get('adx_max', 100),
            'atr_min': market_context_config.get('atr_min', 0.0001),
            'bb_width_min': market_context_config.get('bb_width_min', 0.01),
            'buy_threshold': 0.5,
            'sell_threshold': -0.5,
            'conflict_penalty': 0.3
        }
    
    def create_confluence_engine(self, regime_cfg: Optional[Dict] = None) -> ConfluenceEngine:
        """
        Cria instância de ConfluenceEngine com detectores e pesos configurados.
        
        Args:
            regime_cfg: Config de regime (opcional, usa padrão se não fornecido)
        
        Returns:
            ConfluenceEngine configurado
        """
        if regime_cfg is None:
            regime_cfg = self.build_regime_config()
        
        return ConfluenceEngine(
            detectors=self.detectors,
            weights=self.weights,
            regime_cfg=regime_cfg
        )
