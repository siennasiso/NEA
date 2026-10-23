"""Build docs/PawMatch-NEA-opus.docx: the NEA master with every gap filled from this rebuild.

    .venv/bin/python docs/tools/make_diagrams.py
    .venv/bin/python docs/tools/build_nea_opus.py [path/to/PawMatch-NEA-master.docx]

Her analysis and design text is kept as it is. Each addition goes where its yellow box was, and the
box is removed. Additions inside her design pages get their own section with normal margins.
Measured numbers (timings, capacity, contrast) are measured when this script runs.
"""

from __future__ import annotations

import copy
import inspect
import os
import re
import sys
import tempfile
import time
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from nea_text import (FURTHER, PSEUDO_ADMIN, PSEUDO_BROWSE, PSEUDO_LOGIN, PSEUDO_MATCH, PSEUDO_MENU,  # noqa: E402
                      PSEUDO_QUESTIONNAIRE, PSEUDO_REGISTER, USABILITY)
from pawmatch import auth, db, matching, services, validation  # noqa: E402
from pawmatch.seed import create_admin, demo_animal_values, prepare  # noqa: E402

MASTER = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parents[1] / "NEA" / "kit" / "PawMatch-NEA-master.docx"
OUT = ROOT / "docs" / "PawMatch-NEA-opus.docx"
IMG = ROOT / "docs" / "img"
GREY = RGBColor(0x5f, 0x6b, 0x66)
COMMITS = {1: "ffd0ad5", 2: "10e84e7", 3: "b76527c", 4: "213e208", 5: "fdef5a0"}


# ---------------------------------------------------------------- measurements

def contrast(fg: str, bg: str) -> float:
    def lum(hex_):
        rgb = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    hi, lo = sorted((lum(fg), lum(bg)), reverse=True)
    return round((hi + 0.05) / (lo + 0.05), 1)


def measure() -> dict:
    """Capacity and timing on a temporary database with 500 animals and 100 users."""
    m: dict = {"contrast_text": contrast("#24312d", "#f7f5f0"), "contrast_button": contrast("#ffffff", "#2f7d6d")}
    path = os.path.join(tempfile.mkdtemp(), "measure.db")
    prepare(path)
    base = demo_animal_values()
    with db.connect(path) as conn:
        for i in range(500 - len(base)):
            values, errors = validation.validate_animal(dict(base[i % len(base)], name=f"Test animal {chr(65 + i % 26)}"))
            assert not errors
            db.insert_animal(conn, values)
        users = [auth.register(conn, "Load Tester", f"tester{i}@example.com", 30, "password1", "password1")[0] for i in range(100)]
        m["animals"] = db.count_animals(conn)
        m["users"] = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    answers = {"housing_level": 2, "garden_access": "Yes", "has_children": "Yes", "other_pets": "No", "experience": "None",
               "activity_level": 2, "hours_alone": 4, "preferred_species": "Dog", "preferred_size": "No preference"}
    runs = []
    for user in users[:5]:
        start = time.perf_counter()
        with db.connect(path) as conn:
            results, errors = services.submit_questionnaire(conn, user, answers)
        runs.append(time.perf_counter() - start)
        assert not errors and len(results) == 500
    m["submit_mean"], m["submit_max"] = round(sum(runs) / len(runs), 3), round(max(runs), 3)
    start = time.perf_counter()
    with db.connect(path) as conn:
        found = services.browse(conn, None, None, "")
    m["browse_query"] = round(time.perf_counter() - start, 3)
    assert len(found) == 500
    from streamlit.testing.v1 import AppTest
    from webui import state
    state.DB_PATH = Path(path)
    times = []
    for _ in range(3):
        at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=60)
        start = time.perf_counter()
        at.run()
        at.switch_page(state.PAGES["browse"]).run()
        times.append(time.perf_counter() - start)
        assert not at.exception
    m["browse_page"] = round(max(times), 2)
    m["browse_cards"] = sum(1 for b in at.button if b.label == "View profile")
    return m


# ---------------------------------------------------------------- docx helpers

def set_cell(cell, text: str, bold: bool = False, size: float = 8, shade: str | None = None) -> None:
    cell.text = ""
    para = cell.paragraphs[0]
    add_runs(para, str(text), size=size, bold=bold)
    if shade:
        tc_pr = cell._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), shade)
        tc_pr.append(shd)


def add_runs(para, text: str, size: float | None = None, bold: bool = False, italic: bool = False,
             color: RGBColor | None = None, font: str | None = None) -> None:
    """Add text; **double stars** mark bold parts."""
    for i, part in enumerate(re.split(r"\*\*", text)):
        if not part:
            continue
        run = para.add_run(part)
        run.bold = bold or i % 2 == 1
        run.italic = italic
        if size:
            run.font.size = Pt(size)
        if color is not None:
            run.font.color.rgb = color
        if font:
            run.font.name = font
            run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), font)


def next_sectpr(el):
    for sib in el.itersiblings():
        if sib.tag == qn("w:sectPr"):
            return sib
        if sib.tag == qn("w:p"):
            found = sib.find(qn("w:pPr") + "/" + qn("w:sectPr"))
            if found is not None:
                return found
    raise ValueError("no section after anchor")


class Block:
    """Writes new content immediately before an anchor element."""

    def __init__(self, doc, anchor, wrap: bool = False, note: bool = True):
        self.doc, self.anchor, self.wrap = doc, anchor, wrap
        if wrap:  # end her page's section here, so the addition can have normal margins
            self._sect_para(copy.deepcopy(next_sectpr(anchor)))
        if note:
            self.para("Model version addition", italic=True, size=8, color=GREY)

    def _put(self, el):
        self.anchor.addprevious(el)

    def _sect_para(self, sect):
        p = OxmlElement("w:p")
        ppr = OxmlElement("w:pPr")
        ppr.append(sect)
        p.append(ppr)
        self._put(p)

    def close(self):
        if self.wrap:
            sect = copy.deepcopy(self.doc.element.body.find(qn("w:sectPr")))
            for ref in sect.findall(qn("w:headerReference")) + sect.findall(qn("w:footerReference")):
                sect.remove(ref)
            self._sect_para(sect)

    def para(self, text: str = "", style: str | None = None, size: float | None = 10, bold=False, italic=False,
             color=None, space_after: float = 4):
        p = self.doc.add_paragraph(style=style)
        add_runs(p, text, size=size, bold=bold, italic=italic, color=color)
        p.paragraph_format.space_after = Pt(space_after)
        self._put(p._p)
        return p

    def heading(self, text: str, level: int = 3):
        p = self.doc.add_paragraph(text, style=f"Heading {level}")
        self._put(p._p)

    def bullets(self, items):
        for item in items:
            self.para(item, style="List Bullet", space_after=1)

    def code(self, text: str, size: float = 7.5):
        table = self.doc.add_table(rows=1, cols=1)
        table.style = "Table Grid"
        cell = table.rows[0].cells[0]
        set_cell(cell, "", shade="F3F4F2")
        para = cell.paragraphs[0]
        lines = text.rstrip("\n").split("\n")
        for i, line in enumerate(lines):
            add_runs(para, line.replace("**", "* *"), size=size, font="Courier New")
            if i < len(lines) - 1:
                para.runs[-1].add_break()
        para.paragraph_format.space_after = Pt(0)
        self._put(table._tbl)
        self.para("", size=4, space_after=2)

    def table(self, headers, rows, widths=None, size: float = 7.5):
        table = self.doc.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        for cell, text in zip(table.rows[0].cells, headers):
            set_cell(cell, text, bold=True, size=size, shade="E8F0EC")
        for row in rows:
            cells = table.add_row().cells
            for cell, text in zip(cells, row):
                set_cell(cell, text, size=size)
        if widths:
            for row in table.rows:
                for cell, w in zip(row.cells, widths):
                    cell.width = Inches(w)
            table.autofit = False
            for col, w in zip(table._tbl.tblGrid.findall(qn("w:gridCol")), widths):
                col.set(qn("w:w"), str(int(w * 1440)))  # LibreOffice reads the grid, Word reads the cells
        self._put(table._tbl)
        self.para("", size=4, space_after=2)
        return table

    def image(self, name: str, caption: str, width: float = 6.0):
        p = self.doc.add_paragraph()
        p.add_run().add_picture(str(IMG / name), width=Inches(width))
        self._put(p._p)
        self.para(caption, italic=True, size=8.5, color=GREY, space_after=8)


def fill_table(doc, tbl_el, rows, size: float = 7.5):
    """Fill an existing table's empty rows, adding rows as needed."""
    table = Table(tbl_el, doc)
    body = table.rows[1:]
    for i, values in enumerate(rows):
        cells = body[i].cells if i < len(body) else table.add_row().cells
        for cell, text in zip(cells, values):
            set_cell(cell, text, size=size)
    for extra in body[len(rows):]:
        tbl_el.remove(extra._tr)
    return table


def code_of(obj, start: str | None = None, lines: int | None = None) -> str:
    src = inspect.getsource(obj)
    if start:
        src = src[src.index(start):]
    if lines:
        src = "\n".join(src.split("\n")[:lines])
    return src.rstrip()


def file_lines(rel: str, first: str, count: int) -> str:
    text = (ROOT / rel).read_text().split("\n")
    i = next(n for n, line in enumerate(text) if first in line)
    return "\n".join(text[i:i + count])


