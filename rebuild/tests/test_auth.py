"""Authentication: hashing, registration, login and logout state."""

from pawmatch import auth, db


def test_hash_is_salted_and_not_plain_text():
    first, second = auth.hash_password("correct horse"), auth.hash_password("correct horse")
    assert first != second
    assert "correct horse" not in first
    assert first.startswith("scrypt$")


def test_verify_password_accepts_right_and_rejects_wrong():
    stored = auth.hash_password("correct horse")
    assert auth.verify_password("correct horse", stored)
    assert not auth.verify_password("Correct horse", stored)


def test_verify_password_rejects_malformed_hash():
    assert not auth.verify_password("anything", "plain-text-password")
    assert not auth.verify_password("anything", "md5$1$1$1$00$00")


def test_register_stores_hash_not_password(conn):
    user, errors = auth.register(conn, "Sam", "sam@example.com", 30, "longenough", "longenough")
    assert errors == {} and user.role == "user"
    stored = conn.execute("SELECT password_hash FROM users").fetchone()[0]
    assert stored != "longenough" and auth.verify_password("longenough", stored)


def test_register_rejects_duplicate_email_case_insensitively(conn):
    auth.register(conn, "Sam", "sam@example.com", 30, "longenough", "longenough")
    user, errors = auth.register(conn, "Sam 2", "SAM@example.com", 31, "longenough", "longenough")
    assert user is None and "already exists" in errors["email"]


def test_register_returns_validation_errors_without_saving(conn):
    user, errors = auth.register(conn, "", "bad", 12, "short", "short")
    assert user is None and set(errors) >= {"name", "email", "age", "password"}
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0


def test_login_success_and_email_is_normalised(conn):
    auth.register(conn, "Sam", "sam@example.com", 30, "longenough", "longenough")
    user, errors = auth.login(conn, "  Sam@Example.com ", "longenough")
    assert errors == {} and user.email == "sam@example.com"


def test_wrong_password_and_unknown_email_give_the_same_message(conn):
    auth.register(conn, "Sam", "sam@example.com", 30, "longenough", "longenough")
    _, wrong_password = auth.login(conn, "sam@example.com", "nottheone")
    _, unknown_email = auth.login(conn, "nobody@example.com", "longenough")
    assert wrong_password == unknown_email == {"login": auth.LOGIN_FAILED}


def test_blank_login_is_rejected_before_lookup(conn):
    user, errors = auth.login(conn, "", "")
    assert user is None and set(errors) == {"email", "password"}


def test_role_is_read_from_database(conn):
    user, _ = auth.register(conn, "Staff", "staff@example.com", 40, "longenough", "longenough")
    db.set_role(conn, user.user_id, "admin")
    logged_in, _ = auth.login(conn, "staff@example.com", "longenough")
    assert logged_in.is_admin
