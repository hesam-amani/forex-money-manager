"""Core forex position-sizing calculator.

This module contains the **pure calculation engine** with zero GUI
dependency.  It faithfully reproduces the formulas from the original C++
program and adds sensible extensions (R:R, potential profit, lot tiers,
leverage/margin).

Original C++ formulas
----------------------
    risk_amount   = balance * risk_percent / 100
    pip_value     = risk_amount / stop_loss_pips
    position_size = pip_value / pip_value_per_lot

Leverage does NOT affect risk amount or position sizing.
Leverage only affects the required margin calculation.
"""

from __future__ import annotations

import math

from .constants import (
    APPROX_PRICES,
    INSTRUMENT_PRESETS,
    MICRO_LOT,
    MINI_LOT,
    STANDARD_LOT,
    leverage_to_float,
)
from .models import CalculationResult, TradeSetup
from .validators import validate_trade_setup

# ── Individual helpers (public for testing) ────────────────────────────

def calculate_risk_amount(balance: float, risk_percent: float) -> float:
    """Dollar amount at risk: balance * risk% / 100."""
    return balance * risk_percent / 100.0


def calculate_pip_value(risk_amount: float, stop_loss_pips: float) -> float:
    """Dollar value per pip for the planned trade.

    This is how much each pip of movement is worth given the risk budget
    and stop-loss distance.
    """
    if stop_loss_pips <= 0:
        raise ValueError("stop_loss_pips must be > 0")
    return risk_amount / stop_loss_pips


def calculate_position_size(pip_value: float, pip_value_per_lot: float) -> float:
    """Position size in lots.

    ``pip_value``        = USD per pip for this trade  (from risk budget)
    ``pip_value_per_lot`` = USD per pip for 1 standard lot of the instrument
    """
    if pip_value_per_lot <= 0:
        raise ValueError("pip_value_per_lot must be > 0")
    return pip_value / pip_value_per_lot


def points_to_price_distance(instrument: str, points: float) -> float:
    """Convert an instrument point count into its price distance."""
    preset = INSTRUMENT_PRESETS.get(instrument)
    if preset is None:
        raise ValueError(f"Unknown instrument '{instrument}'")
    return points * float(preset["point_size"])


def points_to_pips(instrument: str, points: float) -> float:
    """Convert Forex-style points into pips using explicit instrument sizes."""
    preset = INSTRUMENT_PRESETS.get(instrument)
    if preset is None:
        raise ValueError(f"Unknown instrument '{instrument}'")
    return points_to_price_distance(instrument, points) / float(preset["pip_size"])


def calculate_instrument_pip_value(
    instrument: str,
    custom_pip_value: float,
    current_price: float | None = None,
) -> float:
    """Return USD value of one pip for one standard lot.

    USD-base forex pairs require their current quote price. When a price is
    omitted, the configured approximate price is used for offline operation.
    Custom instruments use the user-supplied pip value because no universal
    contract specification exists.
    """
    preset = INSTRUMENT_PRESETS.get(instrument)
    if preset is None:
        return custom_pip_value

    if bool(preset.get("dynamic_pip_value", False)):
        price = current_price or APPROX_PRICES.get(instrument)
        if price is None or price <= 0:
            raise ValueError("current_price must be > 0 for dynamic instruments")
        return float(preset["pip_multiplier"]) * float(preset["pip_size"]) / price

    if "pip_value" in preset:
        return float(preset["pip_value"])
    price_unit_value = float(preset.get("monetary_value_per_price_unit", 0.0))
    if price_unit_value > 0:
        return price_unit_value * float(preset["pip_size"])
    return custom_pip_value


