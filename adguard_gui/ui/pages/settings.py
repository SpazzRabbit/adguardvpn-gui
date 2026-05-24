from __future__ import annotations

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from adguard_gui.i18n import LANGUAGES, current_lang, set_lang, tr
from adguard_gui.models.state import AppState
from adguard_gui.models.types import GuiPrefs, VpnConfig
from adguard_gui.services.command_runner import CommandRunner
from adguard_gui.storage.config_store import ConfigStore
from adguard_gui.theme import BORDER, TEXT_MUTED
from adguard_gui.ui.widgets.section_header import PageHeader, SectionHeader
from adguard_gui.ui.widgets.toggle_switch import ToggleSwitch


DNS_PRESETS: list[tuple[str, str]] = [
    ("Default (AdGuard VPN)", ""),
    ("AdGuard DNS", "https://dns.adguard-dns.com/dns-query"),
    ("AdGuard Family", "https://family.adguard-dns.com/dns-query"),
    ("Cloudflare", "https://cloudflare-dns.com/dns-query"),
    ("Quad9", "https://dns.quad9.net/dns-query"),
    ("Google", "https://dns.google/dns-query"),
]


def _card(title: str, subtitle: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(14)
    header = SectionHeader(title, subtitle)
    layout.addWidget(header)
    return frame, layout


def _row(label_text: str, widget: QWidget, hint: str | None = None) -> QWidget:
    box = QFrame()
    layout = QHBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(12)
    label_box = QVBoxLayout()
    label_box.setSpacing(2)
    title = QLabel(label_text)
    title.setStyleSheet("font-size: 14px;")
    label_box.addWidget(title)
    if hint:
        h = QLabel(hint)
        h.setObjectName("Muted")
        h.setStyleSheet("font-size: 12px; color: #9aa0a6;")
        h.setWordWrap(True)
        label_box.addWidget(h)
    layout.addLayout(label_box, 1)
    widget.setMaximumWidth(360)
    layout.addWidget(widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    return box


class SettingsPage(QWidget):
    def __init__(self, state: AppState, runner: CommandRunner, store: ConfigStore) -> None:
        super().__init__()
        self.state = state
        self.runner = runner
        self.store = store
        self._syncing = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 24)
        outer.setSpacing(18)
        outer.addWidget(PageHeader(tr("Settings"), tr("AdGuard VPN CLI and GUI configuration")))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 6, 12)
        body_layout.setSpacing(16)
        scroll.setWidget(body)
        outer.addWidget(scroll, 1)

        body_layout.addWidget(self._build_connection_card())
        body_layout.addWidget(self._build_safety_card())
        body_layout.addWidget(self._build_startup_card())
        body_layout.addWidget(self._build_dns_card())
        body_layout.addWidget(self._build_socks_card())
        body_layout.addWidget(self._build_privacy_card())
        body_layout.addWidget(self._build_updates_card())
        body_layout.addWidget(self._build_network_card())
        body_layout.addWidget(self._build_gui_card())
        body_layout.addStretch(1)

        self.state.config_changed.connect(self._sync_from_config)
        self._sync_from_config(self.state.config)

    # --- Cards -----------------------------------------------------------

    def _build_connection_card(self) -> QFrame:
        card, layout = _card(tr("Connection"), tr("Basic VPN tunnel parameters"))

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["TUN", "SOCKS"])
        self.mode_combo.activated.connect(lambda _i: self._on_user("set-mode", self.mode_combo.currentText().lower()))
        layout.addWidget(_row(tr("Mode"), self.mode_combo, tr("TUN — system tunnel; SOCKS — local proxy.")))

        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["auto", "http2", "quic"])
        self.protocol_combo.activated.connect(lambda _i: self._on_user("set-protocol", self.protocol_combo.currentText()))
        layout.addWidget(_row(tr("Protocol"), self.protocol_combo))

        self.routing_combo = QComboBox()
        self.routing_combo.addItems(["auto", "script", "none"])
        self.routing_combo.activated.connect(lambda _i: self._on_user("set-tun-routing-mode", self.routing_combo.currentText()))
        layout.addWidget(_row("TUN routing", self.routing_combo))

        self.system_dns_toggle = ToggleSwitch()
        self.system_dns_toggle.toggled.connect(lambda v: self._on_user("set-change-system-dns", "on" if v else "off"))
        layout.addWidget(_row(tr("Change system DNS"), self.system_dns_toggle, tr("Replace system DNS with the VPN's.")))

        self.post_quantum_toggle = ToggleSwitch()
        self.post_quantum_toggle.toggled.connect(lambda v: self._on_user("set-post-quantum", "on" if v else "off"))
        layout.addWidget(_row(tr("Post-quantum cryptography"), self.post_quantum_toggle, tr("Protection against potential quantum attacks.")))

        return card

    def _build_safety_card(self) -> QFrame:
        card, layout = _card(tr("Safety"), tr("Protection against unexpected disconnects"))

        self.kill_switch_toggle = ToggleSwitch()
        self.kill_switch_toggle.setChecked(self.state.prefs.kill_switch)
        self.kill_switch_toggle.toggled.connect(self._on_kill_switch)
        layout.addWidget(_row(
            tr("Kill switch"),
            self.kill_switch_toggle,
            tr("Automatically reconnect VPN whenever the tunnel drops."),
        ))

        return card

    def _build_startup_card(self) -> QFrame:
        card, layout = _card(tr("Startup"), tr("Autostart and auto-connect behaviour"))

        self.autostart_toggle = ToggleSwitch()
        self.autostart_toggle.setChecked(self.state.prefs.autostart)
        self.autostart_toggle.toggled.connect(self._on_autostart)
        layout.addWidget(_row(
            tr("Launch at system startup"),
            self.autostart_toggle,
            tr("Adds an entry to ~/.config/autostart."),
        ))

        self.autoconnect_combo = QComboBox()
        self.autoconnect_combo.addItem(tr("Off"), "off")
        self.autoconnect_combo.addItem(tr("Last location"), "last")
        self.autoconnect_combo.addItem(tr("Fastest"), "fastest")
        cur = self.state.prefs.autoconnect_mode or "off"
        for i in range(self.autoconnect_combo.count()):
            if self.autoconnect_combo.itemData(i) == cur:
                self.autoconnect_combo.setCurrentIndex(i)
                break
        self.autoconnect_combo.activated.connect(self._on_autoconnect)
        layout.addWidget(_row(
            tr("Auto-connect on launch"),
            self.autoconnect_combo,
            tr("Connect right after the app starts."),
        ))

        return card

    def _build_dns_card(self) -> QFrame:
        card, layout = _card(tr("DNS"), tr("Which DNS resolver to use inside the VPN"))

        self.dns_preset = QComboBox()
        for title, _ in DNS_PRESETS:
            self.dns_preset.addItem(title)
        self.dns_preset.addItem(tr("Custom upstream"))
        self.dns_preset.activated.connect(self._on_dns_preset)
        layout.addWidget(_row(tr("Preset"), self.dns_preset))

        # Upstream — отдельный блок (под-карточка), чтобы поле + кнопка точно влезли
        dns_block = QFrame(); dns_block.setObjectName("CardFlat")
        db = QVBoxLayout(dns_block); db.setContentsMargins(14, 12, 14, 12); db.setSpacing(8)
        db_title = QLabel(tr("Custom upstream"))
        db_title.setStyleSheet("font-size: 13px; font-weight: 600;")
        db.addWidget(db_title)
        self.dns_input = QLineEdit()
        self.dns_input.setPlaceholderText("https://example/dns-query или 1.1.1.1")
        apply_dns = QPushButton(tr("Apply"))
        apply_dns.setObjectName("Primary")
        apply_dns.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_dns.clicked.connect(self._apply_dns)
        dns_row = QHBoxLayout(); dns_row.setSpacing(8)
        dns_row.addWidget(self.dns_input, 1); dns_row.addWidget(apply_dns)
        db.addLayout(dns_row)
        layout.addWidget(dns_block)

        return card

    def _build_socks_card(self) -> QFrame:
        card, layout = _card(tr("SOCKS proxy"), tr("Used when SOCKS mode is selected"))

        self.socks_host = QLineEdit()
        self.socks_host.setFixedWidth(150)
        apply_host = QPushButton("OK"); apply_host.setObjectName("Ghost"); apply_host.setFixedWidth(54)
        apply_host.clicked.connect(lambda: self._on_user("set-socks-host", self.socks_host.text().strip() or "127.0.0.1"))
        host_wrap = QWidget()
        host_row = QHBoxLayout(host_wrap); host_row.setContentsMargins(0, 0, 0, 0); host_row.setSpacing(6)
        host_row.addWidget(self.socks_host); host_row.addWidget(apply_host)
        layout.addWidget(_row(tr("Host"), host_wrap))

        self.socks_port = QSpinBox()
        self.socks_port.setRange(1, 65535)
        self.socks_port.setFixedWidth(110)
        apply_port = QPushButton("OK"); apply_port.setObjectName("Ghost"); apply_port.setFixedWidth(54)
        apply_port.clicked.connect(lambda: self._on_user("set-socks-port", str(self.socks_port.value())))
        port_wrap = QWidget()
        port_row = QHBoxLayout(port_wrap); port_row.setContentsMargins(0, 0, 0, 0); port_row.setSpacing(6)
        port_row.addWidget(self.socks_port); port_row.addWidget(apply_port)
        layout.addWidget(_row(tr("Port"), port_wrap))

        # Auth — отдельная под-карточка с двумя строками, помещается в любую ширину
        auth_block = QFrame(); auth_block.setObjectName("CardFlat")
        ab = QVBoxLayout(auth_block); ab.setContentsMargins(14, 12, 14, 12); ab.setSpacing(8)
        ab_title = QLabel(tr("Authentication"))
        ab_title.setStyleSheet("font-size: 13px; font-weight: 600;")
        ab_hint = QLabel(tr("Required when SOCKS listens on a non-localhost address"))
        ab_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        ab.addWidget(ab_title); ab.addWidget(ab_hint)

        self.socks_username = QLineEdit(); self.socks_username.setPlaceholderText(tr("username"))
        self.socks_password = QLineEdit(); self.socks_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.socks_password.setPlaceholderText(tr("password"))
        inputs_row = QHBoxLayout(); inputs_row.setSpacing(8)
        inputs_row.addWidget(self.socks_username); inputs_row.addWidget(self.socks_password)
        ab.addLayout(inputs_row)

        btns_row = QHBoxLayout(); btns_row.setSpacing(8)
        save_auth = QPushButton(tr("Save")); save_auth.setObjectName("Primary")
        save_auth.clicked.connect(self._save_socks_auth)
        clear_auth = QPushButton(tr("Reset")); clear_auth.setObjectName("Danger")
        clear_auth.clicked.connect(lambda: self._on_user("clear-socks-auth"))
        btns_row.addWidget(save_auth); btns_row.addWidget(clear_auth); btns_row.addStretch(1)
        ab.addLayout(btns_row)
        layout.addWidget(auth_block)

        create_script = QPushButton(tr("Create route script"))
        create_script.setObjectName("Ghost")
        create_script.clicked.connect(lambda: self._on_user("create-route-script"))
        layout.addWidget(_row(tr("Routing"), create_script))

        return card

    def _build_privacy_card(self) -> QFrame:
        card, layout = _card(tr("Privacy and notifications"))
        self.crash_toggle = ToggleSwitch()
        self.crash_toggle.toggled.connect(lambda v: self._on_user("set-crash-reporting", "on" if v else "off"))
        layout.addWidget(_row(tr("Crash reports"), self.crash_toggle))

        self.telemetry_toggle = ToggleSwitch()
        self.telemetry_toggle.toggled.connect(lambda v: self._on_user("set-telemetry", "on" if v else "off"))
        layout.addWidget(_row(tr("Anonymous statistics"), self.telemetry_toggle))

        self.debug_toggle = ToggleSwitch()
        self.debug_toggle.toggled.connect(lambda v: self._on_user("set-debug-logging", "on" if v else "off"))
        layout.addWidget(_row(tr("Verbose logging"), self.debug_toggle, tr("Useful for diagnostics")))

        self.notify_toggle = ToggleSwitch()
        self.notify_toggle.toggled.connect(lambda v: self._on_user("set-show-notifications", "on" if v else "off"))
        layout.addWidget(_row(tr("System notifications"), self.notify_toggle))

        self.hints_toggle = ToggleSwitch()
        self.hints_toggle.toggled.connect(lambda v: self._on_user("set-show-hints", "on" if v else "off"))
        layout.addWidget(_row(tr("CLI hints"), self.hints_toggle))

        return card

    def _build_updates_card(self) -> QFrame:
        card, layout = _card(tr("Updates"))
        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["release", "beta", "nightly"])
        self.channel_combo.activated.connect(lambda _i: self._on_user("set-update-channel", self.channel_combo.currentText()))
        layout.addWidget(_row(tr("Channel"), self.channel_combo))

        check_btn = QPushButton(tr("Check for updates"))
        check_btn.setObjectName("Ghost")
        check_btn.clicked.connect(self.runner.check_update)
        layout.addWidget(_row(tr("Check"), check_btn))

        return card

    def _build_network_card(self) -> QFrame:
        card, layout = _card(tr("Network"))
        net_block = QFrame(); net_block.setObjectName("CardFlat")
        nb = QVBoxLayout(net_block); nb.setContentsMargins(14, 12, 14, 12); nb.setSpacing(8)
        title = QLabel(tr("Outbound network interface"))
        title.setStyleSheet("font-size: 13px; font-weight: 600;")
        hint = QLabel(tr("Bind VPN to a specific network adapter; empty = auto."))
        hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;"); hint.setWordWrap(True)
        nb.addWidget(title); nb.addWidget(hint)
        self.bound_if = QLineEdit()
        self.bound_if.setPlaceholderText(tr("e.g. wlan0"))
        apply_if = QPushButton(tr("Apply")); apply_if.setObjectName("Primary")
        apply_if.clicked.connect(lambda: self._on_user("set-bound-if-override", self.bound_if.text().strip()))
        row = QHBoxLayout(); row.setSpacing(8); row.addWidget(self.bound_if, 1); row.addWidget(apply_if)
        nb.addLayout(row)
        layout.addWidget(net_block)
        return card

    def _build_gui_card(self) -> QFrame:
        card, layout = _card(tr("Application"), tr("GUI-only settings (not sent to CLI)"))

        bin_block = QFrame(); bin_block.setObjectName("CardFlat")
        bb = QVBoxLayout(bin_block); bb.setContentsMargins(14, 12, 14, 12); bb.setSpacing(8)
        bt = QLabel(tr("Path to adguardvpn-cli")); bt.setStyleSheet("font-size: 13px; font-weight: 600;")
        bb.addWidget(bt)
        self.binary_input = QLineEdit(self.state.prefs.binary_path)
        save_binary = QPushButton(tr("Save")); save_binary.setObjectName("Primary")
        save_binary.clicked.connect(self._save_binary)
        bin_row = QHBoxLayout(); bin_row.setSpacing(8)
        bin_row.addWidget(self.binary_input, 1); bin_row.addWidget(save_binary)
        bb.addLayout(bin_row)
        layout.addWidget(bin_block)

        self.refresh_spin = QSpinBox()
        self.refresh_spin.setRange(2, 60)
        self.refresh_spin.setValue(self.state.prefs.refresh_interval_sec)
        self.refresh_spin.setFixedWidth(100)
        self.refresh_spin.editingFinished.connect(self._save_refresh)
        layout.addWidget(_row(tr("Poll interval (s)"), self.refresh_spin))

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 180)
        self.timeout_spin.setValue(self.state.prefs.timeout_sec)
        self.timeout_spin.setFixedWidth(100)
        self.timeout_spin.editingFinished.connect(self._save_timeout)
        layout.addWidget(_row(tr("Command timeout (s)"), self.timeout_spin))

        self.close_to_tray = ToggleSwitch(self.state.prefs.close_to_tray)
        self.close_to_tray.toggled.connect(self._save_close_to_tray)
        layout.addWidget(_row(tr("Close minimizes to tray"), self.close_to_tray))

        self.start_minimized = ToggleSwitch(self.state.prefs.start_minimized)
        self.start_minimized.toggled.connect(self._save_start_minimized)
        layout.addWidget(_row(tr("Start minimized"), self.start_minimized))

        # Language combo: меняет prefs.lang и просит перезапуск.
        self.lang_combo = QComboBox()
        for code, label in LANGUAGES:
            self.lang_combo.addItem(label, code)
        current = current_lang()
        for i in range(self.lang_combo.count()):
            if self.lang_combo.itemData(i) == current:
                self.lang_combo.setCurrentIndex(i)
                break
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        layout.addWidget(_row(tr("Language"), self.lang_combo))

        return card

    # --- Sync / write helpers --------------------------------------------

    def _sync_from_config(self, cfg: VpnConfig) -> None:
        self._syncing = True
        try:
            self.mode_combo.setCurrentText("TUN" if cfg.mode == "tun" else "SOCKS")
            self.protocol_combo.setCurrentText(cfg.protocol or "auto")
            self.routing_combo.setCurrentText(cfg.tun_routing_mode or "auto")
            self.system_dns_toggle.setChecked(cfg.change_system_dns, animate=False)
            self.post_quantum_toggle.setChecked(cfg.post_quantum, animate=False)
            if cfg.dns_upstream:
                self.dns_input.setText(cfg.dns_upstream)
                matched = False
                for idx, (_, value) in enumerate(DNS_PRESETS):
                    if value and value == cfg.dns_upstream:
                        self.dns_preset.setCurrentIndex(idx)
                        matched = True
                        break
                if not matched:
                    self.dns_preset.setCurrentIndex(self.dns_preset.count() - 1)
            else:
                self.dns_input.clear()
                self.dns_preset.setCurrentIndex(0)
            self.socks_host.setText(cfg.socks_host)
            self.socks_port.setValue(cfg.socks_port)
            self.socks_username.setText(cfg.socks_username)
            self.crash_toggle.setChecked(cfg.crash_reporting, animate=False)
            self.telemetry_toggle.setChecked(cfg.telemetry, animate=False)
            self.debug_toggle.setChecked(cfg.debug_logging, animate=False)
            self.notify_toggle.setChecked(cfg.show_notifications, animate=False)
            self.hints_toggle.setChecked(cfg.show_hints, animate=False)
            self.channel_combo.setCurrentText(cfg.update_channel or "release")
            self.bound_if.setText(cfg.bound_if)
        finally:
            self._syncing = False

    def _on_user(self, key: str, *values: str) -> None:
        if self._syncing:
            return
        self.runner.config_set(key, *values)
        QTimer.singleShot(600, self.runner.config_show)

    def _on_dns_preset(self, idx: int) -> None:
        if self._syncing:
            return
        if idx < len(DNS_PRESETS):
            value = DNS_PRESETS[idx][1]
            self.dns_input.setText(value)
            if value:
                self._on_user("set-dns", value)
            else:
                # default: clear by setting empty? CLI may not support; we just don't apply
                pass

    def _apply_dns(self) -> None:
        text = self.dns_input.text().strip()
        if not text:
            return
        self._on_user("set-dns", text)

    def _save_socks_auth(self) -> None:
        user = self.socks_username.text().strip()
        pwd = self.socks_password.text()
        if user:
            self.runner.config_set("set-socks-username", user)
        if pwd:
            self.runner.config_set("set-socks-password", pwd)
        QTimer.singleShot(600, self.runner.config_show)

    def _save_binary(self) -> None:
        prefs = self.state.prefs
        prefs.binary_path = self.binary_input.text().strip() or "adguardvpn-cli"
        self.runner.adapter.set_prefs(prefs)
        self.store.save(prefs)
        self.state.set_prefs(prefs)

    def _save_refresh(self) -> None:
        prefs = self.state.prefs
        prefs.refresh_interval_sec = self.refresh_spin.value()
        self.store.save(prefs)
        self.state.set_prefs(prefs)

    def _save_timeout(self) -> None:
        prefs = self.state.prefs
        prefs.timeout_sec = self.timeout_spin.value()
        self.runner.adapter.set_prefs(prefs)
        self.store.save(prefs)
        self.state.set_prefs(prefs)

    def _save_close_to_tray(self, value: bool) -> None:
        prefs = self.state.prefs
        prefs.close_to_tray = value
        self.store.save(prefs)
        self.state.set_prefs(prefs)

    def _save_start_minimized(self, value: bool) -> None:
        prefs = self.state.prefs
        prefs.start_minimized = value
        self.store.save(prefs)
        self.state.set_prefs(prefs)

    def _on_kill_switch(self, value: bool) -> None:
        if self._syncing:
            return
        prefs = self.state.prefs
        prefs.kill_switch = value
        self.store.save(prefs)
        self.state.set_prefs(prefs)

    def _on_autostart(self, value: bool) -> None:
        if self._syncing:
            return
        prefs = self.state.prefs
        prefs.autostart = value
        self.store.save(prefs)
        # set_prefs запустит _on_prefs в app.py, который вызовет autostart_sync
        self.state.set_prefs(prefs)

    def _on_autoconnect(self, _idx: int) -> None:
        if self._syncing:
            return
        mode = self.autoconnect_combo.currentData() or "off"
        if mode == self.state.prefs.autoconnect_mode:
            return
        prefs = self.state.prefs
        prefs.autoconnect_mode = mode
        self.store.save(prefs)
        self.state.set_prefs(prefs)

    def _on_language_changed(self, _idx: int) -> None:
        if self._syncing:
            return
        code = self.lang_combo.currentData()
        if not code or code == self.state.prefs.lang:
            return
        prefs = self.state.prefs
        prefs.lang = code
        self.store.save(prefs)
        set_lang(code)
        # Сигнал — MainWindow и Tray пересоберут переводимые строки на лету.
        self.state.language_changed.emit()
        self.state.set_prefs(prefs)
