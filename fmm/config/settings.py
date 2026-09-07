"""Application settings — single source of truth for defaults."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass

from ..core.constants import (
    ALLOWED_LEVERAGE,
    DEFAULT_BALANCE,
    DEFAULT_INSTRUMENT,
    DEFAULT_LEVERAGE,
    DEFAULT_PIP_VALUE_PER_LOT,
    DEFAULT_PRICE,
    DEFAULT_RISK_PCT,
    DEFAULT_STOP_LOSS_PIPS,
    DEFAULT_TAKE_PROFIT_PIPS,
    INSTRUMENT_LIST,
)

SETTINGS_FILE = os.path.join(
    os.path.expanduser("~"), ".config", "fmm", "settings.json"
)


@dataclass
class AppSettings:
    """Persistent application settings."""

    balance: float = DEFAULT_BALANCE
    risk_percent: float = DEFAULT_RISK_PCT
    stop_loss_pips: float = DEFAULT_STOP_LOSS_PIPS
    take_profit_pips: float = DEFAULT_TAKE_PROFIT_PIPS
    pip_value_per_lot: float = DEFAULT_PIP_VALUE_PER_LOT
    current_price: float = DEFAULT_PRICE
    instrument: str = DEFAULT_INSTRUMENT
    leverage: str = DEFAULT_LEVERAGE
    window_width: int = 960
    window_height: int = 720
    window_x: int = -1   # -1 = center on screen
    window_y: int = -1

    # ── Serialisation ──────────────────────────────────────────────

    def save(self) -> None:
        """Persist to disk (creates parent dirs as needed)."""
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
            json.dump(asdict(self), fh, indent=2)

    @classmethod
    def load(cls) -> AppSettings:
        """Load from disk, falling back to defaults.

        Handles:
        - missing settings file → defaults
        - corrupted file → defaults
        - newly added fields → sensible defaults
        - invalid enum/dropdown values → defaults
        """
        if not os.path.isfile(SETTINGS_FILE):
            return cls()
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            # Only accept known fields
            known = cls.__dataclass_fields__
            filtered = {k: v for k, v in data.items() if k in known}
            settings = cls(**filtered)
            # Validate dropdown selections
            if settings.instrument not in INSTRUMENT_LIST:
                settings.instrument = DEFAULT_INSTRUMENT
            if settings.leverage not in ALLOWED_LEVERAGE:
                settings.leverage = DEFAULT_LEVERAGE
            # Sanity-check numeric ranges
            settings.balance = max(0.01, settings.balance)
            settings.risk_percent = max(0.01, min(100.0, settings.risk_percent))
            settings.stop_loss_pips = max(0.1, settings.stop_loss_pips)
            settings.current_price = max(0.000001, settings.current_price)
            settings.window_width = max(860, settings.window_width)
            settings.window_height = max(620, settings.window_height)
            return settings
        except Exception:  # noqa: BLE001
            return cls()
