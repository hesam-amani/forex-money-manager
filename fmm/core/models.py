"""Data models for FMM."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TradeSetup:
    """User inputs for one position-sizing calculation."""

    balance: float
    risk_percent: float
    stop_loss_pips: float
    pip_value_per_lot: float
    take_profit_pips: float | None = None

    def __post_init__(self) -> None:
        for name in (
            "balance",
            "risk_percent",
            "stop_loss_pips",
            "pip_value_per_lot",
            "take_profit_pips",
        ):
            value = getattr(self, name)
            if isinstance(value, str):
                object.__setattr__(self, name, float(value) if value else None)


@dataclass
class CalculationResult:
    """Outputs produced by the position-sizing calculation."""

    risk_amount: float
    pip_value: float
    position_size: float
    rr_ratio: float | None = None
    potential_profit: float | None = None
    potential_loss: float = 0.0


@dataclass
class HistoryEntry:
    """A saved calculation for the history table."""

    timestamp: datetime = field(default_factory=datetime.now)
    setup: TradeSetup = field(default_factory=lambda: TradeSetup(
        balance=0,
        risk_percent=0,
        stop_loss_pips=0,
        pip_value_per_lot=0,
    ))
    result: CalculationResult = field(default_factory=lambda: CalculationResult(
        risk_amount=0,
        pip_value=0,
        position_size=0,
    ))
