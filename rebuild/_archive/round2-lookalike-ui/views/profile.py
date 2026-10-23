"""Animal profile page (criterion 4): full details read from the database, with a way back."""

import streamlit as st

from pawmatch import db
from webui.components import requirements
from webui.state import PAGES, database, image_for

back = st.session_state.get("profile_back", "browse")
st.page_link(PAGES[back], label="Back to my matches" if back == "results" else "Back to animals",
             icon=":material/arrow_back:")

raw_id = st.query_params.get("id", "")
with database() as conn:
    animal = db.get_animal(conn, int(raw_id)) if raw_id.isdigit() else None
if animal is None:
    st.error("That animal could not be found. It may have been adopted.")
    st.stop()

left, right = st.columns([2, 3])
with left:
    path = image_for(animal.image_path)
    if path:
        st.image(path, width="stretch")
with right:
    st.title(animal.name)
    st.markdown(
        f"| | |\n|---|---|\n| Species | {animal.species} |\n| Breed | {animal.breed} |\n"
        f"| Age | {animal.age} year(s) |\n| Sex | {animal.sex} |\n| Size | {animal.size} |"
    )
    st.subheader("Personality")
    st.write(animal.personality)
    st.subheader("Medical needs")
    st.write(animal.medical_notes or "None recorded.")
    st.subheader("Needs and suitability")
    for line in requirements(animal):
        st.markdown(f"- {line}")
