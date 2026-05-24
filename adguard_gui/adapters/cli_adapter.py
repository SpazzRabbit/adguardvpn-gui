from __future__ import annotations

import os
import subprocess
import time
from typing import Sequence

from adguard_gui.models.types import CliResult, GuiPrefs

LONG_TIMEOUT = 60


class CliAdapter:
    def __init__(self, prefs: GuiPrefs) -> None:
        self.prefs = prefs

    def set_prefs(self, prefs: GuiPrefs) -> None:
        self.prefs = prefs

    def _env(self) -> dict[str, str]:
        env = dict(os.environ)
        env["LANG"] = "C.UTF-8"
        env["LC_ALL"] = "C.UTF-8"
        return env

    def _run(self, args: Sequence[str], *, timeout: int | None = None, stdin: str | None = None) -> CliResult:
        cmd = [self.prefs.binary_path, *args]
        start = time.monotonic()
        try:
            proc = subprocess.run(
                cmd,
                input=stdin,
                capture_output=True,
                text=True,
                timeout=timeout or self.prefs.timeout_sec,
                check=False,
                env=self._env(),
            )
            duration_ms = int((time.monotonic() - start) * 1000)
            return CliResult(
                stdout=proc.stdout or "",
                stderr=proc.stderr or "",
                exit_code=proc.returncode,
                duration_ms=duration_ms,
                command=cmd,
            )
        except subprocess.TimeoutExpired as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return CliResult(
                stdout=e.stdout or "",
                stderr=(e.stderr or "") + f"\nTimeout after {timeout or self.prefs.timeout_sec}s",
                exit_code=124,
                duration_ms=duration_ms,
                command=cmd,
            )
        except FileNotFoundError:
            duration_ms = int((time.monotonic() - start) * 1000)
            return CliResult(
                stdout="",
                stderr=f"binary not found: {self.prefs.binary_path}",
                exit_code=127,
                duration_ms=duration_ms,
                command=cmd,
            )

    def status(self) -> CliResult:
        return self._run(["status"])

    def connect(self, location: str | None = None, fastest: bool = False) -> CliResult:
        args = ["connect", "-y"]
        if fastest:
            args.append("-f")
        elif location:
            args.extend(["-l", location])
        if self.prefs.kill_switch:
            # --boot заставляет CLI бесконечно переподключаться при разрыве —
            # это и есть наш «kill switch» в терминах AdGuard VPN.
            args.append("--boot")
        return self._run(args, timeout=LONG_TIMEOUT)

    def disconnect(self) -> CliResult:
        return self._run(["disconnect"], timeout=LONG_TIMEOUT)

    def license(self) -> CliResult:
        return self._run(["license"])

    def list_locations(self) -> CliResult:
        return self._run(["list-locations"], timeout=LONG_TIMEOUT)

    def config_show(self) -> CliResult:
        return self._run(["config", "show"])

    def config_set(self, key: str, *values: str) -> CliResult:
        args = ["config", key, *values]
        return self._run(args)

    def exclusions_mode_get(self) -> CliResult:
        return self._run(["site-exclusions", "mode"])

    def exclusions_mode_set(self, mode: str) -> CliResult:
        return self._run(["site-exclusions", "mode", mode])

    def exclusions_show(self, mode: str) -> CliResult:
        return self._run(["site-exclusions", "show", "--for-mode", mode])

    def exclusions_add(self, mode: str, domains: list[str]) -> CliResult:
        return self._run(["site-exclusions", "add", "--for-mode", mode, *domains])

    def exclusions_remove(self, mode: str, domains: list[str]) -> CliResult:
        return self._run(["site-exclusions", "remove", "--for-mode", mode, *domains])

    def exclusions_clear(self, mode: str) -> CliResult:
        return self._run(["site-exclusions", "clear", "--for-mode", mode])

    def login(self, email: str, password: str) -> CliResult:
        return self._run(["login"], timeout=LONG_TIMEOUT, stdin=f"{email}\n{password}\n")

    def logout(self) -> CliResult:
        return self._run(["logout"])

    def check_update(self) -> CliResult:
        return self._run(["check-update"], timeout=LONG_TIMEOUT)

    def update(self) -> CliResult:
        # CLI скачивает свой установочный скрипт — даём минуты на сеть.
        return self._run(["update", "-y"], timeout=300)

    def export_logs(self, output_path: str) -> CliResult:
        return self._run(["export-logs", "-o", output_path, "-f"], timeout=LONG_TIMEOUT)

    def version(self) -> CliResult:
        return self._run(["--version"])
