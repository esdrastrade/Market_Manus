# market_manus/strategies/strategy_manager_integrated.py
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Callable, Optional

# ⚠️ Usa o contrato unificado que você já tem
from market_manus.strategy_contract import STRATEGY_REGISTRY_V2, run_strategy, list_available_strategies

logger = logging.getLogger(__name__)

@dataclass
class StrategyWrapper:
    key: str
    cls: Any
    default_params: Dict[str, Any] = field(default_factory=dict)

class StrategyManagerIntegrated:
    """
    Manager integrado: inicializa a partir do STRATEGY_REGISTRY_V2,
    evitando reflection frágil por nome de arquivo/classe.
    """

    def __init__(self) -> None:
        self._strategies: Dict[str, StrategyWrapper] = {}
        self._register_from_contract()
        logger.info("Strategy Manager inicializado com %d estratégias", len(self._strategies))

    # ---------- API pública ----------
    def list_strategies(self) -> List[str]:
        return list(self._strategies.keys())

    def get_strategy(self, key: str) -> Optional[StrategyWrapper]:
        return self._strategies.get(key)

    def run(self, key: str, df, **override_params) -> Dict[str, Any]:
        """
        Executa UMA estratégia pelo 'key' usando run_strategy do contrato.
        """
        if key not in self._strategies:
            raise KeyError(f"Estratégia '{key}' não registrada")
        return run_strategy(key, df, **override_params)

    def run_all(self, df, **override_params) -> Dict[str, Dict[str, Any]]:
        """
        Executa TODAS as estratégias registradas.
        """
        out: Dict[str, Dict[str, Any]] = {}
        for key in self._strategies.keys():
            try:
                out[key] = run_strategy(key, df, **override_params)
            except Exception as e:
                logger.exception("Falha ao rodar estratégia %s: %s", key, e)
        return out

    # ---------- Internals ----------
    def _register_from_contract(self) -> None:
        """
        Puxa tudo do STRATEGY_REGISTRY_V2.
        """
        available = list_available_strategies()
        for key in available:
            reg = STRATEGY_REGISTRY_V2[key]
            self._strategies[key] = StrategyWrapper(
                key=key, cls=reg["class"], default_params=reg.get("default_params", {})
            )
