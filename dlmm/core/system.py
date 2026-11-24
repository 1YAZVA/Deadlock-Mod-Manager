# -*- coding: utf-8 -*-
"""Системная интеграция: автозапуск с Windows, URL-протокол, открытие папок/ссылок."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from dlmm.config import APP_ID

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
PROTO_ROOT_KEY = r"Software\Classes\deadlock-mod-manager"


def is_windows() -> bool:
    return sys.platform == "win32"


def _command_for_autostart() -> str:
    """Команда запуска приложения (для реестра)."""
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    script = Path(sys.argv[0]).resolve() if sys.argv and sys.argv[0] else Path("run.py")
    return f'"{sys.executable}" "{script}"'


def set_autostart(enabled: bool) -> None:
    """Включает/выключает автозапуск с Windows (HKCU — без прав администратора)."""
    if not is_windows():
        return
    import winreg  # noqa: PLC0415 — доступен только в Windows

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        if enabled:
            winreg.SetValueEx(key, APP_ID, 0, winreg.REG_SZ, _command_for_autostart())
        else:
            try:
                winreg.DeleteValue(key, APP_ID)
            except FileNotFoundError:
                pass


def set_protocol_handler(enabled: bool) -> None:
    """Регистрирует (или удаляет) URL-протокол deadlock-mod-manager://.

    После регистрации ссылки вида
      deadlock-mod-manager:https://gamebanana.com/mmdl/<file_id>,Mod,<mod_id>
    (кнопка «Mod installer» на GameBanana) открывают приложение и сразу
    ставят мод в один клик.
    """
    if not is_windows():
        return
    import winreg  # noqa: PLC0415

    if not enabled:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, r"Software\Classes", 0, winreg.KEY_SET_VALUE
            ) as key:
                _delete_tree(winreg, key, "deadlock-mod-manager")
        except OSError:
            pass
        return

    command = f'"{_exe_path()}" "%1"'
    with winreg.CreateKey(
        winreg.HKEY_CURRENT_USER, PROTO_ROOT_KEY
    ) as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, "URL:Deadlock Mod Manager")
        winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
    with winreg.CreateKey(
        winreg.HKEY_CURRENT_USER, PROTO_ROOT_KEY + r"\shell\open\command"
    ) as key:
        winreg.SetValueEx(key, None, 0, winreg.REG_SZ, command)


def _delete_tree(winreg, hive_key, subkey: str) -> None:
    """Рекурсивно удаляет ключ реестра (в winreg нет полноценной delete_tree)."""
    try:
        with winreg.OpenKey(hive_key, subkey, 0, winreg.KEY_ALL_ACCESS) as key:
            while True:
                try:
                    child = winreg.EnumKey(key, 0)
                except OSError:
                    break
                _delete_tree(winreg, key, child)
        winreg.DeleteKey(hive_key, subkey)
    except OSError:
        pass


def _exe_path() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    script = Path(sys.argv[0]).resolve() if sys.argv and sys.argv[0] else Path("run.py")
    return f"{sys.executable} {script}"


def open_in_explorer(path: str | Path) -> None:
    """Открывает папку в Проводнике."""
    if is_windows():
        os.startfile(str(path))  # type: ignore[attr-defined]  # noqa: S606
    else:
        subprocess.Popen(["xdg-open", str(path)])  # noqa: S603


def open_url(url: str) -> None:
    """Открывает ссылку в браузере по умолчанию."""
    if is_windows():
        os.startfile(url)  # type: ignore[attr-defined]  # noqa: S606
    else:
        subprocess.Popen(["xdg-open", url])  # noqa: S603
