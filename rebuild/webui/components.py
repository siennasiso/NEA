"""Reusable display pieces: animal cards, requirement lists and match cards."""

from __future__ import annotations

import streamlit as st

from pawmatch.models import ACTIVITY_LEVELS, HOUSING_LEVELS, Animal, MatchResult

from .state import PAGES, image_for

CATEGORY_COLOURS = {"Strong": "green", "Good": "blue", "Possible": "orange", "Low": "red"}


def _image(animal: Animal) -> None:
    path = image_for(animal.image_path)
    if path:
        st.image(path, width="stretch")
    else:
        st.markdown(f"### {'🐶' if animal.species == 'Dog' else '🐱' if animal.species == 'Cat' else '🐰'}")


def open_profile(animal_id: int, came_from: str) -> None:
    st.session_state["profile_back"] = came_from
    st.switch_page(PAGES["profile"], query_params={"id": str(animal_id)})


def animal_card(animal: Animal, came_from: str) -> None:
    """Compact preview card (criterion 3.2): image, name, species, breed and age."""
    with st.container(border=True):
        _image(animal)
        st.markdown(f"**{animal.name}**")
        st.caption(f"{animal.species} · {animal.breed} · {animal.age} yr")
        if st.button("View profile", key=f"view-{came_from}-{animal.animal_id}", width="stretch"):
            open_profile(animal.animal_id, came_from)


def requirements(animal: Animal) -> list[str]:
    return [
        f"Space: at least {HOUSING_LEVELS[animal.min_housing_level].lower()}",
        "Garden: required" if animal.garden_required else "Garden: not required",
        "Children: suitable" if animal.child_compatible else "Children: adult-only home",
        f"Time alone: up to {animal.max_hours_alone} hours a day",
        f"Exercise: {ACTIVITY_LEVELS[animal.exercise_needs]}",
    ]


def match_card(rank: int, result: MatchResult) -> None:
    """One ranked result with score, met and unmet requirements and any warning (criterion 7)."""
    animal = result.animal
    with st.container(border=True):
        left, right = st.columns([1, 3])
        with left:
            _image(animal)
        with right:
            colour = CATEGORY_COLOURS[result.category]
            st.markdown(f"#### {rank}. {animal.name} — {result.compatibility:.0f}% :{colour}-badge[{result.category}]")
            st.caption(f"{animal.species} · {animal.breed} · {animal.age} yr · {animal.size}")
            st.progress(result.compatibility / 100)
            for warning in result.warnings:
                st.warning(f"Important requirement not met. {warning}", icon=":material/warning:")
            with st.expander(f"{len(result.met)} requirements met, {len(result.unmet)} not met"):
                for line in result.met:
                    st.markdown(f":green[✔] {line}")
                for line in result.unmet:
                    st.markdown(f":red[✘] {line}")
            if result.bonus:
                st.caption("Matches your species or size preference, so it is shown higher.")
            if st.button("View profile", key=f"match-{animal.animal_id}"):
                open_profile(animal.animal_id, "results")


def show_errors(errors: dict[str, str]) -> None:
    """All validation messages in one box, so nothing is missed below the fold."""
    if errors:
        st.error("Please fix the following:\n" + "\n".join(f"- {m}" for m in errors.values()))
