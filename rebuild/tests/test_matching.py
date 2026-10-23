"""Matching: each weight, the normalisation, warnings, bonuses and ordering."""

import pytest

from pawmatch.matching import MAX_POINTS, WEIGHTS, category_for, rank_animals, score_animal


def test_weights_match_the_design():
    assert WEIGHTS == {"hours_alone": 20, "children": 15, "housing": 15, "activity": 12, "garden": 10,
                       "other_pets": 10, "experience": 8}
    assert MAX_POINTS == 90


def test_perfect_match_scores_100(animal, answers):
    result = score_animal(animal(), answers())
    assert result.compatibility == 100.0
    assert result.category == "Strong"
    assert result.unmet == [] and result.warnings == [] and len(result.met) == 7


@pytest.mark.parametrize("animal_changes,answer_changes,lost", [
    ({"max_hours_alone": 3}, {}, 20),
    ({"child_compatible": False}, {"has_children": True}, 15),
    ({"min_housing_level": 3}, {}, 15),
    ({"exercise_needs": 3}, {}, 6),
    ({"exercise_needs": 3}, {"activity_level": 1}, 12),
    ({}, {"garden_access": False}, 10),
    ({"good_with_pets": False}, {"other_pets": True}, 10),
    ({"experience_needed": 1}, {}, 4),
    ({"experience_needed": 2}, {}, 8),
    ({"experience_needed": 2}, {"experience": "Some (family pet growing up)"}, 4),
])
def test_each_factor_loses_its_weight(animal, answers, animal_changes, answer_changes, lost):
    result = score_animal(animal(**animal_changes), answers(**answer_changes))
    assert result.compatibility == round(100 * (90 - lost) / 90, 1)
    assert len(result.unmet) == 1


def test_boundaries_count_as_met(animal, answers):
    # Exactly the maximum hours and exactly the minimum housing level both meet the requirement.
    result = score_animal(animal(max_hours_alone=4, min_housing_level=2), answers(hours_alone=4, housing_level=2))
    assert result.compatibility == 100.0


def test_more_activity_than_needed_is_not_penalised(animal, answers):
    assert score_animal(animal(exercise_needs=1), answers(activity_level=3)).compatibility == 100.0


def test_children_rule_only_applies_when_there_are_children(animal, answers):
    assert score_animal(animal(child_compatible=False), answers(has_children=False)).compatibility == 100.0


def test_important_unmet_requirements_raise_warnings(animal, answers):
    result = score_animal(animal(max_hours_alone=2, child_compatible=False), answers(has_children=True))
    assert len(result.warnings) == 2
    assert not result.suitable


def test_garden_and_activity_shortfalls_do_not_warn(animal, answers):
    result = score_animal(animal(exercise_needs=3), answers(garden_access=False))
    assert result.warnings == [] and len(result.unmet) == 2 and result.suitable


def test_everything_unmet_scores_zero(animal, answers):
    result = score_animal(
        animal(max_hours_alone=0, child_compatible=False, min_housing_level=3, exercise_needs=3,
               good_with_pets=False, experience_needed=2),
        answers(hours_alone=8, has_children=True, housing_level=1, activity_level=1, garden_access=False,
                other_pets=True),
    )
    assert result.compatibility == 0.0 and result.category == "Low" and len(result.unmet) == 7


# Stage 9: other pets, experience and allergies (the factors the client interview asked for)

def test_an_animal_that_cannot_live_with_pets_warns_only_when_there_is_another_pet(animal, answers):
    with_pet = score_animal(animal(good_with_pets=False), answers(other_pets=True))
    assert with_pet.warnings and with_pet.warnings[0].startswith("Other pets") and not with_pet.suitable
    assert score_animal(animal(good_with_pets=False), answers(other_pets=False)).compatibility == 100.0


def test_too_little_experience_lowers_the_score_without_a_warning(animal, answers):
    result = score_animal(animal(experience_needed=2), answers(experience="None"))
    assert result.compatibility == round(100 * 82 / 90, 1) and result.warnings == [] and result.suitable


