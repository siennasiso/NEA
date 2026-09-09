"""Display the user's highest-ranked stored PawMatch recommendations."""

from __future__ import annotations

import streamlit as st

from pawmatch_animals import format_age
from pawmatch_matching import fetch_latest_matches, fetch_latest_response
from pawmatch_style import apply_dashboard_style

st.set_page_config(page_title="PawMatch | My matches", page_icon="💗", layout="wide")
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")
if st.session_state.get("role") == "admin":
    st.switch_page("pages/7_Admin_Dashboard.py")
apply_dashboard_style()

user_id = int(st.session_state.user_id)
latest_response = fetch_latest_response(user_id)
matches = fetch_latest_matches(user_id)[:5] if latest_response else []

if latest_response is None:
    with st.container(key="success_card"):
        st.markdown("# 🔒 Complete the questionnaire first")
        st.write("Ranked recommendations are calculated after the seven answers are submitted.")
        if st.button("Open questionnaire", key="secondary_button", width="stretch"):
            st.switch_page("pages/3_Questionnaire.py")
else:
    st.session_state.questionnaire_complete = True
    st.session_state.questionnaire_progress = 100
    st.session_state.match_count = len(matches)
    st.markdown("# 💗 Your best matches")
    st.write("Compatibility measures welfare requirements. Preferences only decide the order of otherwise suitable animals.")

    if not matches:
        st.warning("No available animals currently reach the minimum possible-match score. Try updating your answers later.")

    for position, match in enumerate(matches, start=1):
        with st.container(border=True):
            heading, score = st.columns([3, 1])
            heading.markdown(f"### {position}. {match['name']}")
            heading.caption(f"{match['species']} · {match['breed']} · {format_age(match['age_years'])} · {match['size']}")
            score.metric(f"{match['match_category']} match", f"{match['compatibility_score']}%")
            st.write(match["description"])
            met_column, unmet_column = st.columns(2)
            with met_column:
                st.markdown("**Requirements met**")
                for reason in match["matched_requirements"]:
                    st.write(f"✓ {reason}")
            with unmet_column:
                st.markdown("**Important considerations**")
                if match["unmet_requirements"]:
                    for reason in match["unmet_requirements"]:
                        st.write(f"• {reason}")
                else:
                    st.write("No unmet requirements.")

    left, right = st.columns(2)
    if left.button("Update questionnaire", width="stretch"):
        st.session_state.questionnaire_step = 0
        st.session_state.questionnaire_progress = 0
        st.switch_page("pages/3_Questionnaire.py")
    if right.button("Back to dashboard", key="secondary_button", width="stretch"):
        st.switch_page("pages/1_Home.py")
