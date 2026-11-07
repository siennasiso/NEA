"""Build a clean PawMatch database for manual inspection in DB Browser."""

import argparse
from datetime import datetime
from pathlib import Path

from database import DATABASE_PATH, create_database


def back_up_existing_database(database_path: Path) -> Path | None:
    """Move an existing database to a timestamped backup before a clean build."""
    if not database_path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = database_path.with_name(f"pawmatch-{timestamp}.backup.db")
    database_path.replace(backup_path)
    return backup_path


parser = argparse.ArgumentParser(
    description="Create the PawMatch SQLite database for the DB1 manual test."
)
parser.add_argument(
    "--fresh",
    action="store_true",
    help="Back up the current database and create a new empty one.",
)
arguments = parser.parse_args()

backup = back_up_existing_database(DATABASE_PATH) if arguments.fresh else None
created_path = create_database()

if backup is not None:
    print(f"Previous database moved to: {backup}")
print(f"Database ready: {created_path}")
print("Open this file in DB Browser for SQLite and select the Database Structure tab.")

