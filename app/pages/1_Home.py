"""PawMatch home page matching the three-action interface design."""

from __future__ import annotations

import html
from textwrap import dedent

import streamlit as st

from pawmatch_style import apply_questionnaire_matches_style, render_questionnaire_matches_sidebar

st.set_page_config(page_title="PawMatch | Home", page_icon="🐾", layout="wide")
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")
if st.session_state.get("role") == "admin":
    st.switch_page("pages/7_Admin_Dashboard.py")

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
            dedent(
                f"""
            <main class="home-mockup">
                <header class="home-mockup-header">
                    <h1>Welcome Back {first_name}</h1>
                    <p class="home-mockup-subtitle">Time to find your purrfect companion!</p>
                    <p class="home-mockup-intro">Browse available animals, describe your home and lifestyle and receive ranked<br>recommendations with clear compatibility information.</p>
                </header>

                <h2 class="home-mockup-label">MAIN ACTIONS</h2>
                <nav class="home-actions-grid" aria-label="Main actions">
                    <a class="home-action-card" href="/Browse_Animals" target="_self">
                        <span class="home-design-icon" aria-hidden="true">🐾</span>
                        <strong>Browse animals</strong>
                    </a>
                    <a class="home-action-card" href="/Questionnaire" target="_self">
                        <span class="home-design-icon" aria-hidden="true">✓</span>
                        <strong>Take questionnaire</strong>
                    </a>
                    <a class="home-action-card" href="/My_Account" target="_self">
                        <span class="home-design-icon" aria-hidden="true">●</span>
                        <strong>View account</strong>
                    </a>
                </nav>

                <h2 class="home-mockup-label home-how-label">HOW IT WORKS</h2>
                <section class="home-steps-grid" aria-label="How PawMatch works">
                    <article class="home-step-card">
                        <span class="home-step-number">1</span>
                        <h3>Tell us about your lifestyle</h3>
                        <p>Answer questions about your home, routine and preferences.</p>
                    </article>
                    <article class="home-step-card">
                        <span class="home-step-number">2</span>
                        <h3>Compare requirements</h3>
                        <p>Your answers are compared with each animal's needs.</p>
                    </article>
                    <article class="home-step-card">
                        <span class="home-step-number">3</span>
                        <h3>Receive explained matches</h3>
                        <p>Review ranked results and clear compatibility information.</p>
                    </article>
                </section>
            </main>
            """
            ).replace("\n", ""),
            unsafe_allow_html=True,
        )
<<<<<<< HEAD
=======

        browse_column, questionnaire_column, account_column = st.columns(3, gap="medium")
        with browse_column:
            with st.container(key="animal_card_home_browse"):
                st.markdown('<div class="account-avatar">🐾</div><div class="animal-card-copy"><h3>Browse animals</h3><p class="animal-description">Search the available animals and open their full profiles.</p></div>', unsafe_allow_html=True)
                if st.button("Browse animals", key="home_browse", width="stretch"):
                    st.switch_page("pages/4_Browse_Animals.py")
        with questionnaire_column:
            with st.container(key="animal_card_home_questionnaire"):
                st.markdown('<div class="account-avatar">📝</div><div class="animal-card-copy"><h3>Take questionnaire</h3><p class="animal-description">Answer seven questions to calculate your best matches.</p></div>', unsafe_allow_html=True)
                if st.button("Open questionnaire", key="home_questionnaire", width="stretch"):
                    st.switch_page("pages/3_Questionnaire.py")
        with account_column:
            with st.container(key="animal_card_home_account"):
                st.markdown('<div class="account-avatar">👤</div><div class="animal-card-copy"><h3>My account</h3><p class="animal-description">View your profile and access My Matches under your account.</p></div>', unsafe_allow_html=True)
                if st.button("View account", key="home_account", width="stretch"):
                    st.switch_page("pages/5_My_Account.py")

        if questionnaire_complete:
            st.markdown('<p class="browse-section-title">YOUR QUESTIONNAIRE IS COMPLETE</p>', unsafe_allow_html=True)
            if st.button("View matches", key="view_matches_primary", type="primary", width="stretch"):
                st.switch_page("pages/6_My_Matches.py")

        st.markdown('<p class="browse-section-title">HOW IT WORKS</p>', unsafe_allow_html=True)
        step_columns = st.columns(3, gap="medium")
        steps = (
            ("1", "Tell us about your lifestyle", "Answer questions about your home, routine and preferences."),
            ("2", "We compare requirements", "The algorithm compares your answers with each animal's needs."),
            ("3", "View explained matches", "See ranked animals, compatibility scores and clear reasons."),
        )
        for column, (number, title, copy) in zip(step_columns, steps):
            with column:
                st.markdown(f'<div class="needs-card"><div class="flow-brand-mark">{number}</div><h2>{title}</h2><p class="need-line">{copy}</p></div>', unsafe_allow_html=True)
>>>>>>> parent of 1166e2d (Match sidebar colors to interface design)
