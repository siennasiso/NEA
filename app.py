"""PawMatch registration and login development increment.

Only authentication is implemented on this branch at this stage. The animal,
questionnaire and matching features are intentionally absent so the R1-R6
pre-development tests can be completed against one isolated subsystem.
"""

from typing import Any

import streamlit as st

from auth import authenticate_user, register_user
from database import create_database


st.set_page_config(
    page_title="PawMatch authentication",
    page_icon=":material/pets:",
    layout="centered",
)

# The CREATE TABLE IF NOT EXISTS statements make startup repeatable. They do
# not erase records, so accounts created during manual testing remain stored.
create_database()

# Streamlit reruns this file after every interaction. Session state preserves
# the authenticated account until the user explicitly logs out or closes the
# browser session.
st.session_state.setdefault("current_user", None)
st.session_state.setdefault("authentication_view", "Log in")
st.session_state.setdefault("authenticated_area", "Home")


def show_errors(errors: dict[str, str]) -> None:
    """Display each backend validation message clearly beneath the form."""
    for message in errors.values():
        st.error(message)


def log_out() -> None:
    """Remove authentication data and return to the login view."""
    st.session_state.current_user = None
    st.session_state.authentication_view = "Log in"
    st.session_state.authenticated_area = "Home"


def show_authenticated_area(user: dict[str, Any]) -> None:
    """Render the temporary adopter/admin destinations needed for R2 and R6."""
    header_row = st.container(horizontal=True, vertical_alignment="center")
    with header_row:
        st.title("PawMatch")
        if st.button(
            "Log out",
            key="logout_button",
            icon=":material/logout:",
            width="content",
        ):
            log_out()
            st.rerun()

    st.caption(f"Signed in as {user['name']} · role: {user['role']}")

    # Both choices stay visible so R6 can demonstrate the role check rather
    # than relying only on a hidden navigation link.
    selected_area = st.segmented_control(
        "Choose an area",
        ["Home", "Admin area"],
        key="authenticated_area",
        width="stretch",
    )

    if selected_area == "Admin area" and user["role"] != "admin":
        st.error("Admin access required. You have been returned to the homepage.")
        st.header("Adopter homepage")
        st.write(
            "Your registration and login were successful. Animal browsing and "
            "matching will be added in later development stages."
        )
        return

    if selected_area == "Admin area":
        st.header("Administrator area")
        st.success("Administrator access granted.")
        st.write(
            "Animal management will be implemented after this authentication stage."
        )
        return

    st.header("Adopter homepage" if user["role"] == "user" else "Administrator home")
    st.success("You are securely signed in.")
    st.write(
        "This temporary destination proves that a successful login creates a "
        "session and sends each role to an authorised area."
    )


current_user = st.session_state.current_user

if current_user is not None:
    show_authenticated_area(current_user)
else:
    st.title("PawMatch")
    st.subheader("Registration and login development stage")
    st.write(
        "Create an adopter account or sign in to test the authentication requirements."
    )

    authentication_view = st.segmented_control(
        "Authentication option",
        ["Log in", "Register"],
        key="authentication_view",
        width="stretch",
    )

    if authentication_view == "Register":
        st.header("Create an adopter account")
        st.caption("All five planned fields are present for pre-development test R1.")

        # A form submits all related values together. Backend validation still
        # repeats every rule before any SQL INSERT occurs.
        with st.form("registration_form", clear_on_submit=False):
            name = st.text_input(
                "Full name",
                key="registration_name",
                max_chars=60,
                placeholder="e.g. Sienna Sisodia",
            )
            email = st.text_input(
                "Email address",
                key="registration_email",
                max_chars=254,
                placeholder="e.g. name@example.com",
            )
            age = st.text_input(
                "Age",
                key="registration_age",
                max_chars=3,
                placeholder="You must be 18 or over",
            )
            password = st.text_input(
                "Password",
                type="password",
                key="registration_password",
                max_chars=128,
                help="Use at least 8 characters.",
            )
            confirm_password = st.text_input(
                "Confirm password",
                type="password",
                key="registration_confirmation",
                max_chars=128,
            )
            submitted = st.form_submit_button(
                "Create account",
                type="primary",
                icon=":material/person_add:",
                width="stretch",
            )

        if submitted:
            errors, new_user = register_user(
                name, email, age, password, confirm_password
            )
            if errors:
                show_errors(errors)
            else:
                # Registration creates a normal adopter session immediately;
                # the role is never selected by the person registering.
                st.session_state.current_user = new_user
                st.session_state.authenticated_area = "Home"
                st.rerun()

    else:
        st.header("Log in")
        with st.form("login_form", clear_on_submit=False):
            identifier = st.text_input(
                "Email address or username",
                key="login_identifier",
                max_chars=254,
            )
            login_password = st.text_input(
                "Password",
                type="password",
                key="login_password",
                max_chars=128,
            )
            login_submitted = st.form_submit_button(
                "Log in",
                type="primary",
                icon=":material/login:",
                width="stretch",
            )

        if login_submitted:
            errors, authenticated_user = authenticate_user(
                identifier, login_password
            )
            if errors:
                show_errors(errors)
            else:
                st.session_state.current_user = authenticated_user
                st.session_state.authenticated_area = (
                    "Admin area"
                    if authenticated_user["role"] == "admin"
                    else "Home"
                )
                st.rerun()
