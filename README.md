# PawMatch DB1 manual development test

This branch contains only the PawMatch SQLite schema needed for the DB1 test.
It does not contain the completed application.

## Create the database

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

