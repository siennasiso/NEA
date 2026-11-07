"""Questionnaire persistence and weighted animal-matching logic for PawMatch."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from pawmatch_animals import fetch_animals, initialise_animals_table
from pawmatch_auth import get_connection, initialise_database

HOUSING_OPTIONS = {
    "Flat or limited space": 1,
    "Small or medium house": 2,
    "Large house": 3,
}
ACTIVITY_OPTIONS = {
    "Low": 1,
    "Moderate": 2,
    "High": 3,
}
SPECIES_OPTIONS = ("Dog", "Cat", "Rabbit", "No preference")
SIZE_OPTIONS = ("Small", "Medium", "Large", "No preference")

WEIGHTS = {
    "hours_left_alone": 20,
    "children": 15,
    "housing": 15,
    "activity": 12,
    "garden": 10,
}
MAX_COMPATIBILITY_POINTS = sum(WEIGHTS.values())
MINIMUM_RECOMMENDATION_SCORE = 70


def initialise_matching_tables() -> None:
    """Create the questionnaire-response and calculated-match tables."""
    initialise_database()
    initialise_animals_table()
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS questionnaire_responses (
                response_id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id                  INTEGER NOT NULL,
                housing_level            INTEGER NOT NULL CHECK (housing_level BETWEEN 1 AND 3),
                garden_access            INTEGER NOT NULL CHECK (garden_access IN (0, 1)),
                hours_left_alone          INTEGER NOT NULL CHECK (hours_left_alone BETWEEN 0 AND 24),
                has_children             INTEGER NOT NULL CHECK (has_children IN (0, 1)),
                preferred_activity_level INTEGER NOT NULL
                                         CHECK (preferred_activity_level BETWEEN 1 AND 3),
                preferred_species        TEXT NOT NULL
                                         CHECK (preferred_species IN ('Dog', 'Cat', 'Rabbit', 'No preference')),
                preferred_size           TEXT NOT NULL
                                         CHECK (preferred_size IN ('Small', 'Medium', 'Large', 'No preference')),
                completed_at             TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS match_results (
                match_id             INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id          INTEGER NOT NULL,
                animal_id            INTEGER NOT NULL,
                compatibility_score  REAL NOT NULL CHECK (compatibility_score BETWEEN 0 AND 100),
                preference_score     INTEGER NOT NULL CHECK (preference_score BETWEEN 0 AND 15),
                is_eligible          INTEGER NOT NULL CHECK (is_eligible IN (0, 1)),
                match_category       TEXT NOT NULL
                                     CHECK (match_category IN ('Strong', 'Good', 'Possible', 'Low', 'Ineligible')),
                matched_requirements TEXT NOT NULL DEFAULT '[]',
                unmet_requirements   TEXT NOT NULL DEFAULT '[]',
                calculated_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (response_id, animal_id),
                FOREIGN KEY (response_id) REFERENCES questionnaire_responses(response_id) ON DELETE CASCADE,
                FOREIGN KEY (animal_id) REFERENCES animals(animal_id) ON DELETE CASCADE
            )
            """
        )
        columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(match_results)")
        }
        if "preference_score" not in columns or "is_eligible" not in columns:
            connection.execute("ALTER TABLE match_results RENAME TO match_results_legacy")
            connection.execute(
                """
                CREATE TABLE match_results (
                    match_id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    response_id          INTEGER NOT NULL,
                    animal_id            INTEGER NOT NULL,
                    compatibility_score  REAL NOT NULL CHECK (compatibility_score BETWEEN 0 AND 100),
                    preference_score     INTEGER NOT NULL CHECK (preference_score BETWEEN 0 AND 15),
                    is_eligible          INTEGER NOT NULL CHECK (is_eligible IN (0, 1)),
                    match_category       TEXT NOT NULL
                                         CHECK (match_category IN ('Strong', 'Good', 'Possible', 'Low', 'Ineligible')),
                    matched_requirements TEXT NOT NULL DEFAULT '[]',
                    unmet_requirements   TEXT NOT NULL DEFAULT '[]',
                    calculated_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (response_id, animal_id),
                    FOREIGN KEY (response_id) REFERENCES questionnaire_responses(response_id) ON DELETE CASCADE,
                    FOREIGN KEY (animal_id) REFERENCES animals(animal_id) ON DELETE CASCADE
                )
                """
            )
            connection.execute(
                """
                INSERT INTO match_results (
                    match_id, response_id, animal_id, compatibility_score,
                    preference_score, is_eligible, match_category,
                    matched_requirements, unmet_requirements, calculated_at
                )
                SELECT match_id, response_id, animal_id, compatibility_score,
                       ranking_score, 1, match_category,
                       matched_requirements, unmet_requirements, calculated_at
                FROM match_results_legacy
                """
            )
            connection.execute("DROP TABLE match_results_legacy")
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_questionnaire_user_completed
            ON questionnaire_responses (user_id, completed_at DESC, response_id DESC)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_matches_response_rank
            ON match_results (
                response_id, is_eligible DESC, compatibility_score DESC,
                preference_score DESC, animal_id ASC
            )
            """
        )


def validate_questionnaire(values: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    """Validate the seven designed questions and return errors plus clean values."""
    cleaned = dict(values)
    errors: dict[str, str] = {}

    for field, label in (
        ("housing_level", "housing level"),
        ("preferred_activity_level", "activity level"),
    ):
        try:
            cleaned[field] = int(cleaned.get(field))
        except (TypeError, ValueError):
            errors[field] = f"Select a {label} from 1 to 3."
        else:
            if cleaned[field] not in {1, 2, 3}:
                errors[field] = f"Select a {label} from 1 to 3."

    try:
        cleaned["hours_left_alone"] = int(cleaned.get("hours_left_alone"))
    except (TypeError, ValueError):
        errors["hours_left_alone"] = "Enter a whole number from 0 to 24."
    else:
        if not 0 <= cleaned["hours_left_alone"] <= 24:
            errors["hours_left_alone"] = "Enter a whole number from 0 to 24."

    for field, label in (
        ("garden_access", "garden access"),
        ("has_children", "whether children live in the home"),
    ):
        value = cleaned.get(field)
        if value not in {True, False, 0, 1}:
            errors[field] = f"Select {label}."
        else:
            cleaned[field] = bool(value)

    if cleaned.get("preferred_species") not in SPECIES_OPTIONS:
        errors["preferred_species"] = "Select a supported species or No preference."
    if cleaned.get("preferred_size") not in SIZE_OPTIONS:
        errors["preferred_size"] = "Select a size or No preference."

    return errors, cleaned


def save_questionnaire_response(user_id: int, values: dict[str, Any]) -> int:
    """Validate and persist a completed response, returning its database ID."""
    errors, cleaned = validate_questionnaire(values)
    if errors:
        raise ValueError("The questionnaire contains invalid answers.")
    initialise_matching_tables()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO questionnaire_responses (
                user_id, housing_level, garden_access, hours_left_alone,
                has_children, preferred_activity_level, preferred_species,
                preferred_size
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                cleaned["housing_level"],
                int(cleaned["garden_access"]),
                cleaned["hours_left_alone"],
                int(cleaned["has_children"]),
                cleaned["preferred_activity_level"],
                cleaned["preferred_species"],
                cleaned["preferred_size"],
            ),
        )
        return int(cursor.lastrowid)


def _match_category(score: float, has_compulsory_failure: bool = False) -> str:
    """Convert a score and compulsory checks into the designed category label."""
    if has_compulsory_failure:
        return "Ineligible"
    if score >= 90:
        return "Strong"
    if score >= 80:
        return "Good"
    if score >= 70:
        return "Possible"
    return "Low"


def calculate_match(animal: dict[str, Any], answers: dict[str, Any]) -> dict[str, Any]:
    """Calculate one animal's welfare score and separate preference score."""
    errors, cleaned = validate_questionnaire(answers)
    if errors:
        raise ValueError("The questionnaire contains invalid answers.")

    points = 0
    matched: list[str] = []
    unmet: list[str] = []
    compulsory_failures: list[str] = []
    animal_name = str(animal["name"])
    selected_hours = int(cleaned["hours_left_alone"])
    maximum_hours = int(animal["max_hours_left_alone"])

    if selected_hours <= maximum_hours:
        points += WEIGHTS["hours_left_alone"]
        matched.append(
            f"Time alone: you selected {selected_hours} hour(s) per day; "
            f"{animal_name} can be left for up to {maximum_hours} hour(s)."
        )
    else:
        reason = (
            f"Time alone: you selected {selected_hours} hour(s) per day, but "
            f"{animal_name} can be left for no more than {maximum_hours} hour(s)."
        )
        unmet.append(reason)
        compulsory_failures.append(reason)

    children_suitable = not cleaned["has_children"] or bool(animal["child_compatible"])
    if children_suitable:
        points += WEIGHTS["children"]
        if cleaned["has_children"]:
            matched.append(
                f"Children: you selected a home with children and {animal_name} "
                "is listed as child friendly."
            )
        else:
            matched.append(
                f"Children: you selected a home without children, which meets "
                f"{animal_name}'s child-suitability requirement."
            )
    else:
        reason = (
            f"Children: you selected a home with children, but {animal_name}'s "
            "profile is not suitable for a home with children."
        )
        unmet.append(reason)
        compulsory_failures.append(reason)

    selected_housing = int(cleaned["housing_level"])
    required_housing = int(animal["recommended_housing_level"])
    if selected_housing >= required_housing:
        points += WEIGHTS["housing"]
        matched.append(
            f"Indoor space: your selected space level is {selected_housing} of 3; "
            f"{animal_name} requires level {required_housing} of 3."
        )
    else:
        unmet.append(
            f"Indoor space: your selected space level is {selected_housing} of 3, "
            f"but {animal_name} requires level {required_housing} of 3."
        )

    animal_activity = ACTIVITY_OPTIONS[str(animal["exercise_needs"])]
    if cleaned["preferred_activity_level"] >= animal_activity:
        points += WEIGHTS["activity"]
        matched.append(
            f"Activity: you can support level {cleaned['preferred_activity_level']} of 3; "
            f"{animal_name} needs {str(animal['exercise_needs']).lower()} activity "
            f"(level {animal_activity} of 3)."
        )
    else:
        unmet.append(
            f"Activity: you can support level {cleaned['preferred_activity_level']} of 3, "
            f"but {animal_name} needs {str(animal['exercise_needs']).lower()} activity "
            f"(level {animal_activity} of 3)."
        )

    if not bool(animal["garden_required"]) or cleaned["garden_access"]:
        points += WEIGHTS["garden"]
        if bool(animal["garden_required"]):
            matched.append(
                f"Garden: you selected secure garden access and {animal_name} requires a garden."
            )
        else:
            matched.append(
                f"Garden: {animal_name} does not require a garden, so your selected home is suitable."
            )
    else:
        reason = (
            f"Garden: you selected no garden access, but {animal_name} requires a secure garden."
        )
        unmet.append(reason)
        compulsory_failures.append(reason)

    compatibility = round((points / MAX_COMPATIBILITY_POINTS) * 100, 1)
    preference_score = 0
    if cleaned["preferred_species"] != "No preference" and cleaned["preferred_species"] == animal["species"]:
        preference_score += 10
    if cleaned["preferred_size"] != "No preference" and cleaned["preferred_size"] == animal["size"]:
        preference_score += 5

    is_eligible = not compulsory_failures and compatibility >= MINIMUM_RECOMMENDATION_SCORE

    return {
        "animal_id": int(animal["animal_id"]),
        "compatibility_score": compatibility,
        "preference_score": preference_score,
        "match_category": _match_category(compatibility, bool(compulsory_failures)),
        "is_eligible": is_eligible,
        "matched_requirements": matched,
        "unmet_requirements": unmet,
        "compulsory_failures": compulsory_failures,
    }


