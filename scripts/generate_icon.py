"""
Генерирует оригинальную иконку приложения (icon.ico) программно через Pillow —
без внешних файлов/лицензий. Используется в CI перед сборкой .exe.

Идея иконки: синий конверт (почта) со стрелкой пересылки на круглом фоне
-> визуально отражает "пересылка почты".
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"
SIZE = 256

NAVY = (17, 45, 78, 255)
BLUE = (33, 99, 175, 255)
LIGHT = (235, 244, 255, 255)
WHITE = (255, 255, 255, 255)
GOLD = (240, 180, 60, 255)


def draw_envelope(draw: ImageDraw.ImageDraw, box, fill, outline, width):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle(box, radius=10, fill=fill, outline=outline, width=width)
    # клапан конверта (галочка сверху)
    draw.line([x0, y0, (x0 + x1) / 2, (y0 + y1) / 2], fill=outline, width=width)
    draw.line([x1, y0, (x0 + x1) / 2, (y0 + y1) / 2], fill=outline, width=width)


def draw_forward_arrow(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float):
    length = int(46 * scale)
    thickness = int(10 * scale)
    # хвост стрелки
    draw.rounded_rectangle(
        [cx - length, cy - thickness // 2, cx + int(10 * scale), cy + thickness // 2],
        radius=thickness // 2, fill=GOLD
    )
    # наконечник (треугольник)
    tip = [
        (cx + int(10 * scale), cy - int(24 * scale)),
        (cx + int(10 * scale), cy + int(24 * scale)),
        (cx + int(40 * scale), cy),
    ]
    draw.polygon(tip, fill=GOLD)


def build_base_image() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = SIZE // 2, SIZE // 2

    # фон — круг в градиенте синего (упрощённо: два круга)
    draw.ellipse([4, 4, SIZE - 4, SIZE - 4], fill=BLUE)
    draw.ellipse([14, 14, SIZE - 14, SIZE - 14], fill=NAVY)

    # конверт поверх, светлый
    env_w, env_h = 130, 90
    box = [cx - env_w // 2, cy - env_h // 2 - 10, cx + env_w // 2, cy + env_h // 2 - 10]
    draw_envelope(draw, box, fill=LIGHT, outline=WHITE, width=6)

    # стрелка пересылки (forward) поверх правого края конверта
    draw_forward_arrow(draw, cx + env_w // 2 + 10, cy + env_h // 2 + 30, scale=1.0)

    return img


def main():
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    base = build_base_image()
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    base.save(OUT_PATH, format="ICO", sizes=sizes)
    print(f"Icon saved: {OUT_PATH}")


if __name__ == "__main__":
    main()
