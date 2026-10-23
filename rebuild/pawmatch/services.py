"""Use cases the pages call. Each one validates, checks permissions, then uses the repository."""

from __future__ import annotations

import sqlite3
from typing import Any

from . import db
from .auth import require_admin
from .matching import rank_animals
from .models import Animal, MatchResult, User
from .validation import Errors, validate_animal, validate_answers


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
    results = rank_animals(db.list_animals(conn), answers)
    db.save_results(conn, response_id, results)
    return results, {}


def latest_results(conn: sqlite3.Connection, user: User) -> list[MatchResult] | None:
    """The user's most recent stored ranking, or None if they have not taken the questionnaire."""
    latest = db.latest_response(conn, user.user_id)
    return None if latest is None else db.load_results(conn, latest[0])


def browse(conn: sqlite3.Connection, species: str | None, size: str | None, search: str) -> list[Animal]:
    return db.list_animals(conn, species=species, size=size, search=search)
