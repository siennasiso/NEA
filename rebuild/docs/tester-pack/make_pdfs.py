"""Render the tester pack's markdown to A4 PDFs: pandoc (md -> html), then headless Chromium.

    ../../.venv/bin/python make_pdfs.py
"""

import re
import subprocess
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
CSS = """
@page { size: A4; margin: 11mm 12mm; }
body { font: 9.6pt/1.35 -apple-system, "Helvetica Neue", Arial, sans-serif; color: #2b2326; }
h1 { color: #c23673; font-size: 17pt; margin: 0 0 4px; }
h2 { color: #c23673; font-size: 11.5pt; margin: 9px 0 3px; border-bottom: 1.5px solid #f3c6da; padding-bottom: 1px; }
p, li { margin: 2px 0; }
ul, ol { margin: 2px 0 2px 18px; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 4px 0; }
th { background: #fbeaf2; color: #7a2049; text-align: left; }
th, td { border: 1px solid #e7c3d3; padding: 3px 5px; vertical-align: top; }
small { color: #7a6a70; font-size: 7.5pt; }
td:first-child, th:first-child { width: 1%; white-space: nowrap; }
.form td { height: 34px; }
.form td:first-child { white-space: normal; width: 24%; }
.form td:nth-child(2) { width: 9%; } .form td:nth-child(3), .form td:nth-child(4) { width: 8%; }
.form td:nth-child(5) { width: 13%; }
.sus td { padding: 4px 5px; }
.sus td:nth-child(n+3), .sus th:nth-child(n+3) { text-align: center; width: 30px; font-size: 13pt; }
h2:last-of-type { page-break-before: always; }
.lines { border-bottom: 1px solid #c9b3bd; height: 26px; }
"""


def render(md: str, cls: str = "") -> None:
    html = subprocess.run(["pandoc", str(HERE / md), "-f", "markdown", "-t", "html"],
                          check=True, capture_output=True, text=True).stdout
    html = re.sub(r"<colgroup>.*?</colgroup>", "", html, flags=re.S)  # let the CSS set column widths
    if cls == "form":  # task table gets writing space; SUS table gets centred boxes
        html = html.replace("<table", "<table class=\"form\"", 1)
        first = html.index("<table") + 6
        html = html[:first] + html[first:].replace("<table", "<table class=\"sus\"", 1)
    page_html = f"<!doctype html><meta charset='utf-8'><style>{CSS}</style><body>{html}</body>"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(page_html)
        page.pdf(path=str(HERE / md.replace(".md", ".pdf")), format="A4", print_background=True,
                 margin={"top": "11mm", "bottom": "11mm", "left": "12mm", "right": "12mm"})
        browser.close()


if __name__ == "__main__":
    render("tester-script.md")
    render("feedback-form.md", "form")
