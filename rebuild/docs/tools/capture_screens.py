"""Start PawMatch headless on a fresh database and save screenshots of the main flows.

    .venv/bin/python docs/tools/capture_screens.py docs/img
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pawmatch import db  # noqa: E402
from pawmatch.seed import create_admin, prepare  # noqa: E402

PORT = 8766
BASE = f"http://localhost:{PORT}"
STAFF = ("staff@pawmatch.test", "staff-demo-pass")
ADOPTER = ("Sam Lee", "sam@pawmatch.test", "30", "adopter-pass")


def wait_for_server() -> None:
    for _ in range(60):
        try:
            urllib.request.urlopen(f"{BASE}/_stcore/health", timeout=1)
            return
        except OSError:
            time.sleep(0.5)
    raise RuntimeError("Streamlit did not start")


def settle(page: Page) -> None:
    page.wait_for_timeout(700)
    page.wait_for_selector('[data-testid="stApp"][data-test-script-state="notRunning"]', timeout=20000)
    page.wait_for_timeout(400)


def shot(page: Page, out: Path, name: str, full: bool = True) -> None:
    """Streamlit scrolls an inner container, so grow the viewport to the content for a full shot."""
    settle(page)
    if full:
        height = page.evaluate("() => document.querySelector('[data-testid=stMain]').scrollHeight")
        page.set_viewport_size({"width": 1280, "height": min(max(int(height), 860), 3000)})
        page.wait_for_timeout(300)
    page.screenshot(path=str(out / f"{name}.png"))
    page.set_viewport_size({"width": 1280, "height": 860})
    print("saved", name, flush=True)


def choose(page: Page, label: str, option: str) -> None:
    page.get_by_label(label, exact=True).click()
    page.get_by_role("option", name=option, exact=True).click()
    settle(page)


def click(page: Page, name: str) -> None:
    page.get_by_role("button", name=name).first.click()
    settle(page)


def nav(page: Page, name: str) -> None:
    page.get_by_role("link", name=name).first.click()
    settle(page)


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    db_path = Path(tempfile.mkdtemp()) / "screens.db"
    prepare(str(db_path))
    with db.connect(db_path) as conn:
        create_admin(conn, "Shelter staff", STAFF[0], 40, STAFF[1])
    env = os.environ | {"PAWMATCH_DB": str(db_path)}
    server = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.headless", "true",
         "--server.port", str(PORT)], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    try:
        wait_for_server()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 860})
            page.goto(BASE)
            shot(page, out, "01-home")
            page.goto(f"{BASE}/browse")
            shot(page, out, "02-browse")
            choose(page, "Species", "Rabbit")
            shot(page, out, "03-browse-filter-rabbit")
            page.goto(f"{BASE}/profile?id=2")
            shot(page, out, "04-profile")

            page.goto(f"{BASE}/account")
            settle(page)
            page.get_by_role("tab", name="Register").click()
            panel = page.get_by_role("tabpanel", name="Register")
            panel.get_by_label("Full name", exact=True).fill("S")
            panel.get_by_label("Email address", exact=True).fill("not-an-email")
            panel.get_by_label("Age", exact=True).fill("16")
            panel.get_by_label("Password (at least 8 characters)", exact=True).fill("short")
            panel.get_by_label("Confirm password", exact=True).fill("short")
            click(page, "Create account")
            shot(page, out, "05-register-errors")
            panel.get_by_label("Full name", exact=True).fill(ADOPTER[0])
            panel.get_by_label("Email address", exact=True).fill(ADOPTER[1])
            panel.get_by_label("Age", exact=True).fill(ADOPTER[2])
            panel.get_by_label("Password (at least 8 characters)", exact=True).fill(ADOPTER[3])
            panel.get_by_label("Confirm password", exact=True).fill(ADOPTER[3])
            click(page, "Create account")
            shot(page, out, "06-questionnaire-step1")
            click(page, "Next")
            shot(page, out, "07-questionnaire-blocked")
            choose(page, "What type of home do you live in?", "Small or medium house")
            choose(page, "Do you have a secure garden?", "Yes")
            click(page, "Next")
            choose(page, "Are there children under 16 in your home?", "Yes")
            choose(page, "Do you have other pets?", "No")
            click(page, "Next")
            choose(page, "How much daily activity can you give an animal?", "Medium - about an hour of activity a day")
            choose(page, "On a normal day, how many hours would the animal be alone?", "4 hours")
            choose(page, "How much experience do you have with animals?", "Some (family pet growing up)")
            shot(page, out, "08-questionnaire-step3")
            click(page, "Next")
            choose(page, "Which species would you prefer?", "Dog")
            choose(page, "Which size would you prefer?", "No preference")
            click(page, "Next")
            shot(page, out, "09-questionnaire-review")
            click(page, "Submit and see my matches")
            page.get_by_text("requirements met").first.click()
            shot(page, out, "10-results")
            page.get_by_text("Show every animal").click()
            settle(page)
            page.get_by_text("Important requirement not met").first.scroll_into_view_if_needed()
            shot(page, out, "11-results-warning", full=False)

            # Navigate with the menu from here: a page reload starts a new Streamlit session.
            nav(page, "My account")
            click(page, "Log out")
            nav(page, "Log in")
            panel = page.get_by_role("tabpanel", name="Log in")
            panel.get_by_label("Email", exact=True).fill(STAFF[0])
            panel.get_by_label("Password", exact=True).fill("wrong-password")
            click(page, "Log in")
            shot(page, out, "12-login-error")
            panel.get_by_label("Password", exact=True).fill(STAFF[1])
            click(page, "Log in")
            nav(page, "Manage animals")
            shot(page, out, "13-admin-list")
            page.get_by_role("tab", name="Add animal").click()
            settle(page)
            add = page.get_by_role("tabpanel", name="Add animal")
            add.get_by_label("Name", exact=True).fill("Pip")
            click(page, "Save animal")
            shot(page, out, "14-admin-add-errors")
            page.get_by_role("tab", name="Edit or delete").click()
            choose(page, "Animal", "Oscar (Dog, #5)")
            shot(page, out, "15-admin-edit")
            browser.close()
    finally:
        server.terminate()
        server.wait(timeout=10)


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "docs/img"))