def test_more_experience_than_needed_is_not_penalised(animal, answers):
    assert score_animal(animal(experience_needed=1), answers(experience="Experienced owner")).compatibility == 100.0


def test_an_allergy_caps_the_score_in_the_low_band_and_warns_first(animal, answers):
    result = score_animal(animal(species="Cat"), answers(allergies=("Cat",)))
    assert result.compatibility == 39.0 and result.category == "Low" and not result.suitable
    assert result.warnings[0].startswith("Allergy") and result.unmet[0] == result.warnings[0]


def test_an_allergy_to_another_species_changes_nothing(animal, answers):
    assert score_animal(animal(species="Dog"), answers(allergies=("Cat", "Rabbit"))).compatibility == 100.0


def test_an_allergy_never_raises_a_score_that_is_already_lower(animal, answers):
    # Hours alone, children, housing and garden all unmet: 30 of 90 points, 33.3%, below the cap.
    result = score_animal(animal(max_hours_alone=0, child_compatible=False, min_housing_level=3),
                          answers(hours_alone=8, has_children=True, housing_level=1, garden_access=False,
                                  allergies=("Dog",)))
    assert result.compatibility == round(100 * 30 / 90, 1) == 33.3


def test_an_allergic_home_ranks_the_animal_below_every_suitable_one(animal, answers):
    ranked = rank_animals([animal(animal_id=1, name="Tom", species="Cat"),
                           animal(animal_id=2, name="Rex", species="Dog", exercise_needs=3)],
                          answers(allergies=("Cat",), preferred_species="Cat"))
    assert [r.animal.name for r in ranked] == ["Rex", "Tom"]


@pytest.mark.parametrize("score,label", [(100, "Strong"), (80, "Strong"), (79.9, "Good"), (60, "Good"),
                                         (59.9, "Possible"), (40, "Possible"), (39.9, "Low"), (0, "Low")])
def test_category_thresholds(score, label):
    assert category_for(score) == label


def test_preferences_change_rank_but_not_percentage(animal, answers):
    result = score_animal(animal(species="Cat", size="Small"), answers(preferred_species="Cat", preferred_size="Small"))
    assert result.compatibility == 100.0
    assert result.bonus == 15 and result.ranking_points == 115.0


def test_no_preference_gives_no_bonus(animal, answers):
    assert score_animal(animal(), answers()).bonus == 0


def test_ranking_orders_by_points_then_name(animal, answers):
    pool = [
        animal(animal_id=1, name="Bravo"),                      # 100
        animal(animal_id=2, name="Alpha"),                      # 100, earlier name
        animal(animal_id=3, name="Garden", garden_required=True),  # 100
        animal(animal_id=4, name="Lazy", exercise_needs=3),     # 91.7
    ]
    ranked = rank_animals(pool, answers())
    assert [r.animal.name for r in ranked] == ["Alpha", "Bravo", "Garden", "Lazy"]


def test_preferred_species_moves_up_among_suitable(animal, answers):
    pool = [animal(animal_id=1, name="Dog"), animal(animal_id=2, name="Cat", species="Cat", exercise_needs=3)]
    ranked = rank_animals(pool, answers(preferred_species="Cat"))
    # 91.7 + 10 beats 100 + 0
    assert [r.animal.name for r in ranked] == ["Cat", "Dog"]


def test_unsuitable_animals_always_rank_after_suitable(animal, answers):
    pool = [
        animal(animal_id=1, name="Risky", species="Cat", max_hours_alone=1),  # 72.2 but preferred
        animal(animal_id=2, name="Safe", exercise_needs=3, garden_required=True),  # 91.7
    ]
    ranked = rank_animals(pool, answers(preferred_species="Cat", hours_alone=4))
    assert [r.animal.name for r in ranked] == ["Safe", "Risky"]


def test_ranking_empty_list(answers):
    assert rank_animals([], answers()) == []


def test_ranking_is_deterministic_for_identical_animals(animal, answers):
    pool = [animal(animal_id=i, name="Twin") for i in (3, 1, 2)]
    assert [r.animal.animal_id for r in rank_animals(pool, answers())] == [1, 2, 3]
