"""Weighted compatibility scoring and ranking (criterion 7).

Normalisation, precisely:
  compatibility = round(100 * earned_points / 72, 1)
where 72 is the sum of the five welfare weights below. Each factor earns its
full weight when the requirement is met and 0 when it is not, except activity,
which loses half its weight per level of shortfall (12, 6, then 0).

Species (10) and size (5) preferences never change the percentage. They are
added only to a separate ranking total, so a preferred but unsuitable animal
cannot show a misleadingly high score.
"""

from __future__ import annotations

from collections.abc import Iterable

from .models import HOUSING_LEVELS, NO_PREFERENCE, Animal, Answers, MatchResult

WEIGHTS: dict[str, int] = {
    "hours_alone": 20,
    "children": 15,
    "housing": 15,
    "activity": 12,
    "garden": 10,
}
MAX_POINTS = sum(WEIGHTS.values())  # 72
PREFERENCE_BONUS: dict[str, int] = {"species": 10, "size": 5}

# Unmet requirements on these factors are welfare risks, so they raise a warning.
IMPORTANT_FACTORS = frozenset({"hours_alone", "children", "housing"})

CATEGORY_THRESHOLDS: tuple[tuple[float, str], ...] = (
    (80.0, "Strong"),
    (60.0, "Good"),
    (40.0, "Possible"),
    (0.0, "Low"),
)
MIN_RESULTS_SHOWN = 4


def category_for(compatibility: float) -> str:
    """Map a 0-100 percentage to its label."""
    for threshold, label in CATEGORY_THRESHOLDS:
        if compatibility >= threshold:
            return label
    return "Low"


def _factor_checks(animal: Animal, answers: Answers) -> list[tuple[str, float, str]]:
    """Return (factor, fraction of weight earned, explanation) for each welfare factor."""
    activity_gap = max(0, animal.exercise_needs - answers.activity_level)
    return [
        (
            "hours_alone",
            1.0 if answers.hours_alone <= animal.max_hours_alone else 0.0,
            f"Time alone: you said {answers.hours_alone} h a day; "
            f"{animal.name} can be left for up to {animal.max_hours_alone} h.",
        ),
        (
            "children",
            1.0 if animal.child_compatible or not answers.has_children else 0.0,
            "Children: "
            + ("there are children in your home and " if answers.has_children else "no children in your home; ")
            + f"{animal.name} is {'' if animal.child_compatible else 'not '}suitable for homes with children.",
        ),
        (
            "housing",
            1.0 if answers.housing_level >= animal.min_housing_level else 0.0,
            f"Space: you have '{HOUSING_LEVELS[answers.housing_level]}'; "
            f"{animal.name} needs at least '{HOUSING_LEVELS[animal.min_housing_level]}'.",
        ),
        (
            "activity",
            max(0.0, 1.0 - activity_gap / 2),
            f"Activity: you can offer level {answers.activity_level} of 3; "
            f"{animal.name} needs level {animal.exercise_needs} of 3.",
        ),
        (
            "garden",
            1.0 if answers.garden_access or not animal.garden_required else 0.0,
            f"Garden: {animal.name} {'needs' if animal.garden_required else 'does not need'} a garden; "
            f"you {'have' if answers.garden_access else 'do not have'} one.",
        ),
    ]


def preference_bonus(animal: Animal, answers: Answers) -> int:
    """Ranking-only bonus for the preferred species and size ('No preference' scores 0)."""
    bonus = 0
    if answers.preferred_species not in (NO_PREFERENCE, "") and animal.species == answers.preferred_species:
        bonus += PREFERENCE_BONUS["species"]
    if answers.preferred_size not in (NO_PREFERENCE, "") and animal.size == answers.preferred_size:
        bonus += PREFERENCE_BONUS["size"]
    return bonus


def score_animal(animal: Animal, answers: Answers) -> MatchResult:
    """Score one animal: percentage, category, met/unmet lists and warnings."""
    earned = 0.0
    met: list[str] = []
    unmet: list[str] = []
    warnings: list[str] = []
    for factor, fraction, reason in _factor_checks(animal, answers):
        earned += WEIGHTS[factor] * fraction
        if fraction == 1.0:
            met.append(reason)
        else:
            unmet.append(reason)
            if factor in IMPORTANT_FACTORS:
                warnings.append(reason)
    compatibility = round(100 * earned / MAX_POINTS, 1)
    return MatchResult(
        animal=animal,
        compatibility=compatibility,
        category=category_for(compatibility),
        bonus=preference_bonus(animal, answers),
        met=met,
        unmet=unmet,
        warnings=warnings,
    )


def rank_key(result: MatchResult) -> tuple[int, float, float, str, int]:
    """Suitable animals first, then ranking points, compatibility, name and id (all deterministic)."""
    return (
        0 if result.suitable else 1,
        -result.ranking_points,
        -result.compatibility,
        result.animal.name.lower(),
        result.animal.animal_id,
    )


def rank_animals(animals: Iterable[Animal], answers: Answers) -> list[MatchResult]:
    """Score every animal and return them best first."""
    return sorted((score_animal(a, answers) for a in animals), key=rank_key)
