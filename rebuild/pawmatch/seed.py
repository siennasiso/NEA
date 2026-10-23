"""Demo data and the staff-account command.

    python -m pawmatch.seed                      # create tables and demo animals
    python -m pawmatch.seed --admin EMAIL        # also create (or promote) a staff account
"""

from __future__ import annotations

import argparse
import getpass
import os
import sqlite3
import sys

from . import db
from .auth import register
from .validation import validate_animal

DEFAULT_DB = os.environ.get("PAWMATCH_DB", "data/pawmatch.db")

# name, species, breed, age, sex, size, exercise, housing, garden, children, hours, personality, medical
DEMO_ANIMALS: tuple[tuple, ...] = (
    ("Luna", "Dog", "Labrador cross", 4, "Female", "Large", 3, 2, 1, 1, 4, "Gentle, loves fetch and long walks.", ""),
    ("Archie", "Dog", "Cocker spaniel", 3, "Male", "Medium", 2, 2, 1, 1, 4, "Cheerful and eager to please.", "Ear drops twice weekly."),
    ("Nala", "Dog", "Staffordshire bull terrier cross", 5, "Female", "Medium", 2, 2, 1, 0, 3, "Loyal and affectionate with adults.", ""),
    ("Max", "Dog", "German shepherd cross", 6, "Male", "Large", 3, 3, 1, 0, 3, "Clever, needs training and space.", "Mild hip stiffness."),
    ("Oscar", "Dog", "Jack Russell terrier cross", 8, "Male", "Small", 2, 1, 0, 1, 4, "Small, bright and playful.", ""),
    ("Milo", "Cat", "Domestic shorthair", 2, "Male", "Medium", 1, 1, 0, 1, 8, "Calm lap cat who likes routine.", ""),
    ("Bella", "Cat", "British shorthair cross", 7, "Female", "Medium", 1, 1, 0, 1, 9, "Quiet and independent.", ""),
    ("Simba", "Cat", "Domestic longhair", 4, "Male", "Medium", 2, 2, 1, 0, 8, "Curious outdoor explorer.", "Needs regular grooming."),
    ("Willow", "Cat", "Domestic shorthair", 12, "Female", "Small", 1, 1, 0, 1, 10, "Senior cat, very relaxed.", "Thyroid tablet daily."),
    ("Poppy", "Rabbit", "Mini lop", 2, "Female", "Small", 1, 1, 0, 1, 8, "Gentle and enjoys being stroked.", ""),
    ("Teddy", "Rabbit", "Lionhead", 3, "Male", "Small", 1, 1, 0, 0, 8, "Shy; best in a calm adult home.", ""),
    ("Daisy", "Rabbit", "Dutch rabbit", 4, "Female", "Small", 2, 2, 1, 1, 6, "Lively and loves a big run.", ""),
    ("Clover", "Rabbit", "Rex rabbit", 1, "Female", "Medium", 2, 2, 1, 1, 6, "Inquisitive young rabbit.", "Recently neutered."),
)


def demo_animal_values() -> list[dict]:
    keys = ("name", "species", "breed", "age", "sex", "size", "exercise_needs", "min_housing_level",
            "garden_required", "child_compatible", "max_hours_alone", "personality", "medical_notes")
    rows = []
    for row in DEMO_ANIMALS:
        values = dict(zip(keys, row))
        values["image_path"] = f"assets/animals/{values['name'].lower()}.jpg"
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


def prepare(path: str = DEFAULT_DB) -> None:
    """Create the schema and seed demo animals if needed; safe to call on every start."""
    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with db.connect(path) as conn:
        db.init_schema(conn)
        seed_animals(conn)


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
