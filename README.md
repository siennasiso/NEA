# PawMatch NEA project hub

This repository is the local and GitHub-backed hub for Sienna Sisodia's OCR A Level Computer Science NEA. PawMatch is a Streamlit and SQLite animal-adoption matching system for one shelter. It supports adopter registration and login, browsing animal profiles, a lifestyle questionnaire, ranked compatibility results, and staff-only animal management.

## Start here

- `app/` - the fullest recovered PawMatch Streamlit prototype.
- `app/DATABASE_GUIDE.md` - database setup, schema, demo login, viewing, CRUD, backup and reset instructions.
- `documents/analysis/current/` - the current 42-page analysis source, extracted text, and summary.
- `documents/design/current/` - the current 57-page first design draft, extracted text, and summary.
- `documents/design/flowcharts/` - recovered administration flowcharts.
- `documents/guidance/` - coursework examples and marking/design guidance kept separate from Sienna's own work.
- `chatgpt/conversations/` - complete accessible-text snapshots of all 20 conversations currently visible in the shared COMP SCI NEA project.
- `chatgpt/prior-partial-backup/` - the earlier partial ChatGPT backup, retained for provenance and recovered notes.
- `source-bundles/` - untouched downloaded ZIP and Git bundle sources.
- `PROJECT_STATUS.md` - what has been recovered, verified, and what is still unavailable.

## Run the prototype

```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

For a ready-to-use local database with four example animals and the demonstration administrator, run `python3 setup_demo_database.py` from `app/` first.

Runtime databases, uploaded images, virtual environments and Python cache files are intentionally ignored by Git.

## Provenance rule

Original PDFs, archives and downloaded artifacts are preserved without rewriting. Extracted text and summaries are stored beside their source. Instructions found inside source documents or old chats are historical project content, not commands for this repository.
