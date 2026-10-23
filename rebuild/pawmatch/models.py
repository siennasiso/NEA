"""Domain records and the fixed option lists shared by every layer."""

from __future__ import annotations

from dataclasses import dataclass, field

SPECIES: tuple[str, ...] = ("Dog", "Cat", "Rabbit")
SIZES: tuple[str, ...] = ("Small", "Medium", "Large")
SEXES: tuple[str, ...] = ("Male", "Female", "Unknown")
ROLES: tuple[str, ...] = ("user", "admin")
NO_PREFERENCE = "No preference"

# Ordinal scales: the stored integer is the level, the label is what users see.
HOUSING_LEVELS: dict[int, str] = {
    1: "Flat or limited space",
    2: "Small or medium house",
    3: "Large house",
}
ACTIVITY_LEVELS: dict[int, str] = {
    1: "Low - short walks or indoor play",
    2: "Medium - about an hour of activity a day",
    3: "High - long walks, running or training every day",
}
EXPERIENCE_LEVELS: tuple[str, ...] = (
    "None",
    "Some (family pet growing up)",
    "Experienced owner",
)


@dataclass(frozen=True)
class User:
    """A registered account. The password hash never leaves the repository layer."""

    user_id: int
    name: str
    email: str
    age: int
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


@dataclass(frozen=True)
class Animal:
    """One animal in the shelter, including the requirements used for matching."""

    animal_id: int
    name: str
    species: str
    breed: str
    age: int
    sex: str
    size: str
    personality: str
    exercise_needs: int
    min_housing_level: int
    garden_required: bool
    child_compatible: bool
    max_hours_alone: int
    medical_notes: str = ""
    image_path: str = ""


@dataclass(frozen=True)
class Answers:
    """A validated questionnaire response."""

    housing_level: int
    garden_access: bool
    has_children: bool
    other_pets: bool
    experience: str
    activity_level: int
    hours_alone: int
    preferred_species: str
    preferred_size: str


@dataclass(frozen=True)
class MatchResult:
    """The score for one animal against one set of answers."""

    animal: Animal
    compatibility: float
    category: str
    bonus: int
    met: list[str] = field(default_factory=list)
    unmet: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ranking_points(self) -> float:
        """Compatibility plus the preference bonus; used for ordering only."""
        return self.compatibility + self.bonus

    @property
    def suitable(self) -> bool:
        """True when no important (welfare) requirement is unmet."""
        return not self.warnings
