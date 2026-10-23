"""The landing card (criterion 5): the original's pink panel beside a form, with two tabs.

"Log in" holds the original log-in form; "Create an account" holds the original five-field
registration form. Both pages of the original (app.py and 2_Registration.py) open this card,
each on its own tab, so the page set and its order are unchanged.

Email and password sign-in is PawMatch's own Python (pawmatch/auth.py: scrypt hashes, a
generic failure message, roles). "Continue with Google" is optional: it appears only when
the [auth] settings are in .streamlit/secrets.toml, and a Google (or Clerk) account is
linked to a local adopter account by its verified email address. Staff always use their
PawMatch password.
"""

from __future__ import annotations

import streamlit as st

from pawmatch import auth

from . import html
from .components import field_errors
from .state import PAGES, current_user, database, google_ready, home_for, show_flash, sign_in

LOG_IN, REGISTER = "Log in", "Create an account"
PANELS = {
    LOG_IN: ("PawMatch adoption", "Find a companion who fits your life.",
             "Log in to continue your questionnaire, see your compatibility results and meet "
             "animals suited to your home.",
             ["Personalised compatibility scores", "Clear reasons behind every match",
              "Animal welfare placed first"]),
    REGISTER: ("Join PawMatch", "Create an account and meet your best match.",
               "Register once to save your questionnaire answers, see ranked recommendations and "
               "come back to your results at any time.",
               ["Recommendations based on your lifestyle", "Securely stored account details",
                "A simple explanation for every result"]),
}


def _open_tab(tabs_key: str, tab: str) -> None:
    st.session_state[tabs_key] = tab


def _switch_button(tabs_key: str, tab: str, text: str) -> None:
    """The original's "New to PawMatch?" and "Already have an account?" buttons, now opening the other tab."""
    with st.container(key=f"switch-{'register' if tab == REGISTER else 'log-in'}"):
        st.button(text, key=f"switch-button-{tab[:6].lower()}", on_click=_open_tab, args=(tabs_key, tab),
                  width="stretch")


def _google_button(where: str) -> None:
    """Shown only when the [auth] secrets are set (see webui.state.google_ready)."""
    if google_ready():
        st.html(html.divider("or"))
        with st.container(key=f"google-{where}"):
            st.button("Continue with Google", key=f"google-button-{where}", icon=":material/account_circle:",
                      on_click=st.login, width="stretch")


def log_in_form(tabs_key: str) -> None:
    st.html(html.form_intro("Welcome back", "Log in to your account",
                            "Enter the email address and password you registered with."))
    show_flash()
    errors = st.session_state.pop("login_errors", {})
    with st.form("login", border=False):
        email = st.text_input("Email address", placeholder="name@example.com", max_chars=254)
        field_errors(errors, "email")
        password = st.text_input("Password", type="password", placeholder="Enter your password", max_chars=128)
        field_errors(errors, "password", "login")
        submitted = st.form_submit_button("Log in", type="primary", icon="🐾", width="stretch")
    if submitted:
        with database() as conn:
            found, errors = auth.login(conn, email, password)
        if found:
            sign_in(found)
            st.switch_page(home_for(found))
        st.session_state["login_errors"] = errors
        st.rerun()
    _google_button("log-in")
    st.html(html.divider("New to PawMatch?"))
    _switch_button(tabs_key, REGISTER, "Create an account")


