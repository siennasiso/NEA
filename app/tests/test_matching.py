"""Tests for questionnaire validation, persistence and weighted matching."""

from pathlib import Path
import sys
import tempfile
import unittest

APP_DIRECTORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP_DIRECTORY))

import pawmatch_auth
from pawmatch_animals import fetch_animals, initialise_animals_table, seed_demo_animals
from pawmatch_auth import authenticate_user, create_user, initialise_database
from pawmatch_matching import (
    MINIMUM_RECOMMENDATION_SCORE,
    calculate_and_store_matches,
    calculate_match,
    fetch_latest_matches,
    fetch_latest_response,
    initialise_matching_tables,
    save_questionnaire_response,
    validate_questionnaire,
    _match_category,
)


class MatchingTests(unittest.TestCase):
    """Exercise the algorithm against an isolated SQLite database."""

    def setUp(self) -> None:
        """Create tables, one adopter and the repeatable animal dataset."""
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_database_path = pawmatch_auth.DATABASE_PATH
        pawmatch_auth.DATABASE_PATH = Path(self.temporary_directory.name) / "test.db"
        initialise_database()
        initialise_animals_table()
        initialise_matching_tables()
        seed_demo_animals()
        created, message = create_user(
            "Test Adopter", "match@example.com", 24, "Password123"
        )
        self.assertTrue(created, message)
        self.user_id = int(
            authenticate_user("match@example.com", "Password123")["user_id"]
        )
        self.answers = {
            "housing_level": 3,
            "garden_access": True,
            "hours_left_alone": 2,
            "has_children": False,
            "preferred_activity_level": 3,
            "preferred_species": "Dog",
            "preferred_size": "Small",
        }

    def tearDown(self) -> None:
        """Restore the application database path and remove test files."""
        pawmatch_auth.DATABASE_PATH = self.original_database_path
        self.temporary_directory.cleanup()

    def test_questionnaire_accepts_only_designed_ranges(self) -> None:
        """Valid answers clean successfully and invalid ranges are rejected."""
        errors, cleaned = validate_questionnaire(self.answers)
        self.assertEqual(errors, {})
        self.assertEqual(cleaned["housing_level"], 3)

        invalid = dict(self.answers, hours_left_alone=25, housing_level=4)
        errors, _ = validate_questionnaire(invalid)
        self.assertIn("hours_left_alone", errors)
        self.assertIn("housing_level", errors)

    def test_preference_score_changes_ranking_not_compatibility(self) -> None:
        """A qualifying preferred animal keeps the same visible welfare score."""
        oscar = next(animal for animal in fetch_animals() if animal["name"] == "Oscar")
        preferred = calculate_match(oscar, self.answers)
        neutral = calculate_match(
            oscar,
            dict(self.answers, preferred_species="No preference", preferred_size="No preference"),
        )
        self.assertEqual(preferred["compatibility_score"], neutral["compatibility_score"])
        self.assertEqual(preferred["preference_score"], neutral["preference_score"] + 15)

    def test_requirement_explanations_include_selected_and_required_values(self) -> None:
        """Result explanations state the user's value and the animal's requirement."""
        oscar = next(animal for animal in fetch_animals() if animal["name"] == "Oscar")
        result = calculate_match(oscar, self.answers)
        explanations = " ".join(
            result["matched_requirements"] + result["unmet_requirements"]
        )
        self.assertIn("you selected 2 hour(s)", explanations)
        self.assertIn("Oscar can be left for up to 5 hour(s)", explanations)
        self.assertIn("your selected space level is 3 of 3", explanations)

    def test_preferences_do_not_make_an_ineligible_animal_eligible(self) -> None:
        """Preference points are separate and cannot override compulsory failures."""
        max_profile = next(animal for animal in fetch_animals() if animal["name"] == "Max")
        unsuitable = {
            "housing_level": 1,
            "garden_access": False,
            "hours_left_alone": 24,
            "has_children": True,
            "preferred_activity_level": 1,
            "preferred_species": "Dog",
            "preferred_size": "Large",
        }
        result = calculate_match(max_profile, unsuitable)
        self.assertLess(result["compatibility_score"], MINIMUM_RECOMMENDATION_SCORE)
        self.assertEqual(result["preference_score"], 15)
        self.assertFalse(result["is_eligible"])
        self.assertEqual(result["match_category"], "Ineligible")
        self.assertTrue(result["compulsory_failures"])

    def test_match_categories_use_the_documented_boundaries(self) -> None:
        self.assertEqual(_match_category(90), "Strong")
        self.assertEqual(_match_category(89.9), "Good")
        self.assertEqual(_match_category(79.9), "Possible")
        self.assertEqual(_match_category(69.9), "Low")
        self.assertEqual(_match_category(100, has_compulsory_failure=True), "Ineligible")

    def test_response_and_all_match_results_are_persisted(self) -> None:
        """Submission stores every result while the normal view returns eligible ones."""
        response_id = save_questionnaire_response(self.user_id, self.answers)
        calculated = calculate_and_store_matches(response_id, self.answers)
        expected_eligible = sum(
            calculate_match(animal, self.answers)["is_eligible"]
            for animal in fetch_animals()
        )
        self.assertEqual(len(calculated), len(fetch_animals()))
        with pawmatch_auth.get_connection() as connection:
            stored_count = connection.execute(
                "SELECT COUNT(*) FROM match_results WHERE response_id = ?", (response_id,)
            ).fetchone()[0]
        self.assertEqual(stored_count, len(fetch_animals()))

        latest = fetch_latest_response(self.user_id)
        self.assertEqual(latest["response_id"], response_id)
        displayed = fetch_latest_matches(self.user_id)
        self.assertEqual(len(displayed), expected_eligible)
        self.assertTrue(
            all(
                match["compatibility_score"] >= MINIMUM_RECOMMENDATION_SCORE
                for match in displayed
            )
        )
        ranking_keys = [
            (
                match["compatibility_score"],
                match["preference_score"],
                -match["animal_id"],
            )
            for match in displayed
        ]
        self.assertEqual(ranking_keys, sorted(ranking_keys, reverse=True))


if __name__ == "__main__":
    unittest.main()
