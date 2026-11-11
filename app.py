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
    # If a user record is already stored in session state, the visitor has
    # successfully registered or logged in. The authentication forms are not
    # drawn again; instead, the appropriate protected destination is shown.
    show_authenticated_area(current_user)
else:
    # ---------------------------------------------------------------------
    # PUBLIC AUTHENTICATION INTERFACE
    # ---------------------------------------------------------------------
    # This part of the interface is only visible when nobody is signed in.
    # The title and short instruction make the purpose of this development
    # increment clear to the person carrying out the manual R1-R6 tests.
    st.title("PawMatch")
    st.subheader("Registration and login development stage")
    st.write(
        "Create an adopter account or sign in to test the authentication requirements."
    )

    # A segmented control provides two clearly labelled interface states in
    # the same page: Log in and Register. Its key connects the widget to the
    # `authentication_view` value initialised in session state above. This
    # means Streamlit remembers the selected view when the script reruns.
    authentication_view = st.segmented_control(
        "Authentication option",
        ["Log in", "Register"],
        key="authentication_view",
        width="stretch",
    )

    if authentication_view == "Register":
        # -----------------------------------------------------------------
        # REGISTRATION PAGE INTERFACE (requirements R1-R4)
        # -----------------------------------------------------------------
        # This heading identifies the task and the caption links the visible
        # fields directly to the R1 pre-development test in the documentation.
        st.header("Create an adopter account")
        st.caption("All five planned fields are present for pre-development test R1.")

        # `st.form` groups the five fields and the submit button into one unit.
        # Streamlit therefore waits for Create account to be pressed before it
        # sends the entered values through the registration process. This is
        # preferable to validating on every keystroke and gives the interface
        # the familiar behaviour of a normal registration page.
        #
        # `clear_on_submit=False` deliberately keeps the entered data visible
        # if validation fails. The user can correct the invalid field without
        # having to type every valid field again. Backend validation in
        # `auth.register_user` still checks every rule before an SQL INSERT.
        with st.form("registration_form", clear_on_submit=False):
            # R1 field 1: the adopter's real name. The key gives this widget a
            # stable identity across Streamlit reruns, max_chars prevents an
            # unnecessarily long UI value, and the placeholder shows the
            # expected style of input without supplying an actual value.
            name = st.text_input(
                "Full name",
                key="registration_name",
                max_chars=60,
                placeholder="e.g. Sienna Sisodia",
            )

            # R1 field 2: the email address becomes the adopter's unique login
            # identifier. The interface accepts the text here, while the
            # backend normalises it, checks its format and checks the database
            # for a duplicate before allowing registration.
            email = st.text_input(
                "Email address",
                key="registration_email",
                max_chars=254,
                placeholder="e.g. name@example.com",
            )

            # R1 field 3: age is collected as text so the validation layer can
            # give a controlled message for blank or non-numeric input. The
            # backend converts a valid value to an integer and enforces 18+.
            age = st.text_input(
                "Age",
                key="registration_age",
                max_chars=3,
                placeholder="You must be 18 or over",
            )

            # R1 field 4: type="password" masks the characters on screen so a
            # nearby person cannot read them. Masking is only an interface
            # protection; `auth.py` separately hashes the password with
            # Argon2id before it is stored in SQLite for requirement R4.
            password = st.text_input(
                "Password",
                type="password",
                key="registration_password",
                max_chars=128,
                help="Use at least 8 characters.",
            )

            # R1 field 5: the repeated password reduces accidental typing
            # mistakes. It is also masked and is compared with `password` by
            # the backend. This confirmation value is never saved to the DB.
            confirm_password = st.text_input(
                "Confirm password",
                type="password",
                key="registration_confirmation",
                max_chars=128,
            )

            # The primary full-width button is the single action for the form.
            # `submitted` is False during ordinary page display and becomes
            # True only for the rerun caused by pressing Create account.
            submitted = st.form_submit_button(
                "Create account",
                type="primary",
                icon=":material/person_add:",
                width="stretch",
            )

        if submitted:
            # The interface passes all five collected values to the backend.
            # Keeping validation and database work in auth.py separates the
            # presentation layer from the program logic and makes the rules
            # easier to inspect, maintain and test independently.
            errors, new_user = register_user(
                name, email, age, password, confirm_password
            )
            if errors:
                # Invalid data does not create a database record. Each useful
                # validation message is displayed with `st.error` so the user
                # knows exactly what must be corrected for the R3 cases.
                show_errors(errors)
            else:
                # Registration creates a normal adopter session immediately;
                # the role is never selected by the person registering. This
                # prevents someone from giving their own account admin rights.
                st.session_state.current_user = new_user
                st.session_state.authenticated_area = "Home"

                # Streamlit has already drawn the registration form during
                # this run. Rerunning immediately makes the top-level condition
                # render the protected adopter homepage instead (R2).
                st.rerun()

    else:
        # -----------------------------------------------------------------
        # LOGIN PAGE INTERFACE (requirements R5-R6)
        # -----------------------------------------------------------------
        # Log in is the default view. Returning users need only an identifier
        # and password, so the interface is intentionally shorter than the
        # registration page.
        st.header("Log in")

        # The login controls are also kept in a form. Authentication is only
        # attempted when the Log in button is pressed, rather than after every
        # edit to the email/username or password fields.
        with st.form("login_form", clear_on_submit=False):
            # The demo administrator uses a username while adopter accounts
            # use an email address. One clearly labelled field supports both
            # identifiers; auth.py normalises and looks up the supplied value.
            identifier = st.text_input(
                "Email address or username",
                key="login_identifier",
                max_chars=254,
            )

            # Password characters are masked in the interface. The plaintext
            # entry is used only for Argon2id verification and is never written
            # into the database or stored in Streamlit session state.
            login_password = st.text_input(
                "Password",
                type="password",
                key="login_password",
                max_chars=128,
            )

            # Pressing this button submits both login values together. The
            # distinctive primary style makes the intended action obvious.
            login_submitted = st.form_submit_button(
                "Log in",
                type="primary",
                icon=":material/login:",
                width="stretch",
            )

        if login_submitted:
            # Authentication is delegated to auth.py. The function returns
            # either a generic error or the safe user data needed to create a
            # session; the interface never queries password hashes directly.
            errors, authenticated_user = authenticate_user(
                identifier, login_password
            )
            if errors:
                # Wrong passwords and unknown accounts intentionally display
                # the same message. This prevents the interface from revealing
                # whether a particular account exists (security part of R5).
                show_errors(errors)
            else:
                # A successful result is retained for subsequent Streamlit
                # reruns. Only non-sensitive account details are placed in
                # session state; the entered password is not stored here.
                st.session_state.current_user = authenticated_user

                # The stored database role determines the first authorised
                # destination. It is not taken from a choice on the login form,
                # so an adopter cannot request administrator access (R6).
                st.session_state.authenticated_area = (
                    "Admin area"
                    if authenticated_user["role"] == "admin"
                    else "Home"
                )

                # Redraw the page immediately so the forms disappear and the
                # authenticated homepage/admin interface is displayed.
                st.rerun()
