# -*- coding: utf-8 -*-
"""Установка и управление модами (.vpk), режим Vanilla.

Механика:
  * Каталог модов:  <игра>/game/citadel/addons/*.vpk
  * Отключение:     переименование файла  <имя>.vpk -> <имя>.vpk.off
  * Vanilla:        переименование всей папки addons -> addons_vanilla_backup
                    (быстро и безопасно; после выхода из игры папка возвращается)

Метаданные установленных модов (id на GameBanana, автор и т.д.) хранятся в
installed.json рядом с config.json — благодаря этому статус «установлен»
виден в каталоге даже после перезапуска.
"""
from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from dlmm.config import ADDONS_SUBPATH, installed_db_path

VANILLA_BACKUP_NAME = "addons_vanilla_backup"
DISABLED_SUFFIX = ".off"


class ModError(RuntimeError):
    """Ошибка работы с модами (путь не задан, файл занят и т.п.)."""


@dataclass
class InstalledMod:
    file_name: str              # каноническое имя: что-то.vpk (без .off)
    path: Path                  # фактический путь (активный или отключённый)
    size: int
    enabled: bool
    mod_id: int | None = None
    mod_name: str = ""
    author: str = ""
    installed_at: str = ""
    file_id: int | None = None


class ModManager:
    """Все операции с .vpk-модами игры."""

    def __init__(self, settings) -> None:
        self._settings = settings

    # ------------------------------------------------------------------ пути
    @property
    def game_path(self) -> Path | None:
        return Path(self._settings.game_path) if self._settings.game_path else None

    @property
    def addons_dir(self) -> Path | None:
        game = self.game_path
        return game / ADDONS_SUBPATH if game else None

    def ensure_addons_dir(self) -> Path:
        addons = self.addons_dir
        if addons is None:
            raise ModError("Путь к игре не задан (см. страницу «Настройки»)")
        if not self.game_path.exists():
            raise ModError(f"Каталог игры не найден: {self.game_path}")
        if not addons.exists():
            try:
                addons.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise ModError(f"Не удалось создать {addons}: {exc}") from exc
        return addons

    # --------------------------------------------------------- база модов
    def _load_db(self) -> dict:
        try:
            data = json.loads(installed_db_path().read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _save_db(self, db: dict) -> None:
        try:
            installed_db_path().write_text(
                json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            pass

    def is_installed(self, mod_id: int | None) -> bool:
        if mod_id is None:
            return False
        return any(
            (meta or {}).get("mod_id") == mod_id for meta in self._load_db().values()
        )

    # ----------------------------------------------------------- операции
    def list_installed(self) -> list[InstalledMod]:
        """Сканирует addons/*.vpk и добавляет метаданные из installed.json."""
        db = self._load_db()
        result: list[InstalledMod] = []
        addons = self.addons_dir
        if addons is None or not addons.exists():
            return result

        files = sorted(addons.glob("*.vpk")) + sorted(addons.glob(f"*.vpk{DISABLED_SUFFIX}"))
        seen: set[str] = set()
        for path in files:
            name = path.name
            base = name[: -len(DISABLED_SUFFIX)] if name.endswith(DISABLED_SUFFIX) else name
            if base in seen:
                continue
            seen.add(base)
            meta = db.get(base) or {}
            result.append(
                InstalledMod(
                    file_name=base,
                    path=path,
                    size=path.stat().st_size if path.exists() else 0,
                    enabled=name == base,
                    mod_id=meta.get("mod_id"),
                    mod_name=meta.get("mod_name", ""),
                    author=meta.get("author", ""),
                    installed_at=meta.get("installed_at", ""),
                    file_id=meta.get("file_id"),
                )
            )
        return result

    def count_enabled(self) -> int:
        return sum(1 for mod in self.list_installed() if mod.enabled)

    def install_vpk(self, source: Path, meta: dict | None = None) -> InstalledMod:
        """Копирует .vpk в addons (при совпадении имён добавляет «(2)» и т.д.)."""
        addons = self.ensure_addons_dir()
        target = addons / source.name
        stem, suffix = source.stem, source.suffix  # суффикс всегда .vpk
        counter = 2
        while target.exists():
            target = addons / f"{stem} ({counter}){suffix}"
            counter += 1
        try:
            shutil.copy2(source, target)
        except OSError as exc:
            raise ModError(f"Не удалось скопировать мод: {exc}") from exc

        meta = dict(meta or {})
        meta.setdefault("mod_name", source.stem)
        meta.setdefault("installed_at", time.strftime("%Y-%m-%d %H:%M"))
        db = self._load_db()
        db[target.name] = meta
        self._save_db(db)
        return InstalledMod(
            file_name=target.name,
            path=target,
            size=target.stat().st_size,
            enabled=True,
            mod_id=meta.get("mod_id"),
            mod_name=meta.get("mod_name", ""),
            author=meta.get("author", ""),
            installed_at=meta.get("installed_at", ""),
            file_id=meta.get("file_id"),
        )

    def delete(self, file_name: str) -> None:
        addons = self.addons_dir
        if addons is None:
            raise ModError("Путь к игре не задан")
        for path in (addons / file_name, addons / f"{file_name}{DISABLED_SUFFIX}"):
            if path.exists():
                try:
                    path.unlink()
                except OSError as exc:
                    raise ModError(f"Файл занят — закройте игру: {exc}") from exc
        db = self._load_db()
        db.pop(file_name, None)
        self._save_db(db)

    def set_enabled(self, file_name: str, enabled: bool) -> None:
        """Включает/отключает мод переименованием .vpk <-> .vpk.off."""
        addons = self.addons_dir
        if addons is None:
            raise ModError("Путь к игре не задан")
        active = addons / file_name
        disabled = addons / f"{file_name}{DISABLED_SUFFIX}"
        src, dst = (disabled, active) if enabled else (active, disabled)
        if not src.exists():
            return
        if dst.exists():  # уже в нужном состоянии
            return
        try:
            src.rename(dst)
        except OSError as exc:
            raise ModError(f"Не удалось переименовать (закройте игру): {exc}") from exc

    # ------------------------------------------------------------- Vanilla
    @property
    def _backup_dir(self) -> Path | None:
        addons = self.addons_dir
        return addons.parent / VANILLA_BACKUP_NAME if addons else None

    def is_vanilla_active(self) -> bool:
        backup = self._backup_dir
        return bool(backup and backup.exists())

    def disable_for_vanilla(self) -> int:
        """Убирает моды на время Vanilla-сессии. Возвращает число перенесённых .vpk."""
        addons = self.ensure_addons_dir()
        backup = self._backup_dir
        assert backup is not None
        if backup.exists():
            return 0  # моды уже убраны
        vpk_files = list(addons.glob("*.vpk")) + list(addons.glob(f"*.vpk{DISABLED_SUFFIX}"))
        if not vpk_files:
            return 0  # модов нет — игра и так чистая
        try:
            addons.rename(backup)
        except OSError as exc:
            raise ModError(
                f"Не удалось переместить addons (закройте игру): {exc}"
            ) from exc
        return len(vpk_files)

    def restore_after_vanilla(self) -> bool:
        """Возвращает моды на место после Vanilla-сессии. True — были возвращены."""
        backup = self._backup_dir
        addons = self.addons_dir
        if not backup or not backup.exists():
            return False
        try:
            if not addons.exists():
                backup.rename(addons)
            else:
                # Игра успела пересоздать addons — аккуратно сливаем содержимое.
                for item in list(backup.iterdir()):
                    target = addons / item.name
                    if not target.exists():
                        shutil.move(str(item), str(target))
                if not any(backup.iterdir()):
                    backup.rmdir()
            return True
        except OSError as exc:
            raise ModError(f"Не удалось вернуть моды: {exc}") from exc