def evidence(name: str, tail: int = 3) -> str:
    lines = (ROOT / "docs" / "evidence" / name).read_text().rstrip().split("\n")
    return "\n".join(lines[-tail:])


# ---------------------------------------------------------------- content tables

def criteria_rows(m: dict) -> list[tuple]:
    """(number, how it is measured, evidence, verdict, explanation) for every requirement, in table order."""
    s = f"{m['submit_mean']} s"
    return [
        ("1.1", f"One theme file sets every colour; body text contrast at least 4.5 : 1 (WCAG AA); every action is a labelled button",
         f"T1; contrast {m['contrast_text']} : 1 text, {m['contrast_button']} : 1 buttons; Screens 01-15", "Met",
         f"Contrast is well above 4.5 : 1. Headings and buttons are the theme's own; no page adds its own styling."),
        ("1.2", "At 1280 px and 820 px (tablet) wide: no sideways scrolling and no text cut off",
         "T2; Screens 02 and 16", "Met",
         "Checked in a headless browser at both widths. Not checked on a real tablet or phone; see 5.3."),
        ("1.3", "The top menu holds Home, Animals, Questionnaire, My matches and Log in / My account on 7 of 7 pages",
         "T3; every page test opens pages through the one menu", "Met",
         "The menu is built once in streamlit_app.py, so no page can leave it out."),
        ("1.4", "0 pages with their own colours or CSS", "T1; .streamlit/config.toml", "Met",
         "All styling comes from one 15-line theme file."),
        ("2.1", "The home page states the purpose and the word 'suitability'", "F1; test_home_page_explains_purpose; Screen 01", "Met",
         "The test reads the rendered page text."),
        ("2.2", "1 click from Home to the questionnaire", "F1; Screen 01", "Met", "'Start the questionnaire' is the first button."),
        ("3.1", "Number of cards = number of animal records (13 of 13; 500 of 500 in the load test)",
         f"F2, T5; test_browse_shows_a_card_for_every_animal; {m['browse_cards']} cards for {m['animals']} animals", "Met",
         "Every record in the table appears. There is no 'adopted' status, so every stored animal counts as available."),
        ("3.2", "5 of 5 facts on every card: species, name, breed, age, image", "F2; Screen 02", "Met",
         "The card is one function, so every card is the same."),
        ("3.3", "At least 3 species stored and shown", "F2; test_seed_has_three_species_and_is_idempotent; Screen 03", "Met",
         "Dogs, cats and rabbits; the database CHECK only allows these three."),
        ("3.4", "1 click from a card to its profile", "F3; test_profile_reads_from_database; Screen 04", "Met",
         "'View profile' on every card."),
        ("4.1", "5 of 5 shown: name, species, breed, age, sex", "F3; Screen 04", "Met", "Shown in a table at the top of the profile."),
        ("4.2", "Personality, medical needs, exercise needs and suitability all shown", "F3; Screen 04", "Met",
         "Suitability is listed as plain sentences (garden, children, hours alone, home size)."),
        ("4.3", "Profile is loaded by animal_id from SQLite; editing the record changes the page", "F3, F12; round-trip tests", "Met",
         "The page reads the id from the address and queries the database each time."),
        ("4.4", "1 click back to the list or to My matches", "F3; Screen 04", "Met",
         "The back link remembers whether the user came from the list or the results."),
        ("5.1", "A valid sign-up stores 1 user row with a hashed password", "F4; test_register_stores_hash_not_password", "Met",
         "Age is also collected so the 18+ rule can be checked."),
        ("5.2", "100 % of the blank and invalid cases A2-A6 and A11 are rejected with a message", "F4, R1; test_registration_*; Screen 05",
         "Met", "Every rule in the Design's validation list has a test, including the name format added in stage 5."),
        ("5.3", "Correct details log in; Log out clears the session", "F5; test_login_success_and_email_is_normalised", "Met",
         "Limitation: reloading the browser page also logs the user out (5.3)."),
        ("5.4", "A staff account sees 'Manage animals'; an adopter sees no staff link", "F10; test_admin_page_lists_animals_for_staff",
         "Met", "Staff use the same login form; the menu changes by role."),
        ("5.5", "Wrong password and unknown email give the same message and no session",
         "R2; test_wrong_password_and_unknown_email_give_the_same_message; Screen 12", "Met",
         "The same message means nobody can find out which emails have accounts."),
        ("6.1", "9 questions cover home, garden, children, other pets, activity, hours alone, experience, species, size",
         "F6; test_steps_cover_every_question_once; Screens 06-09", "Met",
         "Other pets and experience are stored but not scored, because the Design gives them no weight."),
        ("6.2", "4 steps and a review step; 4 of 5 testers rate the layout 8/10 or more for clarity",
         "F6; Screens 06-09; tester ratings not collected", "Partly met",
         "The sections are built and tested, but the planned tester rating was not carried out (5.3)."),
        ("6.3", "0 free-text boxes in the questionnaire", "F6; Screens 06, 08", "Met", "Every answer is a drop-down."),
        ("6.4", "A blank answer blocks Next; an incomplete set saves 0 rows",
         "R3, R4; test_questionnaire_blocks_unanswered_step; test_incomplete_submission_saves_nothing; Screen 07", "Met",
         "Checked on each step and again for the whole set before saving."),
        ("7.1", "Every animal gets a result (N results for N animals)", "F7; test_adopter_submission_stores_ranked_results", "Met",
         "Nothing is filtered out before scoring."),
        ("7.2", "A percentage from 0 to 100 (1 decimal place); 500 animals scored and stored in under 2 seconds",
         f"F7, T4; test_matching.py (29 cases); mean {s}, slowest {m['submit_max']} s", "Met",
         "The formula is in the Design (worked example) and each factor has its own test."),
        ("7.3", "At least 4 shown, best first", "F8; test_results_show_at_least_four_ranked_matches; Screen 10", "Met",
         "Five are shown by default and a toggle shows every animal. Animals with a welfare warning come after those without."),
        ("7.4", "Every result lists what is met and what is not", "F8; Screens 10, 11", "Met", "In the 'requirements met / not met' list on each card."),
        ("7.5", "An unmet hours-alone, children or space requirement shows a warning",
         "F9; test_important_unmet_requirements_raise_warnings; Screen 11", "Met", "Garden and activity lose points but do not warn."),
        ("7.6", "The results page says scores are guidance and staff decide", "F8; Screen 10", "Met", "Shown above the results and on Home."),
        ("8.1", "The staff page is reached only through a staff login", "F10, R5; test_admin_page_is_not_routable_for_adopters",
         "Partly met", "Only staff accounts reach it, but staff use the same login form as adopters, not a separate one."),
        ("8.2", "A complete add form stores a record; any invalid field stores nothing", "F11, R6; test_admin_can_add_edit_and_delete; Screen 14",
         "Met", "Every field is validated and the database CHECKs repeat the rules."),
        ("8.3", "An edit is saved and shown on the profile", "F12; test_update_changes_the_stored_record; Screen 15", "Met",
         "Editing an animal that was deleted meanwhile gives a clear error (R7)."),
        ("8.4", "Delete only after the confirmation box is ticked; the record and its results are removed",
         "F13; test_delete_removes_animal_and_its_stored_results", "Met",
         "The record is deleted rather than marked 'adopted' (5.4)."),
        ("8.5", "An adopter is refused every staff action, even if the page is bypassed",
         "R5, R8; test_non_admins_are_refused_every_change; test_admin_page_guard_stops_adopters_even_if_reached_directly", "Met",
         "Checked three times: menu, page guard, and inside each service."),
        ("9.1", f"Stores users, animals, responses and results; at least 500 animals and 100 users",
         f"T5; {m['animals']} animals and {m['users']} users stored and read back", "Met",
         "Four tables with keys and CHECK constraints."),
        ("9.2", "Animals can be added, viewed, edited and deleted", "F11-F13", "Met", "Through the staff page and the services."),
        ("9.3", "Answers are saved and used for the score", "F7; test_responses_and_results_are_stored_and_reloaded_in_rank_order",
         "Met", "Each submission is a new response row; results point to it and record when they were calculated."),
        ("9.4", "Values read back equal the values stored", "F12; test_insert_then_get_round_trips_every_field", "Met",
         "Checked for every animal field."),
    ]


