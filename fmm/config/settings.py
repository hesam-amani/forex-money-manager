"""Persistent application settings."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass

from ..core.constants import (
    DEFAULT_BALANCE,
    DEFAULT_PIP_VALUE_PER_LOT,
    DEFAULT_RISK_PCT,
    DEFAULT_STOP_LOSS_PIPS,
    DEFAULT_TAKE_PROFIT_PIPS,
)

SETTINGS_FILE = os.path.join(
    os.path.expanduser("~"), ".config", "fmm", "settings.json"
)


@dataclass
class AppSettings:
    balance: float = DEFAULT_BALANCE
    risk_percent: float = DEFAULT_RISK_PCT
    stop_loss_pips: float = DEFAULT_STOP_LOSS_PIPS
    take_profit_pips: float = DEFAULT_TAKE_PROFIT_PIPS
    pip_value_per_lot: float = DEFAULT_PIP_VALUE_PER_LOT
    window_width: int = 960
    window_height: int = 720
    window_x: int = -1
    window_y: int = -1

    def save(self) -> None:
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
            json.dump(asdict(self), fh, indent=2)

    @classmethod
    def load(cls) -> AppSettings:
        if not os.path.isfile(SETTINGS_FILE):
            return cls()
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            known = cls.__dataclass_fields__
            settings = cls(**{k: v for k, v in data.items() if k in known})
            settings.balance = max(0.01, settings.balance)
            settings.risk_percent = max(0.01, min(100.0, settings.risk_percent))
            settings.stop_loss_pips = max(0.01, settings.stop_loss_pips)
            settings.pip_value_per_lot = max(0.01, settings.pip_value_per_lot)
            if settings.take_profit_pips is not None:
                settings.take_profit_pips = max(0.0, settings.take_profit_pips)
            settings.window_width = max(760, settings.window_width)
            settings.window_height = max(700, settings.window_height)
            return settings
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            return cls()
