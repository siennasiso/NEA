"""Browse and inspect available animal profiles using the interface design."""

from __future__ import annotations

import html

import streamlit as st

from pawmatch_animals import SPECIES, animal_image_path, fetch_animal, fetch_animals, format_age, seed_demo_animals
from pawmatch_matching import calculate_match, fetch_latest_matches, fetch_latest_response
from pawmatch_style import apply_questionnaire_matches_style, render_questionnaire_matches_sidebar

st.set_page_config(page_title="PawMatch | Browse animals", page_icon="🐾", layout="wide")
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")
if st.session_state.get("role") == "admin":
    st.switch_page("pages/7_Admin_Dashboard.py")

apply_questionnaire_matches_style("browse")
seed_demo_animals()


def _show_profile(animal_id: int) -> None:
    """Open one animal profile within the browse page."""
    st.session_state.browse_animal_id = animal_id
    st.rerun()


def _clear_filters() -> None:
    """Reset every browse filter to its design default."""
    st.session_state.browse_search = ""
    st.session_state.browse_species = "All species"


sidebar_column, main_column = st.columns([0.25, 0.75], gap=None)
with sidebar_column:
    with st.container(key="design_sidebar"):
        render_questionnaire_matches_sidebar()

with main_column:
    with st.container(key="design_main"):
        selected_id = st.session_state.get("browse_animal_id") or st.query_params.get("animal")
        selected_animal = fetch_animal(int(selected_id)) if selected_id else None

        if selected_animal is not None:
            if st.button("← Back to all animals", key="profile_back"):
                st.session_state.pop("browse_animal_id", None)
                st.query_params.clear()
                st.rerun()

            name = html.escape(str(selected_animal["name"]))
            st.markdown(
                f'<div class="profile-title"><h1>Meet {name}</h1><p>{html.escape(str(selected_animal["species"]))} · {html.escape(str(selected_animal["breed"]))}</p></div>',
                unsafe_allow_html=True,
            )
            with st.container(key="profile_hero_card"):
                image_column, description_column = st.columns([1, 1.45], gap="medium")
                with image_column:
                    with st.container(key="profile_image"):
                        portrait = animal_image_path(selected_animal["name"])
                        if portrait.exists():
                            st.image(str(portrait), width="stretch")
                with description_column:
                    st.markdown(f'<h2 class="profile-description-title">{name} description</h2>', unsafe_allow_html=True)
                    st.markdown(f'<div class="profile-description-box">{html.escape(str(selected_animal["description"]))}</div>', unsafe_allow_html=True)
                    fact_columns = st.columns(3, gap="small")
                    facts = (("Age", format_age(selected_animal["age_years"])), ("Sex", selected_animal["sex"]), ("Size", selected_animal["size"]))
                    for column, (label, value) in zip(fact_columns, facts):
                        with column:
                            st.markdown(f'<div class="profile-fact"><span>{label}</span><strong>{html.escape(str(value))}</strong></div>', unsafe_allow_html=True)

            latest_response = fetch_latest_response(int(st.session_state.user_id))
            stored_match = next((match for match in fetch_latest_matches(int(st.session_state.user_id), include_low=True) if int(match["animal_id"]) == int(selected_animal["animal_id"])), None)
            detailed_match = calculate_match(selected_animal, latest_response) if latest_response is not None else None

            needs_column, match_column = st.columns([1.7, 1], gap="medium")
            with needs_column:
                st.markdown(
                    f"""
                    <div class="profile-needs-card">
                        <h2>What {name} Needs from a Home</h2>
                        <div class="profile-needs-grid">
                            <div><span>Activity</span><strong>{html.escape(str(selected_animal['activity_level']))}</strong></div>
                            <div><span>Home Type</span><strong>{html.escape(str(selected_animal['home_type']))}</strong></div>
                            <div><span>Garden</span><strong>{'Required' if selected_animal['garden_required'] else 'Not required'}</strong></div>
                            <div><span>Children</span><strong>{html.escape(str(selected_animal['child_friendly']))}</strong></div>
                            <div><span>Time alone</span><strong>{int(selected_animal['max_hours_alone'])} hours</strong></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with match_column:
                if detailed_match is None:
                    st.markdown('<div class="profile-match-card"><h2>Your match</h2><p>Complete the questionnaire to see your compatibility.</p></div>', unsafe_allow_html=True)
                else:
                    score = int(stored_match["compatibility_score"] if stored_match else detailed_match["compatibility_score"])
                    category = html.escape(str(detailed_match["match_category"]))
                    met = html.escape(str(detailed_match["matched_requirements"][0])) if detailed_match["matched_requirements"] else "No requirements met."
                    unmet = html.escape(str(detailed_match["unmet_requirements"][0])) if detailed_match["unmet_requirements"] else "No important concerns."
                    st.markdown(
                        f"""
                        <div class="profile-match-card">
                            <h2>A {category.lower()} match</h2>
                            <div class="profile-score-row">
                                <div class="score-ring" style="background:conic-gradient(#d84d8b {score}%, #f1d8e4 0)"><span>{score}%</span></div>
                                <div><strong>{category.upper()} MATCH</strong><small>Compatibility with your home and lifestyle.</small></div>
                            </div>
                            <div class="profile-score-track"><span style="width:{score}%"></span></div>
                            <p class="profile-met">✓ {met}</p>
                            <p class="profile-unmet">! {unmet}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.session_state.pop("browse_animal_id", None)
            if st.button("← Back to home", key="page_back"):
                st.switch_page("pages/1_Home.py")
            st.markdown('<div class="flow-page-header"><div><h1>Find your next companion</h1><p>Search and filter the animals currently available for adoption.</p></div></div>', unsafe_allow_html=True)

            with st.container(key="browse_filter_card"):
                search_column, species_column, clear_column = st.columns([1.5, 1, .75], gap="small")
                with search_column:
                    search = st.text_input("Search", key="browse_search", placeholder="Name or breed")
                with species_column:
                    species = st.selectbox("Species", ("All species", *SPECIES), key="browse_species")
                with clear_column:
                    st.write("")
                    st.write("")
                    st.button("Clear filters", on_click=_clear_filters, width="stretch")

            animals = fetch_animals(search, species, "Available")
            st.markdown(f'<p class="browse-section-title">Available animals · {len(animals)}</p>', unsafe_allow_html=True)
            if not animals:
                st.info("No available animals match those filters.")
            else:
                for row_start in range(0, len(animals), 3):
                    columns = st.columns(3, gap="medium")
                    for column, animal in zip(columns, animals[row_start:row_start + 3]):
                        with column:
                            with st.container(key=f"animal_card_{animal['animal_id']}"):
                                portrait = animal_image_path(animal["name"])
                                if portrait.exists():
                                    st.image(str(portrait), width="stretch")
                                st.markdown(
                                    f"""<div class="animal-card-copy"><h3>{html.escape(str(animal['name']))}</h3><p class="animal-breed">{html.escape(str(animal['species']))} · {html.escape(str(animal['breed']))}</p><p class="animal-facts">{format_age(animal['age_years'])} · {html.escape(str(animal['sex']))} · {html.escape(str(animal['size']))}</p><p class="animal-description">{html.escape(str(animal['description']))}</p></div>""",
                                    unsafe_allow_html=True,
                                )
                                if st.button("View profile", key=f"view_profile_{animal['animal_id']}", width="stretch"):
                                    _show_profile(int(animal["animal_id"]))
