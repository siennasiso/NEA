"""Five-section adoption questionnaire defined by the PawMatch design."""

from __future__ import annotations

import streamlit as st

from pawmatch_matching import (
    ACTIVITY_OPTIONS, HOUSING_OPTIONS, SIZE_OPTIONS, SPECIES_OPTIONS,
    calculate_and_store_matches, fetch_latest_response,
    initialise_matching_tables, save_questionnaire_response,
    validate_questionnaire,
)
from pawmatch_style import apply_dashboard_style

st.set_page_config(page_title="PawMatch | Questionnaire", page_icon="📝", layout="wide")
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")
if st.session_state.get("role") == "admin":
    st.switch_page("pages/7_Admin_Dashboard.py")

apply_dashboard_style()
initialise_matching_tables()
SECTION_NAMES = ("Home", "Household", "Lifestyle", "Preferences", "Submit")


def _initial_answers() -> dict[str, object]:
    """Load the latest saved response or provide neutral form defaults."""
    previous = fetch_latest_response(int(st.session_state.user_id))
    if previous:
        return {key: previous[key] for key in (
            "housing_level", "garden_access", "hours_left_alone", "has_children",
            "preferred_activity_level", "preferred_species", "preferred_size",
        )}
    return {
        "housing_level": 1, "garden_access": False, "hours_left_alone": 4,
        "has_children": False, "preferred_activity_level": 2,
        "preferred_species": "No preference", "preferred_size": "No preference",
    }


def _move_to(step: int) -> None:
    """Store the current section and its dashboard progress percentage."""
    safe_step = max(0, min(len(SECTION_NAMES) - 1, step))
    st.session_state.questionnaire_step = safe_step
    st.session_state.questionnaire_progress = safe_step * 20
    st.rerun()


def _yes_no(value: bool) -> int:
    """Return the radio-button index for a stored Boolean answer."""
    return 0 if value else 1


if "questionnaire_answers" not in st.session_state:
    st.session_state.questionnaire_answers = _initial_answers()
if "questionnaire_step" not in st.session_state:
    st.session_state.questionnaire_step = 0

answers = st.session_state.questionnaire_answers
step = int(st.session_state.questionnaire_step)

st.markdown("# 📝 Adoption questionnaire")
st.write("Answer seven questions so PawMatch can compare your home and lifestyle with each available animal.")
st.progress((step + 1) / len(SECTION_NAMES), text=f"Section {step + 1} of 5 — {SECTION_NAMES[step]}")

if step == 0:
    with st.form("home_section"):
        housing_labels = list(HOUSING_OPTIONS)
        current_housing = next(label for label, value in HOUSING_OPTIONS.items() if value == int(answers["housing_level"]))
        housing = st.radio("What type of home do you live in?", housing_labels, index=housing_labels.index(current_housing))
        garden = st.radio("Do you have access to a garden?", ("Yes", "No"), index=_yes_no(bool(answers["garden_access"])), horizontal=True)
        next_clicked = st.form_submit_button("Next", type="primary", width="stretch")
    if next_clicked:
        answers["housing_level"] = HOUSING_OPTIONS[housing]
        answers["garden_access"] = garden == "Yes"
        _move_to(1)

elif step == 1:
    with st.form("household_section"):
        children = st.radio("Are there children living in your home?", ("Yes", "No"), index=_yes_no(bool(answers["has_children"])), horizontal=True)
        back_column, next_column = st.columns(2)
        back_clicked = back_column.form_submit_button("Back", width="stretch")
        next_clicked = next_column.form_submit_button("Next", type="primary", width="stretch")
    if back_clicked:
        _move_to(0)
    if next_clicked:
        answers["has_children"] = children == "Yes"
        _move_to(2)

elif step == 2:
    with st.form("lifestyle_section"):
        activity_labels = list(ACTIVITY_OPTIONS)
        current_activity = next(label for label, value in ACTIVITY_OPTIONS.items() if value == int(answers["preferred_activity_level"]))
        activity = st.radio("What activity level can you support?", activity_labels, index=activity_labels.index(current_activity), horizontal=True)
        hours = st.number_input("How many hours per day would the animal usually be left alone?", min_value=0, max_value=24, value=int(answers["hours_left_alone"]), step=1)
        back_column, next_column = st.columns(2)
        back_clicked = back_column.form_submit_button("Back", width="stretch")
        next_clicked = next_column.form_submit_button("Next", type="primary", width="stretch")
    if back_clicked:
        _move_to(1)
    if next_clicked:
        answers["preferred_activity_level"] = ACTIVITY_OPTIONS[activity]
        answers["hours_left_alone"] = int(hours)
        _move_to(3)

elif step == 3:
    with st.form("preferences_section"):
        species = st.selectbox("Which species would you prefer?", SPECIES_OPTIONS, index=SPECIES_OPTIONS.index(str(answers["preferred_species"])))
        size = st.selectbox("Which animal size would you prefer?", SIZE_OPTIONS, index=SIZE_OPTIONS.index(str(answers["preferred_size"])))
        back_column, next_column = st.columns(2)
        back_clicked = back_column.form_submit_button("Back", width="stretch")
        next_clicked = next_column.form_submit_button("Review answers", type="primary", width="stretch")
    if back_clicked:
        _move_to(2)
    if next_clicked:
        answers["preferred_species"] = species
        answers["preferred_size"] = size
        _move_to(4)

else:
    housing_label = next(label for label, value in HOUSING_OPTIONS.items() if value == int(answers["housing_level"]))
    activity_label = next(label for label, value in ACTIVITY_OPTIONS.items() if value == int(answers["preferred_activity_level"]))
    with st.container(border=True):
        st.markdown("### Check your answers")
        st.write(f"**Home:** {housing_label}")
        st.write(f"**Garden:** {'Yes' if answers['garden_access'] else 'No'}")
        st.write(f"**Children in the home:** {'Yes' if answers['has_children'] else 'No'}")
        st.write(f"**Supported activity level:** {activity_label}")
        st.write(f"**Hours left alone:** {answers['hours_left_alone']}")
        st.write(f"**Preferred species:** {answers['preferred_species']}")
        st.write(f"**Preferred size:** {answers['preferred_size']}")

    errors, cleaned = validate_questionnaire(answers)
    if errors:
        st.error("One or more answers are invalid. Go back and correct them.")
    back_column, submit_column = st.columns(2)
    if back_column.button("Back", width="stretch"):
        _move_to(3)
    if submit_column.button("Submit and calculate matches", type="primary", width="stretch", disabled=bool(errors)):
        response_id = save_questionnaire_response(int(st.session_state.user_id), cleaned)
        results = calculate_and_store_matches(response_id, cleaned)
        recommendations = [result for result in results if result["match_category"] != "Low"]
        st.session_state.questionnaire_answers = cleaned
        st.session_state.questionnaire_complete = True
        st.session_state.questionnaire_progress = 100
        st.session_state.match_count = min(5, len(recommendations))
        st.session_state.latest_response_id = response_id
        st.switch_page("pages/6_My_Matches.py")
