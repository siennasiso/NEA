"""Home page (criterion 2): purpose, suitability focus and a route to the questionnaire."""

import streamlit as st

from pawmatch import services
from webui.state import PAGES, current_user, database

st.title("🐾 PawMatch")
st.subheader("Find the animal whose needs fit your life")
st.write(
    "PawMatch helps you think about **suitability**, not just appearance. You answer a short "
    "questionnaire about your home and routine, and we compare it with what each animal needs: "
    "space, a garden, time alone, exercise and whether they can live with children."
)
st.info("Scores are guidance only. Shelter staff always make the final adoption decision.", icon=":material/info:")

if st.button("Start the questionnaire", type="primary", icon=":material/arrow_forward:"):
    st.switch_page(PAGES["questionnaire"])

with database() as conn:
    animals = services.browse(conn, None, None, "")
st.divider()
cols = st.columns(3)
for col, species in zip(cols, ("Dog", "Cat", "Rabbit")):
    col.metric(f"{species}s looking for a home", sum(a.species == species for a in animals))

st.markdown(
    "**How it works**\n"
    "1. Register or log in.\n"
    "2. Answer four short steps about your home and lifestyle.\n"
    "3. See your matches ranked, with what you meet and what you don't."
)
if current_user() is None:
    st.page_link(PAGES["account"], label="Log in or register", icon=":material/login:")
