# PawMatch (rebuild)

PawMatch helps one animal shelter match adopters with dogs, cats and rabbits. Adopters
register, browse the animals, answer a nine-question lifestyle questionnaire and get a ranked
list. Each animal shows a compatibility score, the requirements the adopter meets and does not
meet, and any welfare warnings. Shelter staff sign in to a separate dashboard to add, edit and
delete animal records.

This rebuild keeps the original app's look: her pink style file and her eight pages, ported
from `../app/`. Underneath is a tested Python engine, `pawmatch/`. Nothing in `../app/` is changed.

Everything is hand-written Python, using Streamlit for the pages and SQLite for the data. CSS
only styles the pages: every rule, check and calculation is in Python.

## Run it

```sh
cd rebuild
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run streamlit_app.py
```

On first start the app creates the database and fills it with 13 demo animals. Open
http://localhost:8501, choose **Create an account**, and you are signed in as an adopter.

### Settings

| Variable | What it does | Default |
|---|---|---|
| `PAWMATCH_DB` | Path of the SQLite database file | `data/pawmatch.db` |
| `PAWMATCH_ADMIN_EMAIL` | The first-start staff account's email | none |
| `PAWMATCH_ADMIN_PASSWORD` | The password for that account (8 characters or more) | none |
| `PAWMATCH_ADMIN_NAME` | The name shown on the staff dashboard | `Shelter staff` |

Staff accounts can't be created from the registration page, so nobody can sign themselves up as
staff. A shelter has two ways to make one:

```sh
# on a server: set the variables, and the account is made on first start
PAWMATCH_ADMIN_EMAIL=manager@your-shelter.example PAWMATCH_ADMIN_PASSWORD='<choose one>' \
    .venv/bin/streamlit run streamlit_app.py

# on your own machine: run this command, which asks for the password
.venv/bin/python -m pawmatch.seed --admin manager@your-shelter.example
```

### Sign in with Google (optional)

The usual email and password sign-in always works. A **Continue with Google** button is added
only when the settings below exist in `.streamlit/secrets.toml`. Git ignores that file, so keep
your real values there and nowhere else.

```toml
[auth]
redirect_uri = "http://localhost:8501/oauth2callback"
cookie_secret = "<a long random string>"
client_id = "<your OAuth client id>"
client_secret = "<your OAuth client secret>"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

You get the client ID and secret by creating an OAuth web client in Google Cloud. Its
authorised redirect URI must be the same as `redirect_uri` above.

Clerk works too: put Clerk's OpenID discovery address in `server_metadata_url`. This uses
Streamlit's own `st.login`, which needs Authlib (already in `requirements.txt`).

A Google sign-in opens the adopter account that has the same verified email address. If there
is no such account, PawMatch makes one after asking for the person's name and age. Staff
accounts never sign in this way: staff always use their PawMatch email and password.

## Test it

```sh
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m playwright install chromium                   # once, for the screenshots
.venv/bin/python docs/tools/capture_screens.py docs/img            # desktop and tablet screenshots
```

The tests cover:

- validation, sign-in and the password rules
- the database layer, on a temporary database
- matching and ranking
- staff-only access
- page checks run headless with Streamlit's `AppTest`
- the style file's contrast and text-size rules (`tests/test_style.py`)

The capture script uses a fresh temporary database and goes through the real pages as an
adopter, then as staff. It also checks every page as drawn in the browser:

- text contrast
- text size
- hover and focus states
- the keyboard tab order

The results go to `docs/evidence/rendered-audit-<size>.json`.

## Accessibility changes made after testing

Her design is unchanged except where a test showed it was hard to read or use:

- **Deeper pinks.** White labels and small pink text now use two deeper pinks from her own
  file (`#c23673`, `#a92660`), so every text colour reaches 4.5:1.
- **Text size.** No text is smaller than 12px.
- **Login and registration panels.** The text is full white, and the ticks are outlined
  instead of filled.
- **Side menu.** Its text is darkened to suit the menu's pink background.
- **Keyboard focus.** The **Log in | Create an account** switch shows a clear ring when a
  keyboard user moves onto it.
- **Hover and focus.** Streamlit gives a hovered or focused button a pale pink fill, which made
  the white "View profile" labels vanish (1.2:1). Those states now keep a deep pink.
- **Upload hint.** The photo uploader's hint uses the body text colour instead of a faded grey.

The browser check (`docs/tools/capture_screens.py`) now finds no problems on any page: 552 text items
and 176 buttons and links, checked at rest, hovered and focused.

`docs/evidence/style-test-before.txt` records the test failing on the original colours.

## Structure

```
streamlit_app.py        entry point: prepares the database, registers the pages, runs one
pawmatch/               the engine: pure Python, never imports Streamlit
  models.py             dataclasses (User, Animal, Answers, MatchResult) and option lists
  validation.py         every form's rules; returns (cleaned values, errors by field)
  auth.py               scrypt password hashing, register, login, Google accounts, require_admin
  matching.py           weights, normalisation, welfare warnings and ranking
  db.py                 SQLite schema and parameterised queries
  services.py           what the pages call (validate, check the role, store)
  seed.py               demo animals, the staff-account command and first-start setup
webui/                  the pages: her app/pawmatch_style.py and app/pages/*.py, ported
  pawmatch_style.py     her pink style, with the palette in one tokens block
  state.py              session, database handle, page guards, the Google check
  signin.py             the Log in | Create an account switch, field errors, Google sign-in
  questions.py          the questionnaire's wording; animals.py and images.py for display
  views/                login (app.py), registration, home, questionnaire, browse,
                        account, matches, admin (pages/1 to 7)
static/fonts/           the Nunito font and its licence (OFL)
tests/                  pytest suite
docs/                   the NEA write-up (docx and PDF), compare.html, screenshots, evidence
_archive/               earlier versions kept for reference
```
