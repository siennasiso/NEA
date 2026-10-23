"""Input validation. Every function returns (cleaned values, errors by field).

An empty errors dict means the input is valid. Uniqueness of email is checked
by the repository, because it needs the database.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from .models import (
    ACTIVITY_LEVELS,
    EXPERIENCE_LEVELS,
    HOUSING_LEVELS,
    NO_PREFERENCE,
    SEXES,
    SIZES,
    SPECIES,
    STATUSES,
    Answers,
)

Errors = dict[str, str]

NAME_MIN, NAME_MAX = 2, 50
MIN_AGE, MAX_AGE = 18, 120
PASSWORD_MIN = 8
ANIMAL_AGE_MAX = 30
TEXT_MAX = 500
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _int(value: Any) -> int | None:
    """Parse a whole number; bools and decimals are rejected."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    text = _text(value)
    return int(text) if re.fullmatch(r"-?\d+", text) else None


def _yes_no(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return {"yes": True, "no": False, "1": True, "0": False}.get(_text(value).lower())


def _has_letter(text: str) -> bool:
    return any(ch.isalpha() for ch in text)


def _check_name(value: Any, errors: Errors, field: str = "name", allow_digits: bool = False) -> str:
    """Person names: letters, spaces, hyphens, apostrophes. Animal names may also use digits ("R2")."""
    name = _text(value)
    allowed = " '-" + ("0123456789" if allow_digits else "")
    if not name:
        errors[field] = "Enter a name."
    elif not NAME_MIN <= len(name) <= NAME_MAX:
        errors[field] = f"Name must be {NAME_MIN} to {NAME_MAX} characters."
    elif not _has_letter(name) or any(not (ch.isalpha() or ch in allowed) for ch in name):
        errors[field] = "Name can only use letters, spaces, hyphens and apostrophes" + (
            " (and numbers)." if allow_digits else ".")
    return name


def _check_range(value: Any, low: int, high: int, field: str, label: str, errors: Errors) -> int | None:
    number = _int(value)
    if number is None:
        errors[field] = f"{label} is required." if _text(value) == "" else f"{label} must be a whole number."
    elif not low <= number <= high:
        errors[field] = f"{label} must be between {low} and {high}."
    return number


def _check_choice(value: Any, options: tuple[str, ...], field: str, label: str, errors: Errors) -> str:
    text = _text(value)
    if text not in options:
        errors[field] = f"Choose a {label}."
    return text


def _check_flag(value: Any, field: str, label: str, errors: Errors) -> bool:
    flag = _yes_no(value)
    if flag is None:
        errors[field] = f"Answer yes or no for {label}."
    return bool(flag)


def validate_person(name: Any, email: Any, age: Any) -> tuple[dict[str, Any], Errors]:
    """Name, email and age: shared by sign-up and by finishing a Google account (criteria 5.1, 5.2)."""
    errors: Errors = {}
    clean_name = _check_name(name, errors)
    clean_email = _text(email).lower()
    if not clean_email:
        errors["email"] = "Enter an email address."
    elif not EMAIL_PATTERN.match(clean_email):
        errors["email"] = "Enter a valid email address, like name@domain.com."
    clean_age = _check_range(age, MIN_AGE, MAX_AGE, "age", "Age", errors)
    if "age" in errors and clean_age is not None and clean_age < MIN_AGE:
        errors["age"] = f"You must be {MIN_AGE} or over to adopt."
    return {"name": clean_name, "email": clean_email, "age": clean_age}, errors


def validate_registration(
    name: Any, email: Any, age: Any, password: Any, confirm: Any
) -> tuple[dict[str, Any], Errors]:
    """Validate a sign-up form (criteria 5.1 and 5.2)."""
    cleaned, errors = validate_person(name, email, age)
    raw_password = "" if password is None else str(password)
    if not raw_password.strip():
        errors["password"] = "Enter a password."
    elif len(raw_password) < PASSWORD_MIN:
        errors["password"] = f"Password must be at least {PASSWORD_MIN} characters."
    elif raw_password != ("" if confirm is None else str(confirm)):
        errors["confirm"] = "The two passwords do not match."
    cleaned["password"] = raw_password
    return cleaned, errors


def validate_login(email: Any, password: Any) -> tuple[dict[str, str], Errors]:
    """Presence checks only; whether the details are right is the auth layer's job."""
    errors: Errors = {}
    clean_email = _text(email).lower()
    raw_password = "" if password is None else str(password)
    if not clean_email:
        errors["email"] = "Enter your email address."
    if not raw_password:
        errors["password"] = "Enter your password."
    return {"email": clean_email, "password": raw_password}, errors


def validate_animal(raw: dict[str, Any]) -> tuple[dict[str, Any], Errors]:
    """Validate an admin's add or edit form (criteria 8.2 and 8.3)."""
    errors: Errors = {}
    cleaned: dict[str, Any] = {"name": _check_name(raw.get("name"), errors, allow_digits=True)}
    cleaned["species"] = _check_choice(raw.get("species"), SPECIES, "species", "species", errors)
    breed = _text(raw.get("breed"))
    if not breed:
        errors["breed"] = "Enter a breed (use 'Mixed' if unknown)."
    elif not NAME_MIN <= len(breed) <= NAME_MAX:
        errors["breed"] = f"Breed must be {NAME_MIN} to {NAME_MAX} characters."
    elif not _has_letter(breed):
        errors["breed"] = "Breed must contain letters."
    cleaned["breed"] = breed
    cleaned["age"] = _check_range(raw.get("age"), 1, ANIMAL_AGE_MAX, "age", "Age", errors)
    cleaned["sex"] = _check_choice(raw.get("sex"), SEXES, "sex", "sex", errors)
    cleaned["size"] = _check_choice(raw.get("size"), SIZES, "size", "size", errors)
    personality = _text(raw.get("personality"))
    if not personality:
        errors["personality"] = "Describe the animal's personality."
    elif len(personality) > TEXT_MAX:
        errors["personality"] = f"Personality must be at most {TEXT_MAX} characters."
    cleaned["personality"] = personality
    cleaned["exercise_needs"] = _check_range(raw.get("exercise_needs"), 1, 3, "exercise_needs", "Exercise needs", errors)
    cleaned["min_housing_level"] = _check_range(
        raw.get("min_housing_level"), 1, 3, "min_housing_level", "Minimum housing level", errors
    )
    cleaned["garden_required"] = _check_flag(raw.get("garden_required"), "garden_required", "garden required", errors)
    cleaned["child_compatible"] = _check_flag(raw.get("child_compatible"), "child_compatible", "child compatible", errors)
    cleaned["max_hours_alone"] = _check_range(raw.get("max_hours_alone"), 0, 24, "max_hours_alone", "Hours alone", errors)
    notes = _text(raw.get("medical_notes"))
    if len(notes) > TEXT_MAX:
        errors["medical_notes"] = f"Medical notes must be at most {TEXT_MAX} characters."
    cleaned["medical_notes"] = notes
    cleaned["image_path"] = _text(raw.get("image_path"))
    # A new record is Available unless staff choose otherwise (the original form's default).
    cleaned["status"] = _check_choice(raw.get("status") or STATUSES[0], STATUSES, "status", "adoption status", errors)
    return cleaned, errors


def _q_housing(v: Any, e: Errors) -> int | None:
    level = _int(v)
    if level not in HOUSING_LEVELS:
        e["housing_level"] = "Choose the type of home you live in."
    return level


def _q_activity(v: Any, e: Errors) -> int | None:
    level = _int(v)
    if level not in ACTIVITY_LEVELS:
        e["activity_level"] = "Choose how active you can be with an animal."
    return level


# One validator per question, grouped by questionnaire step (criterion 6.2).
QUESTION_VALIDATORS: dict[str, Callable[[Any, Errors], Any]] = {
    "housing_level": _q_housing,
    "garden_access": lambda v, e: _check_flag(v, "garden_access", "garden access", e),
    "has_children": lambda v, e: _check_flag(v, "has_children", "children in the home", e),
    "other_pets": lambda v, e: _check_flag(v, "other_pets", "other pets", e),
    "experience": lambda v, e: _check_choice(v, EXPERIENCE_LEVELS, "experience", "level of experience", e),
    "activity_level": _q_activity,
    "hours_alone": lambda v, e: _check_range(v, 0, 24, "hours_alone", "Hours alone", e),
    "preferred_species": lambda v, e: _check_choice(
        v, SPECIES + (NO_PREFERENCE,), "preferred_species", "species or 'No preference'", e
    ),
    "preferred_size": lambda v, e: _check_choice(
        v, SIZES + (NO_PREFERENCE,), "preferred_size", "size or 'No preference'", e
    ),
}

QUESTION_STEPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Your home", ("housing_level", "garden_access")),
    ("Your household", ("has_children", "other_pets")),
    ("Your lifestyle", ("activity_level", "hours_alone", "experience")),
    ("Your preferences", ("preferred_species", "preferred_size")),
)


