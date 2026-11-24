# -*- coding: utf-8 -*-
"""Сборка приложения: один экземпляр, тема, окно, трей, ссылки GameBanana."""
from __future__ import annotations

import logging
import sys
import traceback

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication, QMessageBox

from dlmm import __app_name__, __version__
from dlmm.api.gamebanana import GameBananaClient
from dlmm.config import APP_ID, Settings, log_path
from dlmm.core.mods import ModManager
from dlmm.paths import asset
from dlmm.ui.main_window import MainWindow
from dlmm.ui.theme import apply as apply_theme
from dlmm.ui.tray import TrayManager

logger = logging.getLogger("dlmm")

MMDL_PREFIX = "deadlock-mod-manager:"


def _setup_logging() -> None:
    try:
        logging.basicConfig(
            filename=str(log_path()),
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    except OSError:
        logging.basicConfig(level=logging.INFO)


def _install_excepthook() -> None:
    def hook(exc_type, value, tb) -> None:
        text = "".join(traceback.format_exception(exc_type, value, tb))
        logger.error("Необработанное исключение:\n%s", text)
        try:
            QMessageBox.critical(
                None,
                "Ошибка",
                f"Непредвиденная ошибка (подробности в логе):\n{value}",
            )
        except Exception:  # noqa: BLE001
            pass
        sys.__excepthook__(exc_type, value, tb)

    sys.excepthook = hook


def _window_icon():
    icon = QIcon()
    for name in ("icon.png", "icon.ico"):
        path = asset(name)
        if path.exists():
            icon = QIcon(str(path))
            if not icon.isNull():
                return icon
    return icon


def _single_instance(app: QApplication):
    """Повторный запуск не создаёт второе окно, а активирует первое."""
    socket = QLocalSocket()
    socket.connectToServer(APP_ID)
    if socket.waitForConnected(300):
        socket.write(b"show\n")
        socket.flush()
        socket.waitForBytesWritten(200)
        socket.disconnectFromServer()
        return None
    QLocalServer.removeServer(APP_ID)
    server = QLocalServer()
    server.listen(APP_ID)
    return server


def main(argv: list[str] | None = None) -> int:
    _setup_logging()
    args = list(sys.argv if argv is None else argv)
    logger.info("Запуск Deadlock Mod Manager %s", __version__)

    app = QApplication(args)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(APP_ID)
    app.setWindowIcon(_window_icon())
    app.setQuitOnLastWindowClosed(False)  # закрытие окна -> трей, выход через меню
    apply_theme(app)
    _install_excepthook()

    server = _single_instance(app)
    if server is None:
        logger.info("Приложение уже запущено — активируем существующее окно")
        return 0

    settings = Settings.load()
    client = GameBananaClient(settings.api_base_url, settings.download_mirror)
    mods = ModManager(settings)

    window = MainWindow(settings, client, mods)
    tray = TrayManager(window, mods, settings)
    window.set_tray(tray)
    tray.show()

    def _on_new_connection() -> None:
        sock = server.nextPendingConnection()
        if sock is not None:
            sock.readAll()
            sock.deleteLater()
        window.show_from_tray()

    server.newConnection.connect(_on_new_connection)

    # защита от «зависшего» Vanilla-режима: если прошлый запуск не вернул
    # моды (падение, выключение ПК) — восстанавливаем при старте
    if mods.is_vanilla_active():
        try:
            mods.restore_after_vanilla()
            tray.show_message(
                "Моды возвращены",
                "Резервную папку addons_vanilla_backup восстановили в addons.",
            )
        except Exception:  # noqa: BLE001
            logger.warning("Не удалось вернуть моды при старте", exc_info=True)

    start_hidden = "--minimized" in args or "--hidden" in args or settings.autostart
    if start_hidden:
        window.hide()
    else:
        window.show()

    # установка «в 1 клик» по ссылке GameBanana (deadlock-mod-manager://)
    for arg in args[1:]:
        if arg.lower().startswith(MMDL_PREFIX):
            QTimer.singleShot(400, lambda url=arg: window.handle_mmdl_url(url))

    app.aboutToQuit.connect(window.shutdown_cleanup)
    exit_code = app.exec()
    server.close()
    logger.info("Завершение (код %s)", exit_code)
    return exit_code
