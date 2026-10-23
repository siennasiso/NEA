"""Start PawMatch headless on a fresh database and screenshot every page, desktop and tablet.

    .venv/bin/python docs/tools/capture_screens.py docs/img            # both sizes
    .venv/bin/python docs/tools/capture_screens.py docs/img desktop    # one size

Everything happens through the real interface: an adopter registers, logs in, browses,
answers the questionnaire and opens their matches; then a staff member manages animals.
The database is a temporary file, so nothing here touches data/pawmatch.db.

Each screen is also audited as rendered: every piece of visible text is checked for contrast
against what is actually behind it (WCAG 2.2 AA: 4.5:1, or 3:1 for large text) and for a size
of at least 12px. Every button and link is then hovered and focused in turn and its text checked
again, because a control can pass at rest and fail when the pointer or keyboard is on it. The
login page is worked through with the keyboard alone. The results go to
docs/evidence/rendered-audit-<size>.json.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PORT = 8766
BASE = f"http://localhost:{PORT}"
STAFF = ("staff@pawmatch.test", "staff-demo-pass")
ADOPTER = ("Sam Lee", "sam@pawmatch.test", "30", "adopter-pass")
SIZES = {"desktop": (1280, 860), "tablet": (820, 1180)}
# The questionnaire's ten answers, in order (None: the hours question, typed instead; a tuple: the
# allergies question, where every card in it is chosen). A small flat with a garden, children and
# another pet, someone allergic to cats, gentle exercise and six hours alone: the top five then
# mixes Strong and Good matches, so the screenshots show unmet requirements too.
ANSWERS = ["Limited space", "Yes", "Yes", "Yes", ("Cats",), "Low", None, "Some", "No preference", "No preference"]
HOURS_ALONE = "6"
EVIDENCE = ROOT / "docs" / "evidence"

# Runs inside the page: every visible text element, its colour, what is behind it and its size.
# Backgrounds are blended up through the parents; a gradient behind the text is checked at each
# solid colour stop (translucent highlights are skipped, as in tests/test_style.py).
AUDIT_JS = """
(root) => {
  const parse = c => { const m = c && c.match(/rgba?\\(([^)]+)\\)/); if (!m) return null;
    const p = m[1].split(/[\\s,\\/]+/).filter(Boolean).map(Number);
    return {r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1}; };
  const lum = ({r, g, b}) => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
  const ratio = (x, y) => { const [a, b] = [lum(x), lum(y)].sort((p, q) => q - p); return (a + 0.05) / (b + 0.05); };
  const blend = (top, under) => ({r: top.r * top.a + under.r * (1 - top.a), g: top.g * top.a + under.g * (1 - top.a),
    b: top.b * top.a + under.b * (1 - top.a), a: 1});
  const hex = c => '#' + [c.r, c.g, c.b].map(v => Math.round(v).toString(16).padStart(2, '0')).join('');
  const behind = el => {
    const layers = [];
    for (let e = el; e; e = e.parentElement) {
      const s = getComputedStyle(e);
      const stops = (s.backgroundImage.match(/linear-gradient\\(.*?\\)\\)?(?=,\\s*(?:linear|radial)|$)/g) || [])
        .flatMap(g => (g.match(/rgba?\\([^)]+\\)/g) || []).map(parse)).filter(c => c && c.a === 1);
      if (stops.length) return stops.map(stop => layers.reduceRight((under, top) => blend(top, under), stop));
      const c = parse(s.backgroundColor);
      if (c && c.a > 0) { layers.push(c); if (c.a === 1) return [layers.reduceRight((under, top) => blend(top, under))]; }
    }
    return [layers.reduceRight((under, top) => blend(top, under), {r: 255, g: 255, b: 255, a: 1})];
  };
  const found = [];
  const walker = document.createTreeWalker(root || document.body, NodeFilter.SHOW_TEXT);
  const seen = new Set();
  while (walker.nextNode()) {
    const el = walker.currentNode.parentElement;
    if (!walker.currentNode.textContent.trim() || !el || seen.has(el)) continue;
    seen.add(el);
    const box = el.getBoundingClientRect(), s = getComputedStyle(el);
    if (!box.width || !box.height || s.visibility === 'hidden' || Number(s.opacity) === 0) continue;
    if (el.closest('button:disabled, [aria-disabled="true"], [aria-hidden="true"], style, script, noscript')) continue;
    const colour = parse(s.color); if (!colour) continue;
    const size = parseFloat(s.fontSize), weight = Number(s.fontWeight) || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    const worst = Math.min(...behind(el).map(bg => ratio(colour.a < 1 ? blend(colour, bg) : colour, bg)));
    found.push({text: walker.currentNode.textContent.trim().slice(0, 48), colour: hex(colour),
      ratio: Math.round(worst * 100) / 100, needs: large ? 3 : 4.5, size: Math.round(size * 10) / 10});
  }
  return found;
}
"""

# Runs inside the page: how a keyboard user moves through it. At each Tab stop the focused control
# and the boxes around it (an input's border is drawn by its wrapper) are compared with themselves
# unfocused; a focus indicator is "visible" when they look different.
FOCUS_JS = """
async () => {
  const e = document.activeElement; if (!e || e === document.body) return null;
  const boxes = []; for (let x = e; x && boxes.length < 5; x = x.parentElement) boxes.push(x);
  const look = () => boxes.map(x => { const s = getComputedStyle(x);
    return [s.outlineStyle, s.outlineWidth, s.outlineColor, s.boxShadow, s.borderColor, s.backgroundColor].join('|'); }).join('||');
  const pause = () => new Promise(done => setTimeout(done, 400));
  const focused = look(); e.blur(); await pause(); const blurred = look(); e.focus(); await pause();
  return {tag: e.tagName.toLowerCase(), label: (e.getAttribute('aria-label') || e.innerText || e.placeholder || '').trim().slice(0, 40),
          control: !['main', 'section', 'div'].includes(e.tagName.toLowerCase()), visible: focused !== blurred};
}
"""


def start_server(db_path: Path) -> subprocess.Popen:
    env = dict(os.environ, PAWMATCH_DB=str(db_path), PAWMATCH_ADMIN_EMAIL=STAFF[0],
               PAWMATCH_ADMIN_PASSWORD=STAFF[1], PAWMATCH_ADMIN_NAME="Shelter Staff")
    server = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.port", str(PORT),
         "--server.headless", "true"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(60):
        try:
            urllib.request.urlopen(f"{BASE}/_stcore/health", timeout=1)
            return server
        except OSError:
            time.sleep(0.5)
    server.kill()
    raise SystemExit("PawMatch did not start")


class Shooter:
    def __init__(self, page: Page, out: Path, size: str):
        self.page, self.out, self.size = page, out, size
        self.audit: dict[str, dict] = {}

    def settle(self) -> None:
        self.page.wait_for_timeout(700)
        self.page.wait_for_selector('[data-testid="stApp"][data-test-script-state="notRunning"]', timeout=30000)
        self.page.wait_for_timeout(500)

    def shot(self, name: str) -> None:
        """Save the whole page: the viewport grows to the page's height, then goes back."""
        self.settle()
        width, height = SIZES[self.size]
        full = self.page.evaluate(
            "() => Math.max(...[...document.querySelectorAll('[data-testid=stMain], [data-testid=stSidebar]')]"
            ".map(e => e.scrollHeight), 0)")
        self.page.set_viewport_size({"width": width, "height": min(max(int(full), height), 3600)})
        self.page.wait_for_timeout(500)
        self.page.screenshot(path=str(self.out / f"{name}-{self.size}.png"))
        texts = self.page.evaluate(AUDIT_JS)
        controls, states = self.control_states()
        self.audit[name] = {
            "texts": len(texts),
            "low_contrast": [x for x in texts if x["ratio"] < x["needs"]],
            "below_12px": [x for x in texts if x["size"] < 12],
            "controls_checked": controls,
            "low_contrast_hover_or_focus": states,
        }
        self.page.set_viewport_size({"width": width, "height": height})
        print("saved", name, self.size, len(texts), "texts,", len(self.audit[name]["low_contrast"]), "low contrast,",
              len(self.audit[name]["below_12px"]), "small,", controls, "controls,", len(states), "state problems",
              flush=True)

    def control_states(self) -> tuple[int, list[dict]]:
        """Hover, then focus, every visible enabled button and link, checking its text each time."""
        problems, checked = [], 0
        controls = self.page.locator('button:visible:enabled, [data-testid="stPageLink"] a:visible')
        for index in range(controls.count()):
            control = controls.nth(index)
            checked += 1
            for state in ("hover", "focus"):
                try:
                    control.hover(timeout=2000) if state == "hover" else control.focus(timeout=2000)
                    self.page.wait_for_timeout(150)
                    found = control.evaluate(AUDIT_JS)
                except Exception:  # a control that moved or disappeared; it is checked at rest above
                    continue
                problems += [dict(x, state=state) for x in found if x["ratio"] < x["needs"]]
                control.evaluate("e => e.blur()")
        self.page.mouse.move(0, 0)
        return checked, problems

    def keyboard_tour(self, stops: int = 12) -> None:
        """Press Tab through the login page, recording each stop and whether focus is visible."""
        self.page.evaluate("() => document.activeElement && document.activeElement.blur()")
        tour = []
        for _ in range(stops):
            self.page.keyboard.press("Tab")
            self.page.wait_for_timeout(400)
            tour.append(self.page.evaluate(FOCUS_JS))
        self.audit["keyboard-login"] = {"stops": tour}

    def click(self, text: str, scope: str = "") -> None:
        self.page.locator(f"{scope} button".strip()).filter(has_text=text).first.click()
        self.settle()

    def fill(self, label: str, value: str) -> None:
        self.page.get_by_label(label, exact=True).first.fill(value)

    def log_in(self, email: str, password: str) -> None:
        self.fill("Email address", email)
        self.fill("Password", password)
        self.page.keyboard.press("Enter")
        self.settle()


