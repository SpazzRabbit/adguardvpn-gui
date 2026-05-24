Name:           adguard-gui
Version:        0.2.0
Release:        1%{?dist}
Summary:        AdGuard VPN desktop client (GUI)

License:        MIT
URL:            https://github.com/AdguardTeam
BuildArch:      noarch

Requires:       python3 >= 3.10
Requires:       python3-pyside6
Requires:       adguardvpn-cli

%description
Modern Qt-based GUI on top of adguardvpn-cli with location list, kill-switch,
autostart and multi-language support.

%install
mkdir -p %{buildroot}/usr/share/adguard-gui
cp -r adguard_gui %{buildroot}/usr/share/adguard-gui/
install -Dm755 packaging/adguard-gui %{buildroot}/usr/bin/adguard-gui
install -Dm644 packaging/adguard-gui.desktop %{buildroot}/usr/share/applications/adguard-gui.desktop
for size in 16 22 24 32 48 64 96 128 192 256 512; do
    install -Dm644 assets/icons/hicolor/${size}x${size}/apps/adguard-gui.png \
        %{buildroot}/usr/share/icons/hicolor/${size}x${size}/apps/adguard-gui.png
done
install -Dm644 assets/icons/adguard-gui.svg \
    %{buildroot}/usr/share/icons/hicolor/scalable/apps/adguard-gui.svg

%files
/usr/share/adguard-gui/
/usr/bin/adguard-gui
/usr/share/applications/adguard-gui.desktop
/usr/share/icons/hicolor/*/apps/adguard-gui.*

%post
gtk-update-icon-cache -q /usr/share/icons/hicolor &>/dev/null || :
update-desktop-database -q /usr/share/applications &>/dev/null || :

%postun
gtk-update-icon-cache -q /usr/share/icons/hicolor &>/dev/null || :
update-desktop-database -q /usr/share/applications &>/dev/null || :

%changelog
* Sun May 24 2026 AdGuard VPN GUI <noreply@example.com> - 0.2.0-1
- Initial RPM packaging.
