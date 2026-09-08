"""Database and demonstration-login tests for PawMatch."""

from pathlib import Path
import sys
import tempfile
import unittest

APP_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIRECTORY))

import pawmatch_auth
from pawmatch_animals import fetch_animals, initialise_animals_table, seed_demo_animals
from pawmatch_auth import (
    authenticate_user,
    create_user,
    ensure_demo_admin,
    initialise_database,
)


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_database_path = pawmatch_auth.DATABASE_PATH
        pawmatch_auth.DATABASE_PATH = Path(self.temporary_directory.name) / "test.db"
        initialise_database()
        initialise_animals_table()

    def tearDown(self) -> None:
        pawmatch_auth.DATABASE_PATH = self.original_database_path
        self.temporary_directory.cleanup()

    def test_demo_admin_can_log_in_by_username(self) -> None:
        user_id, created = ensure_demo_admin()

        self.assertTrue(created)
        account = authenticate_user("admin123", "password123")
        self.assertIsNotNone(account)
        self.assertEqual(account["user_id"], user_id)
        self.assertEqual(account["role"], "admin")
        self.assertIsNone(authenticate_user("admin123", "wrong-password"))

    def test_demo_setup_is_repeatable(self) -> None:
        first_id, first_created = ensure_demo_admin()
        second_id, second_created = ensure_demo_admin()

        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(first_id, second_id)
        self.assertEqual(authenticate_user("admin123", "password123")["role"], "admin")

    def test_adopter_can_still_log_in_by_email(self) -> None:
        created, message = create_user(
            "Test Adopter", "adopter@example.com", 24, "Password123"
        )

        self.assertTrue(created, message)
        account = authenticate_user("ADOPTER@example.com", "Password123")
        self.assertIsNotNone(account)
        self.assertEqual(account["role"], "user")

    def test_demo_animals_are_added_only_once(self) -> None:
        self.assertEqual(seed_demo_animals(), 4)
        self.assertEqual(seed_demo_animals(), 0)
        self.assertEqual(len(fetch_animals()), 4)


if __name__ == "__main__":
    unittest.main()
