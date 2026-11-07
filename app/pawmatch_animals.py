"""SQLite helpers for PawMatch animal records and administrator CRUD actions."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from pawmatch_auth import get_connection

SPECIES = ("Dog", "Cat", "Rabbit")
SIZES = ("Small", "Medium", "Large")
ACTIVITY_LEVELS = ("Low", "Moderate", "High")
HOME_TYPES = ("Flat or apartment", "House", "Either")
OTHER_PETS_OPTIONS = ("Yes", "No", "Depends")
EXPERIENCE_LEVELS = ("First-time owner", "Some experience", "Experienced owner")
SEXES = ("Female", "Male", "Unknown")
ANIMAL_IMAGE_DIRECTORY = Path(__file__).resolve().parent / "assets" / "animals"

_IMAGE_URL_PATTERN = re.compile(r"^https?://[^\s]+$", re.IGNORECASE)
_IMAGE_FILE_PATTERN = re.compile(r"^uploads/animals/[A-Za-z0-9._-]+\.(?:jpe?g|png)$", re.IGNORECASE)
_NAME_PATTERN = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ0-9' -]+$")


def animal_image_path(name: Any, stored_location: Any = None) -> Path:
    """Return an uploaded local image when available, otherwise the seeded portrait."""
    location = str(stored_location or "").strip()
    if _IMAGE_FILE_PATTERN.fullmatch(location):
        candidate = Path(__file__).resolve().parent / location
        if candidate.is_file():
            return candidate
    filename = re.sub(r"[^a-z0-9]+", "-", str(name).casefold()).strip("-")
    return ANIMAL_IMAGE_DIRECTORY / f"{filename}.png"


def _create_animals_table(connection: sqlite3.Connection, table_name: str) -> None:
    """Create the current animal schema under one of two internal names."""
    if table_name not in {"animals", "animals_rebuilt"}:
        raise ValueError("Unsupported internal animals table name.")
    connection.execute(
        f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                animal_id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name               TEXT NOT NULL,
                species            TEXT NOT NULL
                                   CHECK (species IN ('Dog', 'Cat', 'Rabbit')),
                breed              TEXT NOT NULL,
                age_years          REAL NOT NULL
                                   CHECK (age_years BETWEEN 0 AND 40),
                sex                TEXT NOT NULL
                                   CHECK (sex IN ('Female', 'Male', 'Unknown')),
                size               TEXT NOT NULL
                                   CHECK (size IN ('Small', 'Medium', 'Large')),
                exercise_needs     TEXT NOT NULL
                                   CHECK (exercise_needs IN ('Low', 'Moderate', 'High')),
                home_type          TEXT NOT NULL
                                   CHECK (home_type IN ('Flat or apartment', 'House', 'Either')),
                recommended_housing_level INTEGER NOT NULL DEFAULT 1
                                   CHECK (recommended_housing_level BETWEEN 1 AND 3),
                garden_required    INTEGER NOT NULL DEFAULT 0
                                   CHECK (garden_required IN (0, 1)),
                child_compatible   INTEGER NOT NULL
                                   CHECK (child_compatible IN (0, 1)),
                other_pets         TEXT NOT NULL
                                   CHECK (other_pets IN ('Yes', 'No', 'Depends')),
                experience_level   TEXT NOT NULL
                                   CHECK (experience_level IN (
                                       'First-time owner',
                                       'Some experience',
                                       'Experienced owner'
                                   )),
                max_hours_left_alone INTEGER NOT NULL
                                   CHECK (max_hours_left_alone BETWEEN 0 AND 24),
                description        TEXT NOT NULL,
                image              TEXT NOT NULL,
                created_at         TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at         TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """
    )


