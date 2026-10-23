"""Registration, login and role checks. Passwords are stored only as salted scrypt hashes."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from typing import Any

from . import db
from .models import User
from .validation import Errors, validate_login, validate_registration

SCRYPT_N, SCRYPT_R, SCRYPT_P = 2**14, 8, 1
LOGIN_FAILED = "Incorrect email or password."


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


def require_admin(user: User | None) -> User:
    """Gate for every staff action (criterion 8.5)."""
    if user is None or not user.is_admin:
        raise AccessDenied("Only shelter staff can manage animal records.")
    return user
