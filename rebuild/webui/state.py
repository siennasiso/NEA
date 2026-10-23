"""Session state, database access and page guards shared by every page."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import sqlite3

import streamlit as st

from pawmatch import db
from pawmatch.models import User

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.environ.get("PAWMATCH_DB", ROOT / "data" / "pawmatch.db"))
PAGES = {
    "home": "webui/views/home.py",
    "browse": "webui/views/browse.py",
    "profile": "webui/views/profile.py",
    "questionnaire": "webui/views/questionnaire.py",
    "results": "webui/views/results.py",
    "account": "webui/views/account.py",
    "admin": "webui/views/admin.py",
}


@contextmanager
def database() -> Iterator[sqlite3.Connection]:
    with db.connect(DB_PATH) as conn:
        yield conn


def current_user() -> User | None:
    """Reload the signed-in user each run so a role change takes effect immediately."""
    user_id = st.session_state.get("user_id")
    if user_id is None:
        return None
    with database() as conn:
        return db.get_user(conn, user_id)


def sign_in(user: User) -> None:
    st.session_state.clear()
    st.session_state["user_id"] = user.user_id


def sign_out() -> None:
    st.session_state.clear()


def require_login() -> User:
    user = current_user()
    if user is None:
        st.info("Please log in or register to use this page.")
        st.page_link(PAGES["account"], label="Log in or register", icon=":material/login:")
        st.stop()
    return user


def require_staff() -> User:
    """Page-level guard; the services also check the role, so this is defence in depth."""
    user = require_login()
    if not user.is_admin:
        st.error("This page is for shelter staff only.")
        st.stop()
    return user


def image_for(path: str) -> str | None:
    full = ROOT / path if path else None
    return str(full) if full and full.is_file() else None
