# -*- coding: utf-8 -*-
"""Страница «Настройки»: путь к игре, API/зеркало, поведение приложения."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from dlmm.config import APP_ID, DEFAULT_PROCESS_NAME, app_data_dir
from dlmm.core import steam
from dlmm.core.system import open_in_explorer, set_autostart, set_protocol_handler
from dlmm.ui.workers import ApiWorker


class SettingsPage(QWidget):
    """Форма настроек; по кнопке «Сохранить» — сигнал saved."""

    saved = pyqtSignal()

    def __init__(self, settings, client, mods, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._client = client
        self._api_worker: ApiWorker | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 12)
        root.setSpacing(12)

        title = QLabel("Настройки")
        title.setObjectName("h2")
        root.addWidget(title)

        form_host = QWidget()
        form = QFormLayout(form_host)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # --- путь к игре
        game_path_row = QHBoxLayout()
        self._game_path_edit = QLineEdit(settings.game_path)
        self._game_path_edit.setPlaceholderText(r"C:\Program Files (x86)\Steam\steamapps\common\Citadel")
        browse_btn = QPushButton("Обзор…")
        browse_btn.clicked.connect(self._browse_game_path)
        detect_btn = QPushButton("Найти автоматически")
        detect_btn.clicked.connect(self._auto_detect)
        game_path_row.addWidget(self._game_path_edit, 1)
        game_path_row.addWidget(browse_btn)
        game_path_row.addWidget(detect_btn)
        form.addRow("Путь к игре:", game_path_row)

        self._process_edit = QLineEdit(settings.game_process_name)
        self._process_edit.setToolTip(
            "Имя процесса игры для отслеживания Vanilla-сессии (по умолчанию citadel.exe)"
        )
        form.addRow("Процесс игры:", self._process_edit)

        # --- GameBanana
        self._api_edit = QLineEdit(settings.api_base_url)
        form.addRow("GameBanana API:", self._api_edit)
        self._mirror_edit = QLineEdit(settings.download_mirror)
        self._mirror_edit.setPlaceholderText("пусто = официальный сервер gamebanana.com")
        form.addRow("Зеркало загрузок:", self._mirror_edit)

        # --- поведение
        self._tray_check = QCheckBox("Сворачивать в трей при закрытии окна")
        self._tray_check.setChecked(settings.minimize_to_tray)
        self._autostart_check = QCheckBox("Автозапуск с Windows")
        self._autostart_check.setChecked(settings.autostart)
        self._launch_check = QCheckBox("Запускать игру после установки мода")
        self._launch_check.setChecked(settings.launch_after_install)
        self._protocol_check = QCheckBox(
            "Открывать ссылки deadlock-mod-manager:// (кнопка «Mod installer» на GameBanana)"
        )
        form.addRow(self._tray_check)
        form.addRow(self._autostart_check)
        form.addRow(self._launch_check)
        form.addRow(self._protocol_check)

        self._timeout_spin = QSpinBox()
        self._timeout_spin.setRange(60, 600)
        self._timeout_spin.setValue(int(settings.vanilla_watch_timeout))
        self._timeout_spin.setSuffix(" сек")
        self._timeout_spin.setToolTip(
            "Сколько секунд после запуска Vanilla ждать появления процесса игры, "
            "прежде чем вернуть моды"
        )
        form.addRow("Ожидание запуска игры:", self._timeout_spin)

        root.addWidget(form_host)

        # --- кнопки
        buttons = QHBoxLayout()
        save_btn = QPushButton("Сохранить настройки")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._save)
        check_btn = QPushButton("Проверить подключение к API")
        check_btn.clicked.connect(self._check_api)
        data_btn = QPushButton("Открыть папку данных")
        data_btn.clicked.connect(lambda: open_in_explorer(app_data_dir()))
        buttons.addWidget(save_btn)
        buttons.addWidget(check_btn)
        buttons.addWidget(data_btn)
        buttons.addStretch(1)
        root.addLayout(buttons)

        self._status = QLabel()
        self._status.setObjectName("dim")
        self._status.setWordWrap(True)
        root.addWidget(self._status)

        hint = QLabel(
            f"Данные приложения: {app_data_dir()} "
            f"(config.json, installed.json, лог {APP_ID.lower()}.log)"
        )
        hint.setObjectName("dim")
        hint.setWordWrap(True)
        root.addWidget(hint)
        root.addStretch(1)

    # -------------------------------------------------------------- helpers
    def _browse_game_path(self) -> None:
        current = self._game_path_edit.text().strip()
        start = current if current and Path(current).exists() else str(Path.home())
        chosen = QFileDialog.getExistingDirectory(
            self, "Выберите папку игры (steamapps/common/Citadel)", start
        )
        if chosen:
            self._game_path_edit.setText(chosen)

    def _auto_detect(self) -> None:
        found = steam.find_game_dir()
        if found is None:
            QMessageBox.warning(
                self,
                "Steam не найден",
                "Не удалось определить путь автоматически.\n"
                "Проверьте, что Steam установлен, и укажите путь вручную.",
            )
            return
        self._game_path_edit.setText(str(found))
        self._status.setText(f"Игра найдена: {found}")

    def _check_api(self) -> None:
        self._status.setText("Проверка API…")
        self._api_worker = ApiWorker(self._client.get_feed_page, 1)
        self._api_worker.ok.connect(self._api_ok)
        self._api_worker.err.connect(self._api_err)
        self._api_worker.start()

    def _api_ok(self, result) -> None:
        records, _total = result
        names = ", ".join(rec.name for rec in records[:3])
        self._status.setText(
            f"API работает. Свежие моды: {names}…"
        )

    def _api_err(self, message: str) -> None:
        self._status.setText(f"Ошибка API: {message}")

    # -------------------------------------------------------------- save
    def sync_from_settings(self) -> None:
        """Обновляет поля формы из текущего объекта настроек (после автоопределения пути)."""
        s = self._settings
        self._game_path_edit.setText(s.game_path)
        self._process_edit.setText(s.game_process_name)
        self._api_edit.setText(s.api_base_url)
        self._mirror_edit.setText(s.download_mirror)
        self._tray_check.setChecked(s.minimize_to_tray)
        self._autostart_check.setChecked(s.autostart)
        self._launch_check.setChecked(s.launch_after_install)
        self._timeout_spin.setValue(int(s.vanilla_watch_timeout))

    def _save(self) -> None:
        s = self._settings
        s.game_path = self._game_path_edit.text().strip()
        s.game_process_name = self._process_edit.text().strip() or DEFAULT_PROCESS_NAME
        s.api_base_url = self._api_edit.text().strip() or "https://gamebanana.com/apiv11"
        s.download_mirror = self._mirror_edit.text().strip()
        s.minimize_to_tray = self._tray_check.isChecked()
        s.autostart = self._autostart_check.isChecked()
        s.launch_after_install = self._launch_check.isChecked()
        s.vanilla_watch_timeout = self._timeout_spin.value()

        try:
            set_autostart(s.autostart)
            set_protocol_handler(self._protocol_check.isChecked())
        except OSError as exc:
            QMessageBox.warning(
                self, "Реестр Windows", f"Не удалось обновить настройки системы: {exc}"
            )
        s.save()
        self.saved.emit()
        QMessageBox.information(self, "Настройки", "Настройки сохранены.")
