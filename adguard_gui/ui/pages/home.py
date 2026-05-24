from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from adguard_gui.i18n import tr
from adguard_gui.models.state import AppState
from adguard_gui.models.types import ConnectionStatus, UpdateInfo
from adguard_gui.services.command_runner import CommandRunner
from adguard_gui.theme import (
    ACCENT,
    ACCENT_HOVER,
    ACCENT_SOFT,
    BG_CARD,
    BG_ELEVATED,
    BORDER,
    DANGER,
    TEXT,
    TEXT_DIM,
    TEXT_MUTED,
    WARNING,
    make_icon,
)
from adguard_gui.ui.widgets.connect_button import ConnectButton
from adguard_gui.ui.widgets.status_card import StatusCard


STATE_LABEL_KEYS = {
    "connected": "Connection protected",
    "disconnected": "Not connected",
    "connecting": "Connecting…",
    "disconnecting": "Disconnecting…",
    "error": "Connection error",
    "unknown": "Status unknown",
}

STATE_DESC_KEYS = {
    "connected": "Your traffic goes through AdGuard VPN.",
    "disconnected": "Press the button to connect.",
    "connecting": "Bringing the tunnel up…",
    "disconnecting": "Closing the tunnel.",
    "error": "Something went wrong. Check the logs.",
    "unknown": "Polling the daemon…",
}