def calculate_risk_per_lot(
    instrument: str,
    points: float,
    custom_pip_value: float,
    current_price: float | None = None,
) -> tuple[float, float, float]:
    """Return ``(price_distance, pip_distance, risk_per_lot)`` for a stop."""
    preset = INSTRUMENT_PRESETS.get(instrument)
    if preset is None:
        raise ValueError(f"Unknown instrument '{instrument}'")
    price_distance = points_to_price_distance(instrument, points)
    if "monetary_value_per_price_unit" in preset:
        return (
            price_distance,
            price_distance / float(preset["pip_size"]),
            price_distance * float(preset["monetary_value_per_price_unit"]),
        )
    pip_distance = points_to_pips(instrument, points)
    pip_value = calculate_instrument_pip_value(
        instrument, custom_pip_value, current_price
    )
    return price_distance, pip_distance, pip_distance * pip_value


def validate_volume(instrument: str, calculated_volume: float) -> tuple[float | None, str | None]:
    """Validate volume against broker constraints without rounding upward."""
    preset = INSTRUMENT_PRESETS.get(instrument, {})
    minimum = float(preset.get("minimum_volume", 0.0))
    step = float(preset.get("volume_step", 0.0))
    maximum = float(preset.get("maximum_volume", float("inf")))
    if calculated_volume < minimum:
        return None, (
            f"Calculated position size: {calculated_volume:.4f} lots. "
            f"Minimum allowed volume: {minimum:.2f} lots. "
            "Exact requested risk cannot be achieved with the broker's volume constraints."
        )
    if calculated_volume > maximum:
        return None, (
            f"Calculated position size: {calculated_volume:.4f} lots exceeds "
            f"the maximum allowed volume of {maximum:.2f} lots."
        )
    tradable = calculated_volume
    if step > 0:
        tradable = round_lot(calculated_volume, step)
    if tradable < minimum:
        return None, (
            f"Calculated position size: {calculated_volume:.4f} lots cannot be "
            f"represented at the {step:.2f}-lot volume step."
        )
    return round(tradable, 8), None


def calculate_rr_ratio(
    take_profit_pips: float | None, stop_loss_pips: float
) -> float | None:
    """Risk-to-reward ratio (reward / risk).  None when TP is absent."""
    if take_profit_pips is None or take_profit_pips <= 0 or stop_loss_pips <= 0:
        return None
    return take_profit_pips / stop_loss_pips


def calculate_potential_profit(
    pip_value: float, take_profit_pips: float | None
) -> float | None:
    """Potential profit in USD.  None when TP is absent."""
    if take_profit_pips is None or take_profit_pips <= 0:
        return None
    return pip_value * take_profit_pips


def calculate_required_margin(
    position_size: float,
    pip_multiplier: float,
    instrument: str,
    leverage: str,
    current_price: float | None = None,
) -> float | None:
    """Approximate required margin based on position size and leverage.

    Formula:
        notional_value = position_size * pip_multiplier * approx_price
        required_margin = notional_value / leverage

    Because we do not have live prices, we use approximate mid-market
    prices from APPROX_PRICES.  For instruments not in that dict
    (e.g. Custom), we return None.

    ``pip_multiplier`` is the contract-size factor stored per instrument:
        forex pairs: 100 000  (1 pip × 100k = $10)
        XAU/USD:     100      (100 ticks per $1, $100/lot per $1)
        DJI/USD:     1        ($1 per point per lot)
    """
    lev = leverage_to_float(leverage)
    if lev <= 0:
        return None

    if instrument not in APPROX_PRICES:
        return None  # Custom or unknown — cannot estimate
    price = current_price or APPROX_PRICES[instrument]

    notional = position_size * pip_multiplier * price
    return round(notional / lev, 2)


def round_lot(value: float, step: float) -> float:
    """Round *value* down to the nearest *step* (floor rounding)."""
    if step <= 0:
        return value
    return math.floor(value / step) * step


# ── Full calculation ───────────────────────────────────────────────────

