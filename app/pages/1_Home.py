"""PawMatch user dashboard with a pink left navigation panel."""

from __future__ import annotations

import html

import streamlit as st

from pawmatch_matching import fetch_latest_matches, fetch_latest_response
from pawmatch_style import apply_sidebar_dashboard_style

st.set_page_config(
    page_title="PawMatch | Home",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Do not show private account information unless a user has logged in.
if not st.session_state.get("logged_in", False):
    st.switch_page("app.py")

if st.session_state.get("role") == "admin":
    st.switch_page("pages/7_Admin_Dashboard.py")

apply_sidebar_dashboard_style()


def log_out() -> None:
    """Clear the current browser session and return to the login page."""
    for state_key in (
        "logged_in",
        "user_id",
        "user_name",
        "user_email",
        "role",
        "questionnaire_progress",
        "questionnaire_complete",
        "match_count",
        "questionnaire_answers",
        "questionnaire_step",
        "latest_response_id",
    ):
        st.session_state.pop(state_key, None)
    st.switch_page("app.py")


# Restore completed questionnaire state when a returning user signs in again.
if "questionnaire_complete" not in st.session_state:
    latest_response = fetch_latest_response(int(st.session_state.user_id))
    if latest_response is not None:
        st.session_state.questionnaire_complete = True
        st.session_state.questionnaire_progress = 100
        st.session_state.match_count = min(
            3, len(fetch_latest_matches(int(st.session_state.user_id)))
        )

full_name = str(st.session_state.get("user_name", "PawMatch user")).strip()
first_name = full_name.split()[0] if full_name else "there"
email = str(st.session_state.get("user_email", ""))

questionnaire_progress = int(st.session_state.get("questionnaire_progress", 0))
questionnaire_progress = max(0, min(100, questionnaire_progress))
questionnaire_complete = bool(
    st.session_state.get("questionnaire_complete", questionnaire_progress == 100)
)
match_count = max(0, int(st.session_state.get("match_count", 0)))

safe_first_name = html.escape(first_name)
safe_email = html.escape(email)

if questionnaire_complete:
    status_label = "Complete"
    status_message = (
        f"Your questionnaire is complete and {match_count} ranked match"
        f"{'es are' if match_count != 1 else ' is'} ready to review."
    )
    questionnaire_button_label = "Review questionnaire"
else:
    status_label = "Not started" if questionnaire_progress == 0 else "In progress"
    status_message = (
        "Complete the questionnaire to unlock ranked compatibility results."
        if questionnaire_progress == 0
        else "Continue from where you stopped to unlock ranked compatibility results."
    )
    questionnaire_button_label = (
        "Start questionnaire" if questionnaire_progress == 0 else "Continue questionnaire"
    )


# ---------------------------
# Left navigation panel
# ---------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-logo" aria-hidden="true">🐾</div>
            <div>
                <p class="sidebar-brand-name">PawMatch</p>
                <p class="sidebar-brand-subtitle">Adoption matching</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<p class="sidebar-section-label">Main menu</p>', unsafe_allow_html=True)

    # Home is styled as the active page. Clicking it simply reruns this page.
    st.button("🏠  Home", key="nav_home", width="stretch")

    if st.button("🐾  Browse animals", key="nav_browse", width="stretch"):
        st.switch_page("pages/4_Browse_Animals.py")

    if st.button("📝  Questionnaire", key="nav_questionnaire", width="stretch"):
        st.switch_page("pages/3_Questionnaire.py")

    if st.button(
        "💗  My matches",
        key="nav_matches",
        width="stretch",
        disabled=not questionnaire_complete,
        help=(
            None
            if questionnaire_complete
            else "Complete the questionnaire before viewing ranked matches."
        ),
    ):
        st.switch_page("pages/6_My_Matches.py")

    if st.button("👤  My account", key="nav_account", width="stretch"):
        st.switch_page("pages/5_My_Account.py")

    st.markdown(
        f"""
        <div class="sidebar-user-card">
            <span class="sidebar-user-icon" aria-hidden="true">👤</span>
            <div>
                <strong>{safe_first_name}</strong>
                <small>{safe_email}</small>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("↪  Log out", key="nav_logout", width="stretch"):
        log_out()


# ---------------------------
# Main dashboard area
# ---------------------------
with st.container(key="home_page_shell"):
    welcome_column, status_column = st.columns([1.55, 0.75], gap="large")

    with welcome_column:
        st.markdown(
            f"""
            <div class="home-heading">
                <p class="home-eyebrow">Your adoption dashboard</p>
                <h1>Welcome back, {safe_first_name}!</h1>
                <p class="home-subtitle">Time to find a companion who fits your life.</p>
                <p class="home-introduction">
                    Browse available animals, describe your home and lifestyle, and
                    receive ranked recommendations with clear compatibility information.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with status_column:
        st.markdown(
            f"""
            <div class="questionnaire-status-card">
                <div class="status-card-topline">
                    <span>Questionnaire status</span>
                    <strong>{status_label}</strong>
                </div>
                <p>{status_message}</p>
                <div class="status-progress-label">
                    <span>Progress</span>
                    <strong>{questionnaire_progress}%</strong>
                </div>
                <div class="status-progress-track" aria-label="Questionnaire progress">
                    <span style="width:{questionnaire_progress}%"></span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="home-section-heading">
            <div>
                <p class="home-eyebrow">Main actions</p>
                <h2>What would you like to do?</h2>
            </div>
            <p>Each option leads to one clear section of the system.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    browse_column, questionnaire_column, matches_column = st.columns(3, gap="large")

    with browse_column:
        with st.container(key="home_browse_card", border=True):
            st.markdown(
                """
                <div class="home-action-icon" aria-hidden="true">🐶</div>
                <p class="home-card-kicker">Explore the shelter</p>
                <h3>Browse animals</h3>
                <p class="home-card-copy">
                    View available dogs, cats and rabbits. Search and filter profiles by
                    details such as species, age and suitability before opening the full profile.
                </p>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "Browse all animals",
                key="home_browse_button",
                width="stretch",
            ):
                st.switch_page("pages/4_Browse_Animals.py")

    with questionnaire_column:
        with st.container(key="home_questionnaire_card", border=True):
            st.markdown(
                """
                <div class="home-action-icon primary-icon" aria-hidden="true">📝</div>
                <p class="home-card-kicker">Personalise your results</p>
                <h3>Take the questionnaire</h3>
                <p class="home-card-copy">
                    Enter information about your living space, routine, experience and
                    preferences. Your answers are used by the compatibility algorithm.
                </p>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                questionnaire_button_label,
                key="home_questionnaire_button",
                type="primary",
                width="stretch",
            ):
                st.switch_page("pages/3_Questionnaire.py")

    with matches_column:
        with st.container(key="home_matches_card", border=True):
            lock_icon = "💗" if questionnaire_complete else "🔒"
            st.markdown(
                f"""
                <div class="home-action-icon" aria-hidden="true">{lock_icon}</div>
                <p class="home-card-kicker">Your personalised results</p>
                <h3>My matches</h3>
                <p class="home-card-copy">
                    Review animals in ranked order with a compatibility score, match
                    category and an explanation of any requirements you do not meet.
                </p>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                "View my matches" if questionnaire_complete else "Complete questionnaire first",
                key="home_matches_button",
                width="stretch",
                disabled=not questionnaire_complete,
                help=(
                    None
                    if questionnaire_complete
                    else "Recommendations need your questionnaire answers first."
                ),
            ):
                st.switch_page("pages/6_My_Matches.py")

    st.markdown(
        """
        <div class="home-section-heading why-heading">
            <div>
                <p class="home-eyebrow">How PawMatch works</p>
                <h2>From your answers to explained matches</h2>
            </div>
            <p>Three clear stages show how the system creates meaningful recommendations.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    reason_one, reason_two, reason_three = st.columns(3, gap="large")

    with reason_one:
        st.markdown(
            """
            <div class="reason-card">
                <div class="reason-icon" aria-hidden="true">1</div>
                <h3>Tell us about your lifestyle</h3>
                <p>Answer questions about your home, available time, experience and animal preferences.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with reason_two:
        st.markdown(
            """
            <div class="reason-card">
                <div class="reason-icon" aria-hidden="true">2</div>
                <h3>Compare requirements</h3>
                <p>The algorithm compares each answer with the care requirements stored for every animal.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with reason_three:
        st.markdown(
            """
            <div class="reason-card">
                <div class="reason-icon" aria-hidden="true">3</div>
                <h3>Receive explained matches</h3>
                <p>Animals are ranked by compatibility score with match categories and unmet requirements.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="dashboard-footer">
            <span>🐾 PawMatch</span>
            <span>Thoughtful matches · Clear explanations · Animal welfare first</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
