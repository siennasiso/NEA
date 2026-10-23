"""Shared pink styling for every PawMatch page: the original app/pawmatch_style.py, ported.

Kept as she wrote it, with four clean-ups: her palette sits in one tokens block (:root) and the
rules use var(); the unused apply_dashboard_style is gone; style-only blocks go through st.html
so they take no space on the page; the menu buttons go to this app's pages (webui/state.PAGES).
The accessibility fixes made after testing are listed in the README and the write-up.

CSS only styles the page: every rule, check and calculation is Python (pawmatch/).
Visual direction (SISO UI hub, ideas only, no code copied):
  21st:lavikatiyar__login                  split-screen sign-in card (login and registration)
  21st:vaib215__auth-form                  sign-in / sign-up switch above the form
  21st:ravikatiyar162__registration-stepper and arc:stepper   question progress
  21st:forgedstep__score-ring              compatibility ring on each match
  arc:metric-card and 21st:ravikatiyar162__stats-card         staff dashboard counts
  21st:manuarora700__sidebar               the left-hand menu
  arc:empty-state                          "nothing here yet" cards with a next step
  arc:sortable-data-table                  the staff animal table
"""

import streamlit as st

from webui.state import PAGES, sign_out


def apply_pawmatch_style() -> None:
    st.html(
        """
        <style>
        :root {
            /* Her palette, kept in one place (also .streamlit/config.toml). */
            --pm-primary: #d93679;     /* primary: active states, links, headings' accents */
            --pm-pink-ring: #d84d8b;   /* score rings, selected answers */
            --pm-pink: #ed4f91;        /* brand pink */
            --pm-pink-warm: #ea4c8c;
            --pm-pink-soft: #f985b2;
            --pm-blush: #fff0f6;       /* backgrounds, lightest to warmest */
            --pm-cream: #fffafd;
            --pm-shell: #fff8fb;
            --pm-mist: #fff7fb;
            --pm-text: #4b3f45;        /* body text */
            --pm-ink: #171318;         /* headings */
            /* Two deeper pinks from the same file, so white labels and small pink text reach 4.5:1. */
            --pm-primary-deep: #c23673;
            --pm-deep: #a92660;
            --pm-button: linear-gradient(90deg, var(--pm-primary-deep), var(--pm-deep));
            --pm-panel: linear-gradient(145deg, var(--pm-primary-deep), var(--pm-deep));
            /* The original file's own names, kept so the rules below read as she wrote them. */
            --pink: var(--pm-pink);
            --dark-pink: var(--pm-primary);
            --deep-pink: var(--pm-deep);
            --pale-pink: #fff4f9;
            --border-pink: #f3bfd4;
            --dark-text: #4b2338;
            --muted-text: #806170;
            --error: #bd294b;
        }

        /* Found by the rendered audit (docs/evidence/rendered-audit-*.json), for every page:
           the upload hint was Streamlit's faded grey (3.2:1), and the sign-in switch showed no
           focus ring for keyboard users. */
        [data-testid="stFileUploaderDropzoneInstructions"] small,
        [data-testid="stFileUploaderDropzoneInstructions"] span { color: var(--pm-text) !important; }
        .st-key-auth_tab_login button:focus-visible,
        .st-key-auth_tab_registration button:focus-visible {
            outline: 3px solid var(--pm-deep) !important;
            outline-offset: 2px;
        }
        /* When hovered or focused, Streamlit gives a button a pale pink fill. White labels would
           vanish on it (1.2:1) and pink labels drop to about 4.1:1, so these states keep a deep pink. */
        [class*="st-key-view_profile_"] button:hover, [class*="st-key-view_profile_"] button:focus,
        .st-key-view_matches_primary button:hover, .st-key-view_matches_primary button:focus {
            background: var(--pm-deep) !important;
            color: white !important;
        }
        .st-key-secondary_button button:hover, .st-key-secondary_button button:focus,
        .st-key-login_button button:hover, .st-key-login_button button:focus,
        .st-key-logout_button button:hover, .st-key-logout_button button:focus,
        .st-key-page_back button:hover, .st-key-page_back button:focus,
        .st-key-profile_back button:hover, .st-key-profile_back button:focus,
        .st-key-flow_back button:hover, .st-key-flow_back button:focus,
        .st-key-overview_manage button:hover, .st-key-overview_manage button:focus,
        .st-key-overview_add button:hover, .st-key-overview_add button:focus {
            color: var(--pm-deep) !important;
        }

        /* Streamlit's own chrome: visitors never see the developer menu, deploy button or footer. */
        #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stMainMenu"],
        [data-testid="stAppDeployButton"], [data-testid="stStatusWidget"],
        [data-testid="stDecoration"] { display: none !important; }

        .stApp {
            background:
                radial-gradient(circle at 10% 10%, #ffc9df 0, transparent 28%),
                radial-gradient(circle at 90% 85%, #f8bad3 0, transparent 25%),
                linear-gradient(135deg, var(--pm-cream), #ffe8f2);
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
            background: radial-gradient(circle at 88% 12%, rgba(255,255,255,.25), transparent 22%),
                var(--pm-panel);
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
            color: white;
            line-height: 1.65;
        }

        .benefit {
            margin: .85rem 0;
            color: white;
            font-size: .94rem;
            font-weight: 650;
        }

        .tick {
            display: inline-grid;
            place-items: center;
            width: 28px;
            height: 28px;
            margin-right: .55rem;
            border: 1.5px solid rgba(255,255,255,.75);
            border-radius: 9px;
            background: transparent;
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
            color: #856573;
            font-size: .76rem;
            line-height: 1.4;
        }

        .stFormSubmitButton button {
            min-height: 49px;
            margin-top: .25rem;
            border: 0;
            border-radius: 13px;
            background: var(--pm-button);
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
            color: var(--pm-primary-deep);
            font-weight: 750;
        }

        .divider {
            display: flex;
            align-items: center;
            gap: .8rem;
            margin: 1rem 0 .7rem;
            color: #886475;
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
            background: var(--pm-mist);
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

        /* "Log in | Create an account" switch above each form (21st:vaib215__auth-form). */
        .st-key-auth_tab_login,
        .st-key-auth_tab_registration { margin-bottom: 1.1rem; }
        .st-key-auth_tab_login [data-testid="stButtonGroup"] > div,
        .st-key-auth_tab_registration [data-testid="stButtonGroup"] > div {
            gap: 4px;
            padding: 4px;
            border: 1px solid var(--border-pink);
            border-radius: 999px;
            background: var(--pale-pink);
        }
        .st-key-auth_tab_login button,
        .st-key-auth_tab_registration button {
            flex: 1 1 0;
            min-height: 40px;
            border: 0 !important;
            border-radius: 999px !important;
            background: transparent !important;
            color: #7b5a69 !important;
            font-weight: 700;
        }
        .st-key-auth_tab_login button p,
        .st-key-auth_tab_registration button p { color: inherit !important; font-weight: inherit; }
        .st-key-auth_tab_login button:hover,
        .st-key-auth_tab_registration button:hover { background: white !important; color: var(--pm-deep) !important; }
        /* The selected tab: Streamlit marks it aria-checked="true", which screen readers also announce. */
        .st-key-auth_tab_login button[aria-checked="true"],
        .st-key-auth_tab_registration button[aria-checked="true"] {
            background: white !important;
            color: var(--pm-deep) !important;
            font-weight: 800;
            box-shadow: 0 4px 12px rgba(169,38,96,.14);
        }

        /* Any other primary button uses the same accessible pink as the form buttons. */
        button[data-testid="stBaseButton-primary"] {
            border: 0;
            background: var(--pm-button);
            color: white;
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
    )


def apply_sidebar_dashboard_style() -> None:
    """Apply the pink theme used by the dashboard with left navigation."""
    apply_pawmatch_style()
    st.html(
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
                var(--pm-cream);
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
            background: var(--pm-button);
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
            color: #6e525e;
            font-size: .78rem;
            font-weight: 650;
        }

        .sidebar-section-label {
            margin: .4rem .55rem .55rem;
            color: #8d4066;
            font-size: .78rem;
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
            border-color: var(--pm-primary);
            background: var(--pm-button);
            color: white;
            box-shadow: 0 10px 22px rgba(190, 55, 114, .22);
        }

        [data-testid="stSidebar"] .st-key-nav_home button:hover {
            border-color: var(--pm-primary);
            background: var(--pm-button);
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
            color: #6d525f;
            font-size: .78rem;
        }

        [data-testid="stSidebar"] .st-key-nav_logout button {
            border-color: #dca5bf;
            background: transparent;
            color: #953963;
        }

        .st-key-home_page_shell {
            padding: .4rem .2rem 0;
        }

        .home-heading {
            padding: .65rem 0 .15rem;
        }

        .home-eyebrow {
            margin: 0 0 .5rem;
            color: var(--pm-primary-deep);
            font-size: .78rem;
            font-weight: 900;
            letter-spacing: .12em;
            text-transform: uppercase;
        }

        .home-heading h1 {
            margin: 0;
            color: var(--pm-text);
            font-size: clamp(2.15rem, 4vw, 3.55rem);
            line-height: 1.05;
            letter-spacing: -.045em;
        }

        .home-subtitle {
            margin: .5rem 0 0;
            color: #c43277;
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
            font-size: .78rem;
            font-weight: 850;
            letter-spacing: .08em;
            text-transform: uppercase;
        }

        .status-card-topline strong {
            padding: .3rem .58rem;
            border-radius: 999px;
            background: #fce2ee;
            color: #b7326b;
            font-size: .78rem;
        }

        .questionnaire-status-card p {
            min-height: 48px;
            margin: .85rem 0 1rem;
            color: #755765;
            font-size: .84rem;
            line-height: 1.5;
        }

        .status-progress-label strong {
            color: var(--pm-primary-deep);
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
            background: linear-gradient(90deg, #f36da4, var(--pm-primary));
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
            color: var(--pm-text);
            font-size: clamp(1.6rem, 2.5vw, 2.15rem);
            line-height: 1.15;
            letter-spacing: -.025em;
        }

        .home-section-heading > p {
            max-width: 390px;
            margin: 0 0 .15rem;
            color: #7d6973;
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
            color: #c73171;
            font-size: .78rem;
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
            background: var(--pm-shell);
            color: #c23673;
            font-weight: 800;
        }

        .st-key-home_questionnaire_button button {
            min-height: 46px;
            border: 0;
            border-radius: 12px;
            background: var(--pm-button);
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
            color: #7d6972;
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
            color: #836674;
            font-size: .78rem;
        }

        .dashboard-footer span:first-child {
            color: var(--pm-primary-deep);
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
    st.html(
        """
        <style>
        .stApp, .stApp button, .stApp input, .stApp select {
            font-family: "Avenir Next", "Nunito", Arial, sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at 92% 8%, rgba(252, 207, 232, .72), transparent 27%),
                linear-gradient(135deg, var(--pm-cream) 0%, #fff0f8 100%);
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
            border: 1px solid #efd5e2;
            border-radius: 3px 0 0 3px;
            background: #fff1f8;
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
            background: var(--pm-primary-deep);
            color: white;
            font-size: 1rem;
        }

        .flow-brand strong, .flow-brand small { display: block; }
        .flow-brand strong { color: #282329; font-size: 1rem; font-weight: 800; }
        .flow-brand small { margin-top: .08rem; color: #7d6873; font-size: .78rem; }

        .st-key-design_sidebar .stButton > button {
            min-height: 49px;
            margin-bottom: .42rem;
            border: 2px solid #efbfd5;
            border-radius: 8px;
            background: #fff8fc;
            color: var(--pm-ink);
            font-size: 1rem;
            font-weight: 800;
            box-shadow: none;
        }

        .st-key-design_sidebar .stButton > button:hover {
            border-color: #e79fbe;
            background: #fde8f3;
            color: var(--pm-ink);
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
            color: #746b71;
            font-size: .9rem !important;
            font-weight: 500;
        }

        .flow-page-header > span {
            padding-top: .18rem;
            color: #af4a79;
            font-size: .78rem !important;
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
            font-size: .78rem;
            font-weight: 650;
            line-height: 1.55;
            box-shadow: 0 4px 6px rgba(76,51,64,.18);
        }

        /* Title on its own line, hint below, both allowed to wrap: four cards in a row
           cut the hints off with an ellipsis before this rule. */
        [class*="st-key-choice_"] button div,
        [class*="st-key-choice_"] button p {
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
        }

        [class*="st-key-choice_"] button p {
            color: #5b4a53;
            font-size: .75rem;
            font-weight: 500;
            line-height: 1.4;
        }

        [class*="st-key-choice_"] button p strong {
            display: block;
            margin-bottom: .2rem;
            color: #352c31;
            font-size: .86rem;
            font-weight: 750;
        }

        [class*="st-key-choice_"] button:hover {
            border-color: #d74d89;
            background: #fae4f0;
            color: #352c31;
        }

        .question-help {
            margin: -.9rem 0 1rem;
            color: #7c6972;
            font-size: .78rem;
        }

        .st-key-question_hours [data-baseweb="input"] {
            min-height: 58px;
            border: 2px solid #e8abc7;
            border-radius: 15px;
            background: var(--pm-mist);
        }

        .st-key-question_hours label {
            color: #654b58;
            font-size: .78rem;
            font-weight: 700;
        }

        .st-key-flow_back button,
        .st-key-flow_next button,
        .st-key-flow_submit button {
            min-height: 47px;
            margin-top: 1rem;
            border-radius: 8px;
            font-size: .78rem;
            font-weight: 800;
        }

        .st-key-flow_back button {
            border: 1px solid #d6538e;
            background: white;
            color: #be3b78;
        }

        .st-key-flow_next button,
        .st-key-flow_submit button {
            border: 1px solid var(--pm-pink-ring);
            background: var(--pm-primary-deep);
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
            background: var(--pm-primary-deep);
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
            color: #c43474;
            font-size: .82rem !important;
            font-weight: 550;
        }

        .match-reason {
            margin: .55rem 0;
            padding: .65rem .75rem;
            border-radius: 8px;
            color: #5c7561;
            background: #eef8ee;
            font-size: .92rem !important;
            line-height: 1.5;
        }

        .match-reason.consideration {
            color: #826c49;
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
        .match-category { margin-bottom: .55rem; color: #bb4077; font-size: .8rem !important; font-weight: 750; }
        .score-ring {
            display: grid;
            place-items: center;
            width: 88px;
            height: 88px;
            margin: 0 auto .6rem;
            border-radius: 50%;
            color: #c33476;
            font-size: .98rem;
            font-weight: 800;
            letter-spacing: -.02em;
        }

        .score-ring span {
            display: grid;
            place-items: center;
            width: 74px;
            height: 74px;
            border-radius: 50%;
            background: white;
        }

        .profile-button {
            display: block;
            padding: .66rem .45rem;
            border-radius: 7px;
            background: var(--pm-primary-deep);
            color: white !important;
            font-size: .78rem !important;
            font-weight: 750;
            text-align: center;
            text-decoration: none !important;
        }

        /* Each ranked match is a keyed container laid out like her .match-card. */
        [class*="st-key-match_card_"] {
            margin-bottom: 1rem;
            padding: 1rem 1.15rem;
            border: 1px solid #d8ced3;
            border-radius: 24px;
            background: white;
            box-shadow: 0 4px 12px rgba(70,48,59,.08);
        }
        [class*="st-key-match_card_"] [data-testid="stHorizontalBlock"] { align-items: center; }
        [class*="st-key-match_card_"] [data-testid="stColumn"]:first-child { align-self: flex-start; }
        [class*="st-key-match_card_"] [data-testid="stPageLink"] a {
            justify-content: center;
            padding: .6rem .5rem;
            border-radius: 9px;
            background: var(--pm-primary-deep);
            text-decoration: none;
        }
        [class*="st-key-match_card_"] [data-testid="stPageLink"] a:hover { background: var(--pm-deep); }
        [class*="st-key-match_card_"] [data-testid="stPageLink"] a span,
        [class*="st-key-match_card_"] [data-testid="stPageLink"] a p {
            color: white;
            font-size: .82rem;
            font-weight: 800;
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
            color: #bf3a75;
            font-size: .78rem;
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
        .completion-card p { color: #796871; font-size: .78rem; }
        .st-key-view_matches_primary button {
            min-height: 48px;
            border: 1px solid var(--pm-pink-ring);
            border-radius: 8px;
            background: var(--pm-primary-deep);
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
        .animal-card-copy .animal-breed { margin: 0 0 .4rem; color: #c43576; font-size: .78rem; }
        .animal-card-copy .animal-facts { margin: 0 0 .55rem; color: #6e6268; font-size: .78rem; }
        .animal-card-copy .animal-description { min-height: 48px; color: #776a71; font-size: .78rem; line-height: 1.45; }
        [class*="st-key-view_profile_"] button {
            min-height: 38px;
            border: 1px solid var(--pm-pink-ring);
            border-radius: 7px;
            background: var(--pm-primary-deep);
            color: white;
            font-size: .78rem;
            font-weight: 800;
        }

        .profile-title h1 { margin: 0; color: #4c4549; font-size: 1.85rem !important; }
        .profile-title p { margin: .25rem 0 1.25rem; color: #c43576; font-size: .78rem; }
        .profile-description { color: #786b72; font-size: .75rem; line-height: 1.65; }
        .profile-fact {
            padding: .75rem;
            border: 1px solid #ead3df;
            border-radius: 10px;
            background: #fff6fa;
            text-align: center;
            color: #685b62;
            font-size: .78rem;
        }
        .profile-fact strong { display: block; color: #c63173; font-size: .78rem; }
        .needs-card, .account-card {
            margin-top: 1.2rem;
            padding: 1.2rem;
            border: 1px solid #ddd0d6;
            border-radius: 17px;
            background: white;
            box-shadow: 0 4px 10px rgba(70,48,59,.08);
        }
        .needs-card h2, .account-card h2 { margin: 0 0 .8rem; color: #51484d; font-size: 1rem !important; }
        .need-line, .account-line { margin: .45rem 0; color: #75656d; font-size: .78rem; }
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
    )
    st.html(
        f"""
        <style>
        .st-key-{active_key} button,
        .st-key-{active_key} button:hover {{
            border-color: #f2aed0 !important;
            background: #f2aed0 !important;
            color: var(--pm-ink) !important;
        }}
        </style>
        """,
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
    for label, key, page in (
        ("Home", "flow_nav_home", "home"),
        ("Browse animals", "flow_nav_animals", "browse"),
        ("Questionnaire", "flow_nav_questionnaire", "questionnaire"),
        ("My account", "flow_nav_account", "account"),
    ):
        if st.button(label, key=key, width="stretch"):
            st.switch_page(PAGES[page])
    if st.button("Log out", key="flow_logout", width="stretch"):
        sign_out()


def apply_admin_dashboard_style(active_view: str = "overview") -> None:
    """Apply the pink PawMatch styling used by the administrator page."""
    apply_sidebar_dashboard_style()
    active_key = {
        "overview": "admin_nav_overview",
        "manage": "admin_nav_manage",
        "add": "admin_nav_add",
    }.get(active_view, "admin_nav_overview")

    st.html(
        f"""
        <style>
        [data-testid="stSidebar"] .st-key-{active_key} button {{
            border-color: var(--pm-primary) !important;
            background: var(--pm-button) !important;
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
            color: #6f525f;
            font-size: .78rem;
            line-height: 1.45;
        }}
        .admin-user-card {{ margin-top: 2.15rem; }}
        [data-testid="stSidebar"] .st-key-admin_nav_logout button {{
            border-color: #dca5bf;
            background: transparent;
            color: #953963;
        }}

        .st-key-admin_page_shell {{ padding: .35rem .1rem 1.5rem; }}
        .admin-eyebrow {{
            margin: 0 0 .48rem;
            color: var(--pm-primary-deep);
            font-size: .78rem;
            font-weight: 900;
            letter-spacing: .12em;
            text-transform: uppercase;
        }}
        .admin-heading h1 {{
            margin: 0;
            color: var(--pm-text);
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
            font-size: .78rem;
            font-weight: 850;
            letter-spacing: .08em;
            text-transform: uppercase;
        }}
        .admin-access-card strong {{ margin-top: .18rem; color: #63344b; font-size: .86rem; }}
        .st-key-admin_header_add button {{
            min-height: 46px;
            border: 0;
            border-radius: 12px;
            background: var(--pm-button);
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
            color: #c63470;
            font-size: 1.1rem;
            font-weight: 900;
        }}
        .metric-available .admin-metric-icon {{ background: #ecf8f1; color: #327c57; }}
        .metric-reserved .admin-metric-icon {{ background: #fff6df; color: #936716; }}
        .metric-attention .admin-metric-icon {{ background: #fff0f1; color: #b94255; }}
        .admin-metric-card p,
        .admin-metric-card strong,
        .admin-metric-card small {{ display: block; margin: 0; }}
        .admin-metric-card p {{
            color: #8c6176;
            font-size: .78rem;
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
            color: #7d6973;
            font-size: .78rem;
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
            color: var(--pm-text);
            font-size: clamp(1.65rem,2.7vw,2.2rem);
            line-height: 1.12;
            letter-spacing: -.03em;
        }}
        .admin-section-heading > p {{
            max-width: 450px;
            margin: 0 0 .1rem;
            color: #7d6973;
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
            color: #c73171;
            font-size: .78rem;
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
            background: var(--pm-blush);
            color: #b73d70;
            font-size: .78rem;
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
            background: var(--pm-shell);
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
            color: #7f6773;
            font-size: .82rem;
            line-height: 1.5;
        }}

        .admin-quality-score {{
            display: flex;
            align-items: end;
            gap: .5rem;
            margin: 1.25rem 0 .55rem;
        }}
        .admin-quality-score strong {{ color: var(--pm-primary-deep); font-size: 2.35rem; line-height: .9; }}
        .admin-quality-score span {{
            padding-bottom: .15rem;
            color: #826672;
            font-size: .78rem;
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
            background: linear-gradient(90deg,#f36da4,var(--pm-primary));
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
            font-size: .78rem;
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
            font-size: .78rem;
            font-weight: 900;
        }}
        .admin-attention-row strong,
        .admin-attention-row small {{ display: block; }}
        .admin-attention-row strong {{ color: #5b394a; font-size: .75rem; }}
        .admin-attention-row small {{ margin-top: .12rem; color: #816773; font-size: .78rem; }}
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
            font-size: .78rem;
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
            background: var(--pm-mist);
        }}
        .admin-algorithm-note strong,
        .admin-algorithm-note span {{ display: block; }}
        .admin-algorithm-note strong {{ color: #743950; font-size: .78rem; }}
        .admin-algorithm-note span {{
            margin-top: .25rem;
            color: #816673;
            font-size: .78rem;
            line-height: 1.4;
        }}

        [data-testid="stTabs"] [data-baseweb="tab-list"] {{ gap: .35rem; margin-bottom: 1rem; }}
        [data-testid="stTabs"] [data-baseweb="tab"] {{
            min-height: 42px;
            border-radius: 11px 11px 0 0;
            color: #765564;
            font-weight: 750;
        }}
        [data-testid="stTabs"] [aria-selected="true"] {{ color: #c63873; background: var(--pm-blush); }}

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
            font-size: .78rem;
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
    )
