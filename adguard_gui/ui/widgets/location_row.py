from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from adguard_gui.i18n import tr
from adguard_gui.models.types import Location
from adguard_gui.theme import (
    ACCENT,
    ACCENT_SOFT,
    BG_HOVER,
    BG_ELEVATED,
    BORDER,
    TEXT,
    TEXT_DIM,
    TEXT_MUTED,
    make_icon,
    ping_color,
)
from adguard_gui.ui.widgets.pending_button import PendingButton


class _IsoBadge(QLabel):
    def __init__(self, iso: str) -> None:
        super().__init__(iso.upper())
        self.setFixedSize(38, 28)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"background-color: {BG_ELEVATED}; color: {TEXT}; "
            f"border: 1px solid {BORDER}; border-radius: 6px; "
            f"font-weight: 700; font-size: 11px; letter-spacing: 0.5px;"
        )


class LocationRow(QFrame):
    connect_requested = Signal(object)
    disconnect_requested = Signal()
    favorite_toggled = Signal(str)

    def __init__(
        self,
        location: Location,
        *,
        is_favorite: bool,
        is_current: bool,
        is_pending: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.location = location
        self._is_favorite = is_favorite
        self._is_current = is_current
        self._is_pending = is_pending
        self.setObjectName("CardFlat")
        self.setMinimumHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(14)

        self.badge = _IsoBadge(location.iso)
        layout.addWidget(self.badge)

        text_box = QVBoxLayout()
        text_box.setContentsMargins(0, 0, 0, 0)
        text_box.setSpacing(2)
        self.city = QLabel(location.city)
        self.city.setStyleSheet(f"color: {TEXT}; font-size: 14px; font-weight: 600;")
        self.country = QLabel(location.country)
        self.country.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
        text_box.addWidget(self.city)
        text_box.addWidget(self.country)
        layout.addLayout(text_box, 1)

        if is_current:
            current_badge = QLabel(tr("active"))
            current_badge.setStyleSheet(
                f"background-color: {ACCENT_SOFT}; color: {ACCENT}; "
                f"padding: 3px 8px; border-radius: 8px; font-size: 11px; font-weight: 600;"
            )
            layout.addWidget(current_badge)
        elif is_pending:
            pending_badge = QLabel(tr("Connecting…"))
            pending_badge.setStyleSheet(
                f"background-color: #3a2f12; color: #ffb74d; "
                f"padding: 3px 8px; border-radius: 8px; font-size: 11px; font-weight: 600;"
            )
            layout.addWidget(pending_badge)

        ping = location.ping_ms
        ping_label = QLabel(f"{ping} ms" if ping is not None else "—")
        ping_label.setStyleSheet(f"color: {ping_color(ping)}; font-size: 13px; font-weight: 600; min-width: 56px;")
        ping_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(ping_label)

        self.fav_btn = QPushButton()
        self.fav_btn.setObjectName("Ghost")
        self.fav_btn.setFixedSize(30, 30)
        self.fav_btn.setIconSize(QSize(18, 18))
        self.fav_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fav_btn.setToolTip(tr("Favorite"))
        self._refresh_fav_icon()
        self.fav_btn.clicked.connect(self._on_fav)
        layout.addWidget(self.fav_btn)

        # Действующая кнопка справа меняется в зависимости от состояния строки.
        if is_current:
            self.action_btn = QPushButton(tr("Disconnect"))
            self.action_btn.setObjectName("DangerSolid")
            self.action_btn.clicked.connect(self.disconnect_requested.emit)
            self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        elif is_pending:
            self.action_btn = PendingButton()
        else:
            self.action_btn = QPushButton(tr("Connect"))
            self.action_btn.setObjectName("Primary")
            self.action_btn.clicked.connect(self._emit_connect)
            self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # Одинаковая высота/ширина для всех состояний — кнопки в столбце выровнены.
        self.action_btn.setFixedSize(132, 38)
        layout.addWidget(self.action_btn)

        self._update_style()

    def _emit_connect(self) -> None:
        self.connect_requested.emit(self.location)

    def _update_style(self) -> None:
        if self._is_current:
            self.setStyleSheet(
                f"QFrame#CardFlat {{ background-color: {ACCENT_SOFT}; border: 1px solid {ACCENT}; }}"
            )
        elif self._is_pending:
            self.setStyleSheet(
                "QFrame#CardFlat { background-color: #2c2818; border: 1px solid #ffb74d; }"
            )
        else:
            self.setStyleSheet("")

    def mouseDoubleClickEvent(self, event) -> None:
        # Двойной клик на активной локации = disconnect, иначе = connect.
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_current:
                self.disconnect_requested.emit()
            elif not self._is_pending:
                self.connect_requested.emit(self.location)
        super().mouseDoubleClickEvent(event)

    def _refresh_fav_icon(self) -> None:
        name = "star_filled" if self._is_favorite else "star"
        color = ACCENT if self._is_favorite else TEXT_DIM
        self.fav_btn.setIcon(make_icon(name, color, 18))

    def _on_fav(self) -> None:
        self._is_favorite = not self._is_favorite
        self._refresh_fav_icon()
        self.favorite_toggled.emit(self.location.iso)