def adopter_flow(s: Shooter) -> None:
    s.page.goto(BASE)
    s.shot("01-login")
    s.keyboard_tour()
    s.log_in(ADOPTER[1], "wrong-password")
    s.shot("02-login-error")
    s.click("Create an account", '[data-testid="stMain"] [data-testid="stButtonGroup"]')
    s.shot("03-register")
    s.click("Create account")
    s.shot("04-register-errors")
    name, email, age, password = ADOPTER
    s.fill("Full name", name)
    s.fill("Email address", email)
    s.fill("Age", age)
    s.fill("Password", password)
    s.fill("Confirm password", password)
    s.click("Create account")  # a new account is signed straight in and lands on home
    s.shot("06-home")
    s.click("Browse animals", ".st-key-design_main")
    s.shot("07-browse")
    s.click("View profile")
    s.shot("08-profile")
    s.click("Questionnaire", ".st-key-design_sidebar")
    s.shot("09-questionnaire")
    for number, answer in enumerate(ANSWERS, start=1):
        if answer is None:
            s.page.get_by_label("Hours left alone").fill(HOURS_ALONE)
            s.page.keyboard.press("Tab")
            s.settle()
            if s.size == "desktop":
                s.shot("10-questionnaire-hours")
        elif isinstance(answer, tuple):
            for card in answer:
                s.click(card, ".st-key-question_card")
            if s.size == "desktop":
                s.shot("10b-questionnaire-allergies")
        else:
            s.click(answer, ".st-key-question_card")
        s.click("Submit questionnaire" if number == len(ANSWERS) else "Next question")
    s.shot("11-questionnaire-done")
    s.click("View matches")
    s.shot("12-matches")
    s.page.locator('[data-testid="stPageLink"] a').first.click()
    s.shot("13-profile-scored")
    s.click("My account", ".st-key-design_sidebar")
    s.shot("14-account")
    s.click("Log out")


def staff_flow(s: Shooter) -> None:
    s.log_in(*STAFF)
    s.shot("15-admin-overview")
    s.click("Manage animals", '[data-testid="stSidebar"]')
    s.shot("16-admin-manage")
    s.click("Add animal", '[data-testid="stSidebar"]')
    s.click("Save animal record")
    s.shot("17-admin-add-errors")


def main(out: Path, sizes: list[str]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for size in sizes:
        with tempfile.TemporaryDirectory() as folder:
            server = start_server(Path(folder) / "screens.db")
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch()
                    page = browser.new_page(viewport=dict(zip(("width", "height"), SIZES[size])))
                    shooter = Shooter(page, out, size)
                    adopter_flow(shooter)
                    staff_flow(shooter)
                    browser.close()
                EVIDENCE.mkdir(parents=True, exist_ok=True)
                (EVIDENCE / f"rendered-audit-{size}.json").write_text(json.dumps(shooter.audit, indent=1))
            finally:
                server.terminate()
                server.wait(timeout=10)


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2:] or list(SIZES))
