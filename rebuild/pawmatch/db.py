"""SQLite repository. Every query is parameterised; no SQL is built from user input."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import SPECIES, STATUSES, Animal, Answers, MatchResult, ShelterStats, User

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    age           INTEGER NOT NULL CHECK (age >= 18),
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at    TEXT    NOT NULL
);
CREATE TABLE IF NOT EXISTS animals (
    animal_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name              TEXT    NOT NULL,
    species           TEXT    NOT NULL CHECK (species IN ('Dog', 'Cat', 'Rabbit')),
    breed             TEXT    NOT NULL,
    age               INTEGER NOT NULL CHECK (age BETWEEN 1 AND 30),
    sex               TEXT    NOT NULL CHECK (sex IN ('Male', 'Female', 'Unknown')),
    size              TEXT    NOT NULL CHECK (size IN ('Small', 'Medium', 'Large')),
    personality       TEXT    NOT NULL,
    exercise_needs    INTEGER NOT NULL CHECK (exercise_needs BETWEEN 1 AND 3),
    min_housing_level INTEGER NOT NULL CHECK (min_housing_level BETWEEN 1 AND 3),
    garden_required   INTEGER NOT NULL CHECK (garden_required IN (0, 1)),
    child_compatible  INTEGER NOT NULL CHECK (child_compatible IN (0, 1)),
    max_hours_alone   INTEGER NOT NULL CHECK (max_hours_alone BETWEEN 0 AND 24),
    medical_notes     TEXT    NOT NULL DEFAULT '',
    image_path        TEXT    NOT NULL DEFAULT '',
    status            TEXT    NOT NULL DEFAULT 'Available' CHECK (status IN ('Available', 'Reserved', 'Adopted')),
    date_added        TEXT    NOT NULL
);
CREATE TABLE IF NOT EXISTS questionnaire_responses (
    response_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    housing_level     INTEGER NOT NULL CHECK (housing_level BETWEEN 1 AND 3),
    garden_access     INTEGER NOT NULL CHECK (garden_access IN (0, 1)),
    has_children      INTEGER NOT NULL CHECK (has_children IN (0, 1)),
    other_pets        INTEGER NOT NULL CHECK (other_pets IN (0, 1)),
    experience        TEXT    NOT NULL,
    activity_level    INTEGER NOT NULL CHECK (activity_level BETWEEN 1 AND 3),
    hours_alone       INTEGER NOT NULL CHECK (hours_alone BETWEEN 0 AND 24),
    preferred_species TEXT    NOT NULL,
    preferred_size    TEXT    NOT NULL,
    completed_at      TEXT    NOT NULL
);
CREATE TABLE IF NOT EXISTS match_results (
    match_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    response_id   INTEGER NOT NULL REFERENCES questionnaire_responses(response_id) ON DELETE CASCADE,
    animal_id     INTEGER NOT NULL REFERENCES animals(animal_id) ON DELETE CASCADE,
    rank          INTEGER NOT NULL,
    compatibility REAL    NOT NULL CHECK (compatibility BETWEEN 0 AND 100),
    category      TEXT    NOT NULL CHECK (category IN ('Strong', 'Good', 'Possible', 'Low')),
    bonus         INTEGER NOT NULL,
    met           TEXT    NOT NULL,
    unmet         TEXT    NOT NULL,
    warnings      TEXT    NOT NULL,
    calculated_at TEXT    NOT NULL DEFAULT ''
);
"""

