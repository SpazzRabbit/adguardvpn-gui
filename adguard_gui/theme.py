from __future__ import annotations

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication


BG = "#15181d"
BG_ELEVATED = "#1d2128"
BG_CARD = "#21262e"
BG_HOVER = "#272d36"
BG_PRESSED = "#2f3641"
BORDER = "#2a2f38"
BORDER_STRONG = "#353c47"

TEXT = "#e8eaed"
TEXT_MUTED = "#9aa0a6"
TEXT_DIM = "#6b7280"

ACCENT = "#68bc71"
ACCENT_HOVER = "#7fc888"
ACCENT_PRESSED = "#56a960"
ACCENT_SOFT = "#2d5235"

DANGER = "#e57373"
DANGER_HOVER = "#ef9a9a"
DANGER_SOFT = "#4a2828"

WARNING = "#ffb74d"
INFO = "#64b5f6"


PING_GOOD = "#68bc71"
PING_MID = "#ffb74d"
PING_BAD = "#e57373"


_ICONS: dict[str, str] = {
    "power": """<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
        <path fill='none' stroke='{c}' stroke-width='2.4' stroke-linecap='round'
              d='M12 3v9'/>
        <path fill='none' stroke='{c}' stroke-width='2.4' stroke-linecap='round'
              d='M6.5 7.5a8 8 0 1 0 11 0'/>
    </svg>""",
    "home": """<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
        <path fill='none' stroke='{c}' stroke-width='2' stroke-linejoin='round'
              d='M3 11 12 4l9 7v9a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z'/>
    </svg>""",
    "location": """<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
        <path fill='none' stroke='{c}' stroke-width='2'
              d='M12 22s7-7.58 7-13a7 7 0 1 0-14 0c0 5.42 7 13 7 13z'/>
        <circle cx='12' cy='9' r='2.6' fill='none' stroke='{c}' stroke-width='2'/>
    </svg>""",
    "settings": """<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
        <circle cx='12' cy='12' r='3' fill='none' stroke='{c}' stroke-width='2'/>
        <path fill='none' stroke='{c}' stroke-width='2' stroke-linejoin='round'
              d='M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 0 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1A2 2 0 1 1 4.3 17l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 4.6 9a1.7 1.7 0 0 0-.3-1.8l-.1-.1A2 2 0 1 1 7 4.3l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1A2 2 0 1 1 19.7 7l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z'/>
    </svg>""",
    "shield": """<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
        <path fill='none' stroke='{c}' stroke-width='2' stroke-linejoin='round'
              d='M12 3 4 6v6c0 5 3.4 9 8 10 4.6-1 8-5 8-10V6z'/>
        <path fill='none' stroke='{c}' stroke-width='2' stroke-linecap='round'
              d='m9 12 2 2 4-4'/>
    </svg>""",
    "user": """<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
        <circle cx='12' cy='8' r='4' fill='none' stroke='{c}' stroke-width='2'/>
        <path fill='none' stroke='{c}' stroke-width='2' stroke-linecap='round'
              d='M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8'/>
    </svg>""",
    "info": """<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
        <circle cx='12' cy='12' r='9' fill='none' stroke='{c}' stroke-width='2'/>
        <path fill='none' stroke='{c}' stroke-width='2' stroke-linecap='round'
              d='M12 11v6M12 7.5v.01'/>
    </svg>""",
    "search": """<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
        <circle cx='11' cy='11' r='7' fill='none' stroke='{c}' stroke-width='2'/>
        <path fill='none' stroke='{c}' stroke-width='2' stroke-linecap='round' d='m20 20-3.5-3.5'/>
    </svg>""",
    "refresh": """<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
        <path fill='none' stroke='{c}' stroke-width='2' stroke-linecap='round'
              d='M3 12a9 9 0 0 1 15.5-6.2L21 8M21 3v5h-5M21 12a9 9 0 0 1-15.5 6.2L3 16M3 21v-5h5'/>
    </svg>""",
    "star": """<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
        <path fill='none' stroke='{c}' stroke-width='1.8' stroke-linejoin='round'
              d='m12 4 2.6 5.4 5.9.7-4.4 4.1 1.2 5.8L12 17l-5.3 3 1.2-5.8L3.5 10.1l5.9-.7z'/>
    </svg>""",
    "star_filled": """<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
        <path fill='{c}' stroke='{c}' stroke-width='1.8' stroke-linejoin='round'
              d='m12 4 2.6 5.4 5.9.7-4.4 4.1 1.2 5.8L12 17l-5.3 3 1.2-5.8L3.5 10.1l5.9-.7z'/>
    </svg>""",
    "close": """<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
        <path fill='none' stroke='{c}' stroke-width='2.2' stroke-linecap='round'
              d='M6 6 18 18M18 6 6 18'/>
    </svg>""",
    "chevron_right": """<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
        <path fill='none' stroke='{c}' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'
              d='m9 6 6 6-6 6'/>
    </svg>""",
    "bolt": """<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
        <path fill='{c}' stroke='{c}' stroke-width='1' stroke-linejoin='round'
              d='M13 2 4 14h7l-1 8 9-12h-7z'/>
    </svg>""",
    "plus": """<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
        <path fill='none' stroke='{c}' stroke-width='2.4' stroke-linecap='round'
              d='M12 5v14M5 12h14'/>
    </svg>""",
}


