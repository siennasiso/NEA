"""Pink PawMatch registration page for the Streamlit multipage app."""

import streamlit as st

from pawmatch_auth import create_user, initialise_database, validate_registration
from pawmatch_style import apply_pawmatch_style

st.set_page_config(
    page_title="PawMatch | Registration",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

initialise_database()
apply_pawmatch_style()

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
            st.switch_page("loginpage.py")
else:
    errors = st.session_state.registration_errors

    with st.container(key="auth_card"):
        left, right = st.columns([0.92, 1.08], gap="large")

        with left:
            with st.container(key="register_pink_panel"):
                st.markdown(
                    """
                    <div class="paw-logo">🐾</div>
                    <p class="eyebrow">Join PawMatch</p>
                    <h1 class="brand-title">Create an account and meet your best match.</h1>
                    <p class="brand-copy">
                        Register once to save your questionnaire answers, receive ranked
                        recommendations and return to your results at any time.
                    </p>
                    <p class="benefit"><span class="tick">✓</span>Recommendations based on your lifestyle</p>
                    <p class="benefit"><span class="tick">✓</span>Securely stored account details</p>
                    <p class="benefit"><span class="tick">✓</span>Simple explanations for every result</p>
                    """,
                    unsafe_allow_html=True,
                )

        with right:
            with st.container(key="register_form_panel"):
                st.markdown(
                    """
                    <p class="eyebrow" style="color:#d93679;">Get started</p>
                    <h2 class="form-title">Create your account</h2>
                    <p class="form-copy">
                        Complete each field below. All fields are required.
                    </p>
                    """,
                    unsafe_allow_html=True,
                )

                with st.form("registration_form", clear_on_submit=False, border=False):
                    with st.container(key="name_error" if "name" in errors else "name_field"):
                        name = st.text_input(
                            "Full name",
                            placeholder="Enter your full name",
                            key="registration_name",
                            max_chars=60,
                            autocomplete="name",
                        )
                        if "name" in errors:
                            st.markdown(
                                f'<p class="field-error">{errors["name"]}</p>',
                                unsafe_allow_html=True,
                            )

                    with st.container(key="email_error" if "email" in errors else "email_field"):
                        email = st.text_input(
                            "Email address",
                            placeholder="name@example.com",
                            key="registration_email",
                            max_chars=254,
                            autocomplete="email",
                        )
                        if "email" in errors:
                            st.markdown(
                                f'<p class="field-error">{errors["email"]}</p>',
                                unsafe_allow_html=True,
                            )

                    with st.container(key="age_error" if "age" in errors else "age_field"):
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
                        if "age" in errors:
                            st.markdown(
                                f'<p class="field-error">{errors["age"]}</p>',
                                unsafe_allow_html=True,
                            )

                    with st.container(
                        key="password_error" if "password" in errors else "password_field"
                    ):
                        password = st.text_input(
                            "Password",
                            type="password",
                            placeholder="Create a password",
                            key="registration_password",
                            max_chars=128,
                            autocomplete="new-password",
                        )
                        st.markdown(
                            '<p class="password-hint">Use 8 or more characters with an uppercase letter, lowercase letter and number.</p>',
                            unsafe_allow_html=True,
                        )
                        if "password" in errors:
                            st.markdown(
                                f'<p class="field-error">{errors["password"]}</p>',
                                unsafe_allow_html=True,
                            )

                    with st.container(
                        key=(
                            "confirm_password_error"
                            if "confirm_password" in errors
                            else "confirm_password_field"
                        )
                    ):
                        confirm_password = st.text_input(
                            "Confirm password",
                            type="password",
                            placeholder="Repeat your password",
                            key="registration_confirm_password",
                            max_chars=128,
                            autocomplete="new-password",
                        )
                        if "confirm_password" in errors:
                            st.markdown(
                                f'<p class="field-error">{errors["confirm_password"]}</p>',
                                unsafe_allow_html=True,
                            )

                    submitted = st.form_submit_button(
                        "Create account",
                        type="primary",
                        icon="🐾",
                        width="stretch",
                    )

                if submitted:
                    validation_errors, cleaned = validate_registration(
                        name,
                        email,
                        age,
                        password,
                        confirm_password,
                    )

                    if validation_errors:
                        st.session_state.registration_errors = validation_errors
                        st.rerun()

                    created, database_message = create_user(
                        cleaned["name"],
                        cleaned["email"],
                        cleaned["age"],
                        cleaned["password"],
                    )

                    if not created:
                        if "already exists" in database_message:
                            st.session_state.registration_errors = {
                                "email": database_message
                            }
                        else:
                            st.session_state.registration_errors = {
                                "email": database_message
                            }
                        st.rerun()

                    st.session_state.registration_errors = {}
                    st.session_state.registration_complete = True
                    st.session_state.registered_name = cleaned["name"]
                    st.session_state.registered_email = cleaned["email"]
                    st.session_state.clear_registration_fields = True
                    st.rerun()

                st.markdown(
                    '<div class="divider"><span>Already have an account?</span></div>',
                    unsafe_allow_html=True,
                )

                if st.button("Back to login", key="secondary_button", width="stretch"):
                    st.session_state.registration_errors = {}
                    st.switch_page("loginpage.py")

                st.markdown(
                    """
                    <div class="privacy-note">
                        🔒 Passwords are converted into a salted hash before being stored.
                        The original password is never saved in the database.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )