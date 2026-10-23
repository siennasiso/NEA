"""The questionnaire as adopters see it: the original app's prompts and answer cards, one per screen.

The order follows the four sections in pawmatch.validation.QUESTION_STEPS, so the stepper
above each question shows which part of the questionnaire the adopter is in. Every value
here is checked again by the matching validator before anything is saved.
"""

from __future__ import annotations

from dataclasses import dataclass

from pawmatch.models import EXPERIENCE_LEVELS, NO_PREFERENCE
from pawmatch.validation import QUESTION_STEPS

Option = tuple[str, str, object]  # (label, hint, stored value)


@dataclass(frozen=True)
class Question:
    field: str
    prompt: str
    options: tuple[Option, ...] = ()  # empty for the one number question
    hint: str = ""
    multiple: bool = False  # several answers can be chosen (the allergies question)


YES_NO_GARDEN = (("Yes", "The animal can use a secure garden", True), ("No", "There is no private garden access", False))

QUESTIONS: tuple[Question, ...] = (
    Question("housing_level", "How much indoor space is available for the animal?", (
        ("Limited space", "One main room", 1),
        ("Moderate space", "Two or three rooms", 2),
        ("Plenty of space", "Most of the home", 3),
    )),
    Question("garden_access", "Do you have access to a garden?", YES_NO_GARDEN),
    Question("has_children", "Are there children living in your home?", (
        ("Yes", "One or more children live at home", True),
        ("No", "No children live at home", False),
    )),
    Question("other_pets", "Do any other pets live in your home?", (
        ("Yes", "Another animal already lives with you", True),
        ("No", "There are no other pets at home", False),
    )),
    Question("allergies", "Is anyone in your home allergic to any of these animals?", (
        ("No allergies", "Nobody at home has an animal allergy", ()),
        ("Dogs", "Someone at home is allergic to dogs", "Dog"),
        ("Cats", "Someone at home is allergic to cats", "Cat"),
        ("Rabbits", "Someone at home is allergic to rabbits", "Rabbit"),
    ), multiple=True),
    Question("activity_level", "What activity level can you support?", (
        ("Low", "Short, gentle daily activity", 1),
        ("Moderate", "Regular walks or active play", 2),
        ("High", "Long exercise and enrichment", 3),
    )),
    Question("hours_alone", "How many hours per day would the animal usually be left alone?",
             hint="Enter a whole number between 0 and 24 hours."),
    Question("experience", "How much experience do you have of caring for an animal?", (
        ("None", "This would be my first pet", EXPERIENCE_LEVELS[0]),
        ("Some", "A family pet while growing up", EXPERIENCE_LEVELS[1]),
        ("Experienced", "I have owned and cared for pets", EXPERIENCE_LEVELS[2]),
    )),
    Question("preferred_species", "Which species would you prefer?", (
        ("Dog", "A canine companion", "Dog"),
        ("Cat", "A feline companion", "Cat"),
        ("Rabbit", "A rabbit companion", "Rabbit"),
        (NO_PREFERENCE, "Show every species", NO_PREFERENCE),
    )),
    Question("preferred_size", "Which animal size would you prefer?", (
        ("Small", "A small animal", "Small"),
        ("Medium", "A medium-sized animal", "Medium"),
        ("Large", "A large animal", "Large"),
        (NO_PREFERENCE, "Show every size", NO_PREFERENCE),
    )),
)

SECTIONS: tuple[str, ...] = tuple(title for title, _ in QUESTION_STEPS)
SECTION_OF: dict[str, int] = {field: n for n, (_, fields) in enumerate(QUESTION_STEPS) for field in fields}


def label_for(question: Question, value: object) -> str:
    """The answer as the adopter chose it, for the summary on My account."""
    if not question.options:
        return f"{value} hours a day"
    if question.multiple and isinstance(value, tuple) and value:
        return ", ".join(label for label, _, stored in question.options if stored in value)
    return next((label for label, _, stored in question.options if stored == value), str(value))
