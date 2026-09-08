"""Ranked matches placeholder connected to the PawMatch dashboard."""

import streamlit as st

from pawmatch_style import apply_dashboard_style

st.set_page_config(page_title="PawMatch | My matches", page_icon="💗", layout="wide")
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")
apply_dashboard_style()

if not st.session_state.get("questionnaire_complete", False):
    with st.container(key="success_card"):
        st.markdown("# 🔒 Complete the questionnaire first")
        st.write(
            "Ranked recommendations cannot be calculated until the questionnaire "
            "answers have been submitted."
        )
        if st.button("Open questionnaire", key="secondary_button", width="stretch"):
            st.switch_page("pages/3_Questionnaire.py")
else:
    with st.container(key="success_card"):
        st.markdown("# 💗 My matches")
        st.write(
            "This page is ready for ranked animal cards showing the compatibility "
            "score, match category and any unmet requirements."
        )
        if st.button("Back to dashboard", key="secondary_button", width="stretch"):
            st.switch_page("pages/1_Home.py")
