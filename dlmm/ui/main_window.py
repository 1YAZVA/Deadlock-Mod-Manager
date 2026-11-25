# -*- coding: utf-8 -*-
"""Главное окно: боковая панель, навигация, кнопки запуска игры, Vanilla-логика."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from dlmm import __version__
from dlmm.config import Settings
from dlmm.core import steam
from dlmm.core.mods import ModError, ModManager
from dlmm.paths import asset
from dlmm.ui.installed_page import InstalledPage
from dlmm.ui.mods_page import ModsPage
from dlmm.ui.settings_page import SettingsPage
from dlmm.ui.theme import ACCENT, gold_glow
from dlmm.ui.workers import GameSessionWatcher


class MainWindow(QMainWindow):
    """Окно приложения: сайдбар с логотипом и страницами + кнопки запуска."""

    def __init__(self, settings: Settings, client, mods: ModManager) -> None:
        super().__init__()
        self._settings = settings
        self._client = client
        self._mods = mods
        self._tray = None
        self._force_quit = False
        self._tray_hint_shown = False
        self._vanilla_watcher: GameSessionWatcher | None = None

        self.setWindowTitle("Deadlock Mod Manager")
        self.resize(*settings.window_size)
        icon = asset("icon.png")
        if icon.exists():
            self.setWindowIcon(QIcon(str(icon)))

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())

        self._stack = QStackedWidget()
        self._mods_page = ModsPage(settings, client, mods)
        self._installed_page = InstalledPage(settings, mods)
        self._settings_page = SettingsPage(settings, client, mods)
        self._mods_page.installed_changed.connect(self._installed_page.refresh)
        self._settings_page.saved.connect(self._on_settings_saved)
        self._stack.addWidget(self._mods_page)
        self._stack.addWidget(self._installed_page)
        self._stack.addWidget(self._settings_page)
        layout.addWidget(self._stack, 1)
        self.setCentralWidget(central)

        self.statusBar().showMessage(
            "Моды: <игра>/game/citadel/addons · Steam AppID 1422450 · GameBanana 20948"
        )
        self._switch_page(0)

    # ------------------------------------------------------------ сайдбар
    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        # Иначе QSS-фон (радиальная золотая подсветка сверху) не рисуется
        sidebar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        sidebar.setFixedWidth(250)
        root = QVBoxLayout(sidebar)
        root.setContentsMargins(16, 18, 16, 14)
        root.setSpacing(6)

        logo_row = QHBoxLayout()
        logo = QLabel()
        pixmap_path = asset("logo.png")
        if pixmap_path.exists():
            pixmap = QPixmap(str(pixmap_path)).scaled(
                44, 44,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo.setPixmap(pixmap)
            gold_glow(logo, blur=16, opacity=60)
        else:
            logo.setText("◉")
            logo.setStyleSheet(f"color: {ACCENT}; font-size: 34px;")
        logo_row.addWidget(logo)
        titles = QVBoxLayout()
        title = QLabel("DEADLOCK")
        title.setObjectName("logoTitle")
        gold_glow(title, blur=24, opacity=70)
        subtitle = QLabel("MOD MANAGER")
        subtitle.setObjectName("logoSub")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        logo_row.addLayout(titles)
        root.addLayout(logo_row)
        root.addSpacing(18)

        self._nav_buttons: list[QPushButton] = []
        for caption, index in (
            ("Каталог модов", 0),
            ("Установленные", 1),
            ("Настройки", 2),
        ):
            btn = QPushButton(caption)
            btn.setObjectName("nav")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, i=index: self._switch_page(i))
            self._nav_buttons.append(btn)
            root.addWidget(btn)

        root.addStretch(1)

        play_btn = QPushButton("ИГРАТЬ С МОДАМИ")
        play_btn.setObjectName("primary")
        play_btn.setProperty("class", "navBig")
        play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        play_btn.clicked.connect(self.play_with_mods)
        root.addWidget(play_btn)

        vanilla_btn = QPushButton("VANILLA (без модов)")
        vanilla_btn.setObjectName("navBig")
        vanilla_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        vanilla_btn.clicked.connect(self.play_vanilla)
        root.addWidget(vanilla_btn)

        restore_btn = QPushButton("Вернуть моды после Vanilla")
        restore_btn.setToolTip(
            "Если игра завершилась, а моды не вернулись — нажмите эту кнопку"
        )
        restore_btn.clicked.connect(self.restore_mods_now)
        root.addWidget(restore_btn)

        version = QLabel(f"v{__version__} · deadlockru.ru style")
        version.setObjectName("dim")
        version.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        root.addWidget(version)
        return sidebar

    def _switch_page(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)
        if index == 1:
            self._installed_page.refresh()

    # ------------------------------------------------------------- запуск
    def _ensure_game_path(self) -> bool:
        path = self._settings.game_path
        if path and Path(path).exists():
            return True
        found = steam.find_game_dir()
        if found is not None:
            self._settings.game_path = str(found)
            self._settings.save()
            self._settings_page.sync_from_settings()
            self.tray_message("Путь найден", f"Deadlock: {found}")
            return True
        QMessageBox.warning(
            self,
            "Путь к игре",
            "Не удалось определить путь к Deadlock.\n\n"
            "Откройте «Настройки» и укажите папку игры вручную "
            "(steamapps/common/Citadel).",
        )
        self._switch_page(2)
        return False

    def play_with_mods(self) -> None:
        """Кнопка «Играть с модами»: проверяет активные моды и запускает игру."""
        if not self._ensure_game_path():
            return
        if self._mods.count_enabled() == 0:
            answer = QMessageBox.question(
                self,
                "Активных модов нет",
                "Все моды отключены или не установлены.\nЗапустить Deadlock без модов?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        steam.launch_game()
        self.statusBar().showMessage("Запуск Deadlock (с модами)…", 8000)

    def play_vanilla(self) -> None:
        """Кнопка «Vanilla»: убирает моды, запускает игру, возвращает их после выхода."""
        if not self._ensure_game_path():
            return
        try:
            moved = self._mods.disable_for_vanilla()
        except ModError as exc:
            QMessageBox.critical(self, "Vanilla", str(exc))
            return
        steam.launch_game()
        if moved:
            self._start_vanilla_watcher()
            self.tray_message(
                "Vanilla-режим",
                "Моды временно перенесены в addons_vanilla_backup "
                "и вернутся после выхода из игры.",
            )
            self.statusBar().showMessage("Запуск Deadlock без модов…", 8000)
        else:
            self.statusBar().showMessage("Запуск Deadlock (модов не было)…", 8000)

    def _start_vanilla_watcher(self) -> None:
        self._vanilla_watcher = GameSessionWatcher(
            self._settings.game_process_name,
            self._settings.vanilla_watch_timeout,
            self,
        )
        self._vanilla_watcher.ended.connect(self._on_vanilla_session_ended)
        self._vanilla_watcher.start()

    def _on_vanilla_session_ended(self, played: bool) -> None:
        try:
            restored = self._mods.restore_after_vanilla()
        except ModError as exc:
            self.tray_message("Ошибка", str(exc))
            return
        if restored:
            self.tray_message(
                "Моды возвращены",
                "Игра закрыта — файлы .vpk снова в game/citadel/addons.",
            )
        elif not played:
            self.tray_message(
                "Vanilla", "Игра не запустилась за отведённое время; моды на месте."
            )
        self._installed_page.refresh()

    def restore_mods_now(self) -> None:
        """Ручной возврат модов (на случай сбоя авто-возврата)."""
        try:
            restored = self._mods.restore_after_vanilla()
        except ModError as exc:
            QMessageBox.warning(self, "Vanilla", str(exc))
            return
        if restored:
            self.tray_message("Моды возвращены", "Файлы .vpk снова в папке addons.")
        else:
            QMessageBox.information(
                self, "Vanilla", "Резервная папка не найдена — моды уже на месте."
            )
        self._installed_page.refresh()

    # ------------------------------------------------------------- настройки
    def _on_settings_saved(self) -> None:
        self._client.base_url = self._settings.api_base_url.rstrip("/")
        self._client.mirror = self._settings.download_mirror.strip().rstrip("/")
        self.statusBar().showMessage("Настройки сохранены", 5000)

    def handle_mmdl_url(self, url: str) -> bool:
        """Установка «в 1 клик» по ссылке GameBanana (deadlock-mod-manager://)."""
        return self._mods_page.handle_mmdl_url(url)

    # ------------------------------------------------------------------- трей
    def set_tray(self, tray) -> None:
        self._tray = tray

    def tray_message(self, title: str, text: str) -> None:
        if self._tray is not None:
            self._tray.show_message(title, text)

    def show_from_tray(self) -> None:
        self.showNormal()
        self.activateWindow()
        self.raise_()

    # ------------------------------------------------------- закрытие/выход
    def closeEvent(self, event) -> None:  # noqa: N802 (Qt API)
        """Закрытие окна = сворачивание в трей (если включено в настройках)."""
        if self._settings.minimize_to_tray and not self._force_quit and self._tray:
            event.ignore()
            self.hide()
            if not self._tray_hint_shown:
                self._tray_hint_shown = True
                self.tray_message(
                    "Deadlock Mod Manager",
                    "Приложение свернуто в трей. Правый клик по иконке — меню, "
                    "двойной клик — открыть окно.",
                )
            return
        event.accept()
        self.shutdown_cleanup()

    def force_quit(self) -> None:
        """Полное завершение приложения (иконка трея → «Выход»)."""
        self._force_quit = True
        self.close()
        QApplication.quit()  # quitOnLastWindowClosed=False, поэтому явно

    def shutdown_cleanup(self) -> None:
        """Безопасное завершение: остановить вотчер и вернуть моды, если нужно."""
        self._force_quit = True
        if self._vanilla_watcher is not None and self._vanilla_watcher.isRunning():
            self._vanilla_watcher.stop()
            self._vanilla_watcher.wait(2000)
        try:
            if self._mods.is_vanilla_active() and not steam.is_game_running(
                self._settings.game_process_name
            ):
                self._mods.restore_after_vanilla()
        except Exception:  # noqa: BLE001 — при выходе не роняем приложение
            pass
