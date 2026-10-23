"""Access control: only staff can change animal records; users can still match."""

import pytest

from pawmatch import auth, db, services
from pawmatch.seed import create_admin, demo_animal_values, seed_animals

GOOD = demo_animal_values()[0]
GOOD_ANSWERS = {
    "housing_level": 2, "garden_access": "Yes", "has_children": "No", "other_pets": "No",
    "experience": "None", "activity_level": 2, "hours_alone": 4,
    "preferred_species": "No preference", "preferred_size": "No preference",
}


@pytest.fixture
def people(conn):
    create_admin(conn, "Staff", "staff@example.com", 40, "staffpass1")
    adopter, _ = auth.register(conn, "Sam", "sam@example.com", 30, "longenough", "longenough")
    staff, _ = auth.login(conn, "staff@example.com", "staffpass1")
    return staff, adopter


def test_admin_can_add_edit_and_delete(conn, people):
    staff, _ = people
    animal_id, errors = services.add_animal(conn, staff, GOOD)
    assert errors == {}
    assert services.edit_animal(conn, staff, animal_id, GOOD | {"name": "Renamed"}) == {}
    assert db.get_animal(conn, animal_id).name == "Renamed"
    assert services.remove_animal(conn, staff, animal_id)
    assert db.get_animal(conn, animal_id) is None


@pytest.mark.parametrize("actor", ["adopter", None])
def test_non_admins_are_refused_every_change(conn, people, actor):
    staff, adopter = people
    who = adopter if actor == "adopter" else None
    animal_id, _ = services.add_animal(conn, staff, GOOD)
    with pytest.raises(auth.AccessDenied):
        services.add_animal(conn, who, GOOD)
    with pytest.raises(auth.AccessDenied):
        services.edit_animal(conn, who, animal_id, GOOD | {"name": "Hacked"})
    with pytest.raises(auth.AccessDenied):
        services.remove_animal(conn, who, animal_id)
    assert db.get_animal(conn, animal_id).name == GOOD["name"]


def test_admin_add_still_validates(conn, people):
    staff, _ = people
    animal_id, errors = services.add_animal(conn, staff, GOOD | {"age": 0})
    assert animal_id is None and "age" in errors and db.count_animals(conn) == 0


def test_edit_of_deleted_animal_reports_error(conn, people):
    staff, _ = people
    assert "animal" in services.edit_animal(conn, staff, 404, GOOD)


def test_create_admin_promotes_an_existing_user(conn, people):
    assert create_admin(conn, "Sam", "sam@example.com", 30, "ignored1") == "promoted"
    assert auth.login(conn, "sam@example.com", "longenough")[0].is_admin


def test_adopter_submission_stores_ranked_results(conn, people):
    _, adopter = people
    seed_animals(conn)
    results, errors = services.submit_questionnaire(conn, adopter, GOOD_ANSWERS)
    assert errors == {} and len(results) == db.count_animals(conn) >= 4
    stored = services.latest_results(conn, adopter)
    assert [r.animal.animal_id for r in stored] == [r.animal.animal_id for r in results]
    scores = [r.ranking_points for r in results if r.suitable]
    assert scores == sorted(scores, reverse=True)


def test_incomplete_submission_saves_nothing(conn, people):
    _, adopter = people
    results, errors = services.submit_questionnaire(conn, adopter, GOOD_ANSWERS | {"hours_alone": ""})
    assert results == [] and "hours_alone" in errors
    assert services.latest_results(conn, adopter) is None
