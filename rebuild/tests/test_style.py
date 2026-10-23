"""Accessibility checks on the page styling in webui/pawmatch_style.py, with no browser needed.

The rules come from WCAG 2.2 level AA: text needs a contrast ratio of at least 4.5:1 with what is
behind it, and no text is set below 12px. A gradient is checked at every colour in it, so the
lightest point of a pink panel counts; translucent highlights in a gradient (rgba) are skipped,
as they only lighten a corner that has no text. A translucent fill on its own is blended over
what is behind it. Text with no background of its own is checked against what
is behind it: the side menu's pink for anything in the menu, otherwise the pale pink page colour
(--pm-blush), the darker of page and card. A hover or focus rule that changes only the background
keeps the text colour of the control at rest, so that pair is checked too. Disabled buttons are
left out, as WCAG allows: they are not meant to be read as active controls.

The first two of those rules were added after the rendered audit (docs/tools/capture_screens.py)
found menu text and a hovered button that this file had passed.
"""

import re
from pathlib import Path

STYLE = Path(__file__).resolve().parents[1] / "webui" / "pawmatch_style.py"
CSS = re.sub(r"/\*.*?\*/", "", STYLE.read_text(encoding="utf-8"), flags=re.S).replace("{{", "{").replace("}}", "}")
HEX = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
RGBA = re.compile(r"rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\d.]+)\s*\)")
MIN_RATIO = 4.5
MIN_TEXT_PX = 12


def _rules() -> list[tuple[str, dict[str, str]]]:
    """Every innermost `selector { property: value; ... }` block, one entry per selector in a list."""
    found = []
    for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", CSS):
        declarations = {}
        for part in body.split(";"):
            name, colon, value = part.partition(":")
            if colon:
                declarations[name.strip().lower()] = value.replace("!important", "").strip()
        found += [(" ".join(selector.split()), declarations) for selector in selectors.split(",")]
    return found


RULES = _rules()
TOKENS = {name[2:]: value for selector, block in RULES if selector.endswith(":root")
          for name, value in block.items() if name.startswith("--")}


def _resolve(value: str) -> str:
    for _ in range(5):
        value = re.sub(r"var\(--([\w-]+)\)", lambda m: TOKENS.get(m.group(1), ""), value)
    return value


def _luminance(colour: str) -> float:
    colour = colour.lstrip("#")
    if len(colour) == 3:
        colour = "".join(c * 2 for c in colour)
    channels = [int(colour[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _blend(layer: tuple[str, str, str, str], under: str) -> str:
    """A translucent rgba() colour laid over a solid #rrggbb one."""
    alpha = float(layer[3])
    base = [int(under.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(int(top) * alpha + low * (1 - alpha)):02x}" for top, low in zip(layer[:3], base))


def contrast(first: str, second: str) -> float:
    light, dark = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def _text_colour(value: str) -> str | None:
    value = _resolve(value).strip().lower()
    if value in ("white", "#fff", "#ffffff"):
        return "#ffffff"
    match = HEX.fullmatch(value)
    return match.group(0) if match else None


STATES = re.compile(r":(?:hover|focus-visible|focus-within|focus|active)\b")
AT_REST = {selector: block["color"] for selector, block in RULES if "color" in block and not STATES.search(selector)}
SIDEBAR = next(HEX.findall(_resolve(block["background"])) for selector, block in RULES
               if selector == '[data-testid="stSidebar"]' and "background" in block)


def _page_behind(selector: str) -> list[str]:
    """What shows through text that has no background of its own."""
    return SIDEBAR if "sidebar" in selector.lower() else [TOKENS["pm-blush"]]


def low_contrast_text() -> list[str]:
    problems = []
    for selector, block in RULES:
        colour = block.get("color") or AT_REST.get(STATES.sub("", selector), "")
        text = _text_colour(colour) if ("color" in block or "background" in block) else None
        if text is None or ":disabled" in selector:
            continue
        background = _resolve(block.get("background", "") or block.get("background-color", ""))
        behind = HEX.findall(background)
        if not behind:
            page = [] if text == "#ffffff" else _page_behind(selector)
            fill = RGBA.findall(background)
            behind = [_blend(fill[0], colour) for colour in page] if fill else page
        for colour in behind:
            ratio = contrast(text, colour)
            if ratio < MIN_RATIO:
                problems.append(f"{selector[:70]}: {text} on {colour} is {ratio:.2f}:1")
    return problems


def small_text() -> list[str]:
    problems = []
    for selector, block in RULES:
        match = re.fullmatch(r"([\d.]+)(rem|em|px)", block.get("font-size", ""))
        if match:
            size = float(match.group(1)) * (1 if match.group(2) == "px" else 16)
            if size < MIN_TEXT_PX:
                problems.append(f"{selector[:70]}: {size:.1f}px")
    return problems


def test_the_palette_tokens_are_her_colours():
    assert TOKENS["pm-primary"] == "#d93679"
    assert [TOKENS[n] for n in ("pm-blush", "pm-cream", "pm-shell", "pm-mist")] == [
        "#fff0f6", "#fffafd", "#fff8fb", "#fff7fb"]
    assert (TOKENS["pm-text"], TOKENS["pm-ink"]) == ("#4b3f45", "#171318")


def test_contrast_measure_matches_wcag_examples():
    assert round(contrast("#000000", "#ffffff"), 1) == 21.0
    assert round(contrast("#767676", "#ffffff"), 2) == 4.54  # the lightest grey that passes on white


def test_every_text_colour_reaches_4_5_to_1():
    problems = low_contrast_text()
    assert not problems, f"{len(problems)} text colours below {MIN_RATIO}:1\n" + "\n".join(problems)


def test_no_text_is_smaller_than_12px():
    problems = small_text()
    assert not problems, f"{len(problems)} font sizes below {MIN_TEXT_PX}px\n" + "\n".join(problems)
