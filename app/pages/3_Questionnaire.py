"""Questionnaire placeholder connected to the PawMatch dashboard."""

import streamlit as st

from pawmatch_style import apply_dashboard_style

st.set_page_config(page_title="PawMatch | Questionnaire", page_icon="📝", layout="wide")
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")
apply_dashboard_style()

with st.container(key="success_card"):
    st.markdown("# 📝 Adoption questionnaire")
    st.write(
        "This page is connected to the dashboard and is ready for your planned "
        "questionnaire fields and scoring inputs."
    )
    st.caption("The dashboard currently reads progress from st.session_state.questionnaire_progress.")
    if st.button("Back to dashboard", key="secondary_button", width="stretch"):
        st.switch_page("pages/1_Home.py")
