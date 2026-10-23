"""Build the NEA write-up, docs/PawMatch-NEA-opus.docx and its PDF, from her master and docs/nea/*.md.

    .venv/bin/python -m pytest -q --junitxml=docs/evidence/pytest-junit.xml
    .venv/bin/python docs/tools/make_diagrams.py && .venv/bin/python docs/tools/make_charts.py
    .venv/bin/python docs/tools/build_nea_v2.py [--no-pdf]

Her paragraphs, tables and images are copied from her master document by position (@her lines).
Everything new is written in docs/nea/*.md, in the small markdown dialect described in
docs/nea/README.md. Page references are Word PAGEREF fields, so a printed reference such as D24
always names the page the target is on, in Word and in the PDF.
"""

from __future__ import annotations

import ast
import copy
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass, field
from pathlib import Path

import docx
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Emu, Pt, RGBColor
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import nea_data  # noqa: E402  (tests, failures and measurements used by the directives)

NEA = ROOT / "docs" / "nea"
IMG = ROOT / "docs" / "img"
MASTER = ROOT.parents[1] / "NEA" / "kit" / "PawMatch-NEA-master.docx"
OUT = ROOT / "docs" / "PawMatch-NEA-opus.docx"
PARTS = ["front.md", "A-analysis.md", "D-design.md", "S-development.md", "E-evaluation.md", "X-appendices.md"]

FONT, MONO = "Nunito", "Courier New"
INK, MUTED = RGBColor(0x2B, 0x23, 0x27), RGBColor(0x6B, 0x5B, 0x63)
HEADINGS = {1: (20, "A92660"), 2: (15, "C23673"), 3: (12.5, "A92660"), 4: (11, "6B2D4A")}
BODY, TABLE, CAPTION, CODE = 10.5, 8, 8.5, 7.2
HEAD_FILL, CODE_FILL, LINE = "FBE3EE", "FFF7FB", "E3C3D3"
BOXES = {  # fill, accent
    "client": ("FFF3F8", "C23673"), "fail": ("FFF6E8", "B45309"), "fix": ("EFF8F2", "2F7D4F"),
    "note": ("F7F4F6", "8A7A82"), "verdict": ("F4F0FF", "6B46C1"), "change": ("EFF6FB", "2B6CB0"),
}
VERDICT_FILLS = {"pass": "DDF2E3", "passed": "DDF2E3", "met": "DDF2E3", "adopt": "DDF2E3", "yes": "DDF2E3",
                 "partly met": "FFF0CC", "partial": "FFF0CC", "adapt": "FFF0CC", "partly": "FFF0CC",
                 "fail": "FBDADA", "failed": "FBDADA", "not met": "FBDADA", "reject": "FBDADA", "no": "FBDADA"}
PAGE_W, PAGE_H, MARGIN = 11906, 16838, 1134  # A4 in twips, 2 cm margins
TEXT_W = PAGE_W - 2 * MARGIN
EMU_PER_TWIP = 635
MAX_IMAGE_H = Cm(23.0)
SKIP_PREFIXES = ("[TO WRITE]", "[HOW THIS DOCUMENT", "[NOTE]")


# ---------------------------------------------------------------- low-level helpers

def _el(tag: str, **attrs) -> OxmlElement:
    element = OxmlElement(tag)
    for name, value in attrs.items():
        element.set(qn(name), str(value))
    return element


def style_run(run, size=None, bold=None, italic=None, color=None, font=FONT) -> None:
    if font:
        run.font.name = font
        run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), font)
        run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:cs"), font)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color is not None:
        run.font.color.rgb = color if isinstance(color, RGBColor) else RGBColor.from_string(color)


def shade(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    for old in tc_pr.findall(qn("w:shd")):
        tc_pr.remove(old)
    tc_pr.append(_el("w:shd", **{"w:val": "clear", "w:color": "auto", "w:fill": fill}))


def cell_borders(cell, colour: str, left_size: int = 4, size: int = 4) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = _el("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        borders.append(_el(f"w:{side}", **{"w:val": "single", "w:sz": left_size if side == "left" else size,
                                           "w:space": 0, "w:color": colour}))
    tc_pr.append(borders)


