"""Numbers and generated tables for build_nea_v2.py, read from the code and the saved evidence.

{{name}} in docs/nea/*.md prints metric(name); @name lines call TABLES[name]. Nothing here is typed
by hand: weights come from pawmatch.matching, counts from the pytest JUnit file, speeds from
docs/evidence/measurements.json (docs/tools/measure_v2.py).
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pawmatch import matching  # noqa: E402
from pawmatch.models import EXPERIENCE_NEEDED, HOUSING_LEVELS, Animal, Answers  # noqa: E402
from pawmatch.seed import demo_animal_values  # noqa: E402

EVIDENCE = ROOT / "docs" / "evidence"
STAGE_ANCHORS: dict[str, str] = {}


def _junit() -> dict[str, int]:
    suite = ElementTree.parse(EVIDENCE / "pytest-junit.xml").getroot()
    suite = suite if suite.tag == "testsuite" else suite.find("testsuite")
    cases = suite.findall("testcase")
    by_file: dict[str, int] = {}
    for case in cases:
        name = case.get("classname", "").split(".")[-1]
        by_file[name] = by_file.get(name, 0) + 1
    failed = sum(1 for c in cases if c.find("failure") is not None or c.find("error") is not None)
    return {"tests_total": len(cases), "tests_failed": failed, **{f"tests_{k}": v for k, v in by_file.items()}}


def _metrics() -> dict:
    m = json.loads((EVIDENCE / "measurements.json").read_text())
    m.update(_junit())
    m["max_points"] = matching.MAX_POINTS
    for factor, weight in matching.WEIGHTS.items():
        m[f"w_{factor}"] = weight
    audit = json.loads((EVIDENCE / "rendered-audit-desktop.json").read_text())
    m["audit_screens"] = len(audit)
    return m


METRICS = _metrics()


def metric(name: str):
    return METRICS[name]


def _demo(name: str) -> Animal:
    values = next(v for v in demo_animal_values() if v["name"] == name)
    fields = Animal.__dataclass_fields__
    return Animal(**{"animal_id": 0, **{k: v for k, v in values.items() if k in fields}})


WORKED_ANSWERS = Answers(housing_level=1, garden_access=False, has_children=True, other_pets=True,
                         experience="Some (family pet growing up)", activity_level=1, hours_alone=6,
                         preferred_species="Cat", preferred_size="No preference", allergies=())


def _columns(animal: Animal, a: Answers) -> dict[str, tuple[str, str]]:
    yes = lambda flag: "Yes" if flag else "No"  # noqa: E731
    return {
        "hours_alone": (f"Left alone at most {animal.max_hours_alone} h", f"{a.hours_alone} h a day"),
        "children": (f"Safe with children: {yes(animal.child_compatible)}", f"Children at home: {yes(a.has_children)}"),
        "housing": (f"At least '{HOUSING_LEVELS[animal.min_housing_level]}'", f"'{HOUSING_LEVELS[a.housing_level]}'"),
        "activity": (f"Activity level {animal.exercise_needs} of 3", f"Can offer level {a.activity_level} of 3"),
        "garden": (f"Needs a garden: {yes(animal.garden_required)}", f"Has a garden: {yes(a.garden_access)}"),
        "other_pets": (f"Good with other pets: {yes(animal.good_with_pets)}", f"Other pets at home: {yes(a.other_pets)}"),
        "experience": (EXPERIENCE_NEEDED[animal.experience_needed], a.experience),
    }


def worked(rest: str, builder):
    """@worked NAME: the score for one demo animal and the worked-example answers, factor by factor."""
    animal = _demo(rest.strip())
    columns = _columns(animal, WORKED_ANSWERS)
    rows = [["Factor", "What the animal needs", "What the adopter answered", "Fraction", "Weight", "Points"]]
    total = 0.0
    for factor, fraction, _ in matching._factor_checks(animal, WORKED_ANSWERS):
        weight = matching.WEIGHTS[factor]
        total += weight * fraction
        need, answer = columns[factor]
        rows.append([factor.replace("_", " ").capitalize(), need, answer, f"{fraction:g}", str(weight),
                     f"{weight * fraction:g}"])
    result = matching.score_animal(animal, WORKED_ANSWERS)
    rows.append(["**Total**", "", "", "", f"**{matching.MAX_POINTS}**", f"**{total:g}**"])
    rows.append([f"**Score** = {total:g} ÷ {matching.MAX_POINTS} × 100, rounded to 1 decimal place", "", "", "", "",
                 f"**{result.compatibility:.1f}% ({result.category})**"])
    METRICS[f"worked_{animal.name}"] = f"{result.compatibility:.1f}%"
    METRICS[f"worked_{animal.name}_warnings"] = len(result.warnings)
    return rows, [1.1, 2.1, 2.1, 0.8, 0.7, 1.2], 7.5


def weights(rest: str, builder):
    """@weights: the weights table straight from pawmatch.matching."""
    why = {
        "hours_alone": "Biggest welfare risk named by the client (Q1, Q10) and by the survey (S5: time available 85.2%).",
        "children": "Safety: a dog that is not child-safe in a family home is the outcome the client most wants to stop (Q10).",
        "housing": "Living space was the top survey factor (S5: 88.9%).",
        "activity": "An under-exercised animal is a common reason for returns (Q1). Half points for one level short.",
        "garden": "Some animals need outdoor space; others do not (Q2, S5).",
        "other_pets": "Added in development stage 5 after a re-check against the interview: other pets are a key factor in the client's summary (Q2, Q10).",
        "experience": "Added in stage 5 for the same reason: experience is a factor people forget (Q1). Half points for one level short.",
    }
    rows = [["Factor", "Weight", "Warning if unmet?", "Why this weight (source)"]]
    for factor, weight in matching.WEIGHTS.items():
        rows.append([factor.replace("_", " ").capitalize(), str(weight),
                     "Yes" if factor in matching.IMPORTANT_FACTORS else "No", why[factor]])
    rows.append(["**Total**", f"**{matching.MAX_POINTS}**", "", "The percentage is points earned ÷ "
                 f"{matching.MAX_POINTS} × 100, so changing one weight cannot break the scale."])
    return rows, [1.2, 0.6, 0.9, 5], 7.8


TABLES = {"worked": worked, "weights": weights}


REVIEWS = json.loads((EVIDENCE / "client-reviews.json").read_text())


def sus_score(answers: list[int]) -> float:
    """System Usability Scale: odd items score answer-1, even items 5-answer; the sum times 2.5 gives 0-100."""
    return 2.5 * sum((a - 1) if i % 2 == 0 else (5 - a) for i, a in enumerate(answers))


for _p in REVIEWS["personas"]:
    METRICS[f"sus_{_p['id']}"] = f"{sus_score(_p['sus']):g}"
METRICS["sus_mean"] = f"{sum(sus_score(p['sus']) for p in REVIEWS['personas']) / len(REVIEWS['personas']):.1f}"


def feedback(rest: str, builder):
    """@feedback N: the client's answers for stage N, then a box with the summary and next steps."""
    review = REVIEWS["reviews"][rest.strip()]
    rows = [["#", "My question", "Client's answer"]]
    rows += [[str(n), q["q"], q["a"]] for n, q in enumerate(review["questions"], 1)]
    builder.table(rows, [0.3, 2, 5.2], size=7.8)
    verdict = "signed off" if review["signed_off"] else "not signed off yet"
    lines = [f"**Rating {review['rating_out_of_10']}/10, {verdict}.** {review['summary']}", "",
             "**Next steps the client asked for:**"] + [f"- {step}" for step in review["next_steps"]]
    builder.box("client", f"Client feedback {rest.strip()}: summary and next steps", lines)
    return None


