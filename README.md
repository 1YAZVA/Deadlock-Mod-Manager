# Deadlock Mod Manager

Менеджер модов для **Deadlock** (Valve, Steam AppID `1422450`) с каталогом
[GameBanana](https://gamebanana.com) (Game ID `20948`), установкой `.vpk` в
один клик, запуском игры **с модами / без модов (Vanilla)** и работой
в системном трее.

> Тёмный интерфейс в стиле Deadlock и deadlockru.ru: чёрно-серый фон,
> мятно-зелёный и бирюзовый акценты, фирменная эмблема «глаз в прицеле» — в
> шапке, иконке `.exe` и в трее.

![CI](https://github.com/1YAZVA/Deadlock-Mod-Manager/actions/workflows/build.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Возможности

| Блок | Что умеет |
| --- | --- |
| Каталог GameBanana | лента всех модов Deadlock (пагинация), превью, автор, категория/герой, лайки и просмотры, статус «установлен/не установлен», поиск по загруженным карточкам |
| Установка модов | скачивание файла мода (прогресс, скорость, отмена), копирование `.vpk` в `<игра>/game/citadel/addons/`, метаданные в локальной базе |
| Управление | включение/отключение (`.vpk` ↔ `.vpk.off`), удаление, открытие папки модов |
| Запуск игры | кнопки **«Играть с модами»** и **«Vanilla (без модов)»**: перед Vanilla-запуском папка `addons` временно переименовывается в `addons_vanilla_backup`, после выхода из игры (отслеживание процесса `citadel.exe`) моды возвращаются автоматически |
| Системный трей | закрытие окна сворачивает приложение в трей; меню: открыть, запустить с модами, запустить Vanilla, вернуть моды, выход; уведомления |
| Настройки | путь к игре (автоопределение через реестр Steam + `libraryfolders.vdf`), зеркало загрузок, сворачивание в трей, автозапуск с Windows, запуск игры после установки мода |
| Установка «в 1 клик» | регистрируется протокол `deadlock-mod-manager://` — кнопка «Mod installer» на странице мода GameBanana открывает приложение и сразу ставит мод |
| Установщик | `Setup_DLMM.exe` (Inno Setup): ярлыки, запись в «Установка и удаление программ», иконка из логотипа |

## Быстрый старт (игроку)

1. Скачайте `Setup_DLMM.exe` со страницы
   [Releases](https://github.com/1YAZVA/Deadlock-Mod-Manager/releases)
   (или соберите сами — см. [docs/BUILD.md](docs/BUILD.md)).
2. Установите (без прав администратора, в `%LOCALAPPDATA%\Programs`).
3. Запустите — путь к игре определится автоматически; в противном случае
   укажите папку `steamapps/common/Citadel` на странице «Настройки».
4. Найдите мод в каталоге → **Установить** → **Играть с модами**.

## Быстрый старт (разработчику)

```bat
git clone https://github.com/1YAZVA/Deadlock-Mod-Manager.git
cd Deadlock-Mod-Manager
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python run.py
```

Сборка `.exe` и установщика: [docs/BUILD.md](docs/BUILD.md) или одной командой
`scripts\build_exe.bat` (+ `iscc scripts\installer.iss`).

## Стек и почему так

**Python 3.11+ / PyQt6** — выбран как лучший баланс для этой задачи:

* `QSystemTrayIcon` встроен в PyQt6 — трей без сторонних библиотек и без
  потоковых костылей `pystray` (меню и события живут в одном Qt-цикле);
* `requests` + `QThread` — сеть не блокирует UI;
* PyInstaller + Inno Setup — проверенный путь «скрипт → Setup_DLMM.exe»;
* Qt Style Sheets позволяют целиком перерисовать интерфейс в стиле Deadlock.

Альтернатива на C# WPF (.NET 8 + Hardcodet.NotifyIcon.Wpf) остаётся валидной,
но требует .NET SDK и WiX/MSI-инфраструктуры; PyQt6-вариант короче и быстрее
в сопровождении. Границы модулей (API / файлы / трей / UI) не привязаны к GUI-
фреймворку — при желании ядро переносится на WPF без переписывания логики.

## Архитектура

```
Deadlock-Mod-Manager/
├── run.py                     # точка входа
├── dlmm/
│   ├── main.py                # QApplication, один экземпляр, трей, mmdl://
│   ├── config.py              # константы игры + настройки (%APPDATA%)
│   ├── paths.py               # ресурсы (PyInstaller-совместимые)
│   ├── api/gamebanana.py      # клиент GameBanana apiv11 + скачивание
│   ├── core/
│   │   ├── steam.py           # реестр Steam, поиск игры, steam://rungameid
│   │   ├── mods.py            # .vpk: установка/вкл-выкл/Vanilla-бэкап
│   │   └── system.py          # автозапуск, протокол, Проводник
│   └── ui/                    # PyQt6: окно, страницы, тема, трей, воркеры
├── tools/make_icons.py        # эмблема «глаз в прицеле» → icon.ico
├── scripts/build_exe.bat      # venv + PyInstaller
├── scripts/installer.iss      # Inno Setup → Setup_DLMM.exe
└── .github/workflows/build.yml# CI: тег v* → Release с установщиком
```

Подробности: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) ·
макет и палитра: [docs/UI_UX.md](docs/UI_UX.md) ·
сборка: [docs/BUILD.md](docs/BUILD.md).

## Данные приложения

| Файл | Назначение |
| --- | --- |
| `%APPDATA%\DeadlockModManager\config.json` | настройки |
| `%APPDATA%\DeadlockModManager\installed.json` | метаданные установленных модов (id GameBanana, автор, дата) |
| `%APPDATA%\DeadlockModManager\dlmm.log` | лог |
| `<игра>\game\citadel\addons\` | сами `.vpk` |
| `<игра>\game\citadel\addons_vanilla_backup\` | временная папка Vanilla-режима |

## Замечания

* Моды устанавливаются в игру «как есть» — ставьте только то, чему доверяете.
* Проект не связан с Valve и GameBanana; Deadlock — торговая марка Valve.
* Лицензия — [MIT](LICENSE).

## Roadmap

- [ ] серверный поиск и сортировки (уточнить параметры `Util/Search/Results`)
- [ ] фильтр по категориям/героям
- [ ] проверка md5 файла после скачивания (`_sMd5Checksum` уже приходит из API)
- [ ] автообновление приложения
- [ ] подсветка конфликтующих модов (два мода на одного героя)
