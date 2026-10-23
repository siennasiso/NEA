"""PawMatch administrator dashboard for animal-record CRUD operations (the original pages/7_Admin_Dashboard.py).

Her sidebar, heading, metric cards, overview, manage and add views are unchanged. Every
change goes through pawmatch.services, which checks the staff role again and validates the
record, so the page guard is not the only protection. Photos are uploaded (PNG or JPG, 2 MB)
and stored beside the database in uploads/.
"""

from __future__ import annotations

import html
import uuid
from datetime import datetime
from typing import Any, Sequence

import streamlit as st

from pawmatch import db, services
from pawmatch.models import ACTIVITY_LEVELS, HOUSING_LEVELS, SEXES, SIZES, SPECIES, STATUSES, Animal
from pawmatch.validation import IMAGE_TYPES, validate_image
from webui.animals import format_age
from webui.pawmatch_style import apply_admin_dashboard_style
from webui.state import data_dir, database, require_staff, sign_out

st.set_page_config(
    page_title="PawMatch | Administrator",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# A normal adopter must not gain access by entering this page's URL directly.
staff = require_staff()

VALID_VIEWS = {"overview", "manage", "add"}
ISSUE_TEXT = {"photo": "Add a photo", "description": "Write a longer description"}
if st.session_state.get("admin_view") not in VALID_VIEWS:
    st.session_state.admin_view = "overview"
current_view = str(st.session_state.admin_view)
apply_admin_dashboard_style(current_view)


def change_view(view: str) -> None:
    if view in VALID_VIEWS:
        st.session_state.admin_view = view
        st.rerun()


def option_index(options: Sequence[Any], value: Any, default: int = 0) -> int:
    try:
        return list(options).index(value)
    except ValueError:
        return default


def clean_date(value: Any) -> str:
    text = str(value or "")
    try:
        return datetime.fromisoformat(text).strftime("%d %b %Y")
    except ValueError:
        return text[:10] or "—"


def table_rows(records: list[Animal]) -> list[dict[str, Any]]:
    return [
        {
            "ID": record.animal_id,
            "Animal": record.name,
            "Species": record.species,
            "Breed": record.breed,
            "Age": format_age(record.age),
            "Status": record.status,
            "Profile": f"{services.profile_completion(record)}%",
            "Added": clean_date(record.date_added),
        }
        for record in records
    ]


def render_metric(icon: str, label: str, value: int, note: str, tone: str) -> None:
    st.html(
        f"""
        <div class="admin-metric-card {tone}">
            <div class="admin-metric-icon" aria-hidden="true">{icon}</div>
            <div>
                <p>{html.escape(label)}</p>
                <strong>{value}</strong>
                <small>{html.escape(note)}</small>
            </div>
        </div>
        """
    )


def render_validation_errors(errors: dict[str, str]) -> None:
    if not errors:
        return
    items = "".join(f"<li>{html.escape(message)}</li>" for message in errors.values())
    st.html(f"<div class='admin-validation-box' role='alert'><strong>Correct these details:</strong><ul>{items}</ul></div>")


def save_photo(upload: Any) -> tuple[str | None, str | None]:
    """Check an uploaded photo; returns (path to store, error). The file is written only after the record saves."""
    if upload is None:
        return None, None
    error = validate_image(upload.name, upload.size)
    if error:
        return None, error
    return f"uploads/{uuid.uuid4().hex}.{upload.name.rsplit('.', 1)[-1].lower()}", None


def write_photo(path: str, upload: Any) -> None:
    folder = data_dir() / "uploads"
    folder.mkdir(parents=True, exist_ok=True)
    (data_dir() / path).write_bytes(upload.getvalue())


def render_animal_form(mode: str, record: Animal | None = None) -> None:
    """Render the shared add/edit form and save validated values through pawmatch.services."""
    animal_id = record.animal_id if record else None
    prefix = f"admin_{mode}_{animal_id or 'new'}"
    error_key = f"{prefix}_errors"
    errors: dict[str, str] = st.session_state.get(error_key, {})

    defaults: dict[str, Any] = vars(record) if record else {
        "name": "",
        "species": "Dog",
        "breed": "",
        "age": 1,
        "sex": "Female",
        "size": "Medium",
        "exercise_needs": 2,
        "min_housing_level": 2,
        "garden_required": False,
        "child_compatible": True,
        "max_hours_alone": 4,
        "status": "Available",
        "personality": "",
        "medical_notes": "",
        "image_path": "",
    }

    title = "Add a new animal" if mode == "add" else f"Edit {record.name}"
    subtitle = (
        "Store the public profile and the care requirements used by the compatibility algorithm."
        if mode == "add"
        else "Changes affect browsing, filtering and future compatibility calculations."
    )
    st.html(
        f"""
        <div class="admin-form-heading">
            <p class="admin-eyebrow">{'New database record' if mode == 'add' else f'Animal ID #{animal_id}'}</p>
            <h2>{html.escape(title)}</h2>
            <p>{html.escape(subtitle)}</p>
        </div>
        """
    )
    render_validation_errors(errors)

    with st.form(f"{prefix}_form", clear_on_submit=False, border=False):
        st.html("<p class='admin-form-section'>Basic profile</p>")
        c1, c2, c3 = st.columns([1.2, 1, 0.85], gap="medium")
        with c1:
            name = st.text_input(
                "Animal name", value=str(defaults["name"]), max_chars=30,
                placeholder="e.g. Luna", key=f"{prefix}_name",
            )
            breed = st.text_input(
                "Breed", value=str(defaults["breed"]), max_chars=40,
                placeholder="e.g. Labrador cross", key=f"{prefix}_breed",
            )
        with c2:
            species = st.selectbox(
                "Species", SPECIES,
                index=option_index(SPECIES, defaults["species"]),
                key=f"{prefix}_species",
            )
            sex = st.selectbox(
                "Sex", SEXES,
                index=option_index(SEXES, defaults["sex"]),
                key=f"{prefix}_sex",
            )
        with c3:
            age = st.number_input(
                "Age in years", min_value=1, max_value=30,
                value=int(defaults["age"]), step=1,
                key=f"{prefix}_age",
            )
            status = st.selectbox(
                "Adoption status", STATUSES,
                index=option_index(STATUSES, defaults["status"]),
                key=f"{prefix}_status",
                help="Only Available animals are shown to adopters and scored.",
            )

        st.html("<p class='admin-form-section'>Matching requirements</p>")
        m1, m2, m3 = st.columns(3, gap="medium")
        with m1:
            size = st.selectbox(
                "Animal size", SIZES,
                index=option_index(SIZES, defaults["size"], 1),
                key=f"{prefix}_size",
            )
            exercise_needs = st.selectbox(
                "Activity level", tuple(ACTIVITY_LEVELS),
                index=option_index(tuple(ACTIVITY_LEVELS), defaults["exercise_needs"], 1),
                format_func=ACTIVITY_LEVELS.get,
                key=f"{prefix}_activity",
            )
        with m2:
            min_housing_level = st.selectbox(
                "Indoor space needed", tuple(HOUSING_LEVELS),
                index=option_index(tuple(HOUSING_LEVELS), defaults["min_housing_level"], 1),
                format_func=HOUSING_LEVELS.get,
                key=f"{prefix}_home",
            )
            child_compatible = st.selectbox(
                "Suitable with children", (True, False),
                index=0 if defaults["child_compatible"] else 1,
                format_func=lambda value: "Yes" if value else "No",
                key=f"{prefix}_children",
            )
        with m3:
            max_hours_alone = st.number_input(
                "Maximum hours left alone", min_value=0, max_value=24,
                value=int(defaults["max_hours_alone"]), step=1,
                key=f"{prefix}_alone",
            )
            garden_required = st.checkbox(
                "A secure garden is required",
                value=bool(defaults["garden_required"]),
                key=f"{prefix}_garden",
            )
        st.html(
            """
            <div class="admin-algorithm-note">
                <strong>Algorithm data</strong>
                <span>These requirements are compared with the adopter's questionnaire answers.</span>
            </div>
            """
        )

        st.html("<p class='admin-form-section'>Public profile</p>")
        personality = st.text_area(
            "Description", value=str(defaults["personality"]), height=145, max_chars=500,
            placeholder="Describe temperament, routine, care needs and the most suitable home.",
            key=f"{prefix}_description",
        )
        medical_notes = st.text_input(
            "Health and care notes (optional)", value=str(defaults["medical_notes"]), max_chars=500,
            placeholder="e.g. Thyroid tablet daily", key=f"{prefix}_medical",
        )
        upload = st.file_uploader(
            "Photo (PNG or JPG, up to 2 MB)" + (" — leave empty to keep the current photo" if record else ""),
            type=list(IMAGE_TYPES), key=f"{prefix}_image",
        )
        submitted = st.form_submit_button(
            "Save animal record" if mode == "add" else "Save changes",
            type="primary", icon="💾", width="stretch",
        )

    if not submitted:
        return

    photo_path, photo_error = save_photo(upload)
    values = {
        "name": name,
        "species": species,
        "breed": breed,
        "age": age,
        "sex": sex,
        "size": size,
        "exercise_needs": exercise_needs,
        "min_housing_level": min_housing_level,
        "garden_required": garden_required,
        "child_compatible": child_compatible,
        "max_hours_alone": max_hours_alone,
        "status": status,
        "personality": personality,
        "medical_notes": medical_notes,
        "image_path": photo_path or str(defaults["image_path"]),
    }
    with database() as conn:
        if photo_error:
            validation_errors = {"image": photo_error}
        elif mode == "add":
            new_id, validation_errors = services.add_animal(conn, staff, values)
        else:
            validation_errors = services.edit_animal(conn, staff, int(animal_id), values)
    if validation_errors:
        st.session_state[error_key] = validation_errors
        st.rerun()

    if photo_path:
        write_photo(photo_path, upload)
    st.session_state.pop(error_key, None)
    if mode == "add":
        st.session_state.admin_flash = f"{name.strip()} was added as animal record #{new_id}."
        st.session_state.admin_selected_animal_id = new_id
        st.session_state.admin_view = "manage"
    else:
        st.session_state.admin_flash = f"{name.strip()}'s record was updated."
    st.rerun()


# Sidebar
full_name = staff.name.strip()
first_name = full_name.split()[0] if full_name else "Administrator"

with st.sidebar:
    st.html(
        """
        <div class="sidebar-brand">
            <div class="sidebar-logo" aria-hidden="true">🐾</div>
            <div>
                <p class="sidebar-brand-name">PawMatch</p>
                <p class="sidebar-brand-subtitle">Shelter administration</p>
            </div>
        </div>
        <p class="sidebar-section-label">Administrator menu</p>
        """
    )
    if st.button("▦  Overview", key="admin_nav_overview", width="stretch"):
        change_view("overview")
    if st.button("🐾  Manage animals", key="admin_nav_manage", width="stretch"):
        change_view("manage")
    if st.button("＋  Add animal", key="admin_nav_add", width="stretch"):
        change_view("add")

    st.html(
        """
        <div class="admin-sidebar-note">
            <strong>Administrator scope</strong>
            <span>Add, view, edit and delete shelter animal records. Adopter accounts cannot access these controls.</span>
        </div>
        """
    )
    st.html(
        f"""
        <div class="sidebar-user-card admin-user-card">
            <span class="sidebar-user-icon" aria-hidden="true">🛡️</span>
            <div>
                <strong>{html.escape(full_name)}</strong>
                <small>{html.escape(staff.email)}</small>
            </div>
        </div>
        """
    )
    if st.button("←  Log out", key="admin_nav_logout", width="stretch"):
        sign_out()


# Shared page heading and metrics
with database() as conn:
    summary = services.dashboard(conn, staff)
    all_records = services.staff_animals(conn, staff)
needs_attention = [record for record in all_records if services.profile_issues(record)]

with st.container(key="admin_page_shell"):
    title_col, access_col = st.columns([1.55, 0.55], gap="large")
    with title_col:
        st.html(
            f"""
            <div class="admin-heading">
                <p class="admin-eyebrow">Shelter administration</p>
                <h1>Welcome back, {html.escape(first_name)}!</h1>
                <p>Manage the animal information used by browsing, filtering and the compatibility algorithm.</p>
            </div>
            """
        )
    with access_col:
        st.html(
            """
            <div class="admin-access-card">
                <span aria-hidden="true">🛡️</span>
                <div><small>Access level</small><strong>Administrator</strong></div>
            </div>
            """
        )
        if st.button("＋ Add new animal", key="admin_header_add", type="primary", width="stretch"):
            change_view("add")

    flash = st.session_state.pop("admin_flash", None)
    if flash:
        st.success(str(flash), icon="✅")

    metric_cols = st.columns(4, gap="medium")
    with metric_cols[0]:
        render_metric("🐾", "Total records", summary.animals, "All stored animals", "metric-total")
    with metric_cols[1]:
        render_metric("✓", "Available", summary.by_status.get("Available", 0), "Visible to adopters", "metric-available")
    with metric_cols[2]:
        render_metric("⌛", "Reserved", summary.by_status.get("Reserved", 0), "Temporarily unavailable", "metric-reserved")
    with metric_cols[3]:
        render_metric("!", "Needs attention", len(needs_attention), "Missing photo or detail", "metric-attention")

    if current_view == "overview":
        st.html(
            """
            <div class="admin-section-heading">
                <div><p class="admin-eyebrow">Database overview</p><h2>Animal records at a glance</h2></div>
                <p>Review recent records and open the management area when changes are required.</p>
            </div>
            """
        )
        left, right = st.columns([1.7, 0.7], gap="large")
        recent = sorted(all_records, key=lambda r: (r.date_added, r.animal_id), reverse=True)[:7]

        with left:
            with st.container(key="admin_recent_records", border=True):
                st.html(
                    f"""
                    <div class="admin-card-heading">
                        <div><p class="admin-card-kicker">Recently added</p><h3>Animal records</h3></div>
                        <span>Latest {len(recent)}</span>
                    </div>
                    """
                )
                if recent:
                    st.dataframe(table_rows(recent), hide_index=True, width="stretch")
                else:
                    st.html(
                        """
                        <div class="admin-empty-state"><span aria-hidden="true">🐾</span><h4>No animal records yet</h4>
                        <p>Add the shelter's first animal to begin testing browsing and matching.</p></div>
                        """
                    )
                if st.button("Manage all animal records", key="overview_manage", width="stretch"):
                    change_view("manage")

        with right:
            with st.container(key="admin_quality_card", border=True):
                average = round(sum(services.profile_completion(r) for r in all_records) / len(all_records)) if all_records else 0
                st.html(
                    f"""
                    <p class="admin-card-kicker">Data quality</p><h3>Profile completeness</h3>
                    <div class="admin-quality-score"><strong>{average}%</strong><span>average</span></div>
                    <div class="admin-quality-track"><span style="width:{average}%"></span></div>
                    <p class="admin-quality-copy">Complete profiles give adopters clearer information and provide reliable values for matching.</p>
                    """
                )
                if needs_attention:
                    st.html("<p class='admin-mini-heading'>Check these records</p>")
                    for record in needs_attention[:3]:
                        st.html(
                            f"""
                            <div class="admin-attention-row"><span>{html.escape(record.name[0].upper())}</span>
                            <div><strong>{html.escape(record.name)}</strong><small>{' · '.join(ISSUE_TEXT[issue] for issue in services.profile_issues(record))}</small></div></div>
                            """
                        )
                else:
                    st.html("<p class='admin-all-clear'>✓ No incomplete profiles detected.</p>")
                if st.button("Add another animal", key="overview_add", width="stretch"):
                    change_view("add")

    elif current_view == "manage":
        st.html(
            """
            <div class="admin-section-heading">
                <div><p class="admin-eyebrow">CRUD management</p><h2>Manage animal records</h2></div>
                <p>Search the database, update a selected record or permanently delete it after confirmation.</p>
            </div>
            """
        )
        with st.container(key="admin_filter_card", border=True):
            f1, f2, f3 = st.columns([1.7, 0.8, 0.8], gap="medium")
            with f1:
                search = st.text_input("Search by name or breed", placeholder="Search animal records...",
                                       key="admin_search", max_chars=40)
            with f2:
                species_filter = st.selectbox("Species", ("All species", *SPECIES), key="admin_species_filter")
            with f3:
                status_filter = st.selectbox("Adoption status", ("All statuses", *STATUSES), key="admin_status_filter")

        with database() as conn:
            records = services.staff_animals(
                conn, staff,
                species=None if species_filter == "All species" else species_filter,
                status=None if status_filter == "All statuses" else status_filter,
                search=search,
            )
        with st.container(key="admin_manage_table", border=True):
            st.html(
                f"""
                <div class="admin-card-heading"><div><p class="admin-card-kicker">Search results</p>
                <h3>{len(records)} record{'s' if len(records) != 1 else ''} found</h3></div><span>Read-only table</span></div>
                """
            )
            if records:
                st.dataframe(table_rows(records), hide_index=True, width="stretch")
            else:
                st.info("No animal records match the selected search and filters.")

        if records:
            ids = [r.animal_id for r in records]
            lookup = {r.animal_id: r for r in records}
            state_id = st.session_state.get("admin_selected_animal_id")
            selected_index = ids.index(state_id) if state_id in ids else 0
            selected_id = st.selectbox(
                "Select a record to edit", ids, index=selected_index,
                format_func=lambda i: f"#{i} — {lookup[i].name} ({lookup[i].species}, {lookup[i].status})",
                key="admin_record_selector",
            )
            st.session_state.admin_selected_animal_id = int(selected_id)
            with database() as conn:
                selected = db.get_animal(conn, int(selected_id))
            if selected:
                edit_tab, delete_tab = st.tabs(["Edit selected record", "Delete selected record"])
                with edit_tab:
                    with st.container(key="admin_edit_card", border=True):
                        render_animal_form("edit", selected)
                with delete_tab:
                    with st.container(key="admin_delete_card", border=True):
                        st.html(
                            f"""
                            <div class="admin-danger-heading"><span aria-hidden="true">!</span><div><p>Permanent database action</p>
                            <h3>Delete {html.escape(selected.name)}?</h3></div></div>
                            <p class="admin-danger-copy">Record #{selected_id} will be removed from browsing and future recommendations. This cannot be undone.</p>
                            """
                        )
                        confirm = st.checkbox(
                            f"I understand that {selected.name}'s record will be permanently deleted.",
                            key=f"confirm_delete_{selected_id}",
                        )
                        if st.button(
                            "Delete animal record", key=f"delete_{selected_id}",
                            type="primary", disabled=not confirm, width="stretch",
                        ):
                            with database() as conn:
                                deleted = services.remove_animal(conn, staff, int(selected_id))
                            if deleted:
                                st.session_state.pop("admin_selected_animal_id", None)
                                st.session_state.admin_flash = f"{selected.name}'s record was deleted."
                                st.rerun()
                            st.error("That record no longer exists. It may already have been deleted.")

    elif current_view == "add":
        with st.container(key="admin_add_card", border=True):
            render_animal_form("add")
