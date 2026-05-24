from __future__ import annotations

import re

from adguard_gui.models.types import LicenseInfo
from adguard_gui.parsers.ansi import strip_ansi

EMAIL_RE = re.compile(r"Logged in as\s+(\S+@\S+)", re.IGNORECASE)
TIER_RE = re.compile(r"using the\s+([A-Za-z]+)\s+version", re.IGNORECASE)
DEVICES_RE = re.compile(r"Up to\s+(\d+)\s+devices", re.IGNORECASE)
VALID_RE = re.compile(r"valid until\s+(\d{4}-\d{2}-\d{2})", re.IGNORECASE)


def parse_license(stdout: str, stderr: str, exit_code: int) -> LicenseInfo:
    text = strip_ansi(stdout)
    raw = text.strip()
    info = LicenseInfo(raw=raw)

    if "not logged in" in text.lower() or "please log in" in text.lower() or exit_code != 0 and not text.strip():
        info.logged_in = False
        return info

    email = EMAIL_RE.search(text)
    tier = TIER_RE.search(text)
    devices = DEVICES_RE.search(text)
    valid = VALID_RE.search(text)

    if email:
        info.email = email.group(1)
        info.logged_in = True
    if tier:
        info.tier = tier.group(1).upper()
    if devices:
        try:
            info.device_limit = int(devices.group(1))
        except ValueError:
            pass
    if valid:
        info.valid_until = valid.group(1)

    return info