DEV_PLAN = [
    # Component A: accounts
    ("A1", "Valid sign-up: the main path must work", "Sam Lee, sam@x.com, 30, 'longenough' twice", "Account stored, logged in", "Normal"),
    ("A2", "Blank fields: presence checks", "name '   ', email '', age '', password ''", "One message per field", "Invalid"),
    ("A3", "Email format", "no-at-sign.com, a@b, two@@x.com", "'Enter a valid email address'", "Invalid"),
    ("A4", "Age boundary: 18+ rule", "17 / 18 / 120 / 121", "17 and 121 rejected; 18 and 120 accepted", "Boundary"),
    ("A5", "Age type check", "2.5, abc", "'Age must be a whole number.'", "Invalid"),
    ("A6", "Password boundary (at least 8)", "7 characters / 8 characters", "7 rejected, 8 accepted", "Boundary"),
    ("A7", "Duplicate email, any case", "SAM@x.com after sam@x.com", "'already exists', nothing stored", "Invalid"),
    ("A8", "Login with right details; email case ignored", "' SAM@X.COM ' + password", "Logged in", "Normal"),
    ("A9", "Wrong password and unknown email", "right email + wrong password; unknown email", "Same message for both", "Invalid"),
    ("A10", "Password stored only as a salted hash", "same password twice", "Two different hashes; no plain text", "Normal"),
    ("A11", "Name format from the Design variables table", "Mary-Jane, Siobhan O'Neill / 12345, Sam3, Sam!",
     "Letters, spaces, hyphens, apostrophes only", "Invalid"),
    # Component B: browsing and profile
    ("B1", "Every animal shown as a card", "13 demo animals", "13 cards", "Normal"),
    ("B2", "Species and size filters", "Rabbit; Small", "Only matching animals", "Normal"),
    ("B3", "Search text is data, not SQL", "' OR 1=1 --", "No animals, no error", "Invalid"),
    ("B4", "Empty search shows everything", "''", "All animals", "Boundary"),
    ("B5", "Search length limit", "21 characters typed", "Box stops at 20", "Boundary"),
    ("B6", "Profile loads from the database by id", "id of Luna", "Luna's details", "Normal"),
    ("B7", "Profile with a missing or bad id", "id=999, id=abc", "'could not be found'", "Invalid"),
    ("B8", "Back link returns to where the user came from", "open from results", "'Back to my matches'", "Normal"),
    # Component C: staff area
    ("C1", "Adopter calls add, edit or delete", "adopter account", "Refused (AccessDenied)", "Invalid"),
    ("C2", "Add a complete animal", "every field valid", "Stored; listed", "Normal"),
    ("C3", "Animal age range", "0 / 1 / 30 / 31", "0 and 31 rejected", "Boundary"),
    ("C4", "Hours alone range", "-1 / 0 / 24 / 25", "-1 and 25 rejected", "Boundary"),
    ("C5", "Edit and save", "new breed", "Breed changed on the profile", "Normal"),
    ("C6", "Edit an animal deleted meanwhile", "stale id", "'no longer exists'", "Invalid"),
    ("C7", "Delete needs confirmation", "box not ticked", "Button disabled", "Invalid"),
    ("C8", "Staff page hidden from adopters", "adopter opens the page by name", "No such page", "Invalid"),
    ("C9", "Photo type and size", "a.gif; 2 MB + 1 byte / exactly 2 MB", "Rejected / accepted", "Boundary"),
    ("C10", "Database repeats the rules", "direct INSERT with species 'Hamster'", "Database refuses it", "Invalid"),
    ("C11", "Breed length and content (Design)", "Mixed / X, ###", "X and ### rejected", "Boundary"),
    # Component D: questionnaire
    ("D1", "Each question in exactly one step", "the four steps", "9 questions, none twice", "Normal"),
    ("D2", "A blank answer blocks Next", "step 1 with one blank", "Error, stays on step", "Invalid"),
    ("D3", "A step only checks its own questions", "step 1 answered, rest blank", "Next allowed", "Normal"),
    ("D4", "Hours alone range", "-1 / 0 / 24 / 25", "-1 and 25 rejected", "Boundary"),
    ("D5", "Answer outside the list", "species 'Hamster'", "Rejected", "Invalid"),
    ("D6", "Incomplete set cannot be saved", "8 of 9 answers", "Nothing stored", "Invalid"),
    ("D7", "Must be logged in", "no session", "'Please log in'", "Invalid"),
    ("D8", "Full valid set", "9 valid answers", "Saved; results page opens", "Normal"),
    # Component E: matching and results
    ("E1", "Weights equal the Design", "WEIGHTS", "20, 15, 15, 12, 10 = 72", "Normal"),
    ("E2", "Perfect match", "every need met", "100 %, Strong", "Boundary"),
    ("E3", "Nothing met", "every need failed", "0 %, Low", "Boundary"),
    ("E4", "Each factor loses its own weight", "fail one factor at a time", "−20, −15, −15, −12, −10 points", "Normal"),
    ("E5", "Exactly at a limit counts as met", "hours = max hours; housing = minimum", "Met", "Boundary"),
    ("E6", "Category cut-offs", "79.9 / 80 / 59.9 / 60 / 39.9 / 40", "Possible/Strong/Possible/Good/Low/Possible", "Boundary"),
    ("E7", "Warnings only for important factors", "fail garden vs fail children", "Warning only for children", "Normal"),
    ("E8", "Preferences change order, not %", "preferred species", "Same %, higher place", "Normal"),
    ("E9", "Unsuitable animals rank after suitable ones", "high score with warning vs lower without", "Lower one first", "Normal"),
    ("E10", "At least 4 results shown", "13 animals", "5 shown, toggle for all", "Normal"),
    ("E11", "Results record when they were calculated (Design table)", "any submission", "calculated_at stored", "Normal"),
]

POST_PLAN_EXTRA = [
    ("U1", "Usability: register and log in without help", "Adopter (survey group), first visit", "Done in under 2 minutes; rates it 8/10+"),
    ("U2", "Usability: complete the questionnaire", "Adopter", "No help needed; rates clarity 8/10+"),
    ("U3", "Usability: explain your top match and any warning", "Adopter", "Can say why the top animal suits them"),
    ("U4", "Usability: add, then edit, then delete an animal", "Shelter staff (client)", "All three done without help"),
    ("U5", "Usability: use the site on a tablet", "Adopter with a tablet", "No zooming or sideways scrolling"),
]

