"""Dark-theme QSS stylesheet for the application."""

from __future__ import annotations

# ── Colour palette ──────────────────────────────────────────────────────
BG_DARK = "#0d1117"        # Deepest background
BG_PANEL = "#161b22"       # Panel / card background
BG_INPUT = "#0d1117"       # Input field background
BG_INPUT_FOCUS = "#111820"  # Input field when focused
BORDER = "#30363d"          # Default borders
BORDER_FOCUS = "#58a6ff"    # Focus ring
ACCENT = "#58a6ff"          # Primary accent (blue)
ACCENT_HOVER = "#79c0ff"    # Accent hover
RISK_RED = "#f85149"        # Risk / loss colour
REWARD_GREEN = "#3fb950"    # Reward / profit colour
TEXT_PRIMARY = "#e6edf3"    # Primary text
TEXT_SECONDARY = "#8b949e"  # Muted / secondary text
TEXT_DIM = "#484f58"        # Very dim text
DANGER = "#f85149"          # Error / warning
SUCCESS = "#3fb950"         # Success

STYLESHEET = f"""
/* ── Global ──────────────────────────────────────────────────────── */
QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", sans-serif;
    font-size: 13px;
}}

/* ── Main window ─────────────────────────────────────────────────── */
QMainWindow {{
    background-color: {BG_DARK};
}}

/* ── Frames / Panels / Group Boxes ───────────────────────────────── */
QFrame, QGroupBox {{
    background-color: {BG_PANEL};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}

QGroupBox {{
    font-weight: 600;
    font-size: 13px;
    padding-top: 18px;
    margin-top: 8px;
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    color: {TEXT_SECONDARY};
}}

/* ── Labels ──────────────────────────────────────────────────────── */
QLabel {{
    background: transparent;
    border: none;
    color: {TEXT_PRIMARY};
}}

QLabel#sectionTitle {{
    font-size: 15px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
}}

QLabel#resultLabel {{
    color: {TEXT_SECONDARY};
    font-size: 13px;
}}

QLabel#resultValue {{
    font-size: 15px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
}}

QLabel#resultValueRisk {{
    font-size: 15px;
    font-weight: 700;
    color: {RISK_RED};
}}

QLabel#resultValueReward {{
    font-size: 15px;
    font-weight: 700;
    color: {REWARD_GREEN};
}}

QLabel#errorLabel {{
    color: {DANGER};
    font-size: 12px;
    background: transparent;
    border: none;
}}

QLabel#dimLabel {{
    color: {TEXT_DIM};
    font-size: 11px;
    background: transparent;
    border: none;
}}

/* ── Line edits / Spin boxes ─────────────────────────────────────── */
QLineEdit, QDoubleSpinBox, QSpinBox {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 14px;
    selection-background-color: {ACCENT};
    min-height: 18px;
}}

QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus {{
    border: 1px solid {BORDER_FOCUS};
    background-color: {BG_INPUT_FOCUS};
}}

QLineEdit:hover, QDoubleSpinBox:hover, QSpinBox:hover {{
    border: 1px solid {TEXT_DIM};
}}

QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
QSpinBox::up-button, QSpinBox::down-button {{
    background-color: {BORDER};
    border: none;
    width: 20px;
}}

QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover,
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background-color: {TEXT_DIM};
}}

QDoubleSpinBox::up-arrow, QDoubleSpinBox::down-arrow,
QSpinBox::up-arrow, QSpinBox::down-arrow {{
    width: 8px;
    height: 8px;
}}

/* ── Combo box ───────────────────────────────────────────────────── */
QComboBox {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 14px;
    min-height: 18px;
}}

QComboBox:hover {{
    border: 1px solid {TEXT_DIM};
}}

QComboBox:focus {{
    border: 1px solid {BORDER_FOCUS};
}}

QComboBox::drop-down {{
    border: none;
    width: 28px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {TEXT_SECONDARY};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    selection-background-color: {ACCENT};
    selection-color: {BG_DARK};
    padding: 4px;
}}

/* ── Buttons ─────────────────────────────────────────────────────── */
QPushButton {{
    background-color: {ACCENT};
    color: {BG_DARK};
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
    min-height: 18px;
}}

QPushButton:hover {{
    background-color: {ACCENT_HOVER};
}}

QPushButton:pressed {{
    background-color: {BORDER_FOCUS};
}}

QPushButton:disabled {{
    background-color: {BORDER};
    color: {TEXT_DIM};
}}

QPushButton#secondaryButton {{
    background-color: transparent;
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER};
}}

QPushButton#secondaryButton:hover {{
    background-color: {BORDER};
    color: {TEXT_PRIMARY};
}}

QPushButton#dangerButton {{
    background-color: transparent;
    color: {RISK_RED};
    border: 1px solid {RISK_RED};
}}

QPushButton#dangerButton:hover {{
    background-color: {RISK_RED};
    color: {BG_DARK};
}}

/* ── Tables ──────────────────────────────────────────────────────── */
QTableWidget {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    gridline-color: {BORDER};
    selection-background-color: {ACCENT};
    selection-color: {BG_DARK};
    font-size: 12px;
}}

QTableWidget::item {{
    padding: 6px 10px;
    border: none;
}}

QTableWidget::item:selected {{
    background-color: {ACCENT};
    color: {BG_DARK};
}}

QHeaderView::section {{
    background-color: {BG_PANEL};
    color: {TEXT_SECONDARY};
    border: none;
    border-bottom: 1px solid {BORDER};
    border-right: 1px solid {BORDER};
    padding: 8px 10px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
}}

QHeaderView::section:last {{
    border-right: none;
}}

/* ── Scroll bars ─────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {TEXT_DIM};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {BORDER};
    border-radius: 4px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {TEXT_DIM};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ── Splitter ────────────────────────────────────────────────────── */
QSplitter::handle {{
    background: {BORDER};
    width: 2px;
}}

QSplitter::handle:hover {{
    background: {TEXT_DIM};
}}

/* ── Tooltips ────────────────────────────────────────────────────── */
QToolTip {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 10px;
    font-size: 12px;
    font-weight: normal;
}}

/* ── Status bar ──────────────────────────────────────────────────── */
QStatusBar {{
    background-color: {BG_PANEL};
    color: {TEXT_SECONDARY};
    border-top: 1px solid {BORDER};
    font-size: 11px;
}}

/* ── Menu bar (if used) ─────────────────────────────────────────── */
QMenuBar {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border-bottom: 1px solid {BORDER};
}}

QMenuBar::item:selected {{
    background-color: {BORDER};
}}

QMenu {{
    background-color: {BG_PANEL};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
}}

QMenu::item:selected {{
    background-color: {ACCENT};
    color: {BG_DARK};
}}
"""
