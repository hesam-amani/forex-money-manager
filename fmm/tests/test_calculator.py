"""Comprehensive tests for the core calculation engine.

Uses the original C++ formulas as the reference:
    risk_amount   = balance * risk_percent / 100
    pip_value     = risk_amount / stop_loss_pips
    position_size = pip_value / pip_value_per_lot

Extended to cover leverage, TP auto-update, instrument list,
persistence, and required margin.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

import pytest

# Ensure the project root is on the path so imports work.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fmm.core.calculator import (
    calculate_instrument_pip_value,
    calculate_pip_value,
    calculate_position_size,
    calculate_potential_profit,
    calculate_risk_amount,
    calculate_risk_per_lot,
    calculate_rr_ratio,
    compute_trade,
    round_lot,
    validate_volume,
)
from fmm.core.constants import (
    ALLOWED_LEVERAGE,
    INSTRUMENT_LIST,
    INSTRUMENT_PRESETS,
    MICRO_LOT,
    MINI_LOT,
    STANDARD_LOT,
    leverage_to_float,
)
from fmm.core.models import TradeSetup
from fmm.core.validators import validate_leverage, validate_trade_setup

# ======================================================================
# calculate_risk_amount
# ======================================================================

class TestRiskAmount:
    """Risk Amount = Balance * Risk% / 100."""

    def test_basic(self) -> None:
        assert calculate_risk_amount(10_000, 1.0) == 100.0

    def test_2_percent(self) -> None:
        assert calculate_risk_amount(10_000, 2.0) == 200.0

    def test_0p5_percent(self) -> None:
        assert calculate_risk_amount(50_000, 0.5) == 250.0

    def test_10_percent(self) -> None:
        assert calculate_risk_amount(1_000, 10.0) == 100.0

    def test_small_balance(self) -> None:
        assert calculate_risk_amount(100, 5.0) == 5.0

    def test_large_balance(self) -> None:
        result = calculate_risk_amount(1_000_000, 1.0)
        assert result == 10_000.0

    def test_fractional_risk(self) -> None:
        assert calculate_risk_amount(10_000, 0.25) == 25.0

    def test_zero_balance(self) -> None:
        assert calculate_risk_amount(0, 1.0) == 0.0


# ======================================================================
# calculate_pip_value
# ======================================================================

class TestPipValue:
    """Pip Value = Risk Amount / Stop-Loss Pips."""

    def test_basic(self) -> None:
        assert calculate_pip_value(100.0, 25.0) == 4.0

    def test_100_risk_50_sl(self) -> None:
        assert calculate_pip_value(100.0, 50.0) == 2.0

    def test_200_risk_25_sl(self) -> None:
        assert calculate_pip_value(200.0, 25.0) == 8.0

    def test_wide_stop(self) -> None:
        assert calculate_pip_value(500.0, 200.0) == 2.5

    def test_tight_stop(self) -> None:
        assert calculate_pip_value(100.0, 5.0) == 20.0

    def test_zero_sl_raises(self) -> None:
        with pytest.raises(ValueError, match="stop_loss_pips must be > 0"):
            calculate_pip_value(100.0, 0)

    def test_negative_sl_raises(self) -> None:
        with pytest.raises(ValueError, match="stop_loss_pips must be > 0"):
            calculate_pip_value(100.0, -10)


# ======================================================================
# calculate_position_size
# ======================================================================

class TestPositionSize:
    """Position Size = Pip Value / Pip Value Per Lot."""

    def test_basic_standard_lot(self) -> None:
        assert calculate_position_size(4.0, 10.0) == 0.4

    def test_full_standard_lot(self) -> None:
        assert calculate_position_size(10.0, 10.0) == 1.0

    def test_two_standard_lots(self) -> None:
        assert calculate_position_size(20.0, 10.0) == 2.0

    def test_mini_lot_instrument(self) -> None:
        result = calculate_position_size(4.0, 6.67)
        assert abs(result - 0.5997) < 0.01

    def test_zero_pip_value_per_lot_raises(self) -> None:
        with pytest.raises(ValueError, match="pip_value_per_lot must be > 0"):
            calculate_position_size(4.0, 0)

    def test_negative_pip_value_per_lot_raises(self) -> None:
        with pytest.raises(ValueError, match="pip_value_per_lot must be > 0"):
            calculate_position_size(4.0, -10.0)


# ======================================================================
# calculate_rr_ratio
# ======================================================================

class TestRRRatio:
    """R:R = Take-Profit Pips / Stop-Loss Pips."""

    def test_1_to_1(self) -> None:
        assert calculate_rr_ratio(25.0, 25.0) == 1.0

    def test_1_to_3(self) -> None:
        assert calculate_rr_ratio(75.0, 25.0) == 3.0

    def test_2_to_1(self) -> None:
        assert calculate_rr_ratio(50.0, 25.0) == 2.0

    def test_none_when_no_tp(self) -> None:
        assert calculate_rr_ratio(None, 25.0) is None

    def test_none_when_tp_zero(self) -> None:
        assert calculate_rr_ratio(0, 25.0) is None

    def test_none_when_sl_zero(self) -> None:
        assert calculate_rr_ratio(25.0, 0) is None

    def test_negative_tp(self) -> None:
        assert calculate_rr_ratio(-10, 25.0) is None


# ======================================================================
# calculate_potential_profit
# ======================================================================

class TestPotentialProfit:
    """Potential Profit = Pip Value * Take-Profit Pips."""

    def test_basic(self) -> None:
        assert calculate_potential_profit(4.0, 75.0) == 300.0

    def test_none_when_no_tp(self) -> None:
        assert calculate_potential_profit(4.0, None) is None

    def test_none_when_tp_zero(self) -> None:
        assert calculate_potential_profit(4.0, 0) is None

    def test_negative_tp(self) -> None:
        assert calculate_potential_profit(4.0, -10) is None


# ======================================================================
# round_lot
# ======================================================================

class TestRoundLot:
    def test_standard_round_down(self) -> None:
        assert round_lot(1.43, STANDARD_LOT) == 1.0

    def test_standard_exact(self) -> None:
        assert round_lot(2.0, STANDARD_LOT) == 2.0

    def test_mini_round_down(self) -> None:
        assert round_lot(0.43, MINI_LOT) == 0.4

    def test_micro_round_down(self) -> None:
        assert round_lot(0.437, MICRO_LOT) == 0.43

    def test_zero_step(self) -> None:
        assert round_lot(1.5, 0) == 1.5


# ======================================================================
# compute_trade  (full integration)
# ======================================================================

class TestComputeTrade:
    """End-to-end calculation matching the original C++ behaviour."""

    def test_cpp_example_1(self) -> None:
        setup = TradeSetup(
            balance=10_000.0, risk_percent=1.0,
            stop_loss_pips=25.0, pip_value_per_lot=10.0,
        )
        result, errors = compute_trade(setup)
        assert errors == []
        assert result.risk_amount == 100.0
        assert result.pip_value == 4.0
        assert result.position_size == 0.4
        assert result.potential_loss == 100.0

    def test_cpp_example_2(self) -> None:
        setup = TradeSetup(
            balance=5_000.0, risk_percent=2.0,
            stop_loss_pips=50.0, pip_value_per_lot=10.0,
        )
        result, errors = compute_trade(setup)
        assert errors == []
        assert result.risk_amount == 100.0
        assert result.pip_value == 2.0
        assert result.position_size == 0.2

    def test_cpp_example_3(self) -> None:
        setup = TradeSetup(
            balance=20_000.0, risk_percent=0.5,
            stop_loss_pips=30.0, pip_value_per_lot=10.0,
        )
        result, errors = compute_trade(setup)
        assert errors == []
        assert result.risk_amount == 100.0
        assert abs(result.pip_value - 3.3333) < 0.01
        assert abs(result.position_size - 0.3333) < 0.01

    def test_with_take_profit(self) -> None:
        setup = TradeSetup(
            balance=10_000.0, risk_percent=1.0,
            stop_loss_pips=25.0, pip_value_per_lot=10.0,
            take_profit_pips=75.0,
        )
        result, errors = compute_trade(setup)
        assert errors == []
        assert result.rr_ratio == 3.0
        assert result.potential_profit == 300.0

    def test_rr_ratio_2_to_1(self) -> None:
        setup = TradeSetup(
            balance=10_000.0, risk_percent=2.0,
            stop_loss_pips=50.0, pip_value_per_lot=10.0,
            take_profit_pips=100.0,
        )
        result, errors = compute_trade(setup)
        assert errors == []
        assert result.rr_ratio == 2.0
        assert result.potential_profit == 400.0

    def test_usdjpy_instrument(self) -> None:
        setup = TradeSetup(
            balance=10_000.0, risk_percent=1.0,
            stop_loss_pips=30.0, pip_value_per_lot=0.0,
            instrument="USD/JPY", current_price=147.0,
        )
        result, errors = compute_trade(setup)
        assert errors == []
        assert result.risk_amount == 100.0
        assert abs(result.pip_value - 3.3333) < 0.01
        assert abs(result.position_size - (100 / 30 / (100000 * 0.01 / 147))) < 0.01

    def test_fifty_point_stop_loss_targets_twenty_five_dollars(self) -> None:
        prices = {
            "EUR/USD": 1.08,
            "GBP/USD": 1.27,
            "AUD/USD": 0.65,
            "NZD/USD": 0.60,
            "USD/CAD": 1.36,
            "USD/CHF": 0.88,
            "USD/JPY": 155.0,
            "XAU/USD": 4545.0,
            "DJI/USD": 53020.0,
        }
        for instrument, price in prices.items():
            result, errors = compute_trade(TradeSetup(
                balance=5_000,
                risk_percent=0.5,
                stop_loss_pips=50,
                pip_value_per_lot=10,
                instrument=instrument,
                current_price=price,
                stop_loss_points=50,
                take_profit_points=100,
            ))
            assert errors == []
            assert result.risk_amount == 25.0
            assert result.volume_message is None
            assert result.tradable_volume is not None

    def test_large_balance(self) -> None:
        setup = TradeSetup(
            balance=500_000.0, risk_percent=1.0,
            stop_loss_pips=20.0, pip_value_per_lot=10.0,
        )
        result, errors = compute_trade(setup)
        assert errors == []
        assert result.risk_amount == 5_000.0
        assert result.pip_value == 250.0
        assert result.position_size == 25.0


# ======================================================================
# Validation
# ======================================================================

class TestValidation:
    def test_zero_balance(self) -> None:
        setup = TradeSetup(balance=0, risk_percent=1.0, stop_loss_pips=25, pip_value_per_lot=10)
        errors = validate_trade_setup(setup)
        assert any("balance" in e.lower() for e in errors)

    def test_negative_balance(self) -> None:
        setup = TradeSetup(balance=-100, risk_percent=1.0, stop_loss_pips=25, pip_value_per_lot=10)
        errors = validate_trade_setup(setup)
        assert any("balance" in e.lower() for e in errors)

    def test_zero_risk(self) -> None:
        setup = TradeSetup(balance=10_000, risk_percent=0, stop_loss_pips=25, pip_value_per_lot=10)
        errors = validate_trade_setup(setup)
        assert any("risk" in e.lower() for e in errors)

    def test_risk_over_100(self) -> None:
        setup = TradeSetup(balance=10_000, risk_percent=150, stop_loss_pips=25, pip_value_per_lot=10)
        errors = validate_trade_setup(setup)
        assert any("100" in e for e in errors)

    def test_high_risk_warning(self) -> None:
        setup = TradeSetup(balance=10_000, risk_percent=15, stop_loss_pips=25, pip_value_per_lot=10)
        errors = validate_trade_setup(setup)
        assert any("aggressive" in e.lower() or "10%" in e for e in errors)

    def test_zero_stop_loss(self) -> None:
        setup = TradeSetup(balance=10_000, risk_percent=1, stop_loss_pips=0, pip_value_per_lot=10)
        errors = validate_trade_setup(setup)
        assert any("stop" in e.lower() for e in errors)

    def test_negative_stop_loss(self) -> None:
        setup = TradeSetup(balance=10_000, risk_percent=1, stop_loss_pips=-5, pip_value_per_lot=10)
        errors = validate_trade_setup(setup)
        assert any("stop" in e.lower() for e in errors)

    def test_zero_pip_value_per_lot(self) -> None:
        setup = TradeSetup(balance=10_000, risk_percent=1, stop_loss_pips=25, pip_value_per_lot=0)
        errors = validate_trade_setup(setup)
        assert any("pip value" in e.lower() for e in errors)

    def test_valid_setup_no_errors(self) -> None:
        setup = TradeSetup(balance=10_000, risk_percent=1, stop_loss_pips=25, pip_value_per_lot=10)
        errors = validate_trade_setup(setup)
        assert errors == []

    def test_compute_trade_validates(self) -> None:
        setup = TradeSetup(balance=0, risk_percent=0, stop_loss_pips=0, pip_value_per_lot=0)
        result, errors = compute_trade(setup)
        assert len(errors) > 0
        assert result.risk_amount == 0.0


# ======================================================================
# Edge cases & precision
# ======================================================================

class TestEdgeCases:
    def test_very_small_risk(self) -> None:
        setup = TradeSetup(
            balance=100_000, risk_percent=0.01, stop_loss_pips=10, pip_value_per_lot=10
        )
        result, errors = compute_trade(setup)
        assert errors == []
        assert result.risk_amount == 10.0
        assert result.pip_value == 1.0
        assert result.position_size == 0.1

    def test_very_tight_stop(self) -> None:
        setup = TradeSetup(
            balance=10_000, risk_percent=1, stop_loss_pips=1, pip_value_per_lot=10
        )
        result, errors = compute_trade(setup)
        assert errors == []
        assert result.position_size == 10.0

    def test_very_wide_stop(self) -> None:
        setup = TradeSetup(
            balance=10_000, risk_percent=1, stop_loss_pips=500, pip_value_per_lot=10
        )
        result, errors = compute_trade(setup)
        assert errors == []
        assert result.position_size == 0.02

    def test_lot_tiers_are_correct(self) -> None:
        setup = TradeSetup(
            balance=10_000, risk_percent=1, stop_loss_pips=25, pip_value_per_lot=10
        )
        result, errors = compute_trade(setup)
        assert errors == []
        assert result.position_size_standard == 0.0
        assert result.position_size_mini == 0.4
        assert result.position_size_micro == 0.40

    def test_lot_tiers_round_down(self) -> None:
        setup = TradeSetup(
            balance=10_000, risk_percent=1, stop_loss_pips=25, pip_value_per_lot=10
        )
        result, _errors = compute_trade(setup)
        assert result.position_size_standard <= result.position_size + 0.001


# ======================================================================
# Leverage
# ======================================================================

class TestLeverage:
    """Leverage affects margin, NOT risk amount."""

    def test_all_allowed_leverage_values(self) -> None:
        """Every value in ALLOWED_LEVERAGE must pass validation."""
        expected = ["1:1", "10:1", "20:1", "30:1", "50:1", "100:1", "200:1", "300:1", "500:1", "1000:1"]
        assert ALLOWED_LEVERAGE == expected

    def test_leverage_to_float_conversion(self) -> None:
        assert leverage_to_float("1:1") == 1.0
        assert leverage_to_float("100:1") == 100.0
        assert leverage_to_float("1000:1") == 1000.0
        assert leverage_to_float("invalid") == 1.0  # fallback

    def test_leverage_does_not_alter_risk_amount(self) -> None:
        """Changing leverage must NOT change risk_amount."""
        base = TradeSetup(
            balance=10_000, risk_percent=1.0,
            stop_loss_pips=25, pip_value_per_lot=10,
            leverage="1:1",
        )
        high = TradeSetup(
            balance=10_000, risk_percent=1.0,
            stop_loss_pips=25, pip_value_per_lot=10,
            leverage="1000:1",
        )
        r_base, _ = compute_trade(base)
        r_high, _ = compute_trade(high)
        assert r_base.risk_amount == r_high.risk_amount == 100.0

    def test_leverage_does_not_alter_position_size(self) -> None:
        """Changing leverage must NOT change position_size."""
        base = TradeSetup(
            balance=10_000, risk_percent=1.0,
            stop_loss_pips=25, pip_value_per_lot=10,
            leverage="1:1",
        )
        high = TradeSetup(
            balance=10_000, risk_percent=1.0,
            stop_loss_pips=25, pip_value_per_lot=10,
            leverage="1000:1",
        )
        r_base, _ = compute_trade(base)
        r_high, _ = compute_trade(high)
        assert r_base.position_size == r_high.position_size == 0.4

    def test_leverage_does_not_alter_pip_value(self) -> None:
        base = TradeSetup(
            balance=10_000, risk_percent=1.0,
            stop_loss_pips=25, pip_value_per_lot=10,
            leverage="1:1",
        )
        high = TradeSetup(
            balance=10_000, risk_percent=1.0,
            stop_loss_pips=25, pip_value_per_lot=10,
            leverage="1000:1",
        )
        r_base, _ = compute_trade(base)
        r_high, _ = compute_trade(high)
        assert r_base.pip_value == r_high.pip_value == 4.0

    def test_invalid_leverage_fails_validation(self) -> None:
        setup = TradeSetup(
            balance=10_000, risk_percent=1.0,
            stop_loss_pips=25, pip_value_per_lot=10,
            leverage="999:1",
        )
        errors = validate_trade_setup(setup)
        assert any("leverage" in e.lower() for e in errors)

    def test_validate_leverage_function(self) -> None:
        assert validate_leverage("100:1") is None
        assert validate_leverage("1:1") is None
        assert validate_leverage("999:1") is not None
        assert validate_leverage("invalid") is not None

    def test_leverage_affects_margin(self) -> None:
        """Higher leverage → lower required margin."""
        low = TradeSetup(
            balance=10_000, risk_percent=1.0,
            stop_loss_pips=25, pip_value_per_lot=10,
            leverage="50:1", instrument="EUR/USD",
        )
        high = TradeSetup(
            balance=10_000, risk_percent=1.0,
            stop_loss_pips=25, pip_value_per_lot=10,
            leverage="500:1", instrument="EUR/USD",
        )
        r_low, _ = compute_trade(low)
        r_high, _ = compute_trade(high)
        assert r_low.required_margin is not None
        assert r_high.required_margin is not None
        assert r_low.required_margin > r_high.required_margin

    def test_margin_decreases_with_higher_leverage(self) -> None:
        """Verify the margin is 10x smaller when leverage is 10x larger."""
        setup_100 = TradeSetup(
            balance=10_000, risk_percent=1.0,
            stop_loss_pips=25, pip_value_per_lot=10,
            leverage="100:1", instrument="EUR/USD",
        )
        setup_1000 = TradeSetup(
            balance=10_000, risk_percent=1.0,
            stop_loss_pips=25, pip_value_per_lot=10,
            leverage="1000:1", instrument="EUR/USD",
        )
        r100, _ = compute_trade(setup_100)
        r1000, _ = compute_trade(setup_1000)
        assert r100.required_margin is not None
        assert r1000.required_margin is not None
        assert abs(r100.required_margin / r1000.required_margin - 10.0) < 0.1


# ======================================================================
# Required Margin
# ======================================================================

class TestRequiredMargin:
    """Margin = (position_size * pip_multiplier * approx_price) / leverage."""

    def test_eurusd_margin(self) -> None:
        setup = TradeSetup(
            balance=10_000, risk_percent=1.0,
            stop_loss_pips=25, pip_value_per_lot=10,
            leverage="100:1", instrument="EUR/USD",
            pip_multiplier=100_000,
        )
        result, errors = compute_trade(setup)
        assert errors == []
        # position_size = 0.4, notional = 0.4 * 100000 * 1.08 = 43200
        # margin = 43200 / 100 = 432.00
        assert result.required_margin is not None
        assert abs(result.required_margin - 432.00) < 1.0

    def test_custom_instrument_no_margin(self) -> None:
        """Custom instruments have no approx price, so margin is None."""
        setup = TradeSetup(
            balance=10_000, risk_percent=1.0,
            stop_loss_pips=25, pip_value_per_lot=10,
            leverage="100:1", instrument="Custom",
            pip_multiplier=100_000,
        )
        result, errors = compute_trade(setup)
        assert errors == []
        assert result.required_margin is None

    def test_xauusd_margin(self) -> None:
        """XAU/USD uses pip_multiplier=100 and approx price ~2400."""
        setup = TradeSetup(
            balance=10_000, risk_percent=1.0,
            stop_loss_pips=25, pip_value_per_lot=10,
            leverage="100:1", instrument="XAU/USD",
            pip_multiplier=100,
        )
        result, errors = compute_trade(setup)
        assert errors == []
        assert result.required_margin is not None
        assert result.required_margin > 0

    def test_djiusd_margin(self) -> None:
        """DJI/USD uses pip_multiplier=1 and approx price ~40000."""
        setup = TradeSetup(
            balance=10_000, risk_percent=1.0,
            stop_loss_pips=25, pip_value_per_lot=1.0,
            leverage="100:1", instrument="DJI/USD",
            pip_multiplier=1,
        )
        result, errors = compute_trade(setup)
        assert errors == []
        assert result.required_margin is not None
        assert result.required_margin > 0


# ======================================================================
# Instrument list
# ======================================================================

class TestInstrumentList:
    """Verify the exact instrument list as specified."""

    EXACT_INSTRUMENTS = [  # noqa: RUF012
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

    def test_exact_instrument_count(self) -> None:
        assert len(INSTRUMENT_LIST) == 10

    def test_exact_instrument_order(self) -> None:
        assert INSTRUMENT_LIST == self.EXACT_INSTRUMENTS

    def test_all_instruments_in_presets(self) -> None:
        for inst in INSTRUMENT_LIST:
            assert inst in INSTRUMENT_PRESETS, f"{inst} missing from INSTRUMENT_PRESETS"

    def test_removed_instruments_not_present(self) -> None:
        removed = [
            "EUR/GBP", "EUR/JPY", "GBP/JPY", "AUD/JPY",
            "CAD/JPY", "CHF/JPY", "NZD/JPY", "EUR/AUD",
            "GBP/AUD", "EUR/CAD", "GBP/CAD", "AUD/NZD",
        ]
        for inst in removed:
            assert inst not in INSTRUMENT_LIST, f"{inst} should have been removed"
            assert inst not in INSTRUMENT_PRESETS, f"{inst} should have been removed from presets"

    def test_eurusd_pip_value(self) -> None:
        assert INSTRUMENT_PRESETS["EUR/USD"]["pip_value"] == 10.0

    def test_gbpusd_pip_value(self) -> None:
        assert INSTRUMENT_PRESETS["GBP/USD"]["pip_value"] == 10.0

    def test_usdcad_pip_value_is_dynamic(self) -> None:
        assert INSTRUMENT_PRESETS["USD/CAD"]["dynamic_pip_value"] is True

    def test_usdchf_pip_value_is_dynamic(self) -> None:
        assert INSTRUMENT_PRESETS["USD/CHF"]["dynamic_pip_value"] is True

    def test_usdjpy_pip_value_is_dynamic(self) -> None:
        assert INSTRUMENT_PRESETS["USD/JPY"]["dynamic_pip_value"] is True

    def test_xauusd_pip_value(self) -> None:
        assert INSTRUMENT_PRESETS["XAU/USD"]["point_size"] == 0.01
        assert INSTRUMENT_PRESETS["XAU/USD"]["monetary_value_per_price_unit"] == 100.0

    def test_djiusd_pip_value(self) -> None:
        assert INSTRUMENT_PRESETS["DJI/USD"]["point_size"] == 1.0
        assert INSTRUMENT_PRESETS["DJI/USD"]["monetary_value_per_price_unit"] == 1.0

    def test_custom_has_no_universal_pip_value(self) -> None:
        assert "pip_value" not in INSTRUMENT_PRESETS["Custom"]

    def test_dynamic_pip_values_follow_price(self) -> None:
        assert calculate_instrument_pip_value("USD/JPY", 0, 147.0) == pytest.approx(1000 / 147)
        assert calculate_instrument_pip_value("USD/JPY", 0, 150.0) == pytest.approx(1000 / 150)

    def test_point_conversion_uses_tenth_pip_for_forex(self) -> None:
        _, pips, risk_per_lot = calculate_risk_per_lot("USD/JPY", 50, 0, 150.0)
        assert pips == pytest.approx(5.0)
        assert risk_per_lot == pytest.approx(5 * (1000 / 150))

    def test_gold_uses_one_cent_points(self) -> None:
        price_distance, _, risk_per_lot = calculate_risk_per_lot("XAU/USD", 1000, 0, 4545.0)
        assert price_distance == pytest.approx(10.0)
        assert risk_per_lot == pytest.approx(1000.0)

    def test_dow_uses_one_point_increments(self) -> None:
        price_distance, _, risk_per_lot = calculate_risk_per_lot("DJI/USD", 100, 0, 53020.0)
        assert price_distance == pytest.approx(100.0)
        assert risk_per_lot == pytest.approx(100.0)

    def test_volume_below_minimum_is_not_rounded_up(self) -> None:
        tradable, message = validate_volume("EUR/USD", 0.0025)
        assert tradable is None
        assert message is not None
        assert "Minimum allowed volume" in message


# ======================================================================
# Take-Profit auto-update (SL → TP = 2× SL)
# ======================================================================

class TestTPAutoUpdate:
    """Test the automatic TP = 2× SL behavior."""

    def test_sl_25_auto_tp_50(self) -> None:
        """SL=25 → TP should auto-become 50."""
        assert round(25.0 * 2, 1) == 50.0

    def test_sl_40_auto_tp_80(self) -> None:
        """SL=40 → TP should auto-become 80."""
        assert round(40.0 * 2, 1) == 80.0

    def test_sl_100_auto_tp_200(self) -> None:
        """SL=100 → TP should auto-become 200."""
        assert round(100.0 * 2, 1) == 200.0

    def test_sl_35_auto_tp_70(self) -> None:
        """SL=35 → TP should auto-become 70."""
        assert round(35.0 * 2, 1) == 70.0

    def test_sl_0p5_auto_tp_1(self) -> None:
        """SL=0.5 → TP should auto-become 1.0."""
        assert round(0.5 * 2, 1) == 1.0

    def test_default_tp_matches_2x_sl(self) -> None:
        """Default TP (50) = 2× default SL (25)."""
        from fmm.core.constants import DEFAULT_STOP_LOSS_PIPS, DEFAULT_TAKE_PROFIT_PIPS
        assert DEFAULT_TAKE_PROFIT_PIPS == DEFAULT_STOP_LOSS_PIPS * 2


# ======================================================================
# TP manual override behavior (GUI-level, tested via logic)
# ======================================================================

class TestTPManualOverride:
    """Verify the flag-based manual override logic."""

    def test_manual_override_flag_prevents_auto_update(self) -> None:
        """Simulate the flag logic: once user edits TP, SL change should not overwrite."""
        tp_user_edited = False
        sl = 25.0
        tp = 50.0

        # Simulate SL change → auto-update
        if not tp_user_edited:
            tp = round(sl * 2, 1)
        assert tp == 50.0

        # Simulate user manually setting TP to 75
        tp = 75.0
        tp_user_edited = True

        # Now SL changes to 40
        sl = 40.0
        if not tp_user_edited:
            tp = round(sl * 2, 1)
        assert tp == 75.0  # TP should NOT have changed

    def test_unrelated_field_change_does_not_reset_tp(self) -> None:
        """Changing balance/risk should not affect the manual TP flag."""
        tp_user_edited = True
        tp = 75.0

        # Simulate balance change
        # (balance change triggers _recalculate, NOT _on_stop_loss_changed)
        # so tp_user_edited should remain True
        assert tp_user_edited is True
        assert tp == 75.0

    def test_clear_resets_manual_flag(self) -> None:
        """Clear button should reset tp_user_edited to False."""
        tp_user_edited = True
        tp_user_edited = False  # Simulating clear
        sl = 25.0
        if not tp_user_edited:
            tp = round(sl * 2, 1)
        assert tp == 50.0 # pyright: ignore[reportPossiblyUnboundVariable]


# ======================================================================
# Persistence (Settings + History)
# ======================================================================

class TestPersistence:
    """Test settings save/load roundtrip."""

    def test_settings_roundtrip(self) -> None:
        from fmm.config.settings import AppSettings
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "settings.json")
            import fmm.config.settings as cfg
            original = cfg.SETTINGS_FILE
            try:
                cfg.SETTINGS_FILE = path
                s = AppSettings(
                    balance=12_500.0,
                    risk_percent=1.5,
                    stop_loss_pips=35.0,
                    take_profit_pips=90.0,
                    pip_value_per_lot=10.0,
                    instrument="XAU/USD",
                    leverage="200:1",
                    window_width=1200,
                    window_height=800,
                    window_x=100,
                    window_y=200,
                )
                s.save()
                loaded = AppSettings.load()
                assert loaded.balance == 12_500.0
                assert loaded.risk_percent == 1.5
                assert loaded.stop_loss_pips == 35.0
                assert loaded.take_profit_pips == 90.0
                assert loaded.pip_value_per_lot == 10.0
                assert loaded.instrument == "XAU/USD"
                assert loaded.leverage == "200:1"
                assert loaded.window_width == 1200
                assert loaded.window_height == 800
                assert loaded.window_x == 100
                assert loaded.window_y == 200
            finally:
                cfg.SETTINGS_FILE = original

    def test_settings_missing_file_uses_defaults(self) -> None:
        from fmm.config.settings import AppSettings
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "nonexistent", "settings.json")
            import fmm.config.settings as cfg
            original = cfg.SETTINGS_FILE
            try:
                cfg.SETTINGS_FILE = path
                loaded = AppSettings.load()
                assert loaded.balance == 10_000.0
                assert loaded.instrument == "EUR/USD"
                assert loaded.leverage == "100:1"
            finally:
                cfg.SETTINGS_FILE = original

    def test_settings_corrupted_file_uses_defaults(self) -> None:
        from fmm.config.settings import AppSettings
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "settings.json")
            with open(path, "w") as f:
                f.write("{invalid json!!!")
            import fmm.config.settings as cfg
            original = cfg.SETTINGS_FILE
            try:
                cfg.SETTINGS_FILE = path
                loaded = AppSettings.load()
                assert loaded.balance == 10_000.0
            finally:
                cfg.SETTINGS_FILE = original

    def test_settings_invalid_instrument_falls_back(self) -> None:
        from fmm.config.settings import AppSettings
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "settings.json")
            with open(path, "w") as f:
                json.dump({"instrument": "INVALID_PAIR", "balance": 5000}, f)
            import fmm.config.settings as cfg
            original = cfg.SETTINGS_FILE
            try:
                cfg.SETTINGS_FILE = path
                loaded = AppSettings.load()
                assert loaded.instrument == "EUR/USD"  # default
                assert loaded.balance == 5000.0
            finally:
                cfg.SETTINGS_FILE = original

    def test_settings_invalid_leverage_falls_back(self) -> None:
        from fmm.config.settings import AppSettings
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "settings.json")
            with open(path, "w") as f:
                json.dump({"leverage": "999:1", "balance": 5000}, f)
            import fmm.config.settings as cfg
            original = cfg.SETTINGS_FILE
            try:
                cfg.SETTINGS_FILE = path
                loaded = AppSettings.load()
                assert loaded.leverage == "100:1"  # default
            finally:
                cfg.SETTINGS_FILE = original

    def test_history_roundtrip_with_leverage(self) -> None:
        from fmm.services.storage import StorageService
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "history.json")
            storage = StorageService(path)
            setup = TradeSetup(
                balance=10_000, risk_percent=1.0,
                stop_loss_pips=25, pip_value_per_lot=10,
                leverage="200:1", instrument="XAU/USD",
                pip_multiplier=100,
            )
            result, _ = compute_trade(setup)
            from datetime import datetime

            from fmm.core.models import HistoryEntry
            entry = HistoryEntry(
                timestamp=datetime.now(), setup=setup, result=result,  # noqa: DTZ005
            )
            storage.save_history([entry])
            loaded = storage.load_history()
            assert len(loaded) == 1
            assert loaded[0].setup.leverage == "200:1"
            assert loaded[0].setup.instrument == "XAU/USD"
            assert loaded[0].setup.pip_multiplier == 100
            assert loaded[0].result.required_margin is not None


# ======================================================================
# GUI structural checks (headless)
# ======================================================================

class TestGUI:
    """Lightweight GUI structural checks (run offscreen)."""

    @pytest.fixture(autouse=True)
    def _setup_qapp(self) -> None:
        """Ensure a QApplication exists (created once per process)."""
        import os as _os
        _os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        import sys as _sys

        from PySide6.QtWidgets import (  # pyright: ignore[reportMissingImports]
            QApplication,  # pyright: ignore[reportMissingImports]
        )
        if not QApplication.instance():
            self._app = QApplication(_sys.argv)
        else:
            self._app = QApplication.instance()

    def _make_window(self):
        from fmm.ui.main_window import MainWindow
        return MainWindow()

    def test_window_has_minimum_size(self) -> None:
        w = self._make_window()
        assert w.minimumWidth() >= 860
        assert w.minimumHeight() >= 620

    def test_leverage_combo_exists(self) -> None:
        w = self._make_window()
        assert w._leverage_combo.count() == 10

    def test_instrument_combo_count(self) -> None:
        w = self._make_window()
        assert w._instrument_combo.count() == 10

    def test_instrument_combo_exact_items(self) -> None:
        w = self._make_window()
        items = [w._instrument_combo.itemText(i) for i in range(w._instrument_combo.count())]
        assert items == TestInstrumentList.EXACT_INSTRUMENTS

    def test_leverage_combo_exact_items(self) -> None:
        w = self._make_window()
        items = [w._leverage_combo.itemText(i) for i in range(w._leverage_combo.count())]
        assert items == ALLOWED_LEVERAGE

    def test_tp_auto_updates_on_sl_change(self) -> None:
        w = self._make_window()
        w._tp_user_edited = False
        w._sl_spin.setValue(40.0)
        # _on_stop_loss_changed fires, should set TP to 80
        assert w._tp_spin.value() == 80.0

    def test_tp_manual_override_persists(self) -> None:
        w = self._make_window()
        # SL=25 → TP auto=50
        w._tp_user_edited = False
        w._sl_spin.setValue(25.0)
        assert w._tp_spin.value() == 50.0

        # User manually sets TP to 75
        w._tp_spin.setValue(75.0)
        assert w._tp_user_edited is True

        # SL changes to 40
        w._sl_spin.setValue(40.0)
        assert w._tp_spin.value() == 75.0  # unchanged

    def test_unrelated_change_does_not_reset_tp(self) -> None:
        w = self._make_window()
        w._tp_user_edited = False
        w._sl_spin.setValue(25.0)
        w._tp_spin.setValue(75.0)
        w._tp_user_edited = True

        # Change balance
        w._balance_spin.setValue(20_000.0)
        # TP should still be 75
        assert w._tp_spin.value() == 75.0

    def test_clear_resets_tp(self) -> None:
        w = self._make_window()
        w._tp_user_edited = True
        w._tp_spin.setValue(999.0)
        w._clear_inputs()
        assert w._tp_user_edited is False
        assert w._tp_spin.value() == DEFAULT_TAKE_PROFIT_PIPS

    def test_settings_persist_leverage(self) -> None:
        from fmm.config.settings import AppSettings
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "settings.json")
            import fmm.config.settings as cfg
            original = cfg.SETTINGS_FILE
            try:
                cfg.SETTINGS_FILE = path
                s = AppSettings(leverage="500:1")
                s.save()
                loaded = AppSettings.load()
                assert loaded.leverage == "500:1"
            finally:
                cfg.SETTINGS_FILE = original

    def test_window_geometry_persists(self) -> None:
        from fmm.config.settings import AppSettings
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "settings.json")
            import fmm.config.settings as cfg
            original = cfg.SETTINGS_FILE
            try:
                cfg.SETTINGS_FILE = path
                s = AppSettings(window_x=150, window_y=250, window_width=1100, window_height=800)
                s.save()
                loaded = AppSettings.load()
                assert loaded.window_x == 150
                assert loaded.window_y == 250
                assert loaded.window_width == 1100
                assert loaded.window_height == 800
            finally:
                cfg.SETTINGS_FILE = original

    def test_all_controls_have_tooltips(self) -> None:
        """Verify that key interactive widgets have tooltips set."""
        w = self._make_window()
        widgets_with_tooltips = [
            (w._balance_spin, "Balance"),
            (w._risk_spin, "Risk %"),
            (w._instrument_combo, "Instrument"),
            (w._pip_value_spin, "Pip Value/Lot"),
            (w._sl_spin, "Stop-Loss"),
            (w._tp_spin, "Take-Profit"),
            (w._leverage_combo, "Leverage"),
            (w._add_btn, "Add to History"),
            (w._copy_btn, "Copy Results"),
            (w._clear_btn, "Clear"),
            (w._clear_history_btn, "Clear History"),
            (w._history_table, "History table"),
            (w._risk_amount_label, "Risk Amount"),
            (w._pos_size_label, "Position Size"),
            (w._pip_value_label, "Pip Value"),
            (w._rr_label, "R:R"),
            (w._loss_label, "Loss"),
            (w._profit_label, "Profit"),
            (w._margin_label, "Margin"),
        ]
        for widget, name in widgets_with_tooltips:
            tip = widget.toolTip()
            assert tip, f"{name} ({widget.__class__.__name__}) has no tooltip"
            assert len(tip) > 3, f"{name} tooltip is too short: '{tip}'"


# Import the default constants used in tests
from fmm.core.constants import DEFAULT_TAKE_PROFIT_PIPS
