# -*- coding: utf-8 -*-
"""Тема оформления — повторяет дизайн сайта deadlockru.ru.

Токены взяты из :root CSS сайта (Next.js + Tailwind):
  фон       #0d1110        панели  #121614 / #161c1a   границы #2a332f
  текст     #e8e6e0        приглушённый #8a9490
  акцент    ЗОЛОТО #c8a96a; градиент кнопок #d8bc7e -> #b3945a
  статусы:  оружие/предупреждение #e08a3c, дух #8c6fd1,
            жизнь/успех #4cad6d, danger #d06a5a
Эффекты сайта: золотое свечение (glow), радиальная подсветка сверху,
карточки с диагональным градиентом 135deg #1a211e -> #121614.

Шрифты сайта: Golos Text (текст) и Unbounded (логотип/заголовки) —
встроены в base64 (dlmm/fonts_data.py, лицензия SIL OFL) и загружаются
в QFontDatabase при старте; при неудаче — системный Segoe UI.
"""
from __future__ import annotations

BG = "#0d1110"           # --bg      общий фон
SIDEBAR = "#121614"      # --panel2  боковая панель, шапки таблиц
CARD = "#161c1a"         # --panel   поля ввода, меню, таблицы
CARD_A = "#1a211e"       # верх диагонального градиента карточек
CARD_HOVER = "#1d2622"   # --accent-hover  наведение
BORDER = "#2a332f"       # --line    рамки
TEXT = "#e8e6e0"         # --ink     основной текст
DIM = "#8a9490"          # --muted2  вторичный текст
ACCENT = "#c8a96a"       # --accent  ЗОЛОТО — главный акцент
ACCENT_LIGHT = "#d8bc7e" # верх градиента кнопок
ACCENT_DARK = "#b3945a"  # низ градиента кнопок
ACCENT_PALE = "#ffdf9e"  # яркое золото при наведении
DANGER = "#d06a5a"       # --danger  удаление/ошибки
WARNING = "#e08a3c"      # --weapon  предупреждения
OK = "#4cad6d"           # --vitality/--ok  успех, «Включён»
ON_ACCENT = "#0d1110"    # текст на золоте

PALETTE = {
    "BG": BG, "SIDEBAR": SIDEBAR, "CARD": CARD, "CARD_A": CARD_A,
    "CARD_HOVER": CARD_HOVER, "BORDER": BORDER, "TEXT": TEXT, "DIM": DIM,
    "ACCENT": ACCENT, "ACCENT_LIGHT": ACCENT_LIGHT, "ACCENT_DARK": ACCENT_DARK,
    "ACCENT_PALE": ACCENT_PALE, "DANGER": DANGER, "WARNING": WARNING,
    "OK": OK, "ON_ACCENT": ON_ACCENT,
}

