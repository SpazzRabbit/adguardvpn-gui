from __future__ import annotations

from PySide6.QtCore import Property, QEasingCurve, QPointF, QPropertyAnimation, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from adguard_gui.theme import (
    ACCENT,
    BG_HOVER,
    BORDER_STRONG,
    DANGER,
    TEXT_MUTED,
    WARNING,
)


class ConnectButton(QWidget):
    """Large circular connect/disconnect button — visual centerpiece of the Home page."""

    clicked = Signal()

    GLOW_PADDING = 26  # запас под внешний glow вокруг кнопки

    def __init__(self, parent: QWidget | None = None, size: int = 200) -> None:
        super().__init__(parent)
        self._size = size
        self._state = "disconnected"
        self._hover = False
        self._pulse = 0.0
        total = size + 2 * self.GLOW_PADDING
        self.setFixedSize(total, total)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._anim = QPropertyAnimation(self, b"pulse", self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setDuration(1200)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)

    def sizeHint(self) -> QSize:
        total = self._size + 2 * self.GLOW_PADDING
        return QSize(total, total)

    def set_state(self, state: str) -> None:
        if state == self._state:
            return
        self._state = state
        if state in ("connecting", "disconnecting"):
            self._anim.start()
        else:
            self._anim.stop()
            self._pulse = 0.0
        self.update()

    def _get_pulse(self) -> float:
        return self._pulse

    def _set_pulse(self, value: float) -> None:
        self._pulse = value
        self.update()

    pulse = Property(float, _get_pulse, _set_pulse)

    def enterEvent(self, event) -> None:
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def _palette(self) -> tuple[QColor, QColor, QColor]:
        """Возвращает (fill, accent, icon)."""
        if self._state == "connected":
            if self._hover:
                return QColor(DANGER), QColor(DANGER), QColor("#ffffff")
            return QColor(ACCENT), QColor(ACCENT), QColor("#0f1a12")
        if self._state in ("connecting", "disconnecting"):
            return QColor(WARNING), QColor(WARNING), QColor("#1a1408")
        if self._state == "error":
            return QColor(DANGER), QColor(DANGER), QColor("#ffffff")
        return QColor(BG_HOVER), QColor(BORDER_STRONG), QColor(TEXT_MUTED)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # rect основной кнопки в центре виджета, glow рисуется внутрь GLOW_PADDING
        cx = self.width() / 2
        cy = self.height() / 2
        half = self._size / 2
        outer = QRectF(cx - half, cy - half, self._size, self._size)

        fill, accent, icon_color = self._palette()

        if self._state == "connected":
            for grow, alpha in ((14, 60), (26, 30)):
                glow = QColor(accent); glow.setAlpha(alpha)
                p.setBrush(glow); p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(outer.adjusted(-grow, -grow, grow, grow))
        elif self._state in ("connecting", "disconnecting"):
            alpha = int(35 + 70 * self._pulse)
            glow = QColor(accent); glow.setAlpha(alpha)
            p.setBrush(glow); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(outer.adjusted(-16, -16, 16, 16))

        # фоновый круг
        p.setBrush(fill)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(outer)

        if self._state != "disconnected":
            inner = outer.adjusted(6, 6, -6, -6)
            hl = QColor("#ffffff"); hl.setAlpha(18)
            p.setBrush(hl); p.drawEllipse(inner)

        self._draw_power_icon(p, cx, cy, icon_color)
        p.end()

    def _draw_power_icon(self, p: QPainter, cx: float, cy: float, color: QColor) -> None:
        # Power-иконка: окружность с симметричным разрывом сверху + вертикальная палочка.
        r = self._size * 0.24
        thickness = max(4.5, self._size * 0.04)

        pen = QPen(color)
        pen.setWidthF(thickness)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)

        # Qt углы: 0° = 3 часа, положительные — CCW (визуально против часовой).
        # 90° = верх (12 часов). Делаем разрыв gap_deg градусов симметрично вокруг 90°.
        gap_deg = 70
        # Дуга идёт CCW от правого края разрыва, через низ, до левого края.
        start_angle = 90 - gap_deg / 2          # правый край разрыва (≈55°)
        span = -(360 - gap_deg)                 # CW обход (через 0° → 270° → 180° → 125°)
        arc_rect = QRectF(cx - r, cy - r, 2 * r, 2 * r)
        p.drawArc(arc_rect, int(start_angle * 16), int(span * 16))

        # Вертикальная палочка строго в центре, чуть выходит за дугу сверху и доходит примерно до 30% высоты круга.
        line_top = cy - r - thickness * 0.35
        line_bottom = cy - r * 0.25
        p.drawLine(QPointF(cx, line_top), QPointF(cx, line_bottom))
