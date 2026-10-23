"""PawMatch login page (the original app.py), on the tested sign-in in pawmatch.auth.

Her two-column card is unchanged. The form now checks details with pawmatch.auth.login
(scrypt hashes, one message for any wrong detail so nobody can probe for accounts), staff
sign in with their email like everyone else, and the Log in | Create an account switch and
the optional "Continue with Google" button sit with the form.
"""

import streamlit as st

from pawmatch import auth
from webui.pawmatch_style import apply_pawmatch_style
from webui.signin import auth_tabs, field, finish_google_account, google_button, show_error
from webui.state import PAGES, current_user, database, google_signed_in, home_for, show_flash, sign_in

st.set_page_config(
    page_title="PawMatch | Login",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_pawmatch_style()

user = current_user()
if user is not None:
    st.switch_page(home_for(user))

show_flash()
with st.container(key="auth_card"):
    left, right = st.columns([1.05, 0.95], gap="large")

    with left:
        with st.container(key="login_pink_panel"):
            st.html(
                """
                <div class="paw-logo" aria-hidden="true">🐾</div>
                <p class="eyebrow">PawMatch Adoption</p>
                <h1 class="brand-title">Find a companion who fits your life.</h1>
                <p class="brand-copy">
                    Sign in to continue your questionnaire, view your compatibility
                    results and discover animals suited to your home.
                </p>
                <p class="benefit"><span class="tick">✓</span>Personalised compatibility scores</p>
                <p class="benefit"><span class="tick">✓</span>Clear reasons behind every match</p>
                <p class="benefit"><span class="tick">✓</span>Animal welfare placed first</p>
                """
            )

    with right:
        with st.container(key="login_form_panel"):
            if google_signed_in():
                finish_google_account()
                st.stop()

            auth_tabs("login")
            st.html(
                """
                <p class="eyebrow" style="color:var(--pm-primary-deep);">Welcome back</p>
                <h2 class="form-title">Log in to your account</h2>
                <p class="form-copy">
                    Enter the email address and password for your PawMatch account.
                </p>
                """
            )

            previous_errors = st.session_state.get("login_errors", {})

            with st.form("login_form", clear_on_submit=False, border=False):
                with st.container(key=field(previous_errors, "login_email")):
                    email = st.text_input(
                        "Email address",
                        placeholder="name@example.com",
                        key="login_identifier",
                        max_chars=254,
                        autocomplete="username",
                    )
                    show_error(previous_errors, "login_email")

                with st.container(key=field(previous_errors, "login_password")):
                    password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Enter your password",
                        key="login_password",
                        max_chars=128,
                        autocomplete="current-password",
                    )
                    show_error(previous_errors, "login_password")

                submitted = st.form_submit_button(
                    "Log in",
                    type="primary",
                    icon="🐾",
                    width="stretch",
                )

            if submitted:
                with database() as conn:
                    user, errors = auth.login(conn, email, password)
                if user is None:
                    # field errors under each box; a wrong email or password under the password
                    st.session_state.login_errors = {
                        f"login_{name}": message for name, message in errors.items() if name != "login"
                    } | ({"login_password": errors["login"]} if "login" in errors else {})
                    st.rerun()
                sign_in(user)
                st.switch_page(home_for(user))

            google_button("login")

            st.html('<div class="divider"><span>New to PawMatch?</span></div>')

            if st.button("Create an account", key="secondary_button", width="stretch"):
                st.session_state.pop("login_errors", None)
                st.switch_page(PAGES["registration"])
