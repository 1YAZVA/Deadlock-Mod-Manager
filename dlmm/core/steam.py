# -*- coding: utf-8 -*-
"""Определение Steam/Deadlock и запуск игры.

Пути:
  HKCU\\Software\\Valve\\Steam -> SteamPath
  <SteamPath>/steamapps/libraryfolders.vdf -> список библиотек
  <библиотека>/steamapps/common/Citadel    -> каталог игры
Моды кладутся в: <игра>/game/citadel/addons/
"""
from __future__ import annotations

import os
import re
import time
from pathlib import Path

from dlmm.config import DEFAULT_GAME_DIR_NAME, STEAM_APPID

_VDF_PATH_RE = re.compile(r'"path"\s+"([^"]+)"', re.IGNORECASE)


def is_windows() -> bool:
    return os.name == "nt"


def find_steam_path() -> Path | None:
    """SteamPath из реестра Windows (HKCU, затем HKLM)."""
    if not is_windows():
        return None
    try:
        import winreg  # noqa: PLC0415
    except ImportError:
        return None

    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        try:
            with winreg.OpenKey(hive, r"Software\Valve\Steam") as key:
                value, _ = winreg.QueryValueEx(key, "SteamPath")
                return Path(value.replace("/", "\\"))
        except OSError:
            continue
    return None


def get_library_folders(steam_path: Path) -> list[Path]:
    """Все библиотеки Steam из libraryfolders.vdf + сама папка Steam."""
    libraries: list[Path] = [steam_path]
    vdf = steam_path / "steamapps" / "libraryfolders.vdf"
    if not vdf.exists():
        vdf = steam_path / "steamapps" / "library.vdf"
    if vdf.exists():
        try:
            text = vdf.read_text(encoding="utf-8", errors="ignore")
            for raw in _VDF_PATH_RE.findall(text):
                path = Path(raw.replace("\\\\", "\\"))
                if path not in libraries:
                    libraries.append(path)
        except OSError:
            pass
    return [lib for lib in libraries if (lib / "steamapps").exists()]


def find_game_dir(game_dir_name: str = DEFAULT_GAME_DIR_NAME) -> Path | None:
    """Ищет каталог Deadlock во всех библиотеках Steam."""
    steam = find_steam_path()
    if steam is None:
        return None
    for lib in get_library_folders(steam):
        candidate = lib / "steamapps" / "common" / game_dir_name
        if candidate.exists():
            return candidate
    return None


def launch_game() -> None:
    """Запуск Deadlock через Steam: steam://rungameid/1422450."""
    url = f"steam://rungameid/{STEAM_APPID}"
    if is_windows():
        os.startfile(url)  # type: ignore[attr-defined]  # noqa: S606
    else:
        import webbrowser  # noqa: PLC0415

        webbrowser.open(url)


def is_game_running(process_name: str = "citadel.exe") -> bool:
    """Запущен ли процесс игры (psutil; если недоступен — False)."""
    try:
        import psutil  # noqa: PLC0415
    except ImportError:
        return False

    name = process_name.lower()
    for proc in psutil.process_iter(["name"]):
        try:
            if (proc.info.get("name") or "").lower() == name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):  # pragma: no cover
            continue
    return False


def wait_game_exit(
    process_name: str,
    timeout_s: int = 180,
    poll_s: float = 2.0,
) -> bool:
    """Ждёт завершения игровой сессии.

    Сначала до timeout_s ждём появления процесса игры (Steam мог ещё грузиться),
    затем ждём его исчезновения. True — игра стартовала и завершилась,
    False — процесс так и не появился за отведённое время.
    """
    deadline = time.monotonic() + max(30, timeout_s)
    seen = False
    while time.monotonic() < deadline:
        if is_game_running(process_name):
            seen = True
            break
        time.sleep(poll_s)
    if not seen:
        return False
    while is_game_running(process_name):
        time.sleep(poll_s)
    return True
