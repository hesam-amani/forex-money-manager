# 💱 Forex Money Manager

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-Qt6-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython/)
[![Tests](https://img.shields.io/badge/tests-22%20passing-2ea043)](#tests)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A lightweight desktop position-sizing calculator for forex traders.

FMM calculates **risk amount, pip value, position size, risk/reward, and potential profit/loss** from a small set of trade inputs. It is designed to keep the calculation transparent instead of trying to infer broker-specific contract details from a symbol or live market price.

## ✨ Features

| Feature | Description |
|---|---|
| 🎯 **Position Sizing** | Calculate the required lot size from account balance, risk, stop-loss, and pip value |
| 💵 **Risk Calculation** | See the exact USD amount being risked on the trade |
| 📏 **Manual Pip Value** | Enter the USD value of one pip for one standard lot supplied by your broker |
| ⚖️ **Risk / Reward** | Calculate TP-to-SL ratio automatically |
| 📈 **R:R Visualisation** | A custom bar shows the loss/reward split, including extreme ratios |
| 💰 **Potential Profit/Loss** | See the dollar outcome at the selected SL and TP |
| 🔄 **Live Recalculation** | Results update immediately when an input changes |
| 🎯 **Auto Take-Profit** | TP defaults to 2× SL and can be manually overridden |
| 📝 **Calculation History** | Save and review recent calculations locally |
| 📋 **Copy Results** | Copy a clean trade summary to the clipboard |
| 💾 **Persistent Settings** | Inputs and window geometry are restored between sessions |
| 🌙 **Dark Interface** | Compact Qt6 desktop UI with a dark theme |
| 🔒 **Offline** | No market-data API, network connection, or account access is required |

## 🧮 How It Works

FMM intentionally asks for **Pip Value / Lot** instead of asking for an instrument and current market price.

Broker and instrument conventions can vary. Rather than making assumptions about contract size, quote currency, leverage, or current price, FMM uses the **USD value of one pip for one standard lot** that you provide from your broker's specifications.

Once that value is known, the position-sizing calculation is straightforward:

```text
risk_amount   = balance × risk_percent / 100
pip_value     = risk_amount / stop_loss_pips
position_size = pip_value / pip_value_per_lot
```

When a take-profit is set:

```text
risk_reward = take_profit_pips / stop_loss_pips
profit      = position_size × pip_value_per_lot × take_profit_pips
loss        = risk_amount
```

### Example

Suppose the trade uses:

- **Balance:** `$10,000`
- **Risk:** `1%`
- **Pip Value / Lot:** `$10`
- **Stop-Loss:** `25 pips`
- **Take-Profit:** `50 pips`

FMM calculates:

```text
Risk amount   = $100.00
Pip value     = $4.00 / pip
Position size = 0.400000 lots
Risk / Reward = 1 : 2.00
Potential loss  = $100.00
Potential profit = $200.00
```

## 🎮 Usage

### 1. Enter account and risk

Set your account **Balance** and the percentage of the account you want to risk.

### 2. Enter the broker's pip value

Enter **Pip Value / Lot** as the USD value of one pip for one standard lot for the instrument you are trading.

### 3. Set the stop-loss

Enter the distance between entry and stop-loss in pips.

### 4. Set the take-profit

FMM initially sets TP to **2× the stop-loss**. Edit it whenever you want a different target; after a manual edit, changing SL will no longer overwrite your TP.

### 5. Review the results

The results panel shows the calculated lot size, pip value, R:R, and potential USD outcomes. You can add the calculation to history or copy the complete summary to the clipboard.

## 🛠️ Tech Stack

- **Python** — application and calculation logic
- **PySide6 / Qt6** — desktop interface
- **pytest** — automated tests
- **JSON** — local settings and history persistence
- **GitHub Actions** — continuous integration
- **PyInstaller** — optional standalone executable packaging

## 📁 Project Structure

```text
forex-money-manager/
├── .github/
│   └── workflows/
│       └── tests.yml             # GitHub Actions test workflow
├── fmm/
│   ├── config/
│   │   └── settings.py          # Persistent application settings
│   ├── core/
│   │   ├── calculator.py        # Position-sizing formulas
│   │   ├── constants.py         # Defaults and application metadata
│   │   ├── models.py            # Trade and result data models
│   │   └── validators.py        # Input validation
│   ├── services/
│   │   └── storage.py           # Local history persistence
│   ├── tests/
│   │   └── test_calculator.py   # Calculation and settings tests
│   └── ui/
│       ├── main_window.py       # Main application window
│       ├── styles.py             # Dark-theme QSS
│       └── widgets.py            # Custom R:R visualisation
├── FMM.spec                     # PyInstaller build specification
├── main.py                      # Application entry point
├── main-v3.cpp                  # Original C++ version/reference
├── requirements.txt
├── LICENSE
└── README.md
```

The calculation engine in `fmm/core/` does not depend on PySide6, so the financial formulas remain separate from the GUI.

## 🚀 Getting Started

### Prerequisites

- Python **3.10+**
- pip
- A desktop environment supported by Qt6

### Run Locally

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/hesam-amani/forex-money-manager.git
cd forex-money-manager

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt
```

Start FMM:

```bash
./main.py
```

You can also run it with Python directly:

```bash
python main.py
```

On Linux/macOS, the executable entry point uses the Python shebang in `main.py`.

## 🧪 Tests

Run the complete test suite with:

```bash
pytest -q
```

The project currently has **22 automated tests** covering the core formulas, complete trade calculations, extreme R:R values, validation behavior, and settings persistence.

GitHub Actions runs the same pytest suite on pushes to the active development branches and on pull requests targeting `main`.

## 💾 Local Data

FMM does not use a database or external service for normal operation.

On Linux, application data is stored under:

```text
~/.config/fmm/
├── settings.json
└── history.json
```

The files contain only the application's local settings and saved calculation history. They are not part of the repository.

The history is capped at the most recent **100 entries**.

## 📦 Packaging

`FMM.spec` contains a PyInstaller configuration for building a windowed executable named `FMM`.

For example, after installing PyInstaller:

```bash
pyinstaller FMM.spec
```

The generated build artifacts are ignored by Git.

## ⚠️ Important Note

FMM is a **position-sizing calculator**, not a broker connection, trading terminal, or market-data application.

The accuracy of the result depends on entering the correct **USD pip value per standard lot** for the instrument and broker you are using. FMM does not fetch or verify that value for you.

Always verify broker contract specifications before placing a trade.

## 📜 History

FMM began as a small C++ console calculator. `main-v3.cpp` is retained in the repository as the original implementation/reference.

The current application is a Python/PySide6 rewrite with a deliberately smaller calculation model and a separation between the calculation engine, persistence layer, and GUI.

## 🤝 Contributing

Issues and pull requests are welcome.

For changes to the calculation engine, please add or update tests that cover the affected behavior. Keep broker-specific assumptions out of the core formulas unless the calculation model is intentionally expanded.

## 📄 License

FMM is open-source software released under the [MIT License](LICENSE).

---

**FMM v1.1.0** · Built by Hesam Amani