STAGES = {
    1: dict(
        title="Stage 1: Data model, validation and matching rules",
        aim=("Builds the parts with no screens: the data classes (Design: variables tables), every validation rule "
             "(Design: the Validation lists for login, registration, animals and the questionnaire) and the compatibility "
             "algorithm (Design: Compatibility algorithm and questionnaire, First Matching part). These come first because "
             "every later stage uses them, and they can be fully tested without a database or a browser. Commit "
             f"{COMMITS[1]}; components A, C, D and E of the hierarchy chart."),
        tests=[("A2-A6", "Registration validation", "see test plan", "Rejected with the right message", "As expected", "Pass", "test_registration_* (Ev 1)"),
               ("C3, C4", "Animal ranges", "0/1/30/31 and -1/0/24/25", "Ends rejected", "As expected", "Pass", "test_invalid_animal_fields_are_rejected"),
               ("D1-D5", "Questionnaire steps and rules", "see test plan", "As planned", "As expected", "Pass", "test_steps_cover_every_question_once, test_step_validation_only_checks_that_step"),
               ("E1-E9", "Scoring and ranking", "see test plan", "As planned", "As expected", "Pass", "test_matching.py, 29 cases"),
               ("A11", "Name format", "12345", "Rejected", "Accepted (not yet checked)", "Fail (found in stage 5)", "Ev 5a"),
               ("C11", "Breed length and content", "X, ###", "Rejected", "Accepted", "Fail (found in stage 5)", "Ev 5a")],
        failed=[("A11, C11", "'12345' was accepted as a person's name, and 'X' and '###' as breeds. Found when the Design was "
                 "re-checked in stage 5.", "The validator only checked presence and length; the Design's format rules "
                 "(letters, spaces and hyphens; breed 2-50 and not only symbols) were missed.",
                 "Added a letters-only rule for people (digits allowed for animal names such as 'R2', as the Design allows) "
                 "and a 2-50, must-contain-letters rule for breeds. Tests written first from the Design wording.",
                 "Pass: 134 passed (Ev 5b)")],
        review=("Developer review against the Design and success criteria, after the stage 1 tests passed (no client or "
                "stakeholder was shown this stage, as it has no screens). Checked: weights 20/15/15/12/10 match the Design table "
                "(test E1); preferences do not change the percentage, as the Design says; every validation list has at least one "
                "test. Open question found: the Design does not say whether failing children or garden makes an animal unsuitable "
                "or only loses points."),
        changes=("Decided and wrote down the rule: every unmet factor loses its points; unmet hours alone, children or space "
                 "also gives a warning, and those animals are listed after all animals without warnings (tests E7 and E9). "
                 "Reason: a high score must never put an unsafe match at the top (Q3). Added a fixed tie-break (name, then id) "
                 "so equal scores always appear in the same order."),
        code=[("Weights and normalisation (pawmatch/matching.py)", "matching_top"),
              ("Scoring one animal", "score"),
              ("Ranking: warnings last, then points", "rank_key"),
              ("One validator per questionnaire step (pawmatch/validation.py)", "validate_step")],
        evidence_text=("stage1-pytest.txt", "Ev 1: the stage 1 test run (docs/evidence/stage1-pytest.txt)"),
    ),
    2: dict(
        title="Stage 2: Database, login and staff-only actions",
        aim=("Builds the SQLite database (Design: Database structure and the four table designs), registration and login with "
             "hashed passwords (Design: Login and Registration), the role check and the add / edit / delete services (Design: "
             f"Admin Page), and the demo animals. Commit {COMMITS[2]}; components A, C and E (storing results)."),
        tests=[("A1, A7", "Register; duplicate email in another case", "sam@x.com then SAM@x.com", "Second refused", "As expected", "Pass", "test_register_rejects_duplicate_email_case_insensitively"),
               ("A8, A9", "Login right / wrong", "see test plan", "Logged in / same message", "As expected", "Pass", "test_login_success..., test_wrong_password_and_unknown_email_give_the_same_message"),
               ("A10", "Salted hash", "same password twice", "Different hashes", "As expected", "Pass", "test_hash_is_salted_and_not_plain_text"),
               ("B3", "SQL injection in search", "' OR 1=1 --", "No rows, no error", "As expected", "Pass", "test_search_text_is_treated_as_data_not_sql"),
               ("C1", "Adopter calls staff actions", "adopter account", "AccessDenied", "As expected", "Pass", "test_non_admins_are_refused_every_change"),
               ("C10", "Database CHECKs", "species 'Hamster'", "IntegrityError", "As expected", "Pass", "test_database_constraints_back_up_validation"),
               ("E11", "calculated_at stored", "any submission", "Timestamp stored", "No such column", "Fail (found in stage 5)", "Ev 5a")],
        failed=[("E11", "Match results had no calculated_at column. Found when the Design's Match Results table was "
                 "re-checked in stage 5.", "The table was built from the scoring needs (rank, score, reasons) and the "
                 "Design's calculated_at field was left out.",
                 "Added the column, one timestamp per ranking, and an in-place upgrade (ALTER TABLE) so databases made before "
                 "the fix keep working; a second test builds an old database and checks it is upgraded.",
                 "Pass: 134 passed (Ev 5b)")],
        review=("Developer review against the Design and criteria 5 and 8-9. Checked: passwords never stored or logged in plain "
                "text; every SQL statement uses ? placeholders (search included, test B3); deleting an animal also removes its "
                "stored results. Found two risks: a login message that says 'no such email' would let anyone test which emails "
                "have accounts; and hiding the staff page alone would not stop a determined user."),
        changes=("One message for any failed login (A9). The role is checked inside every add, edit and delete service as well "
                 "as on the page (C1), so even code that bypasses the page is refused. Staff accounts can only be created from "
                 "the command line (python -m pawmatch.seed --admin), so nobody can register as staff."),
        code=[("Salted scrypt hashing and constant-time check (pawmatch/auth.py)", "hash"),
              ("Login: one message for every failure", "login"),
              ("Role checked inside the service", "services"),
              ("Browse query: values bound, never joined into SQL (pawmatch/db.py)", "list_animals")],
        evidence_text=("stage2-pytest.txt", "Ev 2: the stage 2 test run (docs/evidence/stage2-pytest.txt)"),
    ),
    3: dict(
        title="Stage 3: The pages (home, animals, profile, questionnaire, results, staff area)",
        aim=("Builds every screen from the Design's interface designs: Home and menu (Design: Main Menu), the animal list and "
             "profile (Design: Animal Viewing Page), the four-step questionnaire and results (Design: Compatibility algorithm "
             "and questionnaire, Questionnaire Plan) and the staff page (Design: Admin Page). Pages only call the stage 1-2 "
             f"code. Also adds headless page tests. Commit {COMMITS[3]}; all five components."),
        tests=[("B1", "A card for every animal", "13 animals", "13 cards", "As expected", "Pass", "test_browse_shows_a_card_for_every_animal; Screen 02"),
               ("B2", "Filter rabbits", "Species = Rabbit", "4 rabbits", "As expected", "Pass", "Screen 03"),
               ("B6", "Profile from database", "Luna's id", "Luna's details", "As expected", "Pass", "test_profile_reads_from_database; Screen 04"),
               ("D2", "Blank answer blocks Next", "step 1, one blank", "Error, same step", "First run: test crashed; later: 1 box not 2", "Fail, then Pass", "Ev 3a, 3b; Screen 07"),
               ("D7", "Questionnaire needs login", "no session", "'Please log in'", "As expected", "Pass", "test_questionnaire_needs_login"),
               ("E10", "At least 4 results", "submitted answers", "5 cards, best first", "As expected", "Pass", "test_results_show_at_least_four_ranked_matches; Screen 10"),
               ("C8", "Staff page not routable for adopters", "adopter opens it by name", "No such page", "As expected", "Pass", "test_admin_page_is_not_routable_for_adopters")],
        failed=[("All 9 page tests", "Every page test failed at once: 'AppTest script not found at .../tests/streamlit_app.py'.",
                 "AppTest.from_file resolves a relative path from the test file's folder, not the folder pytest runs from.",
                 "Gave the entry script as an absolute path built from the test file's location (ENTRY), so the tests run "
                 "from any folder.", "Pass: 9 of 9 (later 117 in all)"),
                ("D2", "After errors were merged into one box, test D2 failed: 'assert 1 == 2' (it counted two error boxes).",
                 "The test checked the old design (one box per error), not the behaviour that matters.",
                 "Changed the test to expect one box that contains both messages; the behaviour is what users see.",
                 "Pass: 117 passed (Ev 3)")],
        review=("Developer review: each page compared with its interface design and its criteria, in a browser at laptop width. "
                "Found: one red box per error made long forms noisy; after logging in, a staff user was sent to the staff page "
                "before the menu had registered it; the first test for 'adopters cannot open the staff page' caught any error, "
                "so it would have passed for the wrong reason."),
        changes=("All errors for a form now show in one box (usability, S6), which caused the second failed test above. After "
                 "login every user goes to Home and staff find 'Manage animals' in the menu. The staff-page test now expects "
                 "the exact 'Could not find a navigation page' error, and a second test checks that the page's own guard stops "
                 "an adopter who reaches it directly."),
        code=[("Role-aware menu (streamlit_app.py)", "nav"),
              ("Questionnaire step logic (webui/views/questionnaire.py)", "q_step"),
              ("Page guards (webui/state.py)", "guards")],
        screens=[("01-home.png", "Screen 01: Home. Purpose, suitability focus, guidance note and the questionnaire button (2.1, 2.2, 7.6)."),
                 ("02-browse.png", "Screen 02: Animals. 13 cards with photo, name, species, breed and age; filters and search (3.1-3.3)."),
                 ("04-profile.png", "Screen 04: Profile read from the database, with the back link (4.1-4.4)."),
                 ("07-questionnaire-blocked.png", "Screen 07: Next pressed with a blank answer: one box lists what is missing (6.4)."),
                 ("10-results.png", "Screen 10: My matches: score, category, met / not met and the guidance note (7.2-7.6)."),
                 ("13-admin-list.png", "Screen 13: Staff area for a staff account: list, add, edit or delete (8.1-8.4).")],
        evidence_text=("stage3-pytest.txt", "Ev 3: the stage 3 test run (docs/evidence/stage3-pytest.txt)"),
    ),
    4: dict(
        title="Stage 4: End-to-end run, screenshots and documentation",
        aim=("Runs the whole system as a user would, in a real browser driven by a script (docs/tools/capture_screens.py), at "
             "laptop (1280 px) and tablet (820 px) widths. It produces the 16 screenshots used as evidence, plus the README, a "
             f"short write-up and a comparison page. Commit {COMMITS[4]}; checks criteria 1-9 together."),
        tests=[("T2", "Tablet width", "820 px wide", "No sideways scrolling", "As expected", "Pass", "Screen 16"),
               ("F4-F5", "Register with errors, then log in", "invalid then valid details", "Errors, then logged in", "As expected", "Pass", "Screens 05, 12"),
               ("F6-F9", "Questionnaire to results", "full answers", "Ranked results with warnings", "As expected", "Pass", "Screens 06-11"),
               ("F10-F12", "Staff list, add with errors, edit", "staff account", "As planned", "As expected", "Pass", "Screens 13-15"),
               ("E2E-1", "Fill the Age box", "label 'Age'", "Box filled", "Script stopped: 2 elements matched", "Fail, then Pass", "capture_screens.py"),
               ("E2E-2", "Open My matches after login", "go to its address", "Results page", "Logged out", "Fail, then Pass", "capture_screens.py")],
        failed=[("E2E-1", "The browser script stopped: the label 'Age' matched two elements (the box and its 'Help for Age' button).",
                 "Finding by label matches any label that contains the word unless told to match exactly.",
                 "Used an exact label match (exact=True).", "Pass: all 16 screenshots produced"),
                ("E2E-2", "After logging in, opening a page by its address showed the login page again.",
                 "Typing an address reloads the page, which starts a new Streamlit session, so the login is lost.",
                 "The script now moves between pages with the menu, as a user would. The behaviour itself is a real limitation, "
                 "recorded in the evaluation (5.3, 5.4).", "Pass: all 16 screenshots produced")],
        review=("Developer review of the 16 screenshots against criteria 1-9 (no client was available to review them). Everything "
                "needed was visible, at both widths. Found: a full page reload logs the user out (E2E-2), and nothing on screen "
                "says so."),
        changes=("Not changed in code: fixing it needs a signed browser cookie, which Streamlit does not provide; recorded as a "
                 "limitation with a planned fix (5.5) instead of a rushed change. The README explains how to run and test the "
                 "system so someone else can maintain it."),
        code=[("Browser script: one screenshot step (docs/tools/capture_screens.py)", "capture")],
        screens=[("16-tablet-browse.png", "Screen 16: The animal list at tablet width (820 px): cards rearrange, nothing is cut off (1.2)."),
                 ("11-results-warning.png", "Screen 11: A match with an important requirement not met: orange warning (7.5).")],
        evidence_text=None,
    ),
    5: dict(
        title="Stage 5: Design re-check and fixes",
        aim=("Re-reads every validation list and table design in the Design and compares each with the code, writing a test "
             f"first for anything missing. Commit {COMMITS[5]}; components A, C and E."),
        tests=[("A11", "Name format", "Mary-Jane, O'Neill / 12345, Sam3, Sam!", "Letters only", "First: 3 accepted", "Fail, then Pass", "Ev 5a, 5b"),
               ("C11", "Breed rules", "Mixed / X, ###", "X, ### rejected", "First: accepted", "Fail, then Pass", "Ev 5a, 5b"),
               ("C11b", "Animal name format", "R2 / 123, Luna!", "123, Luna! rejected", "First: accepted", "Fail, then Pass", "Ev 5a, 5b"),
               ("E11", "calculated_at stored", "submission", "Timestamp", "First: no column", "Fail, then Pass", "Ev 5a, 5b"),
               ("E11b", "Old database upgraded", "database without the column", "Column added", "First: missing", "Fail, then Pass", "Ev 5a, 5b"),
               ("A7", "Older duplicate-email test", "'Sam 2', SAM@example.com", "'already exists'", "KeyError 'email'", "Fail, then Pass", "Ev 5c")],
        failed=[("A11, C11, E11 (9 cases)", "9 new tests failed on their first run, as expected for tests written before the fix.",
                 "Design rules missing from the code (see stages 1 and 2).", "Added the rules and the column.", "Pass"),
                ("A7", "After the fix, an older test failed with KeyError 'email'.",
                 "Its second user was called 'Sam 2'. The new name rule rejected that before the duplicate-email check ran, "
                 "so the test no longer tested what its name says.",
                 "Changed the test's name to 'Sam Two' so it again tests the duplicate email; the rule itself is right.",
                 "Pass: 134 passed (Ev 5b)")],
        review=("Developer review: listed every rule in the Design's validation sections and variables tables and ticked each "
                "against a test. After the fixes every listed rule has a test. Two Design points were kept as decisions rather "
                "than changes: login is by email (the Design mentions both), and passwords need at least 8 characters (the Design "
                "says both 'minimum of eight' and 'more than 8')."),
        changes=("None beyond the fixes: the full suite was run again (134 passed) and the screenshots still match, because the "
                 "screens did not change."),
        code=[("Name and breed rules (pawmatch/validation.py)", "check_name"),
              ("Upgrading an older database (pawmatch/db.py)", "init_schema")],
        evidence_text=("stage5-pytest.txt", "Ev 5b: the stage 5 run after the fixes (docs/evidence/stage5-pytest.txt)"),
    ),
}


