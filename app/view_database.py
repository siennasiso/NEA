"""Display safe PawMatch database records without exposing password hashes."""

from argparse import ArgumentParser

from pawmatch_animals import fetch_animals, get_admin_summary, initialise_animals_table
from pawmatch_auth import DATABASE_PATH, get_connection, initialise_database


def list_users() -> None:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT user_id, name, username, email, age, role, created_at
            FROM users
            ORDER BY user_id
            """
        ).fetchall()
    print("user_id | name | username | email | age | role | created_at")
    for row in rows:
        print(" | ".join(str(row[key] or "-") for key in row.keys()))


def list_animals() -> None:
    print("animal_id | name | species | breed | age | status")
    for animal in sorted(fetch_animals(), key=lambda item: item["animal_id"]):
        print(
            f"{animal['animal_id']} | {animal['name']} | {animal['species']} | "
            f"{animal['breed']} | {animal['age_years']:g} | {animal['status']}"
        )


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "table",
        nargs="?",
        choices=("summary", "users", "animals"),
        default="summary",
    )
    arguments = parser.parse_args()
    initialise_database()
    initialise_animals_table()

    print(f"Database: {DATABASE_PATH}")
    if arguments.table == "users":
        list_users()
    elif arguments.table == "animals":
        list_animals()
    else:
        summary = get_admin_summary()
        with get_connection() as connection:
            user_count = int(connection.execute("SELECT COUNT(*) FROM users").fetchone()[0])
        print(f"Users: {user_count}")
        for label, value in summary.items():
            print(f"Animals {label.replace('_', ' ')}: {value}")


if __name__ == "__main__":
    main()
