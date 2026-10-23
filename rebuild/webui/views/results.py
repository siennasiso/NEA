"""Ranked results (criterion 7): at least the top four, with met/unmet requirements and warnings."""

import streamlit as st

from pawmatch import services
from pawmatch.matching import MIN_RESULTS_SHOWN
from webui.components import match_card
from webui.state import PAGES, database, require_login

user = require_login()
st.title("My matches")
st.info(
    "These scores are guidance to help you think about suitability. "
    "Shelter staff always make the final adoption decision.",
    icon=":material/info:",
)

with database() as conn:
    results = services.latest_results(conn, user)
if results is None:
    st.write("You haven't completed the questionnaire yet.")
    st.page_link(PAGES["questionnaire"], label="Start the questionnaire", icon=":material/checklist:")
    st.stop()

show_all = st.toggle("Show every animal", value=False)
shown = results if show_all else results[: max(MIN_RESULTS_SHOWN, 5)]
st.caption(f"Showing {len(shown)} of {len(results)} animals, best match first.")
for rank, result in enumerate(shown, start=1):
    match_card(rank, result)
st.page_link(PAGES["questionnaire"], label="Retake the questionnaire", icon=":material/refresh:")
