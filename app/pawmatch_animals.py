"""SQLite helpers for PawMatch animal records and administrator CRUD actions."""

from __future__ import annotations

import re
import sqlite3
from typing import Any, Iterable

from pawmatch_auth import get_connection

SPECIES = ("Dog", "Cat", "Rabbit")
SEXES = ("Female", "Male")
SIZES = ("Small", "Medium", "Large")
ACTIVITY_LEVELS = ("Low", "Moderate", "High")
HOME_TYPES = ("Flat or apartment", "House", "Either")
CHILD_FRIENDLY_OPTIONS = ("Yes", "No", "Older children only")
OTHER_PETS_OPTIONS = ("Yes", "No", "Depends")
EXPERIENCE_LEVELS = ("First-time owner", "Some experience", "Experienced owner")
ANIMAL_STATUSES = ("Available", "Reserved", "Adopted")

_IMAGE_URL_PATTERN = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)
_NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ' -]+$")


def initialise_animals_table() -> None:
    """Create the animals table when the administration feature first runs."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS animals (
                animal_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name               TEXT NOT NULL,
                species            TEXT NOT NULL
                                   CHECK (species IN ('Dog', 'Cat', 'Rabbit')),
                breed              TEXT NOT NULL,
                age_years          REAL NOT NULL
                                   CHECK (age_years BETWEEN 0 AND 40),
                sex                TEXT NOT NULL
                                   CHECK (sex IN ('Female', 'Male')),
                size               TEXT NOT NULL
                                   CHECK (size IN ('Small', 'Medium', 'Large')),
                activity_level     TEXT NOT NULL
                                   CHECK (activity_level IN ('Low', 'Moderate', 'High')),
                home_type          TEXT NOT NULL
                                   CHECK (home_type IN ('Flat or apartment', 'House', 'Either')),
                garden_required    INTEGER NOT NULL DEFAULT 0
                                   CHECK (garden_required IN (0, 1)),
                child_friendly     TEXT NOT NULL
                                   CHECK (child_friendly IN ('Yes', 'No', 'Older children only')),
                other_pets         TEXT NOT NULL
                                   CHECK (other_pets IN ('Yes', 'No', 'Depends')),
                experience_level   TEXT NOT NULL
                                   CHECK (experience_level IN (
                                       'First-time owner',
                                       'Some experience',
                                       'Experienced owner'
                                   )),
                max_hours_alone    INTEGER NOT NULL
                                   CHECK (max_hours_alone BETWEEN 0 AND 12),
                status             TEXT NOT NULL DEFAULT 'Available'
                                   CHECK (status IN ('Available', 'Reserved', 'Adopted')),
                description        TEXT NOT NULL,
                image_url          TEXT,
                created_at         TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at         TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_animals_species_status
            ON animals (species, status)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_animals_name
            ON animals (name COLLATE NOCASE)
            """
        )


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def validate_animal(values: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    """Validate an animal record and return field errors plus cleaned values."""
    cleaned: dict[str, Any] = {
        "name": _clean_text(values.get("name")),
        "species": _clean_text(values.get("species")),
        "breed": _clean_text(values.get("breed")),
        "age_years": values.get("age_years"),
        "sex": _clean_text(values.get("sex")),
        "size": _clean_text(values.get("size")),
        "activity_level": _clean_text(values.get("activity_level")),
        "home_type": _clean_text(values.get("home_type")),
        "garden_required": bool(values.get("garden_required", False)),
        "child_friendly": _clean_text(values.get("child_friendly")),
        "other_pets": _clean_text(values.get("other_pets")),
        "experience_level": _clean_text(values.get("experience_level")),
        "max_hours_alone": values.get("max_hours_alone"),
        "status": _clean_text(values.get("status")),
        "description": str(values.get("description") or "").strip(),
        "image_url": str(values.get("image_url") or "").strip(),
    }
    errors: dict[str, str] = {}

    if not cleaned["name"]:
        errors["name"] = "Enter the animal's name."
    elif not 2 <= len(cleaned["name"]) <= 40:
        errors["name"] = "The name must contain between 2 and 40 characters."
    elif _NAME_PATTERN.fullmatch(cleaned["name"]) is None:
        errors["name"] = "Use letters, spaces, hyphens or apostrophes only."

    if cleaned["species"] not in SPECIES:
        errors["species"] = "Select a supported species."

    if not cleaned["breed"]:
        errors["breed"] = "Enter a breed or use 'Mixed breed'."
    elif len(cleaned["breed"]) > 60:
        errors["breed"] = "The breed must contain 60 characters or fewer."

    try:
        cleaned["age_years"] = float(cleaned["age_years"])
    except (TypeError, ValueError):
        errors["age_years"] = "Enter the animal's age."
    else:
        if not 0 <= cleaned["age_years"] <= 40:
            errors["age_years"] = "Enter an age between 0 and 40 years."

    allowed_values = {
        "sex": SEXES,
        "size": SIZES,
        "activity_level": ACTIVITY_LEVELS,
        "home_type": HOME_TYPES,
        "child_friendly": CHILD_FRIENDLY_OPTIONS,
        "other_pets": OTHER_PETS_OPTIONS,
        "experience_level": EXPERIENCE_LEVELS,
        "status": ANIMAL_STATUSES,
    }
    messages = {
        "sex": "Select the animal's sex.",
        "size": "Select a size.",
        "activity_level": "Select an activity level.",
        "home_type": "Select a suitable home type.",
        "child_friendly": "Select the animal's suitability for children.",
        "other_pets": "Select the animal's suitability with other pets.",
        "experience_level": "Select the required owner experience.",
        "status": "Select a valid adoption status.",
    }
    for field, valid_options in allowed_values.items():
        if cleaned[field] not in valid_options:
            errors[field] = messages[field]

    try:
        cleaned["max_hours_alone"] = int(cleaned["max_hours_alone"])
    except (TypeError, ValueError):
        errors["max_hours_alone"] = "Enter the maximum number of hours alone."
    else:
        if not 0 <= cleaned["max_hours_alone"] <= 12:
            errors["max_hours_alone"] = "Enter a value between 0 and 12 hours."

    if not cleaned["description"]:
        errors["description"] = "Enter a short profile description."
    elif len(cleaned["description"]) < 30:
        errors["description"] = "Use at least 30 characters so adopters receive useful information."
    elif len(cleaned["description"]) > 1200:
        errors["description"] = "The description must contain no more than 1,200 characters."

    if cleaned["image_url"] and _IMAGE_URL_PATTERN.fullmatch(cleaned["image_url"]) is None:
        errors["image_url"] = "Enter a complete http:// or https:// image address."

    return errors, cleaned


def _database_values(animal: dict[str, Any]) -> tuple[Any, ...]:
    return (
        animal["name"],
        animal["species"],
        animal["breed"],
        animal["age_years"],
        animal["sex"],
        animal["size"],
        animal["activity_level"],
        animal["home_type"],
        int(animal["garden_required"]),
        animal["child_friendly"],
        animal["other_pets"],
        animal["experience_level"],
        animal["max_hours_alone"],
        animal["status"],
        animal["description"],
        animal["image_url"] or None,
    )


def create_animal(animal: dict[str, Any]) -> tuple[bool, int | None, str]:
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO animals (
                    name, species, breed, age_years, sex, size, activity_level,
                    home_type, garden_required, child_friendly, other_pets,
                    experience_level, max_hours_alone, status, description, image_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _database_values(animal),
            )
            animal_id = int(cursor.lastrowid)
        return True, animal_id, ""
    except sqlite3.IntegrityError:
        return False, None, "The record could not be saved because one or more values were invalid."
    except sqlite3.Error:
        return False, None, "The database is unavailable. Please try again."


def update_animal(animal_id: int, animal: dict[str, Any]) -> tuple[bool, str]:
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                UPDATE animals
                SET name = ?, species = ?, breed = ?, age_years = ?, sex = ?,
                    size = ?, activity_level = ?, home_type = ?, garden_required = ?,
                    child_friendly = ?, other_pets = ?, experience_level = ?,
                    max_hours_alone = ?, status = ?, description = ?, image_url = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE animal_id = ?
                """,
                (*_database_values(animal), animal_id),
            )
            if cursor.rowcount == 0:
                return False, "That animal record no longer exists."
        return True, ""
    except sqlite3.IntegrityError:
        return False, "The record could not be updated because one or more values were invalid."
    except sqlite3.Error:
        return False, "The database is unavailable. Please try again."


def delete_animal(animal_id: int) -> tuple[bool, str]:
    try:
        with get_connection() as connection:
            cursor = connection.execute("DELETE FROM animals WHERE animal_id = ?", (animal_id,))
            if cursor.rowcount == 0:
                return False, "That animal record no longer exists."
        return True, ""
    except sqlite3.Error:
        return False, "The database is unavailable. Please try again."


def fetch_animal(animal_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute("SELECT * FROM animals WHERE animal_id = ?", (animal_id,)).fetchone()
    return dict(row) if row is not None else None


def fetch_animals(
    search_text: str = "",
    species: str = "All species",
    status: str = "All statuses",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    parameters: list[Any] = []

    cleaned_search = _clean_text(search_text)
    if cleaned_search:
        clauses.append("(name LIKE ? COLLATE NOCASE OR breed LIKE ? COLLATE NOCASE)")
        pattern = f"%{cleaned_search}%"
        parameters.extend((pattern, pattern))

    if species in SPECIES:
        clauses.append("species = ?")
        parameters.append(species)
    if status in ANIMAL_STATUSES:
        clauses.append("status = ?")
        parameters.append(status)

    query = "SELECT * FROM animals"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY datetime(updated_at) DESC, animal_id DESC"
    if limit is not None:
        query += " LIMIT ?"
        parameters.append(max(1, int(limit)))

    with get_connection() as connection:
        rows = connection.execute(query, tuple(parameters)).fetchall()
    return [dict(row) for row in rows]


def get_admin_summary() -> dict[str, int]:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) AS available,
                SUM(CASE WHEN status = 'Reserved' THEN 1 ELSE 0 END) AS reserved,
                SUM(CASE WHEN status = 'Adopted' THEN 1 ELSE 0 END) AS adopted,
                SUM(CASE WHEN image_url IS NULL OR TRIM(image_url) = ''
                              OR LENGTH(TRIM(description)) < 80
                         THEN 1 ELSE 0 END) AS needs_attention
            FROM animals
            """
        ).fetchone()
    return {
        "total": int(row["total"] or 0),
        "available": int(row["available"] or 0),
        "reserved": int(row["reserved"] or 0),
        "adopted": int(row["adopted"] or 0),
        "needs_attention": int(row["needs_attention"] or 0),
    }


