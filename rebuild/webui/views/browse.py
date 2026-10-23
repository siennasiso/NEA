"""Browse and inspect available animal profiles using the interface design (the original pages/4_Browse_Animals.py).

Adopters only ever see animals marked Available (pawmatch.services.browse). As in the
original, a profile opens in place of the list, from "View profile" or ?animal=<id>.
"""

from __future__ import annotations

import html

import streamlit as st

from pawmatch import db, services
from pawmatch.models import SIZES, SPECIES
from webui.animals import format_age, needs_lines
from webui.pawmatch_style import apply_questionnaire_matches_style, render_questionnaire_matches_sidebar
from webui.state import PAGES, database, picture, require_adopter

st.set_page_config(page_title="PawMatch | Browse animals", page_icon="🐾", layout="wide")
user = require_adopter()

apply_questionnaire_matches_style("browse")


def _show_profile(animal_id: int) -> None:
    """Open one animal profile within the browse page."""
    st.session_state.browse_animal_id = animal_id
    st.rerun()


def _clear_filters() -> None:
    """Reset every browse filter to its design default."""
    st.session_state.browse_search = ""
    st.session_state.browse_species = "All species"
    st.session_state.browse_size = "All sizes"


def _selected_animal():
    """The animal to show, if any: only an available one (a reserved animal's old link shows the list)."""
    selected_id = str(st.session_state.get("browse_animal_id") or st.query_params.get("animal") or "")
    if not selected_id.isdigit():
        return None
    with database() as conn:
        animal = db.get_animal(conn, int(selected_id))
        if animal is None or animal.status != services.AVAILABLE:
            return None
        return animal, services.result_for_animal(conn, user, animal.animal_id)


sidebar_column, main_column = st.columns([0.25, 0.75], gap=None)
with sidebar_column:
    with st.container(key="design_sidebar"):
        render_questionnaire_matches_sidebar()

with main_column:
    with st.container(key="design_main"):
        selected = _selected_animal()

        if selected is not None:
            selected_animal, match = selected
            if st.button("← Back to all animals", key="profile_back"):
                st.session_state.pop("browse_animal_id", None)
                st.query_params.clear()
                st.rerun()

            name = html.escape(selected_animal.name)
            st.html(
                f'<div class="profile-title"><h1>Meet {name}</h1><p>{html.escape(selected_animal.species)} · {html.escape(selected_animal.breed)}</p></div>'
            )
            image_column, description_column = st.columns([1, 1.25], gap="large")
            with image_column:
                st.image(picture(selected_animal, 720), width="stretch", caption=None)
            with description_column:
                st.html(f'<p class="profile-description">{html.escape(selected_animal.personality)}</p>')
                fact_columns = st.columns(3, gap="small")
                facts = (("Age", format_age(selected_animal.age)), ("Sex", selected_animal.sex), ("Size", selected_animal.size))
                for column, (label, value) in zip(fact_columns, facts):
                    with column:
                        st.html(f'<div class="profile-fact"><strong>{html.escape(str(value))}</strong>{label}</div>')

                if match is not None:
                    score_text = f"{match.compatibility:.1f}% compatible · {match.category} match"
                    # Client review 5: a welfare warning (such as an allergy) was the last line of the list,
                    # so warnings now come first, in their own box, in plain words.
                    warnings = "".join(f'<p class="need-line">! {html.escape(line)}</p>' for line in match.warnings)
                    warning_box = (f'<div class="welfare-warning" role="alert"><strong>Talk to the shelter before choosing '
                                   f'{name}</strong>{warnings}</div>') if warnings else ""
                    reasons = "".join(f'<p class="need-line">✓ {html.escape(line)}</p>' for line in match.met)
                    reasons += "".join(f'<p class="need-line">! {html.escape(line)}</p>'
                                       for line in match.unmet if line not in match.warnings)
                    st.html(f'<div class="needs-card"><h2>Your compatibility</h2><p class="need-line"><strong>{score_text}</strong></p>'
                            f'{warning_box}{reasons}</div>')
                else:
                    st.html('<div class="needs-card"><h2>Your compatibility</h2><p class="need-line">'
                            '<strong>Answer the questionnaire to see how well you match.</strong></p></div>')
                    # Client review 3: the message is now a button that goes straight to the questionnaire.
                    if st.button("Take the questionnaire", key="profile_questionnaire", type="primary", width="stretch"):
                        st.switch_page(PAGES["questionnaire"])

            lines = "".join(f'<p class="need-line"><strong>{label}:</strong> {html.escape(value)}</p>'
                            for label, value in needs_lines(selected_animal))
            medical = (f'<p class="need-line"><strong>Health notes:</strong> {html.escape(selected_animal.medical_notes)}</p>'
                       if selected_animal.medical_notes else "")
            st.html(f'<div class="needs-card"><h2>What {name} Needs from a Home</h2>{lines}{medical}</div>')
        else:
            st.session_state.pop("browse_animal_id", None)
            if st.button("← Back to home", key="page_back"):
                st.switch_page(PAGES["home"])
            st.html('<div class="flow-page-header"><div><h1>Find your next companion</h1><p>Search and filter the animals currently available for adoption.</p></div></div>')

            with st.container(key="browse_filter_card"):
                # Client review 3: a size filter, as asked for in the interview and the Design.
                search_column, species_column, size_column, clear_column = st.columns(
                    [1.4, 1, 1, .75], gap="small", vertical_alignment="bottom")
                with search_column:
                    search = st.text_input("Search", key="browse_search", placeholder="Name or breed", max_chars=20)
                with species_column:
                    species = st.selectbox("Species", ("All species", *SPECIES), key="browse_species")
                with size_column:
                    size = st.selectbox("Size", ("All sizes", *SIZES), key="browse_size")
                with clear_column:
                    st.button("Clear filters", on_click=_clear_filters, width="stretch")

            with database() as conn:
                animals = services.browse(conn, None if species == "All species" else species,
                                          None if size == "All sizes" else size, search)
            st.html(f'<p class="browse-section-title">Available animals · {len(animals)}</p>')
            if not animals:
                st.info("No available animals match those filters. Try another name, or clear the filters.")
            else:
                for row_start in range(0, len(animals), 3):
                    columns = st.columns(3, gap="medium")
                    for column, animal in zip(columns, animals[row_start:row_start + 3]):
                        with column:
                            with st.container(key=f"animal_card_{animal.animal_id}"):
                                st.image(picture(animal), width="stretch")
                                st.html(
                                    f"""<div class="animal-card-copy"><h3>{html.escape(animal.name)}</h3><p class="animal-breed">{html.escape(animal.species)} · {html.escape(animal.breed)}</p><p class="animal-facts">{format_age(animal.age)} · {html.escape(animal.sex)} · {html.escape(animal.size)}</p><p class="animal-description">{html.escape(animal.personality)}</p></div>"""
                                )
                                if st.button("View profile", key=f"view_profile_{animal.animal_id}", width="stretch"):
                                    _show_profile(animal.animal_id)
