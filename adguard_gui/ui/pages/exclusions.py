from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from adguard_gui.i18n import tr
from adguard_gui.models.state import AppState
from adguard_gui.models.types import ExclusionsState
from adguard_gui.services.command_runner import CommandRunner
from adguard_gui.theme import (
    ACCENT,
    ACCENT_SOFT,
    BG_ELEVATED,
    BORDER,
    DANGER,
    TEXT,
    TEXT_DIM,
    TEXT_MUTED,
    make_icon,
)
from adguard_gui.ui.widgets.section_header import PageHeader


class ExclusionsPage(QWidget):
    def __init__(self, state: AppState, runner: CommandRunner) -> None:
        super().__init__()
        self.state = state
        self.runner = runner
        self._view_mode = "general"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 24)
        outer.setSpacing(16)
        outer.addWidget(PageHeader(tr("Exclusions"), tr("Sites outside or inside the VPN tunnel")))

        # Mode selector card
        mode_card = QFrame()
        mode_card.setObjectName("Card")
        mode_layout = QVBoxLayout(mode_card)
        mode_layout.setContentsMargins(20, 16, 20, 16)
        mode_layout.setSpacing(8)
        cap = QLabel(tr("Active mode"))
        cap.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; letter-spacing: 1px; text-transform: uppercase;")
        mode_layout.addWidget(cap)

        chips_row = QHBoxLayout(); chips_row.setSpacing(8)
        self.btn_general = QPushButton("General")
        self.btn_general.setCheckable(True); self.btn_general.setObjectName("Chip")
        self.btn_selective = QPushButton("Selective")
        self.btn_selective.setCheckable(True); self.btn_selective.setObjectName("Chip")
        g = QButtonGroup(self); g.setExclusive(True); g.addButton(self.btn_general); g.addButton(self.btn_selective)
        self.btn_general.clicked.connect(lambda: self._set_active_mode("general"))
        self.btn_selective.clicked.connect(lambda: self._set_active_mode("selective"))
        chips_row.addWidget(self.btn_general); chips_row.addWidget(self.btn_selective); chips_row.addStretch(1)
        mode_layout.addLayout(chips_row)

        self.mode_hint = QLabel("")
        self.mode_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        self.mode_hint.setWordWrap(True)
        mode_layout.addWidget(self.mode_hint)
        outer.addWidget(mode_card)

        # View toggle + add row
        tools = QHBoxLayout(); tools.setSpacing(8)
        self.view_general = QPushButton(tr("General list"))
        self.view_general.setCheckable(True); self.view_general.setChecked(True); self.view_general.setObjectName("Chip")
        self.view_selective = QPushButton(tr("Selective list"))
        self.view_selective.setCheckable(True); self.view_selective.setObjectName("Chip")
        gv = QButtonGroup(self); gv.setExclusive(True); gv.addButton(self.view_general); gv.addButton(self.view_selective)
        self.view_general.clicked.connect(lambda: self._switch_view("general"))
        self.view_selective.clicked.connect(lambda: self._switch_view("selective"))
        tools.addWidget(self.view_general); tools.addWidget(self.view_selective); tools.addStretch(1)

        clear_btn = QPushButton(tr("Clear"))
        clear_btn.setObjectName("Danger"); clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_current)
        tools.addWidget(clear_btn)
        outer.addLayout(tools)

        add_card = QFrame(); add_card.setObjectName("Card")
        add_layout = QHBoxLayout(add_card)
        add_layout.setContentsMargins(14, 10, 14, 10); add_layout.setSpacing(8)
        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText(tr("example.com or *.example.com or 1.2.3.4/24"))
        self.domain_input.returnPressed.connect(self._add_domain)
        add_btn = QPushButton(tr("Add"))
        add_btn.setObjectName("Primary")
        add_btn.setIcon(make_icon("plus", "#0f1a12", 16))
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_domain)
        add_layout.addWidget(self.domain_input, 1)
        add_layout.addWidget(add_btn)
        outer.addWidget(add_card)

        # Scrollable list
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.list_holder = QWidget()
        self.list_layout = QVBoxLayout(self.list_holder)
        self.list_layout.setContentsMargins(0, 0, 6, 12); self.list_layout.setSpacing(6)
        self.list_layout.addStretch(1)
        scroll.setWidget(self.list_holder)
        outer.addWidget(scroll, 1)

        self.state.exclusions_changed.connect(self._render)
        self._render(self.state.exclusions)
        self._update_mode_hint()

    def _set_active_mode(self, mode: str) -> None:
        if self.state.exclusions.mode == mode:
            return
        self.runner.exclusions_set_mode(mode)

    def _switch_view(self, mode: str) -> None:
        self._view_mode = mode
        self._render(self.state.exclusions)

    def _domains(self, exclusions: ExclusionsState) -> list[str]:
        return exclusions.general if self._view_mode == "general" else exclusions.selective

    def _add_domain(self) -> None:
        text = self.domain_input.text().strip()
        if not text:
            return
        self.runner.exclusions_add(self._view_mode, [text])
        self.domain_input.clear()
        from PySide6.QtCore import QTimer
        QTimer.singleShot(500, self.runner.exclusions_load)

    def _remove_domain(self, domain: str) -> None:
        self.runner.exclusions_remove(self._view_mode, [domain])
        from PySide6.QtCore import QTimer
        QTimer.singleShot(500, self.runner.exclusions_load)

    def _clear_current(self) -> None:
        reply = QMessageBox.question(
            self,
            tr("Clear list"),
            tr("Delete all entries from the {mode} list?", mode=self._view_mode.upper()),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.runner.exclusions_clear(self._view_mode)
            from PySide6.QtCore import QTimer
            QTimer.singleShot(500, self.runner.exclusions_load)

    def _update_mode_hint(self) -> None:
        mode = self.state.exclusions.mode
        if mode == "general":
            self.mode_hint.setText(tr("GENERAL: traffic goes through the VPN except domains in the list."))
        else:
            self.mode_hint.setText(tr("SELECTIVE: only domains in the list go through the VPN."))

    def _render(self, exclusions: ExclusionsState) -> None:
        # mode selector
        self.btn_general.setChecked(exclusions.mode == "general")
        self.btn_selective.setChecked(exclusions.mode == "selective")
        self._update_mode_hint()

        domains = self._domains(exclusions)

        # clear list
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if not domains:
            empty = QLabel(tr("{mode} list is empty", mode=self._view_mode.upper()))
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; padding: 32px;")
            self.list_layout.insertWidget(0, empty)
            return

        for idx, dom in enumerate(domains):
            row = QFrame()
            row.setObjectName("CardFlat")
            r = QHBoxLayout(row); r.setContentsMargins(14, 8, 8, 8); r.setSpacing(10)
            lbl = QLabel(dom); lbl.setStyleSheet(f"color: {TEXT}; font-size: 13px;")
            r.addWidget(lbl, 1)
            del_btn = QPushButton()
            del_btn.setObjectName("Ghost")
            del_btn.setFixedSize(30, 30)
            del_btn.setIcon(make_icon("close", DANGER, 16))
            del_btn.setIconSize(QSize(16, 16))
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda _=False, d=dom: self._remove_domain(d))
            r.addWidget(del_btn)
            self.list_layout.insertWidget(idx, row)
