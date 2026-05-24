from __future__ import annotations

import os
import sys
import tempfile

from PySide6.QtCore import QLockFile, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from adguard_gui.adapters.cli_adapter import CliAdapter
from adguard_gui.i18n import set_lang, tr
from adguard_gui.models.state import AppState
from adguard_gui.services.autostart import sync as autostart_sync
from adguard_gui.services.command_runner import CommandRunner
from adguard_gui.services.poller import Poller
from adguard_gui.storage.config_store import ConfigStore
from adguard_gui.theme import app_icon, apply_theme
from adguard_gui.ui.main_window import MainWindow
from adguard_gui.ui.tray import TrayIcon


def _lock_path() -> str:
    uid = os.getuid() if hasattr(os, "getuid") else 0
    return os.path.join(tempfile.gettempdir(), f"adguard-gui-{uid}.lock")


def run() -> int:
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("AdGuard VPN GUI")
    qt_app.setDesktopFileName("adguard-gui")
    qt_app.setQuitOnLastWindowClosed(False)
    qt_app.setWindowIcon(app_icon(128))
    apply_theme(qt_app)

    lock = QLockFile(_lock_path())
    lock.setStaleLockTime(0)
    if not lock.tryLock(50):
        QMessageBox.information(
            None,
            "AdGuard VPN",
            tr("The application is already running. Open it from the system tray."),
        )
        return 0
    # keep reference for lifetime of process
    qt_app._adguard_lock = lock  # type: ignore[attr-defined]

    store = ConfigStore()
    prefs = store.load()
    set_lang(prefs.lang)
    # Привести системный autostart к тому, что записано в prefs.
    try:
        autostart_sync(prefs.autostart)
    except OSError:
        pass

    state = AppState(prefs)
    adapter = CliAdapter(prefs)
    runner = CommandRunner(state, adapter)
    poller = Poller(runner, prefs.refresh_interval_sec)

    window = MainWindow(state, adapter, runner, store, poller)
    tray = TrayIcon(state, runner, window)
    tray.show()

    # Initial data load
    QTimer.singleShot(0, runner.list_locations)
    QTimer.singleShot(50, runner.license)
    QTimer.singleShot(100, runner.config_show)
    QTimer.singleShot(150, runner.status)
    QTimer.singleShot(250, runner.exclusions_load)
    # Проверка обновлений CLI: один раз при старте + далее раз в 6 часов.
    QTimer.singleShot(5_000, runner.check_update)
    update_timer = QTimer()
    update_timer.timeout.connect(runner.check_update)
    update_timer.start(6 * 60 * 60 * 1000)
    qt_app._adguard_update_timer = update_timer  # keep reference

    # Auto-connect on launch: дёргаем connect один раз, но только если VPN
    # действительно выключен — после первого status. Не дублирует туннель,
    # если CLI уже был подключён до старта GUI.
    def _maybe_autoconnect() -> None:
        if prefs.autoconnect_mode == "off":
            return
        if state.status.state == "connected":
            return
        if prefs.autoconnect_mode == "fastest":
            runner.connect(fastest=True)
        elif prefs.autoconnect_mode == "last":
            # без -l CLI сам возьмёт последнюю использованную локацию
            runner.connect()

    QTimer.singleShot(900, _maybe_autoconnect)

    # Re-poll status on connect/disconnect completion
    def _on_op_finished(name: str, ok: bool, _msg: str) -> None:
        if name.startswith(("connect", "disconnect")):
            poller.kick_soon(1500)
            QTimer.singleShot(2500, runner.status)
        elif name.startswith("login") or name == "logout":
            QTimer.singleShot(800, runner.license)
            QTimer.singleShot(1100, runner.status)

    runner.operation_finished.connect(_on_op_finished)

    # Reflect prefs changes back to poller and adapter
    def _on_prefs(prefs_obj) -> None:
        poller.set_interval(prefs_obj.refresh_interval_sec)
        store.save(prefs_obj)
        adapter.set_prefs(prefs_obj)
        try:
            autostart_sync(prefs_obj.autostart)
        except OSError:
            pass

    state.prefs_changed.connect(_on_prefs)

    poller.start()

    # CLI-флаг --minimized (используется autostart-записью) либо prefs.start_minimized
    start_hidden = prefs.start_minimized or "--minimized" in sys.argv
    if not start_hidden:
        window.show()

    return qt_app.exec()
