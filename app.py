"""PawMatch authentication entrypoint for the development branch.

Run the connected login and registration interface with:

    streamlit run app.py

Only the two authentication pages are registered here. The animal,
questionnaire and matching pages remain outside this development stage.
"""

import streamlit as st


# Page configuration belongs in the entrypoint so it applies consistently to
# both the login and registration pages.
st.set_page_config(
    page_title="PawMatch | Authentication",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Both pages are registered with Streamlit, but the navigation menu is hidden.
# Users move between them using the interface buttons, matching the behaviour
# of the full PawMatch application.
login_page = st.Page(
    "login.py",
    title="Log in",
    icon=":material/login:",
    default=True,
    help="Sign in with an adopter email address or administrator username.",
)
registration_page = st.Page(
    "registration.py",
    title="Create an account",
    icon=":material/person_add:",
    help="Create a new adopter account using the five required registration fields.",
)

selected_page = st.navigation(
    [login_page, registration_page],
    position="hidden",
)
selected_page.run()
