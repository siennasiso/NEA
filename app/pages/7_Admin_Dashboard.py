"""PawMatch administrator dashboard for animal-record CRUD operations."""

from __future__ import annotations

import html
from datetime import datetime
from typing import Any, Sequence

import streamlit as st

from pawmatch_animals import (
    ACTIVITY_LEVELS,
    ANIMAL_STATUSES,
    CHILD_FRIENDLY_OPTIONS,
    EXPERIENCE_LEVELS,
    HOME_TYPES,
    OTHER_PETS_OPTIONS,
    SEXES,
    SIZES,
    SPECIES,
    create_animal,
    delete_animal,
    fetch_animal,
    fetch_animals,
    format_age,
    get_admin_summary,
    initialise_animals_table,
    profile_completion,
    update_animal,
    validate_animal,
)
from pawmatch_style import apply_admin_dashboard_style

st.set_page_config(
    page_title="PawMatch | Administrator",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# A normal adopter must not gain access by entering this page's URL directly.
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")
if st.session_state.get("role") != "admin":
    st.switch_page("pages/1_Home.py")

initialise_animals_table()

VALID_VIEWS = {"overview", "manage", "add"}
if st.session_state.get("admin_view") not in VALID_VIEWS:
    st.session_state.admin_view = "overview"
current_view = str(st.session_state.admin_view)
apply_admin_dashboard_style(current_view)


def change_view(view: str) -> None:
    if view in VALID_VIEWS:
        st.session_state.admin_view = view
        st.rerun()


def log_out() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("admin_") or key in {
            "logged_in", "user_id", "user_name", "user_email", "role",
            "questionnaire_progress", "questionnaire_complete", "match_count",
        }:
            st.session_state.pop(key, None)
    st.switch_page("app.py")


def option_index(options: Sequence[str], value: Any, default: int = 0) -> int:
    try:
        return list(options).index(str(value))
    except ValueError:
        return default


def clean_date(value: Any) -> str:
    text = str(value or "")
    try:
        return datetime.fromisoformat(text).strftime("%d %b %Y")
    except ValueError:
        return text[:10] or "—"


def table_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "ID": record["animal_id"],
            "Animal": record["name"],
            "Species": record["species"],
            "Breed": record["breed"],
            "Age": format_age(record["age_years"]),
            "Status": record["status"],
            "Profile": f"{profile_completion(record)}%",
            "Updated": clean_date(record["updated_at"]),
        }
        for record in records
    ]


