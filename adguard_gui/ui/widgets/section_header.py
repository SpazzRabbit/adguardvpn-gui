from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from adguard_gui.theme import TEXT, TEXT_MUTED


def _bold(label: QLabel, *, pt: int) -> None:
    f = label.font()
    f.setPointSize(pt)
    f.setBold(True)
    label.setFont(f)


class SectionHeader(QWidget):
    def __init__(self, title: str, subtitle: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.title = QLabel(title)
        self.title.setStyleSheet(f"color: {TEXT};")
        _bold(self.title, pt=11)
        layout.addWidget(self.title)

        if subtitle:
            self.subtitle = QLabel(subtitle)
            self.subtitle.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
            self.subtitle.setWordWrap(True)
            layout.addWidget(self.subtitle)


class PageHeader(QWidget):
    def __init__(self, title: str, subtitle: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.title = QLabel(title)
        self.title.setStyleSheet(f"color: {TEXT};")
        _bold(self.title, pt=18)
        layout.addWidget(self.title)
        if subtitle:
            self.subtitle = QLabel(subtitle)
            self.subtitle.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
            self.subtitle.setWordWrap(True)
            layout.addWidget(self.subtitle)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