def calculate_and_store_matches(response_id: int, answers: dict[str, Any]) -> list[dict[str, Any]]:
    """Persist every result in compatibility-first recommendation order."""
    initialise_matching_tables()
    results = [calculate_match(animal, answers) for animal in fetch_animals()]
    results.sort(
        key=lambda item: (
            -item["compatibility_score"], -item["preference_score"], item["animal_id"]
        )
    )
    with get_connection() as connection:
        connection.execute("DELETE FROM match_results WHERE response_id = ?", (response_id,))
        connection.executemany(
            """
            INSERT INTO match_results (
                response_id, animal_id, compatibility_score, preference_score,
                is_eligible, match_category, matched_requirements, unmet_requirements
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    response_id,
                    result["animal_id"],
                    result["compatibility_score"],
                    result["preference_score"],
                    int(result["is_eligible"]),
                    result["match_category"],
                    json.dumps(result["matched_requirements"]),
                    json.dumps(result["unmet_requirements"]),
                )
                for result in results
            ],
        )
    return results


def fetch_latest_response(user_id: int) -> dict[str, Any] | None:
    """Return a user's newest questionnaire response, with booleans restored."""
    initialise_matching_tables()
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM questionnaire_responses
            WHERE user_id = ?
            ORDER BY datetime(completed_at) DESC, response_id DESC
            LIMIT 1
            """,
            (int(user_id),),
        ).fetchone()
    if row is None:
        return None
    response = dict(row)
    response["garden_access"] = bool(response["garden_access"])
    response["has_children"] = bool(response["has_children"])
    return response


def fetch_latest_matches(user_id: int, include_low: bool = False) -> list[dict[str, Any]]:
    """Return the newest response's recommendation-eligible animal matches."""
    latest = fetch_latest_response(user_id)
    if latest is None:
        return []
    condition = "" if include_low else "AND mr.is_eligible = 1"
    parameters: tuple[Any, ...] = (latest["response_id"],)
    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT mr.*,
                   a.name, a.species, a.breed, a.age_years, a.sex,
                   a.size, a.exercise_needs, a.home_type,
                   a.recommended_housing_level, a.garden_required,
                   a.child_compatible, a.max_hours_left_alone,
                   a.description, a.image
            FROM match_results AS mr
            JOIN animals AS a ON a.animal_id = mr.animal_id
            WHERE mr.response_id = ? {condition}
            ORDER BY mr.compatibility_score DESC, mr.preference_score DESC,
                     mr.animal_id ASC
            """,
            parameters,
        ).fetchall()
    matches = [dict(row) for row in rows]
    for match in matches:
        match["matched_requirements"] = json.loads(match["matched_requirements"])
        match["unmet_requirements"] = json.loads(match["unmet_requirements"])
    return matches
