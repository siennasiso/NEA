"""Show the three highest ranked matches using the interface-design cards."""

from __future__ import annotations

import base64
import html

import streamlit as st

from pawmatch_animals import animal_image_path, format_age
from pawmatch_matching import fetch_latest_matches, fetch_latest_response
from pawmatch_style import (
    apply_questionnaire_matches_style,
    render_questionnaire_matches_sidebar,
)

st.set_page_config(page_title="PawMatch | My matches", page_icon="💗", layout="wide")
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")
if st.session_state.get("role") == "admin":
    st.switch_page("pages/7_Admin_Dashboard.py")

apply_questionnaire_matches_style("matches")

user_id = int(st.session_state.user_id)
latest_response = fetch_latest_response(user_id)
matches = fetch_latest_matches(user_id)[:3] if latest_response else []
species_icons = {"Dog": "🐕", "Cat": "🐈", "Rabbit": "🐇"}

sidebar_column, main_column = st.columns([0.25, 0.75], gap=None)
with sidebar_column:
    with st.container(key="design_sidebar"):
        render_questionnaire_matches_sidebar()

with main_column:
    with st.container(key="design_main"):
        if st.button("← Back to questionnaire", key="page_back"):
            st.switch_page("pages/3_Questionnaire.py")
        st.markdown(
            """
            <div class="flow-page-header matches-heading">
                <div>
                    <h1>Your ranked matches</h1>
                    <p>Animals are ranked from highest compatibility to the lowest compatibility.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if latest_response is None:
            st.markdown(
                '<div class="no-matches-card">Complete the questionnaire to calculate your ranked matches.</div>',
                unsafe_allow_html=True,
            )
        elif not matches:
            st.markdown(
                '<div class="no-matches-card">No available animals currently reach the minimum possible-match score.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.session_state.questionnaire_complete = True
            st.session_state.questionnaire_progress = 100
            st.session_state.match_count = len(matches)

            for position, match in enumerate(matches, start=1):
                score = int(match["compatibility_score"])
                name = html.escape(str(match["name"]))
                species = html.escape(str(match["species"]))
                breed = html.escape(str(match["breed"]))
                age = html.escape(format_age(match["age_years"]))
                portrait = animal_image_path(match["name"])
                if portrait.exists():
                    encoded = base64.b64encode(portrait.read_bytes()).decode("ascii")
                    image_markup = f'<img src="data:image/png;base64,{encoded}" alt="{name}">'
                else:
                    image_markup = species_icons.get(str(match["species"]), "🐾")
                category = html.escape(str(match["match_category"]))
                met = html.escape(
                    str(match["matched_requirements"][0])
                    if match["matched_requirements"]
                    else "Suitable requirements were identified."
                )
                unmet = html.escape(
                    str(match["unmet_requirements"][0])
                    if match["unmet_requirements"]
                    else "No important unmet requirements."
                )
                st.markdown(
                    f"""
                    <article class="match-card">
                        <div class="match-rank">{position}</div>
                        <div class="match-photo" aria-label="{species}">{image_markup}</div>
                        <div class="match-details">
                            <h2 class="match-name">{name}</h2>
                            <p class="match-meta">{species} | {breed} | {age}</p>
                            <p class="match-reason">✓ {met}</p>
                            <p class="match-reason consideration">! {unmet}</p>
                        </div>
                        <div class="match-score-area">
                            <div class="match-category">{category} Match</div>
                            <div class="score-ring" style="background:conic-gradient(#d84d8b {score}%, #f1d8e4 0)"><span>{score}%</span></div>
                            <a class="profile-button" href="/Browse_Animals?animal={int(match['animal_id'])}" target="_self">View animal profile</a>
                        </div>
                    </article>
                    """,
                    unsafe_allow_html=True,
                )
