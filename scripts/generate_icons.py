#!/usr/bin/env python3
"""Generate PNG icons from assets/icons/adguard-gui.svg.

Используется при сборке пакетов: ставит готовые PNG в hicolor-иерархию
``share/icons/hicolor/<size>x<size>/apps/adguard-gui.png``.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

SIZES = [16, 22, 24, 32, 48, 64, 96, 128, 192, 256, 512]


def main() -> int:
    # Offscreen, чтобы не требовать DISPLAY при сборке.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtCore import QByteArray, QSize, Qt
    from PySide6.QtGui import QPainter, QPixmap
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication

    root = Path(__file__).resolve().parents[1]
    svg = root / "assets" / "icons" / "adguard-gui.svg"
    if not svg.exists():
        print(f"ERR: {svg} not found", file=sys.stderr)
        return 1
    out_root = root / "assets" / "icons" / "hicolor"

    QApplication(sys.argv)  # нужен для QPainter/QPixmap
    data = QByteArray(svg.read_bytes())
    for size in SIZES:
        renderer = QSvgRenderer(data)
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        renderer.render(p)
        p.end()
        dest_dir = out_root / f"{size}x{size}" / "apps"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "adguard-gui.png"
        pix.save(str(dest), "PNG")
        print(f"  {size:4}x{size:<4}  →  {dest.relative_to(root)}")
    # scalable
    scalable = out_root / "scalable" / "apps"
    scalable.mkdir(parents=True, exist_ok=True)
    (scalable / "adguard-gui.svg").write_bytes(svg.read_bytes())
    print(f"  scalable    →  {scalable / 'adguard-gui.svg'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