def _migrate_animals_table(connection: sqlite3.Connection) -> None:
    """Rebuild an older animals table using the design field names."""
    columns = {
        row["name"] for row in connection.execute("PRAGMA table_info(animals)")
    }
    expected = {
        "exercise_needs", "recommended_housing_level", "child_compatible",
        "max_hours_left_alone", "image",
    }
    schema_row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'animals'"
    ).fetchone()
    schema_sql = str(schema_row["sql"] or "") if schema_row is not None else ""
    if (
        expected.issubset(columns)
        and "status" not in columns
        and "child_compatible   INTEGER" in schema_sql
    ):
        return

    def source(new_name: str, old_name: str, fallback: str) -> str:
        if new_name in columns:
            return new_name
        if old_name in columns:
            return old_name
        return fallback

    exercise = source("exercise_needs", "activity_level", "'Moderate'")
    housing = source("recommended_housing_level", "minimum_housing_level", "1")
    children = source("child_compatible", "child_friendly", "'No'")
    alone = source("max_hours_left_alone", "max_hours_alone", "0")
    image = source("image", "image_url", "''")
    connection.commit()
    connection.execute("PRAGMA foreign_keys = OFF")
    try:
        connection.execute("DROP TABLE IF EXISTS animals_rebuilt")
        _create_animals_table(connection, "animals_rebuilt")
        connection.execute(
            f"""
            INSERT INTO animals_rebuilt (
                animal_id, name, species, breed, age_years, sex, size,
                exercise_needs, home_type, recommended_housing_level,
                garden_required, child_compatible, other_pets, experience_level,
                max_hours_left_alone, description, image, created_at, updated_at
            )
            SELECT animal_id, name, species, breed, age_years,
                   CASE WHEN sex IN ('Female', 'Male', 'Unknown') THEN sex ELSE 'Unknown' END,
                   size, {exercise}, home_type, {housing}, garden_required,
                   CASE WHEN {children} IN (1, '1', 'Yes', 'yes', 'True', 'true')
                        THEN 1 ELSE 0 END,
                   other_pets, experience_level, {alone}, description,
                   COALESCE({image}, ''), created_at, updated_at
            FROM animals
            """
        )
        connection.execute("DROP TABLE animals")
        connection.execute("ALTER TABLE animals_rebuilt RENAME TO animals")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.execute("PRAGMA foreign_keys = ON")


def initialise_animals_table() -> None:
    """Create or migrate the design-aligned animals table."""
    with get_connection() as connection:
        _create_animals_table(connection, "animals")
        _migrate_animals_table(connection)
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_animals_species
            ON animals (species)
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


def _default_housing_level(home_type: str, size: str) -> int:
    """Derive the design's 1-3 housing requirement for older form records."""
    if home_type in {"Flat or apartment", "Either"}:
        return 1
    return 3 if size == "Large" else 2


def validate_animal_search(
    search_text: Any,
    species: Any,
    size: Any = "All",
) -> tuple[dict[str, str], dict[str, str]]:
    """Validate the browse-page search and documented lookup filters."""
    cleaned_search = _clean_text(search_text)
    cleaned_species = _clean_text(species)
    cleaned_size = _clean_text(size)
    errors: dict[str, str] = {}

    if len(cleaned_search) > 20:
        errors["search"] = "Search cannot exceed 20 characters."
    if cleaned_species not in {"All", "All species", *SPECIES}:
        errors["species"] = "Please select a valid species."
    if cleaned_size not in {"All", "All sizes", *SIZES}:
        errors["size"] = "Please select a valid size."

    return errors, {
        "search": cleaned_search,
        "species": cleaned_species,
        "size": cleaned_size,
    }


