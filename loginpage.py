import re
import streamlit as st

st.set_page_config(
    page_title="PawMatch | Login",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------- LOGIN LOGIC -----------------------
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validate_login(email, password):
    """Check the main login inputs."""
    email = email.strip().lower()
    errors = []

    if email == "":
        errors.append("Enter your email address.")
    elif EMAIL_PATTERN.fullmatch(email) is None:
        errors.append("Enter a valid email address, such as name@example.com.")

    if password == "":
        errors.append("Enter your password.")

    return errors, email


def authenticate_user(email, password):
    """Temporary test login. Replace this with the SQLite check later."""
    return email == "demo@pawmatch.com" and password == "Password123!"


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""


# ----------------------- PINK STYLING -----------------------
st.markdown(
    """
    <style>
    :root {
        --pink: #ed4f91;
        --dark-pink: #d93679;
        --pale-pink: #fff4f9;
        --border-pink: #f3bfd4;
        --dark-text: #4b2338;
        --muted-text: #806170;
    }

    .stApp {
        background:
            radial-gradient(circle at 10% 10%, #ffc9df 0, transparent 28%),
            radial-gradient(circle at 90% 85%, #f8bad3 0, transparent 25%),
            linear-gradient(135deg, #fffafd, #ffe8f2);
        color: var(--dark-text);
    }

    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stDecoration"] { display: none; }

    .block-container {
        max-width: 1100px;
        padding-top: 3rem;
        padding-bottom: 2rem;
    }

    .st-key-login_card {
        padding: 12px;
        border: 1px solid rgba(237, 79, 145, 0.18);
        border-radius: 30px;
        background: rgba(255, 255, 255, 0.88);
        box-shadow: 0 28px 70px rgba(121, 35, 74, 0.16);
    }

    .st-key-pink_panel {
        min-height: 540px;
        padding: 3rem 2.6rem;
        border-radius: 24px;
        background:
            radial-gradient(circle at 88% 12%, rgba(255,255,255,.25), transparent 22%),
            linear-gradient(145deg, #f985b2, #ed4f91 50%, #d93679);
        color: white;
    }

    .st-key-form_panel {
        min-height: 540px;
        padding: 2.6rem 2rem 2rem;
    }

    .paw-logo {
        width: 58px;
        height: 58px;
        display: grid;
        place-items: center;
        margin-bottom: 2rem;
        border: 1px solid rgba(255,255,255,.28);
        border-radius: 18px;
        background: rgba(255,255,255,.20);
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
        color: white;
        font-size: clamp(2.3rem, 4vw, 3.45rem);
        line-height: 1.04;
        letter-spacing: -.045em;
    }

    .brand-copy {
        max-width: 430px;
        margin: 1.2rem 0 1.8rem;
        color: rgba(255,255,255,.86);
        line-height: 1.65;
    }

    .benefit {
        margin: .85rem 0;
        color: rgba(255,255,255,.95);
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
        background: rgba(255,255,255,.18);
    }

    .form-title {
        margin: 0;
        color: var(--dark-text);
        font-size: 2.1rem;
        line-height: 1.1;
        letter-spacing: -.035em;
    }

    .form-copy {
        margin: .7rem 0 1.5rem;
        color: var(--muted-text);
        line-height: 1.6;
    }

    [data-testid="stTextInput"] label {
        color: var(--dark-text);
        font-weight: 700;
    }

    div[data-baseweb="input"] {
        min-height: 48px;
        border: 1px solid var(--border-pink);
        border-radius: 13px;
        background: var(--pale-pink);
    }

    div[data-baseweb="input"]:focus-within {
        border-color: var(--pink);
        box-shadow: 0 0 0 4px rgba(237,79,145,.12);
    }

    div[data-baseweb="input"] > div { background: transparent; }

    .stFormSubmitButton button {
        min-height: 49px;
        margin-top: .35rem;
        border: 0;
        border-radius: 13px;
        background: linear-gradient(90deg, var(--pink), var(--dark-pink));
        color: white;
        font-weight: 800;
        box-shadow: 0 12px 26px rgba(217,54,121,.25);
    }

    .stFormSubmitButton button:hover {
        border: 0;
        color: white;
        transform: translateY(-1px);
    }

    .st-key-register_button button,
    .st-key-logout_button button {
        min-height: 47px;
        border: 1px solid var(--border-pink);
        border-radius: 13px;
        background: white;
        color: var(--dark-pink);
        font-weight: 750;
    }

    .divider {
        display: flex;
        align-items: center;
        gap: .8rem;
        margin: 1.2rem 0 .8rem;
        color: #a98a99;
        font-size: .82rem;
    }

    .divider::before, .divider::after {
        content: "";
        height: 1px;
        flex: 1;
        background: #f1d5e1;
    }

    .demo-box {
        margin-top: .9rem;
        padding: .75rem .9rem;
        border: 1px dashed #efb5cd;
        border-radius: 12px;
        background: #fff7fb;
        color: #775162;
        font-size: .8rem;
        line-height: 1.5;
    }

    .st-key-success_card {
        max-width: 600px;
        margin: 5rem auto 0;
        padding: 3rem;
        border-radius: 27px;
        background: rgba(255,255,255,.92);
        text-align: center;
        box-shadow: 0 24px 60px rgba(121,35,74,.14);
    }

    @media (max-width: 850px) {
        .block-container { padding-top: 1rem; }
        .st-key-pink_panel { min-height: auto; padding: 2rem; }
        .st-key-form_panel { min-height: auto; padding: 2rem 1.2rem; }
        .brand-title { font-size: 2.3rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------- PAGE CONTENT -----------------------
if st.session_state.logged_in:
    with st.container(key="success_card"):
        st.markdown("# 🐾 Login successful")
        st.write(f"Welcome back, **{st.session_state.user_email}**.")
        st.caption("Replace this screen with your user homepage later.")

        if st.button("Log out", key="logout_button", width="stretch"):
            st.session_state.logged_in = False
            st.session_state.user_email = ""
            st.rerun()

else:
    with st.container(key="login_card"):
        left, right = st.columns([1.05, 0.95], gap="large")

        with left:
            with st.container(key="pink_panel"):
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
            with st.container(key="form_panel"):
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

                with st.form("login_form", clear_on_submit=False):
                    email = st.text_input(
                        "Email address",
                        placeholder="name@example.com",
                    )
                    password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Enter your password",
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
                        st.error("\n".join(f"• {error}" for error in errors))
                    elif authenticate_user(cleaned_email, password):
                        st.session_state.logged_in = True
                        st.session_state.user_email = cleaned_email

                        # Later, you can redirect to a multipage homepage instead:
                        # st.switch_page("pages/1_Home.py")
                        st.rerun()
                    else:
                        st.error("The email address or password is incorrect.")

                st.markdown(
                    '<div class="divider"><span>New to PawMatch?</span></div>',
                    unsafe_allow_html=True,
                )

                if st.button(
                    "Create an account",
                    key="register_button",
                    width="stretch",
                ):
                    st.info(
                        "Later connect this to your registration page with "
                        '`st.switch_page("pages/2_Registration.py")`.'
                    )

                st.markdown(
                    """
                    <div class="demo-box">
                        <strong>Temporary test login</strong><br>
                        Email: demo@pawmatch.com<br>
                        Password: Password123!
                    </div>
                    """,
                    unsafe_allow_html=True,
                )