def table_borders(table, colour: str = LINE) -> None:
    tbl_pr = table._tbl.tblPr
    borders = _el("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        borders.append(_el(f"w:{side}", **{"w:val": "single", "w:sz": 4, "w:space": 0, "w:color": colour}))
    tbl_pr.append(borders)


def set_widths(table, twips: list[int]) -> None:
    """Word reads the cell widths, LibreOffice reads the grid: set both."""
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    for old in tbl_pr.findall(qn("w:tblW")):
        tbl_pr.remove(old)
    tbl_pr.append(_el("w:tblW", **{"w:w": sum(twips), "w:type": "dxa"}))
    tbl_pr.append(_el("w:tblLayout", **{"w:type": "fixed"}))
    for col, width in zip(table._tbl.tblGrid.findall(qn("w:gridCol")), twips):
        col.set(qn("w:w"), str(width))
    for row in table.rows:
        for cell, width in zip(row.cells, twips):
            cell.width = Emu(width * EMU_PER_TWIP)


def repeat_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tr_pr.append(_el("w:tblHeader"))


def no_split(row) -> None:
    row._tr.get_or_add_trPr().append(_el("w:cantSplit"))


def spacing(paragraph, before: float = 0, after: float = 6, line: float | None = None) -> None:
    fmt = paragraph.paragraph_format
    fmt.space_before, fmt.space_after = Pt(before), Pt(after)
    if line:
        fmt.line_spacing = line


def keep_with_next(paragraph) -> None:
    paragraph.paragraph_format.keep_with_next = True


class Fields:
    """Bookmarks and the PAGEREF / PAGE fields that point at them."""

    def __init__(self):
        self.next_id = 50_000

    def bookmark(self, paragraph, name: str) -> None:
        self.next_id += 1
        start = _el("w:bookmarkStart", **{"w:id": self.next_id, "w:name": name})
        end = _el("w:bookmarkEnd", **{"w:id": self.next_id})
        p = paragraph._p
        ppr = p.find(qn("w:pPr"))
        (ppr.addnext if ppr is not None else lambda e: p.insert(0, e))(start)
        p.append(end)

    @staticmethod
    def field(paragraph, instruction: str, shown: str, size=None, bold=None, color=None) -> None:
        def run_with(child):
            run = paragraph.add_run()
            style_run(run, size=size, bold=bold, color=color)
            run._r.append(child)
            return run
        run_with(_el("w:fldChar", **{"w:fldCharType": "begin"}))
        instr = _el("w:instrText", **{"xml:space": "preserve"})
        instr.text = f" {instruction} "
        run_with(instr)
        run_with(_el("w:fldChar", **{"w:fldCharType": "separate"}))
        shown_run = paragraph.add_run(shown)
        style_run(shown_run, size=size, bold=bold, color=color)
        run_with(_el("w:fldChar", **{"w:fldCharType": "end"}))


# ---------------------------------------------------------------- her master: copying

def tidy_copy(element, unbold: bool):
    """A copy of one of her body elements, fitted to a normal A4 page."""
    el = copy.deepcopy(element)
    for ppr in el.iter(qn("w:pPr")):
        for tag in ("w:sectPr", "w:ind", "w:framePr", "w:pageBreakBefore"):
            for found in ppr.findall(qn(tag)):
                ppr.remove(found)
    for br in list(el.iter(qn("w:br"))):
        if br.get(qn("w:type")) == "page":
            br.getparent().remove(br)
    for marker in list(el.iter(qn("w:lastRenderedPageBreak"))):
        marker.getparent().remove(marker)
    for size in el.iter(qn("w:sz")):  # her 12 pt body text, as 11 pt like the rest of the document
        if size.get(qn("w:val")) == "24":
            size.set(qn("w:val"), "22")
    paragraphs = [el] if el.tag == qn("w:p") else list(el.iter(qn("w:p")))
    for p in paragraphs:
        text = "".join(t.text or "" for t in p.iter(qn("w:t")))
        ppr = p.find(qn("w:pPr"))
        if len(text) > 120 and ppr is not None:
            jc = ppr.find(qn("w:jc"))
            if jc is not None and jc.get(qn("w:val")) in ("center", "both", "distribute"):
                jc.set(qn("w:val"), "left")
        runs = list(p.iter(qn("w:r")))
        if unbold and len(text) > 90 and runs and all(r.find(qn("w:rPr") + "/" + qn("w:b")) is not None
                                                      for r in runs if (r.findtext(qn("w:t")) or "").strip()):
            for r in runs:
                rpr = r.find(qn("w:rPr"))
                for tag in ("w:b", "w:bCs"):
                    for found in (rpr.findall(qn(tag)) if rpr is not None else []):
                        rpr.remove(found)
    if el.tag == qn("w:tbl"):
        fit_table(el)
    for drawing in el.iter(qn("wp:inline")):
        fit_drawing(drawing, Emu(TEXT_W * EMU_PER_TWIP))
    return el


def fit_table(tbl) -> None:
    tbl_pr = tbl.find(qn("w:tblPr"))
    if tbl_pr is not None:
        for tag in ("w:tblInd", "w:tblpPr", "w:tblW"):
            for found in tbl_pr.findall(qn(tag)):
                tbl_pr.remove(found)
        tbl_pr.append(_el("w:tblW", **{"w:w": TEXT_W, "w:type": "dxa"}))
    grid = tbl.find(qn("w:tblGrid"))
    cols = grid.findall(qn("w:gridCol")) if grid is not None else []
    total = sum(int(c.get(qn("w:w")) or 0) for c in cols)
    if not total:
        return
    scale = TEXT_W / total
    for c in cols:
        c.set(qn("w:w"), str(int(int(c.get(qn("w:w")) or 0) * scale)))
    for tcw in tbl.iter(qn("w:tcW")):
        if tcw.get(qn("w:type")) == "dxa":
            tcw.set(qn("w:w"), str(int(int(tcw.get(qn("w:w"))) * scale)))


def fit_drawing(inline, max_width: int, width: int | None = None) -> None:
    extent = inline.find(qn("wp:extent"))
    cx, cy = int(extent.get("cx")), int(extent.get("cy"))
    target = width or min(cx, max_width)
    if width is None and cx <= max_width:
        return
    new_cx, new_cy = int(target), int(cy * target / cx)
    if new_cy > MAX_IMAGE_H:
        new_cx, new_cy = int(new_cx * MAX_IMAGE_H / new_cy), int(MAX_IMAGE_H)
    extent.set("cx", str(new_cx))
    extent.set("cy", str(new_cy))
    for ext in inline.iter(qn("a:ext")):
        if ext.get("cx"):
            ext.set("cx", str(new_cx))
            ext.set("cy", str(new_cy))


def is_blank(el) -> bool:
    if el.tag != qn("w:p"):
        return False
    text = "".join(t.text or "" for t in el.iter(qn("w:t"))).strip()
    return not text and next(el.iter(qn("a:blip")), None) is None


def skipped(el) -> bool:
    text = "".join(t.text or "" for t in el.iter(qn("w:t"))).strip()
    return text.startswith(SKIP_PREFIXES)


def merge_adjacent_tables(elements: list) -> list:
    merged = []
    for el in elements:
        if (merged and el.tag == qn("w:tbl") and merged[-1].tag == qn("w:tbl")
                and len(el.find(qn("w:tblGrid"))) == len(merged[-1].find(qn("w:tblGrid")))):
            for row in el.findall(qn("w:tr")):
                merged[-1].append(row)
            continue
        merged.append(el)
    return merged


# ---------------------------------------------------------------- the content dialect

HEADING = re.compile(r"^(#{1,4})\s+(.*?)\s*(?:\{#([\w.-]+)\})?\s*$")
INLINE = re.compile(r"(\*\*.+?\*\*|(?<![\w*])\*[^*\s][^*]*?\*(?![\w*])|`[^`]+`|\[\[[\w.-]+\]\]|\{\{[\w.-]+\}\})")


@dataclass
class Heading:
    level: int
    text: str
    key: str
    part: str
    listed: bool


@dataclass
class Part:
    file: str
    letter: str
    title: str
    lines: list[str] = field(default_factory=list)


def read_parts() -> list[Part]:
    parts = []
    for name in PARTS:
        lines = (NEA / name).read_text(encoding="utf-8").split("\n")
        head = lines[0].split(maxsplit=2)
        assert head[0] == "@part", f"{name} must start with @part"
        parts.append(Part(name, head[1], head[2] if len(head) > 2 else "", lines[1:]))
    return parts


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40]


