# -*- coding: utf-8 -*-
"""Страница «Установленные»: включение/отключение и удаление модов."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from dlmm.core.mods import InstalledMod, ModError, ModManager
from dlmm.core.system import open_in_explorer
from dlmm.ui.widgets import human_size

_ROLE_MOD = Qt.ItemDataRole.UserRole


class InstalledPage(QWidget):
    """Список .vpk в game/citadel/addons с действиями."""

    def __init__(self, settings, mods: ModManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._mods = mods

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 12)
        root.setSpacing(10)

        head = QHBoxLayout()
        title = QLabel("Установленные моды")
        title.setObjectName("h2")
        self._count_label = QLabel()
        self._count_label.setObjectName("dim")
        head.addWidget(title)
        head.addSpacing(10)
        head.addWidget(self._count_label)
        head.addStretch(1)
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.refresh)
        head.addWidget(refresh_btn)
        root.addLayout(head)

        toolbar = QHBoxLayout()
        self._toggle_btn = QPushButton("Отключить")
        self._toggle_btn.setEnabled(False)
        self._toggle_btn.clicked.connect(self._toggle_selected)
        self._delete_btn = QPushButton("Удалить")
        self._delete_btn.setObjectName("danger")
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._delete_selected)
        self._folder_btn = QPushButton("Открыть папку модов")
        self._folder_btn.clicked.connect(self._open_folder)
        toolbar.addWidget(self._toggle_btn)
        toolbar.addWidget(self._delete_btn)
        toolbar.addWidget(self._folder_btn)
        toolbar.addStretch(1)
        root.addLayout(toolbar)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Мод", "Автор", "Размер", "Статус"])
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.itemSelectionChanged.connect(self._update_buttons)
        root.addWidget(self._table, 1)

        self._hint_label = QLabel()
        self._hint_label.setObjectName("dim")
        self._hint_label.setWordWrap(True)
        root.addWidget(self._hint_label)

    # ------------------------------------------------------------ данные
    def refresh(self) -> None:
        mods = self._mods.list_installed()
        self._table.setRowCount(len(mods))
        for row, mod in enumerate(mods):
            name_item = QTableWidgetItem(mod.mod_name or mod.file_name)
            name_item.setData(_ROLE_MOD, mod)
            if mod.file_name != (mod.mod_name or "") and mod.mod_name:
                name_item.setToolTip(mod.file_name)
            self._table.setItem(row, 0, name_item)
            self._table.setItem(row, 1, QTableWidgetItem(mod.author or "—"))
            self._table.setItem(row, 2, QTableWidgetItem(human_size(mod.size)))
            status_item = QTableWidgetItem("Включён" if mod.enabled else "Отключён")
            status_item.setForeground(
                QColor("#43E29B" if mod.enabled else "#8A95A3")
            )
            self._table.setItem(row, 3, status_item)

        self._count_label.setText(f"Всего: {len(mods)}")
        if not self._settings.game_path:
            self._hint_label.setText(
                "Путь к игре не задан. Откройте «Настройки» и нажмите "
                "«Найти автоматически» или укажите папку игры вручную."
            )
        elif not mods:
            self._hint_label.setText(
                "Моды не установлены. Откройте «Каталог модов» и нажмите "
                "«Установить» на любой карточке."
            )
        else:
            self._hint_label.setText(
                "Файлы лежат в game/citadel/addons. «Отключён» = переименован "
                "в .vpk.off и не загружается игрой."
            )
        self._update_buttons()

    def _selected(self) -> InstalledMod | None:
        rows = self._table.selectionModel().selectedRows() if self._table.selectionModel() else []
        if not rows:
            return None
        item = self._table.item(rows[0].row(), 0)
        return item.data(_ROLE_MOD) if item else None

    def _update_buttons(self) -> None:
        mod = self._selected()
        has = mod is not None
        self._toggle_btn.setEnabled(has)
        self._delete_btn.setEnabled(has)
        if has:
            self._toggle_btn.setText("Отключить" if mod.enabled else "Включить")

    # ------------------------------------------------------------ действия
    def _toggle_selected(self) -> None:
        mod = self._selected()
        if mod is None:
            return
        try:
            self._mods.set_enabled(mod.file_name, not mod.enabled)
        except ModError as exc:
            QMessageBox.warning(self, "Не удалось переключить мод", str(exc))
        self.refresh()

    def _delete_selected(self) -> None:
        mod = self._selected()
        if mod is None:
            return
        answer = QMessageBox.question(
            self,
            "Удаление мода",
            f"Удалить «{mod.mod_name or mod.file_name}» из папки модов?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self._mods.delete(mod.file_name)
        except ModError as exc:
            QMessageBox.warning(self, "Не удалось удалить", str(exc))
        self.refresh()

    def _open_folder(self) -> None:
        addons = self._mods.addons_dir
        if addons is not None and addons.parent.exists():
            open_in_explorer(addons if addons.exists() else addons.parent)

    def showEvent(self, event) -> None:  # noqa: N802 (Qt API)
        super().showEvent(event)
        self.refresh()
