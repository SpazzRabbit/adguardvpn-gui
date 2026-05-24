# Сборка пакетов AdGuard VPN GUI.
#
# Цели:
#   make icons    — пересобрать PNG-иконки из SVG
#   make install  — установить локально (под DESTDIR/PREFIX)
#   make uninstall— удалить локальную установку
#
# Пакеты:
#   make deb      — .deb (dpkg-deb)            Debian / Ubuntu / Mint / Pop!_OS
#   make rpm      — .rpm (rpmbuild)            Fedora / RHEL / CentOS / openSUSE
#   make arch     — meta для makepkg           Arch / Manjaro / EndeavourOS
#   make alpine   — meta для abuild            Alpine
#   make void     — meta для xbps-src          Void Linux
#   make gentoo   — ebuild                     Gentoo
#   make nix      — Nix derivation             NixOS
#   make flatpak  — собрать через flatpak-builder
#   make snap     — собрать через snapcraft
#   make appimage — собрать AppImage (linuxdeploy)
#
# Переменные:
#   VERSION=0.2.0   версия пакета
#   DESTDIR=        корень установки (для пакетной сборки)
#   PREFIX=/usr     префикс установки

VERSION ?= 0.2.0
DESTDIR ?=
PREFIX  ?= /usr
PY      ?= python3
SIZES   := 16 22 24 32 48 64 96 128 192 256 512

ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
BUILDDIR := $(ROOT)/build
DEBROOT  := $(BUILDDIR)/deb/adguard-gui_$(VERSION)
DEB      := $(BUILDDIR)/adguard-gui_$(VERSION)_all.deb

.PHONY: all icons install uninstall deb rpm arch alpine void gentoo nix flatpak snap appimage clean help

all: deb

help:
	@echo "make icons | install | uninstall"
	@echo "Packages: deb | rpm | arch | alpine | void | gentoo | nix | flatpak | snap | appimage"

icons:
	$(PY) scripts/generate_icons.py

install: icons
	# Python package — без __pycache__ и .pyc
	install -d "$(DESTDIR)$(PREFIX)/share/adguard-gui"
	rsync -a --delete \
		--exclude='__pycache__' --exclude='*.pyc' --exclude='*.pyo' \
		adguard_gui/ "$(DESTDIR)$(PREFIX)/share/adguard-gui/adguard_gui/"
	# Launcher
	install -Dm755 packaging/adguard-gui "$(DESTDIR)$(PREFIX)/bin/adguard-gui"
	# Desktop entry
	install -Dm644 packaging/adguard-gui.desktop \
		"$(DESTDIR)$(PREFIX)/share/applications/adguard-gui.desktop"
	# Icons
	@for s in $(SIZES); do \
		install -Dm644 "assets/icons/hicolor/$${s}x$${s}/apps/adguard-gui.png" \
			"$(DESTDIR)$(PREFIX)/share/icons/hicolor/$${s}x$${s}/apps/adguard-gui.png"; \
	done
	install -Dm644 assets/icons/adguard-gui.svg \
		"$(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/adguard-gui.svg"

uninstall:
	rm -rf "$(DESTDIR)$(PREFIX)/share/adguard-gui"
	rm -f  "$(DESTDIR)$(PREFIX)/bin/adguard-gui"
	rm -f  "$(DESTDIR)$(PREFIX)/share/applications/adguard-gui.desktop"
	@for s in $(SIZES); do \
		rm -f "$(DESTDIR)$(PREFIX)/share/icons/hicolor/$${s}x$${s}/apps/adguard-gui.png"; \
	done
	rm -f "$(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/adguard-gui.svg"

deb: icons
	rm -rf "$(DEBROOT)"
	$(MAKE) install DESTDIR="$(DEBROOT)" PREFIX=/usr
	install -d "$(DEBROOT)/DEBIAN"
	install -m644 packaging/debian/control "$(DEBROOT)/DEBIAN/control"
	install -m755 packaging/debian/postinst "$(DEBROOT)/DEBIAN/postinst"
	install -m755 packaging/debian/postrm "$(DEBROOT)/DEBIAN/postrm"
	# Подставить точную версию в control
	sed -i 's/^Version: .*/Version: $(VERSION)/' "$(DEBROOT)/DEBIAN/control"
	dpkg-deb --root-owner-group --build "$(DEBROOT)" "$(DEB)"
	@echo
	@echo "OK: $(DEB)"

