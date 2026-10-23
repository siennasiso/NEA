"""Shared builders so each test states only the fields it cares about."""

from __future__ import annotations

from dataclasses import replace

import pytest

from pawmatch.models import Animal, Answers

BASE_ANIMAL = Animal(
    animal_id=1, name="Rex", species="Dog", breed="Mixed", age=3, sex="Male", size="Medium",
    personality="Friendly", exercise_needs=2, min_housing_level=2, garden_required=True,
    child_compatible=True, max_hours_alone=4,
)
BASE_ANSWERS = Answers(
    housing_level=2, garden_access=True, has_children=False, other_pets=False,
    experience="None", activity_level=2, hours_alone=4,
    preferred_species="No preference", preferred_size="No preference",
)


@pytest.fixture
def animal():
    return lambda **changes: replace(BASE_ANIMAL, **changes)


@pytest.fixture
def answers():
    return lambda **changes: replace(BASE_ANSWERS, **changes)
