# -*- coding: utf-8 -*-
"""Страница каталога модов: лента GameBanana, поиск, установка."""
from __future__ import annotations

import time
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from dlmm.api.gamebanana import (
    ModFile,
    ModRecord,
    parse_mmdl_url,
)
from dlmm.config import app_data_dir
from dlmm.core import steam
from dlmm.core.mods import ModError
from dlmm.ui.widgets import DownloadDialog, ModCard, human_size
from dlmm.ui.workers import ApiWorker, CatalogLoader, DownloadWorker


class ModsPage(QWidget):
    """Каталог модов Deadlock с GameBanana (Game ID 20948)."""

    installed_changed = pyqtSignal()

    def __init__(self, settings, client, mods, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._client = client
        self._mods = mods

        self._cards: list[ModCard] = []
        self._page = 0            # последняя загруженная страница ленты
        self._total = 0
        self._loader: CatalogLoader | None = None
        self._profile_worker: ApiWorker | None = None
        self._download_worker: DownloadWorker | None = None
        self._download_dialog: DownloadDialog | None = None
        self._pending_file_id: int | None = None  # для установки по ссылке 1-клик
        self._nam = QNetworkAccessManager(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 12)
        root.setSpacing(10)

        # --- шапка
        head = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel("Каталог модов")
        title.setObjectName("h2")
        subtitle = QLabel("GameBanana · Deadlock (Game ID 20948)")
        subtitle.setObjectName("dim")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        head.addLayout(titles)
        head.addStretch(1)
        self._refresh_btn = QPushButton("Обновить")
        self._refresh_btn.clicked.connect(self.refresh)
        head.addWidget(self._refresh_btn)
        root.addLayout(head)

        # --- поиск
        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText(
            "Поиск по загруженным модам (название, автор, категория)…"
        )
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self._search, 1)
        root.addLayout(search_row)

        # --- сетка карточек
        self._grid_holder = QWidget()
        self._grid = QGridLayout(self._grid_holder)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(14)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._grid_holder)
        root.addWidget(scroll, 1)

        # --- низ: счётчик + «загрузить ещё»
        bottom = QHBoxLayout()
        self._count_label = QLabel("Загрузка каталога…")
        self._count_label.setObjectName("dim")
        bottom.addWidget(self._count_label)
        bottom.addStretch(1)
        self._more_btn = QPushButton("Загрузить ещё")
        self._more_btn.clicked.connect(self._fetch)
        bottom.addWidget(self._more_btn)
        root.addLayout(bottom)

        self._error_label = QLabel()
        self._error_label.setObjectName("warn")
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        root.addWidget(self._error_label)

        # первая загрузка — чуть позже показа окна, чтобы UI отрисовался
        QTimer.singleShot(150, self.refresh)

    # ------------------------------------------------------------- каталог
    def refresh(self) -> None:
        """Сбрасывает каталог и грузит первую страницу ленты."""
        self._cards.clear()
        self._page = 0
        self._total = 0
        self._relayout()
        self._fetch()

    def _fetch(self) -> None:
        self._set_busy(True)
        self._error_label.hide()
        self._loader = CatalogLoader(self._client, self._page + 1, self._settings.per_page)
        self._loader.got.connect(self._on_loaded)
        self._loader.err.connect(self._on_error)
        self._loader.start()

    def _set_busy(self, busy: bool) -> None:
        self._refresh_btn.setEnabled(not busy)
        self._more_btn.setEnabled(not busy)
        self._more_btn.setText("Загрузка…" if busy else "Загрузить ещё")

    def _on_loaded(self, records: list, next_page: int, total: int) -> None:
        self._page = next_page - 1
        self._total = total
        installed_ids = {
            mod.mod_id for mod in self._mods.list_installed() if mod.mod_id is not None
        }
        for record in records:
            card = ModCard(record, installed=record.mod_id in installed_ids)
            card.install_requested.connect(self._on_install_clicked)
            self._cards.append(card)
            if record.preview_url:
                self._load_preview(card)
        self._relayout()
        self._update_counts()
        self._set_busy(False)

    def _on_error(self, message: str) -> None:
        self._set_busy(False)
        self._error_label.setText(f"Ошибка загрузки каталога: {message}")
        self._error_label.show()
        self._count_label.setText("Каталог недоступен")

    def _update_counts(self) -> None:
        visible = self._visible_cards()
        if self._search.text().strip():
            self._count_label.setText(
                f"Найдено: {len(visible)} из загруженных {len(self._cards)}"
            )
        else:
            self._count_label.setText(
                f"Показано: {len(self._cards)} из ~{self._total} модов Deadlock"
            )

    def _on_search_changed(self) -> None:
        self._relayout()
        self._update_counts()

    # --------------------------------------------------------------- сетка
    def _visible_cards(self) -> list[ModCard]:
        query = self._search.text().strip().casefold()
        if not query:
            return self._cards
        result = []
        for card in self._cards:
            rec = card.record
            haystack = " ".join(
                (rec.name, rec.author, rec.category, rec.subcategory)
            ).casefold()
            if query in haystack:
                result.append(card)
        return result

    def _columns(self) -> int:
        width = self._grid_holder.width() or max(0, self.width() - 40)
        return max(1, int(width) // (ModCard.CARD_W + 14))

    def _relayout(self) -> None:
        grid = self._grid
        while grid.count():
            item = grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
        for r in range(grid.rowCount()):
            grid.setRowStretch(r, 0)
        for c in range(grid.columnCount()):
            grid.setColumnStretch(c, 0)

        cards = self._visible_cards()
        cols = self._columns()
        for i, card in enumerate(cards):
            card.show()
            grid.addWidget(
                card,
                i // cols,
                i % cols,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            )
        rows = (len(cards) + cols - 1) // cols
        grid.setColumnStretch(cols, 1)
        grid.setRowStretch(rows, 1)

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt API)
        super().resizeEvent(event)
        self._relayout()

    # -------------------------------------------------------------- превью
    def _load_preview(self, card: ModCard) -> None:
        reply = self._nam.get(QNetworkRequest(QUrl(card.record.preview_url)))
        reply.finished.connect(lambda r=reply, c=card: self._preview_done(r, c))

    def _preview_done(self, reply: QNetworkReply, card: ModCard) -> None:
        data = bytes(reply.readAll())
        error = reply.error()
        reply.deleteLater()
        if error != QNetworkReply.NetworkError.NoErrorError:
            return
        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            card.set_preview(pixmap)

    # ------------------------------------------------------------ установка
    def _on_install_clicked(self, record: ModRecord) -> None:
        if self._mods.is_installed(record.mod_id):
            QMessageBox.information(
                self, "Уже установлено", f"«{record.name}» уже установлен."
            )
            return
        self._profile_worker = ApiWorker(self._client.get_mod_profile, record.mod_id)
        self._profile_worker.ok.connect(lambda profile, rec=record: self._on_profile(rec, profile))
        self._profile_worker.err.connect(
            lambda msg: QMessageBox.warning(self, "GameBanana", msg)
        )
        self._profile_worker.start()

    def _on_profile(self, record: ModRecord, profile: dict) -> None:
        files: list[ModFile] = profile.get("files") or []
        if not files:
            QMessageBox.information(
                self, "Нет файлов", "У этого мода нет доступных для скачивания файлов."
            )
            return

        target: ModFile | None = None
        if self._pending_file_id is not None:
            # установка по ссылке GameBanana «в 1 клик»: нужен конкретный файл
            wanted = self._pending_file_id
            self._pending_file_id = None
            target = next((f for f in files if f.file_id == wanted), files[0])
        elif len(files) == 1:
            target = files[0]
        else:
            target = self._choose_file(profile.get("name") or record.name, files)
        if target is None:
            return
        self._start_download(record, profile, target)

    def _choose_file(self, mod_name: str, files: list[ModFile]) -> ModFile | None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Выбор файла")
        dialog.setFixedWidth(460)
        layout = QVBoxLayout(dialog)
        title = QLabel(f"Файлы мода «{mod_name}»:")
        title.setObjectName("h2")
        title.setWordWrap(True)
        layout.addWidget(title)

        chosen: list[ModFile | None] = [None]
        for file_item in files:
            caption = f"{file_item.name}  ({human_size(file_item.size)}, скачиваний: {file_item.downloads})"
            btn = QPushButton(caption)
            btn.clicked.connect(
                lambda _=False, f=file_item: (
                    chosen.__setitem__(0, f), dialog.accept()
                )
            )
            layout.addWidget(btn)

        cancel = QPushButton("Отмена")
        cancel.setObjectName("danger")
        cancel.clicked.connect(dialog.reject)
        layout.addWidget(cancel)
        dialog.exec()
        return chosen[0]

    def _start_download(self, record: ModRecord, profile: dict, file_item: ModFile) -> None:
        dest = app_data_dir() / "downloads" / str(file_item.file_id) / file_item.name
        self._download_dialog = DownloadDialog(self, file_item.name)
        self._download_worker = DownloadWorker(self._client, file_item.download_url, dest)
        self._download_worker.progress.connect(self._download_dialog.on_progress)
        self._download_worker.done.connect(
            lambda path, rec=record, prof=profile, f=file_item: self._on_downloaded(rec, prof, f, path)
        )
        self._download_worker.err.connect(self._download_dialog.on_error)
        self._download_worker.start()
        self._download_dialog.exec()
        self._download_dialog = None
        self._download_worker = None

    def _on_downloaded(
        self, record: ModRecord, profile: dict, file_item: ModFile, path: Path
    ) -> None:
        if self._download_dialog is not None:
            self._download_dialog.accept()
        meta = {
            "mod_id": record.mod_id,
            "mod_name": profile.get("name") or record.name,
            "author": profile.get("author") or record.author,
            "file_id": file_item.file_id,
            "installed_at": time.strftime("%Y-%m-%d %H:%M"),
        }
        try:
            installed = self._mods.install_vpk(path, meta)
        except ModError as exc:
            QMessageBox.critical(self, "Ошибка установки", str(exc))
            return
        QMessageBox.information(
            self,
            "Установка завершена",
            f"Мод установлен: {installed.file_name}\n"
            f"Папка: {installed.path.parent}",
        )
        self._mark_installed(record.mod_id)
        self.installed_changed.emit()
        if self._settings.launch_after_install:
            steam.launch_game()

    def _mark_installed(self, mod_id: int | None) -> None:
        for card in self._cards:
            if card.record.mod_id == mod_id:
                card.set_installed(True)

    # ------------------------------------------- ссылки «в 1 клик» (mmdl://)
    def handle_mmdl_url(self, url: str) -> bool:
        """Установка мода по ссылке deadlock-mod-manager:… (протокол GameBanana).

        Возвращает True, если ссылка распознана и установка запущена.
        """
        parsed = parse_mmdl_url(url)
        if parsed is None:
            return False
        file_id, mod_id = parsed
        if mod_id is None:
            stub_record = ModRecord(mod_id=0, name=f"Файл {file_id} с GameBanana")
            stub_profile = {
                "mod_id": 0,
                "name": f"Файл {file_id} с GameBanana",
                "author": "",
                "files": [
                    ModFile(
                        file_id=file_id,
                        name=f"gamebanana_{file_id}.vpk",
                        size=0,
                        download_url=self._client.file_url_by_id(file_id),
                    )
                ],
            }
            self._start_download(stub_record, stub_profile, stub_profile["files"][0])
            return True

        self._pending_file_id = file_id
        stub_record = ModRecord(
            mod_id=mod_id, name=f"Мод {mod_id} (ссылка GameBanana)"
        )
        self._profile_worker = ApiWorker(self._client.get_mod_profile, mod_id)
        self._profile_worker.ok.connect(
            lambda profile, rec=stub_record: self._on_profile(rec, profile)
        )
        self._profile_worker.err.connect(
            lambda msg: QMessageBox.warning(self, "GameBanana", msg)
        )
        self._profile_worker.start()
        return True
