@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0.."

echo [1/4] Виртуальное окружение...
python -m venv .venv || goto :err
call .venv\Scripts\activate.bat

echo [2/4] Зависимости...
python -m pip install --upgrade pip
pip install -r requirements-dev.txt || goto :err

echo [3/4] Иконки (assets/icon.ico, logo.png)...
python tools\make_icons.py || goto :err

echo [4/4] Сборка .exe (PyInstaller)...
pyinstaller --noconfirm --clean build.spec || goto :err

echo.
echo ============================================================
echo  Готово:  dist\DeadlockModManager\DeadlockModManager.exe
echo  Установщик:  iscc scripts\installer.iss  -^>  dist\installer\Setup_DLMM.exe
echo ============================================================
pause
exit /b 0

:err
echo.
echo Сборка не удалась — смотрите сообщения выше.
pause
exit /b 1
