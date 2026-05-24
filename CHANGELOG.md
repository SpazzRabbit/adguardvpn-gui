# Changelog

## v0.2.0 — first public release (May 24, 2026)

The first version. It already does pretty much everything you'd expect from
a desktop VPN client: connect, switch locations, manage exclusions, kill
switch, autostart, system tray, six languages. Below are the parts worth
calling out.

### Connect

The big round button on Home is the whole story: green when the tunnel is
up, grey when it's off, amber while it's coming up. Hover it while
connected and it turns red — that's the "click me to disconnect" hint.

The duration counter is read from the real tun-interface uptime, so if
the CLI was connected before you opened the app, you'll see the correct
time straight away — not "0s, just started".

### Locations

Search by country, city or ISO code, sort by ping, mark favourites. The
active location gets a green "active" badge and a red **Disconnect**
button. Whatever row you're connecting to gets an amber pill with a
little spinner — the action lives in the row, no banner above the list.

There's also a **Fastest** button at the top if you don't care which
server you land on.

### Settings

Everything `adguardvpn-cli config set-*` can do, but with toggles and
dropdowns: TUN/SOCKS mode, protocol, DNS (with a few sensible presets),
post-quantum, SOCKS auth, update channel, telemetry, bound interface, and
so on.

Plus a handful of GUI-only options — language, refresh interval, "close
to tray", "start minimised".

### Safety & Startup

- **Kill switch** turns on the CLI's `--boot` flag, which makes the
  daemon reconnect forever if the tunnel ever drops. No iptables hackery,
  no extra sudo.
- **Autostart** drops a standard `.desktop` entry into
  `~/.config/autostart`. Works on GNOME, KDE, XFCE, Cinnamon.
- **Auto-connect on launch**: *Off* / *Last location* / *Fastest*.

### Languages

English, Русский, Deutsch, Español, Français, 中文. The first launch
picks the language from `QLocale.system()` (with `$LANG` and friends as a
fallback), so most people don't have to touch the setting. Switching the
language afterwards is live — no restart.

### Updates

The app pings `check-update` 5 s after launch and then every 6 h. When a
new CLI version is out, a green banner shows up on Home with a one-click
**Update now** button. **Later** hides it for that specific version. The
*About* page picks up the new version number automatically when the
update finishes.

### Packaging

Native recipes for every Linux family worth mentioning, plus the three
"universal" formats:

- **.deb** — Debian, Ubuntu, Mint, Pop!_OS, Elementary
- **.rpm** — Fedora, RHEL, CentOS Stream, AlmaLinux, Rocky, openSUSE
- **PKGBUILD** — Arch, Manjaro, EndeavourOS
- **APKBUILD** — Alpine
- **template** — Void Linux (`xbps-src`)
- **ebuild** — Gentoo
- **`default.nix` / `flake.nix`** — NixOS / Nix
- **Flatpak**, **Snap**, **AppImage** for "any distro" installs

One top-level `Makefile` builds them all: `make deb`, `make rpm`,
`make arch`, `make flatpak`, `make snap`, `make appimage`, …

### Things worth a separate mention

- The `.deb` installs almost instantly now. The first cut depended on a
  non-existent `adguardvpn-cli` apt package and a handful of bogus PySide
  alternatives, which sent apt off resolving phantom packages for half a
  minute. Cleaned up — installation is just unpacking ~130 KB plus the
  Qt dependencies you probably already have.
- Pending-connection feedback is now a smooth segmented spinner, not the
  three rotating dots the prototype shipped with.
- Single-instance lock (`QLockFile`) — a second launch raises the
  existing window from the tray instead of fighting it for the CLI
  socket.
- Login password goes to the CLI through stdin, never through argv.

### House-keeping

- MIT licence.
- English README with screenshots and an installation matrix for every
  package format above.
- GitHub Actions for "build on PR" and "publish on tag".
- Donation addresses in the README if you'd like to chip in — this isn't
  paid software, and it isn't an AdGuard product either; it's an
  unofficial frontend that talks to the official CLI.