ANIMAL_FIELDS = (
    "name", "species", "breed", "age", "sex", "size", "personality", "exercise_needs",
    "min_housing_level", "garden_required", "child_compatible", "max_hours_alone",
    "medical_notes", "image_path", "status",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect(path: str | Path) -> Iterator[sqlite3.Connection]:
    """Open the database, commit on success, roll back on error, always close."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    # Databases made before stage 5 lack calculated_at (Design, Match Results table): add it in place.
    columns = {row[1] for row in conn.execute("PRAGMA table_info(match_results)")}
    if "calculated_at" not in columns:
        conn.execute("ALTER TABLE match_results ADD COLUMN calculated_at TEXT NOT NULL DEFAULT ''")
    # Databases made before round 2 lack the adoption status: every existing animal starts Available.
    if "status" not in {row[1] for row in conn.execute("PRAGMA table_info(animals)")}:
        conn.execute("ALTER TABLE animals ADD COLUMN status TEXT NOT NULL DEFAULT 'Available' "
                     "CHECK (status IN ('Available', 'Reserved', 'Adopted'))")


# ---- users ---------------------------------------------------------------

def _user(row: sqlite3.Row) -> User:
    return User(row["user_id"], row["name"], row["email"], row["age"], row["role"])


def email_exists(conn: sqlite3.Connection, email: str) -> bool:
    return conn.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone() is not None


def insert_user(conn: sqlite3.Connection, name: str, email: str, age: int, password_hash: str, role: str = "user") -> User:
    cur = conn.execute(
        "INSERT INTO users (name, email, age, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (name, email, age, password_hash, role, _now()),
    )
    return User(int(cur.lastrowid), name, email, age, role)


def find_user_with_hash(conn: sqlite3.Connection, email: str) -> tuple[User, str] | None:
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return (_user(row), row["password_hash"]) if row else None


def get_user(conn: sqlite3.Connection, user_id: int) -> User | None:
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return _user(row) if row else None


def set_role(conn: sqlite3.Connection, user_id: int, role: str) -> None:
    conn.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))


# ---- animals -------------------------------------------------------------

def _animal(row: sqlite3.Row) -> Animal:
    data = {k: row[k] for k in ("animal_id",) + ANIMAL_FIELDS + ("date_added",)}
    data["garden_required"] = bool(data["garden_required"])
    data["child_compatible"] = bool(data["child_compatible"])
    return Animal(**data)


def insert_animal(conn: sqlite3.Connection, values: dict[str, Any]) -> int:
    columns = ", ".join(ANIMAL_FIELDS)  # fixed column names, never user input
    marks = ", ".join("?" for _ in ANIMAL_FIELDS)
    cur = conn.execute(
        f"INSERT INTO animals ({columns}, date_added) VALUES ({marks}, ?)",
        tuple(values[f] for f in ANIMAL_FIELDS) + (_now(),),
    )
    return int(cur.lastrowid)


def update_animal(conn: sqlite3.Connection, animal_id: int, values: dict[str, Any]) -> bool:
    assignments = ", ".join(f"{f} = ?" for f in ANIMAL_FIELDS)
    cur = conn.execute(
        f"UPDATE animals SET {assignments} WHERE animal_id = ?",
        tuple(values[f] for f in ANIMAL_FIELDS) + (animal_id,),
    )
    return cur.rowcount == 1


def delete_animal(conn: sqlite3.Connection, animal_id: int) -> bool:
    return conn.execute("DELETE FROM animals WHERE animal_id = ?", (animal_id,)).rowcount == 1


def get_animal(conn: sqlite3.Connection, animal_id: int) -> Animal | None:
    row = conn.execute("SELECT * FROM animals WHERE animal_id = ?", (animal_id,)).fetchone()
    return _animal(row) if row else None


def list_animals(
    conn: sqlite3.Connection, species: str | None = None, size: str | None = None, search: str = "",
    status: str | None = None,
) -> list[Animal]:
    """Browse query with optional filters; the search term is bound, never concatenated."""
    sql = "SELECT * FROM animals WHERE 1 = 1"
    params: list[Any] = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if species:
        sql += " AND species = ?"
        params.append(species)
    if size:
        sql += " AND size = ?"
        params.append(size)
    if search.strip():
        sql += " AND (name LIKE ? OR breed LIKE ?)"
        term = f"%{search.strip()}%"
        params += [term, term]
    sql += " ORDER BY species, name"
    return [_animal(r) for r in conn.execute(sql, params)]


def count_animals(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM animals").fetchone()[0]


def use_png_pictures(conn: sqlite3.Connection) -> int:
    """Point round-1 demo animals (.jpg on black) at the transparent .png cut-outs; returns rows changed."""
    return conn.execute(
        """UPDATE animals SET image_path = substr(image_path, 1, length(image_path) - 4) || '.png'
           WHERE image_path LIKE 'assets/animals/%.jpg'"""
    ).rowcount


def shelter_stats(conn: sqlite3.Connection) -> ShelterStats:
    """Dashboard counts in five aggregate queries; a species or status with no animals still shows as 0."""
    by_species = dict.fromkeys(SPECIES, 0)
    for species, count in conn.execute("SELECT species, COUNT(*) FROM animals GROUP BY species"):
        by_species[species] = count
    roles = dict(conn.execute("SELECT role, COUNT(*) FROM users GROUP BY role").fetchall())
    questionnaires = conn.execute("SELECT COUNT(*) FROM questionnaire_responses").fetchone()[0]
    by_status = dict.fromkeys(STATUSES, 0)
    for status, count in conn.execute("SELECT status, COUNT(*) FROM animals GROUP BY status"):
        by_status[status] = count
    return ShelterStats(by_species, roles.get("user", 0), roles.get("admin", 0), questionnaires, by_status)


# ---- questionnaire and results -------------------------------------------

def save_response(conn: sqlite3.Connection, user_id: int, answers: Answers) -> int:
    cur = conn.execute(
        """INSERT INTO questionnaire_responses (user_id, housing_level, garden_access, has_children,
               other_pets, experience, activity_level, hours_alone, preferred_species, preferred_size,
               completed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, answers.housing_level, int(answers.garden_access), int(answers.has_children),
         int(answers.other_pets), answers.experience, answers.activity_level, answers.hours_alone,
         answers.preferred_species, answers.preferred_size, _now()),
    )
    return int(cur.lastrowid)


