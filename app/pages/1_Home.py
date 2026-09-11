"""PawMatch home page built with native Streamlit components."""

from __future__ import annotations

import streamlit as st

from pawmatch_style import apply_questionnaire_matches_style, render_questionnaire_matches_sidebar

st.set_page_config(page_title="PawMatch | Home", page_icon="🐾", layout="wide")
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")
if st.session_state.get("role") == "admin":
    st.switch_page("pages/7_Admin_Dashboard.py")

apply_questionnaire_matches_style("home")

full_name = str(st.session_state.get("user_name", "PawMatch user")).strip()
first_name = full_name.split()[0] if full_name else "there"

sidebar_column, main_column = st.columns([0.25, 0.75], gap=None)
with sidebar_column:
    with st.container(key="design_sidebar"):
        render_questionnaire_matches_sidebar()

with main_column:
    with st.container(key="design_main"):
        with st.container(key="home_intro"):
            st.title(f"Welcome Back {first_name}")
            st.caption("Time to find your purrfect companion!")
            st.write(
                "Browse available animals, describe your home and lifestyle and "
                "receive ranked recommendations with clear compatibility information."
            )

        with st.container(key="home_actions_heading"):
            st.subheader("MAIN ACTIONS")

        browse_column, questionnaire_column, account_column = st.columns(3, gap="large")
        with browse_column:
            with st.container(key="home_action_browse"):
                st.button("🐾", key="home_icon_browse", disabled=True)
                st.page_link("pages/4_Browse_Animals.py", label="Browse animals")

        with questionnaire_column:
            with st.container(key="home_action_questionnaire"):
                st.button("✓", key="home_icon_questionnaire", disabled=True)
                st.page_link("pages/3_Questionnaire.py", label="Take questionnaire")

        with account_column:
            with st.container(key="home_action_account"):
                st.button("●", key="home_icon_account", disabled=True)
                st.page_link("pages/5_My_Account.py", label="View account")

        with st.container(key="home_how_heading"):
            st.subheader("HOW IT WORKS")

        step_one, step_two, step_three = st.columns(3, gap="large")
        steps = (
            (
                step_one,
                "home_step_one",
                "1",
                "Tell us about your lifestyle",
                "Answer questions about your home, routine and preferences.",
            ),
            (
                step_two,
                "home_step_two",
                "2",
                "Compare requirements",
                "Your answers are compared with each animal's needs.",
            ),
            (
                step_three,
                "home_step_three",
                "3",
                "Receive explained matches",
                "Review ranked results and clear compatibility information.",
            ),
        )
        for column, key, number, heading, description in steps:
            with column:
                with st.container(key=key):
                    st.button(number, key=f"{key}_number", disabled=True)
                    st.markdown(f"**{heading}**")
                    st.caption(description)
