"""Adoption form styled to match the interface design (the original pages/3_Questionnaire.py).

One question per screen, as she built it. The questions are in webui/questions.py (her seven
plus other pets, allergies and experience, which the matching uses). The allergies question
takes several answers: each species card turns on and off, and "No allergies" clears them.
"Next question" checks the answer with pawmatch.validation.validate_question; submitting
validates all ten, stores them and ranks every available animal
(pawmatch.services.submit_questionnaire).
"""

from __future__ import annotations

from dataclasses import asdict
from html import escape

import streamlit as st

from pawmatch import db, services
from pawmatch.models import SPECIES
from pawmatch.validation import validate_question
from webui.pawmatch_style import apply_questionnaire_matches_style, render_questionnaire_matches_sidebar
from webui.questions import QUESTIONS
from webui.state import PAGES, database, require_adopter

st.set_page_config(page_title="PawMatch | Questionnaire", page_icon="📝", layout="wide")
user = require_adopter()

apply_questionnaire_matches_style("questionnaire")


def _latest_answers() -> dict[str, object] | None:
    with database() as conn:
        latest = db.latest_response(conn, user.user_id)
    return None if latest is None else asdict(latest[1])


def _initial_answers() -> dict[str, object | None]:
    """Load a saved response or return unanswered values for a new form."""
    previous = _latest_answers()
    if previous:
        return {question.field: previous[question.field] for question in QUESTIONS}
    # Every answer starts empty, the typed hours question included (it used to start at 0).
    return {question.field: None for question in QUESTIONS}


def _move_to(step: int) -> None:
    """Move to a valid question."""
    st.session_state.questionnaire_step = max(0, min(len(QUESTIONS) - 1, step))
    st.session_state.questionnaire_errors = {}
    st.rerun()


def _select_answer(field: str, value: object) -> None:
    """Persist a choice in the current Streamlit browser session."""
    st.session_state.questionnaire_answers[field] = value
    st.session_state.questionnaire_errors = {}
    st.rerun()


def _toggle_species(field: str, species: str) -> None:
    """Turn one species on or off in a several-answer question; none left means not yet answered."""
    chosen = set(st.session_state.questionnaire_answers.get(field) or ())
    chosen ^= {species}
    _select_answer(field, tuple(s for s in SPECIES if s in chosen) or None)


if "questionnaire_answers" not in st.session_state:
    st.session_state.questionnaire_answers = _initial_answers()
if "questionnaire_step" not in st.session_state:
    st.session_state.questionnaire_step = 0
questionnaire_complete = _latest_answers() is not None

answers = st.session_state.questionnaire_answers
step = max(0, min(len(QUESTIONS) - 1, int(st.session_state.questionnaire_step)))
question = QUESTIONS[step]
field = question.field
progress = round(((step + 1) / len(QUESTIONS)) * 100)

sidebar_column, main_column = st.columns([0.25, 0.75], gap=None)
with sidebar_column:
    with st.container(key="design_sidebar"):
        render_questionnaire_matches_sidebar()

with main_column:
    with st.container(key="design_main"):
        if st.session_state.get("questionnaire_just_completed", False):
            st.html(
                """
                <div class="completion-card">
                    <div class="completion-icon" aria-hidden="true">💗</div>
                    <h1>Your questionnaire is complete</h1>
                    <p>Your answers have been saved and your personalised animal matches are ready.</p>
                </div>
                """
            )
            if st.button("View matches", key="view_matches_primary", type="primary", width="stretch"):
                st.session_state.questionnaire_just_completed = False
                st.switch_page(PAGES["matches"])
            if st.button("Back to questionnaire", key="flow_back", width="stretch"):
                st.session_state.questionnaire_just_completed = False
                st.rerun()
            st.stop()

        st.html(
            f"""
            <div class="flow-page-header">
                <div>
                    <h1>Question {step + 1} of {len(QUESTIONS)}</h1>
                    <p>{"Choose all that apply, then continue" if question.multiple else "Choose one answer then continue"}</p>
                </div>
                <span>{progress}% through</span>
            </div>
            <div class="flow-progress" role="progressbar" aria-label="Questionnaire progress"
                 aria-valuenow="{progress}" aria-valuemin="0" aria-valuemax="100"><span style="width:{progress}%"></span></div>
            """
        )

        if questionnaire_complete:
            if st.button("View matches", key="view_matches_primary", type="primary", width="stretch"):
                st.switch_page(PAGES["matches"])

        with st.container(key="question_card"):
            st.html(f'<p class="question-prompt">{escape(question.prompt)}</p>')

            if not question.options:
                st.html(f'<p class="question-help">{escape(question.hint)}</p>')
                with st.container(key="question_hours"):
                    # Client review 4: a pre-filled number could be accepted without being read, so the
                    # box starts empty and Next stays disabled until the adopter types their own answer.
                    hours = st.number_input(
                        "Hours left alone",
                        min_value=0,
                        max_value=24,
                        value=answers[field],
                        step=1,
                        placeholder="Type a number from 0 to 24",
                    )
                answers[field] = None if hours is None else int(hours)
                if hours is None:
                    st.html('<p class="question-help">Type a number from 0 to 24 to continue.</p>')
            else:
                options = question.options
                selected = answers.get(field)
                if selected is None:
                    selected_indexes = []
                elif question.multiple and selected:
                    selected_indexes = [index for index, option in enumerate(options) if option[2] in selected]
                else:
                    selected_indexes = [index for index, option in enumerate(options) if option[2] == selected]
                if selected_indexes:
                    chosen = ",\n".join(
                        f".st-key-choice_{step}_{index} button, .st-key-choice_{step}_{index} button:hover"
                        for index in selected_indexes
                    )
                    st.html(
                        f"""
                        <style>
                        {chosen} {{
                            border: 2px solid var(--pm-pink-ring) !important;
                            background: #fbeaf4 !important;
                            box-shadow: 0 4px 7px rgba(120,45,80,.25) !important;
                        }}
                        </style>
                        """
                    )
                option_columns = st.columns(len(options), gap="small")
                for index, (label, hint, value) in enumerate(options):
                    with option_columns[index]:
                        if st.button(
                            f"**{label}**\n\n{hint}",  # the style file puts the bold title on its own line
                            key=f"choice_{step}_{index}",
                            width="stretch",
                        ):
                            if question.multiple and value != ():
                                _toggle_species(field, value)
                            else:
                                _select_answer(field, value)

            for message in st.session_state.get("questionnaire_errors", {}).values():
                st.html(f'<p class="field-error" role="alert">{escape(message)}</p>')

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
                        st.session_state.questionnaire_errors = validate_question(field, answers.get(field))
                        if not st.session_state.questionnaire_errors:
                            _move_to(step + 1)
                        st.rerun()
                elif st.button(
                    "Submit questionnaire",
                    key="flow_submit",
                    type="primary",
                    width="stretch",
                    disabled=not answer_is_present,
                ):
                    with database() as conn:
                        results, errors = services.submit_questionnaire(conn, user, answers)
                    if errors:
                        st.session_state.questionnaire_errors = {
                            "all": "One or more answers are invalid. Please check each question."
                        }
                        st.rerun()
                    st.session_state.questionnaire_just_completed = True
                    st.rerun()
