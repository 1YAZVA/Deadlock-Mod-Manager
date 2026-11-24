# -*- coding: utf-8 -*-
"""Системный трей: иконка-логотип, контекстное меню, уведомления."""
from __future__ import annotations

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon, QWidget

from dlmm.paths import asset


class TrayManager(QWidget):
    """QSystemTrayIcon + меню: открыть / запустить игру / вернуть моды / выход."""

    def __init__(self, window, mods, settings) -> None:
        super().__init__()
        self._window = window
        self._mods = mods

        self._icon = QIcon()
        for name in ("icon.png", "icon.ico"):
            path = asset(name)
            if path.exists():
                self._icon = QIcon(str(path))
                break

        self.tray = QSystemTrayIcon(self._icon, self)
        self.tray.setToolTip("Deadlock Mod Manager")

        menu = QMenu()
        self._act_restore = menu.addAction("Вернуть моды (после Vanilla)")
        self._act_restore.triggered.connect(window.restore_mods_now)
        menu.addSeparator()
        act_open = menu.addAction("Открыть Deadlock Mod Manager")
        act_open.triggered.connect(window.show_from_tray)
        act_play = menu.addAction("Запустить Deadlock (с модами)")
        act_play.triggered.connect(window.play_with_mods)
        act_vanilla = menu.addAction("Запустить Deadlock (Vanilla)")
        act_vanilla.triggered.connect(window.play_vanilla)
        menu.addSeparator()
        act_quit = menu.addAction("Выход")
        act_quit.triggered.connect(window.force_quit)
        menu.aboutToShow.connect(self._update_menu)
        self._menu = menu

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activated)

    # ---------------------------------------------------------------- API
    def show(self) -> None:
        self.tray.show()

    def show_message(self, title: str, text: str, ms: int = 5000) -> None:
        if self.tray.isVisible():
            self.tray.showMessage(
                title,
                text,
                QSystemTrayIcon.MessageIcon.Information,
                ms,
            )

    # ----------------------------------------------------------- внутренне
    def _on_activated(self, reason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._window.show_from_tray()

    def _update_menu(self) -> None:
        self._act_restore.setEnabled(self._mods.is_vanilla_active())