def code_snippet(key: str) -> str:
    if key == "matching_top":
        text = (ROOT / "pawmatch/matching.py").read_text()
        return text[text.index("WEIGHTS"):text.index("def category_for")].rstrip()
    if key == "score":
        return code_of(matching.score_animal)
    if key == "rank_key":
        return code_of(matching.rank_key) + "\n\n" + code_of(matching.rank_animals)
    if key == "validate_step":
        return code_of(validation.validate_step)
    if key == "hash":
        return code_of(auth.hash_password) + "\n\n" + code_of(auth.verify_password)
    if key == "login":
        return code_of(auth.login)
    if key == "services":
        return code_of(services.add_animal) + "\n\n" + code_of(services.remove_animal)
    if key == "list_animals":
        return code_of(db.list_animals)
    if key == "nav":
        return file_lines("streamlit_app.py", "pages = [", 12)
    if key == "q_step":
        return file_lines("webui/views/questionnaire.py", "user = require_login()", 30)
    if key == "guards":
        return file_lines("webui/state.py", "def require_login", 17)
    if key == "capture":
        return file_lines("docs/tools/capture_screens.py", "def shot(", 18)
    if key == "check_name":
        return code_of(validation._check_name) + "\n\n" + file_lines("pawmatch/validation.py", 'breed = _text(raw.get("breed"))', 8)
    if key == "init_schema":
        return code_of(db.init_schema)
    raise KeyError(key)


CODE_NOTES = {
    "matching_top": "The weights are the Design's table. MAX_POINTS is worked out from them, so changing a weight cannot break the percentage.",
    "score": "Each factor gives a fraction (1, 0.5 or 0) times its weight. Unmet important factors also go into warnings. The percentage is rounded to one decimal place.",
    "rank_key": "Sorting by a tuple applies the rules in order: warnings, points with bonus, percentage, then name and id, so ties always come out the same way.",
    "validate_step": "Each step validates only its own questions, so users get messages for the step they are on.",
    "hash": "A new 16-byte salt for every password; the parameters are stored with the hash so they can be raised later. compare_digest takes the same time whether the first or last character differs.",
    "login": "Validation, then lookup, then hash check. Any failure returns the same message.",
    "services": "require_admin raises AccessDenied before anything is validated or stored.",
    "list_animals": "Filters add '?' placeholders; the user's text only ever goes into params.",
    "nav": "The staff page is only added to the menu for admin users, so for anyone else its address does not exist.",
    "q_step": "The step number and answers live in the session, so Back keeps earlier answers. validate_step runs before moving on.",
    "guards": "Every protected page starts with one of these; require_staff builds on require_login.",
    "capture": "The page height is measured first, so each screenshot shows the whole page.",
    "check_name": "One function serves people and animals; animals may also use digits. Every name must contain a letter.",
    "init_schema": "CREATE TABLE IF NOT EXISTS leaves old tables alone, so the new column is added by hand when it is missing.",
}


# ---------------------------------------------------------------- build

