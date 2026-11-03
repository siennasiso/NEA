"""Single-file PawMatch Streamlit application.

Run with:
    pip install streamlit
    streamlit run app.py

The SQLite database is created beside this file at runtime. The demonstration
administrator is ``admin123`` with password ``password123``.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from pathlib import Path
import re
import sqlite3
from typing import Any

import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DATABASE = APP_DIR / "pawmatch.db"
SPECIES = ("Dog", "Cat", "Rabbit")
SIZES = ("Small", "Medium", "Large")
SEXES = ("Female", "Male", "Unknown")


def connection() -> sqlite3.Connection:
    """Return a database connection with named-column access enabled."""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Return a salted scrypt password hash suitable for local coursework use."""
    salt = salt or os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


def password_matches(password: str, encoded: str) -> bool:
    """Check a password against a stored scrypt value."""
    try:
        scheme, salt_hex, expected_hex = encoded.split("$", 2)
        if scheme != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt_hex), n=16384, r=8, p=1
        )
        return hmac.compare_digest(actual, bytes.fromhex(expected_hex))
    except (ValueError, TypeError):
        return False


def initialise_database() -> None:
    """Create the schema and repeatable demonstration records."""
    with connection() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                age INTEGER NOT NULL CHECK (age >= 18),
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin'))
            );

            CREATE TABLE IF NOT EXISTS animals (
                animal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                species TEXT NOT NULL CHECK (species IN ('Dog', 'Cat', 'Rabbit')),
                breed TEXT NOT NULL,
                age REAL NOT NULL CHECK (age > 0 AND age <= 40),
                sex TEXT NOT NULL CHECK (sex IN ('Female', 'Male', 'Unknown')),
                size TEXT NOT NULL CHECK (size IN ('Small', 'Medium', 'Large')),
                personality TEXT NOT NULL,
                activity_level INTEGER NOT NULL CHECK (activity_level BETWEEN 1 AND 3),
                housing_level INTEGER NOT NULL CHECK (housing_level BETWEEN 1 AND 3),
                garden_required INTEGER NOT NULL CHECK (garden_required IN (0, 1)),
                max_hours_alone INTEGER NOT NULL CHECK (max_hours_alone BETWEEN 0 AND 24),
                child_compatible INTEGER NOT NULL CHECK (child_compatible IN (0, 1)),
                medical_notes TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Available' CHECK (status IN ('Available', 'Adopted'))
            );

            CREATE TABLE IF NOT EXISTS questionnaire_responses (
                response_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                housing_level INTEGER NOT NULL CHECK (housing_level BETWEEN 1 AND 3),
                garden_access INTEGER NOT NULL CHECK (garden_access IN (0, 1)),
                hours_left_alone INTEGER NOT NULL CHECK (hours_left_alone BETWEEN 0 AND 24),
                has_children INTEGER NOT NULL CHECK (has_children IN (0, 1)),
                activity_level INTEGER NOT NULL CHECK (activity_level BETWEEN 1 AND 3),
                preferred_species TEXT NOT NULL,
                preferred_size TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            );
            """
        )
        admin = db.execute("SELECT user_id FROM users WHERE email = ?", ("admin@pawmatch.local",)).fetchone()
        if admin is None:
            db.execute(
                "INSERT INTO users (name, email, age, password_hash, role) VALUES (?, ?, ?, ?, 'admin')",
                ("PawMatch Admin", "admin@pawmatch.local", 18, hash_password("password123")),
            )
        else:
            db.execute(
                "UPDATE users SET name=?, password_hash=?, role='admin' WHERE user_id=?",
                ("PawMatch Admin", hash_password("password123"), admin["user_id"]),
            )

        if db.execute("SELECT COUNT(*) FROM animals").fetchone()[0] == 0:
            animals = [
                ("Luna", "Dog", "Labrador", 3, "Female", "Large", "Friendly, energetic and happiest with an active family.", 3, 3, 1, 4, 1, "", "Available"),
                ("Milo", "Cat", "Domestic Shorthair", 2, "Male", "Small", "Calm, affectionate and comfortable in a quieter home.", 1, 1, 0, 8, 1, "", "Available"),
                ("Clover", "Rabbit", "Mini Lop", 1.5, "Female", "Small", "Gentle and curious; needs patient daily handling.", 2, 1, 0, 6, 1, "Routine dental checks", "Available"),
                ("Archie", "Dog", "Spaniel", 5, "Male", "Medium", "Playful and clever with a strong need for exercise.", 3, 2, 1, 3, 0, "", "Available"),
                ("Nala", "Cat", "British Shorthair", 4, "Female", "Medium", "Independent but enjoys company and predictable routines.", 1, 2, 0, 10, 1, "Weight-management diet", "Available"),
                ("Teddy", "Rabbit", "Rex", 2, "Male", "Small", "Sociable, food-motivated and used to indoor living.", 2, 1, 0, 5, 1, "", "Available"),
            ]
            db.executemany(
                """INSERT INTO animals
                   (name, species, breed, age, sex, size, personality, activity_level,
                    housing_level, garden_required, max_hours_alone, child_compatible,
                    medical_notes, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                animals,
            )


