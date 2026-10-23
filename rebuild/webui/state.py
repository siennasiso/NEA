"""Session state, database access, sign-in, pictures and page guards shared by every page."""

from __future__ import annotations

import base64
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import streamlit as st

from pawmatch import db
from pawmatch.models import Animal, User

from . import images

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.environ.get("PAWMATCH_DB", ROOT / "data" / "pawmatch.db"))
# The original app's pages, in the same order (app.py, then pages/1_ to 7_). The animal
# profile is part of Browse animals, as in the original (?animal=<id>).
PAGES = {
    "login": "webui/views/login.py",
    "home": "webui/views/home.py",
    "registration": "webui/views/registration.py",
    "questionnaire": "webui/views/questionnaire.py",
    "browse": "webui/views/browse.py",
    "account": "webui/views/account.py",
    "matches": "webui/views/matches.py",
    "admin": "webui/views/admin.py",
}
# Settings Streamlit's built-in sign-in (st.login) needs; see README "Sign in with Google".
AUTH_KEYS = ("redirect_uri", "cookie_secret", "client_id", "client_secret", "server_metadata_url")


def data_dir() -> Path:
    """Uploaded photos are kept beside the database, so one folder holds all saved data."""
    return Path(DB_PATH).parent


@contextmanager
def database() -> Iterator[sqlite3.Connection]:
    with db.connect(DB_PATH) as conn:
        yield conn


def current_user() -> User | None:
    """Reload the signed-in user each run so a role change takes effect immediately.

    A browser reload starts a new Streamlit session with empty session state, so the
    session token kept in the address (?s=...) signs the user back in.
    """
    token = st.session_state.get("session_token") or st.query_params.get("s")
    if not token:
        user_id = st.session_state.get("user_id")
        if user_id is None:
            return None
        with database() as conn:
            return db.get_user(conn, user_id)
    with database() as conn:
        found = db.session_user(conn, token)
    if found is None:  # expired or signed out elsewhere
        st.session_state.pop("user_id", None)
        st.session_state.pop("session_token", None)
        if "s" in st.query_params:
            del st.query_params["s"]
        return None
    user, method = found
    st.session_state["user_id"] = user.user_id
    st.session_state["session_token"] = token
    st.session_state.setdefault("signed_in_with", method)
    if st.query_params.get("s") != token:  # page changes drop the address's query string
        st.query_params["s"] = token
    return user


def google_ready() -> bool:
    """True only when every [auth] setting is in .streamlit/secrets.toml and Authlib is installed.

    Without them the "Continue with Google" button is hidden and the app runs as normal.
    """
    try:
        settings = st.secrets.get("auth", {})
    except FileNotFoundError:  # no secrets file at all (StreamlitSecretNotFoundError)
        return False
    if not all(str(settings.get(key, "")).strip() for key in AUTH_KEYS):
        return False
    try:
        import authlib  # noqa: F401  (st.login needs it)
    except ImportError:
        return False
    return True


def google_signed_in() -> bool:
    # .get, not .is_logged_in: st.user is empty until the sign-in service has answered once.
    return google_ready() and bool(st.user.get("is_logged_in", False))


def home_for(user: User) -> str:
    return PAGES["admin"] if user.is_admin else PAGES["home"]


def sign_in(user: User, method: str = "password") -> None:
    st.session_state.clear()
    with database() as conn:
        token = db.create_session(conn, user.user_id, method)
    st.session_state["user_id"] = user.user_id
    st.session_state["signed_in_with"] = method
    st.session_state["session_token"] = token
    st.query_params["s"] = token


def sign_out() -> None:
    """Forget the PawMatch session; also end the Google session, or its cookie would sign them back in."""
    token = st.session_state.get("session_token") or st.query_params.get("s")
    if token:
        with database() as conn:
            db.end_session(conn, token)
    st.session_state.clear()
    st.query_params.clear()
    if google_signed_in():
        st.logout()
    st.switch_page(PAGES["login"])


def flash(message: str, kind: str = "info") -> None:
    """A one-off message for the next page (shown by show_flash)."""
    st.session_state["flash"] = (kind, message)


def show_flash() -> None:
    kind, message = st.session_state.pop("flash", (None, ""))
    if kind == "success":
        st.success(message, icon="🎉")
    elif kind == "info":
        st.info(message, icon="🐾")


def require_adopter() -> User:
    """Adopter pages: send visitors to log in, and staff to their dashboard (as in the original)."""
    user = current_user()
    if user is None:
        flash("Please log in to continue.")
        st.switch_page(PAGES["login"])
    if user.is_admin:
        st.switch_page(PAGES["admin"])
    return user


def require_staff() -> User:
    """Page-level guard; the services also check the role, so this is defence in depth."""
    user = current_user()
    if user is None:
        flash("Please log in with a staff account.")
        st.switch_page(PAGES["login"])
    if not user.is_admin:
        st.error("This page is for shelter staff only.")
        st.stop()
    return user


@st.cache_data(max_entries=400, show_spinner=False)
def _tile(source: str, modified: float, species: str, size: int) -> bytes:
    """Cached by file and modification time, so a replaced photo is drawn again."""
    return images.tile(Path(source) if source else None, species, size)


def photo_file(animal: Animal) -> Path | None:
    return images.resolve(animal.image_path, ROOT, data_dir())


def picture(animal: Animal, size: int = images.TILE) -> bytes:
    """The animal on its pastel tile (see webui/images.py), as JPEG bytes for st.image."""
    source = photo_file(animal)
    return _tile(str(source or ""), source.stat().st_mtime if source else 0.0, animal.species, size)


def thumbnail(animal: Animal) -> str:
    """A small tile as a data URL, for the photo column of the staff table."""
    return "data:image/jpeg;base64," + base64.b64encode(picture(animal, 96)).decode()
