"""Seven-question adoption form styled to match the interface design."""

from __future__ import annotations

import streamlit as st

from pawmatch_matching import (
    calculate_and_store_matches,
    fetch_latest_response,
    initialise_matching_tables,
    save_questionnaire_response,
    validate_questionnaire,
)
from pawmatch_style import (
    apply_questionnaire_matches_style,
    render_questionnaire_matches_sidebar,
)

st.set_page_config(page_title="PawMatch | Questionnaire", page_icon="📝", layout="wide")
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")
if st.session_state.get("role") == "admin":
    st.switch_page("pages/7_Admin_Dashboard.py")

apply_questionnaire_matches_style("questionnaire")
initialise_matching_tables()

QUESTIONS = (
    {
        "field": "housing_level",
        "prompt": "How much indoor space is available for the animal?",
        "options": (
            ("Limited space", "One main room", 1),
            ("Moderate space", "Two or three rooms", 2),
            ("Plenty of space", "Most of the home", 3),
        ),
    },
    {
        "field": "garden_access",
        "prompt": "Do you have access to a garden?",
        "options": (
            ("Yes", "The animal can use a secure garden", True),
            ("No", "There is no private garden access", False),
        ),
    },
    {
        "field": "hours_left_alone",
        "prompt": "How many hours per day would the animal usually be left alone?",
        "help": "Enter a whole number between 0 and 24 hours.",
    },
    {
        "field": "has_children",
        "prompt": "Are there children living in your home?",
        "options": (
            ("Yes", "One or more children live at home", True),
            ("No", "No children live at home", False),
        ),
    },
    {
        "field": "preferred_activity_level",
        "prompt": "What activity level can you support?",
        "options": (
            ("Low", "Short, gentle daily activity", 1),
            ("Moderate", "Regular walks or active play", 2),
            ("High", "Long exercise and enrichment", 3),
        ),
    },
    {
        "field": "preferred_species",
        "prompt": "Which species would you prefer?",
        "options": (
            ("Dog", "A canine companion", "Dog"),
            ("Cat", "A feline companion", "Cat"),
            ("Rabbit", "A rabbit companion", "Rabbit"),
            ("No preference", "Show every species", "No preference"),
        ),
    },
    {
        "field": "preferred_size",
        "prompt": "Which animal size would you prefer?",
        "options": (
            ("Small", "A small animal", "Small"),
            ("Medium", "A medium-sized animal", "Medium"),
            ("Large", "A large animal", "Large"),
            ("No preference", "Show every size", "No preference"),
        ),
    },
)


def _initial_answers() -> dict[str, object | None]:
    """Load a saved response or return unanswered values for a new form."""
    previous = fetch_latest_response(int(st.session_state.user_id))
    fields = tuple(question["field"] for question in QUESTIONS)
    if previous:
        return {field: previous[field] for field in fields}
    return {field: 0 if field == "hours_left_alone" else None for field in fields}


def _move_to(step: int) -> None:
    """Move to a valid question and update the dashboard's saved progress."""
    safe_step = max(0, min(len(QUESTIONS) - 1, step))
    st.session_state.questionnaire_step = safe_step
    st.session_state.questionnaire_progress = round((safe_step / len(QUESTIONS)) * 100)
    st.rerun()


def _select_answer(field: str, value: object) -> None:
    """Persist a choice in the current Streamlit browser session."""
    st.session_state.questionnaire_answers[field] = value
    st.rerun()


if "questionnaire_answers" not in st.session_state:
    st.session_state.questionnaire_answers = _initial_answers()
if "questionnaire_step" not in st.session_state:
    st.session_state.questionnaire_step = 0
if fetch_latest_response(int(st.session_state.user_id)) is not None:
    st.session_state.questionnaire_complete = True
    st.session_state.questionnaire_progress = 100

answers = st.session_state.questionnaire_answers
step = max(0, min(len(QUESTIONS) - 1, int(st.session_state.questionnaire_step)))
question = QUESTIONS[step]
field = str(question["field"])
progress = round(((step + 1) / len(QUESTIONS)) * 100)

sidebar_column, main_column = st.columns([0.25, 0.75], gap=None)
with sidebar_column:
    with st.container(key="design_sidebar"):
        render_questionnaire_matches_sidebar()

