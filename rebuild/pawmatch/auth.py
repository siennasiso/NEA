"""Registration, login and role checks. Passwords are stored only as salted scrypt hashes.

The optional "Continue with Google" sign-in (Streamlit's st.login, set up in
.streamlit/secrets.toml) only proves who someone is. What they may do is still decided
here: external_login() maps the verified email to a local adopter account, refuses staff
accounts (staff always use their PawMatch password) and asks a newcomer for their age.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from typing import Any

from . import db
from .models import User
from .validation import EMAIL_PATTERN, Errors, validate_login, validate_person, validate_registration

SCRYPT_N, SCRYPT_R, SCRYPT_P = 2**14, 8, 1
LOGIN_FAILED = "Incorrect email or password."
STAFF_USE_PASSWORD = "Staff accounts sign in with their PawMatch email and password."
# Stored instead of a hash for accounts made through Google: it is not in the scrypt format,
# so verify_password() always refuses it and nobody can log in to them with a password.
EXTERNAL_ONLY = "external$oidc"


class AccessDenied(PermissionError):
    """Raised when a user without the right role calls a protected action."""


def hash_password(password: str) -> str:
    """Return 'scrypt$n$r$p$salt$hash' with a fresh 16-byte salt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Recompute the hash with the stored salt and compare in constant time."""
    try:
        scheme, n, r, p, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=int(n), r=int(r), p=int(p))
    return hmac.compare_digest(digest.hex(), digest_hex)


def register(
    conn: sqlite3.Connection, name: Any, email: Any, age: Any, password: Any, confirm: Any
) -> tuple[User | None, Errors]:
    """Validate, check the email is unused, then store the account with a hashed password."""
    cleaned, errors = validate_registration(name, email, age, password, confirm)
    if not errors and db.email_exists(conn, cleaned["email"]):
        errors["email"] = "An account with this email already exists."
    if errors:
        return None, errors
    user = db.insert_user(conn, cleaned["name"], cleaned["email"], cleaned["age"], hash_password(cleaned["password"]))
    return user, {}


def login(conn: sqlite3.Connection, email: Any, password: Any) -> tuple[User | None, Errors]:
    """Return the user for correct details; one generic message otherwise (no account probing)."""
    cleaned, errors = validate_login(email, password)
    if errors:
        return None, errors
    found = db.find_user_with_hash(conn, cleaned["email"])
    if found is None or not verify_password(cleaned["password"], found[1]):
        return None, {"login": LOGIN_FAILED}
    return found[0], {}


def external_login(conn: sqlite3.Connection, email: Any, email_verified: Any) -> tuple[User | None, Errors]:
    """Match someone signed in by Google (or Clerk) to their PawMatch account.

    Returns (user, {}) for an adopter account, (None, {}) when there is no account yet (the
    page then asks for their name and age), or (None, errors) when the sign-in can't be used.
    """
    clean = "" if email is None else str(email).strip().lower()
    if email_verified is not True:
        return None, {"email": "That account's email address is not verified, so PawMatch can't use it."}
    if not EMAIL_PATTERN.match(clean):
        return None, {"email": "The sign-in did not share a valid email address."}
    found = db.find_user_with_hash(conn, clean)
    if found is None:
        return None, {}
    if found[0].is_admin:
        return None, {"login": STAFF_USE_PASSWORD}
    return found[0], {}


def finish_external_account(conn: sqlite3.Connection, name: Any, email: Any, age: Any) -> tuple[User | None, Errors]:
    """Create an adopter ('user' role) account for a Google sign-in, after the same checks as sign-up."""
    cleaned, errors = validate_person(name, email, age)
    if not errors and db.email_exists(conn, cleaned["email"]):
        errors["email"] = "An account with this email already exists."
    if errors:
        return None, errors
    return db.insert_user(conn, cleaned["name"], cleaned["email"], cleaned["age"], EXTERNAL_ONLY), {}


def require_admin(user: User | None) -> User:
    """Gate for every staff action (criterion 8.5)."""
    if user is None or not user.is_admin:
        raise AccessDenied("Only shelter staff can manage animal records.")
    return user
