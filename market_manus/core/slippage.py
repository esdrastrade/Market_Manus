"""
Order Book Slippage Simulator
Provides VWAP-based fill price simulation using L2 order book levels.

Usage:
- simulate_market_fill(side, quantity, bids, asks, top_bid=None, top_ask=None)
  Returns dict with avg_price, filled_qty, slippage_abs, slippage_pct.

Notes:
- Levels must be an iterable of (price: float, qty: float) tuples.
- Quantity is in base asset units (e.g., BTC).
"""
from typing import List, Tuple, Optional, Dict


def _vwap_for_fill(levels: List[Tuple[float, float]], quantity: float) -> Tuple[Optional[float], float, int]:
    """
    Compute VWAP for consuming `quantity` across `levels`.

    Args:
        levels: List of (price, qty) tuples, sorted best-first.
        quantity: Desired base quantity to fill.

    Returns:
        (avg_price, filled_qty, consumed_levels_count)
        - avg_price is None if no liquidity (filled_qty == 0)
    """
    remaining = max(quantity, 0.0)
    if remaining == 0.0:
        return None, 0.0, 0

    total_cost = 0.0
    total_filled = 0.0
    consumed = 0

    for price, qty in levels:
        if remaining <= 1e-12:
            break
        fill = min(qty, remaining)
        total_cost += price * fill
        total_filled += fill
        remaining -= fill
        consumed += 1 if fill > 0 else 0

    if total_filled <= 0.0:
        return None, 0.0, 0

    avg_price = total_cost / total_filled
    return avg_price, total_filled, consumed


def simulate_market_fill(
    side: str,
    quantity: float,
    bids: List[Tuple[float, float]],
    asks: List[Tuple[float, float]],
    top_bid: Optional[float] = None,
    top_ask: Optional[float] = None,
) -> Optional[Dict[str, float]]:
    """
    Simulate a market order fill using L2 order book.

    Args:
        side: 'BUY' to take asks, 'SELL' to take bids.
        quantity: Base asset quantity to fill.
        bids: List of (price, qty) bid levels, best-first.
        asks: List of (price, qty) ask levels, best-first.
        top_bid: Best bid price (optional; if not provided, taken from bids[0]).
        top_ask: Best ask price (optional; if not provided, taken from asks[0]).

    Returns:
        Dict with keys:
            - avg_price: VWAP execution price
            - filled_qty: Executed base quantity
            - slippage_abs: Absolute slippage vs top-of-book in price terms
            - slippage_pct: Slippage percentage vs top-of-book
        Returns None if there is no liquidity or invalid inputs.
    """
    side = side.upper()
    if quantity <= 0:
        return None

    if side == 'BUY':
        levels = asks or []
        reference = top_ask if top_ask is not None else (levels[0][0] if levels else None)
    elif side == 'SELL':
        levels = bids or []
        reference = top_bid if top_bid is not None else (levels[0][0] if levels else None)
    else:
        return None

    if not levels or reference is None:
        return None

    avg_price, filled_qty, _ = _vwap_for_fill(levels, quantity)
    if avg_price is None or filled_qty <= 0:
        return None

    if side == 'BUY':
        slippage_abs = avg_price - reference
    else:  # SELL
        slippage_abs = reference - avg_price

    base = max(reference, 1e-12)
    slippage_pct = slippage_abs / base

    return {
        'avg_price': avg_price,
        'filled_qty': filled_qty,
        'slippage_abs': slippage_abs,
        'slippage_pct': slippage_pct,
    }