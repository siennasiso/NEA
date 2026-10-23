"""PawMatch home page matching the three-action interface design (the original pages/1_Home.py)."""

from __future__ import annotations

import html

import streamlit as st

from webui.pawmatch_style import apply_questionnaire_matches_style, render_questionnaire_matches_sidebar
from webui.questions import QUESTIONS
from webui.state import PAGES, require_adopter, show_flash

st.set_page_config(page_title="PawMatch | Home", page_icon="🐾", layout="wide")
user = require_adopter()

apply_questionnaire_matches_style("home")
full_name = user.name.strip()
first_name = html.escape(full_name.split()[0] if full_name else "there")

sidebar_column, main_column = st.columns([0.25, 0.75], gap=None)
with sidebar_column:
    with st.container(key="design_sidebar"):
        render_questionnaire_matches_sidebar()

with main_column:
    with st.container(key="design_main"):
        show_flash()
        st.html(
            f"""
            <div class="flow-page-header">
                <div>
                    <h1>Welcome Back {first_name}</h1>
                    <p>Time to find your purrfect companion!</p>
                </div>
            </div>
            <p class="profile-description">Browse the animals waiting for a home, tell PawMatch about your lifestyle, and view your account.</p>
            <p class="browse-section-title">MAIN ACTIONS</p>
            """
        )

        browse_column, questionnaire_column, account_column = st.columns(3, gap="medium")
        with browse_column:
            with st.container(key="animal_card_home_browse"):
                st.html('<div class="account-avatar" aria-hidden="true">🐾</div><div class="animal-card-copy"><h3>Browse animals</h3><p class="animal-description">Search the available animals and open their full profiles.</p></div>')
                if st.button("Browse animals", key="home_browse", width="stretch"):
                    st.switch_page(PAGES["browse"])
        with questionnaire_column:
            with st.container(key="animal_card_home_questionnaire"):
                st.html(f'<div class="account-avatar" aria-hidden="true">📝</div><div class="animal-card-copy"><h3>Take questionnaire</h3><p class="animal-description">Answer {len(QUESTIONS)} questions to calculate your best matches.</p></div>')
                if st.button("Open questionnaire", key="home_questionnaire", width="stretch"):
                    st.switch_page(PAGES["questionnaire"])
        with account_column:
            with st.container(key="animal_card_home_account"):
                st.html('<div class="account-avatar" aria-hidden="true">👤</div><div class="animal-card-copy"><h3>My account</h3><p class="animal-description">View your profile and access My Matches under your account.</p></div>')
                if st.button("View account", key="home_account", width="stretch"):
                    st.switch_page(PAGES["account"])

        st.html('<p class="browse-section-title">HOW IT WORKS</p>')
        step_columns = st.columns(3, gap="medium")
        steps = (
            ("1", "Tell us about your lifestyle", "Answer questions about your home, routine and preferences."),
            ("2", "We compare requirements", "The algorithm compares your answers with each animal's needs."),
            ("3", "View explained matches", "See ranked animals, compatibility scores and clear reasons."),
        )
        for column, (number, title, copy) in zip(step_columns, steps):
            with column:
                st.html(f'<div class="needs-card"><div class="flow-brand-mark">{number}</div><h2>{title}</h2><p class="need-line">{copy}</p></div>')
