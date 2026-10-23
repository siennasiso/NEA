"""Parts shared by the log-in and registration pages: the tab switch, field errors and Google.

The two pages stay separate, as in the original (app.py and pages/2_Registration.py); the
switch at the top of each form moves between them. "Continue with Google" is optional: it is
drawn only when the [auth] settings are in .streamlit/secrets.toml (webui.state.google_ready).
"""

from html import escape

import streamlit as st

from pawmatch import auth
from webui.state import PAGES, database, google_ready, home_for, sign_in

TABS = {"login": "Log in", "registration": "Create an account"}


def auth_tabs(active: str) -> None:
    """Log in | Create an account, above the form; picking the other tab opens its page."""
    key = f"auth_tab_{active}"

    def keep_open() -> None:
        if st.session_state[key] is None:  # clicking the open tab again leaves it open
            st.session_state[key] = TABS[active]

    choice = st.segmented_control("Log in or create an account", list(TABS.values()), default=TABS[active],
                                  key=key, on_change=keep_open, label_visibility="collapsed", width="stretch")
    if choice and choice != TABS[active]:
        st.switch_page(PAGES[next(page for page, label in TABS.items() if label == choice)])


def field(errors: dict, name: str) -> str:
    """The original's container key: <name>_error draws the field red (see pawmatch_style)."""
    return f"{name}_error" if name in errors else f"{name}_field"


def show_error(errors: dict, *names: str) -> None:
    for name in names:
        if name in errors:
            st.html(f'<p class="field-error" role="alert">{escape(errors[name])}</p>')


def google_button(where: str) -> None:
    if google_ready():
        st.html('<div class="divider"><span>or</span></div>')
        st.button("Continue with Google", key=f"google_{where}", icon=":material/account_circle:",
                  on_click=st.login, width="stretch")


def finish_google_account() -> None:
    """After a Google sign-in: open their PawMatch account, or ask once for the two missing details.

    The email address comes from Google; staff accounts never sign in this way (pawmatch.auth).
    """
    with database() as conn:
        found, errors = auth.external_login(conn, st.user.get("email"), st.user.get("email_verified"))
    if found:
        sign_in(found, method="google")
        st.switch_page(home_for(found))
    st.html(
        """
        <p class="eyebrow" style="color:var(--pm-primary-deep);">Signed in with Google</p>
        <h2 class="form-title">Finish creating your account</h2>
        <p class="form-copy">PawMatch needs your name and age once. Your email address comes from Google.</p>
        """
    )
    if errors:
        show_error(errors, *errors)
        st.button("Sign out of Google", key="secondary_button", on_click=st.logout, width="stretch")
        return
    problems = st.session_state.get("google_errors", {})
    with st.form("google_account_form", border=False):
        with st.container(key=field(problems, "name")):
            name = st.text_input("Full name", value=st.user.get("name") or "", max_chars=50, autocomplete="name")
            show_error(problems, "name")
        with st.container(key=field(problems, "age")):
            age = st.number_input("Age", min_value=18, max_value=120, value=None, step=1,
                                  placeholder="Enter your age",
                                  help="Adopter accounts are available to users aged 18 or over.")
            show_error(problems, "age", "email")
        done = st.form_submit_button("Create account", type="primary", icon="🐾", width="stretch")
    if done:
        with database() as conn:
            created, st.session_state.google_errors = auth.finish_external_account(
                conn, name, st.user.get("email"), age)
        if created:
            sign_in(created, method="google")
            st.switch_page(PAGES["questionnaire"])
        st.rerun()
    st.html('<div class="divider"><span>Not you?</span></div>')
    st.button("Sign out of Google", key="secondary_button", on_click=st.logout, width="stretch")
