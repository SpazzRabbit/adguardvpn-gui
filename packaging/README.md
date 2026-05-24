# Building distribution packages

All build entry points are defined in the top-level [`Makefile`](../Makefile).
Per-distribution recipes live in this directory.

Run `make help` for the short list.

```
icons | install | uninstall
deb | rpm | arch | alpine | void | gentoo | nix | flatpak | snap | appimage
```

## Native packages

### Debian family (`apt`)

Distributions: Debian, Ubuntu, Linux Mint, Pop!_OS, Elementary, Kali, MX Linux…

```bash
make deb
sudo apt install ./build/adguard-gui_0.2.0_all.deb
```

Inputs: `packaging/debian/control`, `postinst`, `postrm`.
Tools required: `dpkg-deb`, `rsync`.

### Red Hat family (`dnf` / `yum` / `zypper`)

Distributions: Fedora, RHEL, CentOS Stream, AlmaLinux, Rocky, openSUSE.

```bash
make rpm
sudo dnf  install ./build/rpm/RPMS/noarch/*.rpm   # Fedora / RHEL / Rocky
sudo zypper install ./build/rpm/RPMS/noarch/*.rpm  # openSUSE
```

Inputs: `packaging/rpm.spec`. Tools required: `rpmbuild`.

### Arch family (`pacman` / `makepkg`)

Distributions: Arch Linux, Manjaro, EndeavourOS, Garuda.

```bash
make arch
sudo pacman -U build/adguard-gui-0.2.0-1-any.pkg.tar.zst
```

Inputs: `packaging/PKGBUILD`. Tools required: `makepkg`, `fakeroot`.

### Alpine (`apk` / `abuild`)

```bash
make alpine
```

Inputs: `packaging/alpine/APKBUILD`. Tools required: `abuild`.

### Void Linux (`xbps`)

```bash
make void
# follow the printed instructions: drop packaging/void/template into
# srcpkgs/adguard-gui/ inside your void-packages checkout and run
#   ./xbps-src pkg adguard-gui
```

Inputs: `packaging/void/template`. Tools required: `xbps-src`.

### Gentoo (`emerge` / ebuild)

```bash
make gentoo
# copy packaging/gentoo/adguard-gui-0.2.0.ebuild into your overlay
# under net-vpn/adguard-gui/ and run:
sudo ebuild adguard-gui-0.2.0.ebuild manifest
sudo emerge -av adguard-gui
```

Inputs: `packaging/gentoo/adguard-gui-0.2.0.ebuild`.

### NixOS / Nix

```bash
make nix
# or with a flake-aware nix:
nix build ./packaging/nix#default
./packaging/nix/result/bin/adguard-gui
```

Inputs: `packaging/nix/default.nix`, `packaging/nix/flake.nix`. Tools
required: `nix` (>=2.18 for flakes).

## Universal packages

### Flatpak

```bash
make flatpak
flatpak install --user ./build/adguard-gui-0.2.0.flatpak
```

The Flatpak runs sandboxed with `org.kde.Platform//6.7` and dials out to
`adguardvpn-cli` on the host through `--filesystem=host-os:ro` +
`--talk-name=org.freedesktop.Flatpak`. The CLI must already be installed
on the host system.

Inputs: `packaging/flatpak/com.adguard.VpnGui.yaml`. Tools required:
`flatpak-builder`.

### Snap

```bash
make snap
sudo snap install --dangerous ./build/adguard-gui_0.2.0_amd64.snap
```

Inputs: `packaging/snap/snapcraft.yaml`. Tools required: `snapcraft`
(install with `sudo snap install snapcraft --classic`).

### AppImage

```bash
make appimage
./build/adguard-gui-0.2.0-x86_64.AppImage
```

The script in `packaging/appimage/build.sh` automatically downloads
`linuxdeploy` and `linuxdeploy-plugin-python`, runs `make install` into an
`AppDir`, and packs the result. Tools required: `bash`, `curl`,
`fakeroot`.

## Local install without a package manager

```bash
sudo make install                    # → /usr
sudo make install PREFIX=/usr/local  # custom prefix
```

`make uninstall` reverses it.

## Icons

`make icons` regenerates the hicolor PNG set under
`assets/icons/hicolor/<size>x<size>/apps/` from the master SVG at
`assets/icons/adguard-gui.svg`. No external converter is needed —
the script uses `QSvgRenderer`.
