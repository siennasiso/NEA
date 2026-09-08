"""PawMatch login page. Run this file with: streamlit run app.py"""

import streamlit as st

from pawmatch_auth import authenticate_user, initialise_database, validate_login
from pawmatch_style import apply_pawmatch_style

st.set_page_config(
    page_title="PawMatch | Login",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

initialise_database()
apply_pawmatch_style()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


if st.session_state.logged_in:
    if st.session_state.get("role") == "admin":
        st.switch_page("pages/7_Admin_Dashboard.py")
    st.switch_page("pages/1_Home.py")
else:

    with st.container(key="auth_card"):
        left, right = st.columns([1.05, 0.95], gap="large")

        with left:
            with st.container(key="login_pink_panel"):
                st.markdown(
                    """
                    <div class="paw-logo">🐾</div>
                    <p class="eyebrow">PawMatch Adoption</p>
                    <h1 class="brand-title">Find a companion who fits your life.</h1>
                    <p class="brand-copy">
                        Sign in to continue your questionnaire, view your compatibility
                        results and discover animals suited to your home.
                    </p>
                    <p class="benefit"><span class="tick">✓</span>Personalised compatibility scores</p>
                    <p class="benefit"><span class="tick">✓</span>Clear reasons behind every match</p>
                    <p class="benefit"><span class="tick">✓</span>Animal welfare placed first</p>
                    """,
                    unsafe_allow_html=True,
                )

        with right:
            with st.container(key="login_form_panel"):
                st.markdown(
                    """
                    <p class="eyebrow" style="color:#d93679;">Welcome back</p>
                    <h2 class="form-title">Log in to your account</h2>
                    <p class="form-copy">
                        Enter the email address and password used when you registered.
                    </p>
                    """,
                    unsafe_allow_html=True,
                )

                previous_errors = st.session_state.get("login_errors", {})

                with st.form("login_form", clear_on_submit=False, border=False):
                    with st.container(
                        key="login_email_error" if "email" in previous_errors else "login_email_field"
                    ):
                        email = st.text_input(
                            "Email address",
                            placeholder="name@example.com",
                            key="login_email",
                            autocomplete="email",
                        )
                        if "email" in previous_errors:
                            st.markdown(
                                f'<p class="field-error">{previous_errors["email"]}</p>',
                                unsafe_allow_html=True,
                            )

                    with st.container(
                        key=(
                            "login_password_error"
                            if "password" in previous_errors
                            else "login_password_field"
                        )
                    ):
                        password = st.text_input(
                            "Password",
                            type="password",
                            placeholder="Enter your password",
                            key="login_password",
                            autocomplete="current-password",
                        )
                        if "password" in previous_errors:
                            st.markdown(
                                f'<p class="field-error">{previous_errors["password"]}</p>',
                                unsafe_allow_html=True,
                            )

                    submitted = st.form_submit_button(
                        "Log in",
                        type="primary",
                        icon="🐾",
                        width="stretch",
                    )

                if submitted:
                    errors, cleaned_email = validate_login(email, password)
                    if errors:
                        st.session_state.login_errors = errors
                        st.rerun()

                    user = authenticate_user(cleaned_email, password)
                    if user is None:
                        st.session_state.login_errors = {
                            "password": "The email address or password is incorrect."
                        }
                        st.rerun()

                    st.session_state.login_errors = {}
                    st.session_state.logged_in = True
                    st.session_state.user_id = user["user_id"]
                    st.session_state.user_name = user["name"]
                    st.session_state.user_email = user["email"]
                    st.session_state.role = user["role"]
                    st.rerun()

                st.markdown(
                    '<div class="divider"><span>New to PawMatch?</span></div>',
                    unsafe_allow_html=True,
                )

                if st.button("Create an account", key="secondary_button", width="stretch"):
                    st.switch_page("pages/2_Registration.py")
