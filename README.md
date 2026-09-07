# FMM — Forex Money Manager

A small, offline desktop tool for calculating forex position size from the numbers that actually matter to the trade.

Built with **Python**, **PySide6**, and **pytest**.

## Why the calculator asks for pip value

FMM deliberately does **not** try to guess an instrument's pip value from its symbol or current market price.

Broker contract specifications vary, especially outside straightforward USD-quoted pairs. Instead, enter the **USD value of one pip for one standard lot** exactly as provided by your broker.

That makes the calculation simple, transparent, and broker-independent.

## Inputs

- **Balance** — account balance in USD.
- **Risk %** — percentage of the balance you want to risk.
- **Pip Value / Lot** — USD value of one pip for one standard lot, supplied by your broker.
- **Stop-Loss** — stop distance in pips.
- **Take-Profit** — optional target distance in pips. It defaults to 2× the stop-loss and can be overridden manually.

There is intentionally **no instrument selector and no current-price input**. FMM does not need either one to size the position once the broker's pip value is known.

## Calculations

```text
risk_amount   = balance × risk_percent / 100
pip_value     = risk_amount / stop_loss_pips
position_size = pip_value / pip_value_per_lot

risk_reward   = take_profit_pips / stop_loss_pips
profit        = position_size × pip_value_per_lot × take_profit_pips
loss          = risk_amount
```

### Example

With:

- Balance: `$10,000`
- Risk: `1%`
- Pip Value / Lot: `$10`
- Stop-Loss: `25 pips`
- Take-Profit: `50 pips`

FMM calculates:

```text
Risk amount   = $100.00
Pip value     = $4.00 / pip
Position size = 0.400000 lots
Risk / Reward = 1 : 2.00
Potential loss = $100.00
Potential gain = $200.00
```

## Features

- Live calculation as inputs change
- Manual broker-supplied pip value
- Automatic 2× SL take-profit with manual override
- Risk/reward calculation
- Potential profit/loss
- Calculation history stored locally as JSON
- Copy results to clipboard
- Persistent input values and window geometry
- Dark Qt6 interface
- No internet connection or market-data API required

## Project Structure

```text
.
├── FMM.spec
├── main.py
├── main-v3.cpp              # Original C++ version/reference
├── requirements.txt
├── fmm/
│   ├── config/
│   │   └── settings.py      # Persistent application settings
│   ├── core/
│   │   ├── calculator.py    # Pure position-sizing formulas
│   │   ├── constants.py     # Defaults and application metadata
│   │   ├── models.py        # Calculation data models
│   │   └── validators.py    # Input validation
│   ├── services/
│   │   └── storage.py       # Local history persistence
│   ├── tests/
│   │   └── test_calculator.py
│   └── ui/
│       ├── main_window.py   # PySide6 interface
│       ├── styles.py         # Dark theme
│       └── widgets.py        # R:R visualization
└── README.md
```

The calculation engine has no PySide6 dependency, so the formulas can be tested independently from the GUI.

## Installation

Python 3.10+ is recommended.

```bash
git clone git@github.com:hesam-amani/forex-money-manager.git
cd forex-money-manager

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Test

```bash
python -m pytest -q
```

The repository also includes a GitHub Actions workflow that runs the test suite on pushes and pull requests.

## Local data

FMM stores settings and history outside the repository:

```text
~/.config/fmm/settings.json
~/.config/fmm/history.json
```

These files are local user data and are not required by the application source.

## Original C++ version

`main-v3.cpp` is kept as a reference to the original console implementation that inspired the Python rewrite. The active application is the Python/PySide6 version.

## License

MIT