def profile_completion(animal: dict[str, Any]) -> int:
    required_fields: Iterable[str] = (
        "name", "species", "breed", "age_years", "sex", "size",
        "activity_level", "home_type", "child_friendly", "other_pets",
        "experience_level", "max_hours_alone", "status", "description", "image_url",
    )
    completed = sum(
        1 for field in required_fields
        if animal.get(field) is not None and str(animal.get(field)).strip() != ""
    )
    return round((completed / 15) * 100)


def format_age(age_years: Any) -> str:
    try:
        age = float(age_years)
    except (TypeError, ValueError):
        return "—"
    if age.is_integer():
        return f"{int(age)} yr" if age == 1 else f"{int(age)} yrs"
    return f"{age:g} yrs"


def seed_demo_animals() -> int:
    """Insert optional sample records only when the table is empty."""
    initialise_animals_table()
    with get_connection() as connection:
        if int(connection.execute("SELECT COUNT(*) FROM animals").fetchone()[0]):
            return 0

    records = [
        {
            "name": "Luna", "species": "Dog", "breed": "Labrador cross",
            "age_years": 3, "sex": "Female", "size": "Large",
            "activity_level": "High", "home_type": "House", "garden_required": True,
            "child_friendly": "Yes", "other_pets": "Depends",
            "experience_level": "Some experience", "max_hours_alone": 4,
            "status": "Available",
            "description": "Luna is an affectionate and energetic dog who enjoys long walks, training games and spending time with people.",
            "image_url": "https://example.com/luna.jpg",
        },
        {
            "name": "Milo", "species": "Cat", "breed": "Domestic shorthair",
            "age_years": 5, "sex": "Male", "size": "Medium",
            "activity_level": "Moderate", "home_type": "Either", "garden_required": False,
            "child_friendly": "Older children only", "other_pets": "No",
            "experience_level": "First-time owner", "max_hours_alone": 7,
            "status": "Reserved",
            "description": "Milo is a calm cat who enjoys quiet company, window watching and short play sessions in a settled home.",
            "image_url": "https://example.com/milo.jpg",
        },
        {
            "name": "Poppy", "species": "Rabbit", "breed": "Mini lop",
            "age_years": 2, "sex": "Female", "size": "Small",
            "activity_level": "Moderate", "home_type": "Either", "garden_required": False,
            "child_friendly": "Yes", "other_pets": "Depends",
            "experience_level": "Some experience", "max_hours_alone": 5,
            "status": "Available",
            "description": "Poppy is a curious rabbit who needs a spacious enclosure, daily enrichment and gentle handling from her adopter.",
            "image_url": "",
        },
        {
            "name": "Archie", "species": "Dog", "breed": "Cocker spaniel",
            "age_years": 7, "sex": "Male", "size": "Medium",
            "activity_level": "Moderate", "home_type": "House", "garden_required": True,
            "child_friendly": "Yes", "other_pets": "Yes",
            "experience_level": "First-time owner", "max_hours_alone": 4,
            "status": "Adopted",
            "description": "Archie is a friendly older dog who enjoys steady walks, human company and relaxing in a comfortable home.",
            "image_url": "https://example.com/archie.jpg",
        },
    ]

    inserted = 0
    for record in records:
        errors, cleaned = validate_animal(record)
        if not errors:
            success, _, _ = create_animal(cleaned)
            inserted += int(success)
    return inserted
