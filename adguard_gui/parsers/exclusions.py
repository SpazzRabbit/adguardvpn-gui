from __future__ import annotations

import re

from adguard_gui.parsers.ansi import strip_ansi

MODE_RE = re.compile(r"exclusion mode is\s+(\w+)", re.IGNORECASE)
HEADER_RE = re.compile(r"Exclusions for\s+(\w+)\s+mode", re.IGNORECASE)


def parse_exclusion_mode(stdout: str) -> str:
    text = strip_ansi(stdout)
    m = MODE_RE.search(text)
    if m:
        return m.group(1).lower()
    return "general"


def parse_exclusions(stdout: str) -> list[str]:
    text = strip_ansi(stdout)
    domains: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if HEADER_RE.search(line):
            continue
        if line.lower().startswith("no exclusions"):
            return []
        domains.append(line)
    return domains
