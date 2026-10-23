"""Number the annotation boxes on her nine annotated screen designs, for the design choices tables.

Her designs are taken unchanged from her master document. An annotation box is a pink region with
a dark border all round it; pink parts of the mock-up itself (side menu, cards, buttons) have no
such border, so they are left alone. Each box gets a numbered badge at its top-left corner, in the
order left column, middle, right column, each read top to bottom.

    python docs/tools/number_callouts.py <master.docx> docs/img/designs
"""

import json
import sys
import zipfile
from collections import deque
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Her annotated designs, by the relationship id each has in her master document.
DESIGNS = {
    "login": "rId39", "register": "rId41", "admin-list": "rId44", "admin-add": "rId46",
    "home": "rId49", "browse": "rId52", "profile": "rId54", "questionnaire": "rId57", "matches": "rId59",
}
FONT = Path(__file__).resolve().parents[2] / "static" / "fonts" / "Nunito.ttf"
BADGE = (194, 54, 115)  # her deeper pink, #c23673
PAD, RADIUS = 36, 26


def _regions(mask: np.ndarray) -> list[tuple[int, int, int, int, int]]:
    """Bounding box and size of every 4-connected region of True cells."""
    height, width = mask.shape
    seen = np.zeros_like(mask, bool)
    found = []
    for y in range(height):
        for x in range(width):
            if mask[y, x] and not seen[y, x]:
                queue, seen[y, x], size = deque([(y, x)]), True, 0
                y0 = y1 = y
                x0 = x1 = x
                while queue:
                    cy, cx = queue.popleft()
                    size += 1
                    y0, y1, x0, x1 = min(y0, cy), max(y1, cy), min(x0, cx), max(x1, cx)
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < height and 0 <= nx < width and mask[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            queue.append((ny, nx))
                found.append((x0, y0, x1 + 1, y1 + 1, size))
    return found


def _bordered(dark: np.ndarray, x0: int, y0: int, x1: int, y1: int, reach: int = 9) -> bool:
    """True when a dark line runs along all four sides just outside the region."""
    top = dark[max(0, y0 - reach):y0 + 2, x0 + 10:x1 - 10].any(axis=0)
    bottom = dark[y1 - 2:y1 + reach, x0 + 10:x1 - 10].any(axis=0)
    left = dark[y0 + 10:y1 - 10, max(0, x0 - reach):x0 + 2].any(axis=1)
    right = dark[y0 + 10:y1 - 10, x1 - 2:x1 + reach].any(axis=1)
    return all(side.size and side.mean() >= 0.85 for side in (top, bottom, left, right))


def annotation_boxes(image: Image.Image, step: int = 3) -> list[tuple[int, int, int, int]]:
    pixels = np.asarray(image.convert("RGB")).astype(int)
    dark = pixels.sum(axis=2) < 300
    small = pixels[::step, ::step]
    red, green, blue = small[..., 0], small[..., 1], small[..., 2]
    pink = (red >= 225) & (blue >= 210) & (red - green >= 6)
    boxes = []
    for x0, y0, x1, y1, size in _regions(pink):
        box = (x0 * step, y0 * step, x1 * step, y1 * step)
        wide, tall = box[2] - box[0], box[3] - box[1]
        if wide >= 150 and tall >= 90 and size / ((x1 - x0) * (y1 - y0)) >= 0.45 and _bordered(dark, *box):
            boxes.append(box)
    third = image.width / 3
    column = lambda b: 0 if (b[0] + b[2]) / 2 < third else 2 if (b[0] + b[2]) / 2 > 2 * third else 1  # noqa: E731
    return sorted(boxes, key=lambda b: (column(b), b[1]))


def numbered(image: Image.Image, boxes: list[tuple[int, int, int, int]]) -> Image.Image:
    canvas = Image.new("RGB", (image.width + 2 * PAD, image.height + 2 * PAD), "white")
    canvas.paste(image.convert("RGB"), (PAD, PAD))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(str(FONT), 34)
    font.set_variation_by_axes([900]) if hasattr(font, "set_variation_by_axes") else None
    for number, (x0, y0, _, _) in enumerate(boxes, 1):
        cx, cy = x0 + PAD - 4, y0 + PAD - 4
        draw.ellipse((cx - RADIUS - 3, cy - RADIUS - 3, cx + RADIUS + 3, cy + RADIUS + 3), fill="white")
        draw.ellipse((cx - RADIUS, cy - RADIUS, cx + RADIUS, cy + RADIUS), fill=BADGE)
        draw.text((cx, cy - 1), str(number), fill="white", font=font, anchor="mm")
    return canvas


def main(master: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(master) as docx:
        rels = docx.read("word/_rels/document.xml.rels").decode()
        record = {}
        for name, rid in DESIGNS.items():
            target = rels.split(f'Id="{rid}"')[1].split('Target="')[1].split('"')[0]
            image = Image.open(BytesIO(docx.read(f"word/{target}")))
            boxes = annotation_boxes(image)
            numbered(image, boxes).save(out / f"{name}.png")
            record[name] = boxes
            print(f"{name}: {len(boxes)} callouts")
    (out / "callouts.json").write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
