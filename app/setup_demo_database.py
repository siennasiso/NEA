"""Create the local PawMatch demo database and documented admin login."""

from pawmatch_animals import initialise_animals_table, seed_demo_animals
from pawmatch_auth import DATABASE_PATH, ensure_demo_admin, initialise_database


def setup_demo_database() -> dict[str, int | bool | str]:
    initialise_database()
    initialise_animals_table()
    admin_id, admin_created = ensure_demo_admin()
    animals_added = seed_demo_animals()
    return {
        "database": str(DATABASE_PATH),
        "admin_id": admin_id,
        "admin_created": admin_created,
        "animals_added": animals_added,
    }


def main() -> None:
    result = setup_demo_database()
    print(f"Database ready: {result['database']}")
    print(
        "Demo administrator created."
        if result["admin_created"]
        else "Demo administrator password and role refreshed."
    )
    print(f"Animal records added: {result['animals_added']}")
    print("Login username: admin123")
    print("Login password: password123")
    print("Change this demonstration password before real deployment.")


if __name__ == "__main__":
    main()
