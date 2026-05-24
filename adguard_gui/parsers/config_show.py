from __future__ import annotations

from adguard_gui.models.types import VpnConfig
from adguard_gui.parsers.ansi import strip_ansi


def _to_bool(value: str) -> bool:
    low = value.strip().lower()
    if "(on)" in low or low.startswith("on") or low == "true" or low == "yes":
        return True
    if "default" in low and "(on)" in low:
        return True
    return False


def _strip_default(value: str) -> str:
    v = value.strip()
    if v.lower().startswith("default"):
        # "Default (auto)" -> "auto", "Default (provided by AdGuard VPN)" -> ""
        start = v.find("(")
        end = v.rfind(")")
        if start != -1 and end != -1:
            inner = v[start + 1 : end].strip()
            if "provided" in inner.lower():
                return ""
            return inner
        return ""
    return v


def parse_config(stdout: str) -> VpnConfig:
    text = strip_ansi(stdout)
    raw = text.strip()
    cfg = VpnConfig(raw=raw)
    for line in text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if "data directory" in key:
            cfg.data_dir = value
        elif key == "mode":
            cfg.mode = value.lower() or "tun"
        elif key == "socks port":
            try:
                cfg.socks_port = int(value)
            except ValueError:
                pass
        elif key == "socks host":
            cfg.socks_host = value
        elif key == "socks username":
            cfg.socks_username = value
        elif key == "dns upstream":
            cfg.dns_upstream = _strip_default(value)
        elif key == "tunnel routing mode":
            cfg.tun_routing_mode = value.lower() or "auto"
        elif key == "change system dns":
            cfg.change_system_dns = _to_bool(value)
        elif key == "crash reporting":
            cfg.crash_reporting = _to_bool(value)
        elif "anonymized usage" in key or key == "send anonymized usage data":
            cfg.telemetry = _to_bool(value)
        elif key == "update channel":
            cfg.update_channel = value.lower() or "release"
        elif key == "protocol":
            cfg.protocol = _strip_default(value).lower() or "auto"
        elif "post-quantum" in key:
            cfg.post_quantum = _to_bool(value)
        elif "show hints" in key:
            cfg.show_hints = _to_bool(value)
        elif "debug logging" in key:
            cfg.debug_logging = _to_bool(value)
        elif "show notifications" in key:
            cfg.show_notifications = _to_bool(value)
        elif "outbound interface" in key:
            cfg.bound_if = "" if "not set" in value.lower() else value
    return cfg
