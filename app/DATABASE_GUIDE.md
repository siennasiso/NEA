# PawMatch database guide

PawMatch uses SQLite, so the whole local database is one file: `app/pawmatch.db`. The file is created automatically and is ignored by Git because it may contain account information and local test data.

## Quick demo setup

From the `app` folder run:

```bash
python3 setup_demo_database.py
```

This command is safe to repeat. It:

1. creates or upgrades the `users` table;
2. creates the `animals`, `questionnaire_responses` and `match_results` tables and indexes;
3. creates or refreshes the demonstration administrator;
4. adds any missing records from the 13-animal demonstration dataset.

Demo administrator:

```text
Username: admin123
Password: password123
```

This deliberately simple password is only for local coursework testing. It is stored in SQLite as a salted scrypt hash, not as plain text. Change it before deploying the site or using real data.

## How the database works

`pawmatch_auth.py` owns the database connection and user authentication. Every connection enables foreign keys and returns rows that can be accessed by column name.

The `users` table contains:

| Column | Purpose |
|---|---|
| `user_id` | Unique automatically generated account ID |
| `name` | Display name |
| `username` | Optional unique login name, primarily for administrators |
| `email` | Unique adopter email and normal adopter login |
| `age` | Validated age from 18 to 120 |
| `password_hash` | Salted scrypt hash; never display or edit directly |
| `role` | Either `user` or `admin` |
| `created_at` | Automatic creation timestamp |

`pawmatch_animals.py` owns animal validation and CRUD operations. The `animals` table stores the public profile, matching requirements, adoption status, image URL and timestamps. Check constraints reject unsupported values even if invalid data bypasses the interface.

`pawmatch_matching.py` owns questionnaire validation, response storage and match calculation. `questionnaire_responses` stores the seven submitted answers. `match_results` links each response to each available animal and records its compatibility, category and explanations. See `MATCHING_ALGORITHM.md` for the precise weights and ranking rules.

## View the data safely

These commands deliberately omit password hashes:

```bash
python3 view_database.py
python3 view_database.py users
python3 view_database.py animals
python3 view_database.py responses
python3 view_database.py matches
```

You can also inspect the file with DB Browser for SQLite, or use the SQLite command line:

```bash
sqlite3 pawmatch.db
.tables
.schema users
.schema animals
.headers on
.mode column
SELECT user_id, name, username, email, role FROM users;
SELECT animal_id, name, species, breed, status FROM animals;
.quit
```

Do not select or publish `password_hash` values. They are authentication data even though they are hashed.

## Insert data

### Recommended: administrator dashboard

1. Run `streamlit run app.py`.
2. Log in with the demonstration administrator.
3. Select **Add animal**.
4. Complete every required field.
5. Submit the form.

The form calls `validate_animal()` and then `create_animal()`. The insert uses `?` parameters rather than joining user input into SQL, which prevents SQL injection.

### Python example

```python
from pawmatch_animals import create_animal, initialise_animals_table, validate_animal

initialise_animals_table()
record = {
    "name": "Ruby",
    "species": "Dog",
    "breed": "Border collie cross",
    "age_years": 4,
    "sex": "Female",
    "size": "Medium",
    "activity_level": "High",
    "home_type": "House",
    "minimum_housing_level": 2,
    "garden_required": True,
    "child_friendly": "Older children only",
    "other_pets": "Depends",
    "experience_level": "Experienced owner",
    "max_hours_alone": 3,
    "status": "Available",
    "description": "Ruby is a clever and energetic dog who enjoys training, enrichment and long daily walks.",
    "image_url": "",
}

errors, cleaned = validate_animal(record)
if errors:
    print(errors)
else:
    success, animal_id, message = create_animal(cleaned)
    print(success, animal_id, message)
```

## Read, update and delete data

Use the helper functions instead of writing SQL in Streamlit pages:

```python
from pawmatch_animals import delete_animal, fetch_animal, fetch_animals, update_animal

all_animals = fetch_animals()
available_dogs = fetch_animals(species="Dog", status="Available")
animal = fetch_animal(1)

# Validate a complete changed record before updating it.
# errors, cleaned = validate_animal(changed_record)
# success, message = update_animal(1, cleaned)

# The admin dashboard asks for confirmation before this permanent action.
# success, message = delete_animal(1)
```

The dashboard already supports searching, filtering, editing and confirmed deletion. `updated_at` changes automatically during an update.

## Back up and reset local data

Stop Streamlit before copying the database:

```bash
cp pawmatch.db pawmatch-backup.db
```

To start with a fresh local database, move the current file somewhere safe and rerun setup:

```bash
mv pawmatch.db pawmatch-old.db
python3 setup_demo_database.py
```

Never commit `pawmatch.db`, backups containing real account data, or real adopter details to GitHub.
