"""Measure capacity and speed for the write-up, and save them to docs/evidence/measurements.json.

    .venv/bin/python docs/tools/measure_v2.py

Runs on a temporary database: 500 animals, 100 adopter accounts, five questionnaire submissions
(each scores and stores all 500 animals), the browse query, and the browse page opened headlessly.
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from pawmatch import auth, db, services, validation  # noqa: E402
from pawmatch.seed import demo_animal_values, prepare  # noqa: E402

ANSWERS = {"housing_level": 2, "garden_access": True, "has_children": True, "other_pets": False, "allergies": (),
           "experience": "Some (family pet growing up)", "activity_level": 2, "hours_alone": 4,
           "preferred_species": "Dog", "preferred_size": "No preference"}


def main() -> None:
    path = str(Path(tempfile.mkdtemp()) / "measure.db")
    prepare(path)
    base = demo_animal_values()
    m: dict = {}
    with db.connect(path) as conn:
        for i in range(500 - db.count_animals(conn)):
            values, errors = validation.validate_animal(dict(base[i % len(base)], name=f"Test {chr(65 + i % 26)}{i}"[:30]))
            assert not errors, errors
            db.insert_animal(conn, values)
        users = [auth.register(conn, "Load Tester", f"tester{i}@example.com", 30, "password1", "password1")[0]
                 for i in range(100)]
        m["animals"] = db.count_animals(conn)
        m["users"] = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    runs = []
    for user in users[:5]:
        start = time.perf_counter()
        with db.connect(path) as conn:
            results, errors = services.submit_questionnaire(conn, user, ANSWERS)
        runs.append(time.perf_counter() - start)
        assert not errors and results
        m["scored"] = len(results)
    m["submit_mean"], m["submit_max"] = round(sum(runs) / len(runs), 3), round(max(runs), 3)
    start = time.perf_counter()
    with db.connect(path) as conn:
        m["browse_found"] = len(services.browse(conn, None, None, ""))
    m["browse_query"] = round(time.perf_counter() - start, 3)

    from streamlit.testing.v1 import AppTest
    from webui import state
    state.DB_PATH = Path(path)
    times = []
    for _ in range(3):
        at = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=90)
        at.session_state["user_id"] = users[0].user_id
        start = time.perf_counter()
        at.run()
        at.switch_page(state.PAGES["browse"]).run()
        times.append(time.perf_counter() - start)
        assert not at.exception, at.exception
    m["browse_page"] = round(max(times), 2)
    out = ROOT / "docs" / "evidence" / "measurements.json"
    out.write_text(json.dumps(m, indent=1) + "\n")
    print(json.dumps(m))


if __name__ == "__main__":
    main()
