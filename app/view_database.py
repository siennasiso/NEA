"""Display safe PawMatch database records without exposing password hashes."""

from argparse import ArgumentParser

from pawmatch_animals import fetch_animals, get_admin_summary, initialise_animals_table
from pawmatch_auth import DATABASE_PATH, get_connection, initialise_database
from pawmatch_matching import initialise_matching_tables


def list_users() -> None:
    """Print non-sensitive user fields."""
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
    """Print a compact list of animal records."""
    print("animal_id | name | species | breed | age | status")
    for animal in sorted(fetch_animals(), key=lambda item: item["animal_id"]):
        print(
            f"{animal['animal_id']} | {animal['name']} | {animal['species']} | "
            f"{animal['breed']} | {animal['age_years']:g} | {animal['status']}"
        )


def list_responses() -> None:
    """Print submitted questionnaire answers without authentication data."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT response_id, user_id, housing_level, garden_access,
                   hours_left_alone, has_children, preferred_activity_level,
                   preferred_species, preferred_size, completed_at
            FROM questionnaire_responses
            ORDER BY response_id
            """
        ).fetchall()
    print("response_id | user_id | home | garden | alone | children | activity | species | size | completed_at")
    for row in rows:
        print(" | ".join(str(row[key]) for key in row.keys()))


def list_matches() -> None:
    """Print stored scores and categories joined to animal names."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT mr.match_id, mr.response_id, a.name, mr.compatibility_score,
                   mr.match_category, mr.calculated_at
            FROM match_results AS mr
            JOIN animals AS a ON a.animal_id = mr.animal_id
            ORDER BY mr.response_id, mr.ranking_score DESC
            """
        ).fetchall()
    print("match_id | response_id | animal | compatibility | category | calculated_at")
    for row in rows:
        print(" | ".join(str(row[key]) for key in row.keys()))


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "table",
        nargs="?",
        choices=("summary", "users", "animals", "responses", "matches"),
        default="summary",
    )
    arguments = parser.parse_args()
    initialise_database()
    initialise_animals_table()
    initialise_matching_tables()

    print(f"Database: {DATABASE_PATH}")
    if arguments.table == "users":
        list_users()
    elif arguments.table == "animals":
        list_animals()
    elif arguments.table == "responses":
        list_responses()
    elif arguments.table == "matches":
        list_matches()
    else:
        summary = get_admin_summary()
        with get_connection() as connection:
            user_count = int(connection.execute("SELECT COUNT(*) FROM users").fetchone()[0])
        print(f"Users: {user_count}")
        for label, value in summary.items():
            print(f"Animals {label.replace('_', ' ')}: {value}")


if __name__ == "__main__":
    main()
