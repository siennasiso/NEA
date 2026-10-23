"""Reusable display pieces: the menus, animal cards, match cards and form errors."""

from __future__ import annotations

import streamlit as st

from pawmatch.models import ACTIVITY_LEVELS, HOUSING_LEVELS, Animal, MatchResult, User

from . import html
from .state import PAGES, picture, sign_out

# The adopter menu, in the original app's order; Log out sits at the bottom.
ADOPTER_MENU = (
    ("home", "Home", ":material/home:"),
    ("browse", "Browse animals", ":material/pets:"),
    ("questionnaire", "Questionnaire", ":material/checklist:"),
    ("account", "My account", ":material/person:"),
)
ACTIVITY_HINTS = {1: "short, gentle daily activity", 2: "regular walks or active play",
                  3: "long exercise and enrichment"}
STAFF_VIEWS = (
    ("overview", "Overview", ":material/dashboard:"),
    ("manage", "Manage animals", ":material/edit_note:"),
    ("add", "Add animal", ":material/add_circle:"),
)


def adopter_menu(user: User, active: str) -> None:
    """The left-hand menu on every adopter page (the original drew it as a column; this is the sidebar)."""
    with st.sidebar:
        st.html(html.brand("Adoption matching"))
        with st.container(key="menu-adopter"):
            for page, text, icon in ADOPTER_MENU:
                with st.container(key=f"nav-{page}{'-active' if page == active else ''}"):
                    st.page_link(PAGES[page], label=text, icon=icon, width="stretch")
        with st.container(key="menu-foot"):
            st.html(html.person(user.name, "Adopter account"))
            if st.button("Log out", key="logout", icon=":material/logout:", width="stretch"):
                sign_out()


def _show_view(view: str) -> None:
    st.session_state["admin_view"] = view


def staff_menu(user: User, view: str) -> None:
    """The administrator menu: three views of the one dashboard page, as in the original."""
    with st.sidebar, st.container(key="menu-staff"):
        st.html(html.brand("Shelter administration") + html.label("Administrator menu"))
        for key, text, icon in STAFF_VIEWS:
            st.button(text, key=f"view-{key}", icon=icon, type="primary" if key == view else "secondary",
                      width="stretch", on_click=_show_view, args=(key,))
        st.html(html.note("Add, view, edit and delete the shelter's animal records. "
                          "Adopter accounts cannot open this page.", "scope", "Staff scope"))
        with st.container(key="menu-foot"):
            st.html(html.person(user.name, "Shelter staff"))
            if st.button("Log out", key="logout", icon=":material/logout:", width="stretch"):
                sign_out()


def action_tile(page: str, emoji: str, title: str, body: str, cta: str) -> None:
    """One of the home page's MAIN ACTIONS: a pastel card whose button opens the page."""
    with st.container(key=f"action-{page}"):
        st.html(html.action_card(emoji, title, body))
        st.page_link(PAGES[page], label=cta, width="stretch")


def back_link(page: str, text: str) -> None:
    with st.container(key=f"back-{page}"):
        st.page_link(PAGES[page], label=text, icon=":material/arrow_back:")


def years(age: int) -> str:
    return f"{age} year{'' if age == 1 else 's'} old"


def species_line(animal: Animal) -> str:
    return f"{animal.species} · {animal.breed}"


def details(animal: Animal) -> str:
    return f"{years(animal.age)} · {animal.sex} · {animal.size}"


def open_profile(animal_id: int, came_from: str) -> None:
    """The profile is part of Browse animals (?animal=<id>), as in the original."""
    st.session_state["profile_back"] = came_from
    st.switch_page(PAGES["browse"], query_params={"animal": str(animal_id)})


def animal_card(animal: Animal) -> None:
    """Browse card (criterion 3.2): picture, name, species and breed, age, sex, size and description."""
    with st.container(key=f"card-animal-{animal.animal_id}"):
        st.image(picture(animal), width="stretch")
        st.html(html.animal_blurb(animal.name, species_line(animal), details(animal), animal.personality))
        if st.button("View profile", key=f"view-{animal.animal_id}", type="primary", width="stretch"):
            open_profile(animal.animal_id, "browse")


def animal_grid(animals: list[Animal]) -> None:
    """Cards in rows of three on a computer and two on a tablet (CSS: .st-key-animal-grid)."""
    with st.container(key="animal-grid", horizontal=True, gap="medium"):
        for animal in animals:
            animal_card(animal)


def needs(animal: Animal) -> list[tuple[str, str, str]]:
    """What the animal needs from a home, as icon, label and value rows (criterion 4)."""
    return [
        ("🎾", "Activity", f"{ACTIVITY_LEVELS[animal.exercise_needs]}: {ACTIVITY_HINTS[animal.exercise_needs]}"),
        ("🏡", "Indoor space", f"At least {HOUSING_LEVELS[animal.min_housing_level].lower()}"
         if animal.min_housing_level > 1 else "Any home, including limited space"),
        ("🌳", "Garden", "Needs a secure garden" if animal.garden_required else "Not needed"),
        ("👶", "Children", "Good with children" if animal.child_compatible else "Adult-only home"),
        ("⏰", "Maximum time alone", f"Up to {animal.max_hours_alone} hours a day"),
    ]


def match_card(rank: int, result: MatchResult) -> None:
    """One ranked result (criterion 7): picture, what is met and not met, the band and score."""
    animal = result.animal
    with st.container(key=f"card-match-{animal.animal_id}"):
        pic, body, side = st.columns([1.05, 2.7, 1.15], gap="medium", vertical_alignment="center")
        pic.image(picture(animal, 360), width="stretch")
        line = f"{species_line(animal)} · {years(animal.age)}"
        bonus = html.chips(html.chip("💗 Matches your preferred species or size", "soft")) if result.bonus else ""
        body.html(html.match_heading(rank, animal.name, line)
                  + html.requirements(result.met, result.unmet, result.warnings) + bonus)
        with side:
            st.html(html.score(result.compatibility, result.category))
            if st.button("View animal profile", key=f"match-{animal.animal_id}", type="primary", width="stretch"):
                open_profile(animal.animal_id, "matches")


def field_errors(errors: dict[str, str], *fields: str) -> None:
    """Messages for these fields, directly under them (as in the original forms)."""
    for name in fields:
        if name in errors:
            st.html(html.field_error(errors[name]))


def show_errors(errors: dict[str, str]) -> None:
    """All validation messages in one box, for the longer staff forms."""
    if errors:
        st.error("Please fix the following:\n" + "\n".join(f"- {m}" for m in errors.values()))
