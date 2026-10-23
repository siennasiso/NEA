"""Step-by-step questionnaire (criterion 6): one section at a time, validated before moving on."""

import streamlit as st

from pawmatch import services
from pawmatch.models import ACTIVITY_LEVELS, EXPERIENCE_LEVELS, HOUSING_LEVELS, NO_PREFERENCE, SIZES, SPECIES
from pawmatch.validation import QUESTION_STEPS, validate_step
from webui.components import show_errors
from webui.state import PAGES, database, require_login

YES_NO = ("Yes", "No")
QUESTIONS = {
    "housing_level": ("What type of home do you live in?", tuple(HOUSING_LEVELS), HOUSING_LEVELS.get),
    "garden_access": ("Do you have a secure garden?", YES_NO, str),
    "has_children": ("Are there children under 16 in your home?", YES_NO, str),
    "other_pets": ("Do you have other pets?", YES_NO, str),
    "activity_level": ("How much daily activity can you give an animal?", tuple(ACTIVITY_LEVELS), ACTIVITY_LEVELS.get),
    "hours_alone": ("On a normal day, how many hours would the animal be alone?", tuple(range(25)),
                    lambda h: f"{h} hour{'s' if h != 1 else ''}"),
    "experience": ("How much experience do you have with animals?", EXPERIENCE_LEVELS, str),
    "preferred_species": ("Which species would you prefer?", SPECIES + (NO_PREFERENCE,), str),
    "preferred_size": ("Which size would you prefer?", SIZES + (NO_PREFERENCE,), str),
}

user = require_login()
step: int = st.session_state.setdefault("q_step", 0)
answers: dict = st.session_state.setdefault("q_answers", {})
last = len(QUESTION_STEPS)  # the review step comes after the question steps

st.title("Adoption questionnaire")
st.progress(step / last, text=f"Step {min(step + 1, last + 1)} of {last + 1}")

if step < last:
    title, names = QUESTION_STEPS[step]
    st.subheader(title)
    for name in names:
        label, options, fmt = QUESTIONS[name]
        saved = answers.get(name)
        answers[name] = st.selectbox(
            label, options, format_func=fmt, placeholder="Choose an answer",
            index=options.index(saved) if saved in options else None, key=f"q-{name}",
        )
    back, nxt, _ = st.columns([1, 1, 4])
    if step > 0 and back.button("Back", icon=":material/arrow_back:"):
        st.session_state["q_step"] = step - 1
        st.rerun()
    if nxt.button("Next", type="primary", icon=":material/arrow_forward:"):
        errors = validate_step(step, answers)
        show_errors(errors)
        if not errors:
            st.session_state["q_step"] = step + 1
            st.rerun()
else:
    st.subheader("Check your answers")
    for name, (label, _, fmt) in QUESTIONS.items():
        st.markdown(f"- {label} **{fmt(answers.get(name)) if answers.get(name) is not None else '—'}**")
    back, submit, _ = st.columns([1, 2, 3])
    if back.button("Change answers", icon=":material/edit:"):
        st.session_state["q_step"] = 0
        st.rerun()
    if submit.button("Submit and see my matches", type="primary"):
        with database() as conn:
            _, errors = services.submit_questionnaire(conn, user, answers)
        show_errors(errors)
        if not errors:
            del st.session_state["q_step"], st.session_state["q_answers"]
            st.switch_page(PAGES["results"])
