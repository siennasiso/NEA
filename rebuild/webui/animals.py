"""How an animal's details read on the adopter pages (the original pawmatch_animals.format_age and profile lines)."""

from __future__ import annotations

from pawmatch.models import ACTIVITY_LEVELS, HOUSING_LEVELS, Animal


def format_age(age_years: int) -> str:
    """Show an animal age in years using the shortest clear label."""
    return f"{age_years} yr" if age_years == 1 else f"{age_years} yrs"


def needs_lines(animal: Animal) -> list[tuple[str, str]]:
    """What the animal needs from a home: the five requirements the matching checks."""
    return [
        ("Activity", ACTIVITY_LEVELS[animal.exercise_needs]),
        ("Home type", f"{HOUSING_LEVELS[animal.min_housing_level]} or more"),
        ("Garden", "Required" if animal.garden_required else "Not required"),
        ("Children", "Good with children" if animal.child_compatible else "Adult-only home"),
        ("Maximum time alone", f"{animal.max_hours_alone} hours"),
    ]
