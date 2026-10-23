"""Make the app's pictures: clean transparent animals, the log-in hero and the paw badge.

    .venv/bin/python docs/tools/make_images.py [path/to/app/assets/animals]

Round 1 flattened these onto black JPEGs, which left a black square and dark fringes on a
pastel page. This keeps the transparency instead:

* every source is trimmed to the animal, padded to a square and resized to 600 x 600;
* the animal stands near the bottom edge so the page can draw a soft "ground" under it;
* milo.png has no alpha channel (a grey-and-white checkerboard was painted into the pixels),
  so the checkerboard reachable from the border is removed and the edge is feathered by 1 px;
* static/hero.png is a dog, a cat and a rabbit side by side for the log-in panel, reduced to
  256 colours so the page loads quickly;
* static/paw-badge.png is the app badge (a white paw on the original app's pink gradient,
  #f985b2 to #d93679), shown in the menu and on the log-in panel.

static/ is served by Streamlit at app/static/ (server.enableStaticServing in config.toml).

The pastel tile behind each animal is drawn when the page shows it (webui/images.py), so a
photo uploaded by staff gets the same treatment.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from webui.images import draw_paw  # noqa: E402  (the tile placeholder uses the same paw)

SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "app" / "assets" / "animals"
OUT = ROOT / "assets" / "animals"
SIZE = 600            # output square, in pixels
MARGIN = 0.07         # empty space around the animal, as a share of SIZE
HERO = ("luna", "milo", "poppy")  # dog, cat, rabbit
STATIC = ROOT / "static"
BADGE_TOP, BADGE_BOTTOM = (249, 133, 178), (217, 54, 121)  # #f985b2 and #d93679, her palette


def checkerboard_alpha(rgb: Image.Image) -> Image.Image:
    """Alpha mask for an image whose 'transparent' background is a painted checkerboard.

    A pixel can be background if it is a light grey or white (R, G and B within 8 of each other,
    brightness 196 or more). Only candidates connected to the border are removed, so
    white fur inside the black outline is kept.
    """
    px = np.asarray(rgb, dtype=np.int16)
    spread = px.max(axis=2) - px.min(axis=2)
    value = px.mean(axis=2)
    candidate = (spread <= 8) & (value >= 196)

    reached = np.zeros_like(candidate)
    reached[0, :], reached[-1, :], reached[:, 0], reached[:, -1] = (
        candidate[0, :], candidate[-1, :], candidate[:, 0], candidate[:, -1])
    while True:  # grow from the border through candidate pixels until nothing changes
        grown = reached.copy()
        grown[1:, :] |= reached[:-1, :]
        grown[:-1, :] |= reached[1:, :]
        grown[:, 1:] |= reached[:, :-1]
        grown[:, :-1] |= reached[:, 1:]
        grown &= candidate
        if (grown == reached).all():
            break
        reached = grown

    alpha = Image.fromarray(np.where(reached, 0, 255).astype(np.uint8))
    # Shrink the animal by one pixel, then soften, so no light rim is left outside the outline.
    return alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))


def load_cutout(path: Path) -> Image.Image:
    image = Image.open(path)
    if image.mode == "RGBA":
        return image
    rgb = image.convert("RGB")
    rgba = rgb.convert("RGBA")
    rgba.putalpha(checkerboard_alpha(rgb))
    return rgba


def fit(cutout: Image.Image, size: int = SIZE, margin: float = MARGIN) -> Image.Image:
    """Trim to the animal, scale it into the square and stand it near the bottom edge."""
    box = cutout.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    animal = cutout.crop(box)
    room = int(size * (1 - 2 * margin))
    scale = room / max(animal.size)
    animal = animal.resize((max(1, round(animal.width * scale)), max(1, round(animal.height * scale))),
                           Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    x = (size - animal.width) // 2
    y = size - int(size * margin) - animal.height
    canvas.alpha_composite(animal, (x, y))
    return canvas


def hero(cutouts: dict[str, Image.Image]) -> Image.Image:
    """Three animals in a row, the middle one slightly in front, on a transparent canvas."""
    width, height = 1100, 640
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dog, cat, rabbit = HERO
    # name, height as a share of the canvas, left edge as a share of the free width
    placements = ((dog, 0.94, 0.0), (cat, 0.82, 1.0), (rabbit, 0.56, 0.5))  # rabbit last = in front
    for name, scale, across in placements:
        side = int(height * scale)
        animal = fit(cutouts[name], SIZE, 0.02).resize((side, side), Image.Resampling.LANCZOS)
        canvas.alpha_composite(animal, (int((width - side) * across), height - side))
    return canvas


def badge(size: int) -> Image.Image:
    """A rounded square in the pink gradient with a white paw: the app badge."""
    gradient = Image.linear_gradient("L").rotate(45, expand=False).resize((size, size))
    fill = Image.composite(Image.new("RGB", (size, size), BADGE_BOTTOM), Image.new("RGB", (size, size), BADGE_TOP), gradient)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=size * 0.3, fill=255)
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    icon.paste(fill, mask=mask)
    draw_paw(icon, (size / 2, size * 0.53), size * 0.95, (255, 255, 255))
    return icon


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cutouts = {}
    for path in sorted(SOURCE.glob("*.png")):
        cutout = load_cutout(path)
        cutouts[path.stem] = cutout
        fit(cutout).save(OUT / f"{path.stem}.png", optimize=True)
        print(f"{path.stem:8} {'alpha kept' if Image.open(path).mode == 'RGBA' else 'checkerboard removed'}")
    hero(cutouts).quantize(256, method=Image.Quantize.FASTOCTREE).save(STATIC / "hero.png", optimize=True)
    badge(144).save(STATIC / "paw-badge.png", optimize=True)
    print(f"{len(cutouts)} animals, static/hero.png and static/paw-badge.png written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
