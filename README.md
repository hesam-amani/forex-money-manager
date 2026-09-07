# FMM — Forex Money Manager

A professional, offline-capable desktop application for forex position sizing and risk management. Built with Python and PySide6 (Qt6).

Originally conceived from a simple C++ console calculator, this is a complete rewrite — a clean, dark-themed, modern desktop utility designed for daily use by forex traders.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![PySide6](https://img.shields.io/badge/PySide6-6.5%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [How to Run Tests](#how-to-run-tests)
- [Core Calculations](#core-calculations)
- [Instrument Presets](#instrument-presets)
- [Leverage](#leverage)
- [Architecture](#architecture)
- [Extending the Application](#extending-the-application)
- [Data Storage](#data-storage)
- [Original C++ Program](#original-c-program)
- [License](#license)

---

## Features

### Core Calculations (from the original C++ program)

| Feature | Description |
|---|---|
| **Position Sizing** | Calculates the exact lot size based on your account balance, risk percentage, and stop-loss distance |
| **Risk Amount** | Shows the dollar amount at risk for each trade |
| **Pip Value** | Calculates the dollar value per pip for the planned trade |
| **Position Size (lots)** | Recommended number of lots to trade |
| **Lot Tier Breakdown** | Shows the position size broken down into standard, mini, and micro lots |

### Extended Calculations

| Feature | Description |
|---|---|
| **Risk/Reward Ratio** | Automatically computed when a take-profit level is set |
| **Potential Profit** | Dollar amount of potential profit at the take-profit level |
| **Potential Loss** | Dollar amount of potential loss at the stop-loss level |
| **Visual R:R Bar** | A custom-painted horizontal bar that visually shows the risk/reward split |
| **Live Recalculation** | All results update instantly as you type — no button press required |
| **Required Margin** | Approximate margin estimate based on leverage and approximate instrument prices |

### Auto Take-Profit

| Feature | Description |
|---|---|
| **SL → TP auto-update** | Changing Stop-Loss automatically sets Take-Profit to 2× SL (default 1:2 R:R) |
| **Manual override** | Once you manually edit Take-Profit, it is preserved even when SL changes |
| **Clear resets** | The Clear button resets TP back to the auto-update behavior |

### Leverage Support

| Feature | Description |
|---|---|
| **Select-only dropdown** | Fixed leverage options: 1:1 through 1000:1 |
| **Margin calculation** | Higher leverage = lower required margin |
| **Risk-independent** | Leverage does NOT affect risk amount or position sizing |
| **Persisted** | Leverage setting is saved between sessions |

### Instrument Support

| Feature | Description |
|---|---|
| **9 Instrument Presets** | Forex majors, USD/JPY, XAU/USD (Gold), DJI/USD (Dow Jones) |
| **Custom Instrument** | Manual pip-value entry for any pair or CFD |
| **Auto-fill** | Selecting an instrument automatically sets the correct pip value per lot |

### Input Validation

| Feature | Description |
|---|---|
| **Zero/negative balance** | Caught and reported |
| **Zero/negative stop-loss** | Prevents division-by-zero crash |
| **Risk % > 100%** | Blocked with a clear message |
| **Risk % > 10%** | Warning shown (aggressive trading) |
| **Zero pip value per lot** | Prevents division-by-zero crash |
| **Negative take-profit** | Blocked |
| **Oversized balance (>$1B)** | Warning shown |
| **Invalid leverage** | Caught and reported |
| **Status bar errors** | All validation errors displayed in the status bar |

### User Experience

| Feature | Description |
|---|---|
| **Dark professional theme** | Custom QSS stylesheet — dark background, clear hierarchy, subtle accent colours |
| **Persistent settings** | Every user-configurable value is saved between sessions |
| **Window geometry** | Window size and position are restored on restart |
| **Calculation history** | Store and review past calculations in a side panel table |
| **Copy to clipboard** | One-click formatted summary ready to paste into a journal or chat |
| **Clear/Reset** | Instantly reset all fields to sensible defaults |
| **Clear History** | One-click history wipe with confirmation dialog |
| **Tooltips on every control** | Every input, result label, and button has a concise tooltip |
| **Status bar** | Live feedback showing the current calculation summary or validation errors |
| **Keyboard friendly** | Standard Tab navigation through all spin boxes and controls |
| **Responsive layout** | Window is freely resizable; layout adapts to all sizes above the minimum |

---

## Project Structure

```
fmm/
├── main.py                         # Application entry point
├── requirements.txt                # Python dependencies
├── main-v3.cpp                     # Original C++ source (reference)
├── README.md                       # This file
│
├── fmm/                            # Main Python package
│   ├── __init__.py
│   │
│   ├── core/                       # Calculation engine (no GUI dependency)
│   │   ├── __init__.py
│   │   ├── calculator.py           # Position-sizing formulas & compute_trade()
│   │   ├── constants.py            # Forex constants, instrument presets, defaults
│   │   ├── models.py               # TradeSetup, CalculationResult, HistoryEntry
│   │   └── validators.py           # Input validation rules
│   │
│   ├── ui/                         # GUI layer (PySide6 / Qt6)
│   │   ├── __init__.py
│   │   ├── main_window.py          # Main window layout, signals, and slots
│   │   ├── styles.py               # Complete dark-theme QSS stylesheet
│   │   └── widgets.py              # Custom RiskRewardBar widget
│   │
│   ├── services/                   # Infrastructure services
│   │   ├── __init__.py
│   │   └── storage.py              # History persistence (JSON on disk)
│   │
│   ├── config/                     # Application configuration
│   │   ├── __init__.py
│   │   └── settings.py             # Settings dataclass with save/load
│   │
│   └── tests/                      # Automated tests
│       ├── __init__.py
│       └── test_calculator.py      # 114 tests covering all functionality
│
└── .config/fmm/                    # Runtime data (auto-created)
    ├── settings.json               # Persisted application settings
    └── history.json                # Persisted calculation history
```

### Module Responsibilities

| Module | Purpose | GUI Dependency |
|---|---|---|
| `core/calculator.py` | All financial formulas and the main `compute_trade()` function | **None** |
| `core/constants.py` | Forex lot sizes, pip sizes, instrument presets, default values | **None** |
| `core/models.py` | `TradeSetup`, `CalculationResult`, `HistoryEntry` dataclasses | **None** |
| `core/validators.py` | Input validation rules returning human-readable error strings | **None** |
| `ui/main_window.py` | Full GUI window: layout, signal wiring, slots | PySide6 |
| `ui/styles.py` | Complete dark-theme QSS stylesheet with colour constants | PySide6 (constants only) |
| `ui/widgets.py` | Custom `RiskRewardBar` paint widget | PySide6 |
| `services/storage.py` | JSON-based history persistence (save/load/clear) | **None** |
| `config/settings.py` | Application settings dataclass with file persistence | **None** |

> **Key design principle:** The `core/` and `services/` packages have zero GUI dependency. You can use the calculation engine as a Python library from any script, notebook, or alternative interface.

---

## Installation

### Prerequisites

- **Python 3.10** or newer
- **pip** (Python package manager)
- A display server (X11/Wayland on Linux, native on macOS/Windows)

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/fmm.git
cd fmm

# (Recommended) Create a virtual environment
python3 -m venv venv
source venv/bin/activate       # Linux / macOS
# venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

| Package | Version | Purpose |
|---|---|---|
| [PySide6](https://pypi.org/project/PySide6/) | >= 6.5.0 | Qt6 bindings for the GUI |
| [pytest](https://pypi.org/project/pytest/) | >= 7.0.0 | Test runner (dev dependency) |

No other external dependencies are required. The application is fully offline-capable.

---

## How to Run

```bash
# From the project root directory
python main.py
```

The application window will open. All values are calculated live as you change any input field.

---

## How to Run Tests

```bash
# From the project root directory
python -m pytest fmm/tests/test_calculator.py -v
```

### Test Coverage

The test suite contains **114 tests** across 16 test classes:

| Test Class | Tests | What It Covers |
|---|---|---|
| `TestRiskAmount` | 8 | `risk_amount = balance × risk% / 100` — basic, fractional, large, small, zero |
| `TestPipValue` | 7 | `pip_value = risk_amount / sl_pips` — basic, edge cases, division-by-zero |
| `TestPositionSize` | 6 | `position_size = pip_value / pip_value_per_lot` — standard, mini, zero/negative |
| `TestRRRatio` | 7 | `rr = tp_pips / sl_pips` — 1:1, 1:3, 2:1, None cases, zero, negative |
| `TestPotentialProfit` | 4 | `profit = pip_value × tp_pips` — basic, None when no TP |
| `TestRoundLot` | 5 | Floor rounding to standard/mini/micro lot increments |
| `TestComputeTrade` | 7 | Full end-to-end integration — C++ scenarios, JPY, large balance, with/without TP |
| `TestValidation` | 10 | All validation rules — zero, negative, excessive, valid |
| `TestEdgeCases` | 5 | Very small risk, tight/wide stops, lot tier correctness |
| `TestLeverage` | 9 | Leverage values, risk-independence, margin calculation, validation |
| `TestRequiredMargin` | 4 | Margin for EUR/USD, XAU/USD, DJI/USD, Custom (no margin) |
| `TestInstrumentList` | 15 | Exact 10-instrument list, removed instruments, pip values, JPY flags |
| `TestTPAutoUpdate` | 6 | SL → TP = 2× SL for various SL values, default consistency |
| `TestTPManualOverride` | 3 | Flag logic, unrelated-change safety, clear-resets behavior |
| `TestPersistence` | 6 | Settings roundtrip, missing/corrupted files, invalid dropdowns, history with leverage |
| `TestGUI` | 13 | Window minimum size, combo items, TP auto-update, tooltips, settings persistence |

---

## Core Calculations

The application implements standard forex position-sizing formulas.

### Formulas

```
risk_amount    = balance × risk_percent / 100
pip_value      = risk_amount / stop_loss_pips
position_size  = pip_value / pip_value_per_lot

rr_ratio       = take_profit_pips / stop_loss_pips        (optional)
potential_profit = pip_value × take_profit_pips            (optional)
potential_loss = risk_amount

required_margin = (position_size × pip_multiplier × approx_price) / leverage
```

### Example

Given:
- Account balance: $10,000
- Risk: 1%
- Stop-loss: 25 pips
- Pip value per lot: $10 (EUR/USD)
- Take-profit: 50 pips (auto-set to 2× SL)
- Leverage: 100:1

Calculations:
```
risk_amount    = $10,000 × 1 / 100           = $100.00
pip_value      = $100.00 / 25                = $4.00 / pip
position_size  = $4.00 / $10.00              = 0.40 lots
rr_ratio       = 50 / 25                     = 1 : 2.00
potential_profit = $4.00 × 50                = $200.00
potential_loss = $100.00
required_margin = (0.40 × 100,000 × 1.08) / 100 = $432.00 (approx)
```

### Lot Tier Breakdown

| Tier | Size | `0.40` lots becomes |
|---|---|---|
| Standard | 1.0 | 0 std lots |
| Mini | 0.1 | 4 mini lots |
| Micro | 0.01 | 40 micro lots |

Rounding is always **floor** (toward zero) so you never over-risk.

### Units and Assumptions

- **Balance** is in the account currency (typically USD).
- **Risk %** is a percentage of the account balance (e.g., 1 = 1%).
- **Stop-loss** and **take-profit** are in pips/ticks.
- **Pip value per lot** is the USD value of 1 pip/tick of movement for 1 standard lot.
  - For XXX/USD pairs this is always `$10.00`.
  - For USD/XXX pairs this varies with the exchange rate.
  - For JPY pairs a pip is 0.01 instead of 0.0001.
  - For XAU/USD (Gold) a tick is $0.01; pip value is $10/lot.
  - For DJI/USD (Dow Jones) a tick is 1 point; pip value is $1/lot.
- The application does **not** fetch live exchange rates.
- **Required margin** uses approximate mid-market prices. Always verify with your broker.

---

## Instrument Presets

| Pair | Pip Value/Lot | Pip Size | Notes |
|---|---|---|---|
| EUR/USD | $10.00 | 0.0001 | Exact for USD-quote pairs |
| GBP/USD | $10.00 | 0.0001 | |
| AUD/USD | $10.00 | 0.0001 | |
| NZD/USD | $10.00 | 0.0001 | |
| USD/CAD | $7.50 | 0.0001 | Approximate — varies with rate |
| USD/CHF | $11.00 | 0.0001 | Approximate — varies with rate |
| USD/JPY | $6.67 | 0.01 | Approximate — varies with rate |
| XAU/USD | $10.00 | 0.01 | Gold — tick value per lot |
| DJI/USD | $1.00 | 1.0 | Dow Jones — point value per lot |
| Custom | User-defined | User-defined | Manual pip/tick value entry |

> **Important:** Pip values for non-USD-quote pairs are approximate. Always verify with your broker. Use the "Custom" option for exact values.

---

## Leverage

Fixed select-only dropdown with these options:

| Leverage | Use Case |
|---|---|
| 1:1 | No leverage (spot) |
| 10:1 | Conservative |
| 20:1 | Common for major pairs |
| 30:1 | Common for EU-regulated accounts |
| 50:1 | Standard retail |
| 100:1 | Common retail (default) |
| 200:1 | High leverage |
| 300:1 | High leverage |
| 500:1 | Very high leverage |
| 1000:1 | Maximum available |

**Key behavior:** Leverage does NOT affect risk amount or position sizing. It only affects required margin. For Custom instruments, margin is not displayed.

---

## Architecture

### Dependency Rules

1. **`core/`** depends on nothing outside itself. Pure-Python calculation library.
2. **`services/`** depends only on `core/models.py` and `core/constants.py`.
3. **`config/`** depends only on `core/constants.py`.
4. **`ui/`** depends on `core/`, `config/`, `services/`, and PySide6.
5. **`main.py`** wires everything together and starts the Qt event loop.

### Signal Flow (GUI)

```
User changes input field
  → valueChanged signal fires
  → _on_stop_loss_changed() / _on_take_profit_changed() / _recalculate()
  → Builds TradeSetup from current spin-box values
  → Calls compute_trade(setup) → (result, errors)
  → Updates result labels + R:R bar + status bar
```

---

## Design Decisions

### Why real-time calculation?

A money-management calculator is used interactively. The calculation is trivial (three divisions), so there is no performance reason to defer it.

### Why auto-set TP to 2× SL?

A 1:2 risk/reward ratio is a common default. The `blockSignals` mechanism ensures no signal recursion between SL→TP and TP manual edits.

### Why not fetch live exchange rates?

Adding a live rate feed would introduce an internet dependency and API complexity. The pip-value-per-lookup approach keeps the calculator self-contained.

### Why JSON for persistence?

Human-readable, zero-dependency, easy to back up, and fast enough for this scale.

---

## Extending the Application

### Adding a New Instrument

Edit `fmm/core/constants.py` and add entries to both `INSTRUMENT_PRESETS` and `INSTRUMENT_LIST`.

### Adding Leverage Options

Edit `ALLOWED_LEVERAGE` in `fmm/core/constants.py`.

### Using the Engine Without the GUI

```python
from fmm.core.calculator import compute_trade
from fmm.core.models import TradeSetup

setup = TradeSetup(
    balance=10_000,
    risk_percent=1.0,
    stop_loss_pips=25.0,
    pip_value_per_lot=10.0,
    take_profit_pips=50.0,
    leverage="100:1",
    instrument="EUR/USD",
)

result, errors = compute_trade(setup)

if errors:
    print("Errors:", errors)
else:
    print(f"Position size: {result.position_size:.4f} lots")
    print(f"Risk: ${result.risk_amount:.2f}")
    print(f"R:R: 1:{result.rr_ratio}")
    print(f"Required margin: ${result.required_margin:.2f}")
```

---

## Data Storage

All persistent data is stored in `~/.config/fmm/`:

| File | Contents |
|---|---|
| `settings.json` | All user settings: balance, risk, SL, TP, instrument, leverage, pip value, window geometry |
| `history.json` | Up to 100 saved calculation entries with timestamps and leverage |

Both files are plain JSON. You can edit them manually or delete them to reset the application.

### What Is Persisted

Every user-configurable value is restored on restart:
- Balance, Risk %, Stop-Loss, Take-Profit
- Instrument selection and Pip Value/Lot
- Leverage selection
- Window width, height, and position

---

## Original C++ Program

The original `main-v3.cpp` is included for reference. It was a console-based infinite-loop calculator with 4 inputs and 3 calculated outputs. The Python application preserves the exact same calculation logic while adding validation, a professional GUI, persistence, and extended functionality.

---

## License

This project is released under the [MIT License](LICENSE).