def make_icon(name: str, color: str = TEXT, size: int = 20) -> QIcon:
    svg = _ICONS.get(name)
    if svg is None:
        return QIcon()
    svg = svg.replace("{c}", color)
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(p)
    p.end()
    return QIcon(pix)


def app_icon_path() -> str:
    """Путь к мастер-SVG приложения. Используется для QApplication.setWindowIcon."""
    import os
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons", "adguard-gui.svg"),
        "/usr/share/icons/hicolor/scalable/apps/adguard-gui.svg",
        "/usr/share/pixmaps/adguard-gui.svg",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]


def app_icon(size: int = 64) -> QIcon:
    path = app_icon_path()
    import os
    if not os.path.exists(path):
        return QIcon()
    renderer = QSvgRenderer(path)
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(p)
    p.end()
    icon = QIcon(pix)
    # подкинем несколько растровых размеров для трея/таскбара
    for s in (16, 22, 32, 48, 128):
        if s == size:
            continue
        p2 = QPixmap(s, s); p2.fill(Qt.GlobalColor.transparent)
        painter = QPainter(p2)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        QSvgRenderer(path).render(painter)
        painter.end()
        icon.addPixmap(p2)
    return icon


def ping_color(ping_ms: int | None) -> str:
    if ping_ms is None:
        return TEXT_DIM
    if ping_ms < 80:
        return PING_GOOD
    if ping_ms < 150:
        return PING_MID
    return PING_BAD