def compute_trade(setup: TradeSetup) -> tuple[CalculationResult, list[str]]:
    """Run the full position-sizing calculation.

    Returns ``(result, errors)``.  If *errors* is non-empty the result
    fields will be zeroed / None — the caller should display the errors
    rather than the (invalid) numbers.
    """
    errors = validate_trade_setup(setup)
    if errors:
        return _empty_result(), errors

    risk_amount = calculate_risk_amount(setup.balance, setup.risk_percent)
    if setup.stop_loss_points is not None:
        price_distance, stop_loss_pips, risk_per_lot = calculate_risk_per_lot(
            setup.instrument,
            setup.stop_loss_points,
            setup.pip_value_per_lot,
            setup.current_price,
        )
        pip_value = risk_amount / stop_loss_pips
        position_size = risk_amount / risk_per_lot
        take_profit_pips = (
            points_to_pips(setup.instrument, setup.take_profit_points)
            if setup.take_profit_points is not None
            else None
        )
        take_profit_price_distance = (
            points_to_price_distance(setup.instrument, setup.take_profit_points)
            if setup.take_profit_points is not None
            else None
        )
        potential_profit = (
            position_size * (
                take_profit_price_distance
                * float(INSTRUMENT_PRESETS[setup.instrument].get(
                    "monetary_value_per_price_unit", 0.0
                ))
                if "monetary_value_per_price_unit" in INSTRUMENT_PRESETS[setup.instrument]
                else take_profit_pips
                * calculate_instrument_pip_value(
                    setup.instrument, setup.pip_value_per_lot, setup.current_price
                )
            )
            if take_profit_price_distance is not None and take_profit_pips is not None
            else None
        )
        rr_ratio = (
            take_profit_pips / stop_loss_pips
            if take_profit_pips is not None and take_profit_pips > 0
            else None
        )
    else:
        stop_loss_pips = setup.stop_loss_pips
        price_distance = None
        take_profit_price_distance = None
        pip_value = calculate_pip_value(risk_amount, stop_loss_pips)
        instrument_pip_value = calculate_instrument_pip_value(
            setup.instrument,
            setup.pip_value_per_lot,
            setup.current_price,
        )
        position_size = calculate_position_size(pip_value, instrument_pip_value)
        rr_ratio = calculate_rr_ratio(setup.take_profit_pips, stop_loss_pips)
        potential_profit = calculate_potential_profit(pip_value, setup.take_profit_pips)

    tradable_volume, volume_message = validate_volume(setup.instrument, position_size)
    preset = INSTRUMENT_PRESETS.get(setup.instrument, {})

    # Margin requires live prices for accuracy; we estimate with approx prices
    required_margin = calculate_required_margin(
        position_size, setup.pip_multiplier, setup.instrument, setup.leverage,
        setup.current_price,
    )

    result = CalculationResult(
        risk_amount=round(risk_amount, 2),
        pip_value=round(pip_value, 2),
        position_size=round(position_size, 4),
        position_size_standard=round(round_lot(position_size, STANDARD_LOT), 2),
        position_size_mini=round(round_lot(position_size, MINI_LOT), 2),
        position_size_micro=round(round_lot(position_size, MICRO_LOT), 2),
        rr_ratio=round(rr_ratio, 2) if rr_ratio is not None else None,
        potential_profit=round(potential_profit, 2) if potential_profit is not None else None,
        potential_loss=round(risk_amount, 2),
        required_margin=required_margin,
        stop_loss_price_distance=price_distance,
        take_profit_price_distance=take_profit_price_distance,
        calculated_volume=round(position_size, 8),
        minimum_volume=float(preset.get("minimum_volume", 0.0)),
        volume_step=float(preset.get("volume_step", 0.0)),
        maximum_volume=float(preset.get("maximum_volume", 0.0)),
        tradable_volume=tradable_volume,
        volume_message=volume_message,
    )
    return result, []


# ── Private helpers ────────────────────────────────────────────────────

def _empty_result() -> CalculationResult:
    """Placeholder result returned when validation fails."""
    return CalculationResult(
        risk_amount=0.0,
        pip_value=0.0,
        position_size=0.0,
        position_size_standard=0.0,
        position_size_mini=0.0,
        position_size_micro=0.0,
        potential_loss=0.0,
    )
