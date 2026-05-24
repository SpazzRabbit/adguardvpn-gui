from __future__ import annotations

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from adguard_gui.i18n import tr
from adguard_gui.models.state import AppState
from adguard_gui.models.types import Location
from adguard_gui.services.command_runner import CommandRunner
from adguard_gui.theme import ACCENT, BG_ELEVATED, BORDER, TEXT_MUTED, make_icon
from adguard_gui.ui.widgets.location_row import LocationRow
from adguard_gui.ui.widgets.section_header import PageHeader


class LocationsPage(QWidget):
    def __init__(self, state: AppState, runner: CommandRunner) -> None:
        super().__init__()
        self.state = state
        self.runner = runner
        self._filter_text = ""
        self._filter_mode = "all"  # all | favorites
        self._pending_iso: str | None = None
        self._pending_city: str | None = None
        self._pending_action: str = "connect"  # "connect" | "disconnect"

        self._pending_timeout = QTimer(self)
        self._pending_timeout.setSingleShot(True)
        self._pending_timeout.setInterval(30000)
        self._pending_timeout.timeout.connect(self._clear_pending)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 24)
        outer.setSpacing(18)

        header_row = QHBoxLayout()
        header_row.addWidget(PageHeader(tr("Locations"), tr("VPN server to connect to")), 1)
        refresh_btn = QPushButton(tr("Refresh"))
        refresh_btn.setObjectName("Ghost")
        refresh_btn.setIcon(make_icon("refresh", TEXT_MUTED, 16))
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.runner.list_locations)
        fastest_btn = QPushButton(tr("Fastest"))
        fastest_btn.setObjectName("Primary")
        fastest_btn.setIcon(make_icon("bolt", "#0f1a12", 16))
        fastest_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fastest_btn.clicked.connect(self._connect_fastest)
        header_row.addWidget(refresh_btn)
        header_row.addWidget(fastest_btn)
        outer.addLayout(header_row)

        # Search + chips row
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        search_wrap = QFrame()
        search_wrap.setObjectName("CardFlat")
        sw = QHBoxLayout(search_wrap)
        sw.setContentsMargins(12, 0, 12, 0)
        sw.setSpacing(8)
        icon_lbl = QLabel()
        icon_lbl.setPixmap(make_icon("search", TEXT_MUTED, 16).pixmap(16, 16))
        sw.addWidget(icon_lbl)
        self.search = QLineEdit()
        self.search.setObjectName("Search")
        self.search.setPlaceholderText(tr("Search by country, city, or code"))
        self.search.setFrame(False)
        self.search.setStyleSheet("background: transparent; border: none; padding: 8px 0;")
        self.search.textChanged.connect(self._on_search)
        sw.addWidget(self.search, 1)
        toolbar.addWidget(search_wrap, 1)

        self.chip_all = QPushButton(tr("All"))
        self.chip_all.setObjectName("Chip")
        self.chip_all.setCheckable(True)
        self.chip_all.setChecked(True)
        self.chip_fav = QPushButton(tr("Favorites"))
        self.chip_fav.setObjectName("Chip")
        self.chip_fav.setCheckable(True)
        chips_group = QButtonGroup(self)
        chips_group.setExclusive(True)
        chips_group.addButton(self.chip_all)
        chips_group.addButton(self.chip_fav)
        self.chip_all.clicked.connect(lambda: self._set_filter_mode("all"))
        self.chip_fav.clicked.connect(lambda: self._set_filter_mode("favorites"))
        toolbar.addWidget(self.chip_all)
        toolbar.addWidget(self.chip_fav)

        outer.addLayout(toolbar)

        # Scroll list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 12)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch(1)
        self.scroll.setWidget(self.list_container)
        outer.addWidget(self.scroll, 1)

        self.empty_label = QLabel(tr("Locations not loaded yet"))
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; padding: 40px;")
        self.list_layout.insertWidget(0, self.empty_label)

        self.state.locations_changed.connect(self._render)
        self.state.status_changed.connect(self._on_status_changed)
        self.state.prefs_changed.connect(self._on_prefs_changed)
        self.runner.operation_finished.connect(self._on_operation_finished)
        self._render(self.state.locations)

    def _on_status_changed(self, status) -> None:
        # Снимаем pending как только VPN явно перешёл в стабильное состояние.
        if self._pending_iso or self._pending_action == "disconnect":
            if status.state in ("connected", "disconnected", "error"):
                self._clear_pending()
        self._render(self.state.locations)

    def _on_prefs_changed(self, _prefs) -> None:
        self._render(self.state.locations)

    def _on_operation_finished(self, name: str, ok: bool, _msg: str) -> None:
        # Если CLI вернул ошибку при connect/disconnect — сразу снимаем pending.
        if name.startswith(("connect", "disconnect")):
            if not ok:
                self._clear_pending()
            # При успехе ждём смены статуса от poller'а — _on_status_changed снимет.

    def _set_filter_mode(self, mode: str) -> None:
        self._filter_mode = mode
        self._render(self.state.locations)

    def _on_search(self, text: str) -> None:
        self._filter_text = text.strip().lower()
        self._render(self.state.locations)

    def _matches(self, loc: Location) -> bool:
        if self._filter_mode == "favorites" and loc.iso not in self.state.prefs.favorite_locations:
            return False
        if not self._filter_text:
            return True
        q = self._filter_text
        return q in loc.country.lower() or q in loc.city.lower() or q in loc.iso.lower()

    def _render(self, locations: list[Location]) -> None:
        # clear existing rows (keep stretch at end)
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if not locations:
            self.empty_label = QLabel(tr("Locations not loaded yet"))
            self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.empty_label.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; padding: 40px;")
            self.list_layout.insertWidget(0, self.empty_label)
            return

        filtered = [l for l in locations if self._matches(l)]
        filtered.sort(key=lambda l: (l.ping_ms is None, l.ping_ms or 0))

        if not filtered:
            empty = QLabel(tr("Nothing found"))
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px; padding: 40px;")
            self.list_layout.insertWidget(0, empty)
            return

        current_iso = self.state.status.location_iso
        current_city = (self.state.status.location_city or "").upper()
        favorites = set(self.state.prefs.favorite_locations)

        for idx, loc in enumerate(filtered):
            is_current = (
                self.state.status.state == "connected"
                and (
                    (current_iso and loc.iso == current_iso)
                    or (current_city and loc.city.upper() == current_city)
                )
            )
            is_pending = self._pending_iso == loc.iso and self._pending_action == "connect"
            row = LocationRow(
                loc,
                is_favorite=loc.iso in favorites,
                is_current=is_current,
                is_pending=is_pending,
            )
            row.connect_requested.connect(self._connect_to)
            row.disconnect_requested.connect(self._disconnect)
            row.favorite_toggled.connect(self.state.toggle_favorite)
            self.list_layout.insertWidget(idx, row)

        self._update_banner()

    def _connect_to(self, location: Location) -> None:
        self.state.prefs.last_location = location.iso
        self.state.prefs_changed.emit(self.state.prefs)
        self._pending_iso = location.iso
        self._pending_city = location.city
        self._pending_action = "connect"
        self._pending_timeout.start()
        self.runner.connect(location=location.city)
        self._render(self.state.locations)

    def _connect_fastest(self) -> None:
        self._pending_iso = None
        self._pending_city = tr("Fastest")
        self._pending_action = "connect"
        self._pending_timeout.start()
        self.runner.connect(fastest=True)
        self._update_banner()

    def _disconnect(self) -> None:
        self._pending_iso = None
        self._pending_city = self.state.status.location_city
        self._pending_action = "disconnect"
        self._pending_timeout.start()
        self.runner.disconnect()
        self._update_banner()

    def _clear_pending(self) -> None:
        self._pending_iso = None
        self._pending_city = None
        self._pending_action = "connect"
        self._pending_timeout.stop()
        self._update_banner()
        # перерисовать строки чтобы убрать pending-метку
        self._render(self.state.locations)

    def _update_banner(self) -> None:
        # Раньше тут был отдельный progress-banner; теперь анимация — на самой кнопке строки.
        return None