def scan_headings(parts: list[Part]) -> tuple[list[Heading], dict[str, str]]:
    """Every heading and every anchor, with the part letter its page number carries."""
    headings, anchors = [], {}
    in_code = False
    for part in parts:
        for n, line in enumerate(part.lines):
            if line.startswith("```"):
                in_code = not in_code
            if in_code:
                continue
            match = HEADING.match(line)
            if match:
                level, text, key = len(match.group(1)), match.group(2), match.group(3)
                listed = level <= 2 or (level == 3 and key is not None)
                key = key or f"h-{part.letter}-{n}"
                assert key not in anchors, f"anchor {key} defined twice"
                anchors[key] = part.letter
                headings.append(Heading(level, text, key, part.letter, listed))
            for key in re.findall(r"^@anchor\s+([\w.-]+)", line):
                anchors[key] = part.letter
    for key, stage in nea_data.STAGE_ANCHORS.items():  # test tables put their own anchors down
        anchors.setdefault(key, "S")
    return headings, anchors


class Builder:
    def __init__(self, master: Path):
        self.doc = docx.Document(str(master))
        body = self.doc.element.body
        self.master = list(body)
        for el in list(body):
            if el.tag != qn("w:sectPr"):
                body.remove(el)
        self.body = body
        self.fields = Fields()
        self.parts = read_parts()
        self.headings, self.anchors = scan_headings(self.parts)
        self.figures: dict[str, int] = {}
        self.codes: dict[str, int] = {}
        self.part: Part | None = None
        self.used_master: set[int] = set()
        self._styles()

    # ---- document set-up

    def _styles(self) -> None:
        styles = self.doc.styles
        normal = styles["Normal"]
        normal.font.name, normal.font.size = FONT, Pt(BODY)
        normal.font.color.rgb = INK
        normal.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
        for level, (size, colour) in HEADINGS.items():
            style = styles[f"Heading {level}"]
            style.font.name, style.font.size, style.font.bold = FONT, Pt(size), True
            style.font.color.rgb = RGBColor.from_string(colour)
            style.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), FONT)
            fmt = style.paragraph_format
            fmt.space_before, fmt.space_after = Pt(14 if level <= 2 else 10), Pt(5)
            fmt.keep_with_next = True
        sect = self.body.find(qn("w:sectPr"))
        self._page_setup(sect)

    @staticmethod
    def _page_setup(sect) -> None:
        for tag in ("w:headerReference", "w:footerReference", "w:titlePg", "w:pgNumType", "w:cols", "w:pgSz", "w:pgMar"):
            for found in sect.findall(qn(tag)):
                sect.remove(found)
        sect.insert(0, _el("w:pgSz", **{"w:w": PAGE_W, "w:h": PAGE_H}))
        sect.insert(1, _el("w:pgMar", **{"w:top": MARGIN, "w:right": MARGIN, "w:bottom": MARGIN, "w:left": MARGIN,
                                         "w:header": 567, "w:footer": 567, "w:gutter": 0}))

    def start_part(self, part: Part, first: bool) -> None:
        if not first:
            self.doc.add_section(WD_SECTION.NEW_PAGE)
        section = self.doc.sections[-1]
        sect = section._sectPr
        self._page_setup(sect)
        number = _el("w:pgNumType", **{"w:start": 1})
        if part.letter == "i":
            number.set(qn("w:fmt"), "lowerRoman")
        sect.append(number)
        section.footer.is_linked_to_previous = False
        footer = section.footer.paragraphs[0]
        footer.text = ""
        footer.paragraph_format.tab_stops.add_tab_stop(Emu(TEXT_W * EMU_PER_TWIP), WD_TAB_ALIGNMENT.RIGHT)
        left = footer.add_run(f"PawMatch: Animal Adoption and Maintenance Tool  ·  {part.title}\t")
        style_run(left, size=8, color=MUTED)
        if part.letter != "i":
            prefix = footer.add_run(part.letter)
            style_run(prefix, size=9, bold=True, color="A92660")
        Fields.field(footer, "PAGE", "1", size=9, bold=True, color="A92660")
        self.part = part

    # ---- inline text

    def inline(self, paragraph, text: str, size=BODY, bold=None, italic=None, color=None) -> None:
        for token in INLINE.split(text):
            if not token:
                continue
            if token.startswith("**") and token.endswith("**") and len(token) > 4:
                self.inline(paragraph, token[2:-2], size, True, italic, color)
            elif token.startswith("`") and token.endswith("`"):
                run = paragraph.add_run(token[1:-1])
                style_run(run, size=size - 0.8, bold=bold, color=color or "6B2D4A", font=MONO)
            elif token.startswith("[[") and token.endswith("]]"):
                key = token[2:-2]
                if key not in self.anchors:
                    raise KeyError(f"page reference to unknown anchor [[{key}]] in {self.part.file}")
                letter = self.anchors[key]
                run = paragraph.add_run("" if letter == "i" else letter)
                style_run(run, size=size, bold=bold, color=color)
                Fields.field(paragraph, f"PAGEREF {key} \\h", "?", size=size, bold=bold, color=color)
            elif token.startswith("{{") and token.endswith("}}"):
                run = paragraph.add_run(str(nea_data.metric(token[2:-2])))
                style_run(run, size=size, bold=bold, italic=italic, color=color)
            elif token.startswith("*") and token.endswith("*") and len(token) > 2:
                self.inline(paragraph, token[1:-1], size, bold, True, color)
            else:
                run = paragraph.add_run(token)
                style_run(run, size=size, bold=bold, italic=italic, color=color)

    # ---- blocks

    def para(self, text: str, container=None, size=BODY, style=None, align=None, after=6, bold=None,
             italic=None, color=None, indent: float | None = None, hanging: float | None = None):
        container = container if container is not None else self.doc
        paragraph = container.add_paragraph(style=style)
        self.inline(paragraph, text, size=size, bold=bold, italic=italic, color=color)
        spacing(paragraph, after=after, line=1.12)
        if align:
            paragraph.alignment = align
        if indent is not None:
            paragraph.paragraph_format.left_indent = Cm(indent)
        if hanging is not None:
            paragraph.paragraph_format.first_line_indent = Cm(-hanging)
        return paragraph

    def heading(self, level: int, text: str, key: str | None, line_no: int) -> None:
        key = key or f"h-{self.part.letter}-{line_no}"
        if level <= 2 and self.doc.element.body[-2:-1]:
            pass
        paragraph = self.doc.add_paragraph(style=f"Heading {level}")
        self.inline(paragraph, text, size=HEADINGS[level][0], bold=True, color=HEADINGS[level][1])
        self.fields.bookmark(paragraph, key)

    def bullets(self, items: list[tuple[int, str]], container=None, size=BODY) -> None:
        for depth, text in items:
            marker = "•" if depth == 0 else "–"
            indent = 0.55 + depth * 0.55
            paragraph = self.para(f"{marker}\t{text}", container, size=size, after=2.5, indent=indent, hanging=0.4)
            paragraph.paragraph_format.tab_stops.add_tab_stop(Cm(indent))

    def numbered(self, items: list[tuple[str, str]], container=None, size=BODY) -> None:
        for number, text in items:
            paragraph = self.para(f"{number}\t{text}", container, size=size, after=2.5, indent=0.75, hanging=0.6)
            paragraph.paragraph_format.tab_stops.add_tab_stop(Cm(0.75))

    def table(self, rows: list[list[str]], widths: list[float] | None = None, size=TABLE, container=None,
              header=True, fills: dict | None = None) -> None:
        container = container if container is not None else self.doc
        columns = max(len(r) for r in rows)
        rows = [r + [""] * (columns - len(r)) for r in rows]
        table = container.add_table(rows=len(rows), cols=columns)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table_borders(table)
        available = TEXT_W if container is self.doc else TEXT_W - 600
        weights = widths or [1] * columns
        twips = [int(available * w / sum(weights)) for w in weights]
        set_widths(table, twips)
        for r, (row, values) in enumerate(zip(table.rows, rows)):
            no_split(row)
            if r == 0 and header:
                repeat_header(row)
            for cell, value in zip(row.cells, values):
                cell.text = ""
                lines = value.split("<br>")
                for i, line in enumerate(lines):
                    paragraph = cell.paragraphs[0] if i == 0 else cell.add_paragraph()
                    bullet = line.startswith("- ")
                    self.inline(paragraph, ("• " + line[2:]) if bullet else line, size=size,
                                bold=True if (r == 0 and header) else None)
                    spacing(paragraph, after=1.5, line=1.05)
                if r == 0 and header:
                    shade(cell, HEAD_FILL)
                else:
                    key = re.sub(r"[*`]", "", value).strip().lower()
                    key = key.split(":")[0].split("(")[0].strip()
                    if key in VERDICT_FILLS:
                        shade(cell, VERDICT_FILLS[key])
        self.para("", container, size=3, after=3)

    def box(self, kind: str, title: str, lines: list[str]) -> None:
        fill, accent = BOXES[kind]
        table = self.doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_widths(table, [TEXT_W])
        cell = table.rows[0].cells[0]
        shade(cell, fill)
        cell_borders(cell, accent, left_size=24, size=4)
        cell.text = ""
        heading = cell.paragraphs[0]
        self.inline(heading, title, size=BODY, bold=True, color=accent)
        spacing(heading, after=4)
        keep_with_next(heading)
        self.blocks(lines, container=cell, size=BODY - 0.5)
        self.para("", size=3, after=4)

    def code(self, text: str, caption: str | None = None, first_line: int | None = None, size=CODE) -> None:
        if caption:
            p = self.para(caption, size=CAPTION, bold=True, color="6B2D4A", after=2)
            keep_with_next(p)
        lines = text.rstrip("\n").split("\n")
        table = self.doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_widths(table, [TEXT_W])
        cell = table.rows[0].cells[0]
        shade(cell, CODE_FILL)
        cell_borders(cell, LINE, left_size=12)
        paragraph = cell.paragraphs[0]
        spacing(paragraph, after=0, line=1.0)
        for i, line in enumerate(lines):
            if first_line is not None:
                number = paragraph.add_run(f"{first_line + i:>4}  ")
                style_run(number, size=size, color="A0848F", font=MONO)
            run = paragraph.add_run(line)
            style_run(run, size=size, color=INK, font=MONO)
            if i < len(lines) - 1:
                run.add_break()
        self.para("", size=3, after=4)

    def figure(self, path: Path, caption: str, width_cm: float | None = None, key: str | None = None,
               crop: tuple[int, int] | None = None, border: bool = True) -> None:
        if crop:
            image = Image.open(path)
            crops = ROOT / "docs" / "img" / "_crops"
            crops.mkdir(exist_ok=True)
            cropped = crops / f"{path.stem}-{crop[0]}-{crop[1]}.png"
            image.crop((0, crop[0], image.width, min(crop[1], image.height))).save(cropped)
            path = cropped
        with Image.open(path) as image:
            w_px, h_px = image.size
        width = Cm(width_cm) if width_cm else Emu(TEXT_W * EMU_PER_TWIP)
        height = int(width * h_px / w_px)
        if height > MAX_IMAGE_H:
            width = int(width * MAX_IMAGE_H / height)
        paragraph = self.doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        spacing(paragraph, before=4, after=2)
        keep_with_next(paragraph)
        run = paragraph.add_run()
        run.add_picture(str(path), width=Emu(int(width)))
        if border:
            for pic in run._r.iter(qn("pic:spPr")):
                line = _el("a:ln", w=9525)
                fill = _el("a:solidFill")
                fill.append(_el("a:srgbClr", val="D9C2CD"))
                line.append(fill)
                pic.append(line)
        self.caption("Figure", caption, key)

    def caption(self, kind: str, text: str, key: str | None = None) -> str:
        letter = self.part.letter.upper()
        counter = self.figures if kind == "Figure" else self.codes
        counter[letter] = counter.get(letter, 0) + 1
        label = f"{kind} {letter}{counter[letter]}"
        paragraph = self.para(f"**{label}:** {text}", size=CAPTION, italic=True, color=MUTED,
                              align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
        if key:
            self.fields.bookmark(paragraph, key)
        return label

    def her(self, spec: str) -> None:
        indexes = []
        for item in spec.split():
            if "-" in item:
                a, b = item.split("-")
                indexes += list(range(int(a), int(b) + 1))
            else:
                indexes.append(int(item))
        chosen = []
        for i in indexes:
            el = self.master[i]
            if el.tag == qn("w:sectPr") or is_blank(el) or skipped(el):
                continue
            self.used_master.add(i)
            chosen.append(tidy_copy(el, unbold=i >= 551))
        for el in merge_adjacent_tables(chosen):
            self.body.find(qn("w:sectPr")).addprevious(el)

    def her_image(self, index: int, caption: str, width_cm: float | None = None, key: str | None = None) -> None:
        el = tidy_copy(self.master[index], unbold=False)
        self.used_master.add(index)
        for inline in el.iter(qn("wp:inline")):
            fit_drawing(inline, Emu(TEXT_W * EMU_PER_TWIP), int(Cm(width_cm)) if width_cm else Emu(TEXT_W * EMU_PER_TWIP))
        ppr = el.find(qn("w:pPr"))
        if ppr is None:
            ppr = _el("w:pPr")
            el.insert(0, ppr)
        for jc in ppr.findall(qn("w:jc")):
            ppr.remove(jc)
        ppr.append(_el("w:keepNext"))
        ppr.append(_el("w:jc", **{"w:val": "center"}))
        self.body.find(qn("w:sectPr")).addprevious(el)
        self.caption("Figure", caption, key)

    def contents(self) -> None:
        for h in self.headings:
            if not h.listed or h.part == "i":
                continue
            indent = {1: 0, 2: 0.6, 3: 1.2}[h.level]
            paragraph = self.doc.add_paragraph()
            spacing(paragraph, before=6 if h.level == 1 else 0, after=1.5 if h.level > 1 else 3)
            paragraph.paragraph_format.left_indent = Cm(indent)
            paragraph.paragraph_format.tab_stops.add_tab_stop(Emu(TEXT_W * EMU_PER_TWIP), WD_TAB_ALIGNMENT.RIGHT,
                                                              WD_TAB_LEADER.DOTS)
            size = 10.5 if h.level == 1 else 9.5 if h.level == 2 else 8.8
            self.inline(paragraph, re.sub(r"\[\[.*?\]\]", "", h.text) + "\t", size=size,
                        bold=h.level == 1, color="A92660" if h.level == 1 else None)
            run = paragraph.add_run(h.part)
            style_run(run, size=size, bold=h.level == 1)
            Fields.field(paragraph, f"PAGEREF {h.key} \\h", "?", size=size, bold=h.level == 1)

    # ---- the parser

    def blocks(self, lines: list[str], container=None, size=BODY) -> None:
        i = 0
        widths: list[float] | None = None
        table_size = TABLE
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith("<!--"):
                i += 1
                continue
            if stripped.startswith("```"):
                end = i + 1
                while not lines[end].strip().startswith("```"):
                    end += 1
                caption = stripped[3:].strip() or None
                self.code("\n".join(lines[i + 1:end]), caption=caption)
                i = end + 1
                continue
            if stripped.startswith(":::"):
                head = stripped[3:].strip().split(maxsplit=1)
                end = i + 1
                depth = 0
                while True:
                    s = lines[end].strip()
                    if s.startswith(":::") and s != ":::":
                        depth += 1
                    elif s == ":::":
                        if depth == 0:
                            break
                        depth -= 1
                    end += 1
                self.box(head[0], head[1] if len(head) > 1 else "", lines[i + 1:end])
                i = end + 1
                continue
            match = HEADING.match(stripped) if container is None else None
            if match:
                self.heading(len(match.group(1)), match.group(2), match.group(3), self._line_no(i, lines))
                i += 1
                continue
            if stripped.startswith("@"):
                directive, _, rest = stripped[1:].partition(" ")
                widths, table_size = self.directive(directive, rest.strip(), widths, table_size)
                i += 1
                continue
            if stripped.startswith("|"):
                rows = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", lines[i].strip())[1:-1]]
                    if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
                        rows.append(cells)
                    i += 1
                self.table(rows, widths, size=table_size, container=container)
                widths, table_size = None, TABLE
                continue
            if re.match(r"^\s*- ", line):
                items = []
                while i < len(lines) and re.match(r"^\s*- ", lines[i]):
                    depth = (len(lines[i]) - len(lines[i].lstrip())) // 2
                    text = lines[i].strip()[2:]
                    i += 1
                    while i < len(lines) and lines[i].startswith("  " * (depth + 1)) and lines[i].strip() \
                            and not re.match(r"^\s*- ", lines[i]):
                        text += " " + lines[i].strip()
                        i += 1
                    items.append((depth, text))
                self.bullets(items, container, size=size)
                continue
            if re.match(r"^\d+\.\s", stripped):
                items = []
                while i < len(lines) and re.match(r"^\d+\.\s", lines[i].strip()):
                    number, text = lines[i].strip().split(maxsplit=1)
                    i += 1
                    while i < len(lines) and lines[i].startswith("   ") and lines[i].strip():
                        text += " " + lines[i].strip()
                        i += 1
                    items.append((number, text))
                self.numbered(items, container, size=size)
                continue
            text = [stripped]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"^\s*([-#|@:`]|\d+\.\s)", lines[i]):
                text.append(lines[i].strip())
                i += 1
            self.para(" ".join(text), container, size=size)

    def _line_no(self, i: int, lines: list[str]) -> int:
        # headings get the same automatic key as in scan_headings: the line number within the part
        return i if lines is self.part.lines else -1

    def directive(self, name: str, rest: str, widths, table_size):
        args = [a.strip() for a in rest.split("|")]
        if name == "widths":
            return [float(w) for w in rest.split()], table_size
        if name == "size":
            return widths, float(rest)
        if name == "pagebreak":
            self.doc.add_page_break()
        elif name == "anchor":
            paragraph = self.para("", size=2, after=0)
            self.fields.bookmark(paragraph, rest)
        elif name == "her":
            self.her(rest)
        elif name == "herimg":
            index, caption = int(args[0].split()[0]), args[1]
            width = float(args[2]) if len(args) > 2 and args[2] else None
            key = args[3] if len(args) > 3 else None
            self.her_image(index, caption, width, key)
        elif name == "img":
            path = IMG / args[0]
            options = dict(o.split("=", 1) for o in args[3:] if "=" in o)
            crop = tuple(int(v) for v in options["crop"].split("-")) if "crop" in options else None
            width = float(args[2]) if len(args) > 2 and args[2] else None
            self.figure(path, args[1], width, options.get("key"), crop)
        elif name == "design":
            self.figure(IMG / "designs" / f"{args[0]}.png", args[1], None, args[2] if len(args) > 2 else None)
        elif name == "code":
            self.source_code(args[0], args[1] if len(args) > 1 else "")
        elif name == "toc":
            self.contents()
        elif name in nea_data.TABLES:
            spec = nea_data.TABLES[name](rest, self)
            if spec:
                rows, w, size = spec
                self.table(rows, w, size=size)
        else:
            raise ValueError(f"unknown directive @{name} in {self.part.file}")
        return widths, table_size

    def source_code(self, ref: str, caption: str) -> None:
        path, _, name = ref.partition("::")
        if ":" in path and not name:
            path, lines = path.split(":")
            first, last = (int(n) for n in lines.split("-"))
        else:
            tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
            node = find_node(tree, name)
            first = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
            last = node.end_lineno
        source = (ROOT / path).read_text(encoding="utf-8").split("\n")[first - 1:last]
        letter = self.part.letter
        self.codes[letter] = self.codes.get(letter, 0) + 1
        label = f"Code {letter}{self.codes[letter]}"
        title = f"{label}: {caption + ' · ' if caption else ''}{path}, lines {first}–{last}"
        self.code("\n".join(source), caption=title, first_line=first)

    # ---- run

    def build(self) -> None:
        for n, part in enumerate(self.parts):
            self.start_part(part, first=n == 0)
            self.blocks(part.lines)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(str(OUT))