_RAW_QSS = """
* { font-family: "Golos Text", "Segoe UI", "Noto Sans", sans-serif; }

QMainWindow, QDialog { background: {BG}; color: {TEXT}; }
QLabel { background: transparent; color: {TEXT}; }
QLabel#logoTitle { font-family: "Unbounded", "Golos Text", sans-serif;
                   color: {ACCENT}; font-size: 16px; font-weight: 700;
                   letter-spacing: 1px; }
QLabel#logoSub   { color: {DIM}; font-size: 10px; letter-spacing: 5px; }
QLabel#h2        { font-size: 16px; font-weight: 600; color: {TEXT}; }
QLabel#dim       { color: {DIM}; font-size: 12px; }
QLabel#accent    { color: {ACCENT}; font-size: 12px; font-weight: 600; }
QLabel#warn      { color: {WARNING}; font-size: 12px; }
QLabel#preview   { background: {CARD}; border: 1px solid {BORDER};
                   border-radius: 8px; }

QWidget#sidebar, QFrame#sidebar {
    background: qradialgradient(cx:0.5, cy:0, radius:1.5, fx:0.5, fy:0,
        stop:0 rgba(200, 169, 106, 0.10),
        stop:0.4 rgba(200, 169, 106, 0.03),
        stop:1 {SIDEBAR});
    border-right: 1px solid {BORDER}; }
QFrame#modCard, QWidget#modCard {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 {CARD_A}, stop:1 {SIDEBAR});
    border: 1px solid {BORDER}; border-radius: 12px; }
QFrame#modCard:hover, QWidget#modCard:hover { border-color: {ACCENT}; }
QFrame#panel, QWidget#panel {
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; }

QPushButton { background: {CARD_HOVER}; color: {TEXT};
              border: 1px solid {BORDER}; border-radius: 10px;
              padding: 8px 14px; font-size: 13px; }
QPushButton:hover { border-color: {ACCENT}; }
QPushButton:pressed { background: {BORDER}; }
QPushButton:disabled { color: {DIM}; background: {CARD}; border-color: {BORDER}; }
QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_LIGHT}, stop:1 {ACCENT_DARK});
    border: none; color: {ON_ACCENT}; font-weight: 700; }
QPushButton#primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_PALE}, stop:1 {ACCENT_LIGHT}); }
QPushButton#primary:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_DARK}, stop:1 {ACCENT}); }
QPushButton#primary:disabled { background: {BORDER}; color: {DIM}; }
QPushButton#gold { background: transparent; border: 1px solid {ACCENT};
                   color: {ACCENT}; font-weight: 600; }
QPushButton#gold:hover { background: rgba(200, 169, 106, 0.12); }
QPushButton#gold:pressed { background: rgba(200, 169, 106, 0.22); }
QPushButton#danger { background: transparent; border: 1px solid {DANGER};
                     color: {DANGER}; }
QPushButton#danger:hover { background: rgba(208, 106, 90, 0.15); }
QPushButton#nav { text-align: left; padding: 10px 14px; border: none;
                  border-radius: 8px; color: {DIM}; font-size: 14px;
                  background: transparent; }
QPushButton#nav:hover { color: {TEXT}; background: {CARD_HOVER}; }
QPushButton#nav:checked { color: {ACCENT}; background: rgba(200, 169, 106, 0.14);
                          font-weight: 600; }
QPushButton#navBig { text-align: center; padding: 12px; font-size: 14px;
                     border-radius: 10px; }

QLineEdit, QComboBox, QSpinBox { background: {CARD};
    border: 1px solid {BORDER}; border-radius: 8px; padding: 8px 10px;
    color: {TEXT}; selection-background-color: {ACCENT};
    selection-color: {ON_ACCENT}; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: {ACCENT}; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox::down-arrow { image: none; border-left: 5px solid transparent;
    border-right: 5px solid transparent; border-top: 6px solid {DIM};
    margin-right: 8px; }
QComboBox QAbstractItemView { background: {CARD}; border: 1px solid {BORDER};
    color: {TEXT}; selection-background-color: {CARD_HOVER};
    selection-color: {ACCENT}; }
QSpinBox::up-button, QSpinBox::down-button { background: {CARD_HOVER};
    border: none; width: 18px; }
QSpinBox::up-arrow { border-left: 4px solid transparent;
    border-right: 4px solid transparent; border-bottom: 5px solid {DIM}; }
QSpinBox::down-arrow { border-left: 4px solid transparent;
    border-right: 4px solid transparent; border-top: 5px solid {DIM}; }

QCheckBox { spacing: 8px; color: {TEXT}; font-size: 13px; background: transparent; }
QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid {BORDER};
    border-radius: 5px; background: {CARD}; }
QCheckBox::indicator:hover { border-color: {ACCENT}; }
QCheckBox::indicator:checked { background: {ACCENT}; border-color: {ACCENT}; }

QProgressBar { background: {CARD}; border: 1px solid {BORDER};
    border-radius: 8px; height: 16px; text-align: center; color: {TEXT};
    font-size: 11px; }
QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
    stop:0 {ACCENT_LIGHT}, stop:1 {ACCENT_DARK}); border-radius: 7px; }

QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: {BORDER}; border-radius: 5px;
    min-height: 30px; }
QScrollBar::handle:vertical:hover { background: {DIM}; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: {BORDER}; border-radius: 5px;
    min-width: 30px; }
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page,
QScrollBar::sub-page { height: 0; width: 0; background: transparent; }

QTableWidget { background: {CARD}; border: 1px solid {BORDER};
    border-radius: 10px; gridline-color: {BORDER}; color: {TEXT}; }
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected { background: {CARD_HOVER}; color: {ACCENT}; }
QHeaderView::section { background: {SIDEBAR}; color: {DIM}; border: none;
    border-bottom: 1px solid {BORDER}; padding: 8px; font-size: 12px;
    font-weight: 600; }

QMenu { background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 6px; }
QMenu::item { padding: 8px 24px; border-radius: 6px; color: {TEXT};
    font-size: 13px; }
QMenu::item:selected { background: {CARD_HOVER}; color: {ACCENT}; }
QMenu::separator { height: 1px; background: {BORDER}; margin: 6px 8px; }

QToolTip { background: {CARD}; color: {TEXT}; border: 1px solid {BORDER};
    padding: 6px; border-radius: 6px; font-size: 12px; }
QStatusBar { background: {SIDEBAR}; color: {DIM};
    border-top: 1px solid {BORDER}; }
QMessageBox { background: {BG}; }
QMessageBox QPushButton { min-width: 90px; }
"""


def qss() -> str:
    """Готовый stylesheet с подставленной палитрой."""
    result = _RAW_QSS
    for token, value in PALETTE.items():
        result = result.replace("{" + token + "}", value)
    return result


def apply(app) -> None:
    """Применяет тему к QApplication: загружает шрифты сайта + stylesheet.

    Шрифты (Golos Text, Unbounded) встроены в dlmm/fonts_data.py; если их
    не удалось загрузить, QSS сам откатится на Segoe UI через список
    font-family.
    """
    from PyQt6.QtCore import QByteArray
    from PyQt6.QtGui import QFont, QFontDatabase

    fonts_ok = True
    try:
        from dlmm import fonts_data
        for _name, data_b64 in fonts_data.FONTS.items():
            font_id = QFontDatabase.addApplicationFontFromData(
                QByteArray.fromBase64(data_b64.encode("ascii")))
            if font_id < 0:
                fonts_ok = False
    except Exception:
        fonts_ok = False

    app.setFont(QFont("Golos Text" if fonts_ok else "Segoe UI", 10))
    app.setStyleSheet(qss())


def gold_glow(widget, blur: int = 18, opacity: float = 90) -> None:
    """Золотое свечение вокруг виджета (аналог box-shadow на сайте).

    Например: 0 0 10px #c8a96a8c у золотых кнопок, 0 0 26px #c8a96a24
    у карточек. QGraphicsDropShadowEffect без смещения = ореол.
    """
    from PyQt6.QtGui import QColor, QGraphicsDropShadowEffect

    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, 0)
    color = QColor(ACCENT)
    color.setAlpha(int(opacity))
    effect.setColor(color)
    widget.setGraphicsEffect(effect)
