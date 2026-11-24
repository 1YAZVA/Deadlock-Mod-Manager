# -*- coding: utf-8 -*-
"""Константы игры, настройки приложения и пути к данным (%APPDATA%)."""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

APP_NAME = "Deadlock Mod Manager"
APP_ID = "DeadlockModManager"

# --- Константы игры ---------------------------------------------------------
STEAM_APPID = 1422450            # Deadlock в Steam (steam://rungameid/1422450)
GAMEBANANA_GAME_ID = 20948       # раздел Deadlock на GameBanana (apiv11)
DEFAULT_GAME_DIR_NAME = "Citadel"            # steamapps/common/Citadel
DEFAULT_PROCESS_NAME = "citadel.exe"         # процесс игры для Vanilla-режима
ADDONS_SUBPATH = Path("game") / "citadel" / "addons"  # куда кладутся .vpk

CONFIG_FILENAME = "config.json"
INSTALLED_DB_FILENAME = "installed.json"
LOG_FILENAME = "dlmm.log"


def app_data_dir() -> Path:
    """Каталог данных приложения: %APPDATA%/DeadlockModManager (Windows)."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    d = base / APP_ID
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_path() -> Path:
    return app_data_dir() / CONFIG_FILENAME


def installed_db_path() -> Path:
    return app_data_dir() / INSTALLED_DB_FILENAME


def log_path() -> Path:
    return app_data_dir() / LOG_FILENAME


@dataclass
class Settings:
    """Настройки, сохраняемые в config.json."""

    # Пути и интеграция
    game_path: str = ""                          # каталог игры (steamapps/common/Citadel)
    game_process_name: str = DEFAULT_PROCESS_NAME
    api_base_url: str = "https://gamebanana.com/apiv11"
    download_mirror: str = ""                    # зеркало CDN (пусто = официальный)

    # Поведение
    minimize_to_tray: bool = True                # закрытие окна -> трей
    autostart: bool = False                      # автозапуск с Windows
    launch_after_install: bool = False           # запускать игру после установки мода
    vanilla_watch_timeout: int = 180             # сколько секунд ждать запуск игры (Vanilla)

    # Каталог
    per_page: int = 15                           # записей ленты GameBanana на страницу

    # Окно
    window_size: list[int] = field(default_factory=lambda: [1180, 760])

    @classmethod
    def load(cls) -> "Settings":
        s = cls()
        path = config_path()
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    for key, value in data.items():
                        if hasattr(s, key):
                            setattr(s, key, value)
            except (OSError, ValueError):
                pass  # битый конфиг -> значения по умолчанию
        return s

    def save(self) -> None:
        try:
            config_path().write_text(
                json.dumps(asdict(self), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass  # не даём настройкам уронить приложение
