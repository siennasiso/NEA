"""Account placeholder connected to the PawMatch dashboard."""

import streamlit as st

from pawmatch_style import apply_dashboard_style

st.set_page_config(page_title="PawMatch | My account", page_icon="👤", layout="wide")
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")
apply_dashboard_style()

with st.container(key="success_card"):
    st.markdown("# 👤 My account")
    st.write(f"**Name:** {st.session_state.get('user_name', '')}")
    st.write(f"**Email:** {st.session_state.get('user_email', '')}")
    st.caption("You can add the editable account fields and validation here later.")
    if st.button("Back to dashboard", key="secondary_button", width="stretch"):
        st.switch_page("pages/1_Home.py")