def registration_form(tabs_key: str) -> None:
    st.html(html.form_intro("Get started", "Create your account",
                            "Complete each field below. All fields are required."))
    errors = st.session_state.pop("registration_errors", {})
    with st.form("registration", border=False):
        name = st.text_input("Full name", max_chars=50)
        field_errors(errors, "name")
        email = st.text_input("Email address", placeholder="name@example.com", max_chars=254)
        field_errors(errors, "email")
        age = st.number_input("Age", min_value=0, max_value=120, value=None, step=1,
                              help="Adopter accounts are for people aged 18 or over.")
        field_errors(errors, "age")
        password = st.text_input("Password", type="password", max_chars=128, help="At least 8 characters.")
        field_errors(errors, "password")
        confirm = st.text_input("Confirm password", type="password", max_chars=128)
        field_errors(errors, "confirm")
        submitted = st.form_submit_button("Create account", type="primary", width="stretch")
    if submitted:
        with database() as conn:
            created, errors = auth.register(conn, name, email, age, password, confirm)
        if created:
            sign_in(created)
            st.session_state["just_registered"] = True
        else:
            st.session_state["registration_errors"] = errors
        st.rerun()
    _google_button("register")
    st.html(html.divider("Already have an account?"))
    _switch_button(tabs_key, LOG_IN, "Back to log in")
    st.html(html.note("Passwords are stored only as a salted scrypt hash, never as the password itself.",
                      "privacy", "Your privacy", "🔒"))


def welcome_card(first_name: str) -> None:
    """Shown once, straight after registering (the original's success card)."""
    del st.session_state["just_registered"]
    st.html(html.form_intro("Account created", f"Welcome to PawMatch, {first_name}!",
                            "Your account is ready and you are logged in. Nine quick questions about "
                            "your home and routine are all PawMatch needs to find your matches."))
    with st.container(key="link-primary-questionnaire"):
        st.page_link(PAGES["questionnaire"], label="Start the questionnaire", icon=":material/checklist:",
                     width="stretch")
    with st.container(key="link-home"):
        st.page_link(PAGES["home"], label="Go to my home page", width="stretch")


def finish_google_account() -> None:
    """First Google sign-in: link it to a PawMatch account, or ask once for the two missing details."""
    with database() as conn:
        found, errors = auth.external_login(conn, st.user.get("email"), st.user.get("email_verified"))
    if found:
        sign_in(found, method="google")
        st.switch_page(home_for(found))
    st.html(html.form_intro("Signed in with Google", "Finish creating your account",
                            "PawMatch needs your name and age once. Your email address comes from Google."))
    if errors:
        for message in errors.values():
            st.error(message)
        st.button("Sign out of Google", icon=":material/logout:", on_click=st.logout, width="stretch")
        return
    with st.form("google-account", border=False):
        name = st.text_input("Full name", value=st.user.get("name") or "", max_chars=50)
        age = st.number_input("Age", min_value=0, max_value=120, value=None, step=1,
                              help="Adopter accounts are for people aged 18 or over.")
        done = st.form_submit_button("Create my account", type="primary", width="stretch")
    if done:
        with database() as conn:
            created, problems = auth.finish_external_account(conn, name, st.user.get("email"), age)
        if created:
            sign_in(created, method="google")
            st.switch_page(PAGES["questionnaire"])
        for message in problems.values():
            st.html(html.field_error(message))
    st.button("Cancel and sign out of Google", type="tertiary", on_click=st.logout)


def auth_page(first_tab: str) -> None:
    """The whole landing card; first_tab is LOG_IN on the log-in page and REGISTER on registration."""
    user = current_user()
    if user and not st.session_state.get("just_registered"):
        st.switch_page(home_for(user))
    with st.container(key="auth-card"):
        panel, side = st.columns([1.02, 0.98], gap="large")
        with side, st.container(key="auth-form"):
            if user:
                welcome_card(user.name.split()[0])
                shown = REGISTER
            elif google_ready() and st.user.is_logged_in:
                finish_google_account()
                shown = REGISTER
            else:
                tabs_key = f"auth-tabs-{first_tab[:6].lower()}"  # one per page, so each opens its own tab
                log_in_tab, register_tab = st.tabs([LOG_IN, REGISTER], default=first_tab, key=tabs_key,
                                                   on_change="rerun")
                with log_in_tab:
                    log_in_form(tabs_key)
                with register_tab:
                    registration_form(tabs_key)
                shown = REGISTER if register_tab.open else LOG_IN
        with panel:
            st.html(html.auth_panel(*PANELS[shown]))
