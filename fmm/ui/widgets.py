"""Custom reusable widgets with no business logic."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt  # pyright: ignore[reportMissingImports]
from PySide6.QtGui import (  # pyright: ignore[reportMissingImports]
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPen,
)
from PySide6.QtWidgets import QWidget  # pyright: ignore[reportMissingImports]

from .styles import REWARD_GREEN, RISK_RED


class RiskRewardBar(QWidget):
    """Horizontal bar that visualises the risk ↔ reward ratio.

    The red portion (left) represents potential loss, the green portion
    (right) represents potential profit.  The divider moves based on the
    R:R ratio.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rr_ratio: float = 1.0  # default 1:1
        self.setMinimumHeight(52)
        self.setMinimumWidth(200)

    def set_rr_ratio(self, ratio: float | None) -> None:
        """Update the displayed ratio (None → show 1:1 placeholder)."""
        self._rr_ratio = ratio if ratio is not None and ratio > 0 else 1.0
        self.update()

    # ── Painting ────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        w = self.width()
        self.height()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bar_h = 14
        bar_y = 6.0
        radius = 7.0

        # The split point: risk occupies 1/(1+rr) of the width
        rr = self._rr_ratio
        total = 1.0 + rr
        risk_frac = 1.0 / total if total > 0 else 0.5
        split_x = w * risk_frac

        # ── Risk portion (red) ──────────────────────────────────────
        risk_rect = QRectF(0, bar_y, split_x, bar_h)
        risk_grad = QLinearGradient(QPointF(0, bar_y), QPointF(0, bar_y + bar_h))
        risk_grad.setColorAt(0, QColor("#f85149"))
        risk_grad.setColorAt(1, QColor("#da3633"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(risk_grad))
        painter.drawRoundedRect(risk_rect, radius, radius)

        # ── Reward portion (green) ──────────────────────────────────
        reward_rect = QRectF(split_x, bar_y, w - split_x, bar_h)
        reward_grad = QLinearGradient(QPointF(0, bar_y), QPointF(0, bar_y + bar_h))
        reward_grad.setColorAt(0, QColor("#3fb950"))
        reward_grad.setColorAt(1, QColor("#2ea043"))
        painter.setBrush(QBrush(reward_grad))
        painter.drawRoundedRect(reward_rect, radius, radius)

        # ── Labels below bar ────────────────────────────────────────
        font = QFont("Segoe UI", 10)
        painter.setFont(font)

        painter.setPen(QPen(QColor(RISK_RED)))
        painter.drawText(
            QRectF(4, bar_y + bar_h + 4, split_x - 8, 18),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "Loss",
        )

        painter.setPen(QPen(QColor(REWARD_GREEN)))
        painter.drawText(
            QRectF(split_x + 4, bar_y + bar_h + 4, w - split_x - 8, 18),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            "Gain",
        )

        # ── Divider marker ──────────────────────────────────────────
        painter.setPen(QPen(QColor("#e6edf3"), 2))
        painter.drawLine(
            QPointF(split_x, bar_y - 1),
            QPointF(split_x, bar_y + bar_h + 1),
        )

        painter.end()
