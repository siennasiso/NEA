"""Registration and login logic for the PawMatch authentication increment.

This module deliberately contains no Streamlit commands. Keeping validation,
password handling and SQL separate from the interface makes the important
security decisions reusable and much easier to explain in the Development
section of the coursework.
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from database import create_database, get_connection


# The pattern is intentionally stricter than checking only for an @ symbol.
# It accepts normal school/personal addresses while rejecting missing domains.
EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,30}$")

# PasswordHasher uses Argon2id and automatically creates a new random salt for
# every call. Therefore two users with the same password still store different
# hashes, which is the behaviour checked by pre-development test R4.
PASSWORD_HASHER = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def normalise_name(name: str) -> str:
    """Trim the name and collapse repeated internal spaces."""
    return " ".join(str(name).strip().split())


def normalise_identifier(identifier: str) -> str:
    """Make email/username comparison predictable and case-insensitive."""
    return str(identifier).strip().lower()


def _email_exists(email: str) -> bool:
    """Return True when a case-insensitive email match is already stored."""
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT 1 FROM users WHERE email = ? COLLATE NOCASE LIMIT 1",
            (email,),
        ).fetchone()
        return row is not None
    finally:
        connection.close()


def validate_registration(
    name: str,
    email: str,
    age_input: str | int,
    password: str,
    confirm_password: str,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Validate raw registration values and return errors plus clean values.

    Streamlit widgets improve usability, but these checks are repeated in the
    backend because a modified client could bypass interface restrictions.
    Returning errors by field lets the page show precise feedback for R3.
    """
    cleaned_name = normalise_name(name)
    cleaned_email = normalise_identifier(email)
    errors: dict[str, str] = {}

    if not cleaned_name:
        errors["name"] = "Enter your full name."
    elif len(cleaned_name) < 2:
        errors["name"] = "Your name must contain at least 2 characters."
    elif len(cleaned_name) > 50:
        errors["name"] = "Your name must contain no more than 50 characters."
    elif not all(
        character.isalpha() or character in {" ", "-", "'", "."}
        for character in cleaned_name
    ):
        errors["name"] = "Use letters, spaces, hyphens, apostrophes or full stops only."

    if not cleaned_email:
        errors["email"] = "Enter your email address."
    elif EMAIL_PATTERN.fullmatch(cleaned_email) is None:
        errors["email"] = "Enter a valid email address, such as name@example.com."
    elif _email_exists(cleaned_email):
        errors["email"] = "An account already exists for this email address."

    try:
        cleaned_age = int(str(age_input).strip())
    except (TypeError, ValueError):
        cleaned_age = None
        errors["age"] = "Enter your age as a whole number."
    else:
        if cleaned_age < 18:
            errors["age"] = "You must be at least 18 to create an adopter account."
        elif cleaned_age > 120:
            errors["age"] = "Enter an age between 18 and 120."

    # Seven characters must fail and eight must pass, matching R3 exactly.
    if not password:
        errors["password"] = "Create a password."
    elif len(password) < 8:
        errors["password"] = "Your password must contain at least 8 characters."
    elif len(password) > 128:
        errors["password"] = "Your password must contain no more than 128 characters."

    if not confirm_password:
        errors["confirm_password"] = "Repeat your password."
    elif password != confirm_password:
        errors["confirm_password"] = "The two passwords do not match."

    cleaned_values = {
        "name": cleaned_name,
        "email": cleaned_email,
        "age": cleaned_age,
        "password": password,
    }
    return errors, cleaned_values


