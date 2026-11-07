# PawMatch

PawMatch is Sienna Sisodia's OCR A Level Computer Science NEA project: a Streamlit and SQLite animal-adoption system for one shelter. Adopters can register, browse animal profiles, complete a lifestyle questionnaire and view ranked matches. Staff can manage animal records through an administrator account.

## Repository contents

- `documentation/PawMatch_Analysis.pdf` - current Analysis document.
- `documentation/PawMatch_Design.docx` - current Design document.
- `app/` - Streamlit application, database modules, animal images and tests.

The two files in `documentation/` are the current coursework sources of truth. Old drafts, chat exports, recovery bundles, guidance files, generated reports and temporary render files are intentionally excluded.

## Run the application

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r app/requirements.txt
python app/setup_demo_database.py
python -m streamlit run app/app.py
```

The repeatable setup command creates the database, loads the demonstration animals and prepares the local administrator account described in `app/README.md`.

## Run the tests

```bash
cd app
python -m unittest discover -s tests
```

Runtime databases, uploaded images, virtual environments, caches and temporary files are ignored by Git.
