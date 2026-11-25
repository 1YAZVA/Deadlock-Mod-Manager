# Сборка: .exe и установщик Setup_DLMM.exe

## Что получится

| Артефакт | Как |
| --- | --- |
| `dist\DeadlockModManager\DeadlockModManager.exe` | PyInstaller (onedir, windowed, иконка) |
| `dist\installer\Setup_DLMM.exe` | Inno Setup поверх каталога PyInstaller |

`onedir` вместо `onefile`: мгновенный запуск и меньше ложных срабатываний
антивирусов; каталог целиком упаковывается в установщик.

## Требования

* Windows 10/11, Python 3.11+ (галочка «Add to PATH» при установке);
* [Inno Setup 6](https://jrsoftware.org/isdl.php) — только для установщика;
* интернет для pip (первый запуск).

## Шаг 1 — .exe одной командой

```bat
scripts\build_exe.bat
```

Скрипт сам: создаёт `.venv` → ставит `requirements-dev.txt` → генерирует
иконки (`tools\make_icons.py`) → запускает `pyinstaller build.spec`.

Ручной вариант:

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
python tools\make_icons.py
.venv\Scripts\pyinstaller --noconfirm --clean build.spec
```

Проверка: запустите `dist\DeadlockModManager\DeadlockModManager.exe` — окно
должно открыться без консоли, иконка .exe — эмблема «глаз в прицеле».

## Шаг 2 — установщик

```bat
iscc scripts\installer.iss
```

(если `iscc` не в PATH: `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" scripts\installer.iss`)

Что делает `Setup_DLMM.exe`:

* ставит в `%LOCALAPPDATA%\Programs\Deadlock Mod Manager` (без прав админа);
* ярлыки в «Пуск» и (по галочке) на рабочий стол;
* запись в «Установка и удаление программ» с иконкой;
* по галочке регистрирует протокол `deadlock-mod-manager://`
  (кнопка «Mod installer» на GameBanana открывает приложение);
* `CloseApplications=yes` — перед обновлением мягко закрывает запущенную копию;
* пользовательские данные в `%APPDATA%\DeadlockModManager` не удаляются.

## Шаг 3 — свой логотип (опционально)

```bat
python tools\make_icons.py путь\к\логотипу.png
```

Без аргумента скрипт использует встроенную эмблему «глаз в прицеле»
(`tools/logo_data.py`); с аргументом — обрежет ваше изображение в квадрат
и соберёт `assets/icon.png`, многоразмерный `assets/icon.ico` (16–256 px)
и `assets/logo.png` для шапки. После этого повторите шаги 1–2.

## Автоматическая сборка (CI)

Workflow `.github/workflows/build.yml` на windows-latest собирает `.exe`,
`Setup_DLMM.exe` и portable-zip и **сам публикует их в GitHub Releases** —
пользователю достаточно скачать готовый `Setup_DLMM.exe`, ему не нужно ставить
Python или собирать проект самостоятельно.

Запустить сборку с публикацией можно любым из способов:

* коммит в `main` со словом `[release]` в сообщении — CI соберёт и опубликует
  Release автоматически (тег `v<версия>` создаётся сам, версия берётся из
  `dlmm/__init__.py`);
* тег: `git tag v1.0.0 && git push origin v1.0.0`;
* кнопка **Run workflow** во вкладке Actions (`workflow_dispatch`).

Пуши в другие ветки и обычные коммиты без `[release]` — job просто
пропускается (skipped), минуты runners не тратятся.

Артефакты Release: `Setup_DLMM.exe` (обычный установщик) и
`DeadlockModManager-Portable-win64.zip` (portable). Во вкладке Actions оба
файла лежат как артефакт `Setup_DLMM` после каждого запуска.

## Подпись кода (опционально)

Без подписи SmartScreen показывает «подробнее → выполнить в любом случае».
С сертификатом (EV/OV) добавьте в конец workflow или локально перед iscc:

```bat
signtool sign /fd SHA256 /tr http://timestamp.digicert.com /td SHA256 ^
  /f cert.pfx /p <пароль> dist\installer\Setup_DLMM.exe
```

## FAQ

**Антивирус ругается на собранный .exe.** Частое следствие PyInstaller:
собирайте на свежем Python, не включайте UPX (в `build.spec` отключён),
подпишите файл или отправьте образец в «ложные срабатывания» своего антивируса.

**Ошибка «assets/icon.ico not found».** Сначала выполните
`python tools\make_icons.py` — иконки собираются из встроенного фирменного
логотипа (`tools/logo_data.py`, эмблема «глаз в прицеле» в base64) и не
хранятся в git в бинарном виде.

**Приложение запускается, но каталог пуст.** Проверьте «Настройки → Проверить
подключение к API»; при необходимости укажите зеркало или базовый URL apiv11.
