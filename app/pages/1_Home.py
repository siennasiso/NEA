"""PawMatch home page matching the three-action interface design."""

from __future__ import annotations

import html

import streamlit as st

from pawmatch_matching import fetch_latest_matches, fetch_latest_response
from pawmatch_style import apply_questionnaire_matches_style, signed_in_main_column

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
    st.session_state.match_count = min(5, len(fetch_latest_matches(int(st.session_state.user_id))))

apply_questionnaire_matches_style("home")
full_name = str(st.session_state.get("user_name", "PawMatch user")).strip()
first_name = html.escape(full_name.split()[0] if full_name else "there")

main_column = signed_in_main_column()

with main_column:
    with st.container(key="design_main"):
        st.markdown(
            f"""
            <header class="home-hero">
                <h1>Find your PawMatch</h1>
                <p class="home-subtitle">Welcome back, {first_name}</p>
                <p class="home-intro">Explore animal profiles or take the questionnaire to see which pets suit your home and routine.</p>
            </header>
            <p class="home-section-title">Main actions</p>
            """,
            unsafe_allow_html=True,
        )

        browse_column, questionnaire_column, account_column = st.columns(3, gap="medium")
        with browse_column:
            with st.container(key="animal_card_home_browse"):
                st.markdown('<div class="home-action-icon">🐾</div><div class="animal-card-copy"><h3>Browse animals</h3><p class="animal-description">Search the animal profiles and learn about their individual needs.</p></div>', unsafe_allow_html=True)
                if st.button("Browse animals", key="home_browse", width="stretch"):
                    st.switch_page("pages/4_Browse_Animals.py")
        with questionnaire_column:
            with st.container(key="animal_card_home_questionnaire"):
                st.markdown('<div class="home-action-icon">📝</div><div class="animal-card-copy"><h3>Take questionnaire</h3><p class="animal-description">Answer seven questions about your home and lifestyle.</p></div>', unsafe_allow_html=True)
                if st.button("Open questionnaire", key="home_questionnaire", type="primary", width="stretch"):
                    st.switch_page("pages/3_Questionnaire.py")
        with account_column:
            with st.container(key="animal_card_home_account"):
                st.markdown('<div class="home-action-icon">👤</div><div class="animal-card-copy"><h3>My account</h3><p class="animal-description">View your details and return to your latest matches.</p></div>', unsafe_allow_html=True)
                if st.button("View account", key="home_account", width="stretch"):
                    st.switch_page("pages/5_My_Account.py")

        st.markdown('<p class="home-section-title home-how-title">How it works</p>', unsafe_allow_html=True)
        step_columns = st.columns(3, gap="medium")
        steps = (
            ("1", "Tell us about your lifestyle", "Answer questions about your home, routine and preferences."),
            ("2", "We compare requirements", "The algorithm compares your answers with each animal's needs."),
            ("3", "View explained matches", "See ranked animals, compatibility scores and clear reasons."),
        )
        for column, (number, title, copy) in zip(step_columns, steps):
            with column:
                st.markdown(f'<div class="home-step-card"><div class="home-step-number">{number}</div><h2>{title}</h2><p>{copy}</p></div>', unsafe_allow_html=True)
