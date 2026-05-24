from __future__ import annotations

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    Qt,
)
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from adguard_gui.theme import WARNING


class PendingButton(QWidget):
    """Янтарная кнопка-индикатор с плавно вращающимся круговым spinner'ом.

    Не наследуем QPushButton — нам не нужен ни клик, ни text-рендер: только
    "пилюля"-фон и spinner в центре. Размер фиксирован, чтобы строка локации
    оставалась выровнена с обычной Connect/Disconnect кнопками.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.ForbiddenCursor)
        self._angle = 0.0
        self._anim = QPropertyAnimation(self, b"angle", self)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(360.0)
        self._anim.setDuration(950)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.Type.Linear)
        self._anim.start()

    def _get_angle(self) -> float:
        return self._angle

    def _set_angle(self, value: float) -> None:
        self._angle = value
        self.update()

    angle = Property(float, _get_angle, _set_angle)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Pill-фон, идентичный по форме обычным кнопкам строки.
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        amber = QColor(WARNING)
        p.setBrush(amber)
        p.setPen(QPen(amber, 1))
        p.drawRoundedRect(rect, 10, 10)

        # Сегментированный spinner: 8 «лопастей», у каждой собственная alpha;
        # при вращении создаётся эффект бегущей кометы — мягко и без рывков.
        cx = self.width() / 2
        cy = self.height() / 2
        radius_outer = 11.0
        radius_inner = 5.0
        tail = QColor("#1a1408")  # тёмный, контрастный к WARNING
        p.translate(cx, cy)
        p.rotate(self._angle)
        pen = QPen()
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setWidthF(2.2)
        SEGMENTS = 8
        for i in range(SEGMENTS):
            c = QColor(tail)
            # alpha от 230 (голова) до 40 (хвост) по экспоненте — приятнее линейной.
            c.setAlpha(int(40 + 190 * ((SEGMENTS - 1 - i) / (SEGMENTS - 1)) ** 1.2))
            pen.setColor(c)
            p.setPen(pen)
            p.drawLine(0, int(radius_inner), 0, int(radius_outer))
            p.rotate(360 / SEGMENTS)
        p.end()

    def sizeHint(self):  # type: ignore[override]
        return self.minimumSizeHint()

    def minimumSizeHint(self):  # type: ignore[override]
        from PySide6.QtCore import QSize
        return QSize(132, 38)
