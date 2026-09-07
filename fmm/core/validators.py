"""Input validation for trade calculations."""

from __future__ import annotations

from .models import TradeSetup


def validate_trade_setup(setup: TradeSetup) -> list[str]:
    """Return human-readable validation errors for a trade setup."""
    errors: list[str] = []

    if setup.balance <= 0:
        errors.append("Account balance must be greater than zero.")
    elif setup.balance > 1_000_000_000:
        errors.append("Account balance seems unreasonably large (>$1B).")

    if setup.risk_percent <= 0:
        errors.append("Risk percentage must be greater than zero.")
    elif setup.risk_percent > 100:
        errors.append("Risk percentage cannot exceed 100%.")
    elif setup.risk_percent > 10:
        errors.append("Risk above 10% per trade is extremely aggressive.")

    if setup.stop_loss_pips <= 0:
        errors.append("Stop-loss must be greater than zero.")

    if setup.pip_value_per_lot <= 0:
        errors.append("Pip value per lot must be greater than zero.")

    if setup.take_profit_pips is not None and setup.take_profit_pips < 0:
        errors.append("Take-profit cannot be negative.")

    return errors
