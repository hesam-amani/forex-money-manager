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
    """Horizontal bar that visualises the risk ↔ reward ratio."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rr_ratio: float | None = None
        self.setMinimumSize(200, 52)
        self.setSizePolicy(self.sizePolicy().horizontalPolicy(), self.sizePolicy().verticalPolicy())

    def set_rr_ratio(self, ratio: float | None) -> None:
        """Update the displayed ratio; None hides the split until TP is set."""
        self._rr_ratio = ratio if ratio is not None and ratio > 0 else None
        self.update()

    def paintEvent(self, event) -> None:
        del event
        w = max(1, self.width())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bar_h = 14.0
        bar_y = 6.0
        radius = 7.0
        label_y = bar_y + bar_h + 5.0
        label_h = max(16.0, self.height() - label_y - 2.0)

        # With no TP, keep the bar visually neutral at 1:1.
        rr = self._rr_ratio if self._rr_ratio is not None else 1.0
        risk_frac = 1.0 / (1.0 + rr)
        split_x = max(1.0, min(float(w) - 1.0, w * risk_frac))

        # Draw one rounded background first, then clip the two colours into it.
        bar_rect = QRectF(0, bar_y, float(w), bar_h)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#21262d"))
        painter.drawRoundedRect(bar_rect, radius, radius)

        painter.save()
        painter.setClipRect(QRectF(0, bar_y, split_x, bar_h))
        risk_grad = QLinearGradient(QPointF(0, bar_y), QPointF(0, bar_y + bar_h))
        risk_grad.setColorAt(0, QColor("#f85149"))
        risk_grad.setColorAt(1, QColor("#da3633"))
        painter.setBrush(QBrush(risk_grad))
        painter.drawRoundedRect(bar_rect, radius, radius)
        painter.restore()

        painter.save()
        painter.setClipRect(QRectF(split_x, bar_y, float(w) - split_x, bar_h))
        reward_grad = QLinearGradient(QPointF(0, bar_y), QPointF(0, bar_y + bar_h))
        reward_grad.setColorAt(0, QColor("#3fb950"))
        reward_grad.setColorAt(1, QColor("#2ea043"))
        painter.setBrush(QBrush(reward_grad))
        painter.drawRoundedRect(bar_rect, radius, radius)
        painter.restore()

        font = QFont("Segoe UI", 10)
        painter.setFont(font)
        painter.setPen(QPen(QColor(RISK_RED)))
        painter.drawText(
            QRectF(4, label_y, max(1.0, split_x - 8), label_h),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "Loss",
        )
        painter.setPen(QPen(QColor(REWARD_GREEN)))
        painter.drawText(
            QRectF(split_x + 4, label_y, max(1.0, float(w) - split_x - 8), label_h),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            "Gain",
        )

        painter.setPen(QPen(QColor("#e6edf3"), 2))
        painter.drawLine(
            QPointF(split_x, bar_y - 1),
            QPointF(split_x, bar_y + bar_h + 1),
        )
        painter.end()
