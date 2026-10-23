"""Animal preview page (criterion 3): filters and a grid of compact cards."""

import streamlit as st

from pawmatch import services
from pawmatch.models import SIZES, SPECIES
from webui.components import animal_card
from webui.state import database

st.title("Animals looking for a home")
f1, f2, f3 = st.columns([1, 1, 2])
species = f1.selectbox("Species", SPECIES, index=None, placeholder="All species")
size = f2.selectbox("Size", SIZES, index=None, placeholder="All sizes")
search = f3.text_input("Search by name or breed", max_chars=20)

with database() as conn:
    animals = services.browse(conn, species, size, search)

if not animals:
    st.info("No animals match those filters.")
st.caption(f"Showing {len(animals)} animal(s).")
cols = st.columns(4)
for i, animal in enumerate(animals):
    with cols[i % 4]:
        animal_card(animal, came_from="browse")
