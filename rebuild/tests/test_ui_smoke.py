"""Headless page checks with Streamlit's AppTest: each page renders, forms report errors, guards hold.

The pages run for real on a temporary database seeded with the 13 demo animals (11 available).
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from pawmatch import auth, db, services
from pawmatch.seed import create_admin, prepare
from webui import state

ENTRY = str(Path(__file__).resolve().parents[1] / "streamlit_app.py")
ANSWERS = {
    "housing_level": 1, "garden_access": True, "has_children": True, "other_pets": True,
    "experience": "Some (family pet growing up)", "activity_level": 1, "hours_alone": 6,
    "preferred_species": "No preference", "preferred_size": "No preference", "allergies": (),
}
GOOGLE = {"redirect_uri": "http://localhost:8501/oauth2callback", "cookie_secret": "test-cookie-secret",
          "client_id": "test-client", "client_secret": "test-secret",
          "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration"}
ADD = "admin_add_new"  # the staff "Add animal" form's key prefix


@pytest.fixture
def ids(tmp_path, monkeypatch):
    path = tmp_path / "ui.db"
    monkeypatch.setattr(state, "DB_PATH", path)
    prepare(str(path))
    with db.connect(path) as conn:
        create_admin(conn, "Staff", "staff@example.com", 40, "staffpass1")
        staff = auth.login(conn, "staff@example.com", "staffpass1")[0]
        user = auth.register(conn, "Sam", "sam@example.com", 30, "longenough", "longenough")[0]
        available = len(db.list_animals(conn, status="Available"))
    return {"staff": staff.user_id, "user": user.user_id, "path": path, "available": available}


def app(user_id=None, page=None, secrets=None):
    at = AppTest.from_file(ENTRY, default_timeout=30)
    if secrets:
        at.secrets["auth"] = secrets
    if user_id is not None:
        at.session_state["user_id"] = user_id
    at.run()
    if page:
        at.switch_page(state.PAGES[page]).run()
    assert not at.exception, at.exception
    return at


def html(at) -> str:
    return " ".join(element.proto.body for element in at.get("html"))


def button(at, label):
    return next(b for b in at.button if b.label == label)


def labels(at):
    return [b.label for b in at.button]


def log_in(at, email, password):
    at.text_input(key="login_identifier").input(email)
    at.text_input(key="login_password").input(password)
    button(at, "Log in").click().run()
    assert not at.exception, at.exception
    return at


def fill_registration(at, password="longenough", confirm="longenough"):
    at.text_input(key="registration_name").input("Ava Jones")
    at.text_input(key="registration_email").input("ava@example.com")
    at.number_input(key="registration_age").set_value(25)
    at.text_input(key="registration_password").input(password)
    at.text_input(key="registration_confirm_password").input(confirm)
    button(at, "Create account").click().run()
    assert not at.exception, at.exception
    return at


# Login and registration (her two pages, with the tab switch above each form)

def test_login_page_shows_her_form_and_the_tab_switch(ids):
    at = app()
    assert [t.label for t in at.text_input] == ["Email address", "Password"]
    tabs = at.get("button_group")[0]
    assert [o.content for o in tabs.proto.options] == ["Log in", "Create an account"]
    assert "Find a companion who fits your life." in html(at)


def test_google_button_is_hidden_without_settings(ids):
    assert "Continue with Google" not in labels(app())


def test_google_button_appears_when_settings_are_present(ids):
    assert "Continue with Google" in labels(app(secrets=GOOGLE))


def test_wrong_password_gives_one_message_that_does_not_say_which_part_was_wrong(ids):
    at = log_in(app(), "sam@example.com", "not-my-password")
    assert "Incorrect email or password." in html(at)
    assert "user_id" not in at.session_state


def test_unknown_email_gives_the_same_message(ids):
    at = log_in(app(), "nobody@example.com", "not-my-password")
    assert "Incorrect email or password." in html(at)


def test_adopter_login_opens_the_home_page(ids):
    at = log_in(app(), "sam@example.com", "longenough")
    assert at.session_state["user_id"] == ids["user"]
    assert "Welcome Back Sam" in html(at)


def test_staff_login_opens_the_dashboard(ids):
    at = log_in(app(), "staff@example.com", "staffpass1")
    assert at.session_state["user_id"] == ids["staff"]
    assert at.session_state["admin_view"] == "overview"


def test_tab_switch_opens_registration(ids):
    at = app()
    at.get("button_group")[0].set_value("Create an account").run()
    assert "Create your account" in html(at)


def test_registration_reports_every_missing_field(ids):
    at = app(page="registration")
    button(at, "Create account").click().run()
    assert set(at.session_state["registration_errors"]) == {"name", "email", "age", "password", "confirm_password"}
    assert "Enter a name." in html(at)


def test_registration_reports_a_password_mismatch_under_confirm(ids):
    at = fill_registration(app(page="registration"), confirm="different1")
    assert set(at.session_state["registration_errors"]) == {"confirm_password"}


def test_registration_creates_an_adopter_account_and_signs_it_in(ids):
    at = fill_registration(app(page="registration"))
    with db.connect(ids["path"]) as conn:
        new_id = auth.login(conn, "ava@example.com", "longenough")[0].user_id
    assert at.session_state["user_id"] == new_id
    with db.connect(ids["path"]) as conn:
        user = auth.login(conn, "ava@example.com", "longenough")[0]
    assert user is not None and not user.is_admin


# Adopter pages

def test_adopter_pages_send_visitors_to_log_in(ids):
    at = app(page="questionnaire")
    assert [t.label for t in at.text_input] == ["Email address", "Password"]


def test_browse_shows_a_card_for_every_available_animal(ids):
    at = app(ids["user"], "browse")
    assert labels(at).count("View profile") == ids["available"] == 11


def test_view_profile_opens_the_animal_with_its_needs(ids):
    at = app(ids["user"], "browse")
    button(at, "View profile").click().run()
    assert "Maximum time alone" in html(at)


def test_questionnaire_waits_for_an_answer_before_next(ids):
    at = app(ids["user"], "questionnaire")
    assert button(at, "Next question").disabled
    at.button(key="choice_0_0").click().run()
    assert not button(at, "Next question").disabled


def test_questionnaire_completes_and_ranks_every_available_animal(ids):
    at = app(ids["user"], "questionnaire")
    for step in range(10):
        if step == 6:  # hours alone is typed as a number, not chosen
            at.number_input[0].set_value(6).run()
        else:
            at.button(key=f"choice_{step}_0").click().run()
        button(at, "Submit questionnaire" if step == 9 else "Next question").click().run()
        assert not at.exception, at.exception
    assert at.session_state["questionnaire_just_completed"] is True
    with db.connect(ids["path"]) as conn:
        user = db.get_user(conn, ids["user"])
        assert len(services.latest_results(conn, user)) == ids["available"]


def test_allergy_cards_turn_on_and_off_and_no_allergies_clears_them(ids):
    at = AppTest.from_file(ENTRY, default_timeout=30)
    at.session_state["user_id"] = ids["user"]
    at.run()
    at.switch_page(state.PAGES["questionnaire"]).run()
    at.session_state["questionnaire_step"] = 4  # the allergies question
    at.run()
    assert "Choose all that apply" in html(at) and button(at, "Next question").disabled
    allergies = lambda: at.session_state["questionnaire_answers"]["allergies"]  # noqa: E731
    at.button(key="choice_4_2").click().run()  # Cats
    at.button(key="choice_4_1").click().run()  # Dogs
    assert allergies() == ("Dog", "Cat") and not button(at, "Next question").disabled
    at.button(key="choice_4_2").click().run()  # Cats off again
    assert allergies() == ("Dog",)
    at.button(key="choice_4_1").click().run()  # nothing chosen: the question is unanswered again
    assert allergies() is None and button(at, "Next question").disabled
    at.button(key="choice_4_3").click().run()  # Rabbits, then No allergies replaces it
    at.button(key="choice_4_0").click().run()
    assert allergies() == ()
    assert not at.exception, at.exception


def test_an_allergic_adopter_sees_the_allergy_warning_on_matches(ids):
    with db.connect(ids["path"]) as conn:
        user = db.get_user(conn, ids["user"])
        services.submit_questionnaire(conn, user, ANSWERS | {"allergies": ("Cat",)})
        results = services.latest_results(conn, user)
    cats = [r for r in results if r.animal.species == "Cat"]
    assert cats and all(r.compatibility <= 39.0 and r.warnings[0].startswith("Allergy") for r in cats)
    assert all(not r.suitable for r in results[-len(cats):])  # the cats are ranked last


def test_matches_page_shows_the_top_five_and_can_show_all(ids):
    with db.connect(ids["path"]) as conn:
        services.submit_questionnaire(conn, db.get_user(conn, ids["user"]), ANSWERS)
    at = app(ids["user"], "matches")
    assert len(at.get("page_link")) == 5
    at.toggle(key="show_all_matches").set_value(True).run()
    assert len(at.get("page_link")) == ids["available"]


def test_matches_page_without_answers_points_to_the_questionnaire(ids):
    at = app(ids["user"], "matches")
    assert "Complete the questionnaire" in html(at)


# Changes made after the client reviews (Development, "Changes made after review")

def test_review1_age_rule_is_written_on_the_form(ids):
    at = app(page="registration")
    assert any("18 or over" in c.value for c in at.caption)


def test_review3_size_filter_narrows_the_list(ids):
    at = app(ids["user"], "browse")
    at.selectbox(key="browse_size").set_value("Small").run()
    with db.connect(ids["path"]) as conn:
        small = len(services.browse(conn, None, "Small", ""))
    assert 0 < small < ids["available"] and f"Available animals · {small}" in html(at)


def test_review3_profile_offers_the_questionnaire_as_a_button(ids):
    at = app(ids["user"], "browse")
    button(at, "View profile").click().run()
    button(at, "Take the questionnaire").click().run()
    assert not at.exception, at.exception


def test_review3_home_says_staff_make_the_decision(ids):
    at = app(ids["user"], "home")
    assert "PawMatch suggests, people decide" in html(at)


def test_review4_hours_question_starts_empty(ids):
    at = app(ids["user"], "questionnaire")
    at.session_state["questionnaire_step"] = 6  # hours alone
    at.run()
    assert at.number_input[0].value is None and button(at, "Next question").disabled
    at.number_input[0].set_value(0).run()
    assert not button(at, "Next question").disabled


def test_review5_matches_explain_the_score_and_the_order(ids):
    with db.connect(ids["path"]) as conn:
        services.submit_questionnaire(conn, db.get_user(conn, ids["user"]), ANSWERS | {"allergies": ("Cat",)})
    at = app(ids["user"], "matches")
    at.toggle(key="show_all_matches").set_value(True).run()
    page = html(at)
    assert "Score key" in page and "No requirements are unmet" not in page
    assert page.count("listed after the others") == 1 and "talk to the shelter first" in page


def test_review5_account_lets_answers_be_updated(ids):
    with db.connect(ids["path"]) as conn:
        services.submit_questionnaire(conn, db.get_user(conn, ids["user"]), ANSWERS)
    at = app(ids["user"], "account")
    assert "Update my questionnaire answers" in labels(at)


# Staff pages

def test_admin_page_stops_adopters(ids):
    at = app(ids["user"], "admin")
    assert any("shelter staff only" in e.value for e in at.error)


def test_staff_add_form_reports_missing_fields(ids):
    at = app(ids["staff"], "admin")
    at.button(key="admin_nav_add").click().run()
    button(at, "Save animal record").click().run()
    assert "name" in at.session_state[f"{ADD}_errors"]


def test_staff_can_add_an_animal_and_then_delete_it(ids):
    at = app(ids["staff"], "admin")
    at.button(key="admin_nav_add").click().run()
    at.text_input(key=f"{ADD}_name").input("Biscuit")
    at.text_input(key=f"{ADD}_breed").input("Beagle")
    at.number_input(key=f"{ADD}_age").set_value(4)
    at.text_area(key=f"{ADD}_description").input(
        "A cheerful beagle who loves sniffing walks and a warm blanket by the radiator.")
    at.selectbox(key=f"{ADD}_pets").set_value(False)
    at.selectbox(key=f"{ADD}_experience").set_value(2)
    button(at, "Save animal record").click().run()
    assert not at.exception, at.exception
    with db.connect(ids["path"]) as conn:
        added = [a for a in db.list_animals(conn) if a.name == "Biscuit"]
    assert len(added) == 1
    assert added[0].good_with_pets is False and added[0].experience_needed == 2
    biscuit = added[0].animal_id
    assert at.session_state["admin_view"] == "manage"
    assert at.session_state["admin_selected_animal_id"] == biscuit
    at.checkbox(key=f"confirm_delete_{biscuit}").check().run()
    at.button(key=f"delete_{biscuit}").click().run()
    with db.connect(ids["path"]) as conn:
        assert all(a.name != "Biscuit" for a in db.list_animals(conn))


# Reloading the browser starts a new Streamlit session; the token in the address signs the user back in


def test_reload_keeps_the_adopter_signed_in(ids):
    at = log_in(app(), "sam@example.com", "longenough")
    token = at.query_params["s"][0] if isinstance(at.query_params["s"], list) else at.query_params["s"]
    reloaded = AppTest.from_file(ENTRY, default_timeout=30)
    reloaded.query_params["s"] = token
    reloaded.run()
    assert not reloaded.exception, reloaded.exception
    assert reloaded.session_state["user_id"] == ids["user"]
    assert "Welcome Back Sam" in html(reloaded)


def test_signed_out_or_unknown_token_does_not_sign_in(ids):
    at = AppTest.from_file(ENTRY, default_timeout=30)
    at.query_params["s"] = "not-a-real-token"
    at.run()
    assert not at.exception, at.exception
    assert "user_id" not in at.session_state
