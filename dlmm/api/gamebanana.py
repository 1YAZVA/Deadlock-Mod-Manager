# -*- coding: utf-8 -*-
"""Клиент GameBanana API v11 для раздела Deadlock (Game ID 20948).

Используемые маршруты (проверены 2026-11):

  GET {api}/Game/20948/Subfeed?_isValidateDate=true&_csvSubfeedTypes=mod&_nPer=15&_nPage=N
      Лента записей игры. На страницу отдаётся до 15 записей (Mod и WiP),
      всего Deadlock-модов ~13 тыс. (_aMetadata._nRecordCount).

  GET {api}/Mod/{mod_id}/ProfilePage
      Профиль мода: _aFiles[] (id, имя, размер, _sDownloadUrl вида
      https://gamebanana.com/dl/{file_id}, md5), описания, превью.

  GET https://gamebanana.com/dl/{file_id}
      Скачивание файла (302 на CDN, requests следует редиректу автоматически).

  Бонус: _aModManagerIntegrations._sDownloadUrl содержит ссылку протокола
  deadlock-mod-manager:https://gamebanana.com/mmdl/{file_id},Mod,{mod_id} —
  GameBanana знает о нашем менеджере и даёт кнопку «установить в один клик»
  (протокол регистрируется установщиком, см. scripts/installer.iss).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import requests

from dlmm import __version__
from dlmm.config import GAMEBANANA_GAME_ID

_MMDL_RE = re.compile(
    r"deadlock-mod-manager:https?://gamebanana\.com/mmdl/(\d+)(?:,([^,]+),(\d+))?",
    re.IGNORECASE,
)


class GameBananaError(RuntimeError):
    """Ошибка API GameBanana (сеть, HTTP, формат ответа)."""


class DownloadCancelled(RuntimeError):
    """Загрузка отменена пользователем."""


@dataclass
class ModRecord:
    """Запись каталога (карточка мода)."""

    mod_id: int
    name: str
    model: str = "Mod"          # Mod / Wip / ...
    author: str = ""
    category: str = ""          # Skins, HUD, Gameplay ...
    subcategory: str = ""       # герой
    version: str = ""
    likes: int = 0
    views: int = 0
    date_added: int = 0
    date_modified: int = 0
    profile_url: str = ""
    preview_url: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)


@dataclass
class ModFile:
    """Файл мода из профиля."""

    file_id: int
    name: str
    size: int
    download_url: str
    downloads: int = 0
    md5: str = ""
    date_added: int = 0


def first_image_url(media: dict | None, prefer: str = "530") -> str:
    """Собирает URL превью из _aPreviewMedia._aImages[0]."""
    if not isinstance(media, dict):
        return ""
    images = media.get("_aImages") or []
    if not images:
        return ""
    image = images[0]
    base = image.get("_sBaseUrl") or ""
    for key in (f"_sFile{prefer}", "_sFile220", "_sFile"):
        file_name = image.get(key)
        if base and file_name:
            return f"{base}/{file_name}"
    return ""


def parse_mmdl_url(text: str) -> tuple[int, int | None] | None:
    """Разбирает ссылку протокола. Возвращает (file_id, mod_id | None)."""
    match = _MMDL_RE.search(text or "")
    if not match:
        return None
    file_id = int(match.group(1))
    mod_id = int(match.group(3)) if match.group(3) else None
    return file_id, mod_id


class GameBananaClient:
    """HTTP-клиент GameBanana (requests.Session + повторное использование)."""

    def __init__(
        self,
        base_url: str = "https://gamebanana.com/apiv11",
        mirror: str = "",
        game_id: int = GAMEBANANA_GAME_ID,
        timeout: float = 15.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.mirror = mirror.strip().rstrip("/")
        self.game_id = game_id
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": (
                    f"DeadlockModManager/{__version__} "
                    "(+https://github.com/1YAZVA/Deadlock-Mod-Manager)"
                ),
                "Accept": "application/json",
            }
        )

    # ------------------------------------------------------------ транспорт
    def _get_json(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        try:
            resp = self._session.get(url, params=params, timeout=self._timeout)
        except requests.RequestException as exc:
            raise GameBananaError(f"Сеть недоступна: {exc}") from exc
        if resp.status_code >= 400:
            raise GameBananaError(f"HTTP {resp.status_code}: {path}")
        try:
            data = resp.json()
        except ValueError as exc:
            raise GameBananaError("Некорректный JSON в ответе GameBanana") from exc
        if isinstance(data, dict) and data.get("_sErrorCode"):
            message = data.get("_sErrorMessage") or data["_sErrorCode"]
            raise GameBananaError(f"GameBanana: {message}")
        return data

    # -------------------------------------------------------------- каталог
    def get_feed_page(self, page: int = 1, per_page: int = 15) -> tuple[list[ModRecord], int]:
        """Страница ленты модов игры -> (записи Mod, всего записей)."""
        data = self._get_json(
            f"/Game/{self.game_id}/Subfeed",
            {
                "_isValidateDate": "true",
                "_csvSubfeedTypes": "mod",
                "_nPer": max(1, min(int(per_page), 15)),
                "_nPage": max(1, int(page)),
            },
        )
        meta = data.get("_aMetadata") or {}
        total = int(meta.get("_nRecordCount") or 0)
        records: list[ModRecord] = []
        for raw in data.get("_aRecords") or []:
            record = self._parse_record(raw)
            if record and record.model == "Mod":  # WiP и прочее не показываем
                records.append(record)
        return records, total

    def _parse_record(self, raw: dict) -> ModRecord | None:
        try:
            mod_id = int(raw.get("_idRow"))
        except (TypeError, ValueError):
            return None
        submitter = raw.get("_aSubmitter") or {}
        root_category = raw.get("_aRootCategory") or {}
        sub_category = raw.get("_aSubCategory") or {}
        return ModRecord(
            mod_id=mod_id,
            name=str(raw.get("_sName") or f"Mod {mod_id}"),
            model=str(raw.get("_sModelName") or "Mod"),
            author=str(submitter.get("_sName") or ""),
            category=str(root_category.get("_sName") or ""),
            subcategory=str(sub_category.get("_sName") or ""),
            version=str(raw.get("_sVersion") or ""),
            likes=int(raw.get("_nLikeCount") or 0),
            views=int(raw.get("_nViewCount") or 0),
            date_added=int(raw.get("_tsDateAdded") or 0),
            date_modified=int(raw.get("_tsDateModified") or 0),
            profile_url=str(raw.get("_sProfileUrl") or ""),
            preview_url=first_image_url(raw.get("_aPreviewMedia")),
            tags=tuple(str(t) for t in (raw.get("_aTags") or ())),
        )

    # -------------------------------------------------------------- профиль
    def get_mod_profile(self, mod_id: int) -> dict:
        """Профиль мода: имя, автор, описание, список файлов."""
        data = self._get_json(f"/Mod/{mod_id}/ProfilePage")
        files: list[ModFile] = []
        for raw in data.get("_aFiles") or []:
            try:
                file_id = int(raw.get("_idRow"))
            except (TypeError, ValueError):
                continue
            files.append(
                ModFile(
                    file_id=file_id,
                    name=str(raw.get("_sFile") or f"file_{file_id}"),
                    size=int(raw.get("_nFilesize") or 0),
                    download_url=str(
                        raw.get("_sDownloadUrl")
                        or f"https://gamebanana.com/dl/{file_id}"
                    ),
                    downloads=int(raw.get("_nDownloadCount") or 0),
                    md5=str(raw.get("_sMd5Checksum") or ""),
                    date_added=int(raw.get("_tsDateAdded") or 0),
                )
            )
        description = str(data.get("_sText") or data.get("_aDescription") or "")
        return {
            "mod_id": mod_id,
            "name": str(data.get("_sName") or ""),
            "author": str((data.get("_aSubmitter") or {}).get("_sName") or ""),
            "description": description[:600],
            "profile_url": str(data.get("_sProfileUrl") or ""),
            "preview_url": first_image_url(data.get("_aPreviewMedia")),
            "files": files,
        }

    # ------------------------------------------------------------ загрузка
    def download_file(
        self,
        url: str,
        dest: Path,
        progress_cb=None,      # progress_cb(done_bytes, total_bytes)
        cancel_cb=None,        # cancel_cb() -> bool  (True = отмена)
    ) -> Path:
        """Стримит файл мода в dest (через .part, с прогрессом и отменой)."""
        if self.mirror:
            url = url.replace("https://gamebanana.com", self.mirror, 1)
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")

        try:
            with self._session.get(
                url, stream=True, timeout=(10, 300), allow_redirects=True
            ) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("Content-Length") or 0)
                done = 0
                with open(tmp, "wb") as fh:
                    for chunk in resp.iter_content(chunk_size=256 * 1024):
                        if cancel_cb is not None and cancel_cb():
                            raise DownloadCancelled("Загрузка отменена")
                        if chunk:
                            fh.write(chunk)
                            done += len(chunk)
                            if progress_cb is not None:
                                progress_cb(done, total)
            tmp.rename(dest)
            return dest
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass

    # -------------------------------------------------- протокол «в 1 клик»
    def file_url_by_id(self, file_id: int) -> str:
        return f"https://gamebanana.com/dl/{file_id}"
