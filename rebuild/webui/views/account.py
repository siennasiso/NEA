"""Show the signed-in user's account and its questionnaire matches link (the original pages/5_My_Account.py)."""

from __future__ import annotations

import html

import streamlit as st

from pawmatch import db
from webui.pawmatch_style import apply_questionnaire_matches_style, render_questionnaire_matches_sidebar
from webui.state import PAGES, database, require_adopter

st.set_page_config(page_title="PawMatch | My account", page_icon="👤", layout="wide")
user = require_adopter()

with database() as conn:
    matches_ready = db.latest_response(conn, user.user_id) is not None

apply_questionnaire_matches_style("account")

sidebar_column, main_column = st.columns([0.25, 0.75], gap=None)
with sidebar_column:
    with st.container(key="design_sidebar"):
        render_questionnaire_matches_sidebar()

with main_column:
    with st.container(key="design_main"):
        if st.button("← Back to home", key="page_back"):
            st.switch_page(PAGES["home"])
        st.html('<div class="flow-page-header"><div><h1>My account</h1><p>Your PawMatch profile and personalised results.</p></div></div>')
        signed_in_with = "Google" if st.session_state.get("signed_in_with") == "google" else "Email and password"
        st.html(
            f"""
            <div class="account-card">
                <div class="account-avatar" aria-hidden="true">👤</div>
                <h2>{html.escape(user.name)}</h2>
                <p class="account-line"><strong>Email:</strong> {html.escape(user.email)}</p>
                <p class="account-line"><strong>Signed in with:</strong> {signed_in_with}</p>
                <p class="account-line"><strong>Questionnaire:</strong> {'Complete' if matches_ready else 'Not complete'}</p>
            </div>
            """
        )
        st.html('<p class="browse-section-title">My matches</p>')
        if st.button(
            "View my matches" if matches_ready else "Complete questionnaire to unlock matches",
            key="view_matches_primary",
            width="stretch",
            disabled=not matches_ready,
        ):
            st.switch_page(PAGES["matches"])
        if not matches_ready and st.button("Go to questionnaire", key="flow_next", width="stretch"):
            st.switch_page(PAGES["questionnaire"])