def rows(query: str, parameters: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    """Return query results as ordinary dictionaries."""
    with connection() as db:
        return [dict(row) for row in db.execute(query, parameters).fetchall()]


def row(query: str, parameters: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    """Return one query result as a dictionary."""
    with connection() as db:
        result = db.execute(query, parameters).fetchone()
        return dict(result) if result else None


def authenticate(identifier: str, password: str) -> dict[str, Any] | None:
    """Authenticate an adopter by email or the demonstration admin by username."""
    identifier = identifier.strip().lower()
    if identifier == "admin123":
        identifier = "admin@pawmatch.local"
    user = row("SELECT * FROM users WHERE email = ? COLLATE NOCASE", (identifier,))
    return user if user and password_matches(password, user["password_hash"]) else None


def create_account(name: str, email: str, age: int, password: str) -> tuple[bool, str]:
    """Validate and create an adopter account."""
    name, email = name.strip(), email.strip().lower()
    if not 2 <= len(name) <= 50:
        return False, "Name must be between 2 and 50 characters."
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return False, "Enter a valid email address."
    if age < 18:
        return False, "You must be at least 18 to register."
    if len(password) < 8:
        return False, "Password must contain at least 8 characters."
    try:
        with connection() as db:
            db.execute(
                "INSERT INTO users (name, email, age, password_hash) VALUES (?, ?, ?, ?)",
                (name, email, age, hash_password(password)),
            )
    except sqlite3.IntegrityError:
        return False, "An account with that email already exists."
    return True, "Account created. You can now log in."


def latest_answers(user_id: int) -> dict[str, Any] | None:
    """Return a user's newest questionnaire response."""
    return row(
        "SELECT * FROM questionnaire_responses WHERE user_id=? ORDER BY response_id DESC LIMIT 1",
        (user_id,),
    )


def calculate_match(animal: dict[str, Any], answers: dict[str, Any]) -> dict[str, Any]:
    """Calculate the designed 72-point welfare score and preference tie-break."""
    checks = [
        (answers["hours_left_alone"] <= animal["max_hours_alone"], 20, f"Can be left for up to {animal['max_hours_alone']} hours", True),
        (not answers["has_children"] or animal["child_compatible"], 15, "Suitable for a home with children", True),
        (answers["housing_level"] >= animal["housing_level"], 15, f"Needs housing level {animal['housing_level']}", False),
        (answers["activity_level"] >= animal["activity_level"], 12, f"Needs activity level {animal['activity_level']}", False),
        (not animal["garden_required"] or answers["garden_access"], 10, "Requires garden access", True),
    ]
    score = sum(points for passed, points, _, _ in checks if passed)
    percentage = round(score / 72 * 100, 1)
    failed = [message for passed, _, message, _ in checks if not passed]
    compulsory_failed = any(not passed and compulsory for passed, _, _, compulsory in checks)
    if compulsory_failed:
        category = "Ineligible"
    elif percentage >= 90:
        category = "Strong"
    elif percentage >= 80:
        category = "Good"
    elif percentage >= 70:
        category = "Possible"
    else:
        category = "Low"
    preference = 0
    if answers["preferred_species"] != "No preference" and answers["preferred_species"] == animal["species"]:
        preference += 10
    if answers["preferred_size"] != "No preference" and answers["preferred_size"] == animal["size"]:
        preference += 5
    return {**animal, "points": score, "compatibility": percentage, "category": category, "failed": failed, "preference": preference}


def logout() -> None:
    """Clear authentication and page state."""
    for key in list(st.session_state):
        del st.session_state[key]
    st.rerun()


def login_page() -> None:
    """Render login and registration in a single entry page."""
    st.title("🐾 PawMatch")
    st.subheader("Find an animal who fits your life")
    login_tab, register_tab = st.tabs(["Log in", "Create account"])
    with login_tab:
        with st.form("login"):
            identifier = st.text_input("Email address or admin username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in", type="primary")
        if submitted:
            user = authenticate(identifier, password)
            if user is None:
                st.error("The login details are incorrect.")
            else:
                st.session_state.user_id = user["user_id"]
                st.session_state.name = user["name"]
                st.session_state.role = user["role"]
                st.rerun()
        st.caption("Demonstration administrator: admin123 / password123")
    with register_tab:
        with st.form("registration"):
            name = st.text_input("Full name")
            email = st.text_input("Email address")
            age = st.number_input("Age", min_value=18, max_value=120, value=18)
            password = st.text_input("Password", type="password", key="register_password")
            confirmation = st.text_input("Confirm password", type="password")
            submitted = st.form_submit_button("Create account", type="primary")
        if submitted:
            if password != confirmation:
                st.error("Passwords do not match.")
            else:
                ok, message = create_account(name, email, int(age), password)
                (st.success if ok else st.error)(message)


def home_page() -> None:
    """Render the adopter home page."""
    st.title(f"Welcome, {st.session_state.name} 🐾")
    st.write("PawMatch compares your home and lifestyle with each animal's welfare needs.")
    available = rows("SELECT * FROM animals WHERE status='Available' ORDER BY animal_id")
    c1, c2, c3 = st.columns(3)
    c1.metric("Animals available", len(available))
    c2.metric("Supported species", len({a["species"] for a in available}))
    c3.metric("Questionnaire", "Complete" if latest_answers(st.session_state.user_id) else "Not started")
    st.info("Use the sidebar to browse animals, complete the questionnaire and view your matches.")


def browse_page() -> None:
    """Render searchable animal profiles."""
    st.title("Browse animals")
    search = st.text_input("Search by name or breed", max_chars=50).strip().lower()
    c1, c2 = st.columns(2)
    species = c1.selectbox("Species", ("All",) + SPECIES)
    size = c2.selectbox("Size", ("All",) + SIZES)
    animals = rows("SELECT * FROM animals WHERE status='Available' ORDER BY name")
    animals = [
        a for a in animals
        if (not search or search in a["name"].lower() or search in a["breed"].lower())
        and (species == "All" or a["species"] == species)
        and (size == "All" or a["size"] == size)
    ]
    if not animals:
        st.warning("No available animals match those filters.")
    for animal in animals:
        with st.expander(f"🐾 {animal['name']} — {animal['species']} · {animal['breed']}"):
            st.write(animal["personality"])
            st.write(f"**Age:** {animal['age']:g} years  |  **Sex:** {animal['sex']}  |  **Size:** {animal['size']}")
            st.write(f"**Activity:** {animal['activity_level']}/3  |  **Housing:** {animal['housing_level']}/3  |  **Maximum time alone:** {animal['max_hours_alone']} hours")
            requirements = []
            if animal["garden_required"]:
                requirements.append("secure garden")
            if not animal["child_compatible"]:
                requirements.append("adult-only home")
            st.write("**Key requirements:** " + (", ".join(requirements) if requirements else "No additional compulsory requirements"))
            if animal["medical_notes"]:
                st.write(f"**Medical notes:** {animal['medical_notes']}")


def questionnaire_page() -> None:
    """Collect and save the seven designed adopter answers."""
    st.title("Adoption questionnaire")
    previous = latest_answers(st.session_state.user_id) or {}
    with st.form("questionnaire"):
        st.subheader("Home")
        housing = st.radio("Available living space", (1, 2, 3), format_func=lambda x: {1: "Flat or limited space", 2: "Small or medium house", 3: "Large house"}[x], horizontal=True, index=max(0, int(previous.get("housing_level", 1)) - 1))
        garden = st.radio("Do you have garden access?", (False, True), format_func=lambda x: "Yes" if x else "No", horizontal=True, index=int(bool(previous.get("garden_access", 0))))
        st.subheader("Household and lifestyle")
        children = st.radio("Do children live in the home?", (False, True), format_func=lambda x: "Yes" if x else "No", horizontal=True, index=int(bool(previous.get("has_children", 0))))
        activity = st.radio("Activity level you can support", (1, 2, 3), format_func=lambda x: {1: "Low", 2: "Moderate", 3: "High"}[x], horizontal=True, index=max(0, int(previous.get("activity_level", 1)) - 1))
        alone = st.number_input("Hours the animal would usually be left alone", min_value=0, max_value=24, value=int(previous.get("hours_left_alone", 0)))
        st.subheader("Preferences")
        preferred_species = st.selectbox("Preferred species", ("No preference",) + SPECIES, index=(("No preference",) + SPECIES).index(previous.get("preferred_species", "No preference")))
        preferred_size = st.selectbox("Preferred size", ("No preference",) + SIZES, index=(("No preference",) + SIZES).index(previous.get("preferred_size", "No preference")))
        submitted = st.form_submit_button("Save and calculate matches", type="primary")
    if submitted:
        with connection() as db:
            db.execute(
                """INSERT INTO questionnaire_responses
                   (user_id, housing_level, garden_access, hours_left_alone,
                    has_children, activity_level, preferred_species, preferred_size)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (st.session_state.user_id, housing, int(garden), int(alone), int(children), activity, preferred_species, preferred_size),
            )
        st.success("Your answers were saved. Open My Matches to see the results.")


def matches_page() -> None:
    """Calculate and render ranked eligible animal matches."""
    st.title("My matches")
    answers = latest_answers(st.session_state.user_id)
    if answers is None:
        st.warning("Complete the questionnaire before viewing matches.")
        return
    matches = [calculate_match(a, answers) for a in rows("SELECT * FROM animals WHERE status='Available'")]
    matches = [m for m in matches if m["category"] != "Ineligible" and m["compatibility"] >= 70]
    matches.sort(key=lambda m: (-m["compatibility"], -m["preference"], m["animal_id"]))
    if not matches:
        st.warning("There are no eligible matches for the latest answers. Staff make every final adoption decision.")
        return
    st.caption("Compatibility is based on welfare requirements. Species and size only break ties.")
    for position, animal in enumerate(matches[:5], 1):
        with st.container(border=True):
            st.subheader(f"{position}. {animal['name']} — {animal['compatibility']}% {animal['category']}")
            st.write(f"{animal['species']} · {animal['breed']} · {animal['size']}")
            st.progress(animal["compatibility"] / 100)
            st.write(animal["personality"])
            if animal["failed"]:
                st.write("**Points to consider:** " + "; ".join(animal["failed"]))


def account_page() -> None:
    """Render the active adopter's stored account details."""
    st.title("My account")
    user = row("SELECT name, email, age, role FROM users WHERE user_id=?", (st.session_state.user_id,))
    if user:
        st.write(f"**Name:** {user['name']}")
        st.write(f"**Email:** {user['email']}")
        st.write(f"**Age:** {user['age']}")
        st.write(f"**Account type:** {user['role'].title()}")


def animal_form(prefix: str, defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    """Render shared admin animal fields and return their values."""
    d = defaults or {}
    name = st.text_input("Name", value=str(d.get("name", "")), key=f"{prefix}_name")
    species = st.selectbox("Species", SPECIES, index=SPECIES.index(d.get("species", "Dog")), key=f"{prefix}_species")
    breed = st.text_input("Breed", value=str(d.get("breed", "")), key=f"{prefix}_breed")
    c1, c2, c3 = st.columns(3)
    age = c1.number_input("Age", min_value=0.1, max_value=40.0, value=float(d.get("age", 1.0)), step=0.1, key=f"{prefix}_age")
    sex = c2.selectbox("Sex", SEXES, index=SEXES.index(d.get("sex", "Unknown")), key=f"{prefix}_sex")
    size = c3.selectbox("Size", SIZES, index=SIZES.index(d.get("size", "Medium")), key=f"{prefix}_size")
    personality = st.text_area("Personality and care information", value=str(d.get("personality", "")), key=f"{prefix}_personality")
    c1, c2, c3 = st.columns(3)
    activity = c1.selectbox("Activity level", (1, 2, 3), index=int(d.get("activity_level", 1)) - 1, key=f"{prefix}_activity")
    housing = c2.selectbox("Housing level", (1, 2, 3), index=int(d.get("housing_level", 1)) - 1, key=f"{prefix}_housing")
    max_alone = c3.number_input("Maximum hours alone", min_value=0, max_value=24, value=int(d.get("max_hours_alone", 0)), key=f"{prefix}_alone")
    c1, c2, c3 = st.columns(3)
    garden = c1.checkbox("Garden required", value=bool(d.get("garden_required", 0)), key=f"{prefix}_garden")
    children = c2.checkbox("Suitable with children", value=bool(d.get("child_compatible", 0)), key=f"{prefix}_children")
    status = c3.selectbox("Status", ("Available", "Adopted"), index=("Available", "Adopted").index(d.get("status", "Available")), key=f"{prefix}_status")
    medical = st.text_area("Medical notes", value=str(d.get("medical_notes", "")), key=f"{prefix}_medical")
    return {"name": name.strip(), "species": species, "breed": breed.strip(), "age": age, "sex": sex, "size": size, "personality": personality.strip(), "activity_level": activity, "housing_level": housing, "garden_required": int(garden), "max_hours_alone": int(max_alone), "child_compatible": int(children), "medical_notes": medical.strip(), "status": status}


def validate_animal(animal: dict[str, Any]) -> str | None:
    """Return the first animal validation error, if any."""
    if not 2 <= len(animal["name"]) <= 50:
        return "Name must be between 2 and 50 characters."
    if not 2 <= len(animal["breed"]) <= 50:
        return "Breed must be between 2 and 50 characters."
    if not 20 <= len(animal["personality"]) <= 1000:
        return "Personality information must be between 20 and 1,000 characters."
    return None


def save_animal(animal: dict[str, Any], animal_id: int | None = None) -> None:
    """Insert or update one validated animal record."""
    values = tuple(animal.values())
    with connection() as db:
        if animal_id is None:
            db.execute(
                """INSERT INTO animals
                   (name, species, breed, age, sex, size, personality, activity_level,
                    housing_level, garden_required, max_hours_alone, child_compatible,
                    medical_notes, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                values,
            )
        else:
            db.execute(
                """UPDATE animals SET name=?, species=?, breed=?, age=?, sex=?, size=?,
                   personality=?, activity_level=?, housing_level=?, garden_required=?,
                   max_hours_alone=?, child_compatible=?, medical_notes=?, status=?
                   WHERE animal_id=?""",
                values + (animal_id,),
            )


def admin_page() -> None:
    """Render the staff CRUD dashboard."""
    st.title("Administrator dashboard")
    animals = rows("SELECT * FROM animals ORDER BY name")
    available = sum(a["status"] == "Available" for a in animals)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total animals", len(animals))
    c2.metric("Available", available)
    c3.metric("Adopted", len(animals) - available)
    list_tab, add_tab, edit_tab, delete_tab = st.tabs(["Animals", "Add", "Edit", "Delete"])
    with list_tab:
        st.dataframe([{k: a[k] for k in ("animal_id", "name", "species", "breed", "age", "size", "status")} for a in animals], hide_index=True, width="stretch")
    with add_tab:
        with st.form("add_animal"):
            animal = animal_form("add")
            submitted = st.form_submit_button("Add animal", type="primary")
        if submitted:
            error = validate_animal(animal)
            if error:
                st.error(error)
            else:
                save_animal(animal)
                st.success("Animal added.")
                st.rerun()
    with edit_tab:
        if animals:
            selected_id = st.selectbox("Choose animal", [a["animal_id"] for a in animals], format_func=lambda i: next(a["name"] for a in animals if a["animal_id"] == i), key="edit_choice")
            selected = next(a for a in animals if a["animal_id"] == selected_id)
            with st.form("edit_animal"):
                animal = animal_form(f"edit_{selected_id}", selected)
                submitted = st.form_submit_button("Save changes", type="primary")
            if submitted:
                error = validate_animal(animal)
                if error:
                    st.error(error)
                else:
                    save_animal(animal, selected_id)
                    st.success("Changes saved.")
                    st.rerun()
    with delete_tab:
        if animals:
            selected_id = st.selectbox("Choose animal to delete", [a["animal_id"] for a in animals], format_func=lambda i: next(a["name"] for a in animals if a["animal_id"] == i), key="delete_choice")
            selected_name = next(a["name"] for a in animals if a["animal_id"] == selected_id)
            confirmed = st.checkbox(f"I understand that {selected_name} will be permanently deleted")
            if st.button("Delete animal", type="primary", disabled=not confirmed):
                with connection() as db:
                    db.execute("DELETE FROM animals WHERE animal_id=?", (selected_id,))
                st.success("Animal deleted.")
                st.rerun()


def apply_style() -> None:
    """Apply compact shared presentation styles without external assets."""
    st.markdown(
        """
        <style>
        :root { --pink:#d93679; --soft:#fff2f7; }
        .stApp { background: linear-gradient(180deg, #fffafd 0%, #ffffff 36%); }
        h1, h2, h3 { color:#3f2633; }
        div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] {
            background:#d93679; border-color:#d93679;
        }
        [data-testid="stMetric"] { background:#fff2f7; padding:1rem; border-radius:1rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Initialise PawMatch and route the active single-page session."""
    st.set_page_config(page_title="PawMatch", page_icon="🐾", layout="wide")
    initialise_database()
    apply_style()
    if "user_id" not in st.session_state:
        login_page()
        return

    role = st.session_state.get("role", "user")
    with st.sidebar:
        st.title("🐾 PawMatch")
        st.write(st.session_state.name)
        if role == "admin":
            page = st.radio("Navigation", ("Admin", "Browse animals"))
        else:
            page = st.radio("Navigation", ("Home", "Browse animals", "Questionnaire", "My matches", "My account"))
        if st.button("Log out", width="stretch"):
            logout()

    pages = {
        "Home": home_page,
        "Browse animals": browse_page,
        "Questionnaire": questionnaire_page,
        "My matches": matches_page,
        "My account": account_page,
        "Admin": admin_page,
    }
    pages[page]()


if __name__ == "__main__":
    main()
