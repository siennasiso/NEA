"""PawMatch entry point: prepares the database, then runs the page asked for.

The pages and their order are the original app's (app.py, then pages/1_ to 7_). Each page
draws its own menu and checks who may see it (webui/state.py), as in the original, so
Streamlit's own page list is hidden.
"""

import streamlit as st

from pawmatch.seed import prepare
from webui.state import DB_PATH, PAGES

st.set_page_config(page_title="PawMatch", page_icon="🐾", layout="wide")


@st.cache_resource
def _prepare_once(path: str) -> None:
    prepare(path)


_prepare_once(str(DB_PATH))

TITLES = {
    "login": "Log in", "home": "Home", "registration": "Create an account", "questionnaire": "Questionnaire",
    "browse": "Browse animals", "account": "My account", "matches": "My matches", "admin": "Administrator",
}
pages = [st.Page(PAGES[name], title=title, default=name == "login") for name, title in TITLES.items()]
st.navigation(pages, position="hidden").run()
