"""Use cases the pages call. Each one validates, checks permissions, then uses the repository."""

from __future__ import annotations

import sqlite3
from typing import Any

from . import db
from .auth import require_admin
from .matching import rank_animals
from .models import STATUSES, Animal, MatchResult, ShelterStats, User
from .validation import Errors, validate_animal, validate_answers

AVAILABLE = STATUSES[0]
# A profile needs a photo and a description of at least this many characters before staff
# count it as complete (the original admin page's "needs attention" rule).
PROFILE_TEXT_MIN = 80
PROFILE_FIELDS = ("name", "species", "breed", "age", "sex", "size", "personality", "exercise_needs",
                  "min_housing_level", "garden_required", "child_compatible", "max_hours_alone",
                  "good_with_pets", "experience_needed", "medical_notes", "image_path", "status")


def add_animal(conn: sqlite3.Connection, actor: User | None, raw: dict[str, Any]) -> tuple[int | None, Errors]:
    require_admin(actor)
    values, errors = validate_animal(raw)
    if errors:
        return None, errors
    return db.insert_animal(conn, values), {}


def edit_animal(conn: sqlite3.Connection, actor: User | None, animal_id: int, raw: dict[str, Any]) -> Errors:
    require_admin(actor)
    values, errors = validate_animal(raw)
    if errors:
        return errors
    if not db.update_animal(conn, animal_id, values):
        return {"animal": "That animal no longer exists."}
    return {}


def remove_animal(conn: sqlite3.Connection, actor: User | None, animal_id: int) -> bool:
    require_admin(actor)
    return db.delete_animal(conn, animal_id)


def submit_questionnaire(
    conn: sqlite3.Connection, user: User, raw: dict[str, Any]
) -> tuple[list[MatchResult], Errors]:
    """Validate the answers, store them, score every animal and store the ranking."""
    answers, errors = validate_answers(raw)
    if answers is None:
        return [], errors
    response_id = db.save_response(conn, user.user_id, answers)
    results = rank_animals(db.list_animals(conn, status=AVAILABLE), answers)  # reserved or adopted: not scored
    db.save_results(conn, response_id, results)
    return results, {}


def latest_results(conn: sqlite3.Connection, user: User) -> list[MatchResult] | None:
    """The user's most recent stored ranking, or None if they have not taken the questionnaire."""
    latest = db.latest_response(conn, user.user_id)
    return None if latest is None else db.load_results(conn, latest[0])


def browse(conn: sqlite3.Connection, species: str | None, size: str | None, search: str) -> list[Animal]:
    """What adopters see: available animals only (criterion 3)."""
    return db.list_animals(conn, species=species, size=size, search=search, status=AVAILABLE)


def staff_animals(conn: sqlite3.Connection, actor: User | None, species: str | None = None,
                  status: str | None = None, search: str = "") -> list[Animal]:
    """Every record, whatever its status, for the staff dashboard."""
    require_admin(actor)
    return db.list_animals(conn, species=species, search=search, status=status)


def result_for_animal(conn: sqlite3.Connection, user: User, animal_id: int) -> MatchResult | None:
    """The user's latest score for one animal, for the profile page; None before the questionnaire."""
    return next((r for r in latest_results(conn, user) or [] if r.animal.animal_id == animal_id), None)


def dashboard(conn: sqlite3.Connection, actor: User | None) -> ShelterStats:
    """Staff-only counts for the dashboard."""
    require_admin(actor)
    return db.shelter_stats(conn)


def profile_issues(animal: Animal) -> list[str]:
    """What staff should add before a profile is complete: a photo, and a description adopters can use."""
    issues = []
    if not animal.image_path.strip():
        issues.append("photo")
    if len(animal.personality.strip()) < PROFILE_TEXT_MIN:
        issues.append("description")
    return issues


def profile_completion(animal: Animal) -> int:
    """The percentage of the record's fields that are filled in (a yes/no answer always counts)."""
    filled = sum(1 for name in PROFILE_FIELDS
                 if str(getattr(animal, name)).strip() or isinstance(getattr(animal, name), bool))
    return round(100 * filled / len(PROFILE_FIELDS))
