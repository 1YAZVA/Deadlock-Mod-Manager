# -*- coding: utf-8 -*-
"""Тема оформления в стиле Deadlock: тёмный фон, мятные и бирюзовые акценты.

Палитра (см. docs/UI_UX.md):
  фон      #0C0F12 / панели #10151B / карточки #151B22
  мята     #43E29B   бирюза #2BD9C7   текст #E9EDF2   приглушённый #8A95A3
"""
from __future__ import annotations

BG = "#0C0F12"          # общий фон
SIDEBAR = "#10151B"     # боковая панель, шапки
CARD = "#151B22"        # карточки, поля ввода
CARD_HOVER = "#1C2530"  # наведение
BORDER = "#242F3A"      # рамки
TEXT = "#E9EDF2"        # основной текст
DIM = "#8A95A3"         # вторичный текст
MINT = "#43E29B"        # мятно-зелёный акцент
TEAL = "#2BD9C7"        # бирюзовый акцент
DANGER = "#E5534B"      # удаление/ошибки
WARNING = "#E8B45A"     # предупреждения

PALETTE = {
    "BG": BG, "SIDEBAR": SIDEBAR, "CARD": CARD, "CARD_HOVER": CARD_HOVER,
    "BORDER": BORDER, "TEXT": TEXT, "DIM": DIM, "MINT": MINT, "TEAL": TEAL,
    "DANGER": DANGER, "WARNING": WARNING,
    "MINT_BRIGHT": "#5CF0B2", "TEAL_BRIGHT": "#4BE8D8",
    "ON_ACCENT": "#08130E",
}

_RAW_QSS = """
* { font-family: "Segoe UI", "Noto Sans", sans-serif; }

QMainWindow, QDialog { background: {BG}; color: {TEXT}; }
QLabel { background: transparent; color: {TEXT}; }
QLabel#logoTitle { color: {MINT}; font-size: 16px; font-weight: 700; letter-spacing: 1px; }
QLabel#logoSub   { color: {DIM};  font-size: 10px; letter-spacing: 5px; }
QLabel#h2        { font-size: 16px; font-weight: 600; color: {TEXT}; }
QLabel#dim       { color: {DIM}; font-size: 12px; }
QLabel#accent    { color: {MINT}; font-size: 12px; font-weight: 600; }
QLabel#warn      { color: {WARNING}; font-size: 12px; }
QLabel#preview   { background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px; }

QFrame#sidebar { background: {SIDEBAR}; border-right: 1px solid {BORDER}; }
QFrame#modCard { background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; }
QFrame#modCard:hover { border-color: {MINT}; }
QFrame#panel { background: {CARD}; border: 1px solid {BORDER}; border-radius: 12px; }

QPushButton { background: {CARD_HOVER}; color: {TEXT}; border: 1px solid {BORDER};
              border-radius: 8px; padding: 8px 14px; font-size: 13px; }
QPushButton:hover { border-color: {MINT}; }
QPushButton:pressed { background: {BORDER}; }
QPushButton:disabled { color: {DIM}; background: {CARD}; border-color: {BORDER}; }
QPushButton#primary { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                      stop:0 {MINT}, stop:1 {TEAL}); border: none;
                      color: {ON_ACCENT}; font-weight: 700; }
QPushButton#primary:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 {MINT_BRIGHT}, stop:1 {TEAL_BRIGHT}); }
QPushButton#primary:disabled { background: {BORDER}; color: {DIM}; }
QPushButton#danger { background: transparent; border: 1px solid {DANGER}; color: {DANGER}; }
QPushButton#danger:hover { background: rgba(229, 83, 75, 0.15); }
QPushButton#nav { text-align: left; padding: 10px 14px; border: none; border-radius: 8px;
                  color: {DIM}; font-size: 14px; background: transparent; }
QPushButton#nav:hover { color: {TEXT}; background: {CARD_HOVER}; }
QPushButton#nav:checked { color: {ON_ACCENT}; background: {MINT}; font-weight: 600; }
QPushButton#navBig { text-align: center; padding: 12px; font-size: 14px; border-radius: 10px; }

QLineEdit, QComboBox, QSpinBox { background: {CARD}; border: 1px solid {BORDER};
    border-radius: 8px; padding: 8px 10px; color: {TEXT};
    selection-background-color: {MINT}; selection-color: {ON_ACCENT}; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: {MINT}; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox::down-arrow { image: none; border-left: 5px solid transparent;
    border-right: 5px solid transparent; border-top: 6px solid {DIM}; margin-right: 8px; }
QComboBox QAbstractItemView { background: {CARD}; border: 1px solid {BORDER};
    color: {TEXT}; selection-background-color: {CARD_HOVER}; selection-color: {MINT}; }
QSpinBox::up-button, QSpinBox::down-button { background: {CARD_HOVER}; border: none; width: 18px; }
QSpinBox::up-arrow { border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-bottom: 5px solid {DIM}; }
QSpinBox::down-arrow { border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid {DIM}; }

QCheckBox { spacing: 8px; color: {TEXT}; font-size: 13px; background: transparent; }
QCheckBox::indicator { width: 18px; height: 18px; border: 1px solid {BORDER};
    border-radius: 5px; background: {CARD}; }
QCheckBox::indicator:hover { border-color: {MINT}; }
QCheckBox::indicator:checked { background: {MINT}; border-color: {MINT}; }

QProgressBar { background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px;
    height: 16px; text-align: center; color: {TEXT}; font-size: 11px; }
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
    stop:0 {MINT}, stop:1 {TEAL}); border-radius: 7px; }

QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: {BORDER}; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: {DIM}; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: {BORDER}; border-radius: 5px; min-width: 30px; }
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page
    { height: 0; width: 0; background: transparent; }

QTableWidget { background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px;
    gridline-color: {BORDER}; color: {TEXT}; }
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected { background: {CARD_HOVER}; color: {TEXT}; }
QHeaderView::section { background: {SIDEBAR}; color: {DIM}; border: none;
    border-bottom: 1px solid {BORDER}; padding: 8px; font-size: 12px; font-weight: 600; }

QMenu { background: {CARD}; border: 1px solid {BORDER}; border-radius: 10px; padding: 6px; }
QMenu::item { padding: 8px 24px; border-radius: 6px; color: {TEXT}; font-size: 13px; }
QMenu::item:selected { background: {CARD_HOVER}; color: {MINT}; }
QMenu::separator { height: 1px; background: {BORDER}; margin: 6px 8px; }

QToolTip { background: {CARD}; color: {TEXT}; border: 1px solid {BORDER};
    padding: 6px; border-radius: 6px; font-size: 12px; }
QStatusBar { background: {SIDEBAR}; color: {DIM}; border-top: 1px solid {BORDER}; }
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
    """Применяет тему к QApplication (шрифт + stylesheet)."""
    from PyQt6.QtGui import QFont

    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(qss())
