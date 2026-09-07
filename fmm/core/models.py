"""Data models for trade parameters and calculation results.

These are plain dataclasses with zero GUI dependency so the calculation
engine can be used independently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .constants import DEFAULT_LEVERAGE, leverage_to_float


@dataclass
class TradeSetup:
    """All user-supplied inputs for a single trade calculation."""

    balance: float
    risk_percent: float
    stop_loss_pips: float
    pip_value_per_lot: float
    take_profit_pips: float | None = None
    instrument: str = "EUR/USD"
    leverage: str = DEFAULT_LEVERAGE
    pip_multiplier: float = 100_000.0  # contract-size factor for margin calc
    current_price: float | None = None
    stop_loss_points: float | None = None
    take_profit_points: float | None = None

    def __post_init__(self) -> None:
        """Coerce string inputs that arrive from GUI spin-box text."""
        for attr in (
            "balance", "risk_percent", "stop_loss_pips", "pip_value_per_lot",
            "current_price", "stop_loss_points", "take_profit_points",
        ):
            val = getattr(self, attr)
            if isinstance(val, str):
                object.__setattr__(self, attr, float(val) if val else 0.0)
        if self.take_profit_pips is not None and isinstance(self.take_profit_pips, str):
            raw = self.take_profit_pips
            object.__setattr__(
                self, "take_profit_pips", float(raw) if raw else None
            )

    @property
    def leverage_float(self) -> float:
        """Numeric leverage value (e.g. 100.0 for '100:1')."""
        return leverage_to_float(self.leverage)


@dataclass
class CalculationResult:
    """Output of a position-sizing calculation."""

    risk_amount: float          # Dollar amount at risk
    pip_value: float            # Dollar value per pip in this trade
    position_size: float        # Recommended position size in lots
    position_size_standard: float  # Rounded to standard lots
    position_size_mini: float      # Rounded to mini lots
    position_size_micro: float     # Rounded to micro lots
    rr_ratio: float | None = None       # Risk : Reward ratio
    potential_profit: float | None = None
    potential_loss: float = 0.0  # Same as risk_amount
    required_margin: float | None = None  # Approximate margin requirement
    stop_loss_price_distance: float | None = None
    take_profit_price_distance: float | None = None
    calculated_volume: float | None = None
    minimum_volume: float | None = None
    volume_step: float | None = None
    maximum_volume: float | None = None
    tradable_volume: float | None = None
    volume_message: str | None = None


@dataclass
class HistoryEntry:
    """A single saved calculation for the history table."""

    timestamp: datetime = field(default_factory=datetime.now)
    setup: TradeSetup = field(default_factory=lambda: TradeSetup(
        balance=0, risk_percent=0, stop_loss_pips=0, pip_value_per_lot=0,
    ))
    result: CalculationResult = field(default_factory=lambda: CalculationResult(
        risk_amount=0, pip_value=0, position_size=0,
        position_size_standard=0, position_size_mini=0, position_size_micro=0,
    ))

    @property
    def net_rr_value(self) -> float | None:
        """Potential profit minus potential loss (expectancy hint)."""
        if self.result.potential_profit is not None:
            return self.result.potential_profit - self.result.potential_loss
        return None
