from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QStackedWidget, QWidget

from adguard_gui.adapters.cli_adapter import CliAdapter
from adguard_gui.i18n import tr
from adguard_gui.models.state import AppState
from adguard_gui.models.types import ConnectionStatus
from adguard_gui.services.command_runner import CommandRunner
from adguard_gui.services.poller import Poller
from adguard_gui.storage.config_store import ConfigStore
from adguard_gui.ui.pages.about import AboutPage
from adguard_gui.ui.pages.account import AccountPage
from adguard_gui.ui.pages.exclusions import ExclusionsPage
from adguard_gui.ui.pages.home import HomePage
from adguard_gui.ui.pages.locations import LocationsPage
from adguard_gui.ui.pages.settings import SettingsPage
from adguard_gui.ui.widgets.nav_sidebar import NavSidebar


def _nav_items() -> list[tuple[str, str]]:
    return [
        ("home", tr("Home")),
        ("location", tr("Locations")),
        ("settings", tr("Settings")),
        ("shield", tr("Exclusions")),
        ("user", tr("Account")),
        ("info", tr("About")),
    ]


class MainWindow(QMainWindow):
    def __init__(
        self,
        state: AppState,
        adapter: CliAdapter,
        runner: CommandRunner,
        store: ConfigStore,
        poller: Poller,
    ) -> None:
        super().__init__()
        self.state = state
        self.adapter = adapter
        self.runner = runner
        self.store = store
        self.poller = poller
        self._force_close = False

        self.setWindowTitle("AdGuard VPN")
        self.setMinimumSize(960, 640)
        self.resize(1120, 720)

        self._build_ui(initial_index=0)

        self.state.status_changed.connect(self._update_footer)
        self.state.license_changed.connect(self._update_footer)
        self.state.language_changed.connect(self._rebuild_ui)
        self._update_footer()

    def _build_ui(self, initial_index: int = 0) -> None:
        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.sidebar = NavSidebar(_nav_items())
        outer.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        outer.addWidget(self.stack, 1)

        self.home = HomePage(self.state, self.runner, navigate_locations=lambda: self._goto(1))
        self.locations = LocationsPage(self.state, self.runner)
        self.settings_page = SettingsPage(self.state, self.runner, self.store)
        self.exclusions = ExclusionsPage(self.state, self.runner)
        self.account = AccountPage(self.state, self.runner)
        self.about = AboutPage(self.state, self.runner, self.adapter)

        for page in [self.home, self.locations, self.settings_page, self.exclusions, self.account, self.about]:
            self.stack.addWidget(page)

        self.sidebar.current_changed.connect(self._goto)
        self.setCentralWidget(root)
        self._goto(initial_index)

    def _rebuild_ui(self) -> None:
        """Пересобрать UI после смены языка, сохранив активную страницу.

        Новые страницы сами подтягивают актуальные значения из state в своих
        конструкторах, поэтому достаточно построить их и удалить старый
        центральный виджет — старые подписки умрут вместе с QObject'ами,
        для которых PySide ведёт автоматический disconnect.
        """
        current = self.stack.currentIndex() if hasattr(self, "stack") else 0
        old_central = self.centralWidget()
        self._build_ui(initial_index=current)
        if old_central is not None:
            old_central.deleteLater()
        self._update_footer()

    def _goto(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.sidebar.set_current(index)

    def _update_footer(self, *_args) -> None:
        st = self.state.status
        lic = self.state.license
        bits: list[str] = []
        if lic.email:
            bits.append(lic.email)
        if st.state == "connected":
            bits.append(tr("VPN active"))
        elif st.state == "connecting":
            bits.append(tr("Connecting…"))
        elif st.state == "disconnected":
            bits.append(tr("VPN off"))
        self.sidebar.set_footer("  •  ".join(bits))

    def show_initial(self) -> None:
        if not self.state.prefs.start_minimized:
            self.show()

    def set_force_close(self, value: bool) -> None:
        self._force_close = value

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._force_close or not self.state.prefs.close_to_tray:
            event.accept()
            from PySide6.QtWidgets import QApplication
            QApplication.instance().quit()
            return
        event.ignore()
        self.hide()