def find_node(tree, dotted: str):
    scope = tree.body
    node = None
    for name in dotted.split("."):
        node = next(n for n in scope if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef, ast.Assign))
                    and (getattr(n, "name", None) == name
                         or (isinstance(n, ast.Assign) and any(getattr(t, "id", None) == name for t in n.targets))))
        scope = getattr(node, "body", [])
    return node


def to_pdf(path: Path) -> Path:
    """LibreOffice, with her font (Nunito) loaded from a private profile rather than installed."""
    profile = Path(tempfile.gettempdir()) / "pawmatch-lo-profile"
    fonts = profile / "user" / "fonts"
    fonts.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "static" / "fonts" / "Nunito.ttf", fonts / "Nunito.ttf")
    subprocess.run(["soffice", f"-env:UserInstallation=file://{profile}", "--headless", "--convert-to", "pdf",
                    "--outdir", str(path.parent), str(path)], check=True, capture_output=True, timeout=900)
    return path.with_suffix(".pdf")


def check_pdf(pdf: Path) -> None:
    pages = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True,
                                                             text=True).stdout).group(1))
    text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
    problems = [p for p in ("Error! Reference", "Error! Bookmark", "[[", "{{", "@her", ":::") if p in text]
    unresolved = re.findall(r"\b[ADSEX]\?(?!\w)", text)
    print(f"{pdf.name}: {pages} pages; unresolved references {len(unresolved)}; markers left {problems}")


if __name__ == "__main__":
    builder = Builder(MASTER)
    builder.build()
    unused = [i for i, el in enumerate(builder.master)
              if i not in builder.used_master and el.tag != qn("w:sectPr") and not is_blank(el) and not skipped(el)]
    print(f"wrote {OUT.relative_to(ROOT)}; her elements used {len(builder.used_master)}, not used {len(unused)}")
    if os.environ.get("SHOW_UNUSED"):
        print(unused)
    if "--no-pdf" not in sys.argv:
        check_pdf(to_pdf(OUT))
