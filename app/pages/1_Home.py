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
