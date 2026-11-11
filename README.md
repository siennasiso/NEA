# PawMatch database and authentication development stages

This branch contains the isolated database, registration and login increments.
Animal management, browsing, questionnaires and matching are intentionally not
present yet. This makes the DB1 and R1-R6 development tests traceable.

## Install and start the authentication stage

```bash
python3 -m pip install -r requirements.txt
python3 setup_database.py --fresh
streamlit run app.py
```

`--fresh` moves an existing database to a timestamped backup before building a
new one. It also creates the local demonstration administrator used for R6:

```text
Username: admin123
Password: password123
```

These credentials are intentionally simple and must only be used for local
coursework testing.

## Create only the database

From this folder, run:

```bash
python3 setup_database.py --fresh
```

The command creates `pawmatch.db`. If a database already exists, `--fresh`
moves it to a timestamped `.backup.db` file before creating the clean database.

## Inspect it in DB Browser for SQLite

1. Open DB Browser for SQLite.
2. Select **Open Database**.
3. Choose `pawmatch.db` from this folder.
4. Open the **Database Structure** tab.
5. Confirm that these tables exist:
   - `users`
   - `animals`
   - `questionnaire_responses`
   - `match_results`
6. Expand each table to inspect its columns and primary key.
7. Select **File > Export > Database to SQL file** only if you want additional
   evidence of the schema; do not save changes to the clean DB1 database.

For a readable terminal summary of the same structure, run:

```bash
python3 inspect_database.py
```

For your Development document, capture a screenshot of the Database Structure
tab showing all four tables and a second screenshot showing the terminal output.

## Registration and login manual tests

The app is ready for the pre-development authentication tests:

- **R1:** confirm the registration form displays name, email, age, password and
  confirmation fields.
- **R2:** register `adopter1@example.com`, age 19, with `password123`; confirm
  that the adopter homepage opens and a `user` row is stored.
- **R3:** try each invalid value separately: blank/one-character name, invalid
  email, age 17, duplicate email, mismatched confirmation, seven-character
  password and eight-character password.
- **R4:** create two users with the same password. In DB Browser, confirm the
  `password_hash` values both begin `$argon2id$`, differ from each other and do
  not contain the plaintext password.
- **R5:** test correct details, a wrong password and an unknown email. The two
  invalid credential attempts must show the same generic message.
- **R6:** confirm an adopter is refused the Admin area, then log in with the
  demonstration administrator and confirm access is granted.

Use fictional `example.com` addresses for evidence rather than personal data.

