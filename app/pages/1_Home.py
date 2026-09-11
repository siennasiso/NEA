"""PawMatch home page matching the three-action interface design."""

from __future__ import annotations

import html

import streamlit as st

from pawmatch_matching import fetch_latest_matches, fetch_latest_response
from pawmatch_style import apply_questionnaire_matches_style, render_questionnaire_matches_sidebar

st.set_page_config(page_title="PawMatch | Home", page_icon="🐾", layout="wide")
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")
if st.session_state.get("role") == "admin":
    st.switch_page("pages/7_Admin_Dashboard.py")

latest_response = fetch_latest_response(int(st.session_state.user_id))
questionnaire_complete = latest_response is not None
if questionnaire_complete:
    st.session_state.questionnaire_complete = True
    st.session_state.questionnaire_progress = 100
    st.session_state.match_count = min(3, len(fetch_latest_matches(int(st.session_state.user_id))))

apply_questionnaire_matches_style("home")
full_name = str(st.session_state.get("user_name", "PawMatch user")).strip()
first_name = html.escape(full_name.split()[0] if full_name else "there")

sidebar_column, main_column = st.columns([0.25, 0.75], gap=None)
with sidebar_column:
    with st.container(key="design_sidebar"):
        render_questionnaire_matches_sidebar()

with main_column:
    with st.container(key="design_main"):
        st.markdown(
            f"""
            <div class="flow-page-header home-design-header">
                <div>
                    <h1>Welcome Back {first_name}</h1>
                    <p>Time to find your purrfect companion!</p>
                </div>
            </div>
            <p class="profile-description">Browse the animals waiting for a home, tell PawMatch about your lifestyle, and view your account.</p>
            <p class="browse-section-title">MAIN ACTIONS</p>
            """,
            unsafe_allow_html=True,
        )

        browse_column, questionnaire_column, account_column = st.columns(3, gap="medium")
        with browse_column:
            with st.container(key="home_action_browse"):
                st.markdown('<div class="home-design-icon">🐾</div>', unsafe_allow_html=True)
                if st.button("Browse animals", key="home_browse", width="stretch"):
                    st.switch_page("pages/4_Browse_Animals.py")
        with questionnaire_column:
            with st.container(key="home_action_questionnaire"):
                st.markdown('<div class="home-design-icon">📝</div>', unsafe_allow_html=True)
                if st.button("Take questionnaire", key="home_questionnaire", width="stretch"):
                    st.switch_page("pages/3_Questionnaire.py")
        with account_column:
            with st.container(key="home_action_account"):
                st.markdown('<div class="home-design-icon">👤</div>', unsafe_allow_html=True)
                if st.button("View account", key="home_account", width="stretch"):
                    st.switch_page("pages/5_My_Account.py")

        st.markdown('<p class="browse-section-title">HOW IT WORKS</p>', unsafe_allow_html=True)
        step_columns = st.columns(3, gap="medium")
        steps = (
            ("1", "Tell us about your lifestyle", "Answer questions about your home, routine and preferences."),
            ("2", "We compare requirements", "The algorithm compares your answers with each animal's needs."),
            ("3", "View explained matches", "See ranked animals, compatibility scores and clear reasons."),
        )
        for column, (number, title, copy) in zip(step_columns, steps):
            with column:
                st.markdown(f'<div class="home-step-card"><div class="home-step-number">{number}</div><h3>{title}</h3><p>{copy}</p></div>', unsafe_allow_html=True)
