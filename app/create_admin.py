"""Create a PawMatch administrator account. Run: python create_admin.py"""

from getpass import getpass

from pawmatch_auth import create_admin_user, initialise_database, validate_registration


def main() -> None:
    initialise_database()
    print("\nCreate a PawMatch administrator account\n")
    name = input("Full name: ").strip()
    username = input("Username (3-30 letters, numbers or underscores): ").strip()
    email = input("Email address: ").strip()
    try:
        age = int(input("Age: ").strip())
    except ValueError:
        age = None
    password = getpass("Password: ")
    confirm_password = getpass("Confirm password: ")

    errors, cleaned = validate_registration(name, email, age, password, confirm_password)
    if errors:
        print("\nThe account was not created:")
        for message in errors.values():
            print(f"- {message}")
        return

    success, message = create_admin_user(
        cleaned["name"],
        cleaned["email"],
        int(cleaned["age"]),
        cleaned["password"],
        username=username,
    )
    print("\nAdministrator account created." if success else f"\n{message}")


if __name__ == "__main__":
    main()
