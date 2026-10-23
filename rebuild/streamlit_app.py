"""PawMatch entry point: prepares the database, builds role-aware navigation and runs the page."""

import streamlit as st

from pawmatch.seed import prepare
from webui.state import DB_PATH, PAGES, current_user

st.set_page_config(page_title="PawMatch", page_icon="🐾", layout="wide")


@st.cache_resource
def _prepare_once(path: str) -> None:
    prepare(path)


_prepare_once(str(DB_PATH))
user = current_user()

pages = [
    st.Page(PAGES["home"], title="Home", icon=":material/home:", default=True),
    st.Page(PAGES["browse"], title="Animals", icon=":material/pets:"),
    st.Page(PAGES["profile"], title="Animal profile", visibility="hidden"),
    st.Page(PAGES["questionnaire"], title="Questionnaire", icon=":material/checklist:"),
    st.Page(PAGES["results"], title="My matches", icon=":material/favorite:"),
    st.Page(PAGES["account"], title="My account" if user else "Log in", icon=":material/person:"),
]
if user and user.is_admin:  # staff page is not even routable for anyone else
    pages.append(st.Page(PAGES["admin"], title="Manage animals", icon=":material/admin_panel_settings:"))

st.navigation(pages, position="top").run()
