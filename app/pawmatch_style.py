"""Shared pink styling for the PawMatch login and registration pages."""

import streamlit as st


def apply_pawmatch_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --pink: #ed4f91;
            --dark-pink: #d93679;
            --deep-pink: #a92660;
            --pale-pink: #fff4f9;
            --border-pink: #f3bfd4;
            --dark-text: #4b2338;
            --muted-text: #806170;
            --error: #bd294b;
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
        [data-testid="stSidebar"] { display: none; }
        [data-testid="collapsedControl"] { display: none; }

        .block-container {
            max-width: 1160px;
            padding-top: 2.2rem;
            padding-bottom: 2rem;
        }

        .st-key-auth_card {
            padding: 12px;
            border: 1px solid rgba(237, 79, 145, 0.18);
            border-radius: 30px;
            background: rgba(255, 255, 255, 0.90);
            box-shadow: 0 28px 70px rgba(121, 35, 74, 0.16);
        }

        .st-key-login_pink_panel,
        .st-key-register_pink_panel {
            padding: 3rem 2.6rem;
            border-radius: 24px;
            background:
                radial-gradient(circle at 88% 12%, rgba(255,255,255,.25), transparent 22%),
                linear-gradient(145deg, #f985b2, #ed4f91 50%, #d93679);
            color: white;
        }

        .st-key-login_pink_panel { min-height: 570px; }
        .st-key-register_pink_panel { min-height: 735px; }
        .st-key-login_form_panel { min-height: 570px; padding: 2.5rem 2rem 2rem; }
        .st-key-register_form_panel { min-height: 735px; padding: 2.15rem 2rem 1.5rem; }

        .paw-logo {
            width: 58px;
            height: 58px;
            display: grid;
            place-items: center;
            margin-bottom: 1.8rem;
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
            font-size: clamp(2.25rem, 4vw, 3.35rem);
            line-height: 1.04;
            letter-spacing: -.045em;
        }

        .brand-copy {
            max-width: 430px;
            margin: 1.15rem 0 1.7rem;
            color: rgba(255,255,255,.88);
            line-height: 1.65;
        }

        .benefit {
            margin: .85rem 0;
            color: rgba(255,255,255,.96);
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
            border-radius: 13px;
            background: var(--pale-pink);
        }

        div[data-baseweb="input"]:focus-within {
            border-color: var(--pink);
            box-shadow: 0 0 0 4px rgba(237,79,145,.12);
        }

        div[data-baseweb="input"] > div { background: transparent; }

        .st-key-name_error div[data-baseweb="input"],
        .st-key-email_error div[data-baseweb="input"],
        .st-key-age_error div[data-baseweb="input"],
        .st-key-password_error div[data-baseweb="input"],
        .st-key-confirm_password_error div[data-baseweb="input"],
        .st-key-login_email_error div[data-baseweb="input"],
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

        .password-hint {
            margin: -.25rem 0 .55rem;
            color: #967584;
            font-size: .76rem;
            line-height: 1.4;
        }

        .stFormSubmitButton button {
            min-height: 49px;
            margin-top: .25rem;
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

        .st-key-secondary_button button,
        .st-key-logout_button button,
        .st-key-login_button button {
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
            .st-key-login_pink_panel,
            .st-key-register_pink_panel {
                min-height: auto;
                padding: 2rem;
            }
            .st-key-login_form_panel,
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


def apply_dashboard_style() -> None:
    """Apply the shared pink theme plus styles used by the user dashboard."""
    apply_pawmatch_style()
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1280px;
            padding-top: 1.15rem;
            padding-bottom: 3rem;
        }

        .st-key-dashboard_topbar {
            margin-bottom: 1.15rem;
            padding: .72rem .85rem;
            border: 1px solid rgba(237,79,145,.16);
            border-radius: 20px;
            background: rgba(255,255,255,.92);
            box-shadow: 0 13px 35px rgba(121,35,74,.09);
            backdrop-filter: blur(10px);
        }

        .dashboard-brand {
            display: flex;
            align-items: center;
            gap: .72rem;
            min-height: 43px;
            color: var(--dark-text);
        }

        .dashboard-brand-mark {
            display: grid;
            place-items: center;
            width: 43px;
            height: 43px;
            border-radius: 13px;
            background: linear-gradient(145deg, #f985b2, var(--dark-pink));
            color: white;
            font-size: 1.2rem;
            box-shadow: 0 9px 20px rgba(217,54,121,.22);
        }

        .dashboard-brand strong {
            display: block;
            font-size: 1.05rem;
            line-height: 1.1;
        }

        .dashboard-brand small {
            display: block;
            margin-top: .18rem;
            color: var(--muted-text);
            font-size: .70rem;
            font-weight: 650;
        }

        .st-key-top_questionnaire_button button,
        .st-key-top_animals_button button,
        .st-key-top_account_button button {
            min-height: 43px;
            border: 0;
            border-radius: 12px;
            background: transparent;
            color: #715160;
            font-size: .85rem;
            font-weight: 750;
            white-space: nowrap;
        }

        .st-key-top_questionnaire_button button:hover,
        .st-key-top_animals_button button:hover,
        .st-key-top_account_button button:hover {
            border: 0;
            background: #fff0f6;
            color: var(--dark-pink);
        }

        .st-key-top_logout_button button {
            min-height: 43px;
            border: 1px solid var(--border-pink);
            border-radius: 12px;
            background: white;
            color: var(--dark-pink);
            font-size: .84rem;
            font-weight: 800;
        }

        .st-key-dashboard_hero {
            position: relative;
            overflow: hidden;
            margin-bottom: 2rem;
            padding: 2.75rem 2.8rem;
            border-radius: 28px;
            background:
                radial-gradient(circle at 88% 10%, rgba(255,255,255,.27), transparent 24%),
                radial-gradient(circle at 10% 100%, rgba(255,255,255,.13), transparent 29%),
                linear-gradient(130deg, #f47ead, #ed4f91 52%, #d93679);
            color: white;
            box-shadow: 0 24px 55px rgba(166,38,94,.20);
        }

        .dashboard-eyebrow {
            margin: 0 0 .65rem;
            color: rgba(255,255,255,.82);
            font-size: .72rem;
            font-weight: 850;
            letter-spacing: .14em;
            text-transform: uppercase;
        }

        .pink-eyebrow { color: var(--dark-pink); }

        .st-key-dashboard_hero h1 {
            max-width: 680px;
            margin: 0;
            color: white;
            font-size: clamp(2.45rem, 4.7vw, 4rem);
            line-height: 1.02;
            letter-spacing: -.055em;
        }

        .dashboard-hero-copy {
            max-width: 700px;
            margin: 1.05rem 0 1.45rem;
            color: rgba(255,255,255,.91);
            font-size: 1.02rem;
            line-height: 1.65;
        }

        .st-key-hero_questionnaire_button button {
            min-height: 49px;
            border: 0;
            border-radius: 13px;
            background: white;
            color: var(--deep-pink);
            font-weight: 850;
            box-shadow: 0 12px 28px rgba(115,24,66,.19);
        }

        .st-key-hero_questionnaire_button button:hover {
            border: 0;
            background: #fff8fb;
            color: var(--deep-pink);
            transform: translateY(-1px);
        }

        .st-key-hero_browse_button button {
            min-height: 49px;
            border: 1px solid rgba(255,255,255,.43);
            border-radius: 13px;
            background: rgba(255,255,255,.12);
            color: white;
            font-weight: 800;
        }

        .st-key-hero_browse_button button:hover {
            border-color: rgba(255,255,255,.7);
            background: rgba(255,255,255,.20);
            color: white;
        }

        .next-step-card {
            margin-top: .1rem;
            padding: 1.55rem;
            border: 1px solid rgba(255,255,255,.35);
            border-radius: 21px;
            background: rgba(255,255,255,.16);
            box-shadow: inset 0 1px 0 rgba(255,255,255,.22);
            backdrop-filter: blur(12px);
        }

        .next-step-icon {
            display: grid;
            place-items: center;
            width: 45px;
            height: 45px;
            margin-bottom: 1rem;
            border-radius: 14px;
            background: rgba(255,255,255,.20);
            color: white;
            font-size: 1.5rem;
            font-weight: 900;
        }

        .next-step-label {
            margin: 0 0 .4rem;
            color: rgba(255,255,255,.74);
            font-size: .69rem;
            font-weight: 850;
            letter-spacing: .10em;
            text-transform: uppercase;
        }

        .next-step-card h3 {
            margin: 0;
            color: white;
            font-size: 1.35rem;
            line-height: 1.18;
        }

        .next-step-card > p:not(.next-step-label) {
            margin: .6rem 0 1.15rem;
            color: rgba(255,255,255,.84);
            font-size: .88rem;
            line-height: 1.5;
        }

        .next-step-meta {
            display: flex;
            justify-content: space-between;
            margin-bottom: .5rem;
            color: rgba(255,255,255,.88);
            font-size: .72rem;
            font-weight: 750;
        }

        .mini-progress {
            height: 8px;
            overflow: hidden;
            border-radius: 999px;
            background: rgba(255,255,255,.24);
        }

        .mini-progress span {
            display: block;
            height: 100%;
            border-radius: inherit;
            background: white;
        }

        .section-heading {
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 2rem;
            margin: 0 0 1.05rem;
        }

        .section-heading h2,
        .st-key-journey_card h2,
        .st-key-how_it_works_card h2 {
            margin: 0;
            color: var(--dark-text);
            font-size: 1.75rem;
            line-height: 1.12;
            letter-spacing: -.035em;
        }

        .section-heading > p {
            max-width: 430px;
            margin: 0 0 .1rem;
            color: var(--muted-text);
            font-size: .88rem;
            line-height: 1.5;
            text-align: right;
        }

        .st-key-questionnaire_action_card,
        .st-key-animals_action_card,
        .st-key-account_action_card {
            min-height: 302px;
            margin-bottom: 1.6rem;
            padding: 1.45rem;
            border: 1px solid rgba(237,79,145,.15);
            border-radius: 21px;
            background: rgba(255,255,255,.94);
            box-shadow: 0 15px 38px rgba(121,35,74,.09);
        }

        .st-key-questionnaire_action_card {
            border-color: rgba(237,79,145,.30);
            box-shadow: 0 17px 42px rgba(217,54,121,.13);
        }

        .action-icon {
            display: grid;
            place-items: center;
            width: 48px;
            height: 48px;
            margin-bottom: 1.15rem;
            border-radius: 15px;
            background: #fff0f6;
            color: var(--dark-pink);
            font-size: 1.35rem;
        }

        .action-icon-pink {
            background: linear-gradient(145deg, #f985b2, var(--dark-pink));
            color: white;
            box-shadow: 0 9px 20px rgba(217,54,121,.22);
        }

        .action-kicker {
            margin: 0 0 .35rem;
            color: var(--dark-pink);
            font-size: .68rem;
            font-weight: 850;
            letter-spacing: .09em;
            text-transform: uppercase;
        }

        .st-key-questionnaire_action_card h3,
        .st-key-animals_action_card h3,
        .st-key-account_action_card h3 {
            margin: 0;
            color: var(--dark-text);
            font-size: 1.25rem;
            letter-spacing: -.02em;
        }

        .action-copy {
            min-height: 95px;
            margin: .65rem 0 .95rem;
            color: var(--muted-text);
            font-size: .84rem;
            line-height: 1.57;
            overflow-wrap: anywhere;
        }

        .st-key-questionnaire_action_button button,
        .st-key-animals_action_button button,
        .st-key-account_action_button button {
            min-height: 45px;
            border-radius: 12px;
            font-size: .84rem;
            font-weight: 800;
        }

        .st-key-questionnaire_action_button button {
            border: 0;
            background: linear-gradient(90deg, var(--pink), var(--dark-pink));
            color: white;
            box-shadow: 0 10px 23px rgba(217,54,121,.20);
        }

        .st-key-animals_action_button button,
        .st-key-account_action_button button {
            border: 1px solid var(--border-pink);
            background: white;
            color: var(--dark-pink);
        }

        .st-key-journey_card,
        .st-key-how_it_works_card {
            min-height: 390px;
            padding: 1.65rem;
            border: 1px solid rgba(237,79,145,.15);
            border-radius: 22px;
            background: rgba(255,255,255,.94);
            box-shadow: 0 15px 38px rgba(121,35,74,.09);
        }

        .card-heading-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 1.05rem;
        }

        .progress-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 58px;
            padding: .43rem .72rem;
            border-radius: 999px;
            background: #fff0f6;
            color: var(--dark-pink);
            font-size: .78rem;
            font-weight: 850;
        }

        .st-key-journey_card [data-testid="stProgress"] {
            margin-bottom: 1.15rem;
        }

        .st-key-journey_card [data-testid="stProgress"] > div > div {
            background: linear-gradient(90deg, var(--pink), var(--dark-pink));
        }

        .journey-steps {
            display: grid;
            gap: .78rem;
        }

        .journey-step {
            display: flex;
            align-items: flex-start;
            gap: .8rem;
            padding: .75rem;
            border: 1px solid #f2dbe5;
            border-radius: 14px;
            background: #fffafb;
        }

        .journey-step > span {
            display: grid;
            place-items: center;
            flex: 0 0 29px;
            width: 29px;
            height: 29px;
            border-radius: 9px;
            background: #f5e8ee;
            color: #9b7a89;
            font-size: .75rem;
            font-weight: 850;
        }

        .journey-step.current {
            border-color: #efadca;
            background: #fff4f9;
        }

        .journey-step.current > span,
        .journey-step.complete > span {
            background: var(--pink);
            color: white;
        }

        .journey-step strong {
            display: block;
            color: var(--dark-text);
            font-size: .83rem;
        }

        .journey-step small {
            display: block;
            margin-top: .18rem;
            color: var(--muted-text);
            font-size: .73rem;
            line-height: 1.35;
        }

        .help-point {
            display: flex;
            align-items: flex-start;
            gap: .8rem;
            margin-top: 1rem;
            padding-top: 1rem;
            border-top: 1px solid #f3dce6;
        }

        .help-point > span {
            display: grid;
            place-items: center;
            flex: 0 0 31px;
            width: 31px;
            height: 31px;
            border-radius: 10px;
            background: #fff0f6;
            color: var(--dark-pink);
            font-size: .80rem;
            font-weight: 900;
        }

        .help-point strong {
            color: var(--dark-text);
            font-size: .84rem;
        }

        .help-point p {
            margin: .2rem 0 0;
            color: var(--muted-text);
            font-size: .76rem;
            line-height: 1.42;
        }

        @media (max-width: 1000px) {
            .st-key-dashboard_topbar [data-testid="stHorizontalBlock"] {
                gap: .25rem;
            }
            .st-key-top_questionnaire_button button,
            .st-key-top_animals_button button,
            .st-key-top_account_button button {
                font-size: .75rem;
            }
            .st-key-dashboard_hero { padding: 2.25rem; }
        }

        @media (max-width: 760px) {
            .block-container { padding-top: .7rem; }
            .st-key-dashboard_topbar { padding: .7rem; }
            .st-key-dashboard_hero { padding: 1.8rem 1.35rem; }
            .st-key-dashboard_hero h1 { font-size: 2.45rem; }
            .section-heading {
                display: block;
            }
            .section-heading > p {
                margin-top: .5rem;
                text-align: left;
            }
            .st-key-questionnaire_action_card,
            .st-key-animals_action_card,
            .st-key-account_action_card,
            .st-key-journey_card,
            .st-key-how_it_works_card {
                min-height: auto;
            }
            .action-copy { min-height: auto; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_sidebar_dashboard_style() -> None:
    """Apply the pink theme used by the dashboard with left navigation."""
    apply_pawmatch_style()
    st.markdown(
        """
        <style>
        /* Keep Streamlit's sidebar for a responsive navigation panel, but hide
           the automatically generated multipage links because this page uses
           its own labelled controls. */
        [data-testid="stSidebarNav"] {
            display: none;
        }

        [data-testid="stSidebar"] {
            display: block;
            min-width: 290px;
            max-width: 290px;
            background:
                radial-gradient(circle at 20% 8%, rgba(255,255,255,.62), transparent 26%),
                linear-gradient(180deg, #f7d8e7 0%, #f2c9dc 100%);
            border-right: 1px solid #e9b9cf;
        }

        [data-testid="stSidebarContent"] {
            padding: 1.15rem 1rem 1.25rem;
        }

        [data-testid="stSidebarHeader"] {
            min-height: 2.6rem;
        }

        [data-testid="collapsedControl"] {
            display: block;
        }

        [data-testid="collapsedControl"] button {
            color: #8b315d;
            background: #fff5fa;
            border: 1px solid #e9b9cf;
        }

        .stApp {
            background:
                radial-gradient(circle at 96% 12%, rgba(249, 186, 214, .32), transparent 27%),
                #fffafd;
        }

        .block-container {
            max-width: 1320px;
            padding-top: 2.2rem;
            padding-right: 2.4rem;
            padding-bottom: 2.4rem;
            padding-left: 2.4rem;
        }

        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: .8rem;
            padding: .75rem .65rem 1.15rem;
            border-bottom: 1px solid rgba(145, 61, 101, .16);
            margin-bottom: 1.1rem;
        }

        .sidebar-logo {
            display: grid;
            place-items: center;
            width: 50px;
            height: 50px;
            flex: 0 0 50px;
            border-radius: 16px;
            background: linear-gradient(145deg, #f77eb0, #d93679);
            color: white;
            font-size: 1.35rem;
            box-shadow: 0 10px 25px rgba(180, 53, 111, .24);
        }

        .sidebar-brand-name {
            margin: 0;
            color: #4b2338;
            font-size: 1.15rem;
            line-height: 1.15;
            font-weight: 850;
        }

        .sidebar-brand-subtitle {
            margin: .18rem 0 0;
            color: #8a6676;
            font-size: .73rem;
            font-weight: 650;
        }

        .sidebar-section-label {
            margin: .4rem .55rem .55rem;
            color: #a24a75;
            font-size: .69rem;
            font-weight: 850;
            letter-spacing: .11em;
            text-transform: uppercase;
        }

        [data-testid="stSidebar"] .stButton > button {
            min-height: 48px;
            margin-bottom: .26rem;
            justify-content: flex-start;
            padding: 0 .9rem;
            border: 1px solid transparent;
            border-radius: 13px;
            background: rgba(255,255,255,.58);
            color: #5e3549;
            font-size: .88rem;
            font-weight: 760;
            box-shadow: none;
        }

        [data-testid="stSidebar"] .stButton > button:hover {
            border-color: #e7a9c6;
            background: rgba(255,255,255,.91);
            color: #b92f6b;
        }

        [data-testid="stSidebar"] .st-key-nav_home button {
            border-color: #d93679;
            background: linear-gradient(90deg, #ea4c8c, #d93679);
            color: white;
            box-shadow: 0 10px 22px rgba(190, 55, 114, .22);
        }

        [data-testid="stSidebar"] .st-key-nav_home button:hover {
            border-color: #d93679;
            background: linear-gradient(90deg, #ea4c8c, #d93679);
            color: white;
        }

        [data-testid="stSidebar"] button:disabled {
            opacity: .54;
            color: #8f7180;
            background: rgba(255,255,255,.42);
        }

        .sidebar-user-card {
            display: flex;
            align-items: center;
            gap: .65rem;
            margin-top: 3.4rem;
            margin-bottom: .65rem;
            padding: .8rem;
            border: 1px solid rgba(172, 67, 116, .16);
            border-radius: 14px;
            background: rgba(255,255,255,.57);
        }

        .sidebar-user-icon {
            display: grid;
            place-items: center;
            width: 35px;
            height: 35px;
            border-radius: 11px;
            background: #fff3f8;
            font-size: .95rem;
        }

        .sidebar-user-card strong,
        .sidebar-user-card small {
            display: block;
            max-width: 168px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .sidebar-user-card strong {
            color: #553145;
            font-size: .82rem;
        }

        .sidebar-user-card small {
            margin-top: .12rem;
            color: #8d6b7b;
            font-size: .67rem;
        }

        [data-testid="stSidebar"] .st-key-nav_logout button {
            border-color: #dca5bf;
            background: transparent;
            color: #9c3c68;
        }

        .st-key-home_page_shell {
            padding: .4rem .2rem 0;
        }

        .home-heading {
            padding: .65rem 0 .15rem;
        }

        .home-eyebrow {
            margin: 0 0 .5rem;
            color: #d93679;
            font-size: .73rem;
            font-weight: 900;
            letter-spacing: .12em;
            text-transform: uppercase;
        }

        .home-heading h1 {
            margin: 0;
            color: #4b3f45;
            font-size: clamp(2.15rem, 4vw, 3.55rem);
            line-height: 1.05;
            letter-spacing: -.045em;
        }

        .home-subtitle {
            margin: .5rem 0 0;
            color: #dc76a6;
            font-size: clamp(1rem, 1.8vw, 1.3rem);
            font-weight: 720;
        }

        .home-introduction {
            max-width: 720px;
            margin: 1rem 0 0;
            color: #765d69;
            font-size: .98rem;
            line-height: 1.65;
        }

        .questionnaire-status-card {
            min-height: 178px;
            padding: 1.3rem 1.35rem;
            border: 1px solid #efbad2;
            border-radius: 20px;
            background: linear-gradient(150deg, #fff 0%, #fff2f8 100%);
            box-shadow: 0 15px 35px rgba(132, 49, 87, .09);
        }

        .status-card-topline,
        .status-progress-label {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }

        .status-card-topline span,
        .status-progress-label span {
            color: #9f5879;
            font-size: .67rem;
            font-weight: 850;
            letter-spacing: .08em;
            text-transform: uppercase;
        }

        .status-card-topline strong {
            padding: .3rem .58rem;
            border-radius: 999px;
            background: #fce2ee;
            color: #c53673;
            font-size: .7rem;
        }

        .questionnaire-status-card p {
            min-height: 48px;
            margin: .85rem 0 1rem;
            color: #755765;
            font-size: .84rem;
            line-height: 1.5;
        }

        .status-progress-label strong {
            color: #d93679;
            font-size: .78rem;
        }

        .status-progress-track {
            height: 9px;
            margin-top: .45rem;
            overflow: hidden;
            border-radius: 999px;
            background: #f3d7e4;
        }

        .status-progress-track span {
            display: block;
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg, #f36da4, #d93679);
        }

        .home-section-heading {
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 2rem;
            margin: 3.1rem 0 1.15rem;
        }

        .home-section-heading h2 {
            margin: 0;
            color: #4b3f45;
            font-size: clamp(1.6rem, 2.5vw, 2.15rem);
            line-height: 1.15;
            letter-spacing: -.025em;
        }

        .home-section-heading > p {
            max-width: 390px;
            margin: 0 0 .15rem;
            color: #8a737e;
            font-size: .85rem;
            line-height: 1.5;
            text-align: right;
        }

        .st-key-home_browse_card,
        .st-key-home_questionnaire_card,
        .st-key-home_matches_card {
            min-height: 325px;
            padding: 1.4rem 1.35rem 1.2rem;
            border-color: #ecd7e1 !important;
            border-radius: 20px !important;
            background: rgba(255,255,255,.96);
            box-shadow: 0 13px 32px rgba(119, 49, 82, .075);
        }

        .st-key-home_questionnaire_card {
            border-color: #ec93bb !important;
            background: linear-gradient(155deg, #fff 0%, #fff3f8 100%);
        }

        .home-action-icon {
            display: grid;
            place-items: center;
            width: 50px;
            height: 50px;
            margin-bottom: 1rem;
            border-radius: 15px;
            background: #fff0f7;
            font-size: 1.35rem;
        }

        .home-action-icon.primary-icon {
            background: linear-gradient(145deg, #f981b2, #e34f8f);
            box-shadow: 0 9px 20px rgba(218, 54, 121, .20);
        }

        .home-card-kicker {
            margin: 0 0 .4rem;
            color: #d24a84;
            font-size: .68rem;
            font-weight: 850;
            letter-spacing: .08em;
            text-transform: uppercase;
        }

        .st-key-home_browse_card h3,
        .st-key-home_questionnaire_card h3,
        .st-key-home_matches_card h3 {
            margin: 0;
            color: #533245;
            font-size: 1.28rem;
            line-height: 1.2;
        }

        .home-card-copy {
            min-height: 103px;
            margin: .75rem 0 .9rem;
            color: #7b6570;
            font-size: .84rem;
            line-height: 1.58;
        }

        .st-key-home_browse_button button,
        .st-key-home_matches_button button {
            min-height: 46px;
            border: 1px solid #e9a8c5;
            border-radius: 12px;
            background: #fff8fb;
            color: #c23673;
            font-weight: 800;
        }

        .st-key-home_questionnaire_button button {
            min-height: 46px;
            border: 0;
            border-radius: 12px;
            background: linear-gradient(90deg, #ed4f91, #d93679);
            color: white;
            font-weight: 850;
            box-shadow: 0 10px 22px rgba(217,54,121,.21);
        }

        .st-key-home_matches_button button:disabled {
            border-color: #e4d7dd;
            background: #f1edef;
            color: #a79aa0;
        }

        .why-heading {
            margin-top: 3.4rem;
        }

        .reason-card {
            min-height: 215px;
            padding: 1.4rem 1.25rem;
            border: 1px solid #efdbe4;
            border-radius: 18px;
            background: rgba(255,255,255,.68);
            text-align: center;
        }

        .reason-icon {
            display: grid;
            place-items: center;
            width: 66px;
            height: 66px;
            margin: 0 auto 1rem;
            border: 1px solid #e291b6;
            border-radius: 50%;
            background: linear-gradient(145deg, #ffd8e9, #f7afd0);
            color: #7f3458;
            font-size: 1.45rem;
            font-weight: 900;
            box-shadow: 0 9px 20px rgba(155, 62, 105, .10);
        }

        .reason-card h3 {
            margin: 0;
            color: #57364a;
            font-size: 1.08rem;
        }

        .reason-card p {
            margin: .65rem auto 0;
            color: #806b75;
            font-size: .82rem;
            line-height: 1.55;
        }

        .dashboard-footer {
            display: flex;
            justify-content: space-between;
            gap: 1.5rem;
            margin-top: 3rem;
            padding-top: 1.1rem;
            border-top: 1px solid #efd9e3;
            color: #9b7f8c;
            font-size: .73rem;
        }

        .dashboard-footer span:first-child {
            color: #d93679;
            font-weight: 850;
        }

        @media (max-width: 980px) {
            [data-testid="stSidebar"] {
                min-width: 270px;
                max-width: 270px;
            }

            .block-container {
                padding-right: 1.25rem;
                padding-left: 1.25rem;
            }

            .home-section-heading {
                display: block;
            }

            .home-section-heading > p {
                margin-top: .55rem;
                text-align: left;
            }
        }

        @media (max-width: 700px) {
            .block-container {
                padding-top: 1rem;
            }

            .home-heading h1 {
                font-size: 2.15rem;
            }

            .home-introduction {
                font-size: .9rem;
            }

            .dashboard-footer {
                display: block;
            }

            .dashboard-footer span {
                display: block;
                margin-bottom: .35rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_questionnaire_matches_style(active_page: str) -> None:
    """Apply the interface-design typography and layout to all signed-in pages."""
    apply_pawmatch_style()
    active_key = {
        "home": "flow_nav_home",
        "browse": "flow_nav_animals",
        "questionnaire": "flow_nav_questionnaire",
        "account": "flow_nav_account",
        "matches": "flow_nav_account",
    }.get(active_page, "flow_nav_home")
    st.markdown(
        """
        <style>
        .stApp, .stApp button, .stApp input, .stApp select {
            font-family: "Avenir Next", "Nunito", Arial, sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 92% 8%, rgba(252, 207, 232, .72), transparent 27%),
                linear-gradient(135deg, #fffafd 0%, #fff0f8 100%);
            color: #454047;
        }

        .block-container {
            width: calc(100% - 1.5rem);
            max-width: 1500px;
            padding: .75rem .75rem 1.25rem;
        }

        .st-key-design_sidebar {
            min-height: calc(100vh - 1.5rem);
            padding: 1.45rem 1.45rem;
            border: 1px solid #ead6e0;
            border-radius: 3px 0 0 3px;
            background: rgba(253, 244, 249, .88);
        }

        .flow-brand {
            display: flex;
            align-items: center;
            gap: .65rem;
            min-height: 64px;
            margin-bottom: 3.5rem;
            padding: .65rem .75rem;
            border: 1px solid #bfaeb7;
            background: rgba(255,255,255,.48);
        }

        .flow-brand-mark {
            display: grid;
            place-items: center;
            width: 35px;
            height: 35px;
            border-radius: 11px;
            background: #db4f8c;
            color: white;
            font-size: 1rem;
        }

        .flow-brand strong, .flow-brand small { display: block; }
        .flow-brand strong { color: #282329; font-size: 1rem; font-weight: 800; }
        .flow-brand small { margin-top: .08rem; color: #8a727e; font-size: .7rem; }

        .st-key-design_sidebar .stButton > button {
            min-height: 49px;
            margin-bottom: .42rem;
            border: 1px solid #efb7d0;
            border-radius: 8px;
            background: rgba(255,255,255,.34);
            color: #272329;
            font-size: 1rem;
            font-weight: 700;
            box-shadow: none;
        }

        .st-key-design_sidebar .stButton > button:hover {
            border-color: #dc4f8c;
            background: #fff8fb;
            color: #ba326f;
        }

        .st-key-flow_logout { margin-top: 13rem; }
        .st-key-flow_logout button { background: transparent !important; }

        .st-key-design_main {
            min-height: calc(100vh - 1.5rem);
            padding: 2.7rem 2.35rem 2.4rem;
            border: 1px solid #ead6e0;
            border-left: 0;
            border-radius: 0 3px 3px 0;
            background: rgba(255,250,253,.36);
        }

        .flow-page-header {
            display: flex;
            align-items: start;
            justify-content: space-between;
            gap: 1rem;
        }

        .flow-page-header h1 {
            margin: 0;
            color: #4a454b;
            font-size: 2.25rem !important;
            line-height: 1.08 !important;
            letter-spacing: -.035em;
            font-weight: 750 !important;
        }

        .flow-page-header p {
            margin: .35rem 0 0;
            color: #948b91;
            font-size: .9rem !important;
            font-weight: 500;
        }

        .flow-page-header > span {
            padding-top: .18rem;
            color: #c06a92;
            font-size: .61rem !important;
            white-space: nowrap;
        }

        .flow-progress {
            height: 8px;
            margin: .7rem 0 1.5rem;
            overflow: hidden;
            border-radius: 999px;
            background: #ecd9e3;
        }

        .flow-progress span {
            display: block;
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg, #cf3e7d, #df5b96);
        }

        .st-key-question_card {
            min-height: 310px;
            padding: 1.55rem 1.4rem 1.25rem;
            border: 1px solid #d9ccd2;
            border-radius: 42px;
            background: rgba(255,255,255,.96);
            box-shadow: 0 6px 12px rgba(70,48,59,.18);
        }

        .question-prompt {
            margin: 0 0 1.5rem;
            color: #161317;
            font-size: 1rem !important;
            line-height: 1.35;
            font-weight: 750;
        }

        [class*="st-key-choice_"] button {
            min-height: 112px;
            padding: .8rem .75rem;
            border: 1px solid #efd5e2;
            border-radius: 18px;
            background: #fbe9f4;
            color: #4a3b43;
            font-size: .72rem;
            font-weight: 650;
            line-height: 1.55;
            box-shadow: 0 4px 6px rgba(76,51,64,.18);
        }

        [class*="st-key-choice_"] button:hover {
            border-color: #d74d89;
            background: #fae4f0;
            color: #352c31;
        }

        .question-help {
            margin: -.9rem 0 1rem;
            color: #9b8992;
            font-size: .68rem;
        }

        .st-key-question_hours [data-baseweb="input"] {
            min-height: 58px;
            border: 2px solid #e8abc7;
            border-radius: 15px;
            background: #fff7fb;
        }

        .st-key-question_hours label {
            color: #654b58;
            font-size: .72rem;
            font-weight: 700;
        }

        .st-key-flow_back button,
        .st-key-flow_next button,
        .st-key-flow_submit button {
            min-height: 47px;
            margin-top: 1rem;
            border-radius: 8px;
            font-size: .72rem;
            font-weight: 800;
        }

        .st-key-flow_back button {
            border: 1px solid #d6538e;
            background: white;
            color: #c4427e;
        }

        .st-key-flow_next button,
        .st-key-flow_submit button {
            border: 1px solid #d84d8b;
            background: #d84d8b;
            color: white;
        }

        .st-key-flow_next button:disabled,
        .st-key-flow_submit button:disabled {
            border-color: #e1ccd6;
            background: #e9dde3;
            color: #a58f99;
        }

        .matches-heading { margin-bottom: 1.2rem; }

        .match-card {
            display: grid;
            grid-template-columns: 42px 190px minmax(340px, 1fr) 175px;
            align-items: center;
            gap: 1rem;
            min-height: 245px;
            margin-bottom: 1.15rem;
            padding: 1.1rem 1.25rem;
            border: 1px solid #d8ced3;
            border-radius: 24px;
            background: rgba(255,255,255,.97);
            box-shadow: 0 5px 9px rgba(65,45,55,.20);
        }

        .match-rank {
            align-self: start;
            display: grid;
            place-items: center;
            width: 30px;
            height: 30px;
            border-radius: 1px;
            background: #d84d8b;
            color: white;
            font-size: 1rem;
        }

        .match-photo {
            display: grid;
            place-items: center;
            width: 190px;
            height: 165px;
            padding: .6rem;
            overflow: hidden;
            border-radius: 18px;
            background: linear-gradient(145deg, #f9c7e2, #f2d1e2);
            font-size: 4rem;
        }

        .match-card:nth-of-type(odd) .match-photo {
            background: linear-gradient(145deg, #ded7ef, #f2dceb);
        }

        .match-name {
            margin: 0;
            color: #595158;
            font-size: 1.7rem !important;
            line-height: 1.05 !important;
            font-weight: 750 !important;
        }

        .match-meta {
            margin: .18rem 0 .8rem;
            color: #d04e88;
            font-size: .82rem !important;
            font-weight: 550;
        }

        .match-reason {
            margin: .55rem 0;
            padding: .65rem .75rem;
            border-radius: 8px;
            color: #77947d;
            background: #eef8ee;
            font-size: .92rem !important;
            line-height: 1.5;
        }

        .match-reason.consideration {
            color: #947b53;
            background: #fff6e6;
        }

        .requirement-heading {
            display: block;
            margin-bottom: .28rem;
            color: inherit;
            font-size: 1rem;
            font-weight: 850;
        }

        .requirement-line {
            display: block;
            margin: .22rem 0;
        }

        .match-score-area { text-align: center; }
        .match-category { margin-bottom: .55rem; color: #c75a8b; font-size: .8rem !important; font-weight: 750; }
        .score-ring {
            display: grid;
            place-items: center;
            width: 76px;
            height: 76px;
            margin: 0 auto .6rem;
            border-radius: 50%;
            color: #cf4c88;
            font-size: 1.05rem;
            font-weight: 800;
        }

        .score-ring span {
            display: grid;
            place-items: center;
            width: 64px;
            height: 64px;
            border-radius: 50%;
            background: white;
        }

        .profile-button {
            display: block;
            padding: .66rem .45rem;
            border-radius: 7px;
            background: #d84d8b;
            color: white !important;
            font-size: .78rem !important;
            font-weight: 750;
            text-align: center;
            text-decoration: none !important;
        }

        .no-matches-card {
            padding: 2rem;
            border: 1px solid #e6c8d7;
            border-radius: 22px;
            background: white;
            color: #705a65;
            font-size: .85rem;
        }

        .page-back-row { margin-bottom: .85rem; }
        .st-key-page_back button,
        .st-key-profile_back button {
            min-height: 38px;
            border: 1px solid #dc5b92;
            border-radius: 8px;
            background: white;
            color: #c5417b;
            font-size: .7rem;
            font-weight: 800;
        }

        .completion-card {
            max-width: 660px;
            margin: 2rem auto;
            padding: 2.4rem;
            border: 1px solid #dfc2d0;
            border-radius: 32px;
            background: white;
            text-align: center;
            box-shadow: 0 8px 18px rgba(72,45,59,.16);
        }
        .completion-card .completion-icon { font-size: 2.5rem; }
        .completion-card h1 { margin: .5rem 0; font-size: 1.8rem !important; color: #4b4147; }
        .completion-card p { color: #8b7882; font-size: .78rem; }
        .st-key-view_matches_primary button {
            min-height: 48px;
            border: 1px solid #d84d8b;
            border-radius: 8px;
            background: #d84d8b;
            color: white;
            font-weight: 800;
        }

        .st-key-browse_filter_card {
            margin: 1.2rem 0;
            padding: 1rem 1.15rem;
            border: 1px solid #ddd0d6;
            border-radius: 12px;
            background: rgba(255,255,255,.96);
            box-shadow: 0 4px 10px rgba(70,48,59,.08);
        }
        .browse-section-title { margin: 1rem 0 .7rem; color: #4c4549; font-size: .92rem; font-weight: 800; }
        [class*="st-key-animal_card_"] {
            min-height: 390px;
            padding: .8rem;
            border: 1px solid #ddcfd6;
            border-radius: 20px;
            background: white;
            box-shadow: 0 5px 10px rgba(65,45,55,.12);
        }
        [class*="st-key-animal_card_"] [data-testid="stImage"] img {
            height: 155px;
            object-fit: contain;
            border-radius: 14px;
            background: linear-gradient(145deg, #f9d9e8, #f4e9f1);
        }
        .animal-card-copy h3 { margin: .35rem 0 .12rem; color: #4d464a; font-size: 1.05rem; }
        .animal-card-copy .animal-breed { margin: 0 0 .4rem; color: #cf4d88; font-size: .64rem; }
        .animal-card-copy .animal-facts { margin: 0 0 .55rem; color: #6e6268; font-size: .62rem; }
        .animal-card-copy .animal-description { min-height: 48px; color: #8b7c84; font-size: .61rem; line-height: 1.45; }
        [class*="st-key-view_profile_"] button {
            min-height: 38px;
            border: 1px solid #d84d8b;
            border-radius: 7px;
            background: #d84d8b;
            color: white;
            font-size: .65rem;
            font-weight: 800;
        }

        .profile-title h1 { margin: 0; color: #4c4549; font-size: 1.85rem !important; }
        .profile-title p { margin: .25rem 0 1.25rem; color: #cf4d88; font-size: .7rem; }
        .profile-description { color: #786b72; font-size: .75rem; line-height: 1.65; }
        .profile-fact {
            padding: .75rem;
            border: 1px solid #ead3df;
            border-radius: 10px;
            background: #fff6fa;
            text-align: center;
            color: #685b62;
            font-size: .66rem;
        }
        .profile-fact strong { display: block; color: #d24986; font-size: .78rem; }
        .needs-card, .account-card {
            margin-top: 1.2rem;
            padding: 1.2rem;
            border: 1px solid #ddd0d6;
            border-radius: 17px;
            background: white;
            box-shadow: 0 4px 10px rgba(70,48,59,.08);
        }
        .needs-card h2, .account-card h2 { margin: 0 0 .8rem; color: #51484d; font-size: 1rem !important; }
        .need-line, .account-line { margin: .45rem 0; color: #75656d; font-size: .7rem; }
        .need-line strong, .account-line strong { color: #4e4449; }
        .account-avatar { font-size: 2.4rem; }

        .match-photo img {
            display: block;
            width: auto !important;
            height: auto !important;
            max-width: 100% !important;
            max-height: 100% !important;
            object-fit: contain !important;
            object-position: center !important;
        }

        @media (max-width: 900px) {
            .st-key-design_sidebar { min-height: auto; }
            .st-key-flow_logout { margin-top: 1rem; }
            .st-key-design_main { border-left: 1px solid #ead6e0; }
            .match-card { grid-template-columns: 30px 110px 1fr; }
            .match-score-area { grid-column: 2 / -1; display: flex; align-items: center; gap: 1rem; }
            .score-ring { margin: 0; }
        }

        @media (max-width: 650px) {
            .block-container { padding: .65rem; }
            .st-key-design_main { padding: 1.4rem .85rem; }
            .flow-page-header h1 { font-size: 1.55rem; }
            .st-key-question_card { border-radius: 26px; }
            .match-card { grid-template-columns: 30px 1fr; }
            .match-photo { width: 165px; height: 150px; font-size: 3rem; }
            .match-details, .match-score-area { grid-column: 1 / -1; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <style>
        .st-key-{active_key} button,
        .st-key-{active_key} button:hover {{
            border-color: #eaa5c3 !important;
            background: #f3b8d5 !important;
            color: #241f24 !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_questionnaire_matches_sidebar() -> None:
    """Render the persistent navigation shown throughout the interface design."""
    st.markdown(
        """
        <div class="flow-brand">
            <span class="flow-brand-mark">🐾</span>
            <span><strong>PawMatch</strong><small>Adoption matching</small></span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Home", key="flow_nav_home", width="stretch"):
        st.switch_page("pages/1_Home.py")
    if st.button("Browse animals", key="flow_nav_animals", width="stretch"):
        st.switch_page("pages/4_Browse_Animals.py")
    if st.button("Questionnaire", key="flow_nav_questionnaire", width="stretch"):
        st.switch_page("pages/3_Questionnaire.py")
    if st.button("My account", key="flow_nav_account", width="stretch"):
        st.switch_page("pages/5_My_Account.py")
    if st.button("Log out", key="flow_logout", width="stretch"):
        for state_key in (
            "logged_in", "user_id", "user_name", "user_email", "role",
            "questionnaire_progress", "questionnaire_complete", "match_count",
            "questionnaire_answers", "questionnaire_step", "latest_response_id",
        ):
            st.session_state.pop(state_key, None)
        st.switch_page("app.py")


def apply_admin_dashboard_style(active_view: str = "overview") -> None:
    """Apply the pink PawMatch styling used by the administrator page."""
    apply_sidebar_dashboard_style()
    active_key = {
        "overview": "admin_nav_overview",
        "manage": "admin_nav_manage",
        "add": "admin_nav_add",
    }.get(active_view, "admin_nav_overview")

    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"] .st-key-{active_key} button {{
            border-color: #d93679 !important;
            background: linear-gradient(90deg, #ea4c8c, #d93679) !important;
            color: white !important;
            box-shadow: 0 10px 22px rgba(190,55,114,.22) !important;
        }}

        .admin-sidebar-note {{
            margin: 1.1rem .15rem 0;
            padding: .85rem;
            border: 1px dashed rgba(160,62,107,.28);
            border-radius: 14px;
            background: rgba(255,255,255,.45);
        }}
        .admin-sidebar-note strong,
        .admin-sidebar-note span {{ display: block; }}
        .admin-sidebar-note strong {{ color: #71384f; font-size: .76rem; }}
        .admin-sidebar-note span {{
            margin-top: .34rem;
            color: #8a6576;
            font-size: .68rem;
            line-height: 1.45;
        }}
        .admin-user-card {{ margin-top: 2.15rem; }}
        [data-testid="stSidebar"] .st-key-admin_nav_logout button {{
            border-color: #dca5bf;
            background: transparent;
            color: #9c3c68;
        }}

        .st-key-admin_page_shell {{ padding: .35rem .1rem 1.5rem; }}
        .admin-eyebrow {{
            margin: 0 0 .48rem;
            color: #d93679;
            font-size: .7rem;
            font-weight: 900;
            letter-spacing: .12em;
            text-transform: uppercase;
        }}
        .admin-heading h1 {{
            margin: 0;
            color: #4b3f45;
            font-size: clamp(2.15rem, 4vw, 3.45rem);
            line-height: 1.04;
            letter-spacing: -.045em;
        }}
        .admin-heading > p:not(.admin-eyebrow) {{
            max-width: 760px;
            margin: .78rem 0 0;
            color: #765d69;
            font-size: .96rem;
            line-height: 1.62;
        }}

        .admin-access-card {{
            display: flex;
            align-items: center;
            gap: .8rem;
            margin-bottom: .65rem;
            padding: .85rem 1rem;
            border: 1px solid #efbad2;
            border-radius: 16px;
            background: linear-gradient(145deg,#fff,#fff2f8);
            box-shadow: 0 12px 28px rgba(132,49,87,.08);
        }}
        .admin-access-card > span {{
            display: grid;
            place-items: center;
            width: 39px;
            height: 39px;
            border-radius: 12px;
            background: #fce4ef;
        }}
        .admin-access-card small,
        .admin-access-card strong {{ display: block; }}
        .admin-access-card small {{
            color: #9f5879;
            font-size: .63rem;
            font-weight: 850;
            letter-spacing: .08em;
            text-transform: uppercase;
        }}
        .admin-access-card strong {{ margin-top: .18rem; color: #63344b; font-size: .86rem; }}
        .st-key-admin_header_add button {{
            min-height: 46px;
            border: 0;
            border-radius: 12px;
            background: linear-gradient(90deg,#ed4f91,#d93679);
            color: white;
            font-weight: 850;
            box-shadow: 0 10px 22px rgba(217,54,121,.20);
        }}

        .admin-metric-card {{
            display: flex;
            align-items: center;
            gap: .9rem;
            min-height: 128px;
            margin-top: 1.55rem;
            padding: 1.05rem;
            border: 1px solid #eed9e3;
            border-radius: 18px;
            background: rgba(255,255,255,.96);
            box-shadow: 0 12px 30px rgba(119,49,82,.07);
        }}
        .admin-metric-icon {{
            display: grid;
            place-items: center;
            width: 45px;
            height: 45px;
            flex: 0 0 45px;
            border-radius: 14px;
            background: #fff0f7;
            color: #cc3d78;
            font-size: 1.1rem;
            font-weight: 900;
        }}
        .metric-available .admin-metric-icon {{ background: #ecf8f1; color: #388b61; }}
        .metric-reserved .admin-metric-icon {{ background: #fff6df; color: #a97719; }}
        .metric-attention .admin-metric-icon {{ background: #fff0f1; color: #b94255; }}
        .admin-metric-card p,
        .admin-metric-card strong,
        .admin-metric-card small {{ display: block; margin: 0; }}
        .admin-metric-card p {{
            color: #91647a;
            font-size: .66rem;
            font-weight: 850;
            letter-spacing: .07em;
            text-transform: uppercase;
        }}
        .admin-metric-card strong {{
            margin-top: .15rem;
            color: #513545;
            font-size: 1.72rem;
            line-height: 1;
        }}
        .admin-metric-card small {{
            margin-top: .38rem;
            color: #8b7580;
            font-size: .69rem;
            line-height: 1.35;
        }}

        .admin-section-heading {{
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 2rem;
            margin: 2.8rem 0 1.05rem;
        }}
        .admin-section-heading h2 {{
            margin: 0;
            color: #4b3f45;
            font-size: clamp(1.65rem,2.7vw,2.2rem);
            line-height: 1.12;
            letter-spacing: -.03em;
        }}
        .admin-section-heading > p {{
            max-width: 450px;
            margin: 0 0 .1rem;
            color: #8a737e;
            font-size: .84rem;
            line-height: 1.5;
            text-align: right;
        }}

        .st-key-admin_recent_records,
        .st-key-admin_quality_card,
        .st-key-admin_filter_card,
        .st-key-admin_manage_table,
        .st-key-admin_edit_card,
        .st-key-admin_delete_card,
        .st-key-admin_add_card {{
            padding: 1.3rem 1.25rem;
            border-color: #ecd7e1 !important;
            border-radius: 20px !important;
            background: rgba(255,255,255,.96);
            box-shadow: 0 13px 32px rgba(119,49,82,.07);
        }}
        .st-key-admin_recent_records,
        .st-key-admin_quality_card {{ min-height: 405px; }}
        .st-key-admin_filter_card {{ margin-bottom: 1rem; padding-bottom: .8rem; }}
        .st-key-admin_manage_table {{ margin-bottom: 1.25rem; }}

        .admin-card-heading {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: .85rem;
        }}
        .admin-card-kicker {{
            margin: 0 0 .28rem;
            color: #d24a84;
            font-size: .65rem;
            font-weight: 850;
            letter-spacing: .08em;
            text-transform: uppercase;
        }}
        .admin-card-heading h3,
        .st-key-admin_quality_card h3 {{
            margin: 0;
            color: #533245;
            font-size: 1.18rem;
        }}
        .admin-card-heading > span {{
            padding: .34rem .58rem;
            border-radius: 999px;
            background: #fff0f6;
            color: #b73d70;
            font-size: .66rem;
            font-weight: 800;
        }}
        [data-testid="stDataFrame"] {{
            border: 1px solid #f0dde6;
            border-radius: 14px;
            overflow: hidden;
        }}
        .st-key-overview_manage button,
        .st-key-overview_add button {{
            min-height: 44px;
            margin-top: .75rem;
            border: 1px solid #e8a7c4;
            border-radius: 11px;
            background: #fff8fb;
            color: #c23673;
            font-weight: 800;
        }}

        .admin-empty-state {{
            display: grid;
            place-items: center;
            min-height: 220px;
            padding: 1.5rem;
            text-align: center;
        }}
        .admin-empty-state > span {{
            display: grid;
            place-items: center;
            width: 54px;
            height: 54px;
            border-radius: 17px;
            background: #fff0f7;
            font-size: 1.35rem;
        }}
        .admin-empty-state h4 {{ margin: .8rem 0 .3rem; color: #5a3548; }}
        .admin-empty-state p {{
            max-width: 390px;
            margin: 0;
            color: #866d79;
            font-size: .82rem;
            line-height: 1.5;
        }}

        .admin-quality-score {{
            display: flex;
            align-items: end;
            gap: .5rem;
            margin: 1.25rem 0 .55rem;
        }}
        .admin-quality-score strong {{ color: #d93679; font-size: 2.35rem; line-height: .9; }}
        .admin-quality-score span {{
            padding-bottom: .15rem;
            color: #90717f;
            font-size: .72rem;
            font-weight: 750;
        }}
        .admin-quality-track {{
            height: 9px;
            overflow: hidden;
            border-radius: 999px;
            background: #f2d7e3;
        }}
        .admin-quality-track span {{
            display: block;
            height: 100%;
            border-radius: inherit;
            background: linear-gradient(90deg,#f36da4,#d93679);
        }}
        .admin-quality-copy {{
            margin: .85rem 0 1.05rem;
            color: #806773;
            font-size: .76rem;
            line-height: 1.5;
        }}
        .admin-mini-heading {{
            margin: .65rem 0 .5rem;
            color: #a24a75;
            font-size: .65rem;
            font-weight: 850;
            letter-spacing: .08em;
            text-transform: uppercase;
        }}
        .admin-attention-row {{
            display: flex;
            align-items: center;
            gap: .65rem;
            margin-top: .48rem;
            padding: .58rem;
            border: 1px solid #f0dce5;
            border-radius: 12px;
            background: #fffafb;
        }}
        .admin-attention-row > span {{
            display: grid;
            place-items: center;
            width: 31px;
            height: 31px;
            flex: 0 0 31px;
            border-radius: 10px;
            background: #ffe9f2;
            color: #bc3b72;
            font-size: .74rem;
            font-weight: 900;
        }}
        .admin-attention-row strong,
        .admin-attention-row small {{ display: block; }}
        .admin-attention-row strong {{ color: #5b394a; font-size: .75rem; }}
        .admin-attention-row small {{ margin-top: .12rem; color: #927784; font-size: .65rem; }}
        .admin-all-clear {{
            padding: .75rem;
            border-radius: 12px;
            background: #edf8f2;
            color: #387a59;
            font-size: .75rem;
            font-weight: 750;
        }}

        .admin-form-heading {{ margin-bottom: 1.15rem; }}
        .admin-form-heading h2 {{
            margin: 0;
            color: #4e3342;
            font-size: 1.72rem;
            letter-spacing: -.025em;
        }}
        .admin-form-heading > p:not(.admin-eyebrow) {{
            max-width: 750px;
            margin: .55rem 0 0;
            color: #806874;
            font-size: .84rem;
            line-height: 1.5;
        }}
        .admin-form-section {{
            margin: 1.2rem 0 .7rem;
            padding-bottom: .42rem;
            border-bottom: 1px solid #f0dce5;
            color: #a94672;
            font-size: .68rem;
            font-weight: 900;
            letter-spacing: .09em;
            text-transform: uppercase;
        }}
        .admin-validation-box {{
            margin-bottom: 1rem;
            padding: .85rem 1rem;
            border: 1px solid #efb3c0;
            border-radius: 13px;
            background: #fff4f6;
            color: #9e354c;
            font-size: .78rem;
        }}
        .admin-validation-box ul {{ margin: .45rem 0 0 1.1rem; padding: 0; }}
        .admin-algorithm-note {{
            margin-top: .9rem;
            padding: .75rem .8rem;
            border: 1px dashed #edb5cc;
            border-radius: 12px;
            background: #fff7fb;
        }}
        .admin-algorithm-note strong,
        .admin-algorithm-note span {{ display: block; }}
        .admin-algorithm-note strong {{ color: #743950; font-size: .72rem; }}
        .admin-algorithm-note span {{
            margin-top: .25rem;
            color: #876a78;
            font-size: .68rem;
            line-height: 1.4;
        }}

        [data-testid="stTabs"] [data-baseweb="tab-list"] {{ gap: .35rem; margin-bottom: 1rem; }}
        [data-testid="stTabs"] [data-baseweb="tab"] {{
            min-height: 42px;
            border-radius: 11px 11px 0 0;
            color: #765564;
            font-weight: 750;
        }}
        [data-testid="stTabs"] [aria-selected="true"] {{ color: #c63873; background: #fff0f6; }}

        .admin-danger-heading {{
            display: flex;
            align-items: center;
            gap: .8rem;
            padding: .95rem;
            border: 1px solid #f0bdc5;
            border-radius: 14px;
            background: #fff5f6;
        }}
        .admin-danger-heading > span {{
            display: grid;
            place-items: center;
            width: 39px;
            height: 39px;
            border-radius: 12px;
            background: #f7d8dd;
            color: #a93348;
            font-weight: 900;
        }}
        .admin-danger-heading p,
        .admin-danger-heading h3 {{ margin: 0; }}
        .admin-danger-heading p {{
            color: #b0495c;
            font-size: .63rem;
            font-weight: 850;
            letter-spacing: .08em;
            text-transform: uppercase;
        }}
        .admin-danger-heading h3 {{ margin-top: .18rem; color: #6c3540; font-size: 1.05rem; }}
        .admin-danger-copy {{ margin: .95rem 0; color: #82636a; font-size: .82rem; line-height: 1.55; }}
        .st-key-admin_delete_card [data-testid="stButton"] button {{
            min-height: 46px;
            border: 0;
            border-radius: 12px;
            background: #b73b51;
            color: white;
            font-weight: 850;
        }}
        .st-key-admin_delete_card [data-testid="stButton"] button:disabled {{
            background: #eadde0;
            color: #a89398;
        }}

        @media (max-width: 760px) {{
            .block-container {{ padding-right: 1rem; padding-left: 1rem; }}
            .admin-section-heading {{ display: block; }}
            .admin-section-heading > p {{ margin-top: .55rem; text-align: left; }}
            .admin-metric-card,
            .st-key-admin_recent_records,
            .st-key-admin_quality_card {{ min-height: auto; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
