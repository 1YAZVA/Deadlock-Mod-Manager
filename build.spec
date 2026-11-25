# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller: сборка DeadlockModManager (onedir, windowed).

Запуск:  pyinstaller --noconfirm --clean build.spec
Результат: dist/DeadlockModManager/DeadlockModManager.exe (+ каталог зависимостей)

onedir выбран вместо onefile: мгновенный старт и меньше проблем с антивирусами;
каталог dist целиком упаковывается в Setup_DLMM.exe скриптом scripts/installer.iss.
"""
from pathlib import Path

ASSETS_DIR = str(Path("assets"))

a = Analysis(
    ["run.py"],
    pathex=["."],
    binaries=[],
    datas=[(ASSETS_DIR, "assets")],
    hiddenimports=["psutil"],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="DeadlockModManager",
    debug=False,
    strip=False,
    upx=False,
    console=False,            # GUI-приложение: без консольного окна
    icon="assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="DeadlockModManager",
)
