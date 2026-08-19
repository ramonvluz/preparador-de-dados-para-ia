from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = PROJECT_ROOT / "src" / "preparador_dados_ia" / "assets"


def main() -> None:
    size = 1024
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (52, 52, 972, 972),
        radius=210,
        fill="#146B5C",
    )
    draw.rounded_rectangle(
        (238, 154, 744, 852),
        radius=62,
        fill="#FFFFFF",
    )
    draw.polygon(
        ((608, 154), (744, 290), (608, 290)),
        fill="#BFE5DA",
    )

    for y, width in ((390, 332), (500, 274), (610, 214)):
        draw.rounded_rectangle(
            (330, y, 330 + width, y + 34),
            radius=17,
            fill="#146B5C",
        )

    sparkle = [
        (776, 610),
        (812, 704),
        (906, 740),
        (812, 776),
        (776, 870),
        (740, 776),
        (646, 740),
        (740, 704),
    ]
    draw.polygon(sparkle, fill="#F4C95D")
    draw.ellipse((742, 706, 810, 774), fill="#FFF4C4")

    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    png = image.resize((512, 512), Image.Resampling.LANCZOS)
    png.save(ASSET_DIR / "app_icon.png", optimize=True)
    image.save(
        ASSET_DIR / "app_icon.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


if __name__ == "__main__":
    main()
