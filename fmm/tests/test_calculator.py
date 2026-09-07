"""Tests for the simplified broker-independent position-sizing engine."""

from __future__ import annotations

import os
import tempfile

import pytest

from fmm.config.settings import AppSettings
from fmm.core.calculator import (
    calculate_pip_value,
    calculate_position_size,
    calculate_potential_profit,
    calculate_risk_amount,
    calculate_rr_ratio,
    compute_trade,
)
from fmm.core.models import TradeSetup


class TestRiskAmount:
    @pytest.mark.parametrize(
        ("balance", "risk", "expected"),
        [(10_000, 1, 100), (10_000, 2, 200), (50_000, 0.5, 250), (100, 5, 5)],
    )
    def test_calculation(self, balance: float, risk: float, expected: float) -> None:
        assert calculate_risk_amount(balance, risk) == expected


class TestCoreFormulas:
    def test_pip_value(self) -> None:
        assert calculate_pip_value(100, 25) == 4

    def test_position_size(self) -> None:
        assert calculate_position_size(4, 10) == 0.4

    def test_invalid_values_raise(self) -> None:
        with pytest.raises(ValueError):
            calculate_pip_value(100, 0)
        with pytest.raises(ValueError):
            calculate_position_size(4, 0)

    def test_rr(self) -> None:
        assert calculate_rr_ratio(50, 25) == 2
        assert calculate_rr_ratio(None, 25) is None

    def test_profit(self) -> None:
        assert calculate_potential_profit(0.4, 10, 50) == 200
        assert calculate_potential_profit(0.4, 10, None) is None


class TestComputeTrade:
    def test_standard_example(self) -> None:
        result, errors = compute_trade(TradeSetup(10_000, 1, 25, 10, 50))
        assert errors == []
        assert result.risk_amount == 100
        assert result.pip_value == 4
        assert result.position_size == 0.4
        assert result.rr_ratio == 2
        assert result.potential_profit == 200
        assert result.potential_loss == 100

    def test_different_broker_pip_values(self) -> None:
        setup = TradeSetup(10_000, 1, 25, 7.5, 50)
        result, errors = compute_trade(setup)
        assert errors == []
        assert result.position_size == pytest.approx(0.533333, rel=1e-5)
        assert result.potential_profit == pytest.approx(200)

    def test_no_take_profit(self) -> None:
        result, errors = compute_trade(TradeSetup(10_000, 1, 25, 10))
        assert errors == []
        assert result.rr_ratio is None
        assert result.potential_profit is None

    def test_validation(self) -> None:
        result, errors = compute_trade(TradeSetup(0, 1, 25, 10))
        assert result.position_size == 0
        assert any("balance" in error.lower() for error in errors)

    @pytest.mark.parametrize("risk", [0.01, 0.25, 1, 2, 10])
    def test_risk_scales_linearly(self, risk: float) -> None:
        result, errors = compute_trade(TradeSetup(10_000, risk, 25, 10))
        assert errors == []
        assert result.position_size == pytest.approx(risk / 25 * 100)


class TestSettings:
    def test_roundtrip(self) -> None:
        import fmm.config.settings as config

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "settings.json")
            original = config.SETTINGS_FILE
            try:
                config.SETTINGS_FILE = path
                saved = AppSettings(balance=12_500, risk_percent=1.5, stop_loss_pips=35, take_profit_pips=70, pip_value_per_lot=8.25)
                saved.save()
                loaded = AppSettings.load()
                assert loaded.balance == 12_500
                assert loaded.risk_percent == 1.5
                assert loaded.stop_loss_pips == 35
                assert loaded.take_profit_pips == 70
                assert loaded.pip_value_per_lot == 8.25
            finally:
                config.SETTINGS_FILE = original

    def test_missing_file_uses_defaults(self) -> None:
        import fmm.config.settings as config
        with tempfile.TemporaryDirectory() as tmp:
            original = config.SETTINGS_FILE
            try:
                config.SETTINGS_FILE = os.path.join(tmp, "missing.json")
                assert AppSettings.load().balance == 10_000
            finally:
                config.SETTINGS_FILE = original
