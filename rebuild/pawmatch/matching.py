"""Weighted compatibility scoring and ranking (criterion 7).

Normalisation, precisely:
  compatibility = round(100 * earned_points / 90, 1)
where 90 is the sum of the seven factor weights below. Each factor earns its
full weight when the requirement is met and 0 when it is not, except activity
and experience, which lose half their weight per level of shortfall.

An allergy is not weighed against the other answers. The client asked that an
animal someone at home is allergic to is never shown as a strong match, so it
adds a warning and caps the score at 39% (the Low band).

Species (10) and size (5) preferences never change the percentage. They are
added only to a separate ranking total, so a preferred but unsuitable animal
cannot show a misleadingly high score.
"""

from __future__ import annotations

from collections.abc import Iterable

from .models import EXPERIENCE_LEVELS, EXPERIENCE_NEEDED, HOUSING_LEVELS, NO_PREFERENCE, Animal, Answers, MatchResult

WEIGHTS: dict[str, int] = {
    "hours_alone": 20,
    "children": 15,
    "housing": 15,
    "activity": 12,
    "garden": 10,
    "other_pets": 10,
    "experience": 8,
}
MAX_POINTS = sum(WEIGHTS.values())  # 90
PREFERENCE_BONUS: dict[str, int] = {"species": 10, "size": 5}

# Unmet requirements on these factors are welfare risks, so they raise a warning.
IMPORTANT_FACTORS = frozenset({"hours_alone", "children", "housing", "other_pets"})
# The highest whole-number score in the Low band (Low is below 40).
ALLERGY_CAP = 39.0

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
    level = EXPERIENCE_LEVELS.index(answers.experience) if answers.experience in EXPERIENCE_LEVELS else 0
    experience_gap = max(0, animal.experience_needed - level)
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
        (
            "other_pets",
            1.0 if animal.good_with_pets or not answers.other_pets else 0.0,
            "Other pets: "
            + ("another pet lives with you and " if answers.other_pets else "no other pets live with you; ")
            + f"{animal.name} {'can' if animal.good_with_pets else 'cannot'} share a home with other animals.",
        ),
        (
            "experience",
            max(0.0, 1.0 - experience_gap / 2),
            f"Experience: you said '{answers.experience}'; "
            f"{animal.name} {EXPERIENCE_NEEDED[animal.experience_needed].lower()}.",
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
    if animal.species in answers.allergies:
        reason = (f"Allergy: someone in your home is allergic to {animal.species.lower()}s; "
                  f"{animal.name} is a {animal.species.lower()}.")
        unmet.insert(0, reason)
        warnings.insert(0, reason)
        compatibility = min(compatibility, ALLERGY_CAP)
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
