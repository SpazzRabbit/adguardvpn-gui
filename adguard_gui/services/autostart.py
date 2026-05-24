"""Управление автозапуском приложения через XDG Autostart (.desktop).

На Linux Desktop Environment-ы (GNOME, KDE, XFCE, Cinnamon и т.д.) подхватывают
.desktop-файлы из ``~/.config/autostart`` при старте сессии. Это самый
переносимый способ автостарта без правок systemd-user или ~/.profile.
"""
from __future__ import annotations

import os
import shlex
import sys
from pathlib import Path


_AUTOSTART_DIR = Path.home() / ".config" / "autostart"
_DESKTOP_FILENAME = "adguard-gui.desktop"


def _entry_path() -> Path:
    return _AUTOSTART_DIR / _DESKTOP_FILENAME


def _launch_command() -> str:
    """Команда, которая запустит этот же экземпляр приложения.

    Если глобальный launcher ``adguard-gui`` доступен в PATH (например, после
    установки .deb/.rpm), используем его. Иначе fallback — запуск через
    текущий Python-интерпретатор и ``main.py``.
    """
    import shutil
    installed = shutil.which("adguard-gui")
    if installed:
        return f"{shlex.quote(installed)} --minimized"
    main_py = Path(__file__).resolve().parents[2] / "main.py"
    parts = [sys.executable, str(main_py), "--minimized"]
    return " ".join(shlex.quote(p) for p in parts)


def is_enabled() -> bool:
    return _entry_path().exists()


def enable() -> None:
    _AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
    content = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=AdGuard VPN\n"
        "Comment=AdGuard VPN desktop client\n"
        f"Exec={_launch_command()}\n"
        "Icon=adguard-gui\n"
        "Terminal=false\n"
        "X-GNOME-Autostart-enabled=true\n"
        "Categories=Network;\n"
    )
    _entry_path().write_text(content, encoding="utf-8")
    try:
        os.chmod(_entry_path(), 0o644)
    except OSError:
        pass


def disable() -> None:
    path = _entry_path()
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass


def sync(want_enabled: bool) -> None:
    """Привести состояние autostart к желаемому."""
    if want_enabled and not is_enabled():
        enable()
    elif not want_enabled and is_enabled():
        disable()