QSS = f"""
QMainWindow, QDialog {{
    background-color: {BG};
    color: {TEXT};
}}

QToolTip {{
    background-color: {BG_CARD};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 6px 8px;
    border-radius: 6px;
}}

/* Sidebar */
#Sidebar {{
    background-color: {BG_ELEVATED};
    border-right: 1px solid {BORDER};
}}
#SidebarBrand {{
    color: {TEXT};
    font-size: 16px;
    font-weight: 600;
    padding: 18px 20px 8px 20px;
}}
#SidebarBrandSub {{
    color: {TEXT_MUTED};
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 0 20px 18px 20px;
}}
QPushButton#NavItem {{
    text-align: left;
    padding: 11px 18px 11px 20px;
    border: none;
    border-left: 3px solid transparent;
    background-color: transparent;
    color: {TEXT_MUTED};
    font-size: 14px;
}}
QPushButton#NavItem:hover {{
    background-color: {BG_HOVER};
    color: {TEXT};
}}
QPushButton#NavItem:checked {{
    background-color: {BG_HOVER};
    border-left: 3px solid {ACCENT};
    color: {TEXT};
    font-weight: 600;
}}

#SidebarFooter {{
    color: {TEXT_DIM};
    font-size: 11px;
    padding: 10px 20px 14px 20px;
}}

/* Cards */
QFrame#Card {{
    background-color: {BG_CARD};
    border-radius: 12px;
    border: 1px solid {BORDER};
}}
QFrame#CardFlat {{
    background-color: {BG_ELEVATED};
    border-radius: 10px;
    border: 1px solid {BORDER};
}}

/* Section headers */
QLabel#SectionTitle {{
    color: {TEXT};
    font-size: 15px;
    font-weight: 600;
}}
QLabel#SectionSubtitle {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}
QLabel#PageTitle {{
    color: {TEXT};
    font-size: 22px;
    font-weight: 700;
}}
QLabel#PageSubtitle {{
    color: {TEXT_MUTED};
    font-size: 13px;
}}
QLabel#Muted {{ color: {TEXT_MUTED}; }}
QLabel#Dim {{ color: {TEXT_DIM}; }}

/* Buttons — единая геометрия для всех вариантов */
QPushButton {{
    background-color: {BG_HOVER};
    color: {TEXT};
    border: 1px solid {BORDER_STRONG};
    border-radius: 10px;
    padding: 9px 18px;
    font-weight: 500;
    min-height: 18px;
}}
QPushButton:hover {{ background-color: {BG_PRESSED}; border-color: {BORDER_STRONG}; }}
QPushButton:pressed {{ background-color: {BG_PRESSED}; }}
QPushButton:disabled {{ color: {TEXT_DIM}; background-color: {BG_ELEVATED}; border-color: {BORDER}; }}

QPushButton#Primary {{
    background-color: {ACCENT};
    color: #0f1a12;
    border: 1px solid {ACCENT};
    border-radius: 10px;
    padding: 9px 18px;
    font-weight: 600;
    min-height: 18px;
}}
QPushButton#Primary:hover {{ background-color: {ACCENT_HOVER}; border-color: {ACCENT_HOVER}; }}
QPushButton#Primary:pressed {{ background-color: {ACCENT_PRESSED}; border-color: {ACCENT_PRESSED}; }}
QPushButton#Primary:disabled {{ background-color: {ACCENT_SOFT}; color: {TEXT_DIM}; border-color: {ACCENT_SOFT}; }}

QPushButton#Danger {{
    background-color: transparent;
    color: {DANGER};
    border: 1px solid {DANGER_SOFT};
    border-radius: 10px;
    padding: 9px 18px;
    font-weight: 500;
    min-height: 18px;
}}
QPushButton#Danger:hover {{ background-color: {DANGER_SOFT}; color: {DANGER_HOVER}; }}

QPushButton#DangerSolid {{
    background-color: {DANGER};
    color: #1a0e0e;
    border: 1px solid {DANGER};
    border-radius: 10px;
    padding: 9px 18px;
    font-weight: 600;
    min-height: 18px;
}}
QPushButton#DangerSolid:hover {{ background-color: {DANGER_HOVER}; border-color: {DANGER_HOVER}; }}
QPushButton#DangerSolid:pressed {{ background-color: #d65656; border-color: #d65656; }}


QPushButton#Ghost {{
    background-color: transparent;
    color: {TEXT_MUTED};
    border: 1px solid transparent;
    border-radius: 10px;
    padding: 9px 18px;
    font-weight: 500;
    min-height: 18px;
}}
QPushButton#Ghost:hover {{ background-color: {BG_HOVER}; color: {TEXT}; }}

QPushButton#Chip {{
    background-color: {BG_ELEVATED};
    color: {TEXT_MUTED};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
    min-height: 14px;
}}
QPushButton#Chip:checked, QPushButton#Chip:hover {{
    background-color: {ACCENT_SOFT};
    color: {ACCENT_HOVER};
    border-color: {ACCENT};
}}

/* Inputs */
QLineEdit, QSpinBox, QComboBox, QPlainTextEdit, QTextEdit {{
    background-color: {BG_ELEVATED};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    selection-background-color: {ACCENT_SOFT};
    selection-color: {TEXT};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus, QTextEdit:focus {{
    border-color: {ACCENT};
}}

QLineEdit#Search {{
    padding-left: 36px;
    background-color: {BG_CARD};
}}

QComboBox::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox::down-arrow {{ image: none; }}
QComboBox QAbstractItemView {{
    background-color: {BG_ELEVATED};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT_SOFT};
    selection-color: {TEXT};
    outline: 0;
    padding: 4px;
}}

QSpinBox::up-button, QSpinBox::down-button {{ width: 0; height: 0; }}

/* Lists & scrolling */
QScrollArea {{ background-color: transparent; border: none; }}
QListWidget, QTreeWidget {{
    background-color: transparent;
    border: none;
    outline: 0;
}}
QListWidget::item {{
    padding: 0;
    background: transparent;
    border-radius: 8px;
    margin: 2px 0;
}}
QListWidget::item:selected {{ background-color: {BG_HOVER}; }}

QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 4px 2px 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER_STRONG};
    min-height: 24px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical:hover {{ background: #4a5260; }}
QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 10px;
    margin: 2px 4px 2px 4px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER_STRONG};
    min-width: 24px;
    border-radius: 5px;
}}
QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {{ width: 0; }}

/* Group boxes */
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 12px;
    background-color: {BG_CARD};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {TEXT_MUTED};
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* Checkbox/radio */
QCheckBox, QRadioButton {{
    color: {TEXT};
    spacing: 8px;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 1.5px solid {BORDER_STRONG};
    background-color: {BG_ELEVATED};
}}
QCheckBox::indicator {{ border-radius: 5px; }}
QRadioButton::indicator {{ border-radius: 9px; }}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background-color: {ACCENT};
    border-color: {ACCENT};
}}
QCheckBox::indicator:hover, QRadioButton::indicator:hover {{ border-color: {ACCENT_HOVER}; }}

/* Frames / separators */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{ color: {BORDER}; }}

/* Tab widget */
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{
    background: transparent;
    color: {TEXT_MUTED};
    padding: 8px 14px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 500;
}}
QTabBar::tab:selected {{ color: {TEXT}; border-bottom: 2px solid {ACCENT}; }}
QTabBar::tab:hover {{ color: {TEXT}; }}

/* Headers (table) */
QHeaderView::section {{
    background-color: transparent;
    color: {TEXT_MUTED};
    border: none;
    padding: 6px 8px;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QTableView, QTableWidget {{
    background-color: transparent;
    border: none;
    gridline-color: transparent;
    selection-background-color: {BG_HOVER};
    selection-color: {TEXT};
}}

/* Message box */
QMessageBox {{ background-color: {BG_CARD}; }}
QMessageBox QLabel {{ color: {TEXT}; }}

/* Menu */
QMenu {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 6px;
}}
QMenu::item {{
    padding: 7px 14px;
    border-radius: 6px;
}}
QMenu::item:selected {{ background-color: {BG_HOVER}; }}
QMenu::separator {{ height: 1px; background: {BORDER}; margin: 5px 4px; }}

/* Toggle switch container button look */
QPushButton#Toggle {{
    border: none;
    padding: 0;
    background: transparent;
}}
"""


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor(BG_ELEVATED))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(BG_CARD))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor(BG_HOVER))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#0f1a12"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(TEXT_DIM))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(TEXT_DIM))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(TEXT_DIM))
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(TEXT_DIM))
    app.setPalette(palette)

    families = QFontDatabase.families()
    chosen = None
    for candidate in ("Inter", "Ubuntu", "Cantarell", "Noto Sans", "Segoe UI", "Helvetica Neue", "DejaVu Sans"):
        if candidate in families:
            chosen = candidate
            break
    font = QFont(chosen) if chosen else QFont()
    font.setPointSize(10)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(font)

    app.setStyleSheet(QSS)


__all__ = [
    "apply_theme",
    "make_icon",
    "ping_color",
    "BG",
    "BG_ELEVATED",
    "BG_CARD",
    "BG_HOVER",
    "BG_PRESSED",
    "BORDER",
    "BORDER_STRONG",
    "TEXT",
    "TEXT_MUTED",
    "TEXT_DIM",
    "ACCENT",
    "ACCENT_HOVER",
    "ACCENT_PRESSED",
    "ACCENT_SOFT",
    "DANGER",
    "DANGER_HOVER",
    "WARNING",
    "INFO",
    "PING_GOOD",
    "PING_MID",
    "PING_BAD",
    "QSize",
]
