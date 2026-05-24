from __future__ import annotations

import re

from adguard_gui.models.types import Location
from adguard_gui.parsers.ansi import strip_ansi

HEADER_TOKENS = {"ISO", "COUNTRY", "CITY", "PING", "ESTIMATE"}


def parse_locations(stdout: str) -> list[Location]:
    text = strip_ansi(stdout)
    out: list[Location] = []
    for line in text.splitlines():
        line = line.rstrip()
        if not line.strip():
            continue
        tokens = re.split(r"\s{2,}", line.strip())
        if not tokens:
            continue
        first = tokens[0].strip().upper()
        if first in HEADER_TOKENS:
            continue
        if len(first) != 2 or not first.isalpha():
            continue
        if len(tokens) < 3:
            continue
        iso = first
        country = tokens[1].strip()
        city = tokens[2].strip()
        ping: int | None = None
        if len(tokens) >= 4:
            digits = re.findall(r"\d+", tokens[3])
            if digits:
                try:
                    ping = int(digits[0])
                except ValueError:
                    ping = None
        out.append(Location(iso=iso, country=country, city=city, ping_ms=ping))
    return out
