# -*- coding: utf-8 -*-
"""Графические компоненты: карточка мода и диалог скачивания."""
from __future__ import annotations

import time

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from dlmm.api.gamebanana import ModRecord
from dlmm.core.system import open_url


def human_size(num: float) -> str:
    """9948734 -> «9.5 МБ»."""
    value = float(num)
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if value < 1024 or unit == "ГБ":
            return f"{value:.1f} {unit}".replace(".0 ", " ")
        value /= 1024
    return f"{value:.1f} ГБ"


def human_count(num: int) -> str:
    """34218 -> «34.2K»."""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return str(num)


class ModCard(QFrame):
    """Карточка мода в каталоге: превью, название, автор, статистика, кнопка."""

    install_requested = pyqtSignal(object)  # ModRecord

    CARD_W, CARD_H = 236, 324
    PREVIEW_W, PREVIEW_H = 212, 128

    def __init__(self, record: ModRecord, installed: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.record = record
        self.setObjectName("modCard")
        self.setFixedSize(self.CARD_W, self.CARD_H)
        self.setToolTip("Двойной клик — открыть страницу мода на GameBanana")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        self.preview = QLabel()
        self.preview.setObjectName("preview")
        self.preview.setFixedSize(self.PREVIEW_W, self.PREVIEW_H)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setText("…")
        layout.addWidget(self.preview)

        self.name_label = QLabel(record.name)
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumHeight(40)
        layout.addWidget(self.name_label)

        category = record.subcategory or record.category or "Мод"
        self.meta_label = QLabel(category if not record.version else f"{category} · v{record.version}")
        self.meta_label.setObjectName("dim")
        layout.addWidget(self.meta_label)

        self.stats_label = QLabel(
            f"Лайки: {human_count(record.likes)}   Просмотры: {human_count(record.views)}"
        )
        self.stats_label.setObjectName("dim")
        layout.addWidget(self.stats_label)

        self.author_label = QLabel(f"Автор: {record.author or '—'}")
        self.author_label.setObjectName("dim")
        layout.addWidget(self.author_label)

        self.install_btn = QPushButton("Установить")
        self.install_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.install_btn.clicked.connect(lambda: self.install_requested.emit(self.record))
        layout.addWidget(self.install_btn)

        self.set_installed(installed)

    # ------------------------------------------------------------- состояние
    def set_installed(self, installed: bool) -> None:
        self._installed = installed
        if installed:
            self.install_btn.setText("Установлен")
            self.install_btn.setObjectName("")
            self.install_btn.setEnabled(True)
            self.install_btn.setToolTip("Мод уже установлен — см. страницу «Установленные»")
        else:
            self.install_btn.setText("Установить")
            self.install_btn.setObjectName("primary")
        self.install_btn.style().unpolish(self.install_btn)
        self.install_btn.style().polish(self.install_btn)

    @property
    def is_installed(self) -> bool:
        return self._installed

    def set_preview(self, pixmap: QPixmap) -> None:
        """Превью «обложкой» (обрезка по центру)."""
        scaled = pixmap.scaled(
            self.PREVIEW_W,
            self.PREVIEW_H,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview.setPixmap(scaled)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # ------------------------------------------------------------------ мышь
    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if self.record.profile_url:
            open_url(self.record.profile_url)
        super().mouseDoubleClickEvent(event)


class DownloadDialog(QDialog):
    """Диалог скачивания: прогресс, скорость, отмена."""

    def __init__(self, parent: QWidget | None, file_name: str) -> None:
        super().__init__(parent)
        self.setWindowTitle("Скачивание мода")
        self.setModal(True)
        self.setFixedWidth(420)
        self._cancelled = False
        self._last_time = time.monotonic()
        self._last_done = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 14)
        layout.setSpacing(10)

        title = QLabel(file_name)
        title.setObjectName("h2")
        title.setWordWrap(True)
        layout.addWidget(title)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.status_label = QLabel("Соединение…")
        self.status_label.setObjectName("dim")
        layout.addWidget(self.status_label)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("danger")
        cancel_btn.clicked.connect(self._on_cancel)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(cancel_btn)
        layout.addLayout(row)

    # ------------------------------------------------------------ колбэки
    def cancel_requested(self) -> bool:
        return self._cancelled

    def _on_cancel(self) -> None:
        self._cancelled = True
        self.status_label.setText("Отмена…")

    def on_progress(self, done: int, total: int) -> None:
        if total > 0:
            percent = min(100, int(done * 100 / total))
            self.progress.setValue(percent)
        now = time.monotonic()
        dt = now - self._last_time
        if dt >= 0.4:
            speed = (done - self._last_done) / dt
            self._last_time, self._last_done = now, done
            suffix = f" из {human_size(total)} · {human_size(speed)}/с" if total else f" · {human_size(speed)}/с"
            self.status_label.setText(f"{human_size(done)}{suffix}")
        if total <= 0:
            self.progress.setRange(0, 0)  # «бегущая полоса», размер неизвестен

    def on_error(self, message: str) -> None:
        if self._cancelled:
            self.reject()
            return
        QMessageBox.critical(self, "Ошибка скачивания", message)
        self.reject()
