"""JSON persistence for calculation history."""

from __future__ import annotations

import json
import os
from datetime import datetime

from ..core.models import CalculationResult, HistoryEntry, TradeSetup

HISTORY_DIR = os.path.join(os.path.expanduser("~"), ".config", "fmm")
HISTORY_FILE = os.path.join(HISTORY_DIR, "history.json")
MAX_HISTORY_ENTRIES = 100


class StorageService:
    """Load and save the user's calculation history."""

    def __init__(self, path: str = HISTORY_FILE) -> None:
        self._path = path
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def load_history(self) -> list[HistoryEntry]:
        if not os.path.isfile(self._path):
            return []
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
            entries: list[HistoryEntry] = []
            for item in raw:
                setup = TradeSetup(
                    balance=item["balance"],
                    risk_percent=item["risk_percent"],
                    stop_loss_pips=item["stop_loss_pips"],
                    pip_value_per_lot=item["pip_value_per_lot"],
                    take_profit_pips=item.get("take_profit_pips"),
                )
                result = CalculationResult(
                    risk_amount=item["risk_amount"],
                    pip_value=item["pip_value"],
                    position_size=item["position_size"],
                    rr_ratio=item.get("rr_ratio"),
                    potential_profit=item.get("potential_profit"),
                    potential_loss=item.get("potential_loss", 0),
                )
                entries.append(HistoryEntry(
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    setup=setup,
                    result=result,
                ))
            return entries[-MAX_HISTORY_ENTRIES:]
        except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError):
            return []

    def save_history(self, entries: list[HistoryEntry]) -> None:
        raw = []
        for entry in entries[-MAX_HISTORY_ENTRIES:]:
            raw.append({
                "timestamp": entry.timestamp.isoformat(),
                "balance": entry.setup.balance,
                "risk_percent": entry.setup.risk_percent,
                "stop_loss_pips": entry.setup.stop_loss_pips,
                "pip_value_per_lot": entry.setup.pip_value_per_lot,
                "take_profit_pips": entry.setup.take_profit_pips,
                "risk_amount": entry.result.risk_amount,
                "pip_value": entry.result.pip_value,
                "position_size": entry.result.position_size,
                "rr_ratio": entry.result.rr_ratio,
                "potential_profit": entry.result.potential_profit,
                "potential_loss": entry.result.potential_loss,
            })
        parent = os.path.dirname(self._path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(raw, fh, indent=2)

    def clear_history(self) -> None:
        if os.path.isfile(self._path):
            os.remove(self._path)
