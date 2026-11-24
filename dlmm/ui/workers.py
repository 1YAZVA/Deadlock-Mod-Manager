# -*- coding: utf-8 -*-
"""Переиспользуемые фоновые воркеры (QThread) — UI не блокируется сетью/файлами."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from dlmm.core import steam


class ApiWorker(QThread):
    """Выполняет произвольную функцию в фоне: ok(результат) / err(текст)."""

    ok = pyqtSignal(object)
    err = pyqtSignal(str)

    def __init__(self, fn, *args, parent=None) -> None:
        super().__init__(parent)
        self._fn = fn
        self._args = args

    def run(self) -> None:
        try:
            self.ok.emit(self._fn(*self._args))
        except Exception as exc:  # noqa: BLE001 — выводим любой текст ошибки в UI
            self.err.emit(str(exc))


class CatalogLoader(QThread):
    """Загружает страницу ленты GameBanana (до 4 страниц за раз, пока не наберёт моды).

    Лента GameBanana содержит смесь Mod/WiP и отдаёт фиксированные 15 записей
    на страницу, поэтому за один запрос может прийти мало карточек.
    """

    got = pyqtSignal(list, int, int)  # records, следующая_страница, всего
    err = pyqtSignal(str)

    def __init__(self, client, page: int, per_page: int = 15, max_pages: int = 4, parent=None) -> None:
        super().__init__(parent)
        self._client = client
        self._page = page
        self._per_page = per_page
        self._max_pages = max_pages

    def run(self) -> None:
        collected: list = []
        page = self._page
        total = 0
        try:
            for _ in range(self._max_pages):
                records, total = self._client.get_feed_page(page, self._per_page)
                collected.extend(records)
                page += 1
                if collected:
                    break
        except Exception as exc:  # noqa: BLE001
            self.err.emit(str(exc))
            return
        self.got.emit(collected, page, total)


class DownloadWorker(QThread):
    """Скачивает файл мода с прогрессом и поддержкой отмены."""

    progress = pyqtSignal(int, int)  # done, total
    done = pyqtSignal(object)        # Path
    err = pyqtSignal(str)

    def __init__(self, client, url: str, dest: Path, parent=None) -> None:
        super().__init__(parent)
        self._client = client
        self._url = url
        self._dest = Path(dest)
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        try:
            path = self._client.download_file(
                self._url,
                self._dest,
                progress_cb=lambda d, t: self.progress.emit(d, t),
                cancel_cb=lambda: self._cancelled,
            )
            self.done.emit(path)
        except Exception as exc:  # noqa: BLE001
            self.err.emit(str(exc))


class GameSessionWatcher(QThread):
    """Ждёт завершения игры (для возврата модов после Vanilla-сессии)."""

    ended = pyqtSignal(bool)  # True — игра стартовала и завершилась

    def __init__(self, process_name: str, timeout_s: int, parent=None) -> None:
        super().__init__(parent)
        self._process_name = process_name
        self._timeout = timeout_s
        self._stop = False

    def stop(self) -> None:
        """Запросить остановку ожидания (при выходе из приложения)."""
        self._stop = True

    def run(self) -> None:
        import time

        deadline = time.monotonic() + max(30, self._timeout)
        seen = False
        while not self._stop and time.monotonic() < deadline:
            if steam.is_game_running(self._process_name):
                seen = True
                break
            time.sleep(2.0)
        while seen and not self._stop and steam.is_game_running(self._process_name):
            time.sleep(2.0)
        self.ended.emit(seen and not self._stop)