def render_metric(icon: str, label: str, value: int, note: str, tone: str) -> None:
    st.markdown(
        f"""
        <div class="admin-metric-card {tone}">
            <div class="admin-metric-icon">{icon}</div>
            <div>
                <p>{html.escape(label)}</p>
                <strong>{value}</strong>
                <small>{html.escape(note)}</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_validation_errors(errors: dict[str, str]) -> None:
    if not errors:
        return
    items = "".join(f"<li>{html.escape(message)}</li>" for message in errors.values())
    st.markdown(
        f"<div class='admin-validation-box'><strong>Correct these details:</strong><ul>{items}</ul></div>",
        unsafe_allow_html=True,
    )


def render_animal_form(mode: str, record: dict[str, Any] | None = None) -> None:
    """Render the shared add/edit form and save validated values to SQLite."""
    animal_id = int(record["animal_id"]) if record else None
    prefix = f"admin_{mode}_{animal_id or 'new'}"
    error_key = f"{prefix}_errors"
    errors: dict[str, str] = st.session_state.get(error_key, {})

    defaults: dict[str, Any] = record or {
        "name": "",
        "species": "Dog",
        "breed": "",
        "age_years": 1.0,
        "sex": "Female",
        "size": "Medium",
        "activity_level": "Moderate",
        "home_type": "Either",
        "garden_required": False,
        "child_friendly": "Yes",
        "other_pets": "Depends",
        "experience_level": "First-time owner",
        "max_hours_alone": 4,
        "status": "Available",
        "description": "",
        "image_url": "",
    }

    title = "Add a new animal" if mode == "add" else f"Edit {record['name']}"
    subtitle = (
        "Store the public profile and the care requirements used by the compatibility algorithm."
        if mode == "add"
        else "Changes affect browsing, filtering and future compatibility calculations."
    )
    st.markdown(
        f"""
        <div class="admin-form-heading">
            <p class="admin-eyebrow">{'New database record' if mode == 'add' else f'Animal ID #{animal_id}'}</p>
            <h2>{html.escape(title)}</h2>
            <p>{html.escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_validation_errors(errors)

    with st.form(f"{prefix}_form", clear_on_submit=False, border=False):
        st.markdown("<p class='admin-form-section'>Basic profile</p>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.2, 1, 0.85], gap="medium")
        with c1:
            name = st.text_input(
                "Animal name", value=str(defaults.get("name", "")),
                placeholder="e.g. Luna", key=f"{prefix}_name",
            )
            breed = st.text_input(
                "Breed", value=str(defaults.get("breed", "")),
                placeholder="e.g. Labrador cross", key=f"{prefix}_breed",
            )
        with c2:
            species = st.selectbox(
                "Species", SPECIES,
                index=option_index(SPECIES, defaults.get("species")),
                key=f"{prefix}_species",
            )
            sex = st.selectbox(
                "Sex", SEXES,
                index=option_index(SEXES, defaults.get("sex")),
                key=f"{prefix}_sex",
            )
        with c3:
            age_years = st.number_input(
                "Age in years", min_value=0.0, max_value=40.0,
                value=float(defaults.get("age_years", 1.0)), step=0.5,
                key=f"{prefix}_age",
            )
            status = st.selectbox(
                "Adoption status", ANIMAL_STATUSES,
                index=option_index(ANIMAL_STATUSES, defaults.get("status")),
                key=f"{prefix}_status",
            )

        st.markdown("<p class='admin-form-section'>Matching requirements</p>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3, gap="medium")
        with m1:
            size = st.selectbox(
                "Animal size", SIZES,
                index=option_index(SIZES, defaults.get("size"), 1),
                key=f"{prefix}_size",
            )
            activity_level = st.selectbox(
                "Activity level", ACTIVITY_LEVELS,
                index=option_index(ACTIVITY_LEVELS, defaults.get("activity_level"), 1),
                key=f"{prefix}_activity",
            )
            max_hours_alone = st.number_input(
                "Maximum hours left alone", min_value=0, max_value=12,
                value=int(defaults.get("max_hours_alone", 4)), step=1,
                key=f"{prefix}_alone",
            )
        with m2:
            home_type = st.selectbox(
                "Suitable home type", HOME_TYPES,
                index=option_index(HOME_TYPES, defaults.get("home_type"), 2),
                key=f"{prefix}_home",
            )
            child_friendly = st.selectbox(
                "Suitable with children", CHILD_FRIENDLY_OPTIONS,
                index=option_index(CHILD_FRIENDLY_OPTIONS, defaults.get("child_friendly")),
                key=f"{prefix}_children",
            )
            other_pets = st.selectbox(
                "Suitable with other pets", OTHER_PETS_OPTIONS,
                index=option_index(OTHER_PETS_OPTIONS, defaults.get("other_pets"), 2),
                key=f"{prefix}_pets",
            )
        with m3:
            experience_level = st.selectbox(
                "Required adopter experience", EXPERIENCE_LEVELS,
                index=option_index(EXPERIENCE_LEVELS, defaults.get("experience_level")),
                key=f"{prefix}_experience",
            )
            garden_required = st.checkbox(
                "A secure garden is required",
                value=bool(defaults.get("garden_required", False)),
                key=f"{prefix}_garden",
            )
            st.markdown(
                """
                <div class="admin-algorithm-note">
                    <strong>Algorithm data</strong>
                    <span>These requirements are compared with the adopter's questionnaire answers.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<p class='admin-form-section'>Public profile</p>", unsafe_allow_html=True)
        description = st.text_area(
            "Description", value=str(defaults.get("description", "")), height=145,
            placeholder="Describe temperament, routine, care needs and the most suitable home.",
            key=f"{prefix}_description",
        )
        image_url = st.text_input(
            "Image URL (optional while designing)",
            value=str(defaults.get("image_url") or ""),
            placeholder="https://example.org/animal-photo.jpg",
            key=f"{prefix}_image",
        )
        submitted = st.form_submit_button(
            "Save animal record" if mode == "add" else "Save changes",
            type="primary", icon="💾", width="stretch",
        )

    if not submitted:
        return

    values = {
        "name": name,
        "species": species,
        "breed": breed,
        "age_years": age_years,
        "sex": sex,
        "size": size,
        "activity_level": activity_level,
        "home_type": home_type,
        "garden_required": garden_required,
        "child_friendly": child_friendly,
        "other_pets": other_pets,
        "experience_level": experience_level,
        "max_hours_alone": max_hours_alone,
        "status": status,
        "description": description,
        "image_url": image_url,
    }
    validation_errors, cleaned = validate_animal(values)
    if validation_errors:
        st.session_state[error_key] = validation_errors
        st.rerun()

    st.session_state.pop(error_key, None)
    if mode == "add":
        success, new_id, message = create_animal(cleaned)
        if success:
            st.session_state.admin_flash = f"{cleaned['name']} was added as animal record #{new_id}."
            st.session_state.admin_selected_animal_id = new_id
            st.session_state.admin_view = "manage"
            st.rerun()
    else:
        success, message = update_animal(int(animal_id), cleaned)
        if success:
            st.session_state.admin_flash = f"{cleaned['name']}'s record was updated."
            st.rerun()
    st.error(message)


# Sidebar
full_name = str(st.session_state.get("user_name", "Administrator")).strip()
first_name = full_name.split()[0] if full_name else "Administrator"
email = str(st.session_state.get("user_email", ""))

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-logo">🐾</div>
            <div>
                <p class="sidebar-brand-name">PawMatch</p>
                <p class="sidebar-brand-subtitle">Shelter administration</p>
            </div>
        </div>
        <p class="sidebar-section-label">Administrator menu</p>
        """,
        unsafe_allow_html=True,
    )
    if st.button("▦  Overview", key="admin_nav_overview", width="stretch"):
        change_view("overview")
    if st.button("🐾  Manage animals", key="admin_nav_manage", width="stretch"):
        change_view("manage")
    if st.button("＋  Add animal", key="admin_nav_add", width="stretch"):
        change_view("add")

    st.markdown(
        """
        <div class="admin-sidebar-note">
            <strong>Administrator scope</strong>
            <span>Add, view, edit and delete shelter animal records. Adopter accounts cannot access these controls.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="sidebar-user-card admin-user-card">
            <span class="sidebar-user-icon">🛡️</span>
            <div>
                <strong>{html.escape(full_name)}</strong>
                <small>{html.escape(email)}</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("←  Log out", key="admin_nav_logout", width="stretch"):
        log_out()


# Shared page heading and metrics
summary = get_admin_summary()
with st.container(key="admin_page_shell"):
    title_col, access_col = st.columns([1.55, 0.55], gap="large")
    with title_col:
        st.markdown(
            f"""
            <div class="admin-heading">
                <p class="admin-eyebrow">Shelter administration</p>
                <h1>Welcome back, {html.escape(first_name)}!</h1>
                <p>Manage the animal information used by browsing, filtering and the compatibility algorithm.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with access_col:
        st.markdown(
            """
            <div class="admin-access-card">
                <span>🛡️</span>
                <div><small>Access level</small><strong>Administrator</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("＋ Add new animal", key="admin_header_add", type="primary", width="stretch"):
            change_view("add")

    flash = st.session_state.pop("admin_flash", None)
    if flash:
        st.success(str(flash), icon="✅")

    metric_cols = st.columns(4, gap="medium")
    with metric_cols[0]:
        render_metric("🐾", "Total records", summary["total"], "All stored animals", "metric-total")
    with metric_cols[1]:
        render_metric("✓", "Available", summary["available"], "Visible to adopters", "metric-available")
    with metric_cols[2]:
        render_metric("⌛", "Reserved", summary["reserved"], "Temporarily unavailable", "metric-reserved")
    with metric_cols[3]:
        render_metric("!", "Needs attention", summary["needs_attention"], "Missing image or detail", "metric-attention")

    if current_view == "overview":
        st.markdown(
            """
            <div class="admin-section-heading">
                <div><p class="admin-eyebrow">Database overview</p><h2>Animal records at a glance</h2></div>
                <p>Review recent records and open the management area when changes are required.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        left, right = st.columns([1.7, 0.7], gap="large")
        recent = fetch_animals(limit=7)
        all_records = fetch_animals()

        with left:
            with st.container(key="admin_recent_records", border=True):
                st.markdown(
                    """
                    <div class="admin-card-heading">
                        <div><p class="admin-card-kicker">Recently updated</p><h3>Animal records</h3></div>
                        <span>Latest 7</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if recent:
                    st.dataframe(table_rows(recent), hide_index=True, width="stretch")
                else:
                    st.markdown(
                        """
                        <div class="admin-empty-state"><span>🐾</span><h4>No animal records yet</h4>
                        <p>Add the shelter's first animal to begin testing browsing and matching.</p></div>
                        """,
                        unsafe_allow_html=True,
                    )
                if st.button("Manage all animal records", key="overview_manage", width="stretch"):
                    change_view("manage")

        with right:
            with st.container(key="admin_quality_card", border=True):
                average = round(sum(profile_completion(r) for r in all_records) / len(all_records)) if all_records else 0
                st.markdown(
                    f"""
                    <p class="admin-card-kicker">Data quality</p><h3>Profile completeness</h3>
                    <div class="admin-quality-score"><strong>{average}%</strong><span>average</span></div>
                    <div class="admin-quality-track"><span style="width:{average}%"></span></div>
                    <p class="admin-quality-copy">Complete profiles give adopters clearer information and provide reliable values for matching.</p>
                    """,
                    unsafe_allow_html=True,
                )
                attention = [
                    r for r in all_records
                    if not str(r.get("image_url") or "").strip()
                    or len(str(r.get("description") or "").strip()) < 80
                ][:3]
                if attention:
                    st.markdown("<p class='admin-mini-heading'>Check these records</p>", unsafe_allow_html=True)
                    for record in attention:
                        issues = []
                        if not str(record.get("image_url") or "").strip():
                            issues.append("image")
                        if len(str(record.get("description") or "").strip()) < 80:
                            issues.append("description")
                        st.markdown(
                            f"""
                            <div class="admin-attention-row"><span>{html.escape(record['name'][0].upper())}</span>
                            <div><strong>{html.escape(record['name'])}</strong><small>Check {' and '.join(issues)}</small></div></div>
                            """,
                            unsafe_allow_html=True,
                        )
                else:
                    st.markdown("<p class='admin-all-clear'>✓ No incomplete profiles detected.</p>", unsafe_allow_html=True)
                if st.button("Add another animal", key="overview_add", width="stretch"):
                    change_view("add")

    elif current_view == "manage":
        st.markdown(
            """
            <div class="admin-section-heading">
                <div><p class="admin-eyebrow">CRUD management</p><h2>Manage animal records</h2></div>
                <p>Search the database, update a selected record or permanently delete it after confirmation.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.container(key="admin_filter_card", border=True):
            f1, f2, f3 = st.columns([1.7, 0.8, 0.8], gap="medium")
            with f1:
                search = st.text_input("Search by name or breed", placeholder="Search animal records...", key="admin_search")
            with f2:
                species_filter = st.selectbox("Species", ("All species", *SPECIES), key="admin_species_filter")
            with f3:
                status_filter = st.selectbox("Adoption status", ("All statuses", *ANIMAL_STATUSES), key="admin_status_filter")

        records = fetch_animals(search, species_filter, status_filter)
        with st.container(key="admin_manage_table", border=True):
            st.markdown(
                f"""
                <div class="admin-card-heading"><div><p class="admin-card-kicker">Search results</p>
                <h3>{len(records)} record{'s' if len(records) != 1 else ''} found</h3></div><span>Read-only table</span></div>
                """,
                unsafe_allow_html=True,
            )
            if records:
                st.dataframe(table_rows(records), hide_index=True, width="stretch")
            else:
                st.info("No animal records match the selected search and filters.")

        if records:
            ids = [int(r["animal_id"]) for r in records]
            lookup = {int(r["animal_id"]): r for r in records}
            state_id = st.session_state.get("admin_selected_animal_id")
            selected_index = ids.index(int(state_id)) if state_id in ids else 0
            selected_id = st.selectbox(
                "Select a record to edit", ids, index=selected_index,
                format_func=lambda i: f"#{i} — {lookup[i]['name']} ({lookup[i]['species']}, {lookup[i]['status']})",
                key="admin_record_selector",
            )
            st.session_state.admin_selected_animal_id = int(selected_id)
            selected = fetch_animal(int(selected_id))
            if selected:
                edit_tab, delete_tab = st.tabs(["Edit selected record", "Delete selected record"])
                with edit_tab:
                    with st.container(key="admin_edit_card", border=True):
                        render_animal_form("edit", selected)
                with delete_tab:
                    with st.container(key="admin_delete_card", border=True):
                        st.markdown(
                            f"""
                            <div class="admin-danger-heading"><span>!</span><div><p>Permanent database action</p>
                            <h3>Delete {html.escape(selected['name'])}?</h3></div></div>
                            <p class="admin-danger-copy">Record #{selected_id} will be removed from browsing and future recommendations. This cannot be undone.</p>
                            """,
                            unsafe_allow_html=True,
                        )
                        confirm = st.checkbox(
                            f"I understand that {selected['name']}'s record will be permanently deleted.",
                            key=f"confirm_delete_{selected_id}",
                        )
                        if st.button(
                            "Delete animal record", key=f"delete_{selected_id}",
                            type="primary", disabled=not confirm, width="stretch",
                        ):
                            success, message = delete_animal(int(selected_id))
                            if success:
                                st.session_state.pop("admin_selected_animal_id", None)
                                st.session_state.admin_flash = f"{selected['name']}'s record was deleted."
                                st.rerun()
                            st.error(message)

    elif current_view == "add":
        with st.container(key="admin_add_card", border=True):
            render_animal_form("add")
