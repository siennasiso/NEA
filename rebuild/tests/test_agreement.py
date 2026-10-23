"""Fixed-profile agreement test and weight sensitivity (evaluation, section 4.1).

Ten adopter profiles. For each, the animals a person applying the rescue's welfare rules would
certainly put in the top three ("include") and the animals that must never be in it ("exclude")
were written by hand from the demo animals' profiles before running the program.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace

import pytest

from pawmatch import matching
from pawmatch.models import Animal, Answers
from pawmatch.seed import demo_animal_values

DOGS = ["Luna", "Archie", "Nala", "Oscar"]
CATS = ["Milo", "Simba", "Willow"]
RABBITS = ["Poppy", "Teddy", "Daisy", "Clover"]
BASE = Answers(housing_level=2, garden_access=True, has_children=False, other_pets=False,
               experience="Some (family pet growing up)", activity_level=2, hours_alone=4,
               preferred_species="No preference", preferred_size="No preference")

# id, who, answer changes, include, exclude
PROFILES = [
    ("A1", "Flat, out 8 h a day, first pet, low activity",
     dict(housing_level=1, garden_access=False, experience="None", activity_level=1, hours_alone=8),
     ["Milo", "Poppy"], DOGS),
    ("A2", "Family house with garden, wants a dog",
     dict(housing_level=3, has_children=True, activity_level=3, hours_alone=3, preferred_species="Dog"),
     ["Luna", "Archie"], ["Nala", "Simba", "Teddy"]),
    ("A3", "Same family, allergic to dogs, wants a rabbit",
     dict(housing_level=3, has_children=True, activity_level=3, hours_alone=3, preferred_species="Rabbit",
          allergies=("Dog",)),
     ["Daisy", "Clover"], DOGS + ["Teddy"]),
    ("A4", "Older experienced owner, flat, out 10 h, likes cats",
     dict(housing_level=1, garden_access=False, experience="Experienced owner", activity_level=1,
          hours_alone=10, preferred_species="Cat"),
     ["Willow"], DOGS),
    ("A5", "Already has a pet, wants a second dog",
     dict(other_pets=True, preferred_species="Dog"),
     ["Archie", "Oscar"], ["Nala", "Simba", "Teddy"]),
    ("A6", "First-time owner, out 6 h, wants a rabbit",
     dict(experience="None", activity_level=3, hours_alone=6, preferred_species="Rabbit"),
     ["Daisy", "Poppy"], ["Luna", "Nala"]),
    ("A7", "Experienced runner, large house, wants a large dog",
     dict(housing_level=3, experience="Experienced owner", activity_level=3, hours_alone=3,
          preferred_species="Dog", preferred_size="Large"),
     ["Luna"], RABBITS),
    ("A8", "Flat with children and a cat, out 5 h",
     dict(housing_level=1, garden_access=False, has_children=True, other_pets=True, hours_alone=5),
     ["Milo", "Poppy", "Willow"], ["Teddy", "Simba", "Nala"]),
    ("A9", "Allergic to cats and rabbits, house with garden",
     dict(allergies=("Cat", "Rabbit")),
     ["Archie", "Oscar"], CATS + RABBITS),
    ("A10", "Out 12 h with children and a pet: nothing is safe",
     dict(housing_level=1, garden_access=False, has_children=True, other_pets=True, hours_alone=12),
     [], []),
]


def available_animals() -> list[Animal]:
    rows = [v for v in demo_animal_values() if v["status"] == "Available"]
    return [Animal(animal_id=i, **{k: v for k, v in row.items() if k in Animal.__dataclass_fields__})
            for i, row in enumerate(rows, 1)]


def top_three(answers: Answers) -> list[matching.MatchResult]:
    return matching.rank_animals(available_animals(), answers)[:3]


@contextmanager
def weights(changes: dict[str, float]):
    """Temporarily change the factor weights (used only by the sensitivity check)."""
    saved = dict(matching.WEIGHTS), matching.MAX_POINTS
    matching.WEIGHTS.update(changes)
    matching.MAX_POINTS = sum(matching.WEIGHTS.values())
    try:
        yield
    finally:
        matching.WEIGHTS.clear()
        matching.WEIGHTS.update(saved[0])
        matching.MAX_POINTS = saved[1]


def sensitivity() -> list[dict]:
    """For each weight at -10% and +10%, which profiles' top-three set changes."""
    base = {p[0]: {r.animal.name for r in top_three(replace(BASE, **p[2]))} for p in PROFILES}
    rows = []
    for factor, weight in list(matching.WEIGHTS.items()):
        for step in (-0.1, 0.1):
            with weights({factor: weight * (1 + step)}):
                changed = [p[0] for p in PROFILES
                           if {r.animal.name for r in top_three(replace(BASE, **p[2]))} != base[p[0]]]
            rows.append({"factor": factor, "weight": weight, "change": f"{step:+.0%}", "changed": changed})
    return rows


@pytest.mark.parametrize("pid, who, changes, include, exclude", PROFILES, ids=[p[0] for p in PROFILES])
def test_top_three_agrees_with_the_hand_expectation(pid, who, changes, include, exclude):
    names = [r.animal.name for r in top_three(replace(BASE, **changes))]
    assert set(include) <= set(names), names
    assert not set(exclude) & set(names), names


def test_no_animal_is_called_suitable_when_none_is_safe():
    pid, who, changes, *_ = PROFILES[-1]
    assert all(not r.suitable for r in top_three(replace(BASE, **changes)))


def test_ten_percent_weight_changes_do_not_change_any_top_three():
    assert all(not row["changed"] for row in sensitivity()), [r for r in sensitivity() if r["changed"]]


def test_weights_are_restored_after_the_sensitivity_check():
    sensitivity()
    assert matching.WEIGHTS["hours_alone"] == 20 and matching.MAX_POINTS == 90
