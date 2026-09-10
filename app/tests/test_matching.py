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
    calculate_and_store_matches,
    calculate_match,
    fetch_latest_matches,
    fetch_latest_response,
    initialise_matching_tables,
    save_questionnaire_response,
    validate_questionnaire,
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

    def test_preference_bonus_changes_ranking_not_compatibility(self) -> None:
        """A suitable preferred animal keeps the same visible welfare score."""
        oscar = next(animal for animal in fetch_animals() if animal["name"] == "Oscar")
        preferred = calculate_match(oscar, self.answers)
        neutral = calculate_match(
            oscar,
            dict(self.answers, preferred_species="No preference", preferred_size="No preference"),
        )
        self.assertEqual(preferred["compatibility_score"], neutral["compatibility_score"])
        self.assertEqual(preferred["ranking_score"], neutral["ranking_score"] + 15)

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

    def test_low_score_never_receives_preference_bonus(self) -> None:
        """Species and size cannot promote an animal below the 60% threshold."""
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
        self.assertLess(result["compatibility_score"], 60)
        self.assertEqual(result["ranking_score"], result["compatibility_score"])

    def test_response_and_available_matches_are_persisted(self) -> None:
        """Submission stores one response and results only for available animals."""
        response_id = save_questionnaire_response(self.user_id, self.answers)
        calculated = calculate_and_store_matches(response_id, self.answers)
        available_count = len(fetch_animals(status="Available"))
        self.assertEqual(len(calculated), available_count)

        latest = fetch_latest_response(self.user_id)
        self.assertEqual(latest["response_id"], response_id)
        displayed = fetch_latest_matches(self.user_id)
        self.assertTrue(all(match["match_category"] != "Low" for match in displayed))
        ranking_scores = [match["ranking_score"] for match in displayed]
        self.assertEqual(ranking_scores, sorted(ranking_scores, reverse=True))


if __name__ == "__main__":
    unittest.main()
