# PawMatch rebuild: short write-up

The full coursework-style document is `PawMatch-NEA-opus.docx` (and `.pdf`) in this folder.
This file is the short engineering summary.

## 1. Analysis

The requirements come from the original analysis (client interview Q1-Q15, 27-response survey
S1-S8, competitor examples E1-E3). Her success-criteria table has nine numbered groups; each
row is numbered here in table order, so **5.2** is the second requirement of group 5.

| # | Measurable criterion |
|---|---|
| 1.1-1.4 | Calm theme with clear headings and buttons; readable at laptop (1280 px) and tablet (820 px) widths; one menu to Home, Animals, account/login; the same menu and theme on every page |
| 2.1-2.2 | Home states the purpose and the suitability focus; one button opens the questionnaire |
| 3.1-3.4 | Every animal shown as a card with species, name, breed, age and image; at least 3 species; each card opens the profile |
| 4.1-4.4 | Profile shows name, species, breed, age, sex, personality, medical needs, exercise and suitability, read from the database by id; a link back to the list or results |
| 5.1-5.5 | Register with name, email, age (18+) and password; reject blanks and bad emails; log in and out; staff log in to the staff page; wrong details give an error and no access |
| 6.1-6.4 | Questions cover home, garden, children, other pets, activity, hours alone and experience; asked in 4 steps plus a review; dropdowns only; a step with a blank answer cannot be passed and an incomplete set cannot be submitted |
| 7.1-7.6 | Every animal scored against the answers; a 0-100 % score; at least the top 4 shown best first; met and unmet lists; a warning for unmet important requirements; a note that staff decide |
| 8.1-8.5 | Staff page reached only through a staff login; add, edit and delete animals with validation; adopters cannot reach the page or call the actions |
| 9.1-9.4 | Users, animals, responses and results stored in SQLite; CRUD through the staff page; answers stored and used for scoring; retrieved data matches what was stored |

Two points the design left open are fixed here: login is by **email** (not username), and
passwords need **at least 8** characters.

## 2. Design

**Decomposition.** Two layers. `pawmatch/` is the domain and runs without Streamlit, so all of
it can be unit-tested. `webui/` draws pages and calls `pawmatch.services`.

```
streamlit_app.py ─▶ webui/views/*.py ─▶ webui/components.py, webui/state.py
                                 │
                                 ▼
                       pawmatch/services.py ─▶ auth.py ─▶ validation.py
                                 │                │
                                 ├─▶ matching.py ─┘ (uses models.py)
                                 └─▶ db.py ─▶ SQLite (users, animals,
                                              questionnaire_responses, match_results)
```

**Schema.** `users(user_id, name, email UNIQUE NOCASE, age ≥ 18, password_hash, role ∈
{user, admin}, created_at)`; `animals(animal_id, name, species ∈ {Dog, Cat, Rabbit}, breed,
age 1-30, sex, size, personality, exercise_needs 1-3, min_housing_level 1-3, garden_required
0/1, child_compatible 0/1, max_hours_alone 0-24, medical_notes, image_path, date_added)`;
`questionnaire_responses(response_id, user_id → users, housing_level, garden_access,
has_children, other_pets, experience, activity_level, hours_alone, preferred_species,
preferred_size, completed_at)`; `match_results(match_id, response_id → responses, animal_id →
animals ON DELETE CASCADE, rank, compatibility, category, bonus, met, unmet, warnings)`.
The CHECK constraints repeat the validation rules so bad data cannot get in by another route.

**Matching algorithm.** Weights are hers: hours alone 20, children 15, housing 15,
activity 12, garden 10 (72 in total); species 10 and size 5 only affect order.

```
FUNCTION score(animal, answers)
    earned ← 0
    hours    ← 1 IF answers.hours_alone ≤ animal.max_hours_alone ELSE 0
    children ← 1 IF animal.child_compatible OR NOT answers.has_children ELSE 0
    housing  ← 1 IF answers.housing_level ≥ animal.min_housing_level ELSE 0
    gap      ← MAX(0, animal.exercise_needs − answers.activity_level)
    activity ← MAX(0, 1 − gap / 2)                     // 1, 0.5 or 0
    garden   ← 1 IF answers.garden_access OR NOT animal.garden_required ELSE 0
    FOR EACH factor: earned ← earned + WEIGHT[factor] × fraction
        IF fraction = 1 THEN add reason to met ELSE add reason to unmet
        IF fraction < 1 AND factor IN {hours, children, housing} THEN add reason to warnings
    percent  ← ROUND(100 × earned / 72, 1)
    category ← Strong ≥ 80, Good ≥ 60, Possible ≥ 40, else Low
    bonus    ← 10 IF species = preferred species, + 5 IF size = preferred size
    RETURN percent, category, bonus, met, unmet, warnings

FUNCTION rank(animals, answers)
    results ← [score(a, answers) FOR a IN animals]
    SORT results BY (has warnings, −(percent + bonus), −percent, name, id)
    RETURN results                                     // page shows the first 5 (never fewer than 4)
```

**Validation table (main rules).**

