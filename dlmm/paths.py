# -*- coding: utf-8 -*-
"""Пути к ресурсам приложения (совместимость с PyInstaller onedir/onefile)."""
from __future__ import annotations

import sys
from pathlib import Path


def app_root() -> Path:
    """Каталог исходников проекта или распакованных ресурсов PyInstaller."""
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", None)
        if base:
            return Path(base)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource(*parts: str) -> Path:
    """Путь к файлу ресурса относительно корня приложения."""
    return app_root().joinpath(*parts)


def asset(name: str) -> Path:
    """Путь к файлу в каталоге assets/ (иконки, логотипы)."""
    return resource("assets", name)
