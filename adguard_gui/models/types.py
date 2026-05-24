from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ConnectionState = Literal[
    "disconnected",
    "connecting",
    "connected",
    "disconnecting",
    "error",
    "unknown",
]


@dataclass(slots=True)
class CliResult:
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    command: list[str]

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


@dataclass(slots=True)
class ConnectionStatus:
    state: ConnectionState = "unknown"
    location_iso: str | None = None
    location_city: str | None = None
    mode: str | None = None
    interface: str | None = None
    raw: str = ""


@dataclass(slots=True, frozen=True)
class Location:
    iso: str
    country: str
    city: str
    ping_ms: int | None = None

    @property
    def key(self) -> str:
        return f"{self.iso}:{self.city}"


@dataclass(slots=True)
class LicenseInfo:
    logged_in: bool = False
    email: str | None = None
    tier: str | None = None
    device_limit: int | None = None
    valid_until: str | None = None
    raw: str = ""


@dataclass(slots=True)
class VpnConfig:
    mode: str = "tun"
    socks_port: int = 1080
    socks_host: str = "127.0.0.1"
    socks_username: str = ""
    dns_upstream: str = ""
    tun_routing_mode: str = "auto"
    change_system_dns: bool = True
    crash_reporting: bool = False
    telemetry: bool = False
    update_channel: str = "release"
    protocol: str = "auto"
    post_quantum: bool = True
    show_hints: bool = True
    debug_logging: bool = False
    show_notifications: bool = False
    bound_if: str = ""
    data_dir: str = ""
    raw: str = ""


@dataclass(slots=True)
class ExclusionsState:
    mode: str = "general"
    general: list[str] = field(default_factory=list)
    selective: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GuiPrefs:
    binary_path: str = "adguardvpn-cli"
    timeout_sec: int = 30
    refresh_interval_sec: int = 5
    minimize_to_tray: bool = True
    start_minimized: bool = False
    close_to_tray: bool = True
    favorite_locations: list[str] = field(default_factory=list)
    last_location: str | None = None
    lang: str = "ru"
    kill_switch: bool = False
    autostart: bool = False
    autoconnect_mode: str = "off"  # off | last | fastest
    dismissed_update: str | None = None  # latest CLI version юзер отклонил


@dataclass(slots=True)
class UpdateInfo:
    available: bool = False
    latest: str | None = None
    current: str | None = None
    raw: str = ""


@dataclass(slots=True)
class UiError:
    code: str
    message: str
