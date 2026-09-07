"""Core position-sizing calculations for FMM.

All calculations use USD-denominated pip value supplied by the user. This keeps
position sizing independent of instrument conventions, broker pricing models,
and live market data.
"""

from __future__ import annotations

from .models import CalculationResult, TradeSetup
from .validators import validate_trade_setup


def calculate_risk_amount(balance: float, risk_percent: float) -> float:
    """Return the dollar amount the trader is willing to risk."""
    return balance * risk_percent / 100.0


def calculate_pip_value(risk_amount: float, stop_loss_pips: float) -> float:
    """Return the USD value per pip required to hit the chosen risk at SL."""
    if stop_loss_pips <= 0:
        raise ValueError("stop_loss_pips must be > 0")
    return risk_amount / stop_loss_pips


def calculate_position_size(pip_value: float, pip_value_per_lot: float) -> float:
    """Return position size in standard lots."""
    if pip_value_per_lot <= 0:
        raise ValueError("pip_value_per_lot must be > 0")
    return pip_value / pip_value_per_lot


def calculate_rr_ratio(
    take_profit_pips: float | None, stop_loss_pips: float
) -> float | None:
    """Return reward-to-risk as TP/SL, or None when TP is not set."""
    if take_profit_pips is None or take_profit_pips <= 0 or stop_loss_pips <= 0:
        return None
    return take_profit_pips / stop_loss_pips


def calculate_potential_profit(
    position_size: float,
    pip_value_per_lot: float,
    take_profit_pips: float | None,
) -> float | None:
    """Return potential USD profit at TP for the calculated position."""
    if take_profit_pips is None or take_profit_pips <= 0:
        return None
    return position_size * pip_value_per_lot * take_profit_pips


def compute_trade(setup: TradeSetup) -> tuple[CalculationResult, list[str]]:
    """Calculate a complete position size from a validated trade setup."""
    errors = validate_trade_setup(setup)
    if errors:
        return _empty_result(), errors

    risk_amount = calculate_risk_amount(setup.balance, setup.risk_percent)
    pip_value = calculate_pip_value(risk_amount, setup.stop_loss_pips)
    position_size = calculate_position_size(pip_value, setup.pip_value_per_lot)
    rr_ratio = calculate_rr_ratio(setup.take_profit_pips, setup.stop_loss_pips)
    potential_profit = calculate_potential_profit(
        position_size,
        setup.pip_value_per_lot,
        setup.take_profit_pips,
    )

    result = CalculationResult(
        risk_amount=round(risk_amount, 2),
        pip_value=round(pip_value, 2),
        position_size=round(position_size, 6),
        rr_ratio=round(rr_ratio, 2) if rr_ratio is not None else None,
        potential_profit=round(potential_profit, 2)
        if potential_profit is not None
        else None,
        potential_loss=round(risk_amount, 2),
    )
    return result, []


def _empty_result() -> CalculationResult:
    """Return a safe empty result when validation fails."""
    return CalculationResult(
        risk_amount=0.0,
        pip_value=0.0,
        position_size=0.0,
        potential_loss=0.0,
    )
