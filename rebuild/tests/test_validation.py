"""Validation: normal, boundary and erroneous data for every form."""

import pytest

from pawmatch.validation import (
    QUESTION_STEPS,
    validate_animal,
    validate_answers,
    validate_login,
    validate_registration,
    validate_step,
)

GOOD_ANIMAL = {
    "name": "Luna", "species": "Dog", "breed": "Labrador cross", "age": "4", "sex": "Female",
    "size": "Large", "personality": "Gentle", "exercise_needs": 3, "min_housing_level": 2,
    "garden_required": "Yes", "child_compatible": "No", "max_hours_alone": 4, "medical_notes": "",
}
GOOD_ANSWERS = {
    "housing_level": 2, "garden_access": "Yes", "has_children": "No", "other_pets": "No",
    "experience": "None", "activity_level": 2, "hours_alone": 4,
    "preferred_species": "Cat", "preferred_size": "No preference",
}


def register(**overrides):
    fields = {"name": "Sam Lee", "email": "Sam@Example.com ", "age": "30",
              "password": "longenough", "confirm": "longenough"} | overrides
    return validate_registration(**fields)


def test_valid_registration_is_cleaned():
    cleaned, errors = register(name="  Sam Lee  ")
    assert errors == {}
    assert cleaned["name"] == "Sam Lee"
    assert cleaned["email"] == "sam@example.com"
    assert cleaned["age"] == 30


@pytest.mark.parametrize("field,value", [("name", "   "), ("email", ""), ("age", ""), ("password", "")])
def test_registration_rejects_blank_required_fields(field, value):
    _, errors = register(**{field: value})
    assert field in errors


@pytest.mark.parametrize("email", ["no-at-sign.com", "a@b", "two@@x.com", "spa ce@x.com"])
def test_registration_rejects_bad_email_format(email):
    assert "email" in register(email=email)[1]


@pytest.mark.parametrize("age,ok", [("17", False), ("18", True), ("120", True), ("121", False), ("2.5", False), ("abc", False)])
def test_registration_age_boundaries(age, ok):
    assert ("age" not in register(age=age)[1]) is ok


def test_under_18_message_is_specific():
    assert "18 or over" in register(age="17")[1]["age"]


@pytest.mark.parametrize("password,ok", [("1234567", False), ("12345678", True)])
def test_password_minimum_length_boundary(password, ok):
    assert ("password" not in register(password=password, confirm=password)[1]) is ok


def test_password_confirmation_must_match():
    assert "confirm" in register(confirm="different1")[1]


def test_name_length_boundaries():
    assert "name" in register(name="A")[1]
    assert "name" not in register(name="Al")[1]
    assert "name" in register(name="x" * 51)[1]


def test_login_presence_checks():
    _, errors = validate_login("", "")
    assert set(errors) == {"email", "password"}


def test_valid_animal_passes_and_converts_types():
    cleaned, errors = validate_animal(GOOD_ANIMAL)
    assert errors == {}
    assert cleaned["age"] == 4 and cleaned["garden_required"] is True and cleaned["child_compatible"] is False


@pytest.mark.parametrize("field,value", [
    ("name", ""), ("species", "Hamster"), ("breed", ""), ("age", 0), ("age", 31), ("sex", "?"),
    ("size", "Huge"), ("personality", " "), ("exercise_needs", 4), ("min_housing_level", 0),
    ("garden_required", "maybe"), ("max_hours_alone", 25), ("max_hours_alone", -1),
    ("medical_notes", "x" * 501),
])
def test_invalid_animal_fields_are_rejected(field, value):
    assert field in validate_animal(GOOD_ANIMAL | {field: value})[1]


def test_full_questionnaire_returns_answers():
    answers, errors = validate_answers(GOOD_ANSWERS)
    assert errors == {}
    assert answers.garden_access is True and answers.hours_alone == 4


def test_unanswered_question_blocks_submission():
    answers, errors = validate_answers(GOOD_ANSWERS | {"hours_alone": None})
    assert answers is None and "hours_alone" in errors


@pytest.mark.parametrize("hours,ok", [(-1, False), (0, True), (24, True), (25, False)])
def test_hours_alone_range(hours, ok):
    assert ("hours_alone" not in validate_answers(GOOD_ANSWERS | {"hours_alone": hours})[1]) is ok


def test_step_validation_only_checks_that_step():
    errors = validate_step(0, {"housing_level": 9})
    assert set(errors) == {"housing_level", "garden_access"}


def test_steps_cover_every_question_once():
    asked = [q for _, names in QUESTION_STEPS for q in names]
    assert sorted(asked) == sorted(GOOD_ANSWERS)