rpm: icons
	@command -v rpmbuild >/dev/null || { echo "rpmbuild not found"; exit 1; }
	mkdir -p "$(BUILDDIR)/rpm/BUILD" "$(BUILDDIR)/rpm/RPMS" "$(BUILDDIR)/rpm/SOURCES" "$(BUILDDIR)/rpm/SPECS"
	tar -czf "$(BUILDDIR)/rpm/SOURCES/adguard-gui-$(VERSION).tar.gz" \
		--transform "s,^,adguard-gui-$(VERSION)/," \
		adguard_gui packaging assets scripts
	cp packaging/rpm.spec "$(BUILDDIR)/rpm/SPECS/adguard-gui.spec"
	rpmbuild --define "_topdir $(BUILDDIR)/rpm" \
	         --define "version $(VERSION)" \
	         -bb "$(BUILDDIR)/rpm/SPECS/adguard-gui.spec"
	@echo
	@echo "OK: $(BUILDDIR)/rpm/RPMS/noarch/"

arch:
	@command -v makepkg >/dev/null || { echo "makepkg not found (run on Arch / Manjaro)"; exit 1; }
	cd packaging && makepkg -f --noconfirm
	@mkdir -p "$(BUILDDIR)"
	@mv packaging/*.pkg.tar.* "$(BUILDDIR)/" 2>/dev/null || true
	@echo
	@echo "OK: $(BUILDDIR)/*.pkg.tar.*"

alpine:
	@command -v abuild >/dev/null || { echo "abuild not found (run on Alpine)"; exit 1; }
	cd packaging/alpine && abuild -r

void:
	@command -v xbps-src >/dev/null || { echo "xbps-src not found (run inside void-packages)"; exit 1; }
	@echo "Copy packaging/void/template into srcpkgs/adguard-gui/ inside your"
	@echo "void-packages checkout, then run: ./xbps-src pkg adguard-gui"

gentoo:
	@echo "Ebuild lives in packaging/gentoo/adguard-gui-$(VERSION).ebuild —"
	@echo "drop it into your overlay (net-vpn/adguard-gui/) and run:"
	@echo "  ebuild adguard-gui-$(VERSION).ebuild manifest"
	@echo "  emerge -av adguard-gui"

nix:
	@command -v nix >/dev/null || { echo "nix not found"; exit 1; }
	cd packaging/nix && nix build .#default
	@echo
	@echo "OK: packaging/nix/result/bin/adguard-gui"

flatpak:
	@command -v flatpak-builder >/dev/null || { echo "flatpak-builder not found"; exit 1; }
	mkdir -p "$(BUILDDIR)/flatpak"
	flatpak-builder --force-clean \
	    "$(BUILDDIR)/flatpak/build" \
	    packaging/flatpak/com.adguard.VpnGui.yaml \
	    --repo="$(BUILDDIR)/flatpak/repo"
	flatpak build-bundle "$(BUILDDIR)/flatpak/repo" \
	    "$(BUILDDIR)/adguard-gui-$(VERSION).flatpak" \
	    com.adguard.VpnGui
	@echo
	@echo "OK: $(BUILDDIR)/adguard-gui-$(VERSION).flatpak"

snap:
	@command -v snapcraft >/dev/null || { echo "snapcraft not found (sudo snap install snapcraft --classic)"; exit 1; }
	cd packaging/snap && snapcraft --use-lxd
	@mkdir -p "$(BUILDDIR)"
	@mv packaging/snap/*.snap "$(BUILDDIR)/" 2>/dev/null || true
	@echo
	@echo "OK: $(BUILDDIR)/*.snap"

appimage: icons
	VERSION=$(VERSION) bash packaging/appimage/build.sh

clean:
	rm -rf "$(BUILDDIR)"
