"""Main application window."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt  # pyright: ignore[reportMissingImports]
from PySide6.QtWidgets import (
    QApplication, QDoubleSpinBox, QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QMainWindow, QMessageBox, QPushButton, QSizePolicy,
    QSplitter, QStatusBar, QTableWidget, QTableWidgetItem, QToolTip, QVBoxLayout,
    QWidget,
)

from ..config.settings import AppSettings
from ..core.calculator import compute_trade
from ..core.constants import (
    APP_NAME, APP_VERSION, DEFAULT_BALANCE, DEFAULT_PIP_VALUE_PER_LOT,
    DEFAULT_RISK_PCT, DEFAULT_STOP_LOSS_PIPS, DEFAULT_TAKE_PROFIT_PIPS,
)
from ..core.models import HistoryEntry, TradeSetup
from ..services.storage import StorageService
from .styles import ACCENT, RISK_RED, TEXT_PRIMARY, TEXT_SECONDARY
from .widgets import RiskRewardBar


class MainWindow(QMainWindow):
    """Single-window GUI for simple, broker-independent position sizing."""

    def __init__(self) -> None:
        super().__init__()
        self._settings = AppSettings.load()
        self._storage = StorageService()
        self._history = self._storage.load_history()
        self._tp_user_edited = False
        tooltip_font = QApplication.font()
        tooltip_font.setPointSize(12)
        QToolTip.setFont(tooltip_font)
        self._build_ui()
        self._load_settings_to_ui()
        self._connect_signals()
        self._recalculate()

    def _build_ui(self) -> None:
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(760, 560)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        if self._settings.window_x >= 0 and self._settings.window_y >= 0:
            self.setGeometry(self._settings.window_x, self._settings.window_y,
                             self._settings.window_width, self._settings.window_height)
        else:
            self.resize(self._settings.window_width, self._settings.window_height)
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 8)
        main_layout.setSpacing(10)
        header = QHBoxLayout()
        title = QLabel("FMM")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {ACCENT}; letter-spacing: 1px;")
        subtitle = QLabel("Forex Money Manager")
        subtitle.setStyleSheet(f"font-size: 14px; color: {TEXT_SECONDARY};")
        header.addWidget(title)
        header.addWidget(subtitle)
        header.addStretch()
        main_layout.addLayout(header)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_input_panel())
        splitter.addWidget(self._build_history_panel())
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter, stretch=1)
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Ready")

    def _build_input_panel(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(self._build_account_group())
        layout.addWidget(self._build_trade_group())
        layout.addWidget(self._build_results_group())
        layout.addStretch(1)
        layout.addWidget(self._build_actions(), 0, Qt.AlignmentFlag.AlignBottom)
        return widget

    def _new_spin(self, minimum: float, maximum: float, decimals: int, step: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setDecimals(decimals)
        spin.setSingleStep(step)
        spin.setGroupSeparatorShown(True)
        return spin

    def _build_account_group(self) -> QGroupBox:
        group = QGroupBox("ACCOUNT & RISK")
        grid = QGridLayout(group)
        grid.setSpacing(8)
        grid.setColumnStretch(1, 1)
        self._balance_spin = self._new_spin(0.01, 1_000_000_000, 2, 100)
        self._balance_spin.setPrefix("$ ")
        self._risk_spin = self._new_spin(0.01, 100, 2, 0.25)
        self._risk_spin.setSuffix(" %")
        self._risk_amount_label = QLabel("$ 0.00")
        self._risk_amount_label.setObjectName("resultValueRisk")
        for row, label, control in ((0, "Balance", self._balance_spin), (1, "Risk %", self._risk_spin), (2, "Risk Amount", self._risk_amount_label)):
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(control, row, 1)
        return group

    def _build_trade_group(self) -> QGroupBox:
        group = QGroupBox("TRADE SETUP")
        grid = QGridLayout(group)
        grid.setSpacing(8)
        grid.setColumnStretch(1, 1)
        self._pip_value_spin = self._new_spin(0.01, 100_000, 4, 0.5)
        self._pip_value_spin.setPrefix("$ ")
        self._pip_value_spin.setToolTip("USD value of one pip for one standard lot.\nEnter the exact value supplied by your broker for the instrument.")
        self._sl_spin = self._new_spin(0.01, 99_999_999, 2, 1)
        self._sl_spin.setSuffix(" pips")
        self._sl_spin.setToolTip("Distance from entry to stop-loss in pips.")
        self._tp_spin = self._new_spin(0, 99_999_999, 2, 1)
        self._tp_spin.setSuffix(" pips")
        self._tp_spin.setToolTip("Distance from entry to take-profit in pips.\nDefaults to 2× stop-loss until you edit it.")
        for row, label, control in ((0, "Pip Value / Lot", self._pip_value_spin), (1, "Stop-Loss", self._sl_spin), (2, "Take-Profit", self._tp_spin)):
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(control, row, 1)
        return group

    def _build_results_group(self) -> QGroupBox:
        group = QGroupBox("RESULTS")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        grid = QGridLayout()
        grid.setSpacing(6)
        grid.setColumnStretch(1, 1)
        self._pos_size_label = QLabel("0.000000 lots")
        self._pos_size_label.setObjectName("resultValue")
        self._pip_value_label = QLabel("$ 0.00 / pip")
        self._pip_value_label.setObjectName("resultValue")
        self._rr_label = QLabel("—")
        self._rr_label.setObjectName("resultValue")
        self._loss_label = QLabel("$ 0.00")
        self._loss_label.setObjectName("resultValueRisk")
        self._profit_label = QLabel("—")
        self._profit_label.setObjectName("resultValueReward")
        for row, label, value in ((0, "Position Size", self._pos_size_label), (1, "Pip Value", self._pip_value_label), (2, "Risk / Reward", self._rr_label), (3, "Potential Loss", self._loss_label), (4, "Potential Profit", self._profit_label)):
            grid.addWidget(QLabel(label), row, 0)
            grid.addWidget(value, row, 1)
        layout.addLayout(grid)
        self._rr_bar = RiskRewardBar()
        layout.addWidget(self._rr_bar, 0, Qt.AlignmentFlag.AlignTop)
        return group

    def _build_actions(self) -> QWidget:
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self._add_btn = QPushButton("Add to History")
        self._copy_btn = QPushButton("Copy Results")
        self._copy_btn.setObjectName("secondaryButton")
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setObjectName("secondaryButton")
        self._about_btn = QPushButton("About")
        self._about_btn.setObjectName("secondaryButton")
        for button in (self._add_btn, self._copy_btn, self._clear_btn, self._about_btn):
            layout.addWidget(button)
        layout.addStretch()
        return widget

    def _build_history_panel(self) -> QFrame:
        frame = QFrame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)
        header = QHBoxLayout()
        header.setContentsMargins(2, 0, 2, 0)
        title = QLabel("History")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        self._clear_history_btn = QPushButton("Clear History")
        self._clear_history_btn.setObjectName("dangerButton")
        header.addWidget(self._clear_history_btn)
        layout.addLayout(header)
        self._history_table = QTableWidget()
        self._history_table.setColumnCount(7)
        self._history_table.setHorizontalHeaderLabels(["#", "Balance", "Risk%", "Risk$", "SL", "TP", "Lots"])
        header_view = self._history_table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._history_table.setColumnWidth(0, 48)
        for column in range(1, 7):
            header_view.setSectionResizeMode(column, QHeaderView.ResizeMode.Stretch)
        self._history_table.verticalHeader().setVisible(False)
        self._history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._history_table.setAlternatingRowColors(True)
        layout.addWidget(self._history_table, stretch=1)
        self._refresh_history_table()
        return frame

    def _connect_signals(self) -> None:
        self._balance_spin.valueChanged.connect(self._recalculate)
        self._risk_spin.valueChanged.connect(self._recalculate)
        self._pip_value_spin.valueChanged.connect(self._recalculate)
        self._sl_spin.valueChanged.connect(self._on_stop_loss_changed)
        self._tp_spin.valueChanged.connect(self._on_take_profit_changed)
        self._add_btn.clicked.connect(self._add_to_history)
        self._copy_btn.clicked.connect(self._copy_results)
        self._clear_btn.clicked.connect(self._clear_inputs)
        self._about_btn.clicked.connect(self._show_about)
        self._clear_history_btn.clicked.connect(self._clear_history)

    def _make_setup(self) -> TradeSetup:
        tp = self._tp_spin.value()
        return TradeSetup(balance=self._balance_spin.value(), risk_percent=self._risk_spin.value(), stop_loss_pips=self._sl_spin.value(), pip_value_per_lot=self._pip_value_spin.value(), take_profit_pips=tp if tp > 0 else None)

    def _on_stop_loss_changed(self) -> None:
        if not self._tp_user_edited:
            self._tp_spin.blockSignals(True)
            self._tp_spin.setValue(round(self._sl_spin.value() * 2, 2))
            self._tp_spin.blockSignals(False)
        self._recalculate()

    def _on_take_profit_changed(self) -> None:
        self._tp_user_edited = True
        self._recalculate()

    def _recalculate(self) -> None:
        result, errors = compute_trade(self._make_setup())
        if errors:
            self._show_errors(errors)
            return
        self._hide_errors()
        self._risk_amount_label.setText(f"$ {result.risk_amount:,.2f}")
        self._pos_size_label.setText(f"{result.position_size:.6f} lots")
        self._pip_value_label.setText(f"$ {result.pip_value:.2f} / pip")
        self._loss_label.setText(f"−$ {result.potential_loss:,.2f}")
        if result.rr_ratio is None:
            self._rr_label.setText("— (set take-profit)")
            self._profit_label.setText("— (set take-profit)")
            self._rr_bar.set_rr_ratio(None)
        else:
            self._rr_label.setText(f"1 : {result.rr_ratio:.2f}")
            self._profit_label.setText(f"+$ {result.potential_profit:,.2f}")
            self._rr_bar.set_rr_ratio(result.rr_ratio)
        self._status_bar.showMessage(f"Position: {result.position_size:.6f} lots  ·  Risk: ${result.risk_amount:,.2f}" + (f"  ·  R:R 1:{result.rr_ratio:.2f}" if result.rr_ratio else ""))

    def _show_errors(self, errors: list[str]) -> None:
        for label in (self._risk_amount_label, self._pos_size_label, self._pip_value_label, self._rr_label, self._loss_label, self._profit_label):
            label.setText("—")
        self._rr_bar.set_rr_ratio(None)
        self._status_bar.showMessage("⚠  " + "  |  ".join(errors))

    def _hide_errors(self) -> None:
        self._pos_size_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {TEXT_PRIMARY};")

    def _add_to_history(self) -> None:
        setup = self._make_setup()
        result, errors = compute_trade(setup)
        if errors:
            return
        self._history.append(HistoryEntry(datetime.now(), setup, result))
        self._storage.save_history(self._history)
        self._refresh_history_table()
        self._status_bar.showMessage("Added to history.")

    def _copy_results(self) -> None:
        setup = self._make_setup()
        result, errors = compute_trade(setup)
        if errors:
            return
        lines = ["FMM – Trade Calculation", "=" * 32, f"Balance:        ${setup.balance:,.2f}", f"Risk:           {setup.risk_percent:.2f}%", f"Risk Amount:    ${result.risk_amount:,.2f}", f"Pip Value/Lot:  ${setup.pip_value_per_lot:.4f}", f"Stop-Loss:      {setup.stop_loss_pips:.2f} pips"]
        if setup.take_profit_pips:
            lines.append(f"Take-Profit:    {setup.take_profit_pips:.2f} pips")
        lines += ["-" * 32, f"Position Size:  {result.position_size:.6f} lots", f"Pip Value:      ${result.pip_value:.2f} / pip", f"Potential Loss: ${result.potential_loss:,.2f}"]
        if result.rr_ratio is not None:
            lines += [f"R:R Ratio:      1 : {result.rr_ratio:.2f}", f"Potential Gain: ${result.potential_profit:,.2f}"]
        QApplication.clipboard().setText("\n".join(lines))
        self._status_bar.showMessage("Results copied to clipboard.")

    def _clear_inputs(self) -> None:
        self._tp_user_edited = False
        self._balance_spin.setValue(DEFAULT_BALANCE)
        self._risk_spin.setValue(DEFAULT_RISK_PCT)
        self._pip_value_spin.setValue(DEFAULT_PIP_VALUE_PER_LOT)
        self._sl_spin.setValue(DEFAULT_STOP_LOSS_PIPS)
        self._tp_spin.blockSignals(True)
        self._tp_spin.setValue(DEFAULT_TAKE_PROFIT_PIPS)
        self._tp_spin.blockSignals(False)
        self._recalculate()
        self._status_bar.showMessage("Fields reset to defaults.")

    def _clear_history(self) -> None:
        if not self._history:
            return
        reply = QMessageBox.question(self, APP_NAME, "Remove all history entries?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._history.clear()
            self._storage.clear_history()
            self._refresh_history_table()
            self._status_bar.showMessage("History cleared.")

    def _show_about(self) -> None:
        QMessageBox.about(self, f"About {APP_NAME}", f"<h2>{APP_NAME}</h2>" f"<p>Version {APP_VERSION}</p>" "<p>A simple position-sizing calculator built with Python and PySide6.</p>" "<p>Created by Hesam Amani.</p>")

    def _refresh_history_table(self) -> None:
        table = self._history_table
        table.setRowCount(len(self._history))
        for row, entry in enumerate(reversed(self._history)):
            s = entry.setup
            values = (str(len(self._history) - row), f"${s.balance:,.0f}", f"{s.risk_percent:.2f}%", f"${entry.result.risk_amount:,.2f}", f"{s.stop_loss_pips:.2f}", f"{s.take_profit_pips:.2f}" if s.take_profit_pips else "—", f"{entry.result.position_size:.6f}")
            for column, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row, column, item)

    def _load_settings_to_ui(self) -> None:
        s = self._settings
        self._balance_spin.setValue(s.balance)
        self._risk_spin.setValue(s.risk_percent)
        self._pip_value_spin.setValue(s.pip_value_per_lot)
        self._sl_spin.setValue(s.stop_loss_pips)
        self._tp_spin.blockSignals(True)
        self._tp_spin.setValue(s.take_profit_pips)
        self._tp_spin.blockSignals(False)

    def closeEvent(self, event) -> None:
        s = self._settings
        s.balance = self._balance_spin.value()
        s.risk_percent = self._risk_spin.value()
        s.pip_value_per_lot = self._pip_value_spin.value()
        s.stop_loss_pips = self._sl_spin.value()
        s.take_profit_pips = self._tp_spin.value()
        s.window_width = self.width()
        s.window_height = self.height()
        s.window_x = self.x()
        s.window_y = self.y()
        s.save()
        event.accept()
