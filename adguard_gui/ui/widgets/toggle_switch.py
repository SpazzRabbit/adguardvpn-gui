from __future__ import annotations

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget

from adguard_gui.theme import ACCENT, BG_ELEVATED, BORDER_STRONG, TEXT


class ToggleSwitch(QWidget):
    toggled = Signal(bool)

    def __init__(self, checked: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._checked = checked
        self._offset = 1.0 if checked else 0.0
        self.setFixedSize(46, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def sizeHint(self) -> QSize:
        return QSize(46, 24)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, value: bool, *, animate: bool = True) -> None:
        if value == self._checked:
            return
        self._checked = value
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._offset)
            self._anim.setEndValue(1.0 if value else 0.0)
            self._anim.start()
        else:
            self._offset = 1.0 if value else 0.0
            self.update()
        self.toggled.emit(value)

    def _get_offset(self) -> float:
        return self._offset

    def _set_offset(self, v: float) -> None:
        self._offset = v
        self.update()

    offset = Property(float, _get_offset, _set_offset)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
        super().mousePressEvent(event)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        w, h = self.width(), self.height()
        track_color = QColor(ACCENT) if self._offset > 0.5 else QColor(BG_ELEVATED)
        if self._offset < 1 and self._offset > 0:
            # blend
            a = QColor(BG_ELEVATED)
            b = QColor(ACCENT)
            t = self._offset
            track_color = QColor(
                int(a.red() * (1 - t) + b.red() * t),
                int(a.green() * (1 - t) + b.green() * t),
                int(a.blue() * (1 - t) + b.blue() * t),
            )
        p.setPen(QColor(BORDER_STRONG))
        p.setBrush(track_color)
        p.drawRoundedRect(QRectF(0.5, 0.5, w - 1, h - 1), h / 2 - 0.5, h / 2 - 0.5)

        knob_d = h - 6
        knob_x = 3 + self._offset * (w - knob_d - 6)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(TEXT))
        p.drawEllipse(QRectF(knob_x, 3, knob_d, knob_d))
        p.end()
