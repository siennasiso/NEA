"""Draw the design diagrams for the NEA write-up into docs/img/ (matplotlib only).

    .venv/bin/python docs/tools/make_diagrams.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle

OUT = Path(__file__).resolve().parents[1] / "img"
GREEN, PALE, CREAM, INK, GREY, AMBER = "#2f7d6d", "#e8f0ec", "#f7f5f0", "#24312d", "#8a948f", "#f3d9a4"


def canvas(w: float, h: float):
    fig, ax = plt.subplots(figsize=(w, h), dpi=150)
    ax.set_xlim(0, w * 10)
    ax.set_ylim(0, h * 10)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fc=PALE, ec=GREEN, size=8, bold=False, round_=True, align="center"):
    style = "round,pad=0.02,rounding_size=1.2" if round_ else "square,pad=0.02"
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=style, fc=fc, ec=ec, lw=1.2))
    tx = x if align == "center" else x - w / 2 + 1
    ax.text(tx, y, text, ha=align, va="center", fontsize=size, color=INK, wrap=True,
            fontweight="bold" if bold else "normal", family="DejaVu Sans")


def diamond(ax, x, y, w, h, text, size=7.5):
    ax.add_patch(Polygon([(x, y + h / 2), (x + w / 2, y), (x, y - h / 2), (x - w / 2, y)],
                         closed=True, fc=AMBER, ec="#b98a2f", lw=1.2))
    ax.text(x, y, text, ha="center", va="center", fontsize=size, color=INK)


def arrow(ax, x1, y1, x2, y2, label="", lx=0.0, ly=0.0, color=INK):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0, shrinkA=0, shrinkB=0))
    if label:
        ax.text((x1 + x2) / 2 + lx, (y1 + y2) / 2 + ly, label, fontsize=7, color=GREEN, ha="center",
                va="center", fontweight="bold", bbox=dict(fc="white", ec="none", pad=0.5))


def line(ax, pts, color=INK):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=1.0)


def save(fig, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def hierarchy() -> None:
    fig, ax = canvas(13, 7.6)
    box(ax, 65, 70, 30, 6, "PawMatch", fc=GREEN, ec=GREEN, size=11, bold=True)
    ax.texts[-1].set_color("white")
    parts = [
        ("1  Accounts\n(User/Admin\nAuthentication)", ["Validate registration\n(name, email, age 18+,\npassword ≥ 8, confirm)",
                                                  "Check email unique", "Hash password\n(salted scrypt)",
                                                  "Log in: find user,\nverify hash", "Start session,\nroute by role", "Log out"]),
        ("2  Home page /\nmain menu", ["Check session", "Explain purpose\n(suitability first)", "Show menu for\nthe user's role",
                                      "Questionnaire done?\nshow results link\nor start button"]),
        ("3  Animal\nbrowsing", ["Read search term\n(≤ 20 chars, trimmed)", "Species and size\nfilters", "Parameterised\nquery",
                                 "Animal cards or\n'no animals' message", "Open profile\nby animal_id"]),
        ("4  Questionnaire\nand matching", ["4 steps + review\n(drop-downs only)", "Validate each step\nbefore Next",
                                           "Save response", "Score every animal\n(÷ 72 → %)", "Warnings, category,\nrank, save results",
                                           "Show top 5 (≥ 4)"]),
        ("5  Staff area\n(Administrator)", ["Role check\n(page + every action)", "Validate all\nanimal fields",
                                            "Add (INSERT)", "Edit (UPDATE)", "Delete with\nconfirmation", "Photo: type,\nsize, safe name"]),
    ]
    xs = [13, 39, 65, 91, 117]
    line(ax, [(65, 67), (65, 62.5)])
    line(ax, [(xs[0], 62.5), (xs[-1], 62.5)])
    for x, (title, subs) in zip(xs, parts):
        line(ax, [(x, 62.5), (x, 60)])
        box(ax, x, 56, 22, 8, title, fc=PALE, size=8.5, bold=True)
        line(ax, [(x - 9, 52), (x - 9, 52 - 8.2 * len(subs) + 4)])
        for i, sub in enumerate(subs):
            y = 47 - i * 8.2
            line(ax, [(x - 9, y), (x - 7.5, y)])
            box(ax, x + 2.5, y, 19, 7, sub, fc=CREAM, ec=GREY, size=6.8)
    ax.set_ylim(-4, 76)
    ax.text(65, -2.5, "All five parts read and write one SQLite database (users, animals, questionnaire_responses, match_results).",
            ha="center", fontsize=8, color=GREY, style="italic")
    save(fig, "d01-hierarchy.png")


def structure() -> None:
    fig, ax = canvas(12, 6.2)
    box(ax, 60, 57, 72, 6, "streamlit_app.py  (entry: prepare database, role-aware menu)", fc=GREEN, size=8, bold=True)
    ax.texts[-1].set_color("white")
    views = ["home", "browse", "profile", "account", "questionnaire", "results", "admin\n(staff only)"]
    for i, v in enumerate(views):
        x = 12 + i * 16
        box(ax, x, 44, 14, 6.5, f"views/{v}.py", size=7)
        arrow(ax, 60, 54, x, 47.3)
    box(ax, 26, 33, 40, 5.5, "webui/components.py  (animal card, match card, error box)", fc=CREAM, ec=GREY, size=7.5)
    box(ax, 94, 33, 40, 5.5, "webui/state.py  (session, database handle, page guards)", fc=CREAM, ec=GREY, size=7.5)
    ax.add_patch(Rectangle((2, 2), 116, 24, fc="none", ec=GREEN, ls="--", lw=1))
    ax.text(4, 24, "pawmatch/  domain layer: no Streamlit, all unit-tested", fontsize=8, color=GREEN, fontweight="bold")
    box(ax, 60, 19, 34, 5, "services.py  (validate → check role → store)", size=8, bold=True)
    arrow(ax, 60, 40.5, 60, 21.6, "pages call\nservices only", lx=0, ly=-3)
    mods = [("validation.py\nrules + messages", 14), ("auth.py\nscrypt, login,\nrequire_admin", 38), ("matching.py\nweights, %,\nwarnings, rank", 62),
            ("db.py\nSQL (parameterised)", 86), ("models.py\ndataclasses", 108)]
    for text, x in mods:
        box(ax, x, 8.5, 19, 8, text, fc=CREAM, ec=GREY, size=7)
        arrow(ax, 60, 16.5, x, 12.6)
    box(ax, 86, -5, 30, 5, "SQLite: data/pawmatch.db", fc=AMBER, ec="#b98a2f", size=7.5)
    arrow(ax, 86, 4.5, 86, -2.5)
    ax.set_ylim(-9, 62)
    save(fig, "d02-structure.png")


def er() -> None:
    fig, ax = canvas(12.5, 6.8)
    tables = {
        "users": (14, 44, ["PK user_id INTEGER", "name TEXT", "email TEXT UNIQUE", "age INTEGER ≥ 18", "password_hash TEXT",
                           "role 'user' | 'admin'", "created_at TEXT"]),
        "questionnaire_responses": (50, 44, ["PK response_id INTEGER", "FK user_id → users", "housing_level 1-3", "garden_access 0/1",
                                             "has_children 0/1", "other_pets 0/1", "experience TEXT", "activity_level 1-3",
                                             "hours_alone 0-24", "preferred_species", "preferred_size", "completed_at TEXT"]),
        "match_results": (88, 44, ["PK match_id INTEGER", "FK response_id → responses", "FK animal_id → animals", "rank INTEGER",
                                   "compatibility REAL 0-100", "category Strong/Good/\n  Possible/Low", "bonus INTEGER",
                                   "met, unmet, warnings (JSON)", "calculated_at TEXT"]),
        "animals": (88, 2, ["PK animal_id INTEGER", "name, species, breed", "age 1-30, sex, size", "personality, medical_notes",
                            "exercise_needs 1-3", "min_housing_level 1-3", "garden_required 0/1", "child_compatible 0/1",
                            "max_hours_alone 0-24", "image_path, date_added"]),
    }
    geo = {}
    for name, (x, top, fields) in tables.items():
        h = 3.6 * len(fields) + 5
        ax.add_patch(Rectangle((x - 13, top - h + 20), 26, h, fc="white", ec=GREEN, lw=1.3))
        ax.add_patch(Rectangle((x - 13, top + 20 - 5), 26, 5, fc=GREEN, ec=GREEN))
        ax.text(x, top + 17.5, name, ha="center", va="center", color="white", fontsize=8, fontweight="bold")
        for i, f in enumerate(fields):
            ax.text(x - 12, top + 13 - i * 3.6, f, fontsize=6.6, va="center", color=INK,
                    fontweight="bold" if f.startswith(("PK", "FK")) else "normal")
        geo[name] = (x, top + 20, top + 20 - h)
    arrow(ax, 27, 58, 37, 58, "1        many", ly=2.5)
    arrow(ax, 63, 58, 75, 58, "1        many", ly=2.5)
    arrow(ax, 88, geo["animals"][1], 88, geo["match_results"][2], "1 animal → many results", lx=-14)
    ax.text(60, -25, "Deleting a user deletes their responses; deleting a response or an animal deletes its results (ON DELETE CASCADE).",
            ha="center", fontsize=7.5, color=GREY, style="italic")
    ax.set_ylim(-28, 68)
    save(fig, "d03-er.png")


def classes() -> None:
    fig, ax = canvas(12, 4.6)
    specs = [
        ("User", ["user_id: int", "name: str", "email: str", "age: int", "role: str", "is_admin → bool"]),
        ("Animal", ["animal_id: int", "name, species, breed: str", "age: int; sex, size: str", "exercise_needs: 1-3",
                    "min_housing_level: 1-3", "garden_required: bool", "child_compatible: bool", "max_hours_alone: 0-24"]),
        ("Answers", ["housing_level: 1-3", "garden_access: bool", "has_children: bool", "other_pets: bool", "experience: str",
                     "activity_level: 1-3", "hours_alone: 0-24", "preferred_species, preferred_size"]),
        ("MatchResult", ["animal: Animal", "compatibility: float 0-100", "category: str", "bonus: int",
                         "met, unmet, warnings: list[str]", "ranking_points → float", "suitable → bool"]),
    ]
    for i, (name, fields) in enumerate(specs):
        x = 15 + i * 30
        h = 4 * len(fields) + 6
        ax.add_patch(Rectangle((x - 13, 44 - h), 26, h, fc="white", ec=GREEN, lw=1.3))
        ax.add_patch(Rectangle((x - 13, 39), 26, 5, fc=PALE, ec=GREEN))
        ax.text(x, 41.5, f"«frozen dataclass»  {name}", ha="center", va="center", fontsize=7.5, fontweight="bold", color=INK)
        for j, f in enumerate(fields):
            ax.text(x - 12, 35.5 - j * 4, f, fontsize=6.8, va="center")
    line(ax, [(105, 44), (105, 48), (45, 48)])
    arrow(ax, 45, 48, 45, 44.2, "MatchResult has one Animal", lx=30, ly=2)
    ax.text(60, -1, "Frozen (read-only) so a score can't change an animal or answer by accident; built by db.py from rows.",
            ha="center", fontsize=7.5, color=GREY, style="italic")
    ax.set_ylim(-3, 52)
    save(fig, "d08-classes.png")


def flow(name: str, w: float, h: float, nodes: dict, edges: list, note: str = "", loop=None) -> None:
    fig, ax = canvas(w, h)
    for key, (x, y, kind, text) in nodes.items():
        if kind == "d":
            diamond(ax, x, y, 26, 9, text)
        elif kind == "t":
            box(ax, x, y, 34, 5.5, text, fc=GREEN, size=7.5, bold=True)
            ax.texts[-1].set_color("white")
        else:
            box(ax, x, y, 26, 6.5, text, fc=PALE if kind == "p" else "#fbe7e2", ec=GREEN if kind == "p" else "#c0604a", size=7)
    for a, b, label in edges:
        (x1, y1, k1, _), (x2, y2, k2, _) = nodes[a], nodes[b]
        h1 = 4.5 if k1 == "d" else 3.25
        h2 = 4.5 if k2 == "d" else 3.25
        if abs(x1 - x2) < 1:
            arrow(ax, x1, y1 - h1, x2, y2 + h2, label, lx=4)
        elif abs(y1 - y2) < 1:
            sx = 13 if x2 > x1 else -13
            arrow(ax, x1 + sx, y1, x2 - (13 if x2 > x1 else -13), y2, label, ly=2)
        else:
            line(ax, [(x1 + (13 if x2 > x1 else -13), y1), (x2, y1)])
            arrow(ax, x2, y1, x2, y2 + (h2 if y2 < y1 else -h2), label, lx=4)
    if loop:  # draw a loop-back from the left of one node to the left of another
        (x1, y1, _, _), (x2, y2, k2, _) = nodes[loop[0]], nodes[loop[1]]
        left = min(x1, x2) - 20
        line(ax, [(x1 - 13, y1), (left, y1), (left, y2)])
        arrow(ax, left, y2, x2 - 13, y2, "loop", ly=2)
    if note:
        ax.text(w * 5, 1.5, note, ha="center", fontsize=7.5, color=GREY, style="italic")
    save(fig, name)


def flows() -> None:
    flow("d04-flow-login.png", 13, 9, {
        "s": (25, 85, "t", "Register"),
        "v": (25, 74, "p", "validate_registration(name, email,\nage, password, confirm)"),
        "ok": (25, 61, "d", "errors empty?"),
        "e1": (57, 61, "x", "Show every error in one box;\nkeep what was typed"),
        "u": (25, 48, "d", "email already used?"),
        "e2": (57, 48, "x", "'An account with this email\nalready exists.'"),
        "h": (25, 35, "p", "hash ← scrypt(password, random salt)"),
        "i": (25, 24, "p", "INSERT user (role = 'user')"),
        "l": (84, 85, "t", "Log in"),
        "f": (84, 74, "p", "find user by email\n(lower-cased)"),
        "m": (84, 61, "d", "found AND hash\nmatches?"),
        "e3": (116, 46, "x", "'Incorrect email or password.'\n(same message for both)"),
        "ss": (84, 33, "p", "session.user_id ← id\n(new session)"),
        "r": (84, 21, "d", "role = admin?"),
        "a": (84, 8, "p", "menu adds 'Manage animals'"),
    }, [("s", "v", ""), ("v", "ok", ""), ("ok", "e1", "No"), ("ok", "u", "Yes"), ("u", "e2", "Yes"), ("u", "h", "No"),
        ("h", "i", ""), ("l", "f", ""), ("f", "m", ""), ("m", "e3", "No"), ("m", "ss", "Yes"), ("ss", "r", ""),
        ("r", "a", "Yes")], "")
    flow("d05-flow-questionnaire.png", 10, 9.4, {
        "s": (40, 90, "t", "Questionnaire"),
        "c": (40, 80, "d", "logged in?"),
        "lg": (78, 80, "x", "Ask to log in or register"),
        "st": (40, 68, "p", "step ← 0; answers ← {}"),
        "sh": (40, 57, "p", "show questions of\nQUESTION_STEPS[step] (drop-downs)"),
        "nx": (40, 45, "d", "validate_step(step)\nempty?"),
        "er": (78, 45, "x", "Show errors; stay on step"),
        "lst": (40, 33, "d", "step = 3 ?"),
        "inc": (78, 33, "p", "step ← step + 1"),
        "rv": (40, 21, "p", "Review page: every answer,\nBack allowed"),
        "sb": (40, 9, "p", "validate_answers → save →\nrank → save results → Results"),
    }, [("s", "c", ""), ("c", "lg", "No"), ("c", "st", "Yes"), ("st", "sh", ""), ("sh", "nx", "Next"), ("nx", "er", "No"),
        ("nx", "lst", "Yes"), ("lst", "inc", "No"), ("lst", "rv", "Yes"), ("rv", "sb", "Submit")],
        "")
    flow("d06-flow-matching.png", 10, 9.4, {
        "s": (40, 90, "t", "rank_animals(animals, answers)"),
        "lp": (40, 79, "d", "next animal?"),
        "sc": (40, 67, "p", "earned ← Σ weight × fraction\n(hours, children, housing,\nactivity, garden)"),
        "pc": (40, 55, "p", "percent ← round(100 × earned / 72, 1)\ncategory from cut-offs"),
        "wn": (40, 43, "p", "warnings ← important factors\nnot met; bonus ← species 10 + size 5"),
        "add": (40, 31, "p", "append MatchResult"),
        "so": (80, 79, "p", "sort by (has warnings,\n−(percent+bonus), −percent, name)"),
        "sh": (80, 64, "p", "show first 5 (never < 4);\n'Show every animal' toggle"),
    }, [("s", "lp", ""), ("lp", "sc", "Yes"), ("sc", "pc", ""), ("pc", "wn", ""), ("wn", "add", ""), ("lp", "so", "No"),
        ("so", "sh", "")], loop=("add", "lp"))


def wireframes() -> None:
    fig, ax = canvas(13, 6.6)
    panels = [(2, "A  Questionnaire step (2 of 4)"), (45, "B  Results"), (88, "C  Staff area: edit / delete")]
    for x0, title in panels:
        ax.add_patch(Rectangle((x0, 2), 40, 60, fc=CREAM, ec=INK, lw=1.2))
        ax.add_patch(Rectangle((x0, 56), 40, 6, fc="white", ec=INK, lw=0.8))
        ax.text(x0 + 1.5, 59, "PawMatch   Home  Animals  Questionnaire  Results  Account", fontsize=5.6, va="center")
        ax.text(x0 + 20, 64.5, title, ha="center", fontsize=8.5, fontweight="bold", color=GREEN)
    x = 2
    ax.text(x + 2, 52, "Your household", fontsize=9, fontweight="bold")
    ax.add_patch(Rectangle((x + 2, 47.5), 36, 2, fc=PALE, ec=GREEN))
    ax.add_patch(Rectangle((x + 2, 47.5), 18, 2, fc=GREEN, ec=GREEN))
    ax.text(x + 2, 45, "Step 2 of 4", fontsize=6.5, color=GREY)
    for i, q in enumerate(["Are there children in your home?", "Do you have other pets?"]):
        y = 40 - i * 10
        ax.text(x + 2, y, q, fontsize=7)
        ax.add_patch(Rectangle((x + 2, y - 5.5), 36, 4, fc="white", ec=GREY))
        ax.text(x + 3, y - 3.5, "Choose  ▾", fontsize=6.5, color=GREY, va="center")
    ax.add_patch(Rectangle((x + 2, 12), 36, 6, fc="#fbe7e2", ec="#c0604a"))
    ax.text(x + 3, 15, "Answer yes or no for other pets.", fontsize=6.5, va="center")
    ax.add_patch(Rectangle((x + 2, 4), 12, 5, fc="white", ec=GREY))
    ax.text(x + 8, 6.5, "Back", ha="center", fontsize=7, va="center")
    ax.add_patch(Rectangle((x + 26, 4), 12, 5, fc=GREEN, ec=GREEN))
    ax.text(x + 32, 6.5, "Next", ha="center", fontsize=7, va="center", color="white")
    x = 45
    ax.text(x + 2, 52, "Your matches", fontsize=9, fontweight="bold")
    ax.text(x + 2, 48.5, "Scores are guidance; shelter staff make the final decision.", fontsize=5.6, color=GREY)
    for i, (nm, pct, cat, warn) in enumerate([("Milo · Cat", 100, "Strong", False), ("Archie · Dog", 83.3, "Strong", False),
                                              ("Luna · Dog", 64.6, "Good", True)]):
        y = 41 - i * 12.5
        ax.add_patch(Rectangle((x + 2, y - 9), 36, 11, fc="white", ec=GREY))
        ax.add_patch(Rectangle((x + 3, y - 8), 8, 9, fc=PALE, ec=GREY))
        ax.text(x + 7, y - 3.5, "photo", fontsize=5.5, ha="center", va="center", color=GREY)
        ax.text(x + 12.5, y, f"{nm}   {cat}", fontsize=6.8, fontweight="bold", va="center")
        ax.add_patch(Rectangle((x + 12.5, y - 3.5), 24, 1.6, fc=PALE, ec="none"))
        ax.add_patch(Rectangle((x + 12.5, y - 3.5), 24 * pct / 100, 1.6, fc=GREEN, ec="none"))
        ax.text(x + 12.5, y - 6, f"{pct} %  ·  met / not met ▸" + ("   ⚠ warning" if warn else ""), fontsize=5.8,
                color="#c0604a" if warn else INK)
    ax.text(x + 2, 4, "☐ Show every animal", fontsize=7)
    x = 88
    ax.text(x + 2, 52, "Manage animals", fontsize=9, fontweight="bold")
    ax.text(x + 2, 47.5, "All animals | Add animal | Edit or delete", fontsize=6.5, color=GREEN)
    for i, lab in enumerate(["Name", "Species ▾", "Breed", "Age", "Exercise needs ▾", "Max hours alone"]):
        cx, cy = x + 2 + (i % 2) * 18.5, 40 - (i // 2) * 8
        ax.text(cx, cy, lab, fontsize=6)
        ax.add_patch(Rectangle((cx, cy - 5), 17, 3.5, fc="white", ec=GREY))
    ax.add_patch(Rectangle((x + 2, 13), 36, 4, fc=GREEN, ec=GREEN))
    ax.text(x + 20, 15, "Save animal", ha="center", va="center", fontsize=7, color="white")
    ax.text(x + 2, 9, "☐ Yes, remove Luna (adopted or no longer available)", fontsize=5.8)
    ax.add_patch(Rectangle((x + 2, 3), 16, 4, fc="white", ec=GREY))
    ax.text(x + 10, 5, "Delete animal", ha="center", va="center", fontsize=6.3, color=GREY)
    save(fig, "d07-wireframes.png")


if __name__ == "__main__":
    hierarchy()
    structure()
    er()
    classes()
    flows()
    wireframes()
    print("diagrams written to", OUT)
