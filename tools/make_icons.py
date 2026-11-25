# -*- coding: utf-8 -*-
"""Сборка иконок приложения из фирменного логотипа «глаз в прицеле».

По умолчанию логотип берётся из tools/logo_data.py — эмблема встроена
в репозиторий в base64 (256x256, палитра 256 цветов), поэтому иконки
собираются одинаково локально и на CI, без бинарных файлов в git.
Можно подставить и свой файл логотипа:

    python tools/make_icons.py                # встроенный фирменный логотип
    python tools/make_icons.py my_logo.png    # свой логотип

Результат (в assets/):
    icon.png   256x256 RGBA — иконка окна и трея
    icon.ico   16..256 px    — иконка .exe (PyInstaller / Inno Setup)
    logo.png   256x256 RGBA — логотип в шапке (в интерфейсе — 44x44)
"""
from __future__ import annotations

import base64
import io
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
CANVAS = 256


def embedded_logo():
    """Декодирует встроенный фирменный логотип в RGBA CANVAS x CANVAS."""
    from PIL import Image

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from logo_data import LOGO_B64  # type: ignore

    raw = base64.b64decode(LOGO_B64)
    image = Image.open(io.BytesIO(raw)).convert("RGBA")
    if image.size != (CANVAS, CANVAS):
        image = image.resize((CANVAS, CANVAS), Image.LANCZOS)
    return image


def square_fit(source: Path, size: int):
    """Вписывает произвольное изображение в квадрат size x size."""
    from PIL import Image

    image = Image.open(source).convert("RGBA")
    bbox = image.getchannel("A").getbbox() or (0, 0, image.width, image.height)
    image = image.crop(bbox)
    side = max(image.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(image, ((side - image.width) // 2, (side - image.height) // 2))
    return canvas.resize((size, size), Image.LANCZOS)


def save_ico(image, path: Path) -> None:
    """Многоразмерный .ico: каждый кадр уменьшается LANCZOS явно."""
    from PIL import Image

    frames = [image]
    frames += [
        image.resize((s, s), Image.LANCZOS)
        for s in sorted(ICO_SIZES, reverse=True)
        if s < image.width
    ]
    frames[0].save(
        path,
        format="ICO",
        sizes=[(s, s) for s in ICO_SIZES],
        append_images=frames[1:],
    )


def main(argv: list[str]) -> int:
    # На Windows (CI-раннер, cp1252/cp437) кириллица в print() вызывает
    # UnicodeEncodeError и роняет скрипт ПОСЛЕ успешной сборки — переключаем
    # потоки вывода в UTF-8 явно.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    try:
        from PIL import Image  # noqa: F401 — проверка наличия Pillow
    except ImportError:
        print("Требуется Pillow: pip install pillow")
        return 1

    ASSETS.mkdir(exist_ok=True)
    base = square_fit(Path(argv[1]), CANVAS) if len(argv) > 1 else embedded_logo()

    # 1) icon.png — иконка окна и трея
    icon_path = ASSETS / "icon.png"
    base.save(icon_path)

    # 2) icon.ico — все размеры для Windows (exe, ярлыки, трей)
    save_ico(base, ASSETS / "icon.ico")

    # 3) logo.png — логотип в шапке приложения
    logo_path = ASSETS / "logo.png"
    base.save(logo_path)

    print(f"Готово:\n  {icon_path}\n  {ASSETS / 'icon.ico'}\n  {logo_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
