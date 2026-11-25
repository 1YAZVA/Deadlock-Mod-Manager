# -*- coding: utf-8 -*-
"""Генерация иконок приложения: логотип «глаз в шестерёнке» (мята/бирюза).

Использование:
    python tools/make_icons.py                # нарисовать логотип и собрать icon.ico
    python tools/make_icons.py my_logo.png    # взять готовый логотип и собрать icon.ico

Результат (в assets/):
    icon.png   256x256, прозрачный фон — иконка окна и трея
    icon.ico   16..256 px — иконка .exe (PyInstaller/Inno Setup)
    logo.png   512x512 на тёмной подложке — логотип в шапке приложения

Если у вас есть «родной» логотип (глаз в шестерёнке) — передайте его путь
аргументом: скрипт сам приведёт его к нужным размерам и формату.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]

MINT = (67, 226, 155, 255)      # #43E29B
TEAL = (43, 217, 199, 255)      # #2BD9C7
DARK = (12, 15, 18, 255)        # #0C0F12
WHITE = (233, 237, 242, 255)    # #E9EDF2


def _rotate(points, cx, cy, deg):
    rad = math.radians(deg)
    cos, sin = math.cos(rad), math.sin(rad)
    return [
        (cx + (x - cx) * cos - (y - cy) * sin, cy + (x - cx) * sin + (y - cy) * cos)
        for x, y in points
    ]


def draw_default_logo(size: int = 512, on_background: bool = False):
    """Рисует логотип: бирюзовая шестерёнка + мятный глаз-зрачок."""
    from PIL import Image, ImageDraw

    if on_background:
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        corner = int(size * 0.22)
        draw.rounded_rectangle(
            (0, 0, size - 1, size - 1), radius=corner, fill=DARK
        )
        image_inner = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    else:
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        image_inner = image
    draw = ImageDraw.Draw(image_inner)

    cx = cy = size / 2

    # --- шестерёнка: 8 зубьев + кольцо
    ring_outer = size * 0.40
    ring_inner = size * 0.29
    tooth_len = size * 0.09
    tooth_w = size * 0.13
    for i in range(8):
        angle = i * 45
        base = [
            (cx - tooth_w / 2, cy - ring_inner),
            (cx + tooth_w / 2, cy - ring_inner),
            (cx + tooth_w / 2, cy - ring_outer - tooth_len),
            (cx - tooth_w / 2, cy - ring_outer - tooth_len),
        ]
        draw.polygon(_rotate(base, cx, cy, angle), fill=TEAL)
    draw.ellipse(
        (cx - ring_outer, cy - ring_outer, cx + ring_outer, cy + ring_outer),
        fill=TEAL,
    )
    draw.ellipse(
        (cx - ring_inner, cy - ring_inner, cx + ring_inner, cy + ring_inner),
        fill=DARK if on_background else (0, 0, 0, 0),
    )

    # --- глаз: миндалевидное веко, мятная радужка, тёмный зрачок, блик
    eye_w, eye_h = size * 0.23, size * 0.115
    draw.ellipse(
        (cx - eye_w, cy - eye_h, cx + eye_w, cy + eye_h),
        fill=WHITE,
    )
    iris_r = eye_h * 0.92
    draw.ellipse(
        (cx - iris_r, cy - iris_r, cx + iris_r, cy + iris_r),
        fill=MINT,
    )
    pupil_r = iris_r * 0.55
    draw.ellipse(
        (cx - pupil_r, cy - pupil_r, cx + pupil_r, cy + pupil_r),
        fill=DARK,
    )
    glint_r = pupil_r * 0.32
    draw.ellipse(
        (cx + pupil_r * 0.35, cy - pupil_r * 0.45,
         cx + pupil_r * 0.35 + glint_r, cy - pupil_r * 0.45 + glint_r),
        fill=WHITE,
    )

    if on_background:
        image.alpha_composite(image_inner)
    return image


def square_fit(source: Path, size: int):
    """Вписывает произвольное изображение в квадрат size x size."""
    from PIL import Image

    image = Image.open(source).convert("RGBA")
    side = min(image.size)
    left = (image.width - side) // 2
    top = (image.height - side) // 2
    image = image.crop((left, top, left + side, top + side))
    return image.resize((size, size), Image.LANCZOS)


def main(argv: list[str]) -> int:
    try:
        from PIL import Image, ImageDraw  # noqa: F401 — проверка наличия Pillow
    except ImportError:
        print("Требуется Pillow: pip install pillow")
        return 1

    ASSETS.mkdir(exist_ok=True)
    source = Path(argv[1]) if len(argv) > 1 else None

    # 1) icon.png — прозрачная иконка 256x256
    icon = square_fit(source, 256) if source else draw_default_logo(256)
    icon_path = ASSETS / "icon.png"
    icon.save(icon_path)

    # 2) icon.ico — все размеры для Windows (exe, ярлыки, трей)
    if source:
        base = square_fit(source, 256)
    else:
        base = icon
    base.save(ASSETS / "icon.ico", sizes=[(s, s) for s in ICO_SIZES])

    # 3) logo.png — крупный логотип на тёмной подложке для шапки
    if source:
        logo = square_fit(source, 512)
        backdrop = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        mask = Image.new("L", (512, 512), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle((0, 0, 511, 511), radius=112, fill=255)
        backdrop.paste(DARK, (0, 0, 512, 512), mask)
        backdrop.alpha_composite(logo)
        logo = backdrop
    else:
        logo = draw_default_logo(512, on_background=True)
    logo.save(ASSETS / "logo.png")

    print(f"Готово:\n  {icon_path}\n  {ASSETS / 'icon.ico'}\n  {ASSETS / 'logo.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
