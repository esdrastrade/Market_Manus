"""
Smart Money Concepts (SMC) strategies module

Arquitetura ICT Framework v2.0:
- Legacy functions mantidas para compatibilidade
- Novo ICT Framework profissional com 4 pilares
"""

from .patterns import (
    SMCDetector,
    detect_bos,
    detect_choch,
    detect_order_blocks,
    detect_fvg,
    detect_liquidity_sweep,
    detect_liquidity_zones,
    ConfluenceEngine,
    confluence_decision
)

from .ict_framework import (
    ICTFramework,
    detect_ict_signal,
    validate_ict_setup_components
)

from .market_structure import (
    MarketStructureState,
    detect_bos_advanced,
    detect_choch_advanced,
    detect_order_blocks_advanced,
    detect_liquidity_sweep_advanced
)

from .context import (
    MarketContext,
    get_market_context
)

from .narrative import (
    MarketNarrative,
    get_market_narrative
)

from .setup import (
    ICTSetup,
    ICTSetupBuilder
)

__all__ = [
    'SMCDetector',
    'detect_bos',
    'detect_choch',
    'detect_order_blocks',
    'detect_fvg',
    'detect_liquidity_sweep',
    'detect_liquidity_zones',
    'ConfluenceEngine',
    'confluence_decision',
    'ICTFramework',
    'detect_ict_signal',
    'validate_ict_setup_components',
    'MarketStructureState',
    'detect_bos_advanced',
    'detect_choch_advanced',
    'detect_order_blocks_advanced',
    'detect_liquidity_sweep_advanced',
    'MarketContext',
    'get_market_context',
    'MarketNarrative',
    'get_market_narrative',
    'ICTSetup',
    'ICTSetupBuilder'
]
