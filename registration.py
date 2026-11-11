"""PawMatch registration page isolated for the development documentation.

This is the registration interface used by the full PawMatch application. It
keeps the same pink two-column layout, field-level errors and success screen.
Run the connected login and registration pages on the development branch with:

    streamlit run app.py
"""

import streamlit as st

from auth import register_user
from database import create_database


# ---------------------------------------------------------------------------
# DATABASE SETUP
# ---------------------------------------------------------------------------
# app.py owns the shared Streamlit page configuration and hidden navigation.
# The registration page can still initialise its required database safely.
# CREATE TABLE IF NOT EXISTS is repeatable, so existing test users are retained.
create_database()


def apply_registration_style() -> None:
    """Apply the same pink styling used by the full PawMatch interface.

    The full application stores this CSS in pawmatch_style.py so several pages
    can share it. It is included here to keep this development-stage file
    self-contained while preserving the appearance of the original page.
    """
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

        .st-key-register_pink_panel {
            min-height: 735px;
            padding: 3rem 2.6rem;
            border: 1px solid rgba(184, 76, 124, .16);
            border-radius: 20px;
            background: var(--brand-panel);
            color: var(--dark-text);
        }

        .st-key-register_form_panel {
            min-height: 735px;
            padding: 2.15rem 2rem 1.5rem;
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

        [data-testid="stTextInput"] label,
        [data-testid="stNumberInput"] label {
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

        .st-key-name_error div[data-baseweb="input"],
        .st-key-email_error div[data-baseweb="input"],
        .st-key-age_error div[data-baseweb="input"],
        .st-key-password_error div[data-baseweb="input"],
        .st-key-confirm_password_error div[data-baseweb="input"] {
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

        .password-hint {
            margin: -.25rem 0 .55rem;
            color: #967584;
            font-size: .76rem;
            line-height: 1.4;
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
        .st-key-login_button button {
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

        .privacy-note {
            margin-top: .7rem;
            padding: .7rem .85rem;
            border: 1px dashed #efb5cd;
            border-radius: 12px;
            background: #fff7fb;
            color: #775162;
            font-size: .77rem;
            line-height: 1.45;
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
            .st-key-register_pink_panel {
                min-height: auto;
                padding: 2rem;
            }
            .st-key-register_form_panel {
                min-height: auto;
                padding: 2rem 1.15rem;
            }
            .brand-title { font-size: 2.25rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# Apply the appearance before drawing the interface so users do not see the
# default theme flash before the branded registration card is displayed.
apply_registration_style()


# ---------------------------------------------------------------------------
# SESSION-STATE SETUP
# ---------------------------------------------------------------------------
# These are the exact keys used by the five widgets. Keeping them together
# makes it safe to clear the form after a successful manual test.
REGISTRATION_WIDGET_KEYS = (
    "registration_name",
    "registration_email",
    "registration_age",
    "registration_password",
    "registration_confirm_password",
)

# A successful submission sets this flag. The old widget values must be
# removed before the widgets are created on the next run; Streamlit does not
# permit changing a widget's session value after that widget has been drawn.
if st.session_state.pop("clear_registration_fields", False):
    for widget_key in REGISTRATION_WIDGET_KEYS:
        st.session_state.pop(widget_key, None)

# Session state survives Streamlit reruns. It holds only interface status and
# safe account details—never the plaintext password or stored password hash.
st.session_state.setdefault("registration_complete", False)
st.session_state.setdefault("registration_errors", {})
st.session_state.setdefault("registered_name", "")
st.session_state.setdefault("registered_email", "")


if st.session_state.registration_complete:
    # -----------------------------------------------------------------------
    # SUCCESS SCREEN
    # -----------------------------------------------------------------------
    # This card is only rendered after the account has passed validation and
    # the database INSERT has committed successfully.
    with st.container(key="success_card"):
        st.markdown("# 🎉 Account created")
        st.write(
            f"Welcome to PawMatch, **{st.session_state.registered_name}**. "
            f"Your account has been created for "
            f"**{st.session_state.registered_email}**."
        )
        st.caption(
            "The new row can now be inspected in pawmatch.db using DB Browser "
            "for SQLite."
        )

        # This restores the original success-screen route back to the login
        # interface. The account remains in SQLite so it can be tested there.
        if st.button(
            "Go to login",
            key="login_button",
            width="stretch",
        ):
            st.session_state.registration_complete = False
            st.session_state.registration_errors = {}
            st.session_state.clear_registration_fields = True
            st.switch_page("login.py")

else:
    # Any errors saved after the last submit are read before the form is drawn.
    # This lets the page give the affected field a red border as well as text.
    errors = st.session_state.registration_errors

    # auth_card is the white rounded card containing both interface columns.
    with st.container(key="auth_card"):
        # The original design uses a slightly narrower brand column and a
        # slightly wider form column. On small screens Streamlit stacks them.
        left, right = st.columns([0.92, 1.08], gap="large")

        with left:
            # ---------------------------------------------------------------
            # LEFT BRAND PANEL
            # ---------------------------------------------------------------
            # This is presentation content from the full PawMatch interface.
            # It explains the benefit of registering before asking for data.
            with st.container(key="register_pink_panel"):
                st.markdown(
                    """
                    <div class="paw-logo">🐾</div>
                    <p class="eyebrow">PawMatch</p>
                    <h1 class="brand-title">Find a companion who fits your life.</h1>
                    <p class="brand-copy">
                        Create an account to save your questionnaire and receive ranked
                        compatibility results.
                    </p>
                    <p class="benefit"><span class="tick">✓</span>Recommendations based on your lifestyle</p>
                    <p class="benefit"><span class="tick">✓</span>Securely stored account details</p>
                    <p class="benefit"><span class="tick">✓</span>Simple explanations for every result</p>
                    """,
                    unsafe_allow_html=True,
                )

        with right:
            # ---------------------------------------------------------------
            # RIGHT REGISTRATION FORM PANEL — REQUIREMENTS R1-R4
            # ---------------------------------------------------------------
            with st.container(key="register_form_panel"):
                st.markdown(
                    """
                    <p class="eyebrow" style="color:#dc548e;">Get started</p>
                    <h2 class="form-title">Create your account</h2>
                    <p class="form-copy">
                        Complete each field below. All fields are required.
                    </p>
                    """,
                    unsafe_allow_html=True,
                )

                # st.form groups all five fields into one transaction. The
                # validation/database code runs only when Create account is
                # pressed, not on every character typed by the user.
                with st.form(
                    "registration_form",
                    clear_on_submit=False,
                    border=False,
                ):
                    # R1 FIELD 1 — FULL NAME
                    # The container key changes when an error is present. The
                    # CSS uses that key to turn only this input border red.
                    with st.container(
                        key="name_error" if "name" in errors else "name_field"
                    ):
                        name = st.text_input(
                            "Full name",
                            placeholder="Enter your full name",
                            key="registration_name",
                            max_chars=50,
                            autocomplete="name",
                        )
                        if "name" in errors:
                            st.markdown(
                                f'<p class="field-error">{errors["name"]}</p>',
                                unsafe_allow_html=True,
                            )

                    # R1 FIELD 2 — EMAIL ADDRESS
                    # Email is the unique identifier for an adopter. auth.py
                    # normalises it and checks both its format and uniqueness.
                    with st.container(
                        key="email_error" if "email" in errors else "email_field"
                    ):
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

                    # R1 FIELD 3 — AGE
                    # value=None means the form begins blank. The widget blocks
                    # values outside 18-120, while auth.py repeats the check so
                    # security does not depend only on the visible interface.
                    with st.container(
                        key="age_error" if "age" in errors else "age_field"
                    ):
                        age = st.number_input(
                            "Age",
                            min_value=18,
                            max_value=120,
                            value=None,
                            step=1,
                            placeholder="Enter your age",
                            key="registration_age",
                            help=(
                                "Adopter accounts are available to users aged "
                                "18 or over."
                            ),
                        )
                        if "age" in errors:
                            st.markdown(
                                f'<p class="field-error">{errors["age"]}</p>',
                                unsafe_allow_html=True,
                            )

                    # R1 FIELD 4 — PASSWORD
                    # type=password masks the value on screen. register_user
                    # hashes it with Argon2id before the SQLite INSERT occurs.
                    with st.container(
                        key=(
                            "password_error"
                            if "password" in errors
                            else "password_field"
                        )
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
                            '<p class="password-hint">Use at least 8 characters.</p>',
                            unsafe_allow_html=True,
                        )
                        if "password" in errors:
                            st.markdown(
                                f'<p class="field-error">{errors["password"]}</p>',
                                unsafe_allow_html=True,
                            )

                    # R1 FIELD 5 — CONFIRM PASSWORD
                    # This value is compared with password to catch typing
                    # mistakes. It is never written to the database.
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
                                f'<p class="field-error">'
                                f'{errors["confirm_password"]}</p>',
                                unsafe_allow_html=True,
                            )

                    # This is the form's only submit action. The primary style
                    # makes the intended next step clear to the user.
                    submitted = st.form_submit_button(
                        "Create account",
                        type="primary",
                        icon=":material/person_add:",
                        width="stretch",
                    )

                if submitted:
                    # -------------------------------------------------------
                    # VALIDATION AND DATABASE PROCESSING
                    # -------------------------------------------------------
                    # register_user handles normalisation, validation, Argon2id
                    # hashing and the parameterised SQL INSERT in auth.py.
                    validation_errors, new_user = register_user(
                        name,
                        email,
                        age,
                        password,
                        confirm_password,
                    )

                    if validation_errors:
                        # Store errors before rerunning. The next run can then
                        # draw messages beside each relevant field and apply
                        # the red error-border container key.
                        st.session_state.registration_errors = validation_errors
                        st.rerun()

                    # A successful result contains only safe account details;
                    # neither the plaintext password nor its hash is returned.
                    st.session_state.registration_errors = {}
                    st.session_state.registration_complete = True
                    st.session_state.registered_name = new_user["name"]
                    st.session_state.registered_email = new_user["email"]
                    st.session_state.clear_registration_fields = True
                    st.rerun()

                # Restore the navigation from the original registration page.
                # Both pages are registered by app.py, so the button switches
                # pages without displaying a sidebar navigation menu.
                st.markdown(
                    '<div class="divider"><span>Already have an account?</span></div>',
                    unsafe_allow_html=True,
                )

                if st.button(
                    "Back to login",
                    key="secondary_button",
                    width="stretch",
                ):
                    st.session_state.registration_errors = {}
                    st.switch_page("login.py")

                st.markdown(
                    """
                    <div class="privacy-note">
                        Passwords are converted into a salted Argon2id hash before
                        storage. The original password is never saved.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
