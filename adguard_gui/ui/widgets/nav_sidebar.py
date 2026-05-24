from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QButtonGroup, QFrame, QLabel, QPushButton, QVBoxLayout, QWidget

from adguard_gui.theme import ACCENT, TEXT, TEXT_MUTED, make_icon


class NavSidebar(QFrame):
    current_changed = Signal(int)

    def __init__(self, items: list[tuple[str, str]], parent: QWidget | None = None) -> None:
        """items: list of (icon_name, label)."""
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(228)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        brand = QLabel("AdGuard VPN")
        brand.setObjectName("SidebarBrand")
        outer.addWidget(brand)
        outer.addSpacing(8)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._buttons: list[QPushButton] = []
        for idx, (icon_name, label) in enumerate(items):
            btn = QPushButton(label)
            btn.setObjectName("NavItem")
            btn.setCheckable(True)
            btn.setIcon(make_icon(icon_name, TEXT_MUTED, 18))
            btn.setIconSize(QSize(18, 18))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, i=idx: self._on_clicked(i))
            self._group.addButton(btn, idx)
            self._buttons.append(btn)
            outer.addWidget(btn)
            # swap icon on toggle
            btn.toggled.connect(lambda checked, b=btn, n=icon_name: b.setIcon(make_icon(n, TEXT if checked else TEXT_MUTED, 18)))

        outer.addStretch(1)

        self.footer = QLabel("")
        self.footer.setObjectName("SidebarFooter")
        self.footer.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.footer.setWordWrap(True)
        outer.addWidget(self.footer)

        self.set_current(0)

    def set_current(self, index: int) -> None:
        if 0 <= index < len(self._buttons):
            self._buttons[index].setChecked(True)

    def _on_clicked(self, index: int) -> None:
        self.current_changed.emit(index)

    def set_footer(self, text: str) -> None:
        self.footer.setText(text)