def build() -> None:
    m = measure()
    d = docx.Document(str(MASTER))
    els = list(d.element.body.iterchildren())

    def text_of(el):
        return "".join(t.text or "" for t in el.iter(qn("w:t")))

    boxes = {i: el for i, el in enumerate(els) if el.tag == qn("w:p")
             and re.match(r"\s*\[(TO WRITE|HOW THIS DOCUMENT WORKS|NOTE)\]", text_of(el))}
    assert len(boxes) == 40, len(boxes)

    def find(start: int, predicate):
        return next(i for i in range(start, len(els)) if predicate(els[i]))

    def para_index(text: str, start: int = 0) -> int:
        return find(start, lambda e: e.tag == qn("w:p") and text_of(e).strip().startswith(text))

    def table_after(i: int) -> int:
        return find(i, lambda e: e.tag == qn("w:tbl"))

    criteria = criteria_rows(m)
    crit_table = Table(els[table_after(para_index("Success Criteria"))], d)
    requirements = [row.cells[3].text.strip() for row in crit_table.rows[1:]]
    assert len(requirements) == 38 == len(criteria), len(requirements)

    # Cover: replace the kit instructions with an honest notice.
    b = Block(d, boxes[14], note=False)
    b.para("**Model version.** This copy keeps Sienna's analysis and design text as written and fills every gap with "
           "work produced by an AI (Claude Opus 5.5, Anthropic) on 23 October 2026 from her analysis and design, as a "
           "comparison. It is not her work and must not be handed in as hers (JCQ AI rules). Each addition is marked "
           "'Model version addition'. The code it describes is in the rebuild/ folder.", size=10)

    # Analysis: measurable criteria (after her table).
    crit_el = crit_table._tbl
    b = Block(d, crit_el.getnext(), wrap=True)
    b.heading("How each success criterion will be measured", 3)
    b.para("Each requirement in the table above is numbered by group and row: 5.2 is the second requirement of group 5. "
           "Where possible the measure is a number (a count, a time, a capacity or a rating), so the evaluation can say met, "
           "partly met or not met. Tests named T are timing and capacity checks in the post-development plan.", size=9)
    b.table(["#", "Requirement (from the table above)", "How it will be measured"],
            [(c[0], req, c[1]) for c, req in zip(criteria, requirements)], widths=[0.4, 3.0, 3.0])
    b.close()

    # Design: hierarchy chart and structure.
    b = Block(d, boxes[557], wrap=True)
    b.heading("Hierarchy chart", 3)
    b.image("d01-hierarchy.png", "Diagram D1: PawMatch broken down into its five components and their sub-tasks.", 6.3)
    b.para("Why this breakdown: each box is small enough to build and test on its own, and the order follows what each part "
           "needs. Accounts and the database come first because every other part needs a logged-in user and stored animals; "
           "browsing needs animals; matching needs both the questionnaire answers and the animals. The scoring and validation "
           "boxes need no screen at all, so they can be built and fully tested before any page exists (Development, stage 1).")
    b.heading("Structure of the solution", 3)
    b.image("d02-structure.png", "Diagram D2: modules and layers. Pages only call services; only db.py runs SQL.", 6.3)
    b.para("Two layers. The pawmatch package holds all rules and data access and never imports Streamlit, so every rule can be "
           "unit-tested. The webui pages read input, call one service and show the result. This means a change to a rule "
           "happens in one place, and a page cannot skip a check because the check is inside the service, not the page.")
    b.close()

    # Design: ER diagram after the relationships text.
    b = Block(d, els[para_index("Validation", para_index("Database structure"))], wrap=True)
    b.heading("Entity relationship diagram", 3)
    b.image("d03-er.png", "Diagram D3: the four tables, their keys and the one-to-many links.", 6.3)
    b.para("Two fields are added to the questionnaire table (other_pets, experience) so the answers to those questions are "
           "stored even though the Design does not score them, and match_results also stores the met / unmet lists and the "
           "bonus, so the results page can be shown again without re-scoring. Foreign keys use ON DELETE CASCADE so no result "
           "can point to an animal or response that no longer exists.")
    b.heading("Data structures and classes", 3)
    b.image("d08-classes.png", "Diagram D4: the four data classes passed between the modules.", 6.3)
    b.table(["Structure", "Type", "Why this structure", "Validation"], [
        ("User, Animal, Answers, MatchResult", "Frozen dataclasses",
         "Named fields instead of loose tuples; frozen so scoring cannot change an animal or answer by mistake", "Only built from validated or stored values"),
        ("WEIGHTS", "Dictionary factor → points", "The Design's weight table in one place; MAX_POINTS = sum of WEIGHTS", "Test E1 checks 20/15/15/12/10"),
        ("QUESTION_STEPS", "Tuple of (title, question names)", "The questionnaire plan as data: the page and the validator both use it", "Test D1: every question once"),
        ("errors", "Dictionary field → message", "Every validator returns one, so a page can show all problems at once", "Empty dictionary means valid"),
        ("session.user_id, session.q_step, session.q_answers", "Streamlit session state", "Who is logged in, and progress through the questionnaire",
         "user_id re-checked against the database on every page"),
        ("results", "List of MatchResult, sorted", "Ranked order is the output; a list keeps it", "Every animal appears once"),
    ], widths=[1.6, 1.2, 2.4, 1.6])
    b.close()

    # Pseudocode boxes.
    def pseudo_block(box_index, title, parts, fits, images=()):
        blk = Block(d, boxes[box_index], wrap=True)
        blk.heading(title, 3)
        for name, caption in images:
            blk.image(name, caption, 5.6)
        for text in parts:
            blk.code(text)
        blk.para("**How it fits the whole solution.** " + fits)
        blk.close()

    pseudo_block(591, "Pseudocode: registration, login, session and role check, logout", [PSEUDO_REGISTER, PSEUDO_LOGIN],
                 "Register and Login are the only ways to get a session. Every other page starts with CurrentUser() or "
                 "RequireStaff(), so the role check written here protects the whole system. Uniqueness is checked only after "
                 "the cheap checks pass, so the database is not queried for a form that is already invalid.",
                 [("d04-flow-login.png", "Diagram D5: registration and login flowchart (model version).")])
    pseudo_block(632, "Pseudocode: staff add, edit and delete animal", [PSEUDO_ADMIN],
                 "The staff page calls AddAnimal, EditAnimal and DeleteAnimal. Each one checks the role itself, so even if the "
                 "page guard were bypassed nothing could be changed. ValidateAnimal is also used for the demo animals, so seed "
                 "data obeys the same rules as staff input.")
    pseudo_block(705, "Pseudocode: menu, home page and 'My matches' entry", [PSEUDO_MENU],
                 "BuildMenu runs on every page load. Because the staff page is only added for admins, adopters never see a "
                 "link they cannot use. The questionnaire-completed check sits on the My matches page: users who have not "
                 "finished it are sent to it.")
    pseudo_block(731, "Pseudocode: browse, filter, search and open a profile", [PSEUDO_BROWSE],
                 "The same ListAnimals function serves Home (counts), the animal list and the staff list. The profile is "
                 "opened by animal_id, so two animals with the same name can never be confused.")
    pseudo_block(765, "Pseudocode: questionnaire, compatibility score and ranking", [PSEUDO_QUESTIONNAIRE, PSEUDO_MATCH],
                 "ValidateStep stops gaps step by step; ValidateAnswers checks the whole set again before anything is stored. "
                 "SubmitQuestionnaire then joins the parts: it stores the response, calls RankAnimals (which calls ScoreAnimal "
                 "for every animal) and stores the ranked results that the My matches page shows.",
                 [("d05-flow-questionnaire.png", "Diagram D6: questionnaire flowchart (model version)."),
                  ("d06-flow-matching.png", "Diagram D7: scoring and ranking flowchart (model version).")])

    # Exact compatibility score and worked example.
    b = Block(d, boxes[824], wrap=True)
    b.heading("Compatibility score, exactly", 3)
    b.bullets([
        "Each factor gives a fraction: 1 if met, 0 if not. Activity can also give 0.5: fraction = max(0, 1 − gap ÷ 2), where gap = "
        "the animal's exercise level minus the adopter's activity level (never below 0). Being more active than needed is not penalised.",
        "points = 20 × hours + 15 × children + 15 × housing + 12 × activity + 10 × garden (maximum 72).",
        "**compatibility % = round(100 × points ÷ 72, 1)**.",
        "Hard rules (children, hours alone, space) **lose their points and give a warning**; they do not remove the animal. Animals "
        "with a warning are listed after every animal without one. Garden and activity lose points only.",
        "Categories: **Strong** 80 % or more; **Good** 60 to 79.9 %; **Possible** 40 to 59.9 %; **Low** below 40 %.",
        "Preferences (species 10, size 5) are added only to the sorting points, never to the percentage, as the Design says.",
    ])
    b.para("**Worked example.** Adopter: lives in a flat (housing 1), no garden, has children, can offer activity level 2, leaves "
           "an animal 6 hours a day, prefers dogs, no size preference.")
    b.table(["Factor (weight)", "Milo, cat: needs housing 1, no garden, child-safe, exercise 1, up to 8 h alone",
             "Oscar, dog: needs housing 1, no garden, child-safe, exercise 2, up to 4 h alone"], [
        ("Hours alone (20)", "6 ≤ 8: met → 20", "6 > 4: not met → 0, **warning**"),
        ("Children (15)", "child-safe: met → 15", "child-safe: met → 15"),
        ("Housing (15)", "1 ≥ 1: met → 15", "1 ≥ 1: met → 15"),
        ("Activity (12)", "gap max(0, 1 − 2) = 0 → 12", "gap max(0, 2 − 2) = 0 → 12"),
        ("Garden (10)", "not needed: met → 10", "not needed: met → 10"),
        ("Points", "72", "52"),
        ("Percentage", "100 × 72 ÷ 72 = 100.0 % (Strong)", "100 × 52 ÷ 72 = 72.2 % (Good)"),
        ("Preference bonus", "cat ≠ dog → 0", "dog = dog → 10"),
        ("Sorting points", "100.0", "82.2, but has a warning"),
    ], widths=[1.4, 2.6, 2.6])
    b.para("Result: Milo is listed above Oscar, and Oscar comes after every animal without a warning even though his sorting "
           "points (82.2) are higher than some of theirs. Running the real code on the same answers gives the same numbers "
           "(Milo 100.0, Oscar 72.2 with one warning); this example is reused as test data (E2, E7, E9).")
    b.close()

    # Usability features + wireframes.
    b = Block(d, boxes[825], wrap=True)
    b.heading("Usability features", 3)
    b.table(["Feature", "Where it appears", "Why it is included"], USABILITY, widths=[2.2, 1.3, 3.1])
    b.image("d07-wireframes.png", "Diagram D8: wireframes for the questionnaire step, results and staff edit screens (model version).", 6.3)
    b.close()

    # Test plans.
    b = Block(d, boxes[829], wrap=True)
    b.heading("Development test plan", 3)
    b.para("Five components, 8 to 11 tests each, mixing normal, boundary and invalid data. Each test is chosen to prove a rule "
           "from the Design works on both sides of its edge. These numbers are used in the Development section.", size=9)
    b.table(["Test", "What is tested and why", "Input data", "Expected result", "Type"], DEV_PLAN, widths=[0.45, 2.0, 1.7, 1.75, 0.7])
    b.heading("Post-development test plan", 3)
    b.para("One test per success criterion, using the measure from the Analysis, plus timing (T), robustness (R) and usability "
           "tests (U). The usability tests need real people from the stakeholder groups (adopters from the survey group and the "
           "shelter client).", size=9)
    b.table(["Test", "Criterion", "Measure / expected result"], [(f"P{c[0]}", req[:90] + ("…" if len(req) > 90 else ""), c[1])
                                                                for c, req in zip(criteria, requirements)], widths=[0.5, 2.9, 3.2])
    b.table(["Test", "What", "Who", "Expected"], [
        ("T1", "Theme and contrast", "Developer", "Text contrast at least 4.5 : 1"),
        ("T2", "Width check", "Developer, headless browser", "No sideways scrolling at 1280 and 820 px"),
        ("T3", "Menu on every page", "AppTest", "Same menu on 7 of 7 pages"),
        ("T4", "Scoring time", "Developer", "500 animals scored and stored in under 2 s"),
        ("T5", "Capacity", "Developer", "500 animals and 100 users stored and listed"),
    ] + POST_PLAN_EXTRA, widths=[0.5, 2.4, 1.7, 2.0])
    b.close()

    # ------------------------------------------------------------ Development
    b = Block(d, boxes[831])
    b.para("Development was done in five stages, each saved as a commit on the opus-rebuild branch, so every prototype "
           "can be restored. The stages follow the hierarchy chart: rules first, then storage, then pages, then a whole-system "
           "run, then a re-check against the Design. Each module was written with its tests, and the full test suite was run at "
           "the end of every stage; the output of each run is kept in docs/evidence.")
    b.table(["Stage", "Commit (prototype)", "What it added", "Tests after"], [
        ("1", COMMITS[1], "models.py, validation.py, matching.py", "73 passed"),
        ("2", COMMITS[2], "db.py, auth.py, services.py, seed.py, animal photos", "103 passed"),
        ("3", COMMITS[3], "streamlit_app.py, webui/ pages, page tests, screenshot script", "117 passed"),
        ("4", COMMITS[4], "README, write-up, comparison page, 16 screenshots", "117 passed"),
        ("5", COMMITS[5], "Design re-check: name and breed rules, calculated_at", "134 passed"),
    ], widths=[0.5, 1.3, 3.6, 1.0])
    b.para("Reviews: no client or stakeholder was available for this model version, so each review below is a developer review "
           "against the Design and success criteria, and says so. In a real project each one would also be shown to the client.",
           italic=True, size=9)
    b.close()

    stage_heads = [i for i, el in enumerate(els) if el.tag == qn("w:p") and text_of(el).startswith("Stage ")
                   and i > 831 - 2 and i < 908]
    assert len(stage_heads) == 5, stage_heads
    for n, head_i in enumerate(stage_heads, start=1):
        st = STAGES[n]
        Paragraph(els[head_i], d).text = st["title"]
        aim_box, code_box, review_box, change_box = [i for i in sorted(boxes) if head_i < i < (stage_heads[n] if n < 5 else 908)]
        blk = Block(d, boxes[aim_box], note=False)
        blk.para(st["aim"])
        blk.close()
        blk = Block(d, boxes[code_box], note=False)
        for caption, key in st["code"]:
            blk.para(f"**{caption}.** {CODE_NOTES[key]}", size=9)
            blk.code(code_snippet(key), size=7)
        if st.get("evidence_text"):
            name, caption = st["evidence_text"]
            blk.para(f"**Prototype evidence.** {caption}:", size=9)
            blk.code(evidence(name))
        for name, caption in st.get("screens", []):
            blk.image(name, caption, 5.8)
        blk.close()
        testing_tbl = table_after(code_box)
        fill_table(d, els[testing_tbl], st["tests"], size=7)
        failed_tbl = table_after(testing_tbl + 1)
        fill_table(d, els[failed_tbl], st["failed"], size=7)
        if n == 3:
            blk = Block(d, els[failed_tbl].getnext(), note=False)
            blk.para("Ev 3a, the first failure (docs/evidence/stage3-fail1-apptest-path.txt):", size=8.5, italic=True)
            blk.code(evidence("stage3-fail1-apptest-path.txt", 3), size=6.5)
            blk.para("Ev 3b, the second failure (docs/evidence/stage3-fail2-error-box.txt):", size=8.5, italic=True)
            blk.code(evidence("stage3-fail2-error-box.txt", 3), size=6.5)
            blk.close()
        if n == 5:
            blk = Block(d, els[failed_tbl].getnext(), note=False)
            blk.para("Ev 5a, the tests written first, before the fix (docs/evidence/stage5-fail-design-recheck.txt):", size=8.5, italic=True)
            blk.code(evidence("stage5-fail-design-recheck.txt", 11), size=6.5)
            blk.para("Ev 5c, the older test that the new rule broke (docs/evidence/stage5-fail-regression-auth.txt):", size=8.5, italic=True)
            blk.code(evidence("stage5-fail-regression-auth.txt", 3), size=6.5)
            blk.close()
        blk = Block(d, boxes[review_box], note=False)
        blk.para(st["review"])
        blk.close()
        blk = Block(d, boxes[change_box], note=False)
        blk.para(st["changes"])
        blk.close()

    # ------------------------------------------------------------ Testing to inform evaluation
    b = Block(d, boxes[908])
    b.para("All tests below were run on the finished system (commit " + COMMITS[5] + "). Function tests (F) follow the main "
           "paths; robustness tests (R) try wrong, extreme or hostile input; T tests are measured. 'Actual' is what happened. "
           "Screens are in docs/img and the automated tests are in tests/.")
    b.para(f"**Measured results.** Scoring and storing 500 animals: mean {m['submit_mean']} s over 5 runs, slowest "
           f"{m['submit_max']} s (target under 2 s). Listing 500 animals from the database: {m['browse_query']} s. Rendering the "
           f"animal page with 500 animals: {m['browse_page']} s at worst over 3 headless runs, with {m['browse_cards']} cards. "
           f"Capacity: {m['animals']} animals and {m['users']} users stored and read back. Contrast: text {m['contrast_text']} : 1, "
           f"button text {m['contrast_button']} : 1.")
    b.code(evidence("stage5-pytest.txt", 2))
    b.close()
    func_rows = [
        ("F1", "2.1, 2.2", "Open Home; click the button", "Purpose shown; questionnaire opens", "As expected", "Screen 01"),
        ("F2", "3.1-3.3", "Open Animals; filter Rabbit", "13 cards; 4 rabbits", "As expected", "Screens 02, 03"),
        ("F3", "3.4, 4.1-4.4", "View Luna's profile, then Back", "All details; back to list", "As expected", "Screen 04"),
        ("F4", "5.1, 5.2", "Register with errors, then correctly", "All errors in one box; then account made", "As expected", "Screen 05"),
        ("F5", "5.3", "Log in, then log out", "Menu shows My account; then Log in", "As expected", "auth tests"),
        ("F6", "6.1-6.3", "Answer steps 1-4", "Progress bar, drop-downs, review", "As expected", "Screens 06, 08, 09"),
        ("F7", "7.1, 7.2, 9.3", "Submit the answers", "Every animal scored and stored", "As expected", "test_adopter_submission_stores_ranked_results"),
        ("F8", "7.3, 7.4, 7.6", "Open My matches", "5 shown, best first, met / not met, guidance note", "As expected", "Screen 10"),
        ("F9", "7.5", "Answers that fail hours alone", "Orange warning", "As expected", "Screen 11"),
        ("F10", "5.4, 8.1", "Log in as staff", "'Manage animals' in the menu", "As expected", "Screen 13"),
        ("F11", "8.2, 9.2", "Add an animal", "Stored and listed", "As expected", "test_admin_can_add_edit_and_delete"),
        ("F12", "8.3, 4.3, 9.4", "Edit the breed", "New breed on the profile", "As expected", "Screen 15"),
        ("F13", "8.4", "Tick confirm, Delete", "Animal and its results removed", "As expected", "test_delete_removes_animal_and_its_stored_results"),
        ("R1", "5.2", "Age 17, 2.5, abc; email two@@x.com", "Each rejected with its message", "As expected", "test_registration_age_boundaries"),
        ("R2", "5.5", "Wrong password; unknown email", "Same message; no session", "As expected", "Screen 12"),
        ("R3", "6.4", "Next with a blank answer", "Stays on step, error shown", "As expected", "Screen 07"),
        ("R4", "6.4", "Submit 8 of 9 answers", "Nothing stored", "As expected", "test_incomplete_submission_saves_nothing"),
        ("R5", "8.1, 8.5", "Adopter asks for the staff page by name", "No such page", "As expected", "test_admin_page_is_not_routable_for_adopters"),
        ("R6", "8.2", "Add with blanks and age 31", "Every error listed; nothing stored", "As expected", "Screen 14"),
        ("R7", "8.3", "Edit an animal deleted in another tab", "'That animal no longer exists.'", "As expected", "test_edit_of_deleted_animal_reports_error"),
        ("R8", "8.5", "Adopter reaches the staff page directly", "'This page is for shelter staff only.'", "As expected", "test_admin_page_guard_stops_adopters_even_if_reached_directly"),
        ("R9", "9.1", "Search ' OR 1=1 --", "No animals, no error", "As expected", "test_search_text_is_treated_as_data_not_sql"),
        ("R10", "8.2", "Upload a .gif; a 2 MB + 1 byte file", "Rejected", "As expected", "test_image_type_and_size"),
        ("R11", "9.1", "Insert species 'Hamster' directly into SQLite", "Database refuses it", "As expected", "test_database_constraints_back_up_validation"),
        ("R12", "5.3", "Reload the browser page while logged in", "Still logged in", "Logged out", "Capture run (E2E-2)"),
        ("T4", "7.2", "500 animals, 5 submissions", "Under 2 s", f"Mean {m['submit_mean']} s", "Measured above"),
        ("T5", "9.1", "500 animals, 100 users", "All stored and listed", f"{m['animals']} / {m['users']}", "Measured above"),
    ]
    func_i = para_index("4.1", 908)
    fill_table(d, els[table_after(func_i)], func_rows, size=7)
    b = Block(d, els[table_after(func_i)].getnext(), note=False)
    for name, caption in [
        ("05-register-errors.png", "Screen 05 (F4, R1): registration with several mistakes. Every problem is listed in one box and the typed values stay."),
        ("12-login-error.png", "Screen 12 (R2): a wrong password gives the same message as an unknown email."),
        ("09-questionnaire-review.png", "Screen 09 (F6): the review step lists every answer before submitting."),
        ("14-admin-add-errors.png", "Screen 14 (R6): the staff form refuses an incomplete animal and lists each field to fix."),
        ("15-admin-edit.png", "Screen 15 (F12, F13): editing an animal; Delete stays disabled until the confirmation is ticked."),
    ]:
        b.image(name, caption, 5.8)
    b.close()
    use_i = para_index("4.2", func_i)
    fill_table(d, els[table_after(use_i)], [
        ("Developer (not a stakeholder)", "U1: register and log in", "Done in 4 screens; errors clear (Screen 05)", "Not collected", "Needs a real adopter"),
        ("Developer (not a stakeholder)", "U2: complete the questionnaire", "4 steps + review; blank answer blocked (Screens 06-09)", "Not collected", "Needs a real adopter"),
        ("Developer (not a stakeholder)", "U3: explain the top match", "Met / not met list and warning are readable (Screens 10, 11)", "Not collected", "Needs a real adopter"),
        ("Developer (not a stakeholder)", "U4: add, edit, delete an animal", "All three done; delete needs the tick (Screens 13-15)", "Not collected", "Needs the shelter client"),
        ("Developer (not a stakeholder)", "U5: use it at tablet width", "No sideways scrolling at 820 px (Screen 16)", "Not collected", "Real tablet not tried"),
    ], size=7)
    b = Block(d, els[table_after(use_i)].getnext(), note=False)
    b.para("**What this shows and what it does not.** The walkthrough was done by the developer in a headless browser using the "
           "planned usability tasks. It shows every task can be completed and the usability features are present. It is not "
           "usability testing with stakeholders: no adopter or member of shelter staff tried the system, so there are no ratings. "
           "This is why criterion 6.2 is only partly met; running U1-U5 with five adopters and the client is the first item in "
           "Future development.")
    b.close()

    # ------------------------------------------------------------ Evaluation
    b = Block(d, boxes[916])
    met = sum(1 for c in criteria if c[3] == "Met")
    partly = [c[0] for c in criteria if c[3] == "Partly met"]
    b.para(f"Each requirement is cross-referenced to the tests in section 4 (F, R, T) and to the development tests. Of 38 "
           f"requirements, {met} are met and {len(partly)} are partly met ({', '.join(partly)}); none are unmet. 'Met' is only "
           "used where a test or screenshot shows the measure from the Analysis was reached.")
    b.close()
    eval_table = Table(els[table_after(para_index("5.1", 916))], d)
    group_rows = list(eval_table.rows[1:])
    by_group: dict[str, list] = {}
    for c, req in zip(criteria, requirements):
        by_group.setdefault(c[0].split(".")[0], []).append((c, req))
    for row in group_rows:
        group = row.cells[0].text.strip().split()[0]
        items = by_group[group]
        verdicts = {c[3] for c, _ in items}
        set_cell(row.cells[1], f"{len(items)} requirements, below", size=7, bold=True)
        set_cell(row.cells[3], "Met" if verdicts == {"Met"} else "Partly met", size=7, bold=True)
        last = row._tr
        for c, req in items:
            new = eval_table.add_row()
            for cell, text in zip(new.cells, (c[0], req, c[2], c[3], c[4])):
                set_cell(cell, text, size=7)
            last.addnext(new._tr)
            last = new._tr

    b = Block(d, boxes[921], note=False)
    b.table(["Usability feature", "Evidence", "Worked?", "How to improve"], [
        ("Calm theme, one file", f"Screens 01-16; contrast {m['contrast_text']} : 1", "Yes", "Ask testers about the colours (U1-U5)"),
        ("Same menu on every page, by role", "T3; R5; Screens 10, 13", "Yes", "Show who is logged in next to the menu"),
        ("Questionnaire in steps with progress bar", "F6; Screens 06-09", "Yes, but not rated by users", "Run U2 with five adopters"),
        ("Drop-downs only", "F6; R3", "Yes: no invalid answer can be typed", "Radio buttons for short lists may be quicker on tablets"),
        ("All errors in one box", "F4, R6; Screens 05, 14", "Yes", "Also mark the field itself red"),
        ("Animal cards", "F2; Screens 02, 16", "Yes, also at tablet width", "Add 'good with children' icons on the card"),
        ("Score bar, category, met / not met", "F8; Screen 10", "Yes", "Open the met / not met list for the top result by default"),
        ("Warnings for important needs", "F9; Screen 11", "Yes", "Link the warning to the profile section it refers to"),
        ("Guidance note", "Screens 01, 10", "Yes", "None needed"),
        ("Delete confirmation", "F13; Screen 15", "Yes", "Offer 'mark as adopted' instead of deleting (5.5)"),
        ("Back links", "F3; test B8", "Yes", "None needed"),
    ], widths=[1.6, 1.6, 1.4, 2.0])
    b.close()
    b = Block(d, boxes[923], note=False)
    b.table(["Criterion", "Why it is not fully met", "How further development would address it"], [
        ("6.2 Clear sections (rated 8/10 by testers)", "The sections are built and tested, but the rating needs real users and none "
         "were available for this model version.", "Run U2 with five adopters from the survey group; change wording where the score is below 8."),
        ("8.1 Separate admin login", "Staff log in on the same form as adopters; the system then gives them the staff page. Access "
         "is safe (R5, R8) but the login itself is not separate.", "Add a 'Staff login' page that only accepts admin accounts and "
         "remove staff access from the normal form."),
    ], widths=[1.6, 2.5, 2.5])
    b.para("Also noted although the criterion is met: 5.3 (log in and out) works, but a full page reload logs the user out (R12). "
           "1.2 was checked at tablet width in a browser, not on a real tablet or phone.", size=9)
    b.close()
    b = Block(d, boxes[925], note=False)
    b.para("**Maintenance.** The code is split so each change has one place to go: weights and cut-offs at the top of "
           "matching.py; every validation rule in validation.py; all SQL in db.py; colours in one 15-line theme file. Each "
           "function has a comment saying what it does and why. 134 automated tests run in about 5 seconds, so a maintainer "
           "can change a rule and know at once whether anything broke; this is how the stage 5 regression was caught. The "
           "README explains how to run, test and add a staff account, and the database upgrades itself when a column is added "
           "(stage 5).")
    b.para("**Limitations.**")
    b.bullets([
        "One shelter only, and three species, as the Analysis planned.",
        "A page reload logs the user out (Streamlit keeps the login in the browser session).",
        "No animal status: removing an adopted animal deletes the record and the results that mention it.",
        "Other pets and experience are asked and stored but not scored, because animals have no matching fields yet.",
        "No password reset and no limit on login attempts.",
        "Not tested with real users or on a real tablet or phone.",
        "Animal photos are stored as files on the same computer; a hosted version would need shared storage.",
    ])
    b.close()
    b = Block(d, boxes[927], note=False)
    b.table(["Improvement", "How"], FURTHER, widths=[1.8, 4.8])
    b.close()

    # ------------------------------------------------------------ Appendices
    b = Block(d, boxes[929], note=False)
    b.para("This whole model version was produced with AI, as listed below. A record of every change is the git history of the "
           "opus-rebuild branch.", size=9)
    b.close()
    fill_table(d, els[table_after(boxes_index(boxes, 929))], [
        ("23 Oct 2026", "Claude Opus 5.5 (Anthropic)", "Rebuild the app from Sienna's analysis and design", "All code and tests", "rebuild/", "Git history"),
        ("23 Oct 2026", "Claude Opus 5.5", "Fill every gap in the NEA document", "All model additions", "Sections 1-5", "This document"),
        ("23 Oct 2026", "Claude Opus 5.5 (script)", "Draw the diagrams", "Diagrams D1-D8", "Design", "docs/tools/make_diagrams.py"),
        ("23 Oct 2026", "Claude Opus 5.5 (script)", "Take the screenshots", "Screens 01-16", "Development, Testing", "docs/tools/capture_screens.py"),
        ("23 Oct 2026", "Claude Haiku 5.5", "Summarise the document structure", "Planning only", "None", "None"),
    ], size=7)
    b = Block(d, boxes[933], note=False)
    for ref in [
        "Sienna's Analysis references (above) are kept unchanged.",
        "Streamlit (2026) Streamlit documentation: st.navigation, st.Page and AppTest. Available at: https://docs.streamlit.io/ (Accessed: 23 October 2026).",
        "Python Software Foundation (2026) hashlib: scrypt. Available at: https://docs.python.org/3/library/hashlib.html (Accessed: 23 October 2026).",
        "SQLite (2026) SQLite foreign key support. Available at: https://www.sqlite.org/foreignkeys.html (Accessed: 23 October 2026).",
        "OWASP (2026) Password storage cheat sheet. Available at: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html (Accessed: 23 October 2026).",
        "W3C (2018) Web Content Accessibility Guidelines 2.1: contrast (minimum). Available at: https://www.w3.org/TR/WCAG21/#contrast-minimum (Accessed: 23 October 2026).",
        "pytest (2026) pytest documentation. Available at: https://docs.pytest.org/ (Accessed: 23 October 2026).",
        "Microsoft (2026) Playwright for Python. Available at: https://playwright.dev/python/ (Accessed: 23 October 2026).",
    ]:
        b.para(ref, size=9)
    b.close()

    for el in boxes.values():
        el.getparent().remove(el)
    d.save(str(OUT))
    print("saved", OUT, m)


def boxes_index(boxes: dict, i: int) -> int:
    return i


if __name__ == "__main__":
    build()