class HomePage(QWidget):
    def __init__(self, state: AppState, runner: CommandRunner, navigate_locations) -> None:
        super().__init__()
        self.state = state
        self.runner = runner
        self._navigate_locations = navigate_locations

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(20)

        # Баннер обновления CLI — компактная карточка вверху, скрыта когда
        # обновлений нет или пользователь дисмисснул эту версию.
        self.update_banner = self._build_update_banner()
        self.update_banner.hide()
        layout.addWidget(self.update_banner)

        layout.addStretch(1)

        center = QVBoxLayout()
        center.setSpacing(16)
        center.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self.button = ConnectButton(size=220)
        self.button.clicked.connect(self._on_toggle)
        btn_wrap = QHBoxLayout()
        btn_wrap.addStretch(1)
        btn_wrap.addWidget(self.button)
        btn_wrap.addStretch(1)
        center.addLayout(btn_wrap)

        self.state_title = QLabel(tr(STATE_LABEL_KEYS["unknown"]))
        self.state_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_title.setStyleSheet(f"color: {TEXT};")
        f = self.state_title.font()
        f.setPointSize(17)
        f.setBold(True)
        self.state_title.setFont(f)
        center.addWidget(self.state_title)

        self.state_subtitle = QLabel(tr(STATE_DESC_KEYS["unknown"]))
        self.state_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_subtitle.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
        center.addWidget(self.state_subtitle)

        layout.addLayout(center)

        # Location card
        loc_card = QFrame()
        loc_card.setObjectName("Card")
        loc_layout = QHBoxLayout(loc_card)
        loc_layout.setContentsMargins(20, 14, 14, 14)
        loc_layout.setSpacing(14)

        loc_icon = QLabel()
        loc_icon.setPixmap(make_icon("location", ACCENT, 28).pixmap(28, 28))
        loc_layout.addWidget(loc_icon)

        loc_text = QVBoxLayout()
        loc_text.setSpacing(2)
        cap = QLabel(tr("CURRENT LOCATION"))
        cap.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; letter-spacing: 1px; text-transform: uppercase;")
        self.location_label = QLabel("—")
        self.location_label.setStyleSheet(f"color: {TEXT}; font-size: 15px; font-weight: 600;")
        loc_text.addWidget(cap)
        loc_text.addWidget(self.location_label)
        loc_layout.addLayout(loc_text, 1)

        change_btn = QPushButton(tr("Change"))
        change_btn.setObjectName("Ghost")
        change_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        change_btn.clicked.connect(lambda: self._navigate_locations())
        loc_layout.addWidget(change_btn)

        fastest_btn = QPushButton(tr("Fastest server"))
        fastest_btn.setObjectName("Primary")
        fastest_btn.setIcon(make_icon("bolt", "#0f1a12", 16))
        fastest_btn.setIconSize(QSize(16, 16))
        fastest_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fastest_btn.clicked.connect(lambda: self.runner.connect(fastest=True))
        loc_layout.addWidget(fastest_btn)

        layout.addWidget(loc_card)

        self.status_card = StatusCard()
        layout.addWidget(self.status_card)

        layout.addStretch(1)

        # Bind state
        self.state.status_changed.connect(self._on_status_changed)
        self.state.config_changed.connect(self._on_config_changed)
        self.state.update_changed.connect(self._on_update_info)
        self._on_status_changed(self.state.status)
        self._on_update_info(self.state.update_info)

    def _on_toggle(self) -> None:
        st = self.state.status.state
        if st == "connected":
            self.runner.disconnect()
        elif st in ("connecting", "disconnecting"):
            return
        else:
            last = self.state.prefs.last_location
            if last:
                loc = self.state.find_location(iso=last) or self.state.find_location(city=last)
                if loc:
                    self.runner.connect(location=loc.city)
                    return
            self.runner.connect(fastest=True)

    def _on_status_changed(self, status: ConnectionStatus) -> None:
        st = status.state if status.state in STATE_LABEL_KEYS else "unknown"
        self.state_title.setText(tr(STATE_LABEL_KEYS[st]))
        self.state_subtitle.setText(tr(STATE_DESC_KEYS[st]))
        self.button.set_state(st)

        if status.state == "connected" and status.location_city:
            iso = status.location_iso
            city = status.location_city.title() if status.location_city.isupper() else status.location_city
            # try map via locations
            mapped = self.state.find_location(city=status.location_city)
            country = ""
            if mapped:
                iso = mapped.iso
                city = mapped.city
                country = mapped.country
            label = f"{iso}  •  {city}" if iso else city
            if country:
                label = f"{label} ({country})"
            self.location_label.setText(label)
        elif status.state in ("disconnected", "unknown", "error"):
            self.location_label.setText("—")

        self.status_card.set_status(status, protocol=self.state.config.protocol)

    def _on_config_changed(self, _config) -> None:
        self.status_card.set_status(self.state.status, protocol=self.state.config.protocol)

    # ---- Update banner -------------------------------------------------

    def _build_update_banner(self) -> QFrame:
        card = QFrame(); card.setObjectName("Card")
        card.setStyleSheet(
            f"QFrame#Card {{ background-color: #1f2a1e; border: 1px solid {ACCENT}; }}"
        )
        layout = QHBoxLayout(card)
        layout.setContentsMargins(18, 14, 14, 14)
        layout.setSpacing(14)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(make_icon("refresh", ACCENT, 22).pixmap(22, 22))
        icon_lbl.setFixedSize(QSize(28, 28))
        layout.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        text_col = QVBoxLayout(); text_col.setSpacing(2)
        self.update_title = QLabel("")
        self.update_title.setStyleSheet(f"color: {TEXT}; font-size: 14px; font-weight: 600;")
        self.update_subtitle = QLabel("")
        self.update_subtitle.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        text_col.addWidget(self.update_title)
        text_col.addWidget(self.update_subtitle)
        layout.addLayout(text_col, 1)

        self.update_dismiss_btn = QPushButton(tr("Later"))
        self.update_dismiss_btn.setObjectName("Ghost")
        self.update_dismiss_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_dismiss_btn.clicked.connect(self._dismiss_update)
        layout.addWidget(self.update_dismiss_btn)

        self.update_install_btn = QPushButton(tr("Update now"))
        self.update_install_btn.setObjectName("Primary")
        self.update_install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_install_btn.clicked.connect(self._start_update)
        layout.addWidget(self.update_install_btn)
        return card

    def _on_update_info(self, info: UpdateInfo) -> None:
        dismissed = self.state.prefs.dismissed_update
        if not info.available or not info.latest or dismissed == info.latest:
            self.update_banner.hide()
            return
        if info.current and info.latest:
            self.update_title.setText(
                tr("AdGuard VPN CLI update available: v{current} → v{latest}",
                   current=info.current, latest=info.latest)
            )
        else:
            self.update_title.setText(
                tr("AdGuard VPN CLI update available: v{latest}", latest=info.latest)
            )
        self.update_subtitle.setText(tr("It only takes a few seconds to install."))
        self.update_install_btn.setEnabled(True)
        self.update_install_btn.setText(tr("Update now"))
        self.update_banner.show()

    def _start_update(self) -> None:
        self.update_install_btn.setEnabled(False)
        self.update_install_btn.setText(tr("Updating…"))
        self.runner.update()

    def _dismiss_update(self) -> None:
        info = self.state.update_info
        if info.latest:
            prefs = self.state.prefs
            prefs.dismissed_update = info.latest
            self.state.set_prefs(prefs)
        self.update_banner.hide()
