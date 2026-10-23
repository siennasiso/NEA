"""Staff area (criterion 8): list, add, edit and delete animal records."""

import uuid

import streamlit as st

from pawmatch import services
from pawmatch.models import ACTIVITY_LEVELS, HOUSING_LEVELS, SEXES, SIZES, SPECIES, Animal
from pawmatch.validation import IMAGE_TYPES, validate_image
from webui.components import show_errors
from webui.state import ROOT, database, require_staff

staff = require_staff()
st.title("Manage animals")
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))
YES_NO = ("Yes", "No")


def _pick(options: tuple, value, **kwargs):
    return dict(options=options, index=options.index(value) if value in options else None,
                placeholder="Choose", **kwargs)


def animal_form(form_key: str, animal: Animal | None) -> tuple[dict, object, bool]:
    """Draw the add/edit form; returns the raw values, the upload and whether it was submitted."""
    a = animal
    with st.form(form_key, clear_on_submit=animal is None):
        c1, c2, c3 = st.columns(3)
        raw = {
            "name": c1.text_input("Name", a.name if a else "", max_chars=50),
            "species": c2.selectbox("Species", **_pick(SPECIES, a and a.species)),
            "breed": c3.text_input("Breed", a.breed if a else "", max_chars=50),
            "age": c1.number_input("Age (years)", 1, 30, a.age if a else None, step=1),
            "sex": c2.selectbox("Sex", **_pick(SEXES, a and a.sex)),
            "size": c3.selectbox("Size", **_pick(SIZES, a and a.size)),
            "exercise_needs": c1.selectbox("Exercise needs", **_pick(tuple(ACTIVITY_LEVELS), a and a.exercise_needs),
                                           format_func=ACTIVITY_LEVELS.get),
            "min_housing_level": c2.selectbox("Minimum home", **_pick(tuple(HOUSING_LEVELS), a and a.min_housing_level),
                                              format_func=HOUSING_LEVELS.get),
            "max_hours_alone": c3.number_input("Max hours alone", 0, 24, a.max_hours_alone if a else None, step=1),
            "garden_required": c1.selectbox("Garden required?", **_pick(YES_NO, a and ("Yes" if a.garden_required else "No"))),
            "child_compatible": c2.selectbox("Good with children?", **_pick(YES_NO, a and ("Yes" if a.child_compatible else "No"))),
            "personality": st.text_area("Personality", a.personality if a else "", max_chars=500),
            "medical_notes": st.text_area("Medical notes (optional)", a.medical_notes if a else "", max_chars=500),
            "image_path": a.image_path if a else "",
        }
        upload = st.file_uploader("Photo (PNG or JPG, up to 2 MB)", type=list(IMAGE_TYPES))
        submitted = st.form_submit_button("Save animal", type="primary")
    return raw, upload, submitted


def attach_upload(raw: dict, upload) -> str | None:
    """Store an uploaded photo under data/uploads and point the record at it."""
    if upload is None:
        return None
    error = validate_image(upload.name, upload.size)
    if error:
        return error
    folder = ROOT / "data" / "uploads"
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}.{upload.name.rsplit('.', 1)[-1].lower()}"
    (folder / name).write_bytes(upload.getvalue())
    raw["image_path"] = f"data/uploads/{name}"
    return None


with database() as conn:
    animals = services.browse(conn, None, None, "")

list_tab, add_tab, edit_tab = st.tabs(["All animals", "Add animal", "Edit or delete"])

with list_tab:
    st.dataframe(
        [{"ID": a.animal_id, "Name": a.name, "Species": a.species, "Breed": a.breed, "Age": a.age,
          "Size": a.size, "Garden": "Yes" if a.garden_required else "No",
          "Children": "Yes" if a.child_compatible else "No", "Max hours alone": a.max_hours_alone}
         for a in animals],
        hide_index=True, width="stretch",
    )

with add_tab:
    raw, upload, submitted = animal_form("add", None)
    if submitted:
        upload_error = attach_upload(raw, upload)
        with database() as conn:
            new_id, errors = (None, {"image": upload_error}) if upload_error else services.add_animal(conn, staff, raw)
        show_errors(errors)
        if new_id:
            st.success(f"{raw['name'].strip()} was added.")

with edit_tab:
    chosen = st.selectbox("Animal", animals, format_func=lambda a: f"{a.name} ({a.species}, #{a.animal_id})",
                          index=None, placeholder="Choose an animal to edit")
    if chosen:
        raw, upload, submitted = animal_form(f"edit-{chosen.animal_id}", chosen)
        if submitted:
            upload_error = attach_upload(raw, upload)
            with database() as conn:
                errors = {"image": upload_error} if upload_error else services.edit_animal(conn, staff, chosen.animal_id, raw)
            show_errors(errors)
            if not errors:
                st.success("Changes saved.")
        st.divider()
        confirm = st.checkbox(f"Yes, remove {chosen.name} (adopted or no longer available)")
        if st.button("Delete animal", type="secondary", disabled=not confirm, icon=":material/delete:"):
            with database() as conn:
                services.remove_animal(conn, staff, chosen.animal_id)
            st.session_state["flash"] = f"{chosen.name} was removed."
            st.rerun()
