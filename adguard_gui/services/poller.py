from __future__ import annotations

from PySide6.QtCore import QObject, QTimer

from adguard_gui.services.command_runner import CommandRunner


class Poller(QObject):
    def __init__(self, runner: CommandRunner, interval_sec: int) -> None:
        super().__init__()
        self.runner = runner
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.set_interval(interval_sec)

    def set_interval(self, interval_sec: int) -> None:
        interval_sec = max(2, int(interval_sec))
        self._timer.setInterval(interval_sec * 1000)

    def start(self) -> None:
        if not self._timer.isActive():
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def kick_soon(self, delay_ms: int = 1500) -> None:
        QTimer.singleShot(delay_ms, self._tick)

    def _tick(self) -> None:
        self.runner.status()
