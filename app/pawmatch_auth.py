"""Database and authentication helpers for the PawMatch Streamlit app."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
from pathlib import Path
from typing import Any

DATABASE_PATH = Path(__file__).resolve().parent / "pawmatch.db"
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,30}$")

# These values are stored with each password hash so they can be changed later.
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1


class _ClosingConnection(sqlite3.Connection):
    """Commit or roll back a context block, then close its SQLite connection."""

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> bool:
        """Complete the transaction and release the database file handle."""
        suppress = super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return bool(suppress)


def get_connection() -> sqlite3.Connection:
    """Open a database connection and return rows by column name."""
    connection = sqlite3.connect(DATABASE_PATH, timeout=5, factory=_ClosingConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialise_database() -> None:
    """Create the users table the first time the application is run."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT NOT NULL,
                username      TEXT COLLATE NOCASE,
                email         TEXT NOT NULL COLLATE NOCASE UNIQUE,
                age           INTEGER NOT NULL CHECK (age BETWEEN 18 AND 120),
                password_hash TEXT NOT NULL,
                role          TEXT NOT NULL DEFAULT 'user'
                              CHECK (role IN ('user', 'admin')),
                created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Existing PawMatch databases pre-date username login. SQLite cannot add
        # a UNIQUE column in-place, so add the nullable column and enforce
        # uniqueness with a partial index.
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(users)")
        }
        if "username" not in columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN username TEXT COLLATE NOCASE"
            )
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username
            ON users (username COLLATE NOCASE)
            WHERE username IS NOT NULL
            """
        )


def normalise_name(name: str) -> str:
    """Remove leading/trailing spaces and collapse repeated spaces."""
    return " ".join(name.strip().split())


def normalise_email(email: str) -> str:
    """Make email comparison consistent."""
    return email.strip().lower()


def normalise_username(username: str) -> str:
    """Make username comparison consistent."""
    return username.strip().lower()


def validate_registration(
    name: str,
    email: str,
    age: int | None,
    password: str,
    confirm_password: str,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Validate registration inputs and return errors plus cleaned values."""
    cleaned_name = normalise_name(name)
    cleaned_email = normalise_email(email)
    errors: dict[str, str] = {}

    if not cleaned_name:
        errors["name"] = "Enter your full name."
    elif len(cleaned_name) < 2:
        errors["name"] = "Your name must contain at least 2 characters."
    elif len(cleaned_name) > 60:
        errors["name"] = "Your name must be 60 characters or fewer."
    elif not all(
        character.isalpha() or character in {" ", "-", "'", "."}
        for character in cleaned_name
    ):
        errors["name"] = "Use letters, spaces, hyphens or apostrophes only."

    if not cleaned_email:
        errors["email"] = "Enter your email address."
    elif EMAIL_PATTERN.fullmatch(cleaned_email) is None:
        errors["email"] = "Enter a valid email address, such as name@example.com."

    if age is None:
        errors["age"] = "Enter your age."
    elif age < 18:
        errors["age"] = "You must be at least 18 to create an adopter account."
    elif age > 120:
        errors["age"] = "Enter an age between 18 and 120."

    if not password:
        errors["password"] = "Create a password."
    elif len(password) < 8:
        errors["password"] = "Your password must contain at least 8 characters."
    elif len(password) > 128:
        errors["password"] = "Your password must contain no more than 128 characters."
    elif not any(character.islower() for character in password):
        errors["password"] = "Include at least one lowercase letter."
    elif not any(character.isupper() for character in password):
        errors["password"] = "Include at least one uppercase letter."
    elif not any(character.isdigit() for character in password):
        errors["password"] = "Include at least one number."

    if not confirm_password:
        errors["confirm_password"] = "Repeat your password."
    elif password != confirm_password:
        errors["confirm_password"] = "The two passwords do not match."

    cleaned_values = {
        "name": cleaned_name,
        "email": cleaned_email,
        "age": age,
        "password": password,
    }
    return errors, cleaned_values


def validate_login(identifier: str, password: str) -> tuple[dict[str, str], str]:
    """Validate an email address or username plus password."""
    cleaned_identifier = identifier.strip().lower()
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


