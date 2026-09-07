"""Forex constants, instrument presets, and application defaults."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Lot sizes
# ---------------------------------------------------------------------------
STANDARD_LOT: float = 1.0
MINI_LOT: float = 0.1
MICRO_LOT: float = 0.01

LOT_LABELS: dict[str, float] = {
    "Standard": STANDARD_LOT,
    "Mini": MINI_LOT,
    "Micro": MICRO_LOT,
}

# ---------------------------------------------------------------------------
# Pip sizes
# ---------------------------------------------------------------------------
PIP_SIZE_NORMAL: float = 0.0001  # Most currency pairs
PIP_SIZE_JPY: float = 0.01       # JPY-quoted pairs

# ---------------------------------------------------------------------------
# Leverage options (select-only, no arbitrary values)
# ---------------------------------------------------------------------------
ALLOWED_LEVERAGE: list[str] = [
    "1:1",
    "10:1",
    "20:1",
    "30:1",
    "50:1",
    "100:1",
    "200:1",
    "300:1",
    "500:1",
    "1000:1",
]

def leverage_to_float(leverage_str: str) -> float:
    """Convert a leverage string like '100:1' to its numeric value (100.0)."""
    try:
        return float(leverage_str.split(":")[0])
    except (ValueError, IndexError):
        return 1.0

def float_to_leverage(value: float) -> str:
    """Convert a numeric leverage back to display string, snapping to allowed values."""
    for opt in ALLOWED_LEVERAGE:
        if abs(leverage_to_float(opt) - value) < 0.01:
            return opt
    return "1:1"

# ---------------------------------------------------------------------------
# Instrument presets
# Each entry describes the contract and whether pip value depends on price.
#
# pip_value_per_standard_lot = USD value of 1 pip/tick for 1 standard lot.
# pip_multiplier = contract_size used to convert pip/tick size to dollar value.
#
# For forex: pip_multiplier = contract_size = 100 000 (1 pip × 100k = $10)
# For XAU/USD: tick = $0.01, pip_multiplier = 100 (100 ticks per $1, $100/lot)
# For DJI/USD: tick = 1 point, pip_multiplier = 1 ($1 per point per lot)
# ---------------------------------------------------------------------------
INSTRUMENT_PRESETS: dict[str, dict[str, float | bool | str]] = {
    "EUR/USD":  {"pip_value": 10.0, "pip_size": 0.0001, "point_size": 0.00001, "contract_size": 100_000, "pip_multiplier": 100_000, "dynamic_pip_value": False, "minimum_volume": 0.01, "volume_step": 0.01, "maximum_volume": 100.0},
    "GBP/USD":  {"pip_value": 10.0, "pip_size": 0.0001, "point_size": 0.00001, "contract_size": 100_000, "pip_multiplier": 100_000, "dynamic_pip_value": False, "minimum_volume": 0.01, "volume_step": 0.01, "maximum_volume": 100.0},
    "AUD/USD":  {"pip_value": 10.0, "pip_size": 0.0001, "point_size": 0.00001, "contract_size": 100_000, "pip_multiplier": 100_000, "dynamic_pip_value": False, "minimum_volume": 0.01, "volume_step": 0.01, "maximum_volume": 100.0},
    "NZD/USD":  {"pip_value": 10.0, "pip_size": 0.0001, "point_size": 0.00001, "contract_size": 100_000, "pip_multiplier": 100_000, "dynamic_pip_value": False, "minimum_volume": 0.01, "volume_step": 0.01, "maximum_volume": 100.0},
    "USD/CAD":  {"pip_size": 0.0001, "point_size": 0.00001, "contract_size": 100_000, "pip_multiplier": 100_000, "dynamic_pip_value": True, "minimum_volume": 0.01, "volume_step": 0.01, "maximum_volume": 100.0},
    "USD/CHF":  {"pip_size": 0.0001, "point_size": 0.00001, "contract_size": 100_000, "pip_multiplier": 100_000, "dynamic_pip_value": True, "minimum_volume": 0.01, "volume_step": 0.01, "maximum_volume": 100.0},
    "USD/JPY":  {"pip_size": 0.01, "point_size": 0.001, "contract_size": 100_000, "pip_multiplier": 100_000, "dynamic_pip_value": True, "minimum_volume": 0.01, "volume_step": 0.01, "maximum_volume": 100.0},
    "XAU/USD":  {"pip_size": 0.01, "point_size": 0.001, "contract_size": 100, "pip_multiplier": 100, "monetary_value_per_price_unit": 100.0, "dynamic_pip_value": False, "minimum_volume": 0.01, "volume_step": 0.01, "maximum_volume": 100.0},
    "DJI/USD":  {"pip_size": 1.0, "point_size": 0.1, "contract_size": 1, "pip_multiplier": 1, "monetary_value_per_price_unit": 1.0, "dynamic_pip_value": False, "minimum_volume": 0.01, "volume_step": 0.01, "maximum_volume": 100.0},
    "Custom":   {"pip_size": 0.0001, "point_size": 0.00001, "contract_size": 100_000, "pip_multiplier": 100_000, "dynamic_pip_value": False, "minimum_volume": 0.01, "volume_step": 0.01, "maximum_volume": 100.0},
}

# Ordered list for UI dropdown — matches INSTRUMENT_PRESETS keys exactly.
INSTRUMENT_LIST: list[str] = [
    "EUR/USD",
    "GBP/USD",
    "AUD/USD",
    "NZD/USD",
    "USD/CAD",
    "USD/CHF",
    "USD/JPY",
    "XAU/USD",
    "DJI/USD",
    "Custom",
]

# ---------------------------------------------------------------------------
# Approximate mid-market prices for notional/margin estimation
# (Used only when live prices are unavailable — clearly approximate.)
# ---------------------------------------------------------------------------
APPROX_PRICES: dict[str, float] = {
    "EUR/USD":  1.08,
    "GBP/USD":  1.27,
    "AUD/USD":  0.65,
    "NZD/USD":  0.60,
    "USD/CAD":  1.36,
    "USD/CHF":  0.88,
    "USD/JPY":  155.0,
    "XAU/USD":  2400.0,
    "DJI/USD":  40_000.0,
}

# ---------------------------------------------------------------------------
# Default values
# ---------------------------------------------------------------------------
DEFAULT_BALANCE: float = 10_000.0
DEFAULT_RISK_PCT: float = 1.0
DEFAULT_STOP_LOSS_PIPS: float = 25.0
DEFAULT_TAKE_PROFIT_PIPS: float = 50.0  # Defaults to 2× SL
DEFAULT_PIP_VALUE_PER_LOT: float = 10.0
DEFAULT_INSTRUMENT: str = "EUR/USD"
DEFAULT_PRICE: float = APPROX_PRICES[DEFAULT_INSTRUMENT]
DEFAULT_LEVERAGE: str = "100:1"

# ---------------------------------------------------------------------------
# Lot-size rounding increments
# ---------------------------------------------------------------------------
LOT_STEP_MICRO: float = 0.01
LOT_STEP_MINI: float = 0.1
LOT_STEP_STANDARD: float = 1.0

# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------
APP_NAME: str = "Forex Money Manager"
APP_VERSION: str = "1.0.0"
