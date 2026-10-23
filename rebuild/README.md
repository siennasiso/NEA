# PawMatch (rebuild)

A clean rebuild of PawMatch, an adoption-matching app for one animal shelter. Adopters
register, browse dogs, cats and rabbits, answer a step-by-step questionnaire and get a ranked
list of animals with a compatibility score, what they meet and don't meet, and warnings.
Shelter staff log in to a separate page to add, edit and delete animals.

It is built from the analysis and design in `../documents/` as a teaching comparison with the
original app in `../app/`. Nothing in `../app/` is changed.

## Run it

```sh
cd rebuild
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pawmatch.seed --admin staff@yourshelter.org   # asks for a staff password
.venv/bin/streamlit run streamlit_app.py
```

The database is `data/pawmatch.db` (override with `PAWMATCH_DB`). It is created and seeded
with 13 demo animals on first start. Adopters register in the app; staff accounts are only
made with the command above, so nobody can sign up as staff.

## Test it

```sh
.venv/bin/python -m pytest -q
```

134 tests: validation, auth, the repository (on a temporary database), matching, staff-only
access, and headless page checks with Streamlit's `AppTest`.
`docs/tools/capture_screens.py` runs the app headless and saves screenshots with Playwright.

## Structure

```
streamlit_app.py        entry: prepares the database, role-aware top menu, runs the page
pawmatch/               domain layer: pure Python, never imports Streamlit
  models.py             dataclasses (User, Animal, Answers, MatchResult) and option lists
  validation.py         every form's rules; returns (cleaned values, errors by field)
  auth.py               scrypt hashing, register, login, require_admin
  matching.py           weights, normalisation, warnings and ranking
  db.py                 SQLite schema and parameterised queries
  services.py           use cases the pages call (validate -> check role -> store)
  seed.py               demo animals and the staff-account command
webui/                  presentation layer
  state.py              session, database handle, page guards
  components.py         animal card, match card, error box
  views/*.py            one short file per page
tests/                  pytest suite
docs/                   WRITEUP.md, compare.html, the NEA write-up, screenshots and evidence
```
