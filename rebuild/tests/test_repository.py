"""Repository: CRUD round-trips, filters, constraints and SQL safety on a temp database."""

import sqlite3

import pytest

from pawmatch import db
from pawmatch.matching import rank_animals
from pawmatch.models import Answers
from pawmatch.seed import DEMO_ANIMALS, demo_animal_values, seed_animals
from pawmatch.validation import validate_animal

ANSWERS = Answers(2, True, False, False, "None", 2, 4, "No preference", "No preference")


def first_values():
    return validate_animal(demo_animal_values()[0])[0]


def test_schema_creates_four_tables(conn):
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"users", "animals", "questionnaire_responses", "match_results"} <= names


def test_insert_then_get_round_trips_every_field(conn):
    values = first_values()
    animal = db.get_animal(conn, db.insert_animal(conn, values))
    for field, value in values.items():
        assert getattr(animal, field) == value


def test_update_changes_the_stored_record(conn):
    animal_id = db.insert_animal(conn, first_values())
    assert db.update_animal(conn, animal_id, first_values() | {"name": "Lunar", "max_hours_alone": 6})
    updated = db.get_animal(conn, animal_id)
    assert (updated.name, updated.max_hours_alone) == ("Lunar", 6)


def test_update_and_delete_report_missing_rows(conn):
    assert not db.update_animal(conn, 999, first_values())
    assert not db.delete_animal(conn, 999)


def test_delete_removes_animal_and_its_stored_results(conn):
    user = db.insert_user(conn, "Sam", "sam@example.com", 30, "x")
    animal_id = db.insert_animal(conn, first_values())
    response_id = db.save_response(conn, user.user_id, ANSWERS)
    db.save_results(conn, response_id, rank_animals(db.list_animals(conn), ANSWERS))
    assert db.delete_animal(conn, animal_id)
    assert db.get_animal(conn, animal_id) is None
    assert db.load_results(conn, response_id) == []


def test_seed_has_three_species_and_is_idempotent(conn):
    assert seed_animals(conn) == len(DEMO_ANIMALS)
    assert seed_animals(conn) == 0
    assert {a.species for a in db.list_animals(conn)} == {"Dog", "Cat", "Rabbit"}


def test_filters_by_species_size_and_search(conn):
    seed_animals(conn)
    assert {a.species for a in db.list_animals(conn, species="Cat")} == {"Cat"}
    assert all(a.size == "Small" for a in db.list_animals(conn, size="Small"))
    assert [a.name for a in db.list_animals(conn, search="spaniel")] == ["Archie"]


def test_search_text_is_treated_as_data_not_sql(conn):
    seed_animals(conn)
    assert db.list_animals(conn, search="' OR 1=1 --") == []
    assert db.count_animals(conn) == len(DEMO_ANIMALS)


def test_database_constraints_back_up_validation(conn):
    with pytest.raises(sqlite3.IntegrityError):
        db.insert_animal(conn, first_values() | {"species": "Hamster"})
    with pytest.raises(sqlite3.IntegrityError):
        db.insert_user(conn, "Kid", "kid@example.com", 12, "x")


def test_responses_and_results_are_stored_and_reloaded_in_rank_order(conn):
    seed_animals(conn)
    user = db.insert_user(conn, "Sam", "sam@example.com", 30, "x")
    response_id = db.save_response(conn, user.user_id, ANSWERS)
    ranked = rank_animals(db.list_animals(conn), ANSWERS)
    db.save_results(conn, response_id, ranked)
    assert db.latest_response(conn, user.user_id) == (response_id, ANSWERS)
    reloaded = db.load_results(conn, response_id)
    assert [r.animal.animal_id for r in reloaded] == [r.animal.animal_id for r in ranked]
    assert reloaded[0].met == ranked[0].met and reloaded[-1].warnings == ranked[-1].warnings


def test_latest_response_is_none_for_new_user(conn):
    user = db.insert_user(conn, "New", "new@example.com", 30, "x")
    assert db.latest_response(conn, user.user_id) is None


def test_connect_rolls_back_on_error(tmp_path):
    path = tmp_path / "rollback.db"
    with db.connect(path) as conn:
        db.init_schema(conn)
    with pytest.raises(RuntimeError), db.connect(path) as conn:
        db.insert_user(conn, "Sam", "sam@example.com", 30, "x")
        raise RuntimeError("boom")
    with db.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0


def test_saved_results_record_when_they_were_calculated(conn):
    """Design, Match Results table: calculated_at is required."""
    seed_animals(conn)
    user_id = conn.execute(
        "INSERT INTO users (name, email, age, password_hash, created_at) VALUES ('Sam', 's@x.com', 30, 'h', '2026-10-23')"
    ).lastrowid
    response_id = db.save_response(conn, user_id, ANSWERS)
    db.save_results(conn, response_id, rank_animals(db.list_animals(conn), ANSWERS))
    stamps = {r[0] for r in conn.execute("SELECT calculated_at FROM match_results")}
    assert len(stamps) == 1 and stamps.pop()[:4].isdigit()


def test_old_database_gains_calculated_at_column(tmp_path):
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.executescript(db.SCHEMA.replace(",\n    calculated_at TEXT    NOT NULL DEFAULT ''", ""))  # schema before stage 5
    old.close()
    with db.connect(str(path)) as conn:
        db.init_schema(conn)
        columns = {r[1] for r in conn.execute("PRAGMA table_info(match_results)")}
    assert "calculated_at" in columns
