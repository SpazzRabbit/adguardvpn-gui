from __future__ import annotations

import os
import time
from datetime import datetime

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget

from adguard_gui.i18n import tr
from adguard_gui.models.types import ConnectionStatus
from adguard_gui.theme import ACCENT, BG_CARD, BORDER, TEXT, TEXT_DIM, TEXT_MUTED


def _iface_started_at(iface: str | None) -> float | None:
    """Возвращает unix-время создания сетевого интерфейса по mtime sysfs-симлинка.

    На Linux /sys/class/net/<iface> создаётся при поднятии интерфейса, и mtime
    у симлинка совпадает с моментом создания. Это позволяет показывать аптайм
    туннеля независимо от того, когда был запущен GUI.
    """
    if not iface:
        return None
    try:
        return os.stat(f"/sys/class/net/{iface}").st_mtime
    except OSError:
        return None


class StatusCard(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.setFrameShape(QFrame.Shape.NoFrame)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(10)

        self.title = QLabel(tr("Session"))
        self.title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; letter-spacing: 1px; text-transform: uppercase;")
        outer.addWidget(self.title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(10)

        self._fields: dict[str, QLabel] = {}
        labels = [
            ("mode", "Mode"),
            ("iface", "Interface"),
            ("protocol", "Protocol"),
            ("duration", "Duration"),
        ]
        for col, (key, title) in enumerate(labels):
            t = QLabel(tr(title))
            t.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
            v = QLabel("—")
            v.setStyleSheet(f"color: {TEXT}; font-size: 14px; font-weight: 600;")
            grid.addWidget(t, 0, col)
            grid.addWidget(v, 1, col)
            self._fields[key] = v

        outer.addLayout(grid)

        # Базовая метка времени для расчёта длительности. Сначала пытаемся
        # взять реальное время создания tun-интерфейса; если не получилось —
        # как fallback фиксируем момент, когда GUI впервые увидел connected.
        self._started_at: float | None = None
        self._iface: str | None = None
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick_duration)

    def set_status(self, status: ConnectionStatus, protocol: str | None = None) -> None:
        if status.state == "connected":
            iface = status.interface
            if iface != self._iface:
                self._iface = iface
                self._started_at = _iface_started_at(iface)
            if self._started_at is None:
                # fallback: либо нет sysfs-данных, либо нет имени интерфейса
                self._started_at = time.time()
            self._fields["mode"].setText(status.mode or "—")
            self._fields["iface"].setText(iface or "—")
            self._fields["protocol"].setText((protocol or "auto").upper())
            if not self._timer.isActive():
                self._timer.start()
            self._tick_duration()
        else:
            self._started_at = None
            self._iface = None
            self._timer.stop()
            for f in self._fields.values():
                f.setText("—")

    def _tick_duration(self) -> None:
        if self._started_at is None:
            self._fields["duration"].setText("—")
            return
        total = max(0, int(time.time() - self._started_at))
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        if h:
            self._fields["duration"].setText(f"{h}{tr('h')} {m:02d}{tr('m')} {s:02d}{tr('s')}")
        else:
            self._fields["duration"].setText(f"{m:02d}{tr('m')} {s:02d}{tr('s')}")
