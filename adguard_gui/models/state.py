from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from adguard_gui.models.types import (
    ConnectionStatus,
    ExclusionsState,
    GuiPrefs,
    LicenseInfo,
    Location,
    UpdateInfo,
    VpnConfig,
)


class AppState(QObject):
    status_changed = Signal(ConnectionStatus)
    license_changed = Signal(LicenseInfo)
    locations_changed = Signal(list)
    config_changed = Signal(VpnConfig)
    exclusions_changed = Signal(ExclusionsState)
    prefs_changed = Signal(GuiPrefs)
    busy_changed = Signal(bool)
    language_changed = Signal()
    update_changed = Signal(UpdateInfo)

    def __init__(self, prefs: GuiPrefs) -> None:
        super().__init__()
        self._prefs = prefs
        self._status = ConnectionStatus()
        self._license = LicenseInfo()
        self._locations: list[Location] = []
        self._config = VpnConfig()
        self._exclusions = ExclusionsState()
        self._update = UpdateInfo()
        self._busy = False

    @property
    def prefs(self) -> GuiPrefs:
        return self._prefs

    def set_prefs(self, prefs: GuiPrefs) -> None:
        self._prefs = prefs
        self.prefs_changed.emit(prefs)

    @property
    def status(self) -> ConnectionStatus:
        return self._status

    def set_status(self, status: ConnectionStatus) -> None:
        self._status = status
        self.status_changed.emit(status)

    @property
    def license(self) -> LicenseInfo:
        return self._license

    def set_license(self, info: LicenseInfo) -> None:
        self._license = info
        self.license_changed.emit(info)

    @property
    def locations(self) -> list[Location]:
        return self._locations

    def set_locations(self, locations: list[Location]) -> None:
        self._locations = locations
        self.locations_changed.emit(locations)

    def find_location(self, *, iso: str | None = None, city: str | None = None) -> Location | None:
        for loc in self._locations:
            if iso and loc.iso.upper() == iso.upper():
                return loc
            if city and loc.city.upper() == city.upper():
                return loc
        return None

    @property
    def config(self) -> VpnConfig:
        return self._config

    def set_config(self, config: VpnConfig) -> None:
        self._config = config
        self.config_changed.emit(config)

    @property
    def exclusions(self) -> ExclusionsState:
        return self._exclusions

    def set_exclusions(self, exclusions: ExclusionsState) -> None:
        self._exclusions = exclusions
        self.exclusions_changed.emit(exclusions)

    @property
    def update_info(self) -> UpdateInfo:
        return self._update

    def set_update_info(self, info: UpdateInfo) -> None:
        self._update = info
        self.update_changed.emit(info)

    @property
    def busy(self) -> bool:
        return self._busy

    def set_busy(self, busy: bool) -> None:
        if self._busy != busy:
            self._busy = busy
            self.busy_changed.emit(busy)

    def toggle_favorite(self, iso: str) -> None:
        favs = list(self._prefs.favorite_locations)
        if iso in favs:
            favs.remove(iso)
        else:
            favs.append(iso)
        self._prefs.favorite_locations = favs
        self.prefs_changed.emit(self._prefs)
