"""Show the top five ranked matches using the interface-design cards (the original pages/6_My_Matches.py).

The scores and reasons come from pawmatch.matching through the stored ranking. One change
from the original: "View animal profile" is a Streamlit page link, not a plain <a href>, so
opening a profile no longer reloads the page and signs the adopter out.
"""

from __future__ import annotations

import base64
import html

import streamlit as st

from pawmatch import services
from webui.animals import format_age
from webui.pawmatch_style import apply_questionnaire_matches_style, render_questionnaire_matches_sidebar
from webui.state import PAGES, database, picture, require_adopter

st.set_page_config(page_title="PawMatch | My matches", page_icon="💗", layout="wide")
user = require_adopter()

apply_questionnaire_matches_style("matches")

with database() as conn:
    results = services.latest_results(conn, user)
SHOWN = 5



def _match_card(position: int, match) -> None:
    animal = match.animal
    score = match.compatibility
    name = html.escape(animal.name)
    encoded = base64.b64encode(picture(animal, 380)).decode("ascii")
    met_lines = "".join(
        f'<span class="requirement-line">✓ {html.escape(reason)}</span>' for reason in match.met
    ) or '<span class="requirement-line">None of this animal\'s requirements are met yet.</span>'
    # Client review 5: an amber "not met" box saying nothing was unmet looked like a warning, and
    # "(welfare need)" was not explained. Welfare needs now get their own red box in plain words,
    # and the amber box only appears when something else is unmet.
    welfare_lines = "".join(f'<span class="requirement-line">! {html.escape(reason)}</span>' for reason in match.warnings)
    other_lines = "".join(f'<span class="requirement-line">! {html.escape(reason)}</span>'
                          for reason in match.unmet if reason not in match.warnings)
    boxes = ""
    if welfare_lines:
        boxes += ('<div class="match-reason welfare"><strong class="requirement-heading">Welfare needs your home may '
                  f'not meet: talk to the shelter first</strong>{welfare_lines}</div>')
    if other_lines:
        boxes += f'<div class="match-reason consideration"><strong class="requirement-heading">Requirements not met</strong>{other_lines}</div>'
    if not match.unmet:
        boxes = '<div class="match-reason"><strong class="requirement-heading">You meet every requirement for this animal</strong></div>'
    with st.container(key=f"match_card_{position}"):
        rank_column, photo_column, details_column, score_column = st.columns(
            [0.055, 0.235, 0.49, 0.22], gap="medium")
        rank_column.html(f'<div class="match-rank" aria-label="Rank {position}">{position}</div>')
        photo_column.html(f'<div class="match-photo"><img src="data:image/jpeg;base64,{encoded}" alt="Photo of {name}"></div>')
        details_column.html(
            f"""
            <div class="match-details">
                <h2 class="match-name">{name}</h2>
                <p class="match-meta">{html.escape(animal.species)} | {html.escape(animal.breed)} | {format_age(animal.age)}</p>
                <div class="match-reason"><strong class="requirement-heading">Requirements met</strong>{met_lines}</div>
                {boxes}
            </div>
            """
        )
        with score_column:
            st.html(
                f"""
                <div class="match-score-area">
                    <div class="match-category">{html.escape(match.category)} Match</div>
                    <div class="score-ring" role="img" aria-label="{score:.1f}% compatible"
                         style="background:conic-gradient(var(--pm-pink-ring) {score}%, #f1d8e4 0)"><span>{score:.1f}%</span></div>
                </div>
                """
            )
            st.page_link(PAGES["browse"], label="View animal profile", query_params={"animal": animal.animal_id},
                         width="stretch")


sidebar_column, main_column = st.columns([0.25, 0.75], gap=None)
with sidebar_column:
    with st.container(key="design_sidebar"):
        render_questionnaire_matches_sidebar()

with main_column:
    with st.container(key="design_main"):
        if st.button("← Back to questionnaire", key="page_back"):
            st.switch_page(PAGES["questionnaire"])
        st.html(
            """
            <div class="flow-page-header matches-heading">
                <div>
                    <h1>Your ranked matches</h1>
                    <p>Animals whose welfare needs you meet come first, then the best compatibility.</p>
                </div>
            </div>
            <p class="score-key"><strong>Score key:</strong> Strong 80% or more · Good 60 to 79% · Possible 40 to 59% ·
            Low under 40%. Scores are a guide: the shelter team meets you and makes the final decision.</p>
            """
        )

        if results is None:
            st.html('<div class="no-matches-card">Complete the questionnaire to calculate your ranked matches.</div>')
            if st.button("Go to questionnaire", key="flow_next", type="primary"):
                st.switch_page(PAGES["questionnaire"])
        elif not results:
            st.html('<div class="no-matches-card">No animals are available for adoption right now. '
                    'Please check back soon.</div>')
        else:
            show_all = st.toggle(f"Show all {len(results)} animals, not just your top {SHOWN}", key="show_all_matches")
            divider_shown = False
            for position, match in enumerate(results if show_all else results[:SHOWN], start=1):
                if match.warnings and not divider_shown:
                    # Client review 5: the order rule was invisible, so the point where it changes is labelled.
                    st.html('<div class="warning-divider">The animals below have at least one welfare need your home '
                            'may not meet, so they are listed after the others even if their score is higher.</div>')
                    divider_shown = True
                _match_card(position, match)
            st.caption("Scores help you think about suitability. Shelter staff always make the final adoption decision.")
