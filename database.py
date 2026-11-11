"""Create the PawMatch SQLite tables used for the DB1 development test."""

from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).with_name("pawmatch.db")


SCHEMA = """
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
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username
ON users (username COLLATE NOCASE)
WHERE username IS NOT NULL;

CREATE TABLE IF NOT EXISTS animals (
    animal_id                INTEGER PRIMARY KEY AUTOINCREMENT,
    name                     TEXT NOT NULL,
    species                  TEXT NOT NULL
                             CHECK (species IN ('Dog', 'Cat', 'Rabbit')),
    breed                    TEXT NOT NULL,
    age_years                REAL NOT NULL CHECK (age_years BETWEEN 0 AND 40),
    sex                      TEXT NOT NULL
                             CHECK (sex IN ('Male', 'Female', 'Unknown')),
    size                     TEXT NOT NULL
                             CHECK (size IN ('Small', 'Medium', 'Large')),
    exercise_needs           TEXT NOT NULL
                             CHECK (exercise_needs IN ('Low', 'Moderate', 'High')),
    home_type                TEXT NOT NULL
                             CHECK (home_type IN (
                                 'Flat or apartment', 'House', 'Either'
                             )),
    recommended_housing_level INTEGER NOT NULL DEFAULT 1
                              CHECK (recommended_housing_level BETWEEN 1 AND 3),
    garden_required          INTEGER NOT NULL DEFAULT 0
                             CHECK (garden_required IN (0, 1)),
    child_compatible         INTEGER NOT NULL DEFAULT 0
                             CHECK (child_compatible IN (0, 1)),
    other_pets               TEXT NOT NULL
                             CHECK (other_pets IN ('Yes', 'No', 'Depends')),
    experience_level         TEXT NOT NULL
                             CHECK (experience_level IN (
                                 'First-time owner',
                                 'Some experience',
                                 'Experienced owner'
                             )),
    max_hours_left_alone     INTEGER NOT NULL
                             CHECK (max_hours_left_alone BETWEEN 0 AND 24),
    description              TEXT NOT NULL,
    image                    TEXT NOT NULL,
    created_at               TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at               TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_animals_species
ON animals (species);

CREATE INDEX IF NOT EXISTS idx_animals_name
ON animals (name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS questionnaire_responses (
    response_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                  INTEGER NOT NULL,
    housing_level            INTEGER NOT NULL
                             CHECK (housing_level BETWEEN 1 AND 3),
    garden_access            INTEGER NOT NULL
                             CHECK (garden_access IN (0, 1)),
    hours_left_alone         INTEGER NOT NULL
                             CHECK (hours_left_alone BETWEEN 0 AND 24),
    has_children             INTEGER NOT NULL
                             CHECK (has_children IN (0, 1)),
    preferred_activity_level INTEGER NOT NULL
                             CHECK (preferred_activity_level BETWEEN 1 AND 3),
    preferred_species        TEXT NOT NULL
                             CHECK (preferred_species IN (
                                 'Dog', 'Cat', 'Rabbit', 'No preference'
                             )),
    preferred_size           TEXT NOT NULL
                             CHECK (preferred_size IN (
                                 'Small', 'Medium', 'Large', 'No preference'
                             )),
    completed_at             TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS match_results (
    match_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id          INTEGER NOT NULL,
    animal_id            INTEGER NOT NULL,
    compatibility_score  REAL NOT NULL
                         CHECK (compatibility_score BETWEEN 0 AND 100),
    preference_score     INTEGER NOT NULL
                         CHECK (preference_score BETWEEN 0 AND 15),
    is_eligible          INTEGER NOT NULL CHECK (is_eligible IN (0, 1)),
    match_category       TEXT NOT NULL
                         CHECK (match_category IN (
                             'Strong', 'Good', 'Possible', 'Low', 'Ineligible'
                         )),
    matched_requirements TEXT NOT NULL DEFAULT '[]',
    unmet_requirements   TEXT NOT NULL DEFAULT '[]',
    calculated_at        TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (response_id, animal_id),
    FOREIGN KEY (response_id)
        REFERENCES questionnaire_responses(response_id) ON DELETE CASCADE,
    FOREIGN KEY (animal_id)
        REFERENCES animals(animal_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_questionnaire_user_completed
ON questionnaire_responses (user_id, completed_at DESC, response_id DESC);

CREATE INDEX IF NOT EXISTS idx_matches_response_rank
ON match_results (
    response_id,
    is_eligible DESC,
    compatibility_score DESC,
    preference_score DESC,
    animal_id ASC
);
"""


def get_connection(database_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    """Open SQLite with row names and foreign-key checking enabled.

    Keeping this configuration in one function avoids a subtle error where one
    part of the program enables foreign keys but another part forgets. Named
    rows also make the authentication code easier to read than tuple indexes.
    """
    connection = sqlite3.connect(database_path, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_database(database_path: Path = DATABASE_PATH) -> Path:
    """Create every designed table and return the database path."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = get_connection(database_path)
    try:
        connection.executescript(SCHEMA)
        connection.commit()
    finally:
        connection.close()
    return database_path

