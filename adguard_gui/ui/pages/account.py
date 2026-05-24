from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from adguard_gui.i18n import tr
from adguard_gui.models.state import AppState
from adguard_gui.models.types import LicenseInfo
from adguard_gui.services.command_runner import CommandRunner
from adguard_gui.theme import (
    ACCENT,
    ACCENT_SOFT,
    BG_CARD,
    BORDER,
    TEXT,
    TEXT_DIM,
    TEXT_MUTED,
    WARNING,
    make_icon,
)
from adguard_gui.ui.widgets.section_header import PageHeader, SectionHeader


def _field(label: str, value: str) -> QWidget:
    box = QVBoxLayout()
    box.setSpacing(2)
    t = QLabel(label)
    t.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; letter-spacing: 1px; text-transform: uppercase;")
    v = QLabel(value)
    v.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: 600;")
    v.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    wrap = QFrame()
    wrap.setLayout(box)
    box.addWidget(t)
    box.addWidget(v)
    return wrap


class AccountPage(QWidget):
    def __init__(self, state: AppState, runner: CommandRunner) -> None:
        super().__init__()
        self.state = state
        self.runner = runner

        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 24)
        outer.setSpacing(18)
        outer.addWidget(PageHeader(tr("Account"), tr("AdGuard VPN authentication and subscription")))

        self.logged_card = self._build_logged_card()
        self.login_card = self._build_login_card()
        outer.addWidget(self.logged_card)
        outer.addWidget(self.login_card)
        outer.addStretch(1)

        self.state.license_changed.connect(self._render)
        self._render(self.state.license)

    def _build_logged_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)

        header = QHBoxLayout(); header.setSpacing(12)
        icon = QLabel(); icon.setPixmap(make_icon("user", ACCENT, 32).pixmap(32, 32))
        header.addWidget(icon)
        title_box = QVBoxLayout(); title_box.setSpacing(2)
        self.account_email = QLabel("—")
        self.account_email.setStyleSheet(f"color: {TEXT}; font-size: 18px; font-weight: 700;")
        title_box.addWidget(self.account_email)
        self.tier_badge = QLabel("—")
        self.tier_badge.setStyleSheet(
            f"background-color: {ACCENT_SOFT}; color: {ACCENT}; "
            f"padding: 2px 8px; border-radius: 8px; font-size: 11px; font-weight: 700;"
        )
        self.tier_badge.setFixedHeight(20)
        tier_row = QHBoxLayout(); tier_row.setContentsMargins(0, 0, 0, 0); tier_row.setSpacing(6)
        tier_row.addWidget(self.tier_badge); tier_row.addStretch(1)
        title_box.addLayout(tier_row)
        header.addLayout(title_box, 1)

        logout_btn = QPushButton(tr("Sign out"))
        logout_btn.setObjectName("Danger")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self._logout)
        header.addWidget(logout_btn)
        layout.addLayout(header)

        details_row = QHBoxLayout(); details_row.setSpacing(30)
        self.devices_field = QLabel("—"); self.devices_field.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: 600;")
        self.valid_field = QLabel("—"); self.valid_field.setStyleSheet(f"color: {TEXT}; font-size: 16px; font-weight: 600;")

        for title, widget in [(tr("Devices"), self.devices_field), (tr("Subscription valid until"), self.valid_field)]:
            box = QVBoxLayout(); box.setSpacing(2)
            t = QLabel(title); t.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px; letter-spacing: 1px; text-transform: uppercase;")
            box.addWidget(t); box.addWidget(widget)
            wrap = QFrame(); wrap.setLayout(box)
            details_row.addWidget(wrap)
        details_row.addStretch(1)
        layout.addLayout(details_row)

        return card

    def _build_login_card(self) -> QFrame:
        card = QFrame(); card.setObjectName("Card")
        layout = QVBoxLayout(card); layout.setContentsMargins(24, 22, 24, 22); layout.setSpacing(12)

        layout.addWidget(SectionHeader(tr("Sign in to AdGuard VPN"), tr("Enter your AdGuard credentials")))

        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("you@example.com")
        layout.addWidget(self.login_email)

        self.login_password = QLineEdit()
        self.login_password.setPlaceholderText(tr("Password"))
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.login_password)

        btn = QPushButton(tr("Sign in"))
        btn.setObjectName("Primary")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._login)
        layout.addWidget(btn)

        return card

    def _render(self, info: LicenseInfo) -> None:
        if info.logged_in:
            self.logged_card.setVisible(True)
            self.login_card.setVisible(False)
            self.account_email.setText(info.email or "—")
            tier = info.tier or "FREE"
            self.tier_badge.setText(tier)
            if tier == "PREMIUM":
                self.tier_badge.setStyleSheet(
                    f"background-color: {ACCENT_SOFT}; color: {ACCENT}; padding: 2px 8px; border-radius: 8px; font-size: 11px; font-weight: 700;"
                )
            else:
                self.tier_badge.setStyleSheet(
                    f"background-color: rgba(255, 183, 77, 0.18); color: {WARNING}; padding: 2px 8px; border-radius: 8px; font-size: 11px; font-weight: 700;"
                )
            self.devices_field.setText(tr("up to {n}", n=info.device_limit) if info.device_limit else "—")
            self.valid_field.setText(info.valid_until or "—")
        else:
            self.logged_card.setVisible(False)
            self.login_card.setVisible(True)

    def _logout(self) -> None:
        reply = QMessageBox.question(
            self,
            tr("Confirmation"),
            tr("Sign out of AdGuard VPN? VPN will be disconnected."),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.runner.logout()
            from PySide6.QtCore import QTimer
            QTimer.singleShot(600, self.runner.license)
            QTimer.singleShot(800, self.runner.status)

    def _login(self) -> None:
        email = self.login_email.text().strip()
        pwd = self.login_password.text()
        if not email or not pwd:
            QMessageBox.warning(self, tr("Sign in"), tr("Enter email and password."))
            return
        self.runner.login(email, pwd)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(800, self.runner.license)
        self.login_password.clear()
