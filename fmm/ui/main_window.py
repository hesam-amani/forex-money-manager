"""Main application window."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt  # pyright: ignore[reportMissingImports]
from PySide6.QtWidgets import (  # pyright: ignore[reportMissingImports]
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from ..config.settings import AppSettings
from ..core.calculator import calculate_instrument_pip_value, compute_trade
from ..core.constants import (
    ALLOWED_LEVERAGE,
    APP_NAME,
    APP_VERSION,
    APPROX_PRICES,
    DEFAULT_BALANCE,
    DEFAULT_INSTRUMENT,
    DEFAULT_LEVERAGE,
    DEFAULT_PIP_VALUE_PER_LOT,
    DEFAULT_RISK_PCT,
    DEFAULT_STOP_LOSS_PIPS,
    DEFAULT_TAKE_PROFIT_PIPS,
    INSTRUMENT_LIST,
    INSTRUMENT_PRESETS,
)
from ..core.models import HistoryEntry, TradeSetup
from ..services.storage import StorageService
from .styles import (
    ACCENT,
    RISK_RED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from .widgets import RiskRewardBar


class MainWindow(QMainWindow):
    """The single top-level window of the application."""

    def __init__(self) -> None:
        super().__init__()
        self._settings = AppSettings.load()
        self._storage = StorageService()
        self._history: list[HistoryEntry] = self._storage.load_history()

        # State: tracks whether TP was manually edited by the user
        self._tp_user_edited: bool = False

        tooltip_font = QApplication.font()
        tooltip_font.setPointSize(12)
        tooltip_font.setBold(False)
        QToolTip.setFont(tooltip_font)

        self._build_ui()
        # Load saved values before connecting signals so the initial
        # values come from settings, not from widget defaults.
        self._load_settings_to_ui()
        self._connect_signals()
        self._tp_user_edited = False  # Reset after initial load
        self._recalculate()

    # ==================================================================
    # UI construction
    # ==================================================================

    def _build_ui(self) -> None:
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(860, 620)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Restore window geometry
        sw = self._settings.window_width
        sh = self._settings.window_height
        sx = self._settings.window_x
        sy = self._settings.window_y
        if sx >= 0 and sy >= 0:
            self.setGeometry(sx, sy, sw, sh)
        else:
            self.resize(sw, sh)

        # ── Central widget + splitter ───────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 8)
        main_layout.setSpacing(10)

        # ── Header ──────────────────────────────────────────────────
        header = self._build_header()
        main_layout.addWidget(header)

        # ── Splitter: inputs | history ──────────────────────────────
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setChildrenCollapsible(False)

        left_panel = self._build_left_panel()
        right_panel = self._build_history_panel()

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter, stretch=1)

        # ── Status bar ──────────────────────────────────────────────
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

    # ── Header ──────────────────────────────────────────────────────

    def _build_header(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 0, 4, 0)

        title = QLabel("FMM")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: 800; color: {ACCENT}; letter-spacing: 1px;"
        )

        subtitle = QLabel("Forex Money Manager")
        subtitle.setStyleSheet(f"font-size: 14px; color: {TEXT_SECONDARY};")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addStretch()
        return widget

    # ── Left panel (inputs + results + actions) ─────────────────────

    def _build_left_panel(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        layout.addWidget(self._build_account_group())
        layout.addWidget(self._build_trade_group())
        layout.addWidget(self._build_results_group())
        layout.addWidget(self._build_actions())

        layout.addStretch()
        return widget

    # ── Account & Risk group ────────────────────────────────────────

    def _build_account_group(self) -> QGroupBox:
        group = QGroupBox("ACCOUNT")
        grid = QGridLayout(group)
        grid.setSpacing(8)
        grid.setColumnStretch(1, 1)

        # Balance
        lbl = QLabel("Balance")
        lbl.setToolTip("Your current trading account balance.")
        self._balance_spin = QDoubleSpinBox()
        self._balance_spin.setRange(0.01, 1_000_000_000)
        self._balance_spin.setDecimals(2)
        self._balance_spin.setPrefix("$ ")
        self._balance_spin.setSingleStep(100)
        self._balance_spin.setGroupSeparatorShown(True)
        self._balance_spin.setToolTip("Your current trading account balance.")

        grid.addWidget(lbl, 0, 0)
        grid.addWidget(self._balance_spin, 0, 1)

        # Risk %
        lbl2 = QLabel("Risk %")
        lbl2.setToolTip(
            "Percentage of your account balance you are willing to risk on this trade."
        )
        self._risk_spin = QDoubleSpinBox()
        self._risk_spin.setRange(0.01, 100)
        self._risk_spin.setDecimals(2)
        self._risk_spin.setSuffix(" %")
        self._risk_spin.setSingleStep(0.25)
        self._risk_spin.setToolTip(
            "Percentage of your account balance you are willing to risk on this trade."
        )

        grid.addWidget(lbl2, 1, 0)
        grid.addWidget(self._risk_spin, 1, 1)

        # Risk amount (read-only)
        lbl3 = QLabel("Risk Amount")
        lbl3.setToolTip("Dollar amount at risk — automatically calculated.")
        self._risk_amount_label = QLabel("$ 0.00")
        self._risk_amount_label.setObjectName("resultValue")
        self._risk_amount_label.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {RISK_RED};"
            f"QToolTip {{ color: {RISK_RED}; font-size: 14px; }}"
        )
        self._risk_amount_label.setToolTip("Dollar amount at risk — automatically calculated.")

        grid.addWidget(lbl3, 2, 0)
        grid.addWidget(self._risk_amount_label, 2, 1)

        return group

    # ── Trade setup group ───────────────────────────────────────────

    def _build_trade_group(self) -> QGroupBox:
        group = QGroupBox("TRADE SETUP")
        grid = QGridLayout(group)
        grid.setSpacing(8)
        grid.setColumnStretch(1, 1)

        # Instrument
        lbl = QLabel("Instrument")
        lbl.setToolTip(
            "Select the trading instrument used to determine the pip/tick value per standard lot."
        )
        self._instrument_combo = QComboBox()
        self._instrument_combo.addItems(INSTRUMENT_LIST)
        self._instrument_combo.setCurrentText(DEFAULT_INSTRUMENT)
        self._instrument_combo.setToolTip(
            "Select the trading instrument used to determine the pip/tick value per standard lot."
        )

        grid.addWidget(lbl, 0, 0)
        grid.addWidget(self._instrument_combo, 0, 1)

        # Current price
        price_label = QLabel("Current Price")
        price_label.setToolTip(
            "Current market price used for dynamic pip values and margin estimates."
        )
        self._price_spin = QDoubleSpinBox()
        self._price_spin.setRange(0.000001, 1_000_000_000)
        self._price_spin.setDecimals(5)
        self._price_spin.setSingleStep(0.0001)
        self._price_spin.setGroupSeparatorShown(True)
        self._price_spin.setToolTip(
            "Current market price used for dynamic pip values and margin estimates."
        )
        grid.addWidget(price_label, 1, 0)
        grid.addWidget(self._price_spin, 1, 1)

        # Pip value per lot
        lbl2 = QLabel("Pip Value/Lot")
        lbl2.setToolTip(
            "USD value of 1 pip/tick for 1 standard lot.\n"
            "Auto-filled for presets; verify with your broker.\n"
            "Editable when 'Custom' is selected."
        )
        self._pip_value_spin = QDoubleSpinBox()
        self._pip_value_spin.setRange(0.01, 1000)
        self._pip_value_spin.setDecimals(4)
        self._pip_value_spin.setPrefix("$ ")
        self._pip_value_spin.setSingleStep(0.5)
        self._pip_value_spin.setToolTip(
            "USD value of 1 pip/tick for 1 standard lot.\n"
            "Auto-filled for presets; verify with your broker.\n"
            "Editable when 'Custom' is selected."
        )

        grid.addWidget(lbl2, 2, 0)
        grid.addWidget(self._pip_value_spin, 2, 1)

        # Stop-loss
        lbl3 = QLabel("Stop-Loss (points)")
        lbl3.setToolTip(
            "Distance from your entry price to your stop-loss, measured in points.\n"
            "Setting this auto-sets Take-Profit to 2x (overrideable)."
        )
        self._sl_spin = QDoubleSpinBox()
        self._sl_spin.setRange(0.01, 99_999_999_999.99)
        self._sl_spin.setDecimals(2)
        self._sl_spin.setSuffix(" points")
        self._sl_spin.setSingleStep(1)
        self._sl_spin.setToolTip(
            "Distance from your entry price to your stop-loss, measured in points.\n"
            "Setting this auto-sets Take-Profit to 2x (overrideable)."
        )

        grid.addWidget(lbl3, 3, 0)
        grid.addWidget(self._sl_spin, 3, 1)

        # Take-profit
        lbl4 = QLabel("Take-Profit (points)")
        lbl4.setToolTip(
            "Target distance from your entry price, measured in pips.\n"
            "Defaults to 2x Stop-Loss. Manually edit to override."
        )
        self._tp_spin = QDoubleSpinBox()
        self._tp_spin.setRange(0, 99_999_999_999.99)
        self._tp_spin.setDecimals(2)
        self._tp_spin.setSuffix(" points")
        self._tp_spin.setSingleStep(1)
        self._tp_spin.setToolTip(
            "Target distance from your entry price, measured in pips.\n"
            "Defaults to 2x Stop-Loss. Manually edit to override."
        )

        grid.addWidget(lbl4, 4, 0)
        grid.addWidget(self._tp_spin, 4, 1)

        # Leverage
        lbl5 = QLabel("Leverage")
        lbl5.setToolTip(
            "Maximum position exposure relative to your account capital.\n"
            "Leverage affects margin requirements, not the dollar amount you choose to risk."
        )
        self._leverage_combo = QComboBox()
        self._leverage_combo.addItems(ALLOWED_LEVERAGE)
        self._leverage_combo.setCurrentText(DEFAULT_LEVERAGE)
        self._leverage_combo.setToolTip(
            "Maximum position exposure relative to your account capital.\n"
            "Leverage affects margin requirements, not the dollar amount you choose to risk."
        )

        grid.addWidget(lbl5, 5, 0)
        grid.addWidget(self._leverage_combo, 5, 1)

        return group

    # ── Results group ───────────────────────────────────────────────

    def _build_results_group(self) -> QGroupBox:
        group = QGroupBox("RESULTS")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setColumnStretch(1, 1)

        # Position size
        lbl = QLabel("Position Size")
        lbl.setToolTip("Recommended position size in lots based on your risk settings.")
        self._pos_size_label = QLabel("0.00 lots")
        self._pos_size_label.setObjectName("resultValue")
        self._pos_size_label.setToolTip(
            '<nobr><span style="font-size: 12px; font-weight: normal;">'
            "Recommended position size in lots."
            "</span></nobr>"
        )
        grid.addWidget(lbl, 0, 0)
        grid.addWidget(self._pos_size_label, 0, 1)

        # Lot breakdown
        self._lot_breakdown_label = QLabel("")
        self._lot_breakdown_label.setStyleSheet(
            f"font-size: 11px; color: {TEXT_SECONDARY};"
        )
        self._lot_breakdown_label.setToolTip(
            "Position size broken down into standard, mini, and micro lots (floored)."
        )
        grid.addWidget(self._lot_breakdown_label, 1, 1)

        # Pip value
        lbl2 = QLabel("Pip Value")
        lbl2.setToolTip("Dollar value per pip of movement for your planned position.")
        self._pip_value_label = QLabel("$ 0.00 / pip")
        self._pip_value_label.setObjectName("resultValue")
        self._pip_value_label.setToolTip("Dollar value per pip of movement.")
        grid.addWidget(lbl2, 2, 0)
        grid.addWidget(self._pip_value_label, 2, 1)

        # R:R
        lbl3 = QLabel("Risk / Reward")
        lbl3.setToolTip("Risk-to-reward ratio based on your SL and TP distances.")
        self._rr_label = QLabel("—")
        self._rr_label.setObjectName("resultValue")
        self._rr_label.setToolTip("Risk-to-reward ratio.")
        grid.addWidget(lbl3, 3, 0)
        grid.addWidget(self._rr_label, 3, 1)

        # Potential loss
        lbl4 = QLabel("Potential Loss")
        lbl4.setToolTip("Maximum loss if your stop-loss is hit.")
        self._loss_label = QLabel("$ 0.00")
        self._loss_label.setObjectName("resultValueRisk")
        self._loss_label.setToolTip("Maximum loss if your stop-loss is hit.")
        grid.addWidget(lbl4, 4, 0)
        grid.addWidget(self._loss_label, 4, 1)

        # Potential profit
        lbl5 = QLabel("Potential Profit")
        lbl5.setToolTip("Profit if your take-profit target is reached.")
        self._profit_label = QLabel("$ 0.00")
        self._profit_label.setObjectName("resultValueReward")
        self._profit_label.setToolTip("Profit if your take-profit target is reached.")
        grid.addWidget(lbl5, 5, 0)
        grid.addWidget(self._profit_label, 5, 1)

        # Required margin
        lbl6 = QLabel("Required Margin")
        lbl6.setToolTip(
            "Estimated margin needed to open this position.\n"
            "Based on approximate mid-market prices — verify with your broker."
        )
        self._margin_label = QLabel("—")
        self._margin_label.setObjectName("resultValue")
        self._margin_label.setToolTip(
            '<nobr><span style="font-size: 12px; font-weight: normal;">'
            "Estimated margin needed. Uses approximate prices."
            "</span></nobr>"
        )
        grid.addWidget(lbl6, 6, 0)
        grid.addWidget(self._margin_label, 6, 1)

        layout.addLayout(grid)

        # ── R:R visual bar ──────────────────────────────────────────
        self._rr_bar = RiskRewardBar()
        layout.addWidget(self._rr_bar)

        return group

    # ── Action buttons ──────────────────────────────────────────────

    def _build_actions(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._add_btn = QPushButton("Add to History")
        self._add_btn.setToolTip("Save this calculation to the history table.")

        self._copy_btn = QPushButton("Copy Results")
        self._copy_btn.setObjectName("secondaryButton")
        self._copy_btn.setToolTip(
            "Copy a formatted summary of the results to the clipboard."
        )

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setObjectName("secondaryButton")
        self._clear_btn.setToolTip("Reset all input fields to their default values.")

        self._about_btn = QPushButton("About")
        self._about_btn.setObjectName("secondaryButton")
        self._about_btn.setToolTip("Show application and creator information.")

        layout.addWidget(self._add_btn)
        layout.addWidget(self._copy_btn)
        layout.addWidget(self._clear_btn)
        layout.addWidget(self._about_btn)
        layout.addStretch()

        return widget

    # ── History panel (right side) ──────────────────────────────────

    def _build_history_panel(self) -> QFrame:
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header row
        hdr = QHBoxLayout()
        hdr.setContentsMargins(8, 0, 0, 0)
        title = QLabel("History")
        title.setObjectName("sectionTitle")
        hdr.addWidget(title)
        hdr.addStretch()

        self._clear_history_btn = QPushButton("Clear History")
        self._clear_history_btn.setObjectName("dangerButton")
        self._clear_history_btn.setFixedHeight(28)
        self._clear_history_btn.setToolTip("Remove all saved calculation history.")
        hdr.addWidget(self._clear_history_btn)

        layout.addLayout(hdr)

        # Table
        self._history_table = QTableWidget()
        self._history_table.setColumnCount(8)
        self._history_table.setHorizontalHeaderLabels([
            "#", "Balance", "Risk%", "Risk$", "SL", "TP", "Lots", "R:R",
        ])
        header_view = self._history_table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self._history_table.setColumnWidth(0, 36)
        self._history_table.verticalHeader().setVisible(False)
        self._history_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._history_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._history_table.setAlternatingRowColors(True)
        self._history_table.setToolTip(
            "Saved calculation history. Newest entries appear at the top."
        )

        layout.addWidget(self._history_table, stretch=1)

        # Refresh history display
        self._refresh_history_table()

        return frame

    # ==================================================================
    # Signal wiring
    # ==================================================================

    def _connect_signals(self) -> None:
        # Live recalculation on any input change
        self._balance_spin.valueChanged.connect(self._recalculate)
        self._risk_spin.valueChanged.connect(self._recalculate)
        self._sl_spin.valueChanged.connect(self._on_stop_loss_changed)
        self._tp_spin.valueChanged.connect(self._on_take_profit_changed)
        self._pip_value_spin.valueChanged.connect(self._recalculate)
        self._price_spin.valueChanged.connect(self._on_price_changed)
        self._instrument_combo.currentTextChanged.connect(self._on_instrument_changed)
        self._leverage_combo.currentTextChanged.connect(self._recalculate)

        # Buttons
        self._add_btn.clicked.connect(self._add_to_history)
        self._copy_btn.clicked.connect(self._copy_results)
        self._clear_btn.clicked.connect(self._clear_inputs)
        self._about_btn.clicked.connect(self._show_about)
        self._clear_history_btn.clicked.connect(self._clear_history)

    # ==================================================================
    # Slots
    # ==================================================================

    def _on_instrument_changed(self, name: str) -> None:
        """Auto-fill pip value per lot when a preset instrument is selected.

        When 'Custom' is selected, keep the current pip-value spin editable.
        When switching away from Custom, restore the preset value.
        """
        INSTRUMENT_PRESETS.get(name, {})
        approximate_price = APPROX_PRICES.get(name, 1.0)
        self._price_spin.blockSignals(True)
        self._price_spin.setValue(approximate_price)
        self._price_spin.blockSignals(False)
        self._update_pip_value_for_instrument(name)
        self._recalculate()

    def _update_pip_value_for_instrument(self, name: str) -> None:
        """Refresh the displayed per-lot pip value for the selected instrument."""
        if name == "Custom":
            self._pip_value_spin.setReadOnly(False)
        else:
            pip_value = calculate_instrument_pip_value(
                name,
                self._pip_value_spin.value(),
                self._price_spin.value(),
            )
            self._pip_value_spin.blockSignals(True)
            self._pip_value_spin.setValue(pip_value)
            self._pip_value_spin.blockSignals(False)
            self._pip_value_spin.setReadOnly(True)
        self._pip_value_spin.setEnabled(True)

    def _on_price_changed(self) -> None:
        """Refresh dynamic pip value and calculation when price changes."""
        instrument = self._instrument_combo.currentText()
        if bool(INSTRUMENT_PRESETS.get(instrument, {}).get("dynamic_pip_value", False)):
            self._update_pip_value_for_instrument(instrument)
        self._recalculate()

    def _on_stop_loss_changed(self) -> None:
        """When SL changes, auto-set TP to 2× SL unless user manually edited TP.

        Uses blockSignals to prevent signal recursion: we update the TP spin
        programmatically without triggering _on_take_profit_changed.
        """
        sl = self._sl_spin.value()
        if not self._tp_user_edited:
            new_tp = round(sl * 2, 1)
            self._tp_spin.blockSignals(True)
            self._tp_spin.setValue(new_tp)
            self._tp_spin.blockSignals(False)
        self._recalculate()

    def _on_take_profit_changed(self) -> None:
        """When TP is changed by the user, mark it as manually edited.

        Once marked, SL changes will no longer auto-update TP.
        """
        self._tp_user_edited = True
        self._recalculate()

    def _recalculate(self) -> None:
        """Run the calculation engine and update all result displays."""
        instrument = self._instrument_combo.currentText()
        preset = INSTRUMENT_PRESETS.get(instrument, {})
        pip_multiplier = float(preset.get("pip_multiplier", 100_000))

        setup = TradeSetup(
            balance=self._balance_spin.value(),
            risk_percent=self._risk_spin.value(),
            stop_loss_pips=self._sl_spin.value(),
            pip_value_per_lot=self._pip_value_spin.value(),
            take_profit_pips=(
                self._tp_spin.value() if self._tp_spin.value() > 0 else None
            ),
            instrument=instrument,
            leverage=self._leverage_combo.currentText(),
            pip_multiplier=pip_multiplier,
            current_price=self._price_spin.value(),
            stop_loss_points=self._sl_spin.value(),
            take_profit_points=(
                self._tp_spin.value() if self._tp_spin.value() > 0 else None
            ),
        )

        result, errors = compute_trade(setup)

        if errors:
            self._show_errors(errors)
            return

        self._hide_errors()

        # Risk amount
        self._risk_amount_label.setText(f"$ {result.risk_amount:,.2f}")

        # Position size
        self._pos_size_label.setText(f"{result.position_size:.4f} lots")
        self._lot_breakdown_label.setText(
            f"\u2248 {result.position_size_standard:.2f} std  \u00b7  "
            f"{result.position_size_mini:.1f} mini  \u00b7  "
            f"{result.position_size_micro:.2f} micro"
        )

        # Pip value
        self._pip_value_label.setText(f"$ {result.pip_value:.2f} / pip")

        # R:R
        if result.rr_ratio is not None:
            self._rr_label.setText(f"1 : {result.rr_ratio:.2f}")
            self._rr_bar.set_rr_ratio(result.rr_ratio)
        else:
            self._rr_label.setText("\u2014 (set take-profit)")
            self._rr_bar.set_rr_ratio(None)

        # Loss / Profit
        self._loss_label.setText(f"\u2212$ {result.potential_loss:,.2f}")
        if result.potential_profit is not None:
            self._profit_label.setText(f"+$ {result.potential_profit:,.2f}")
        else:
            self._profit_label.setText("\u2014 (set take-profit)")

        # Required margin
        if result.required_margin is not None:
            self._margin_label.setText(f"$ {result.required_margin:,.2f}")
            self._margin_label.setStyleSheet(
                f"font-size: 14px; font-weight: 700; color: {TEXT_PRIMARY};"
            )
        else:
            self._margin_label.setText("\u2014 (Custom instrument)")
            self._margin_label.setStyleSheet(
                f"font-size: 14px; color: {TEXT_SECONDARY};"
            )

        # Status
        status_parts = [
            f"Position: {result.position_size:.4f} lots",
            f"Risk: ${result.risk_amount:,.2f}",
        ]
        if result.rr_ratio is not None:
            status_parts.append(f"R:R 1:{result.rr_ratio:.2f}")
        if result.volume_message:
            status_parts.append(result.volume_message)
        elif result.tradable_volume is not None:
            status_parts.append(f"Tradable: {result.tradable_volume:.2f} lots")
        self._status_bar.showMessage("  \u00b7  ".join(status_parts))

    def _show_errors(self, errors: list[str]) -> None:
        self._pos_size_label.setText("\u2014")
        self._pos_size_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        self._lot_breakdown_label.setText("")
        self._pip_value_label.setText("\u2014")
        self._rr_label.setText("\u2014")
        self._loss_label.setText("\u2014")
        self._profit_label.setText("\u2014")
        self._margin_label.setText("\u2014")
        self._rr_bar.set_rr_ratio(None)
        self._risk_amount_label.setText("\u2014")
        self._status_bar.showMessage("\u26a0  " + "  |  ".join(errors))

    def _hide_errors(self) -> None:
        self._pos_size_label.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {TEXT_PRIMARY};"
        )

    def _add_to_history(self) -> None:
        """Add the current calculation to the history table."""
        instrument = self._instrument_combo.currentText()
        preset = INSTRUMENT_PRESETS.get(instrument, {})
        pip_multiplier = float(preset.get("pip_multiplier", 100_000))

        setup = TradeSetup(
            balance=self._balance_spin.value(),
            risk_percent=self._risk_spin.value(),
            stop_loss_pips=self._sl_spin.value(),
            pip_value_per_lot=self._pip_value_spin.value(),
            take_profit_pips=(
                self._tp_spin.value() if self._tp_spin.value() > 0 else None
            ),
            instrument=instrument,
            leverage=self._leverage_combo.currentText(),
            pip_multiplier=pip_multiplier,
            current_price=self._price_spin.value(),
            stop_loss_points=self._sl_spin.value(),
            take_profit_points=(
                self._tp_spin.value() if self._tp_spin.value() > 0 else None
            ),
        )
        result, errors = compute_trade(setup)
        if errors:
            return

        entry = HistoryEntry(
            timestamp=datetime.now(),  # noqa: DTZ005
            setup=setup,
            result=result,
        )
        self._history.append(entry)
        self._refresh_history_table()
        self._storage.save_history(self._history)
        self._status_bar.showMessage("Added to history.")

    def _copy_results(self) -> None:
        """Copy a formatted summary to the clipboard."""
        instrument = self._instrument_combo.currentText()
        preset = INSTRUMENT_PRESETS.get(instrument, {})
        pip_multiplier = float(preset.get("pip_multiplier", 100_000))

        setup = TradeSetup(
            balance=self._balance_spin.value(),
            risk_percent=self._risk_spin.value(),
            stop_loss_pips=self._sl_spin.value(),
            pip_value_per_lot=self._pip_value_spin.value(),
            take_profit_pips=(
                self._tp_spin.value() if self._tp_spin.value() > 0 else None
            ),
            instrument=instrument,
            leverage=self._leverage_combo.currentText(),
            pip_multiplier=pip_multiplier,
            current_price=self._price_spin.value(),
            stop_loss_points=self._sl_spin.value(),
            take_profit_points=(
                self._tp_spin.value() if self._tp_spin.value() > 0 else None
            ),
        )
        result, errors = compute_trade(setup)
        if errors:
            return

        lines = [
            f"{'FMM \u2013 Trade Calculation':=^40}",
            f"Instrument:     {setup.instrument}",
            f"Leverage:       {setup.leverage}",
            f"Balance:        ${setup.balance:,.2f}",
            f"Risk:           {setup.risk_percent:.2f}%",
            f"Risk Amount:    ${result.risk_amount:,.2f}",
            f"Stop-Loss:      {setup.stop_loss_points:.1f} points",
        ]
        if setup.take_profit_points and setup.take_profit_points > 0:
            lines.append(f"Take-Profit:    {setup.take_profit_points:.1f} points")
        lines += [
            f"Pip Value/Lot:  ${setup.pip_value_per_lot:.2f}",
            f"{'\u2500'*40}",
            f"Position Size:  {result.position_size:.4f} lots",
            f"Pip Value:      ${result.pip_value:.2f} / pip",
        ]
        if result.rr_ratio is not None:
            lines.append(f"R:R Ratio:      1 : {result.rr_ratio:.2f}")
        lines += [
            f"Potential Loss: ${result.potential_loss:,.2f}",
        ]
        if result.volume_message:
            lines.append(result.volume_message)
        elif result.tradable_volume is not None:
            lines.append(f"Tradable Volume: {result.tradable_volume:.2f} lots")
        if result.potential_profit is not None:
            lines.append(f"Potential Gain: ${result.potential_profit:,.2f}")
        if result.required_margin is not None:
            lines.append(f"Required Margin: ${result.required_margin:,.2f} (approx)")

        QApplication.clipboard().setText("\n".join(lines))
        self._status_bar.showMessage("Results copied to clipboard.")

    def _clear_inputs(self) -> None:
        """Reset all input fields to defaults."""
        # Block TP signals during reset so _on_take_profit_changed doesn't
        # re-set the manual-edit flag.
        self._tp_spin.blockSignals(True)
        self._tp_user_edited = False
        self._tp_spin.setValue(DEFAULT_TAKE_PROFIT_PIPS)
        self._tp_spin.blockSignals(False)
        self._balance_spin.setValue(DEFAULT_BALANCE)
        self._risk_spin.setValue(DEFAULT_RISK_PCT)
        self._sl_spin.setValue(DEFAULT_STOP_LOSS_PIPS)
        self._instrument_combo.setCurrentText(DEFAULT_INSTRUMENT)
        self._leverage_combo.setCurrentText(DEFAULT_LEVERAGE)
        self._pip_value_spin.setValue(DEFAULT_PIP_VALUE_PER_LOT)
        self._price_spin.setValue(APPROX_PRICES[DEFAULT_INSTRUMENT])
        self._recalculate()
        self._status_bar.showMessage("Fields reset to defaults.")

    def _clear_history(self) -> None:
        """Clear all history entries."""
        if not self._history:
            return
        dialog = QMessageBox(self)
        dialog.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
        )
        dialog.setWindowTitle(APP_NAME)
        dialog.setText("Clear History")
        dialog.setInformativeText("Remove all history entries?")
        dialog.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        dialog.setDefaultButton(QMessageBox.StandardButton.No)
        dialog.setMinimumWidth(600)
        reply = dialog.exec()
        if reply == QMessageBox.StandardButton.Yes:
            self._history.clear()
            self._refresh_history_table()
            self._storage.clear_history()
            self._status_bar.showMessage("History cleared.")

    def _show_about(self) -> None:
        """Show application and creator information."""
        dialog = QMessageBox(self)
        dialog.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
        )
        dialog.setWindowTitle(f"About {APP_NAME}")
        dialog.setText(
            "<h2>Forex Money Manager</h2>"
            "<p><b>Created by</b><br>"
            "Hesam Amani<br>"
            "Developer &amp; Creator</p>"
            "<p><b>Contact</b><br>"
            '<a href="mailto:hesam.amani1999@gmail.com">'
            "hesam.amani1999@gmail.com</a><br>"
            "GitHub: hesam-amani</p>"
            "<p><b>Application</b><br>"
            f"Version {APP_VERSION}<br>"
            "&copy; 2026 Hesam Amani</p>"
            "<p>Built with &#10084; and code</p>"
        )
        dialog.setMinimumWidth(600)
        dialog.exec()

    # ==================================================================
    # History table
    # ==================================================================

    def _refresh_history_table(self) -> None:
        """Rebuild the history table from the internal list."""
        table = self._history_table
        table.setRowCount(len(self._history))

        for i, entry in enumerate(reversed(self._history)):
            row = len(self._history) - 1 - i  # newest on top
            s = entry.setup
            r = entry.result

            items = [
                str(row + 1),
                f"${s.balance:,.0f}",
                f"{s.risk_percent:.2f}%",
                f"${r.risk_amount:,.2f}",
                f"{(s.stop_loss_points if s.stop_loss_points is not None else s.stop_loss_pips):.1f}",
                f"{(s.take_profit_points if s.take_profit_points is not None else s.take_profit_pips):.1f}"
                if (s.take_profit_points is not None or s.take_profit_pips)
                else "\u2014",
                f"{r.position_size:.4f}",
                f"1:{r.rr_ratio:.2f}" if r.rr_ratio else "\u2014",
            ]

            for col, text in enumerate(items):
                cell = QTableWidgetItem(text)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(i, col, cell)

    # ==================================================================
    # Settings persistence
    # ==================================================================

    def _load_settings_to_ui(self) -> None:
        """Populate UI from saved settings.

        Uses blockSignals on the TP spin to avoid triggering auto-update
        during the initial load from settings.
        """
        s = self._settings
        self._balance_spin.setValue(s.balance)
        self._risk_spin.setValue(s.risk_percent)
        self._sl_spin.setValue(s.stop_loss_pips)

        # Block TP signal during load so the auto-SL→TP update doesn't
        # overwrite the saved take-profit value.
        self._tp_spin.blockSignals(True)
        self._tp_spin.setValue(s.take_profit_pips)
        self._tp_spin.blockSignals(False)

        self._instrument_combo.setCurrentText(s.instrument)
        self._leverage_combo.setCurrentText(s.leverage)
        self._pip_value_spin.setValue(s.pip_value_per_lot)
        self._price_spin.setValue(s.current_price)
        self._update_pip_value_for_instrument(self._instrument_combo.currentText())

    def closeEvent(self, event) -> None:
        """Save settings and window geometry on close."""
        self._settings.balance = self._balance_spin.value()
        self._settings.risk_percent = self._risk_spin.value()
        self._settings.stop_loss_pips = self._sl_spin.value()
        self._settings.take_profit_pips = self._tp_spin.value()
        self._settings.instrument = self._instrument_combo.currentText()
        self._settings.leverage = self._leverage_combo.currentText()
        self._settings.pip_value_per_lot = self._pip_value_spin.value()
        self._settings.current_price = self._price_spin.value()
        self._settings.window_width = self.width()
        self._settings.window_height = self.height()
        self._settings.window_x = self.x()
        self._settings.window_y = self.y()
        self._settings.save()
        event.accept()