def personas(rest: str, builder):
    """@personas: each simulated tester, their task ratings and SUS score."""
    rows = [["Tester", "Who", "U1", "U2", "U3", "U4", "U5", "SUS"]]
    for p in REVIEWS["personas"]:
        marks = {t["id"]: t for t in p["tasks"]}
        cell = lambda t: "n/a" if t["completed_without_help"] == "n/a" else (  # noqa: E731
            f"{t['rating_out_of_10']}/10" + ("" if t["completed_without_help"] == "yes" else " (help)"))
        rows.append([f"{p['id']} {p['name']}", p["who"], *[cell(marks[u]) for u in ("U1", "U2", "U3", "U4", "U5")],
                     f"**{sus_score(p['sus']):g}**"])
    rows.append(["**Mean**", "", "", "", "", "", "", f"**{METRICS['sus_mean']}**"])
    return rows, [1.1, 3.2, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6], 7.8


def suschart(rest: str, builder):
    """@suschart: a bar chart of the SUS scores against the industry average of 68."""
    from PIL import Image, ImageDraw, ImageFont
    font_path = str(ROOT / "static" / "fonts" / "Nunito.ttf")
    font, small = ImageFont.truetype(font_path, 30), ImageFont.truetype(font_path, 24)
    w, h, left, base, top = 1400, 620, 120, 520, 60
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    scale = (base - top) / 100
    for v in range(0, 101, 20):
        y = base - v * scale
        draw.line((left, y, w - 40, y), fill="#F1DCE6", width=2)
        draw.text((left - 60, y - 15), str(v), fill="#6B5B63", font=small)
    bar = 200
    gap = (w - left - 40 - bar * len(REVIEWS["personas"])) // (len(REVIEWS["personas"]) + 1)
    for i, p in enumerate(REVIEWS["personas"]):
        score = sus_score(p["sus"])
        x = left + gap + i * (bar + gap)
        draw.rounded_rectangle((x, base - score * scale, x + bar, base), radius=14, fill="#E04D8B")
        draw.text((x + bar / 2, base - score * scale - 22), f"{score:g}", fill="#A92660", font=font, anchor="mm")
        draw.text((x + bar / 2, base + 34), f"{p['id']} {p['name']}", fill="#2B2327", font=small, anchor="mm")
    y = base - 68 * scale
    for x in range(left, w - 40, 28):
        draw.line((x, y, x + 14, y), fill="#6B46C1", width=4)
    draw.text((w - 46, y - 34), "average website 68", fill="#6B46C1", font=small, anchor="rm")
    path = ROOT / "docs" / "img" / "sus-chart.png"
    img.save(path)
    builder.figure(path, rest or "SUS scores for the four testers (higher is better)", 14, "fig-sus", border=False)
    return None


TABLES.update({"feedback": feedback, "personas": personas, "suschart": suschart})