def hash_password(password: str) -> str:
    """Return a salted scrypt hash; the plain password is never stored."""
    salt = secrets.token_bytes(16)
    password_hash = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=64,
    )
    return (
        f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}$"
        f"{salt.hex()}${password_hash.hex()}"
    )


def verify_password(password: str, stored_value: str) -> bool:
    """Compare a password with the salted hash stored in SQLite."""
    try:
        scheme, n, r, p, salt_hex, hash_hex = stored_value.split("$")
        if scheme != "scrypt":
            return False

        calculated_hash = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(bytes.fromhex(hash_hex)),
        )
        return hmac.compare_digest(calculated_hash.hex(), hash_hex)
    except (ValueError, TypeError):
        return False


def create_user(name: str, email: str, age: int, password: str) -> tuple[bool, str]:
    """Insert a normal user account into SQLite."""
    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (name, email, age, password_hash, role)
                VALUES (?, ?, ?, ?, 'user')
                """,
                (name, email, age, hash_password(password)),
            )
        return True, ""
    except sqlite3.IntegrityError as error:
        if "users.email" in str(error) or "UNIQUE constraint failed" in str(error):
            return False, "An account already exists for this email address."
        return False, "The account could not be created because the data was invalid."
    except sqlite3.Error:
        return False, "The database is unavailable. Please try again."


def authenticate_user(identifier: str, password: str) -> dict[str, Any] | None:
    """Return safe user details when the supplied login is correct."""
    cleaned_identifier = identifier.strip().lower()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT user_id, name, username, email, password_hash, role
            FROM users
            WHERE email = ? OR username = ? COLLATE NOCASE
            """,
            (cleaned_identifier, cleaned_identifier),
        ).fetchone()

    if row is None or not verify_password(password, row["password_hash"]):
        return None

    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "username": row["username"],
        "email": row["email"],
        "role": row["role"],
    }


def create_admin_user(
    name: str,
    email: str,
    age: int,
    password: str,
    username: str | None = None,
) -> tuple[bool, str]:
    """Create an administrator account during one-time project setup."""
    cleaned_username = normalise_username(username or "") or None
    if cleaned_username is not None and USERNAME_PATTERN.fullmatch(cleaned_username) is None:
        return False, "Use 3-30 letters, numbers or underscores for the username."
    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (name, username, email, age, password_hash, role)
                VALUES (?, ?, ?, ?, ?, 'admin')
                """,
                (
                    normalise_name(name),
                    cleaned_username,
                    normalise_email(email),
                    int(age),
                    hash_password(password),
                ),
            )
        return True, ""
    except (TypeError, ValueError):
        return False, "Enter a valid age for the administrator account."
    except sqlite3.IntegrityError as error:
        if "users.email" in str(error) or "UNIQUE constraint failed" in str(error):
            return False, "An account already exists for this email address or username."
        return False, "The administrator account could not be created because the data was invalid."
    except sqlite3.Error:
        return False, "The database is unavailable. Please try again."


def ensure_demo_admin(
    username: str = "admin123",
    password: str = "password123",
) -> tuple[int, bool]:
    """Create or refresh the documented local demo administrator.

    This deliberately weak credential is for coursework demonstration only.
    Re-running setup replaces only this demo account's password and role.
    """
    initialise_database()
    cleaned_username = normalise_username(username)
    if USERNAME_PATTERN.fullmatch(cleaned_username) is None:
        raise ValueError("The demo administrator username is invalid.")

    with get_connection() as connection:
        existing = connection.execute(
            """
            SELECT user_id
            FROM users
            WHERE username = ? COLLATE NOCASE OR email = ? COLLATE NOCASE
            ORDER BY CASE WHEN username = ? COLLATE NOCASE THEN 0 ELSE 1 END
            LIMIT 1
            """,
            (cleaned_username, "admin123@pawmatch.local", cleaned_username),
        ).fetchone()
        new_hash = hash_password(password)
        if existing is None:
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
                    new_hash,
                ),
            )
            return int(cursor.lastrowid), True

        user_id = int(existing["user_id"])
        connection.execute(
            """
            UPDATE users
            SET name = ?, username = ?, email = ?, age = ?, password_hash = ?, role = 'admin'
            WHERE user_id = ?
            """,
            (
                "PawMatch Administrator",
                cleaned_username,
                "admin123@pawmatch.local",
                18,
                new_hash,
                user_id,
            ),
        )
        return user_id, False
