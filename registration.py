"""Standalone PawMatch registration interface for the development evidence.

Run only this development stage with:

    streamlit run registration.py

The page deliberately contains registration only. Login, animal browsing,
questionnaires and matching are outside the scope of this file so the
registration requirements can be implemented, tested and documented alone.
"""

from typing import Any

import streamlit as st

from auth import register_user
from database import create_database


# ---------------------------------------------------------------------------
# PAGE AND DATABASE SETUP
# ---------------------------------------------------------------------------
# set_page_config must be the first Streamlit command in the file. It controls
# the browser-tab title, the paw icon and the maximum width of the interface.
st.set_page_config(
    page_title="PawMatch registration",
    page_icon=":material/pets:",
    layout="centered",
)

# Calling create_database here makes the registration page safe to run on a
# new computer. The function uses CREATE TABLE IF NOT EXISTS, so it creates a
# missing database but does not delete accounts that are already stored.
create_database()

# Streamlit runs this entire file again whenever a widget is used. Session
# state preserves whether registration has just succeeded and the safe account
# details needed for the confirmation screen. The password is never stored in
# either of these session-state values.
st.session_state.setdefault("registration_complete", False)
st.session_state.setdefault("registered_user", None)


def display_validation_errors(errors: dict[str, str]) -> None:
    """Display every registration error returned by the backend.

    Validation is performed in auth.py rather than being trusted to the page.
    The interface receives a dictionary so it can show more than one problem
    at a time, helping the user correct all invalid fields efficiently.
    """
    for message in errors.values():
        st.error(message, icon=":material/error:")


def start_another_registration() -> None:
    """Clear the completed state so another manual test can be performed."""
    st.session_state.registration_complete = False
    st.session_state.registered_user = None

    # Widget values are also stored in session state under their keys. Removing
    # them here gives the next test a blank form. This callback runs before the
    # page is redrawn, while the registration widgets are not on the page.
    for widget_key in (
        "registration_name",
        "registration_email",
        "registration_age",
        "registration_password",
        "registration_confirmation",
    ):
        st.session_state.pop(widget_key, None)


# ---------------------------------------------------------------------------
# PAGE HEADING
# ---------------------------------------------------------------------------
# These visible elements give the page a clear title and explain why the user
# is being asked for personal information.
st.title("PawMatch")
st.subheader("Create an adopter account")


if st.session_state.registration_complete:
    # -----------------------------------------------------------------------
    # SUCCESS INTERFACE
    # -----------------------------------------------------------------------
    # This branch is shown only after register_user has validated the data and
    # successfully inserted the new adopter into SQLite.
    registered_user: dict[str, Any] = st.session_state.registered_user

    st.success(
        f"Account created for {registered_user['name']}.",
        icon=":material/check_circle:",
    )
    st.write(
        f"The adopter account **{registered_user['email']}** is now stored in "
        "the PawMatch database."
    )
    st.caption(
        "Open pawmatch.db in DB Browser for SQLite to capture the database "
        "evidence for this successful registration test."
    )

    # This button resets only the interface state. It does not delete the user
    # that was inserted into SQLite, allowing every test record to be inspected.
    st.button(
        "Test another registration",
        key="test_another_registration",
        icon=":material/person_add:",
        type="primary",
        width="stretch",
        on_click=start_another_registration,
    )

else:
    # -----------------------------------------------------------------------
    # REGISTRATION FORM INTERFACE — PRE-DEVELOPMENT REQUIREMENTS R1-R4
    # -----------------------------------------------------------------------
    st.write(
        "Complete all five fields below. You must be at least 18 years old, "
        "and your password must contain at least 8 characters."
    )
    st.caption(
        "This isolated page can be used to collect manual evidence for valid, "
        "invalid, boundary, duplicate-email and password-hashing tests."
    )

    # st.form groups the five related values into one submission. Streamlit
    # therefore waits until Create account is pressed instead of rerunning the
    # validation code after every single keystroke.
    #
    # clear_on_submit=False is intentional. If validation fails, the values
    # remain visible so the user can correct the problem without re-entering
    # every valid field.
    with st.form("registration_form", clear_on_submit=False):
        # R1 FIELD 1 — FULL NAME
        # A stable key preserves the widget across Streamlit reruns. max_chars
        # is an interface limit for usability; auth.py repeats the length and
        # character checks because client-side restrictions cannot be trusted.
        name = st.text_input(
            "Full name",
            key="registration_name",
            max_chars=50,
            placeholder="Enter your full name",
            autocomplete="name",
            help="Use letters, spaces, hyphens, apostrophes or full stops.",
        )

        # R1 FIELD 2 — EMAIL ADDRESS
        # The email is the unique identifier for an adopter account. The
        # backend trims and lowercases it, checks its format and queries SQLite
        # for duplicates before it allows a new row to be inserted.
        email = st.text_input(
            "Email address",
            key="registration_email",
            max_chars=254,
            placeholder="name@example.com",
            autocomplete="email",
        )

        # R1 FIELD 3 — AGE
        # A text input is used deliberately so manual testing can include blank
        # and non-numeric data. auth.py safely converts valid input to an
        # integer and rejects ages below 18 or above 120.
        age = st.text_input(
            "Age",
            key="registration_age",
            max_chars=3,
            placeholder="You must be 18 or over",
            autocomplete="off",
        )

        # R1 FIELD 4 — PASSWORD
        # type="password" hides the characters from people looking at the
        # screen. This does not provide database security by itself: auth.py
        # hashes the value with Argon2id and a random salt before storage.
        password = st.text_input(
            "Password",
            key="registration_password",
            type="password",
            max_chars=128,
            autocomplete="new-password",
            help="Use at least 8 characters. Seven must fail; eight must pass.",
        )

        # R1 FIELD 5 — PASSWORD CONFIRMATION
        # Asking for the value twice catches typing errors. The backend compares
        # the two values but never saves this confirmation to the database.
        confirm_password = st.text_input(
            "Confirm password",
            key="registration_confirmation",
            type="password",
            max_chars=128,
            autocomplete="new-password",
            help="Enter exactly the same password again.",
        )

        # This is the form's only action. submitted is False while the form is
        # simply displayed and True on the rerun caused by this button press.
        submitted = st.form_submit_button(
            "Create account",
            type="primary",
            icon=":material/person_add:",
            width="stretch",
        )

    if submitted:
        # -------------------------------------------------------------------
        # FORM PROCESSING
        # -------------------------------------------------------------------
        # The interface sends the five raw values to register_user. Keeping the
        # rules, hashing and SQL in auth.py separates presentation from program
        # logic and makes the implementation easier to explain and maintain.
        errors, new_user = register_user(
            name,
            email,
            age,
            password,
            confirm_password,
        )

        if errors:
            # Invalid input is not written to the database. Specific feedback
            # supports the invalid and boundary cases in manual test R3.
            display_validation_errors(errors)
        else:
            # register_user returns only safe account data after the INSERT has
            # committed. It never returns the plaintext password or its hash.
            st.session_state.registered_user = new_user
            st.session_state.registration_complete = True

            # Elements already drawn during this run do not disappear by
            # themselves. st.rerun immediately redraws the page and selects the
            # success branch at the top using the updated session-state flag.
            st.rerun()

    # This security note is visible even before submission. It reassures users
    # and gives a clear screenshot annotation for password-hashing test R4.
    st.info(
        "Passwords are stored as salted Argon2id hashes. The original password "
        "and confirmation are never saved in SQLite.",
        icon=":material/lock:",
    )
