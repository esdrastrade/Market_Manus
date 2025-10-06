"""
Shadow Mode Validator - WS1 Task 2 (Fase 2)

Executa VoteData (sistema atual) e ConfluenceEngine em paralelo,
compara outputs e loga diferenças para validação gradual.

Feature Flags:
- ENABLE_SHADOW_MODE: Ativa comparação paralela (default: True para validação)
- ENABLE_NEW_CONFLUENCE_ENGINE: Usa novo engine para decisões reais (default: False)
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from market_manus.core.signal import Signal
from market_manus.confluence_mode.confluence_engine_adapter import ConfluenceEngineAdapter

# Feature Flags
ENABLE_SHADOW_MODE = True  # Ativa comparação paralela
ENABLE_NEW_CONFLUENCE_ENGINE = False  # Usa novo engine para decisões (ainda em validação)


@dataclass
class ShadowComparisonResult:
    """Resultado da comparação entre sistemas"""
    legacy_signals: List[Tuple[int, str]]  # VoteData output
    new_signal: Signal  # ConfluenceEngine output
    agreement: bool  # True se sistemas concordam
    differences: List[str]  # Lista de diferenças encontradas
    stats: Dict  # Estatísticas da comparação


class ShadowModeValidator:
    """
    Valida ConfluenceEngine rodando em paralelo com sistema VoteData.
    
    Workflow:
    1. Executa ambos sistemas com mesmos inputs
    2. Normaliza outputs para comparação
    3. Calcula métricas de concordância
    4. Loga diferenças para análise
    """
    
    def __init__(self, log_differences: bool = True):
        """
        Args:
            log_differences: Se True, imprime diferenças encontradas
        """
        self.log_differences = log_differences
        self.comparison_history = []
    
    def compare_outputs(
        self,
        legacy_signals: List[Tuple[int, str]],
        new_signal: Signal,
        total_candles: int
    ) -> ShadowComparisonResult:
        """
        Compara outputs de ambos sistemas.
        
        Args:
            legacy_signals: Lista de (índice, direção) do VoteData
            new_signal: Signal do ConfluenceEngine
            total_candles: Total de candles analisados
        
        Returns:
            ShadowComparisonResult com análise detalhada
        """
        differences = []
        
        # Conta sinais por direção no legacy system
        legacy_buy = sum(1 for _, direction in legacy_signals if direction == "BUY")
        legacy_sell = sum(1 for _, direction in legacy_signals if direction == "SELL")
        legacy_total = len(legacy_signals)
        
        # Extrai info do novo sistema
        new_action = new_signal.action
        new_confidence = new_signal.confidence
        
        # Verifica concordância básica de direção
        agreement = self._check_agreement(legacy_signals, new_signal)
        
        # Analisa diferenças
        if legacy_total == 0 and new_action != "HOLD":
            differences.append(f"Legacy: 0 sinais, New: {new_action} (conf={new_confidence:.2f})")
        elif legacy_total > 0 and new_action == "HOLD":
            differences.append(f"Legacy: {legacy_total} sinais (BUY={legacy_buy}, SELL={legacy_sell}), New: HOLD")
        
        if not agreement:
            legacy_bias = "BUY" if legacy_buy > legacy_sell else "SELL" if legacy_sell > legacy_buy else "NEUTRAL"
            differences.append(f"Direção divergente: Legacy={legacy_bias}, New={new_action}")
        
        # Estatísticas
        stats = {
            "legacy_total_signals": legacy_total,
            "legacy_buy_signals": legacy_buy,
            "legacy_sell_signals": legacy_sell,
            "new_action": new_action,
            "new_confidence": new_confidence,
            "agreement": agreement,
            "total_candles": total_candles
        }
        
        result = ShadowComparisonResult(
            legacy_signals=legacy_signals,
            new_signal=new_signal,
            agreement=agreement,
            differences=differences,
            stats=stats
        )
        
        # Log diferenças
        if self.log_differences and differences:
            self._log_differences(result)
        
        # Armazena histórico
        self.comparison_history.append(result)
        
        return result
    
    def _check_agreement(self, legacy_signals: List[Tuple[int, str]], new_signal: Signal) -> bool:
        """
        Verifica se ambos sistemas concordam na direção principal.
        
        Considera concordância se:
        - Ambos sugerem BUY
        - Ambos sugerem SELL
        - Ambos sugerem HOLD/sem sinal
        """
        if not legacy_signals and new_signal.action == "HOLD":
            return True  # Ambos sem sinal
        
        if not legacy_signals or new_signal.action == "HOLD":
            return False  # Um tem sinal, outro não
        
        # Conta votos no legacy
        buy_count = sum(1 for _, direction in legacy_signals if direction == "BUY")
        sell_count = sum(1 for _, direction in legacy_signals if direction == "SELL")
        
        # Direção dominante no legacy
        if buy_count > sell_count:
            legacy_bias = "BUY"
        elif sell_count > buy_count:
            legacy_bias = "SELL"
        else:
            legacy_bias = "NEUTRAL"
        
        # Compara com novo sistema
        return legacy_bias == new_signal.action or (legacy_bias == "NEUTRAL" and new_signal.action == "HOLD")
    
    def _log_differences(self, result: ShadowComparisonResult):
        """Imprime diferenças encontradas para análise"""
        print(f"\n⚠️  Shadow Mode: Diferenças detectadas")
        print(f"  Legacy: {result.stats['legacy_total_signals']} sinais " +
              f"(BUY={result.stats['legacy_buy_signals']}, SELL={result.stats['legacy_sell_signals']})")
        print(f"  New: {result.stats['new_action']} (confidence={result.stats['new_confidence']:.2f})")
        for diff in result.differences:
            print(f"    - {diff}")
    
    def get_agreement_stats(self) -> Dict:
        """
        Calcula estatísticas de concordância ao longo do histórico.
        
        Returns:
            Dict com métricas agregadas
        """
        if not self.comparison_history:
            return {
                "total_comparisons": 0,
                "agreements": 0,
                "disagreements": 0,
                "agreement_rate": 0.0
            }
        
        total = len(self.comparison_history)
        agreements = sum(1 for r in self.comparison_history if r.agreement)
        disagreements = total - agreements
        
        return {
            "total_comparisons": total,
            "agreements": agreements,
            "disagreements": disagreements,
            "agreement_rate": agreements / total if total > 0 else 0.0,
            "avg_legacy_signals": sum(r.stats['legacy_total_signals'] for r in self.comparison_history) / total,
            "new_buy_rate": sum(1 for r in self.comparison_history if r.new_signal.action == "BUY") / total,
            "new_sell_rate": sum(1 for r in self.comparison_history if r.new_signal.action == "SELL") / total,
            "new_hold_rate": sum(1 for r in self.comparison_history if r.new_signal.action == "HOLD") / total
        }
    
    def print_summary(self):
        """Imprime resumo das comparações"""
        stats = self.get_agreement_stats()
        
        print("\n" + "="*70)
        print("📊 SHADOW MODE VALIDATION - RESUMO")
        print("="*70)
        print(f"Total de Comparações: {stats['total_comparisons']}")
        print(f"Concordância: {stats['agreements']} ({stats['agreement_rate']*100:.1f}%)")
        print(f"Divergência: {stats['disagreements']} ({(1-stats['agreement_rate'])*100:.1f}%)")
        print(f"\nMédias:")
        print(f"  Legacy signals/run: {stats['avg_legacy_signals']:.1f}")
        print(f"  New engine actions: BUY={stats['new_buy_rate']*100:.1f}%, " +
              f"SELL={stats['new_sell_rate']*100:.1f}%, HOLD={stats['new_hold_rate']*100:.1f}%")
        print("="*70 + "\n")


def run_shadow_validation(
    df: pd.DataFrame,
    strategy_configs: Dict,
    legacy_calculate_fn: callable,
    regime_cfg: Optional[Dict] = None
) -> Tuple[List[Tuple[int, str]], Signal, ShadowComparisonResult]:
    """
    Executa validação shadow-mode: roda ambos sistemas e compara.
    
    Args:
        df: DataFrame OHLCV
        strategy_configs: Configs das estratégias selecionadas
        legacy_calculate_fn: Função legacy que calcula confluência (VoteData)
        regime_cfg: Config opcional de regime para ConfluenceEngine
    
    Returns:
        Tuple (legacy_signals, new_signal, comparison_result)
    """
    # Executa sistema legacy (VoteData)
    legacy_signals = legacy_calculate_fn()
    
    # Executa novo sistema (ConfluenceEngine)
    adapter = ConfluenceEngineAdapter(strategy_configs, df)
    if regime_cfg is None:
        regime_cfg = adapter.build_regime_config()
    
    engine = adapter.create_confluence_engine(regime_cfg)
    new_signal = engine.evaluate(df, ctx={"shadow_mode": True})
    
    # Compara outputs
    validator = ShadowModeValidator(log_differences=True)
    comparison = validator.compare_outputs(legacy_signals, new_signal, len(df))
    
    return legacy_signals, new_signal, comparison