def validate_step(step: int, raw: dict[str, Any]) -> Errors:
    """Validate only the questions on one step, so users can't move on with gaps."""
    errors: Errors = {}
    for name in QUESTION_STEPS[step][1]:
        QUESTION_VALIDATORS[name](raw.get(name), errors)
    return errors


def validate_question(name: str, value: Any) -> Errors:
    """Validate one answer, so the one-question-per-screen form stops at a gap or a bad value."""
    errors: Errors = {}
    QUESTION_VALIDATORS[name](value, errors)
    return errors


def validate_answers(raw: dict[str, Any]) -> tuple[Answers | None, Errors]:
    """Validate the whole questionnaire; returns Answers only when every answer is valid."""
    errors: Errors = {}
    cleaned = {name: check(raw.get(name), errors) for name, check in QUESTION_VALIDATORS.items()}
    return (None, errors) if errors else (Answers(**cleaned), errors)


IMAGE_TYPES = ("png", "jpg", "jpeg")
IMAGE_MAX_BYTES = 2 * 1024 * 1024


def validate_image(filename: str, size_bytes: int) -> str | None:
    """Return an error message for an unsuitable upload, or None if it is acceptable."""
    if filename.rsplit(".", 1)[-1].lower() not in IMAGE_TYPES:
        return "Images must be PNG or JPG."
    if size_bytes > IMAGE_MAX_BYTES:
        return "Images must be 2 MB or smaller."
    return None
