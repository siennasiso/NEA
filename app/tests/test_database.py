"""Database and demonstration-login tests for PawMatch."""

from pathlib import Path
import sys
import tempfile
import unittest

APP_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIRECTORY))

import pawmatch_auth
from pawmatch_animals import (
    fetch_animals,
    initialise_animals_table,
    seed_demo_animals,
    validate_animal,
    validate_animal_search,
)
from pawmatch_auth import (
    authenticate_user,
    create_user,
    ensure_demo_admin,
    initialise_database,
    validate_registration,
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
        self.assertEqual(seed_demo_animals(), 13)
        self.assertEqual(seed_demo_animals(), 0)
        self.assertEqual(len(fetch_animals()), 13)
        self.assertGreaterEqual(len(fetch_animals(status="Available")), 10)

    def test_registration_uses_documented_name_and_password_limits(self) -> None:
        errors, _ = validate_registration(
            "A" * 50, "valid@example.com", 24, "abcdefghi", "abcdefghi"
        )
        self.assertEqual(errors, {})

        errors, _ = validate_registration(
            "A" * 51, "another@example.com", 24, "abcdefgh", "abcdefgh"
        )
        self.assertIn("name", errors)
        self.assertIn("password", errors)

    def test_registration_rejects_an_email_already_in_the_database(self) -> None:
        created, message = create_user(
            "Existing User", "existing@example.com", 24, "abcdefghi"
        )
        self.assertTrue(created, message)
        errors, _ = validate_registration(
            "New User", "EXISTING@example.com", 25, "abcdefghi", "abcdefghi"
        )
        self.assertIn("email", errors)

    def test_animal_validation_uses_documented_text_and_hour_limits(self) -> None:
        seed_demo_animals()
        animal = fetch_animals()[0]
        animal.update(
            name="7",
            breed="A1",
            description="A" * 20,
            max_hours_alone=24,
            garden_required=1,
        )
        errors, cleaned = validate_animal(animal)
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["max_hours_alone"], 24)

        animal.update(name="A" * 51, breed="--", description="A" * 19)
        errors, _ = validate_animal(animal)
        self.assertIn("name", errors)
        self.assertIn("breed", errors)
        self.assertIn("description", errors)

    def test_browse_search_validation_matches_documented_limits(self) -> None:
        errors, cleaned = validate_animal_search("  Luna  ", "Dog", "Small")
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["search"], "Luna")

        errors, _ = validate_animal_search("x" * 21, "Horse", "Huge")
        self.assertEqual(set(errors), {"search", "species", "size"})

    def test_old_twelve_hour_database_constraint_is_migrated(self) -> None:
        with pawmatch_auth.get_connection() as connection:
            schema = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'animals'"
            ).fetchone()["sql"]
            connection.execute("DROP TABLE animals")
            connection.execute(str(schema).replace("BETWEEN 0 AND 24", "BETWEEN 0 AND 12"))

        initialise_animals_table()
        with pawmatch_auth.get_connection() as connection:
            migrated_schema = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'animals'"
            ).fetchone()["sql"]
        self.assertIn("max_hours_alone BETWEEN 0 AND 24", migrated_schema)


if __name__ == "__main__":
    unittest.main()
