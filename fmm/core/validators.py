"""Input validation for trade parameters.

Returns a list of human-readable error strings.  An empty list means valid.
"""

from __future__ import annotations

from .constants import ALLOWED_LEVERAGE, INSTRUMENT_PRESETS
from .models import TradeSetup


def validate_trade_setup(setup: TradeSetup) -> list[str]:
    """Validate a *TradeSetup* and return error messages (empty if OK)."""
    errors: list[str] = []

    # ---- Balance ----
    if setup.balance <= 0:
        errors.append("Account balance must be greater than zero.")
    elif setup.balance > 1_000_000_000:
        errors.append("Account balance seems unreasonably large (>$1B).")

    # ---- Risk % ----
    if setup.risk_percent <= 0:
        errors.append("Risk percentage must be greater than zero.")
    elif setup.risk_percent > 100:
        errors.append("Risk percentage cannot exceed 100%.")
    elif setup.risk_percent > 10:
        errors.append("Risk above 10% per trade is extremely aggressive.")

    # ---- Stop-loss ----
    stop_loss_value = (
        setup.stop_loss_points
        if setup.stop_loss_points is not None
        else setup.stop_loss_pips
    )
    if stop_loss_value <= 0:
        errors.append("Stop-loss must be greater than zero.")

    # ---- Pip value per lot ----
    dynamic_pip_value = bool(
        INSTRUMENT_PRESETS.get(setup.instrument, {}).get("dynamic_pip_value", False)
    )
    if setup.pip_value_per_lot <= 0 and not dynamic_pip_value:
        errors.append("Pip value per lot must be greater than zero.")

    # ---- Leverage ----
    if setup.leverage not in ALLOWED_LEVERAGE:
        errors.append(f"Invalid leverage '{setup.leverage}'.")

    # ---- Take-profit (optional) ----
    take_profit_value = (
        setup.take_profit_points
        if setup.take_profit_points is not None
        else setup.take_profit_pips
    )
    if take_profit_value is not None:
        if take_profit_value < 0:
            errors.append("Take-profit pips cannot be negative.")
        elif take_profit_value == 0:
            # Allow zero – treated as no take-profit
            pass

    return errors


def validate_leverage(leverage_str: str) -> str | None:
    """Validate a leverage string.  Returns error message or None."""
    if leverage_str not in ALLOWED_LEVERAGE:
        return f"Invalid leverage '{leverage_str}'. Allowed: {', '.join(ALLOWED_LEVERAGE)}"
    return None


def validate_positive_float(value: float | None, label: str) -> str | None:
    """Quick single-field validation helper. Returns error string or None."""
    if value is None:
        return f"{label} is required."
    if value <= 0:
        return f"{label} must be greater than zero."
    return None
