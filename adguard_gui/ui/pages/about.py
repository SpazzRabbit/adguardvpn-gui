from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from adguard_gui.adapters.cli_adapter import CliAdapter
from adguard_gui.i18n import tr
from adguard_gui.models.state import AppState
from adguard_gui.parsers.ansi import strip_ansi
from adguard_gui.services.command_runner import CommandRunner
from adguard_gui.theme import ACCENT, BG_ELEVATED, BORDER, TEXT, TEXT_DIM, TEXT_MUTED
from adguard_gui.ui.widgets.section_header import PageHeader, SectionHeader


GUI_VERSION = "0.2.0"


class AboutPage(QWidget):
    def __init__(self, state: AppState, runner: CommandRunner, adapter: CliAdapter) -> None:
        super().__init__()
        self.state = state
        self.runner = runner
        self.adapter = adapter

        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 24)
        outer.setSpacing(16)
        outer.addWidget(PageHeader(tr("About"), tr("CLI version, updates, log export")))

        # CLI version card
        ver_card = QFrame(); ver_card.setObjectName("Card")
        v = QVBoxLayout(ver_card); v.setContentsMargins(22, 18, 22, 18); v.setSpacing(8)
        v.addWidget(SectionHeader(tr("Versions")))

        row = QHBoxLayout(); row.setSpacing(40)
        gui_box = QVBoxLayout(); gui_box.setSpacing(2)
        gt = QLabel("AdGuard VPN GUI"); gt.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; letter-spacing: 1px; text-transform: uppercase;")
        gv = QLabel(GUI_VERSION); gv.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: 600;")
        gui_box.addWidget(gt); gui_box.addWidget(gv)
        gui_wrap = QFrame(); gui_wrap.setLayout(gui_box)

        cli_box = QVBoxLayout(); cli_box.setSpacing(2)
        ct = QLabel("adguardvpn-cli"); ct.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; letter-spacing: 1px; text-transform: uppercase;")
        self.cli_version_label = QLabel(tr("detecting…")); self.cli_version_label.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: 600;")
        cli_box.addWidget(ct); cli_box.addWidget(self.cli_version_label)
        cli_wrap = QFrame(); cli_wrap.setLayout(cli_box)

        row.addWidget(gui_wrap); row.addWidget(cli_wrap); row.addStretch(1)
        v.addLayout(row)
        outer.addWidget(ver_card)

        # Actions
        actions_card = QFrame(); actions_card.setObjectName("Card")
        a = QVBoxLayout(actions_card); a.setContentsMargins(22, 18, 22, 18); a.setSpacing(10)
        a.addWidget(SectionHeader(tr("Maintenance")))

        btn_row = QHBoxLayout(); btn_row.setSpacing(10)
        check_btn = QPushButton(tr("Check CLI updates"))
        check_btn.setObjectName("Ghost")
        check_btn.clicked.connect(self.runner.check_update)
        export_btn = QPushButton(tr("Export logs as ZIP…"))
        export_btn.setObjectName("Ghost")
        export_btn.clicked.connect(self._export_logs)
        btn_row.addWidget(check_btn); btn_row.addWidget(export_btn); btn_row.addStretch(1)
        a.addLayout(btn_row)
        outer.addWidget(actions_card)

        # Output console
        log_card = QFrame(); log_card.setObjectName("Card")
        lcl = QVBoxLayout(log_card); lcl.setContentsMargins(22, 18, 22, 18); lcl.setSpacing(8)
        lcl.addWidget(SectionHeader(tr("Command log"), tr("Latest CLI output")))
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setFixedHeight(220)
        self.console.setStyleSheet(
            f"background-color: {BG_ELEVATED}; border: 1px solid {BORDER}; border-radius: 8px; "
            f"color: {TEXT_MUTED}; font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 12px; padding: 10px;"
        )
        lcl.addWidget(self.console)
        outer.addWidget(log_card)

        outer.addStretch(1)

        self.runner.raw_result.connect(self._on_raw)
        self.state.update_changed.connect(self._on_update_info)
        self.runner.operation_finished.connect(self._on_op_finished)
        # initial CLI version probe
        self._refresh_cli_version()

    def _refresh_cli_version(self) -> None:
        result = self.adapter.version()
        text = (result.stdout or result.stderr or "?").strip().splitlines()[0] if (result.stdout or result.stderr) else "?"
        self.cli_version_label.setText(text or "?")

    def _on_update_info(self, info) -> None:
        # state.update_info обновляется и после check-update, и после update —
        # синхронизируем подпись.
        if info.current:
            self.cli_version_label.setText(f"AdGuard VPN CLI v{info.current}")

    def _on_op_finished(self, name: str, ok: bool, _msg: str) -> None:
        if name == "update" and ok:
            # На всякий случай перечитаем версию напрямую — в `runner.update`
            # уже это делается, но если адаптер вернул нестандартный вывод,
            # подстрахуемся ещё одним вызовом.
            self._refresh_cli_version()

    def _export_logs(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("Save logs as…"),
            str(Path.home() / "adguardvpn-logs.zip"),
            "ZIP archives (*.zip)",
        )
        if path:
            self.runner.export_logs(path)

    def _on_raw(self, op: str, result) -> None:
        header = f"$ {' '.join(result.command)}  (exit {result.exit_code}, {result.duration_ms}ms)"
        body = strip_ansi(result.stdout).strip()
        err = strip_ansi(result.stderr).strip()
        chunk = header
        if body:
            chunk += "\n" + body
        if err:
            chunk += "\n[stderr]\n" + err
        self.console.appendPlainText(chunk + "\n")
