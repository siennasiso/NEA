"""Headless UI checks with Streamlit's AppTest: pages render and guards hold."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from pawmatch import auth, db, services
from pawmatch.seed import create_admin, prepare
from webui import state

ENTRY = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")
ANSWERS = {
    "housing_level": 2, "garden_access": "Yes", "has_children": "No", "other_pets": "No",
    "experience": "None", "activity_level": 2, "hours_alone": 4,
    "preferred_species": "No preference", "preferred_size": "No preference",
}


@pytest.fixture
def ids(tmp_path, monkeypatch):
    path = tmp_path / "ui.db"
    monkeypatch.setattr(state, "DB_PATH", path)
    prepare(str(path))
    with db.connect(path) as conn:
        create_admin(conn, "Staff", "staff@example.com", 40, "staffpass1")
        staff = auth.login(conn, "staff@example.com", "staffpass1")[0]
        user = auth.register(conn, "Sam", "sam@example.com", 30, "longenough", "longenough")[0]
    return {"staff": staff.user_id, "user": user.user_id, "path": path}


def app(user_id=None, page=None):
    at = AppTest.from_file(ENTRY, default_timeout=30)
    if user_id is not None:
        at.session_state["user_id"] = user_id
    at.run()
    if page:
        at.switch_page(state.PAGES[page]).run()
    assert not at.exception, at.exception
    return at


def texts(elements):
    return " ".join(e.value for e in elements)


def test_home_page_explains_purpose(ids):
    at = app()
    assert at.title[0].value.endswith("PawMatch")
    assert "final adoption decision" in texts(at.info)


def test_browse_shows_a_card_for_every_animal(ids):
    at = app(page="browse")
    assert len([b for b in at.button if b.label == "View profile"]) == 13


def test_profile_reads_from_database(ids):
    at = AppTest.from_file(ENTRY, default_timeout=30)
    at.run()
    at.switch_page(state.PAGES["profile"])
    at.query_params["id"] = "1"
    at.run()
    assert not at.exception and at.title[0].value == "Luna"


def test_questionnaire_needs_login(ids):
    assert "log in" in texts(app(page="questionnaire").info).lower()


def test_questionnaire_blocks_unanswered_step(ids):
    at = app(ids["user"], page="questionnaire")
    next(b for b in at.button if b.label == "Next").click().run()
    assert len(at.error) == 1 and at.session_state["q_step"] == 0
    assert "type of home" in at.error[0].value and "garden access" in at.error[0].value


def test_questionnaire_advances_when_step_is_answered(ids):
    at = app(ids["user"], page="questionnaire")
    at.selectbox(key="q-housing_level").select(2)
    at.selectbox(key="q-garden_access").select("Yes")
    next(b for b in at.button if b.label == "Next").click().run()
    assert not at.error and at.session_state["q_step"] == 1


def test_results_show_at_least_four_ranked_matches(ids):
    with db.connect(ids["path"]) as conn:
        services.submit_questionnaire(conn, db.get_user(conn, ids["user"]), ANSWERS)
    at = app(ids["user"], page="results")
    headings = [m.value for m in at.markdown if m.value.startswith("#### ")]
    assert len(headings) >= 4 and headings[0].startswith("#### 1.")
    assert "guidance" in texts(at.info)


def test_admin_page_is_not_routable_for_adopters(ids):
    at = app(ids["user"])
    with pytest.raises(ValueError, match="Could not find a navigation page"):
        at.switch_page(state.PAGES["admin"])


def test_admin_page_guard_stops_adopters_even_if_reached_directly(ids):
    at = AppTest.from_file(str(Path(ENTRY).parent / state.PAGES["admin"]), default_timeout=30)
    at.session_state["user_id"] = ids["user"]
    at.run()
    assert "staff only" in texts(at.error) and not at.dataframe


def test_admin_page_lists_animals_for_staff(ids):
    at = app(ids["staff"], page="admin")
    assert at.title[0].value == "Manage animals" and len(at.dataframe) == 1