def hash_password(password: str) -> str:
    """Return a salted Argon2id hash; plaintext is never written to SQLite."""
    return PASSWORD_HASHER.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    """Safely compare a submitted password with its stored Argon2id hash."""
    try:
        return PASSWORD_HASHER.verify(stored_hash, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        # Login failures return False rather than exposing cryptographic errors.
        return False


def register_user(
    name: str,
    email: str,
    age_input: str | int,
    password: str,
    confirm_password: str,
) -> tuple[dict[str, str], dict[str, Any] | None]:
    """Validate and create one adopter account using parameterised SQL."""
    create_database()
    errors, cleaned = validate_registration(
        name, email, age_input, password, confirm_password
    )
    if errors:
        return errors, None

    connection = get_connection()
    try:
        cursor = connection.execute(
            """
            INSERT INTO users (name, email, age, password_hash, role)
            VALUES (?, ?, ?, ?, 'user')
            """,
            (
                cleaned["name"],
                cleaned["email"],
                cleaned["age"],
                hash_password(cleaned["password"]),
            ),
        )
        connection.commit()
        user_id = int(cursor.lastrowid)
    except sqlite3.IntegrityError:
        # The UNIQUE database constraint is a second defence against duplicates.
        return {"email": "An account already exists for this email address."}, None
    finally:
        connection.close()

    return {}, {
        "user_id": user_id,
        "name": cleaned["name"],
        "email": cleaned["email"],
        "username": None,
        "role": "user",
    }


def validate_login(identifier: str, password: str) -> tuple[dict[str, str], str]:
    """Check the presence and format of an email address or username."""
    cleaned_identifier = normalise_identifier(identifier)
    errors: dict[str, str] = {}

    if not cleaned_identifier:
        errors["identifier"] = "Enter your email address or username."
    elif "@" in cleaned_identifier:
        if EMAIL_PATTERN.fullmatch(cleaned_identifier) is None:
            errors["identifier"] = "Enter a valid email address."
    elif USERNAME_PATTERN.fullmatch(cleaned_identifier) is None:
        errors["identifier"] = (
            "A username must contain 3-30 letters, numbers or underscores."
        )

    if not password:
        errors["password"] = "Enter your password."

    return errors, cleaned_identifier


def authenticate_user(
    identifier: str, password: str
) -> tuple[dict[str, str], dict[str, Any] | None]:
    """Return safe account details only when both credentials are correct."""
    create_database()
    errors, cleaned_identifier = validate_login(identifier, password)
    if errors:
        return errors, None

    connection = get_connection()
    try:
        row = connection.execute(
            """
            SELECT user_id, name, username, email, password_hash, role
            FROM users
            WHERE email = ? COLLATE NOCASE
               OR username = ? COLLATE NOCASE
            LIMIT 1
            """,
            (cleaned_identifier, cleaned_identifier),
        ).fetchone()
    finally:
        connection.close()

    # The same message is used for an unknown account and a wrong password.
    # This prevents the interface from confirming whether an email is stored.
    if row is None or not verify_password(password, row["password_hash"]):
        return {"credentials": "Incorrect email/username or password."}, None

    return {}, {
        "user_id": int(row["user_id"]),
        "name": str(row["name"]),
        "username": row["username"],
        "email": str(row["email"]),
        "role": str(row["role"]),
    }


def ensure_demo_admin(
    username: str = "admin123", password: str = "password123"
) -> tuple[int, bool]:
    """Create the documented local administrator used by manual test R6.

    These intentionally simple credentials are for local coursework testing
    only. A deployed system would use a private setup secret or an identity
    provider instead of publishing a demonstration password.
    """
    create_database()
    cleaned_username = normalise_identifier(username)
    if USERNAME_PATTERN.fullmatch(cleaned_username) is None:
        raise ValueError("The demonstration username is invalid.")

    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT user_id FROM users WHERE username = ? COLLATE NOCASE",
            (cleaned_username,),
        ).fetchone()

        if row is None:
            cursor = connection.execute(
                """
                INSERT INTO users (
                    name, username, email, age, password_hash, role
                )
                VALUES (?, ?, ?, ?, ?, 'admin')
                """,
                (
                    "PawMatch Administrator",
                    cleaned_username,
                    "admin123@pawmatch.local",
                    18,
                    hash_password(password),
                ),
            )
            connection.commit()
            return int(cursor.lastrowid), True

        # Refresh the local demo password so the setup remains reproducible.
        connection.execute(
            """
            UPDATE users
            SET password_hash = ?, role = 'admin'
            WHERE user_id = ?
            """,
            (hash_password(password), int(row["user_id"])),
        )
        connection.commit()
        return int(row["user_id"]), False
    finally:
        connection.close()

