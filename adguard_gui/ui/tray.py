from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from adguard_gui.i18n import tr
from adguard_gui.models.state import AppState
from adguard_gui.models.types import ConnectionStatus
from adguard_gui.services.command_runner import CommandRunner
from adguard_gui.theme import ACCENT, TEXT_MUTED, WARNING, app_icon, make_icon
from adguard_gui.ui.main_window import MainWindow


class TrayIcon(QSystemTrayIcon):
    def __init__(self, state: AppState, runner: CommandRunner, window: MainWindow) -> None:
        super().__init__()
        self.state = state
        self.runner = runner
        self.window = window

        self.setIcon(self._icon_for_state(state.status.state))
        self.setToolTip("AdGuard VPN")

        self.menu = QMenu()
        self.status_action = QAction(tr("VPN: …"))
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)
        self.menu.addSeparator()

        self.connect_last_action = QAction(tr("Connect (fastest)"))
        self.connect_last_action.triggered.connect(lambda: self.runner.connect(fastest=True))
        self.menu.addAction(self.connect_last_action)

        self.disconnect_action = QAction(tr("Disconnect"))
        self.disconnect_action.triggered.connect(self._confirm_disconnect)
        self.menu.addAction(self.disconnect_action)

        self.menu.addSeparator()

        self.show_action = QAction(tr("Open window"))
        self.show_action.triggered.connect(self._show_window)
        self.menu.addAction(self.show_action)

        self.quit_action = QAction(tr("Quit"))
        self.quit_action.triggered.connect(self._quit)
        self.menu.addAction(self.quit_action)

        self.setContextMenu(self.menu)
        self.activated.connect(self._on_activated)

        self.state.status_changed.connect(self._on_status)
        self.state.language_changed.connect(self._retranslate)

    def _retranslate(self) -> None:
        self.connect_last_action.setText(tr("Connect (fastest)"))
        self.disconnect_action.setText(tr("Disconnect"))
        self.show_action.setText(tr("Open window"))
        self.quit_action.setText(tr("Quit"))
        # перерисуем статус-строку под новый язык
        self._on_status(self.state.status)

    def _icon_for_state(self, st: str) -> QIcon:
        if st == "connected":
            # «фирменная» иконка приложения — зелёная, ясно сигнализирует «защищено»
            return app_icon(22)
        color = WARNING if st in ("connecting", "disconnecting") else TEXT_MUTED
        return make_icon("shield", color, 22)

    def _on_status(self, status: ConnectionStatus) -> None:
        self.setIcon(self._icon_for_state(status.state))
        label = {
            "connected": tr("VPN: connected"),
            "disconnected": tr("VPN: off"),
            "connecting": tr("VPN: connecting…"),
            "disconnecting": tr("VPN: disconnecting…"),
            "error": tr("VPN: error"),
            "unknown": tr("VPN: …"),
        }.get(status.state, tr("VPN: …"))
        if status.state == "connected" and status.location_city:
            label += f"  •  {status.location_city.title() if status.location_city.isupper() else status.location_city}"
        self.status_action.setText(label)
        self.disconnect_action.setEnabled(status.state == "connected")
        self.connect_last_action.setEnabled(status.state in ("disconnected", "error", "unknown"))

    def _on_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            if self.window.isVisible():
                self.window.hide()
            else:
                self._show_window()

    def _show_window(self) -> None:
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _confirm_disconnect(self) -> None:
        reply = QMessageBox.question(
            self.window,
            tr("Disconnect VPN"),
            tr("Disconnect from AdGuard VPN?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.runner.disconnect()

    def _quit(self) -> None:
        self.window.set_force_close(True)
        QApplication.instance().quit()
