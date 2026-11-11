"""PawMatch pink login interface for the authentication development stage."""

from typing import Any

import streamlit as st

from auth import authenticate_user
from database import create_database


# ---------------------------------------------------------------------------
# DATABASE AND INTERFACE SETUP
# ---------------------------------------------------------------------------
# The database creation is repeatable and does not remove existing accounts.
# This lets the login page run immediately after registration testing.
create_database()


def apply_login_style() -> None:
    """Apply the same pink styling used by the original PawMatch login page."""
    st.markdown(
        """
        <style>
        :root {
            --pink: #dd5b94;
            --dark-pink: #c73f7a;
            --deep-pink: #9d2f63;
            --pale-pink: #fff7fb;
            --border-pink: #efbfd4;
            --dark-text: #44383f;
            --muted-text: #796872;
            --error: #bd294b;
            --brand-panel: linear-gradient(150deg, #f5c5da 0%, #efaccb 58%, #e99abe 100%);
            --brand-canvas:
                radial-gradient(circle at 12% 8%, rgba(246, 190, 216, .52), transparent 28%),
                radial-gradient(circle at 88% 88%, rgba(238, 181, 207, .38), transparent 26%),
                #fff8fc;
        }

        .stApp {
            background: var(--brand-canvas);
            color: var(--dark-text);
        }

        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stDecoration"] { display: none; }
        [data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }

        .block-container {
            max-width: 1080px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        .st-key-auth_card {
            padding: 10px;
            border: 1px solid rgba(196, 77, 132, .14);
            border-radius: 26px;
            background: rgba(255, 255, 255, .94);
            box-shadow: 0 24px 60px rgba(101, 49, 75, .13);
        }

        .st-key-login_pink_panel {
            min-height: 570px;
            padding: 3rem 2.6rem;
            border: 1px solid rgba(184, 76, 124, .16);
            border-radius: 20px;
            background: var(--brand-panel);
            color: var(--dark-text);
        }

        .st-key-login_form_panel {
            min-height: 570px;
            padding: 2.5rem 2rem 2rem;
        }

        .paw-logo {
            width: 58px;
            height: 58px;
            display: grid;
            place-items: center;
            margin-bottom: 1.8rem;
            border: 1px solid rgba(255,255,255,.62);
            border-radius: 17px;
            background: rgba(255,255,255,.42);
            font-size: 1.65rem;
        }

        .eyebrow {
            margin: 0 0 .7rem;
            font-size: .76rem;
            font-weight: 800;
            letter-spacing: .14em;
            text-transform: uppercase;
        }

        .brand-title {
            max-width: 430px;
            margin: 0;
            color: var(--dark-text);
            font-size: clamp(2.25rem, 4vw, 3.25rem);
            line-height: 1.04;
            letter-spacing: -.045em;
        }

        .brand-copy {
            max-width: 430px;
            margin: 1.15rem 0 1.7rem;
            color: var(--dark-text);
            line-height: 1.65;
        }

        .benefit {
            margin: .85rem 0;
            color: var(--dark-text);
            font-size: .94rem;
            font-weight: 650;
        }

        .tick {
            display: inline-grid;
            place-items: center;
            width: 28px;
            height: 28px;
            margin-right: .55rem;
            border-radius: 9px;
            background: rgba(255,255,255,.55);
        }

        .form-title {
            margin: 0;
            color: var(--dark-text);
            font-size: 2.05rem;
            line-height: 1.1;
            letter-spacing: -.035em;
        }

        .form-copy {
            margin: .65rem 0 1.15rem;
            color: var(--muted-text);
            line-height: 1.55;
        }

        [data-testid="stTextInput"] label {
            color: var(--dark-text);
            font-weight: 700;
        }

        div[data-baseweb="input"] {
            min-height: 47px;
            border: 1px solid var(--border-pink);
            border-radius: 11px;
            background: var(--pale-pink);
        }

        div[data-baseweb="input"]:focus-within {
            border-color: var(--pink);
            box-shadow: 0 0 0 4px rgba(221,91,148,.10);
        }

        div[data-baseweb="input"] > div { background: transparent; }

        .st-key-login_identifier_error div[data-baseweb="input"],
        .st-key-login_password_error div[data-baseweb="input"] {
            border-color: var(--error);
            box-shadow: 0 0 0 3px rgba(189,41,75,.10);
        }

        .field-error {
            margin: -.35rem 0 .45rem;
            color: var(--error);
            font-size: .80rem;
            font-weight: 700;
            line-height: 1.35;
        }

        .stFormSubmitButton button {
            min-height: 49px;
            margin-top: .25rem;
            border: 1px solid var(--dark-pink);
            border-radius: 11px;
            background: var(--dark-pink);
            color: white;
            font-weight: 800;
            box-shadow: 0 10px 24px rgba(157,47,99,.18);
        }

        .stFormSubmitButton button:hover {
            border: 1px solid var(--deep-pink);
            color: white;
            background: var(--deep-pink);
        }

        .st-key-secondary_button button,
        .st-key-logout_button button {
            min-height: 47px;
            border: 1px solid var(--border-pink);
            border-radius: 11px;
            background: white;
            color: var(--dark-pink);
            font-weight: 750;
        }

        .divider {
            display: flex;
            align-items: center;
            gap: .8rem;
            margin: 1rem 0 .7rem;
            color: #a98a99;
            font-size: .82rem;
        }

        .divider::before, .divider::after {
            content: "";
            height: 1px;
            flex: 1;
            background: #f1d5e1;
        }

        .st-key-success_card {
            max-width: 650px;
            margin: 4.5rem auto 0;
            padding: 3rem;
            border: 1px solid rgba(237,79,145,.16);
            border-radius: 27px;
            background: rgba(255,255,255,.94);
            text-align: center;
            box-shadow: 0 24px 60px rgba(121,35,74,.14);
        }

        @media (max-width: 850px) {
            .block-container { padding-top: 1rem; }
            .st-key-login_pink_panel {
                min-height: auto;
                padding: 2rem;
            }
            .st-key-login_form_panel {
                min-height: auto;
                padding: 2rem 1.15rem;
            }
            .brand-title { font-size: 2.25rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# Styling is applied before either the form or success screen is drawn.
apply_login_style()

# Streamlit reruns the current page after each interaction. These session values
# keep the safe authenticated account and the last field-specific errors.
st.session_state.setdefault("current_user", None)
st.session_state.setdefault("login_errors", {})


def show_signed_in_screen(user: dict[str, Any]) -> None:
    """Show a temporary authenticated destination for manual R5/R6 evidence."""
    with st.container(key="success_card"):
        st.markdown("# 🎉 Login successful")
        st.write(f"Welcome back, **{user['name']}**.")
        st.caption(f"Authenticated role: {user['role']}")

        if user["role"] == "admin":
            st.success("Administrator access granted.")
        else:
            st.success("Adopter homepage access granted.")

        # Logout deletes only the browser-session account data. It does not
        # remove the registered user from the SQLite database.
        if st.button("Log out", key="logout_button", width="stretch"):
            st.session_state.current_user = None
            st.session_state.login_errors = {}
            st.rerun()


current_user = st.session_state.current_user

if current_user is not None:
    show_signed_in_screen(current_user)
else:
    # -----------------------------------------------------------------------
    # ORIGINAL PAWMATCH LOGIN INTERFACE
    # -----------------------------------------------------------------------
    with st.container(key="auth_card"):
        # The original login uses a slightly wider pink panel than form panel.
        left, right = st.columns([1.05, 0.95], gap="large")

        with left:
            # This branded panel introduces PawMatch before credentials are
            # requested and repeats the benefits shown in the full application.
            with st.container(key="login_pink_panel"):
                st.markdown(
                    """
                    <div class="paw-logo">🐾</div>
                    <p class="eyebrow">PawMatch</p>
                    <h1 class="brand-title">Find a companion who fits your life.</h1>
                    <p class="brand-copy">
                        PawMatch compares an animal's needs with your home and lifestyle
                        so that suitability comes before appearance.
                    </p>
                    <p class="benefit"><span class="tick">✓</span>Personalised compatibility scores</p>
                    <p class="benefit"><span class="tick">✓</span>Clear reasons behind every match</p>
                    <p class="benefit"><span class="tick">✓</span>Animal welfare placed first</p>
                    """,
                    unsafe_allow_html=True,
                )

        with right:
            # The form panel contains the same text, fields and navigation
            # action as the original PawMatch login screen.
            with st.container(key="login_form_panel"):
                st.markdown(
                    """
                    <p class="eyebrow" style="color:#dc548e;">Welcome back</p>
                    <h2 class="form-title">Login to continue</h2>
                    <p class="form-copy">
                        Enter your email address or administrator username and password.
                    </p>
                    """,
                    unsafe_allow_html=True,
                )

                previous_errors = st.session_state.login_errors

                # Grouping the fields prevents authentication from running until
                # the Log in button is pressed.
                with st.form("login_form", clear_on_submit=False, border=False):
                    # R5 FIELD 1 — EMAIL ADDRESS OR ADMIN USERNAME
                    # The container key changes when validation fails so CSS can
                    # apply a red border to the affected field.
                    with st.container(
                        key=(
                            "login_identifier_error"
                            if (
                                "identifier" in previous_errors
                                or "credentials" in previous_errors
                            )
                            else "login_identifier_field"
                        )
                    ):
                        identifier = st.text_input(
                            "Email address or username",
                            placeholder="name@example.com or admin123",
                            key="login_identifier",
                            autocomplete="username",
                        )
                        if "identifier" in previous_errors:
                            st.markdown(
                                f'<p class="field-error">'
                                f'{previous_errors["identifier"]}</p>',
                                unsafe_allow_html=True,
                            )

                    # R5 FIELD 2 — PASSWORD
                    # The input is masked and used only for Argon2id verification.
                    # It is not retained in session state after a successful login.
                    with st.container(
                        key=(
                            "login_password_error"
                            if (
                                "password" in previous_errors
                                or "credentials" in previous_errors
                            )
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
                        message = previous_errors.get(
                            "password",
                            previous_errors.get("credentials"),
                        )
                        if message:
                            st.markdown(
                                f'<p class="field-error">{message}</p>',
                                unsafe_allow_html=True,
                            )

                    submitted = st.form_submit_button(
                        "Log in",
                        type="primary",
                        icon=":material/login:",
                        width="stretch",
                    )

                if submitted:
                    # auth.py performs format checking, a parameterised database
                    # lookup and Argon2id password verification. Unknown accounts
                    # and incorrect passwords receive the same generic message.
                    errors, authenticated_user = authenticate_user(
                        identifier,
                        password,
                    )

                    if errors:
                        st.session_state.login_errors = errors
                        st.rerun()

                    # Store only safe account data for the authenticated session.
                    # The database role controls adopter/admin access for R6.
                    st.session_state.login_errors = {}
                    st.session_state.current_user = authenticated_user
                    st.rerun()

                st.markdown(
                    '<div class="divider"><span>New to PawMatch?</span></div>',
                    unsafe_allow_html=True,
                )

                # Since both files are registered by app.py, Streamlit can move
                # to registration without exposing a navigation sidebar.
                if st.button(
                    "Create an account",
                    key="secondary_button",
                    width="stretch",
                ):
                    st.switch_page("registration.py")
