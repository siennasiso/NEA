"""Demo data, the staff-account command and first-run setup.

    python -m pawmatch.seed                      # create tables and demo animals
    python -m pawmatch.seed --admin EMAIL        # also create (or promote) a staff account

On a server, set PAWMATCH_ADMIN_EMAIL and PAWMATCH_ADMIN_PASSWORD instead: prepare() creates
that staff account on first start, so a fresh deployment has a demo login without a shell.
"""

from __future__ import annotations

import argparse
import getpass
import os
import sqlite3
import sys
from collections.abc import Mapping

from . import db
from .auth import register
from .validation import validate_animal

DEFAULT_DB = os.environ.get("PAWMATCH_DB", "data/pawmatch.db")

# name, species, breed, age, sex, size, exercise, housing, garden, children, hours, personality, medical
DEMO_ANIMALS: tuple[tuple, ...] = (
    ("Luna", "Dog", "Labrador cross", 4, "Female", "Large", 3, 2, 1, 1, 4, "Luna is an affectionate and energetic dog who enjoys long walks, training games and spending time with people.", ""),
    ("Archie", "Dog", "Cocker spaniel", 3, "Male", "Medium", 2, 2, 1, 1, 4, "Archie is a friendly dog who enjoys steady walks, human company and relaxing in a comfortable home.", "Ear drops twice weekly."),
    ("Nala", "Dog", "Staffordshire bull terrier cross", 5, "Female", "Medium", 2, 2, 1, 0, 3, "Nala is a bright and energetic dog who needs consistent training, active walks and careful introductions.", ""),
    ("Max", "Dog", "German shepherd cross", 6, "Male", "Large", 3, 3, 1, 0, 3, "Max is a loyal working-breed dog who needs an experienced adult home, structured training and daily exercise.", "Mild hip stiffness."),
    ("Oscar", "Dog", "Jack Russell terrier cross", 8, "Male", "Small", 2, 1, 0, 1, 4, "Oscar is a cheerful small dog who likes brisk walks, puzzle toys and being involved in family life.", ""),
    ("Milo", "Cat", "Domestic shorthair", 2, "Male", "Medium", 1, 1, 0, 1, 8, "Milo is a calm cat who enjoys quiet company, window watching and short play sessions in a settled home.", ""),
    ("Bella", "Cat", "British shorthair cross", 7, "Female", "Medium", 1, 1, 0, 1, 9, "Bella is a gentle indoor cat who enjoys quiet company, soft beds and short play sessions each day.", ""),
    ("Simba", "Cat", "Domestic longhair", 4, "Male", "Medium", 2, 2, 1, 0, 8, "Simba is an independent long-haired cat who prefers a peaceful adult home and regular grooming.", "Needs regular grooming."),
    ("Willow", "Cat", "Domestic shorthair", 12, "Female", "Small", 1, 1, 0, 1, 10, "Willow is a relaxed older cat who enjoys warm resting places, gentle affection and a predictable routine.", "Thyroid tablet daily."),
    ("Poppy", "Rabbit", "Mini lop", 2, "Female", "Small", 1, 1, 0, 1, 8, "Poppy is a curious rabbit who needs a spacious enclosure, daily enrichment and gentle handling from her adopter.", ""),
    ("Teddy", "Rabbit", "Lionhead", 3, "Male", "Small", 1, 1, 0, 0, 8, "Teddy is a shy rabbit who needs patient handling, a roomy enclosure and calm daily interaction.", ""),
    ("Daisy", "Rabbit", "Dutch rabbit", 4, "Female", "Small", 2, 2, 1, 1, 6, "Daisy is a sociable rabbit who enjoys enrichment, supervised exploration and gentle family attention.", ""),
    ("Clover", "Rabbit", "Rex rabbit", 1, "Female", "Medium", 2, 2, 1, 1, 6, "Clover is an inquisitive rabbit who needs generous indoor space, secure outdoor exercise and patient care.", "Recently neutered."),
)


# Most demo animals are Available; one is Reserved and one Adopted, to show the status in use.
DEMO_STATUSES = {"Max": "Reserved", "Bella": "Adopted"}


def demo_animal_values() -> list[dict]:
    keys = ("name", "species", "breed", "age", "sex", "size", "exercise_needs", "min_housing_level",
            "garden_required", "child_compatible", "max_hours_alone", "personality", "medical_notes")
    rows = []
    for row in DEMO_ANIMALS:
        values = dict(zip(keys, row))
        values["image_path"] = f"assets/animals/{values['name'].lower()}.png"
        values["status"] = DEMO_STATUSES.get(values["name"], "Available")
        rows.append(values)
    return rows


def seed_animals(conn: sqlite3.Connection) -> int:
    """Insert the demo animals into an empty table; every row passes the same validation as the admin form."""
    if db.count_animals(conn):
        return 0
    for raw in demo_animal_values():
        values, errors = validate_animal(raw)
        if errors:
            raise ValueError(f"Bad demo animal {raw['name']}: {errors}")
        db.insert_animal(conn, values)
    return len(DEMO_ANIMALS)


def prepare(path: str = DEFAULT_DB, env: Mapping[str, str] | None = None) -> str | None:
    """Create the schema, seed demo animals and the env staff account if needed; safe on every start.

    Returns what happened to the env staff account ('created', 'promoted', 'exists' or None).
    A bad PAWMATCH_ADMIN_* value is reported on stderr but never stops the app starting.
    """
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with db.connect(path) as conn:
        db.init_schema(conn)
        seed_animals(conn)
        db.use_png_pictures(conn)
        try:
            return admin_from_env(conn, os.environ if env is None else env)
        except ValueError as problem:
            print(f"PawMatch: staff account from environment not created: {problem}", file=sys.stderr)
            return None


def admin_from_env(conn: sqlite3.Connection, env: Mapping[str, str]) -> str | None:
    """Create (or promote) the staff account named by PAWMATCH_ADMIN_EMAIL / _PASSWORD.

    Both must be set; otherwise nothing happens. An existing staff account is left alone, so a
    password changed later is never reset by a restart. Raises ValueError for invalid details.
    """
    email = env.get("PAWMATCH_ADMIN_EMAIL", "").strip()
    password = env.get("PAWMATCH_ADMIN_PASSWORD", "")
    if not email or not password:
        return None
    found = db.find_user_with_hash(conn, email.lower())
    if found and found[0].is_admin:
        return "exists"
    return create_admin(conn, env.get("PAWMATCH_ADMIN_NAME", "Shelter staff"), email, 30, password)


def create_admin(conn: sqlite3.Connection, name: str, email: str, age: int, password: str) -> str:
    """Register a staff account, or promote an existing account to admin."""
    found = db.find_user_with_hash(conn, email.strip().lower())
    if found:
        db.set_role(conn, found[0].user_id, "admin")
        return "promoted"
    user, errors = register(conn, name, email, age, password, password)
    if user is None:
        raise ValueError("; ".join(errors.values()))
    db.set_role(conn, user.user_id, "admin")
    return "created"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--admin", metavar="EMAIL", help="create or promote a staff account")
    parser.add_argument("--name", default="Shelter staff")
    args = parser.parse_args(argv)
    prepare(args.db)
    if args.admin:
        password = os.environ.get("PAWMATCH_ADMIN_PASSWORD") or getpass.getpass("Staff password: ")
        with db.connect(args.db) as conn:
            print(f"Staff account {create_admin(conn, args.name, args.admin, 30, password)}.")
    print(f"Database ready at {args.db}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