def validate_animal(values: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    """Validate an animal record and return field errors plus cleaned values."""
    cleaned: dict[str, Any] = {
        "name": _clean_text(values.get("name")),
        "species": _clean_text(values.get("species")),
        "breed": _clean_text(values.get("breed")),
        "age_years": values.get("age_years"),
        "sex": _clean_text(values.get("sex")),
        "size": _clean_text(values.get("size")),
        "exercise_needs": _clean_text(values.get("exercise_needs", values.get("activity_level"))),
        "home_type": _clean_text(values.get("home_type")),
        "recommended_housing_level": values.get(
            "recommended_housing_level", values.get("minimum_housing_level")
        ),
        "garden_required": values.get("garden_required", False),
        "child_compatible": values.get("child_compatible", values.get("child_friendly")),
        "other_pets": _clean_text(values.get("other_pets")),
        "experience_level": _clean_text(values.get("experience_level")),
        "max_hours_left_alone": values.get(
            "max_hours_left_alone", values.get("max_hours_alone")
        ),
        "description": str(values.get("description") or "").strip(),
        "image": str(values.get("image", values.get("image_url")) or "").strip(),
    }
    errors: dict[str, str] = {}

    if not cleaned["name"]:
        errors["name"] = "Enter the animal's name."
    elif not 2 <= len(cleaned["name"]) <= 50:
        errors["name"] = "The name must contain between 2 and 50 characters."
    elif _NAME_PATTERN.fullmatch(cleaned["name"]) is None:
        errors["name"] = "Use letters, numbers, spaces, hyphens or apostrophes only."

    if cleaned["species"] not in SPECIES:
        errors["species"] = "Select a supported species."

    if not cleaned["breed"]:
        errors["breed"] = "Enter a breed or use 'Mixed breed'."
    elif not 2 <= len(cleaned["breed"]) <= 50:
        errors["breed"] = "The breed must contain between 2 and 50 characters."
    elif not any(character.isalnum() for character in cleaned["breed"]):
        errors["breed"] = "The breed cannot contain only symbols."

    # The design pseudocode models age as a whole number. PawMatch's existing
    # interface and sample profiles use half-year ages for young animals, so
    # this compatible extension preserves those visible records and controls.
    try:
        cleaned["age_years"] = float(cleaned["age_years"])
    except (TypeError, ValueError):
        errors["age_years"] = "Enter the animal's age."
    else:
        if not 0 < cleaned["age_years"] <= 40:
            errors["age_years"] = "Enter an age greater than 0 and no more than 40 years."

    allowed_values = {
        "sex": SEXES,
        "size": SIZES,
        "exercise_needs": ACTIVITY_LEVELS,
        "home_type": HOME_TYPES,
        "other_pets": OTHER_PETS_OPTIONS,
        "experience_level": EXPERIENCE_LEVELS,
    }
    messages = {
        "sex": "Select the animal's sex.",
        "size": "Select a size.",
        "exercise_needs": "Select an activity level.",
        "home_type": "Select a suitable home type.",
        "other_pets": "Select the animal's suitability with other pets.",
        "experience_level": "Select the required owner experience.",
    }
    for field, valid_options in allowed_values.items():
        if cleaned[field] not in valid_options:
            errors[field] = messages[field]

    if type(cleaned["child_compatible"]) not in {bool, int} or cleaned["child_compatible"] not in {0, 1}:
        errors["child_compatible"] = "Child compatibility must be Yes or No."
    else:
        cleaned["child_compatible"] = bool(cleaned["child_compatible"])

    if cleaned["recommended_housing_level"] is None:
        cleaned["recommended_housing_level"] = _default_housing_level(
            cleaned["home_type"], cleaned["size"]
        )
    try:
        cleaned["recommended_housing_level"] = int(cleaned["recommended_housing_level"])
    except (TypeError, ValueError):
        errors["recommended_housing_level"] = "Select a housing level from 1 to 3."
    else:
        if cleaned["recommended_housing_level"] not in {1, 2, 3}:
            errors["recommended_housing_level"] = "Select a housing level from 1 to 3."

    try:
        cleaned["max_hours_left_alone"] = int(cleaned["max_hours_left_alone"])
    except (TypeError, ValueError):
        errors["max_hours_left_alone"] = "Enter the maximum number of hours alone."
    else:
        if not 0 <= cleaned["max_hours_left_alone"] <= 24:
            errors["max_hours_left_alone"] = "Enter a value between 0 and 24 hours."

    if type(cleaned["garden_required"]) not in {bool, int} or cleaned["garden_required"] not in {0, 1}:
        errors["garden_required"] = "Garden required must be Yes or No."
    else:
        cleaned["garden_required"] = bool(cleaned["garden_required"])

    if not cleaned["description"]:
        errors["description"] = "Enter a short profile description."
    elif len(cleaned["description"]) < 20:
        errors["description"] = "Use at least 20 characters so adopters receive useful information."
    elif len(cleaned["description"]) > 1000:
        errors["description"] = "The description must contain no more than 1,000 characters."

    image_is_valid = (
        _IMAGE_URL_PATTERN.fullmatch(cleaned["image"]) is not None
        or _IMAGE_FILE_PATTERN.fullmatch(cleaned["image"]) is not None
    )
    if cleaned["image"] and not image_is_valid:
        errors["image"] = "Upload a JPG or PNG image, or provide a complete image address."

    return errors, cleaned


def _database_values(animal: dict[str, Any]) -> tuple[Any, ...]:
    return (
        animal["name"],
        animal["species"],
        animal["breed"],
        animal["age_years"],
        animal["sex"],
        animal["size"],
        animal["exercise_needs"],
        animal["home_type"],
        animal["recommended_housing_level"],
        int(animal["garden_required"]),
        animal["child_compatible"],
        animal["other_pets"],
        animal["experience_level"],
        animal["max_hours_left_alone"],
        animal["description"],
        animal["image"],
    )


def create_animal(animal: dict[str, Any]) -> tuple[bool, int | None, str]:
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO animals (
                    name, species, breed, age_years, sex, size, exercise_needs,
                    home_type, recommended_housing_level, garden_required,
                    child_compatible, other_pets,
                    experience_level, max_hours_left_alone, description, image
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
                    size = ?, exercise_needs = ?, home_type = ?, recommended_housing_level = ?,
                    garden_required = ?, child_compatible = ?, other_pets = ?, experience_level = ?,
                    max_hours_left_alone = ?, description = ?, image = ?,
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
    limit: int | None = None,
    size: str = "All sizes",
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
    if size in SIZES:
        clauses.append("size = ?")
        parameters.append(size)

    query = "SELECT * FROM animals"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    # Keep the original seeded order so the named cartoon portraits appear with
    # their matching animals instead of being pushed below newer text-only rows.
    query += " ORDER BY animal_id ASC"
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
                SUM(CASE WHEN image IS NULL OR TRIM(image) = ''
                              OR LENGTH(TRIM(description)) < 80
                         THEN 1 ELSE 0 END) AS needs_attention
            FROM animals
            """
        ).fetchone()
    return {
        "total": int(row["total"] or 0),
        "needs_attention": int(row["needs_attention"] or 0),
    }


def profile_completion(animal: dict[str, Any]) -> int:
    required_fields: Iterable[str] = (
        "name", "species", "breed", "age_years", "sex", "size",
        "exercise_needs", "home_type", "recommended_housing_level", "child_compatible", "other_pets",
        "experience_level", "max_hours_left_alone", "description", "image",
    )
    completed = sum(
        1 for field in required_fields
        if animal.get(field) is not None and str(animal.get(field)).strip() != ""
    )
    return round((completed / len(tuple(required_fields))) * 100)


def format_age(age_years: Any) -> str:
    try:
        age = float(age_years)
    except (TypeError, ValueError):
        return "—"
    if age.is_integer():
        return f"{int(age)} yr" if age == 1 else f"{int(age)} yrs"
    return f"{age:g} yrs"


def seed_demo_animals() -> int:
    """Insert missing design-aligned sample animals without creating duplicates."""
    initialise_animals_table()

    records = [
        {
            "name": "Luna", "species": "Dog", "breed": "Labrador cross",
            "age_years": 3, "sex": "Female", "size": "Large",
            "exercise_needs": "High", "home_type": "House", "garden_required": True,
            "recommended_housing_level": 3,
            "child_compatible": True, "other_pets": "Depends",
            "experience_level": "Some experience", "max_hours_left_alone": 4,
            "description": "Luna is an affectionate and energetic dog who enjoys long walks, training games and spending time with people.",
            "image": "https://example.com/luna.jpg",
        },
        {
            "name": "Milo", "species": "Cat", "breed": "Domestic shorthair",
            "age_years": 5, "sex": "Male", "size": "Medium",
            "exercise_needs": "Moderate", "home_type": "Either", "garden_required": False,
            "recommended_housing_level": 1,
            "child_compatible": False, "other_pets": "No",
            "experience_level": "First-time owner", "max_hours_left_alone": 7,
            "description": "Milo is a calm cat who enjoys quiet company, window watching and short play sessions in a settled home.",
            "image": "https://example.com/milo.jpg",
        },
        {
            "name": "Poppy", "species": "Rabbit", "breed": "Mini lop",
            "age_years": 2, "sex": "Female", "size": "Small",
            "exercise_needs": "Moderate", "home_type": "Either", "garden_required": False,
            "recommended_housing_level": 1,
            "child_compatible": True, "other_pets": "Depends",
            "experience_level": "Some experience", "max_hours_left_alone": 5,
            "description": "Poppy is a curious rabbit who needs a spacious enclosure, daily enrichment and gentle handling from her adopter.",
            "image": "",
        },
        {
            "name": "Archie", "species": "Dog", "breed": "Cocker spaniel",
            "age_years": 7, "sex": "Male", "size": "Medium",
            "exercise_needs": "Moderate", "home_type": "House", "garden_required": True,
            "recommended_housing_level": 2,
            "child_compatible": True, "other_pets": "Yes",
            "experience_level": "First-time owner", "max_hours_left_alone": 4,
            "description": "Archie is a friendly older dog who enjoys steady walks, human company and relaxing in a comfortable home.",
            "image": "https://example.com/archie.jpg",
        },
        {
            "name": "Bella", "species": "Cat", "breed": "British shorthair cross",
            "age_years": 4, "sex": "Female", "size": "Small",
            "exercise_needs": "Low", "home_type": "Flat or apartment",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": True, "other_pets": "Depends",
            "experience_level": "First-time owner", "max_hours_left_alone": 8,
            "description": "Bella is a gentle indoor cat who enjoys quiet company, soft beds and short play sessions each day.",
            "image": "",
        },
        {
            "name": "Teddy", "species": "Rabbit", "breed": "Lionhead",
            "age_years": 1.5, "sex": "Male", "size": "Small",
            "exercise_needs": "Low", "home_type": "Either",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": False, "other_pets": "No",
            "experience_level": "Some experience", "max_hours_left_alone": 6,
            "description": "Teddy is a shy rabbit who needs patient handling, a roomy enclosure and calm daily interaction.",
            "image": "",
        },
        {
            "name": "Nala", "species": "Dog", "breed": "Staffordshire bull terrier cross",
            "age_years": 2, "sex": "Female", "size": "Medium",
            "exercise_needs": "High", "home_type": "House",
            "recommended_housing_level": 2, "garden_required": True,
            "child_compatible": False, "other_pets": "Depends",
            "experience_level": "Experienced owner", "max_hours_left_alone": 3,
            "description": "Nala is a bright and energetic dog who needs consistent training, active walks and careful introductions.",
            "image": "",
        },
        {
            "name": "Simba", "species": "Cat", "breed": "Domestic longhair",
            "age_years": 6, "sex": "Male", "size": "Medium",
            "exercise_needs": "Moderate", "home_type": "Either",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": False, "other_pets": "No",
            "experience_level": "Some experience", "max_hours_left_alone": 8,
            "description": "Simba is an independent long-haired cat who prefers a peaceful adult home and regular grooming.",
            "image": "",
        },
        {
            "name": "Daisy", "species": "Rabbit", "breed": "Dutch rabbit",
            "age_years": 3, "sex": "Female", "size": "Small",
            "exercise_needs": "Moderate", "home_type": "Either",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": True, "other_pets": "Depends",
            "experience_level": "First-time owner", "max_hours_left_alone": 6,
            "description": "Daisy is a sociable rabbit who enjoys enrichment, supervised exploration and gentle family attention.",
            "image": "",
        },
        {
            "name": "Max", "species": "Dog", "breed": "German shepherd cross",
            "age_years": 5, "sex": "Male", "size": "Large",
            "exercise_needs": "High", "home_type": "House",
            "recommended_housing_level": 3, "garden_required": True,
            "child_compatible": False, "other_pets": "No",
            "experience_level": "Experienced owner", "max_hours_left_alone": 2,
            "description": "Max is a loyal working-breed dog who needs an experienced adult home, structured training and daily exercise.",
            "image": "",
        },
        {
            "name": "Willow", "species": "Cat", "breed": "Domestic shorthair",
            "age_years": 9, "sex": "Female", "size": "Small",
            "exercise_needs": "Low", "home_type": "Flat or apartment",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": True, "other_pets": "Depends",
            "experience_level": "First-time owner", "max_hours_left_alone": 9,
            "description": "Willow is a relaxed older cat who enjoys warm resting places, gentle affection and a predictable routine.",
            "image": "",
        },
        {
            "name": "Oscar", "species": "Dog", "breed": "Jack Russell terrier cross",
            "age_years": 4, "sex": "Male", "size": "Small",
            "exercise_needs": "Moderate", "home_type": "Either",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": True, "other_pets": "Depends",
            "experience_level": "Some experience", "max_hours_left_alone": 5,
            "description": "Oscar is a cheerful small dog who likes brisk walks, puzzle toys and being involved in family life.",
            "image": "",
        },
        {
            "name": "Clover", "species": "Rabbit", "breed": "Rex rabbit",
            "age_years": 2.5, "sex": "Male", "size": "Medium",
            "exercise_needs": "Moderate", "home_type": "House",
            "recommended_housing_level": 2, "garden_required": True,
            "child_compatible": False, "other_pets": "No",
            "experience_level": "Some experience", "max_hours_left_alone": 5,
            "description": "Clover is an inquisitive rabbit who needs generous indoor space, secure outdoor exercise and patient care.",
            "image": "",
        },
        {
            "name": "Ruby", "species": "Dog", "breed": "Border collie cross",
            "age_years": 2, "sex": "Female", "size": "Medium",
            "exercise_needs": "High", "home_type": "House",
            "recommended_housing_level": 2, "garden_required": True,
            "child_compatible": False, "other_pets": "Depends",
            "experience_level": "Experienced owner", "max_hours_left_alone": 3,
            "description": "Ruby is a clever and energetic dog who needs daily training, active exercise and plenty of mental stimulation.",
            "image": "",
        },
        {
            "name": "Finn", "species": "Dog", "breed": "Greyhound",
            "age_years": 4, "sex": "Male", "size": "Large",
            "exercise_needs": "Moderate", "home_type": "House",
            "recommended_housing_level": 3, "garden_required": True,
            "child_compatible": True, "other_pets": "No",
            "experience_level": "First-time owner", "max_hours_left_alone": 5,
            "description": "Finn is a gentle retired greyhound who enjoys relaxed walks, soft beds and calm companionship at home.",
            "image": "",
        },
        {
            "name": "Maple", "species": "Dog", "breed": "Beagle cross",
            "age_years": 3, "sex": "Female", "size": "Medium",
            "exercise_needs": "High", "home_type": "House",
            "recommended_housing_level": 2, "garden_required": True,
            "child_compatible": True, "other_pets": "Yes",
            "experience_level": "Some experience", "max_hours_left_alone": 4,
            "description": "Maple is a sociable scent hound who loves exploring, food puzzles and spending time with an active family.",
            "image": "",
        },
        {
            "name": "Bruno", "species": "Dog", "breed": "Boxer cross",
            "age_years": 6, "sex": "Male", "size": "Large",
            "exercise_needs": "Moderate", "home_type": "House",
            "recommended_housing_level": 3, "garden_required": True,
            "child_compatible": False, "other_pets": "No",
            "experience_level": "Experienced owner", "max_hours_left_alone": 4,
            "description": "Bruno is an affectionate dog who needs steady exercise, confident handling and a home with predictable routines.",
            "image": "",
        },
        {
            "name": "Skye", "species": "Dog", "breed": "Whippet",
            "age_years": 1.5, "sex": "Female", "size": "Medium",
            "exercise_needs": "Moderate", "home_type": "Either",
            "recommended_housing_level": 2, "garden_required": False,
            "child_compatible": True, "other_pets": "Depends",
            "experience_level": "First-time owner", "max_hours_left_alone": 3,
            "description": "Skye is a sensitive young dog who enjoys short bursts of exercise followed by quiet time beside her family.",
            "image": "",
        },
        {
            "name": "Alfie", "species": "Dog", "breed": "Cavalier King Charles spaniel",
            "age_years": 8, "sex": "Male", "size": "Small",
            "exercise_needs": "Low", "home_type": "Flat or apartment",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": True, "other_pets": "Yes",
            "experience_level": "First-time owner", "max_hours_left_alone": 5,
            "description": "Alfie is a friendly older companion who prefers gentle walks, regular company and a comfortable place to rest.",
            "image": "",
        },
        {
            "name": "Rosie", "species": "Dog", "breed": "Poodle cross",
            "age_years": 4, "sex": "Female", "size": "Small",
            "exercise_needs": "Moderate", "home_type": "Either",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": True, "other_pets": "Yes",
            "experience_level": "Some experience", "max_hours_left_alone": 4,
            "description": "Rosie is a cheerful small dog who enjoys learning tricks, meeting friendly people and receiving regular grooming.",
            "image": "",
        },
        {
            "name": "Hugo", "species": "Dog", "breed": "Rottweiler cross",
            "age_years": 5, "sex": "Male", "size": "Large",
            "exercise_needs": "High", "home_type": "House",
            "recommended_housing_level": 3, "garden_required": True,
            "child_compatible": False, "other_pets": "No",
            "experience_level": "Experienced owner", "max_hours_left_alone": 2,
            "description": "Hugo is a strong and loyal dog who needs experienced handling, structured training and plenty of daily exercise.",
            "image": "",
        },
        {
            "name": "Misty", "species": "Cat", "breed": "Russian Blue cross",
            "age_years": 3, "sex": "Female", "size": "Small",
            "exercise_needs": "Moderate", "home_type": "Flat or apartment",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": False, "other_pets": "No",
            "experience_level": "First-time owner", "max_hours_left_alone": 8,
            "description": "Misty is a quiet indoor cat who enjoys climbing, gentle play and choosing when to approach people for affection.",
            "image": "",
        },
        {
            "name": "Jasper", "species": "Cat", "breed": "Bengal cross",
            "age_years": 2, "sex": "Male", "size": "Medium",
            "exercise_needs": "High", "home_type": "House",
            "recommended_housing_level": 2, "garden_required": False,
            "child_compatible": False, "other_pets": "Depends",
            "experience_level": "Experienced owner", "max_hours_left_alone": 6,
            "description": "Jasper is an active and curious cat who needs climbing space, interactive games and an experienced household.",
            "image": "",
        },
        {
            "name": "Cleo", "species": "Cat", "breed": "Siamese cross",
            "age_years": 7, "sex": "Female", "size": "Small",
            "exercise_needs": "Moderate", "home_type": "Either",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": True, "other_pets": "Depends",
            "experience_level": "First-time owner", "max_hours_left_alone": 7,
            "description": "Cleo is a talkative and affectionate cat who enjoys company, warm resting places and short daily play sessions.",
            "image": "",
        },
        {
            "name": "Felix", "species": "Cat", "breed": "Tuxedo domestic shorthair",
            "age_years": 1, "sex": "Male", "size": "Medium",
            "exercise_needs": "High", "home_type": "Either",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": True, "other_pets": "Yes",
            "experience_level": "First-time owner", "max_hours_left_alone": 5,
            "description": "Felix is a playful young cat who enjoys chasing toys, exploring high places and living with an active family.",
            "image": "",
        },
        {
            "name": "Ivy", "species": "Cat", "breed": "Maine Coon cross",
            "age_years": 5, "sex": "Female", "size": "Large",
            "exercise_needs": "Moderate", "home_type": "House",
            "recommended_housing_level": 2, "garden_required": False,
            "child_compatible": True, "other_pets": "Yes",
            "experience_level": "Some experience", "max_hours_left_alone": 8,
            "description": "Ivy is a calm and sociable cat who needs regular grooming, sturdy climbing furniture and friendly company.",
            "image": "",
        },
        {
            "name": "George", "species": "Cat", "breed": "Domestic shorthair",
            "age_years": 11, "sex": "Male", "size": "Medium",
            "exercise_needs": "Low", "home_type": "Flat or apartment",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": False, "other_pets": "No",
            "experience_level": "First-time owner", "max_hours_left_alone": 9,
            "description": "George is a settled senior cat who would suit a quiet adult home with soft beds and a predictable routine.",
            "image": "",
        },
        {
            "name": "Suki", "species": "Cat", "breed": "Calico domestic shorthair",
            "age_years": 4, "sex": "Female", "size": "Small",
            "exercise_needs": "Moderate", "home_type": "Either",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": False, "other_pets": "Depends",
            "experience_level": "Some experience", "max_hours_left_alone": 7,
            "description": "Suki is a confident cat who enjoys puzzle feeders, sunny windows and respectful interaction with older children.",
            "image": "",
        },
        {
            "name": "Honey", "species": "Rabbit", "breed": "Netherland dwarf",
            "age_years": 1, "sex": "Female", "size": "Small",
            "exercise_needs": "Moderate", "home_type": "Either",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": False, "other_pets": "No",
            "experience_level": "Some experience", "max_hours_left_alone": 5,
            "description": "Honey is a small and alert rabbit who needs patient handling, daily enrichment and a spacious secure enclosure.",
            "image": "",
        },
        {
            "name": "Pepper", "species": "Rabbit", "breed": "English spot",
            "age_years": 2, "sex": "Male", "size": "Medium",
            "exercise_needs": "High", "home_type": "House",
            "recommended_housing_level": 2, "garden_required": True,
            "child_compatible": True, "other_pets": "Depends",
            "experience_level": "Some experience", "max_hours_left_alone": 5,
            "description": "Pepper is an active rabbit who enjoys tunnels, supervised outdoor exercise and plenty of space for running.",
            "image": "",
        },
        {
            "name": "Bluebell", "species": "Rabbit", "breed": "Havana rabbit",
            "age_years": 3.5, "sex": "Female", "size": "Medium",
            "exercise_needs": "Low", "home_type": "Either",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": True, "other_pets": "No",
            "experience_level": "First-time owner", "max_hours_left_alone": 6,
            "description": "Bluebell is a gentle rabbit who likes calm attention, forage toys and a comfortable indoor living area.",
            "image": "",
        },
        {
            "name": "Peanut", "species": "Rabbit", "breed": "Mini Rex",
            "age_years": 0.5, "sex": "Male", "size": "Small",
            "exercise_needs": "High", "home_type": "Either",
            "recommended_housing_level": 1, "garden_required": False,
            "child_compatible": False, "other_pets": "Depends",
            "experience_level": "Some experience", "max_hours_left_alone": 4,
            "description": "Peanut is a lively young rabbit who needs careful handling, chew-safe enrichment and room to exercise every day.",
            "image": "",
        },
        {
            "name": "Fern", "species": "Rabbit", "breed": "French lop cross",
            "age_years": 4, "sex": "Female", "size": "Large",
            "exercise_needs": "Moderate", "home_type": "House",
            "recommended_housing_level": 2, "garden_required": True,
            "child_compatible": True, "other_pets": "No",
            "experience_level": "Experienced owner", "max_hours_left_alone": 6,
            "description": "Fern is a large friendly rabbit who needs generous accommodation, secure outdoor exercise and regular grooming.",
            "image": "",
        },
    ]

    inserted = 0
    connection = get_connection()
    try:
        existing_records = {
            (str(row["name"]).casefold(), str(row["species"]))
            for row in connection.execute("SELECT name, species FROM animals")
        }
    finally:
        connection.close()

    for record in records:
        identity = (record["name"].casefold(), record["species"])
        if identity in existing_records:
            continue
        errors, cleaned = validate_animal(record)
        if not errors:
            success, _, _ = create_animal(cleaned)
            inserted += int(success)
            if success:
                existing_records.add(identity)
    return inserted
