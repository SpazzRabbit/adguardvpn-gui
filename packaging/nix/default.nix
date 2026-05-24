{ lib
, stdenv
, python3
, python3Packages
, qt6
, makeWrapper
, copyDesktopItems
}:

stdenv.mkDerivation (finalAttrs: {
  pname = "adguard-gui";
  version = "0.2.0";

  src = ../..;

  nativeBuildInputs = [
    makeWrapper
    copyDesktopItems
    qt6.wrapQtAppsHook
  ];

  propagatedBuildInputs = [
    python3Packages.pyside6
  ];

  buildInputs = [
    qt6.qtbase
    qt6.qtsvg
  ];

  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall

    install -d $out/share/adguard-gui
    cp -r adguard_gui $out/share/adguard-gui/

    install -Dm755 packaging/adguard-gui $out/bin/adguard-gui
    install -Dm644 packaging/adguard-gui.desktop \
      $out/share/applications/adguard-gui.desktop

    for s in 16 22 24 32 48 64 96 128 192 256 512; do
      install -Dm644 "assets/icons/hicolor/''${s}x''${s}/apps/adguard-gui.png" \
        "$out/share/icons/hicolor/''${s}x''${s}/apps/adguard-gui.png"
    done
    install -Dm644 assets/icons/adguard-gui.svg \
      $out/share/icons/hicolor/scalable/apps/adguard-gui.svg

    wrapProgram $out/bin/adguard-gui \
      --prefix PYTHONPATH : "$out/share/adguard-gui" \
      --prefix PYTHONPATH : "${python3Packages.pyside6}/${python3.sitePackages}"

    runHook postInstall
  '';

  meta = with lib; {
    description = "Unofficial modern desktop GUI for adguardvpn-cli";
    homepage = "https://github.com/AdguardTeam/adguard-gui";
    license = licenses.mit;
    platforms = platforms.linux;
    mainProgram = "adguard-gui";
  };
})
