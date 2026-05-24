from __future__ import annotations

import re

from adguard_gui.models.types import ConnectionStatus
from adguard_gui.parsers.ansi import strip_ansi

CONNECTED_RE = re.compile(
    r"Connected to\s+(?P<city>[^\s]+(?:\s+\([^)]+\))?)\s+in\s+(?P<mode>TUN|SOCKS)\s+mode(?:,\s+running on\s+(?P<iface>\S+))?",
    re.IGNORECASE,
)
DISCONNECTED_MARKERS = (
    "vpn is disconnected",
    "vpn is not connected",
    "not connected",
    "no active connection",
)


def parse_status(stdout: str, stderr: str, exit_code: int) -> ConnectionStatus:
    text = strip_ansi(stdout) + "\n" + strip_ansi(stderr)
    clean = " ".join(text.split())
    raw = text.strip()

    if exit_code != 0 and not text.strip():
        return ConnectionStatus(state="error", raw=raw)

    match = CONNECTED_RE.search(clean)
    if match:
        return ConnectionStatus(
            state="connected",
            location_city=match.group("city"),
            mode=match.group("mode").upper(),
            interface=match.group("iface"),
            raw=raw,
        )

    low = clean.lower()
    if any(marker in low for marker in DISCONNECTED_MARKERS):
        return ConnectionStatus(state="disconnected", raw=raw)

    if "connecting" in low:
        return ConnectionStatus(state="connecting", raw=raw)

    return ConnectionStatus(state="disconnected" if exit_code == 0 else "unknown", raw=raw)
