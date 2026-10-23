"""Pink PawMatch registration page (the original pages/2_Registration.py), on pawmatch.auth.

Her layout, fields, hints and success card are unchanged. pawmatch.auth.register does the
checks (the same rules as her validate_registration) and stores a scrypt hash.
"""

import streamlit as st

from pawmatch import auth
from pawmatch.validation import PASSWORD_MIN
from webui.pawmatch_style import apply_pawmatch_style
from webui.signin import auth_tabs, field, google_button, show_error
from webui.state import PAGES, current_user, database, flash, home_for, sign_in

st.set_page_config(
    page_title="PawMatch | Registration",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_pawmatch_style()

user = current_user()
if user is not None:
    st.switch_page(home_for(user))

REGISTRATION_WIDGET_KEYS = (
    "registration_name",
    "registration_email",
    "registration_age",
    "registration_password",
    "registration_confirm_password",
)

# Clear old values before any widgets are created.
if st.session_state.pop("clear_registration_fields", False):
    for widget_key in REGISTRATION_WIDGET_KEYS:
        st.session_state.pop(widget_key, None)

if "registration_complete" not in st.session_state:
    st.session_state.registration_complete = False
if "registration_errors" not in st.session_state:
    st.session_state.registration_errors = {}


if st.session_state.registration_complete:
    with st.container(key="success_card"):
        st.markdown("# 🎉 Account created")
        st.write(
            f"Welcome to PawMatch, **{st.session_state.registered_name}**. "
            f"Your account has been created for **{st.session_state.registered_email}**."
        )
        st.caption("You can now log in and begin the adoption questionnaire.")

        if st.button("Go to login", key="login_button", width="stretch"):
            st.session_state.registration_complete = False
            st.switch_page(PAGES["login"])
else:
    errors = st.session_state.registration_errors

    with st.container(key="auth_card"):
        left, right = st.columns([0.92, 1.08], gap="large")

        with left:
            with st.container(key="register_pink_panel"):
                st.html(
                    """
                    <div class="paw-logo" aria-hidden="true">🐾</div>
                    <p class="eyebrow">Join PawMatch</p>
                    <h1 class="brand-title">Create an account and meet your best match.</h1>
                    <p class="brand-copy">
                        Register once to save your questionnaire answers, receive ranked
                        recommendations and return to your results at any time.
                    </p>
                    <p class="benefit"><span class="tick">✓</span>Recommendations based on your lifestyle</p>
                    <p class="benefit"><span class="tick">✓</span>Securely stored account details</p>
                    <p class="benefit"><span class="tick">✓</span>Simple explanations for every result</p>
                    """
                )

        with right:
            with st.container(key="register_form_panel"):
                auth_tabs("registration")
                st.html(
                    """
                    <p class="eyebrow" style="color:var(--pm-primary-deep);">Get started</p>
                    <h2 class="form-title">Create your account</h2>
                    <p class="form-copy">
                        Complete each field below. All fields are required.
                    </p>
                    """
                )

                with st.form("registration_form", clear_on_submit=False, border=False):
                    with st.container(key=field(errors, "name")):
                        name = st.text_input(
                            "Full name",
                            placeholder="Enter your full name",
                            key="registration_name",
                            max_chars=50,
                            autocomplete="name",
                        )
                        show_error(errors, "name")

                    with st.container(key=field(errors, "email")):
                        email = st.text_input(
                            "Email address",
                            placeholder="name@example.com",
                            key="registration_email",
                            max_chars=254,
                            autocomplete="email",
                        )
                        show_error(errors, "email")

                    with st.container(key=field(errors, "age")):
                        age = st.number_input(
                            "Age",
                            min_value=18,
                            max_value=120,
                            value=None,
                            step=1,
                            placeholder="Enter your age",
                            key="registration_age",
                            help="Adopter accounts are available to users aged 18 or over.",
                        )
                        show_error(errors, "age")

                    with st.container(key=field(errors, "password")):
                        password = st.text_input(
                            "Password",
                            type="password",
                            placeholder="Create a password",
                            key="registration_password",
                            max_chars=128,
                            autocomplete="new-password",
                        )
                        st.html(f'<p class="password-hint">Use at least {PASSWORD_MIN} characters.</p>')
                        show_error(errors, "password")

                    with st.container(key=field(errors, "confirm_password")):
                        confirm_password = st.text_input(
                            "Confirm password",
                            type="password",
                            placeholder="Repeat your password",
                            key="registration_confirm_password",
                            max_chars=128,
                            autocomplete="new-password",
                        )
                        show_error(errors, "confirm_password")

                    submitted = st.form_submit_button(
                        "Create account",
                        type="primary",
                        icon="🐾",
                        width="stretch",
                    )

                if submitted:
                    with database() as conn:
                        created, problems = auth.register(conn, name, email, age, password, confirm_password)
                    if created is None:
                        st.session_state.registration_errors = {
                            "confirm_password" if key == "confirm" else key: message
                            for key, message in problems.items()
                        }
                        st.rerun()

                    # Client review 2: going back to the login screen after sign-up felt like
                    # nothing had happened, so a new account is signed straight in.
                    sign_in(created)
                    flash(f"Welcome to PawMatch, {created.name}. Your account is ready.", "success")
                    st.switch_page(home_for(created))

                google_button("registration")

                st.html('<div class="divider"><span>Already have an account?</span></div>')

                if st.button("Back to login", key="secondary_button", width="stretch"):
                    st.session_state.registration_errors = {}
                    st.switch_page(PAGES["login"])

                st.html(
                    """
                    <div class="privacy-note">
                        🔒 Passwords are converted into a salted hash before being stored.
                        The original password is never saved in the database.
                    </div>
                    """
                )
