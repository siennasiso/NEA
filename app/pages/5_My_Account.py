"""Show the signed-in user's account and its questionnaire matches link."""

from __future__ import annotations

import html

import streamlit as st

from pawmatch_matching import fetch_latest_response
from pawmatch_style import apply_questionnaire_matches_style, render_questionnaire_matches_sidebar

st.set_page_config(page_title="PawMatch | My account", page_icon="👤", layout="wide")
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")
if st.session_state.get("role") == "admin":
    st.switch_page("pages/7_Admin_Dashboard.py")

response = fetch_latest_response(int(st.session_state.user_id))
matches_ready = response is not None
if matches_ready:
    st.session_state.questionnaire_complete = True
    st.session_state.questionnaire_progress = 100

apply_questionnaire_matches_style("account")

sidebar_column, main_column = st.columns([0.25, 0.75], gap=None)
with sidebar_column:
    with st.container(key="design_sidebar"):
        render_questionnaire_matches_sidebar()

with main_column:
    with st.container(key="design_main"):
        if st.button("← Back to home", key="page_back"):
            st.switch_page("pages/1_Home.py")
        st.markdown('<div class="flow-page-header"><div><h1>My account</h1><p>Your PawMatch profile and personalised results.</p></div></div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="account-card">
                <div class="account-avatar">👤</div>
                <h2>{html.escape(str(st.session_state.get('user_name', 'PawMatch user')))}</h2>
                <p class="account-line"><strong>Email:</strong> {html.escape(str(st.session_state.get('user_email', '')))}</p>
                <p class="account-line"><strong>Questionnaire:</strong> {'Complete' if matches_ready else 'Not complete'}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<p class="browse-section-title">My matches</p>', unsafe_allow_html=True)
        if st.button(
            "View my matches" if matches_ready else "Complete questionnaire to unlock matches",
            key="view_matches_primary",
            width="stretch",
            disabled=not matches_ready,
        ):
            st.switch_page("pages/6_My_Matches.py")
        if not matches_ready and st.button("Go to questionnaire", key="flow_next", width="stretch"):
            st.switch_page("pages/3_Questionnaire.py")
