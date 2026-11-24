#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Точка входа Deadlock Mod Manager.

Запуск из исходников:  python run.py
Сборка в .exe:         scripts/build_exe.bat  (см. docs/BUILD.md)
"""
import sys

from dlmm.main import main

if __name__ == "__main__":
    sys.exit(main())