| Field | Rules | Normal / boundary / erroneous |
|---|---|---|
| Name | presence, 2-50 chars, trimmed | "Sam Lee" / "Al", 50 chars / "A", "" |
| Email | presence, `x@y.tld`, lower-cased, unique | "sam@x.com" / "SAM@X.COM " / "no-at.com", duplicate |
| Age | whole number, 18-120 | 30 / 18, 120 / 17, 2.5, "abc" |
| Password | presence, ≥ 8 chars, matches confirmation | "longenough" / 8 chars / 7 chars, mismatch |
| Animal age | whole number 1-30 | 4 / 1, 30 / 0, 31 |
| Exercise, housing | 1-3 | 2 / 1, 3 / 0, 4 |
| Max hours alone | 0-24 | 4 / 0, 24 / −1, 25 |
| Questionnaire answers | one of the listed options; none blank | — / — / blank, out of list |
| Photo | png or jpg, ≤ 2 MB | a.png / exactly 2 MB / .gif, 2 MB + 1 byte |

**Test plan.** Unit tests for each pure module (validation, matching); repository tests on a
temporary SQLite file; service tests for access control; `AppTest` page tests; a headless
browser run for screenshots and the end-to-end flow.

## 3. Development

| Stage commit | What was built | Tests after |
|---|---|---|
| `ffd0ad5` stage 1 | `models.py`, `validation.py`, `matching.py` | 73 passed |
| `10e84e7` stage 2 | `db.py`, `auth.py`, `services.py`, `seed.py`, image thumbnails | 103 passed |
| `b76527c` stage 3 | `streamlit_app.py`, `webui/`, AppTest smoke tests, screenshot tool | 117 passed |
| stage 4 | README, this write-up, `compare.html`, screenshots | 117 passed |

Stage 1 core: preferences never change the percentage.

```python
compatibility = round(100 * earned / MAX_POINTS, 1)
return MatchResult(animal=animal, compatibility=compatibility, category=category_for(compatibility),
                   bonus=preference_bonus(animal, answers), met=met, unmet=unmet, warnings=warnings)
```

Stage 2 core: every staff action checks the role itself, not just the page.

```python
def remove_animal(conn, actor, animal_id):
    require_admin(actor)            # raises AccessDenied for adopters and anonymous users
    return db.delete_animal(conn, animal_id)
```

Stage 3 core: the staff page is only registered in the menu for staff, so its URL doesn't
exist for anyone else; the page also has its own guard.

Two real test failures happened in stage 3 and are kept in `docs/evidence/`:
the first AppTest run failed 9 of 9 because `AppTest.from_file` resolves relative paths from the
test file, not the working directory (fixed with an absolute path); later, merging error
messages into one box broke a test that counted two boxes (the test was updated to check one
box holding both messages).

## 4. Testing

```
$ .venv/bin/python -m pytest -q
........................................................................ [ 61%]
.............................................                            [100%]
117 passed in 4.90s
```

Cases per file: validation 48, matching 29, repository 12, auth 10, UI 10, admin access 8.

| Criterion | Evidence |
|---|---|
| 1.1-1.4 | `.streamlit/config.toml` theme; screenshots `docs/img/01`-`16`, incl. `16-tablet-browse.png` at 820 px |
| 2.1-2.2 | `test_home_page_explains_purpose`; `01-home.png` |
| 3.1-3.4 | `test_browse_shows_a_card_for_every_animal` (13 cards); `test_seed_has_three_species_and_is_idempotent`; `02`, `03` |
| 4.1-4.4 | `test_profile_reads_from_database`; `test_insert_then_get_round_trips_every_field`; `04-profile.png` |
| 5.1-5.5 | `test_auth.py` (10); `test_registration_*` in `test_validation.py`; `05`, `12` |
| 6.1-6.4 | `test_steps_cover_every_question_once`; `test_questionnaire_blocks_unanswered_step`; `test_unanswered_question_blocks_submission`; `06`-`09` |
| 7.1-7.6 | `test_matching.py` (29); `test_results_show_at_least_four_ranked_matches`; `10`, `11` |
| 8.1-8.5 | `test_admin_access.py` (8); `test_admin_page_is_not_routable_for_adopters`; `test_admin_page_guard_stops_adopters_even_if_reached_directly`; `13`-`15` |
| 9.1-9.4 | `test_repository.py` (12); `test_adopter_submission_stores_ranked_results` |

## 5. Evaluation

| Criterion | Result | Evidence and notes |
|---|---|---|
| 1.1, 1.3, 1.4 | Met | One theme file and one menu drawn by the entry script for every page |
| 1.2 | Met | Checked at 1280 px and 820 px (screenshots); not checked on a phone |
| 2.1, 2.2 | Met | Home text and button; AppTest |
| 3.1-3.4 | Met | 13 cards, three species, profile button on each |
| 4.1-4.4 | Met | Profile loaded by id from SQLite; back link returns to list or results |
| 5.1, 5.2, 5.5 | Met | Validation and auth tests; one generic message for wrong email or password |
| 5.3 | Met | Login/logout tests and screenshots. Limit: Streamlit keeps login in the browser session, so a full page reload logs the user out |
| 5.4, 8.1 | Met | Staff log in on the same form and get the staff page in the menu; staff accounts can only be made from the command line |
| 6.1-6.4 | Met | All seven topics asked; other pets and experience are stored but not scored, because the design gives them no weight |
| 7.1-7.6 | Met | Every animal scored; top 5 by default, "show every animal" toggle; warnings for hours, children and housing |
| 8.2-8.5 | Met | Service tests prove adopters are refused even if a page were bypassed |
| 9.1-9.4 | Met | Repository round-trip and ranking-reload tests |

**Limitations and next steps.** Session ends on page reload (persistent sign-in would need a
signed cookie); no password reset; no rate limit on login; animals have no "adopted" status, so
removing one deletes it and its stored results; species-specific factors (other pets,
experience) would need new animal fields before they could be scored.