def latest_response(conn: sqlite3.Connection, user_id: int) -> tuple[int, Answers] | None:
    row = conn.execute(
        "SELECT * FROM questionnaire_responses WHERE user_id = ? ORDER BY response_id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    if row is None:
        return None
    return row["response_id"], Answers(
        housing_level=row["housing_level"], garden_access=bool(row["garden_access"]),
        has_children=bool(row["has_children"]), other_pets=bool(row["other_pets"]),
        experience=row["experience"], activity_level=row["activity_level"], hours_alone=row["hours_alone"],
        preferred_species=row["preferred_species"], preferred_size=row["preferred_size"],
    )


def save_results(conn: sqlite3.Connection, response_id: int, results: list[MatchResult]) -> None:
    conn.execute("DELETE FROM match_results WHERE response_id = ?", (response_id,))
    calculated_at = _now()  # one timestamp for the whole ranking
    conn.executemany(
        """INSERT INTO match_results (response_id, animal_id, rank, compatibility, category, bonus,
               met, unmet, warnings, calculated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [(response_id, r.animal.animal_id, rank, r.compatibility, r.category, r.bonus,
          json.dumps(r.met), json.dumps(r.unmet), json.dumps(r.warnings), calculated_at)
         for rank, r in enumerate(results, start=1)],
    )


def load_results(conn: sqlite3.Connection, response_id: int) -> list[MatchResult]:
    """Stored results joined to the current animal records, in saved rank order."""
    rows = conn.execute(
        """SELECT m.compatibility, m.category, m.bonus, m.met, m.unmet, m.warnings, a.*
           FROM match_results m JOIN animals a ON a.animal_id = m.animal_id
           WHERE m.response_id = ? ORDER BY m.rank""",
        (response_id,),
    ).fetchall()
    return [
        MatchResult(animal=_animal(r), compatibility=r["compatibility"], category=r["category"],
                    bonus=r["bonus"], met=json.loads(r["met"]), unmet=json.loads(r["unmet"]),
                    warnings=json.loads(r["warnings"]))
        for r in rows
    ]
