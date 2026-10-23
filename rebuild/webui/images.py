"""Animal pictures on a pastel tile: the same look for the demo cut-outs and for staff uploads.

* A transparent PNG (the demo animals) stands on a soft species-coloured tile with a shadow.
* A photo without transparency (an upload) is cropped to a square instead, so nothing is
  squashed or letter-boxed.
* A missing or unreadable file gives a tile with a paw print, never a broken image.

Tiles are returned as JPEG bytes (about a tenth of the PNG size); the page caches them.
No Streamlit import here, so the drawing is unit-tested on its own.
"""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps, UnidentifiedImageError

TILE = 600
# species: (top colour, bottom colour) of the tile's vertical gradient. All are tints of the
# original app's pinks (#fff7fb at the top), so pictures sit inside her palette; the species
# differ only slightly (warmer for dogs, lilac for cats, rosier for rabbits).
PASTELS: dict[str, tuple[tuple[int, int, int], tuple[int, int, int]]] = {
    "Dog": ((255, 247, 251), (253, 221, 230)),
    "Cat": ((255, 247, 251), (243, 221, 240)),
    "Rabbit": ((255, 247, 251), (250, 214, 232)),
}
DEFAULT_PASTEL = ((255, 247, 251), (255, 224, 238))


def resolve(image_path: str, root: Path, data_dir: Path) -> Path | None:
    """Where a stored image path lives: uploads/ beside the database, anything else in the app."""
    if not image_path:
        return None
    path = Path(image_path)
    if path.is_absolute() or ".." in path.parts:
        return None  # stored paths are always relative; refuse anything that escapes the folders
    base = data_dir if path.parts[0] == "uploads" else root
    full = base / path
    return full if full.is_file() else None


def _background(species: str, size: int) -> Image.Image:
    top, bottom = PASTELS.get(species, DEFAULT_PASTEL)
    gradient = Image.linear_gradient("L").resize((size, size))
    tile = Image.composite(Image.new("RGB", (size, size), bottom), Image.new("RGB", (size, size), top), gradient)
    glow = Image.new("L", (size, size), 0)
    ImageDraw.Draw(glow).ellipse((size * 0.12, size * 0.04, size * 0.88, size * 0.72), fill=120)
    return Image.composite(Image.new("RGB", (size, size), (255, 255, 255)), tile,
                           glow.filter(ImageFilter.GaussianBlur(size / 10)))


def _shadow(tile: Image.Image, animal: Image.Image, x: int, y: int) -> None:
    """A soft oval under the animal's feet so it stands on the tile instead of floating."""
    box = animal.getchannel("A").getbbox() or (0, 0, animal.width, animal.height)
    width = (box[2] - box[0]) * 0.8
    centre_x, feet_y = x + (box[0] + box[2]) / 2, y + box[3]
    mask = Image.new("L", tile.size, 0)
    ImageDraw.Draw(mask).ellipse((centre_x - width / 2, feet_y - 14, centre_x + width / 2, feet_y + 10), fill=70)
    tile.paste((60, 30, 60), mask=mask.filter(ImageFilter.GaussianBlur(9)))


def draw_paw(image: Image.Image, centre: tuple[float, float], size: float, colour: tuple[int, ...]) -> None:
    """A paw print: one large pad and four toes. Also used for the logo (docs/tools/make_images.py)."""
    draw = ImageDraw.Draw(image)
    cx, cy = centre
    draw.ellipse((cx - size * 0.17, cy - size * 0.02, cx + size * 0.17, cy + size * 0.24), fill=colour)
    for dx, dy in ((-0.2, -0.12), (-0.07, -0.22), (0.07, -0.22), (0.2, -0.12)):
        x, y = cx + dx * size, cy + dy * size
        draw.ellipse((x - size * 0.06, y - size * 0.075, x + size * 0.06, y + size * 0.075), fill=colour)


def tile(source: Path | None, species: str, size: int = TILE) -> bytes:
    """JPEG bytes of the animal on its tile (see the module docstring for the three cases)."""
    background = _background(species, size)
    picture = None
    if source is not None:
        try:
            picture = Image.open(source)
            picture.load()
        except (OSError, UnidentifiedImageError):
            picture = None
    if picture is None:
        draw_paw(background, (size / 2, size / 2), size, (255, 255, 255))  # placeholder
    elif picture.mode in ("RGBA", "LA") or "transparency" in picture.info:
        animal = picture.convert("RGBA")
        animal.thumbnail((size, size), Image.Resampling.LANCZOS)
        x, y = (size - animal.width) // 2, size - animal.height
        _shadow(background, animal, x, y)
        background.paste(animal, (x, y), animal)
    else:
        background = ImageOps.fit(ImageOps.exif_transpose(picture).convert("RGB"), (size, size),
                                  Image.Resampling.LANCZOS)
    out = io.BytesIO()
    background.save(out, "JPEG", quality=88, optimize=True, progressive=True)
    return out.getvalue()


def web_png(source: Path, max_side: int) -> bytes:
    """A transparent picture scaled down for the page (the home-page hero)."""
    picture = Image.open(source).convert("RGBA")
    picture.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    picture.save(out, "PNG", optimize=True)
    return out.getvalue()
