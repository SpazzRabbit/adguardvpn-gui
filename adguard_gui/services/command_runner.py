from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from adguard_gui.adapters.cli_adapter import CliAdapter
from adguard_gui.models.state import AppState
from adguard_gui.models.types import (
    CliResult,
    ConnectionStatus,
    ExclusionsState,
    LicenseInfo,
    Location,
    VpnConfig,
)
from adguard_gui.parsers.config_show import parse_config
from adguard_gui.parsers.exclusions import parse_exclusion_mode, parse_exclusions
from adguard_gui.parsers.license import parse_license
from adguard_gui.parsers.locations import parse_locations
from adguard_gui.parsers.status import parse_status
from adguard_gui.parsers.update_check import parse_check_update, parse_cli_version


class _Worker(QRunnable):
    def __init__(self, fn: Callable[[], None]) -> None:
        super().__init__()
        self.fn = fn
        self.setAutoDelete(True)

    def run(self) -> None:
        try:
            self.fn()
        except Exception:
            pass


class CommandRunner(QObject):
    operation_started = Signal(str)
    operation_finished = Signal(str, bool, str)
    raw_result = Signal(str, object)

    status_ready = Signal(ConnectionStatus)
    license_ready = Signal(LicenseInfo)
    locations_ready = Signal(list)
    config_ready = Signal(VpnConfig)
    exclusions_ready = Signal(ExclusionsState)

    def __init__(self, state: AppState, adapter: CliAdapter) -> None:
        super().__init__()
        self.state = state
        self.adapter = adapter
        self.pool = QThreadPool.globalInstance()
        self.pool.setMaxThreadCount(4)

    def _submit(self, op: str, fn: Callable[[], CliResult], on_result: Callable[[CliResult], None]) -> None:
        self.state.set_busy(True)
        self.operation_started.emit(op)

        def task() -> None:
            try:
                result = fn()
                ok = result.ok
                message = result.stderr.strip() or result.stdout.strip()
                self.raw_result.emit(op, result)
                try:
                    on_result(result)
                except Exception as e:
                    ok = False
                    message = f"parse error: {e}"
                self.operation_finished.emit(op, ok, message[:300])
            finally:
                self.state.set_busy(False)

        self.pool.start(_Worker(task))

    def status(self) -> None:
        def handle(r: CliResult) -> None:
            st = parse_status(r.stdout, r.stderr, r.exit_code)
            if st.location_city and self.state.locations:
                loc = self.state.find_location(city=st.location_city)
                if loc:
                    st.location_iso = loc.iso
                    st.location_city = loc.city
            self.status_ready.emit(st)
            self.state.set_status(st)

        self._submit("status", self.adapter.status, handle)

    def license(self) -> None:
        def handle(r: CliResult) -> None:
            info = parse_license(r.stdout, r.stderr, r.exit_code)
            self.license_ready.emit(info)
            self.state.set_license(info)

        self._submit("license", self.adapter.license, handle)

    def list_locations(self) -> None:
        def handle(r: CliResult) -> None:
            locs: list[Location] = parse_locations(r.stdout) if r.ok else []
            if locs:
                self.locations_ready.emit(locs)
                self.state.set_locations(locs)

        self._submit("list-locations", self.adapter.list_locations, handle)

    def config_show(self) -> None:
        def handle(r: CliResult) -> None:
            cfg = parse_config(r.stdout)
            self.config_ready.emit(cfg)
            self.state.set_config(cfg)

        self._submit("config-show", self.adapter.config_show, handle)

    def connect(self, location: str | None = None, fastest: bool = False) -> None:
        label = "connect (fastest)" if fastest else (f"connect → {location}" if location else "connect")
        # Optimistically mark state as connecting so UI reacts instantly.
        current = self.state.status
        self.state.set_status(ConnectionStatus(state="connecting", raw=current.raw))
        self._submit(label, lambda: self.adapter.connect(location=location, fastest=fastest), lambda r: None)

    def disconnect(self) -> None:
        current = self.state.status
        self.state.set_status(ConnectionStatus(state="disconnecting", raw=current.raw))
        self._submit("disconnect", self.adapter.disconnect, lambda r: None)

    def config_set(self, key: str, *values: str) -> None:
        op = f"config {key} {' '.join(values)}".strip()
        self._submit(op, lambda: self.adapter.config_set(key, *values), lambda r: None)

    def exclusions_load(self) -> None:
        def handle_show(mode: str) -> Callable[[CliResult], None]:
            def inner(r: CliResult) -> None:
                domains = parse_exclusions(r.stdout) if r.ok else []
                state = ExclusionsState(
                    mode=self.state.exclusions.mode,
                    general=self.state.exclusions.general,
                    selective=self.state.exclusions.selective,
                )
                if mode == "general":
                    state.general = domains
                else:
                    state.selective = domains
                self.exclusions_ready.emit(state)
                self.state.set_exclusions(state)
            return inner

        def handle_mode(r: CliResult) -> None:
            mode = parse_exclusion_mode(r.stdout)
            state = ExclusionsState(
                mode=mode,
                general=self.state.exclusions.general,
                selective=self.state.exclusions.selective,
            )
            self.state.set_exclusions(state)
            self.exclusions_ready.emit(state)
            # then load both lists
            self._submit("exclusions-show-general", lambda: self.adapter.exclusions_show("general"), handle_show("general"))
            self._submit("exclusions-show-selective", lambda: self.adapter.exclusions_show("selective"), handle_show("selective"))

        self._submit("exclusions-mode", self.adapter.exclusions_mode_get, handle_mode)

    def exclusions_set_mode(self, mode: str) -> None:
        self._submit(f"exclusions mode → {mode}", lambda: self.adapter.exclusions_mode_set(mode), lambda r: None)

    def exclusions_add(self, mode: str, domains: list[str]) -> None:
        self._submit(f"exclusions add ({mode})", lambda: self.adapter.exclusions_add(mode, domains), lambda r: None)

    def exclusions_remove(self, mode: str, domains: list[str]) -> None:
        self._submit(f"exclusions remove ({mode})", lambda: self.adapter.exclusions_remove(mode, domains), lambda r: None)

    def exclusions_clear(self, mode: str) -> None:
        self._submit(f"exclusions clear ({mode})", lambda: self.adapter.exclusions_clear(mode), lambda r: None)

    def login(self, email: str, password: str) -> None:
        self._submit("login", lambda: self.adapter.login(email, password), lambda r: None)

    def logout(self) -> None:
        self._submit("logout", self.adapter.logout, lambda r: None)

    def check_update(self) -> None:
        def on_done(r):
            # Текущая версия — отдельным subprocess'ом, чтобы Update-карточка
            # могла показать «v1.7.12 → v1.7.18».
            current = parse_cli_version(self.adapter.version().stdout)
            info = parse_check_update(r.stdout, current=current)
            self.state.set_update_info(info)
        self._submit("check-update", self.adapter.check_update, on_done)

    def update(self) -> None:
        # `update` тянет тяжёлый bash-скрипт от AdGuard — таймаут увеличиваем.
        def on_done(r):
            # После установки обновим версию и снимем «available».
            current = parse_cli_version(self.adapter.version().stdout)
            self.state.set_update_info(parse_check_update("", current=current))
        self._submit("update", self.adapter.update, on_done)

    def export_logs(self, path: str) -> None:
        self._submit(f"export-logs → {path}", lambda: self.adapter.export_logs(path), lambda r: None)