with main_column:
    with st.container(key="design_main"):
        if st.session_state.get("questionnaire_just_completed", False):
            st.markdown(
                """
                <div class="completion-card">
                    <div class="completion-icon">💗</div>
                    <h1>Your questionnaire is complete</h1>
                    <p>Your answers have been saved and your personalised animal matches are ready.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("View matches", key="view_matches_primary", type="primary", width="stretch"):
                st.session_state.questionnaire_just_completed = False
                st.switch_page("pages/6_My_Matches.py")
            if st.button("Back to questionnaire", key="flow_back", width="stretch"):
                st.session_state.questionnaire_just_completed = False
                st.rerun()
            st.stop()

        st.markdown(
            f"""
            <div class="flow-page-header">
                <div>
                    <h1>Question {step + 1} of {len(QUESTIONS)}</h1>
                    <p>Choose one answer then continue</p>
                </div>
                <span>{progress}% through</span>
            </div>
            <div class="flow-progress"><span style="width:{progress}%"></span></div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.get("questionnaire_complete", False):
            if st.button("View matches", key="view_matches_primary", type="primary", width="stretch"):
                st.switch_page("pages/6_My_Matches.py")

        with st.container(key="question_card"):
            st.markdown(
                f'<p class="question-prompt">{question["prompt"]}</p>',
                unsafe_allow_html=True,
            )

            if field == "hours_left_alone":
                st.markdown(
                    f'<p class="question-help">{question["help"]}</p>',
                    unsafe_allow_html=True,
                )
                with st.container(key="question_hours"):
                    hours = st.number_input(
                        "Hours left alone",
                        min_value=0,
                        max_value=24,
                        value=int(answers[field] or 0),
                        step=1,
                    )
                answers[field] = int(hours)
            else:
                options = question["options"]
                selected = answers.get(field)
                if selected is not None:
                    selected_index = next(
                        index for index, option in enumerate(options)
                        if option[2] == selected
                    )
                    st.markdown(
                        f"""
                        <style>
                        .st-key-choice_{step}_{selected_index} button,
                        .st-key-choice_{step}_{selected_index} button:hover {{
                            border: 2px solid #d84d8b !important;
                            background: #fbeaf4 !important;
                            box-shadow: 0 4px 7px rgba(120,45,80,.25) !important;
                        }}
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )
                option_columns = st.columns(len(options), gap="small")
                for index, (label, hint, value) in enumerate(options):
                    with option_columns[index]:
                        if st.button(
                            f"{label}\n\n{hint}",
                            key=f"choice_{step}_{index}",
                            width="stretch",
                        ):
                            _select_answer(field, value)

            back_column, next_column = st.columns([1, 1.35], gap="large")
            with back_column:
                if st.button(
                    "Back",
                    key="flow_back",
                    width="stretch",
                    disabled=step == 0,
                ):
                    _move_to(step - 1)

            with next_column:
                answer_is_present = answers.get(field) is not None
                if step < len(QUESTIONS) - 1:
                    if st.button(
                        "Next question",
                        key="flow_next",
                        type="primary",
                        width="stretch",
                        disabled=not answer_is_present,
                    ):
                        _move_to(step + 1)
                elif st.button(
                    "Submit questionnaire",
                    key="flow_submit",
                    type="primary",
                    width="stretch",
                    disabled=not answer_is_present,
                ):
                    errors, cleaned = validate_questionnaire(answers)
                    if errors:
                        st.error("One or more answers are invalid. Please check each question.")
                    else:
                        response_id = save_questionnaire_response(
                            int(st.session_state.user_id), cleaned
                        )
                        results = calculate_and_store_matches(response_id, cleaned)
                        recommendations = [
                            result for result in results
                            if result["match_category"] != "Low"
                        ]
                        st.session_state.questionnaire_answers = cleaned
                        st.session_state.questionnaire_complete = True
                        st.session_state.questionnaire_progress = 100
                        st.session_state.match_count = min(3, len(recommendations))
                        st.session_state.latest_response_id = response_id
                        st.session_state.questionnaire_just_completed = True
                        st.rerun()
