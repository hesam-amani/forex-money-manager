"""Persistence service — history and settings storage."""

from __future__ import annotations

import json
import os
from datetime import datetime

from ..core.constants import DEFAULT_LEVERAGE
from ..core.models import CalculationResult, HistoryEntry, TradeSetup

HISTORY_DIR = os.path.join(os.path.expanduser("~"), ".config", "fmm")
HISTORY_FILE = os.path.join(HISTORY_DIR, "history.json")

MAX_HISTORY_ENTRIES = 100


class StorageService:
    """Handles saving/loading calculation history to disk."""

    def __init__(self, path: str = HISTORY_FILE) -> None:
        self._path = path
        os.makedirs(os.path.dirname(self._path), exist_ok=True)

    # ── History ─────────────────────────────────────────────────────

    def load_history(self) -> list[HistoryEntry]:
        """Load history entries from disk.

        Gracefully handles entries saved by older versions that lack
        leverage or required_margin fields.
        """
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
                    instrument=item.get("instrument", "Custom"),
                    leverage=item.get("leverage", DEFAULT_LEVERAGE),
                    pip_multiplier=float(item.get("pip_multiplier", 100_000)),
                    current_price=item.get("current_price"),
                    stop_loss_points=item.get("stop_loss_points"),
                    take_profit_points=item.get("take_profit_points"),
                )
                result = CalculationResult(
                    risk_amount=item["risk_amount"],
                    pip_value=item["pip_value"],
                    position_size=item["position_size"],
                    position_size_standard=item.get("position_size_standard", 0),
                    position_size_mini=item.get("position_size_mini", 0),
                    position_size_micro=item.get("position_size_micro", 0),
                    rr_ratio=item.get("rr_ratio"),
                    potential_profit=item.get("potential_profit"),
                    potential_loss=item.get("potential_loss", 0),
                    required_margin=item.get("required_margin"),
                )
                ts = datetime.fromisoformat(item["timestamp"])
                entries.append(HistoryEntry(timestamp=ts, setup=setup, result=result))
            return entries
        except Exception:  # noqa: BLE001
            return []

    def save_history(self, entries: list[HistoryEntry]) -> None:
        """Persist history entries to disk."""
        # Trim to max size
        entries = entries[-MAX_HISTORY_ENTRIES:]
        raw = []
        for e in entries:
            raw.append({
                "timestamp": e.timestamp.isoformat(),
                "balance": e.setup.balance,
                "risk_percent": e.setup.risk_percent,
                "stop_loss_pips": e.setup.stop_loss_pips,
                "pip_value_per_lot": e.setup.pip_value_per_lot,
                "take_profit_pips": e.setup.take_profit_pips,
                "instrument": e.setup.instrument,
                "leverage": e.setup.leverage,
                "pip_multiplier": e.setup.pip_multiplier,
                "current_price": e.setup.current_price,
                "stop_loss_points": e.setup.stop_loss_points,
                "take_profit_points": e.setup.take_profit_points,
                "risk_amount": e.result.risk_amount,
                "pip_value": e.result.pip_value,
                "position_size": e.result.position_size,
                "position_size_standard": e.result.position_size_standard,
                "position_size_mini": e.result.position_size_mini,
                "position_size_micro": e.result.position_size_micro,
                "rr_ratio": e.result.rr_ratio,
                "potential_profit": e.result.potential_profit,
                "potential_loss": e.result.potential_loss,
                "required_margin": e.result.required_margin,
            })
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(raw, fh, indent=2)

    def clear_history(self) -> None:
        """Remove all saved history."""
        if os.path.isfile(self._path):
            os.remove(self._path)
