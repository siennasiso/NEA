# Build stages

Build PawMatch again in a new folder, `pawmatch/`, one stage at a time. The existing `app/` folder stays as
reference only: read it, understand it, but type your own version. Submitted code has to be code you wrote and can
explain line by line.

| Stage | Build | Tests to try that should fail first | Review with |
| --- | --- | --- | --- |
| 1. Database and login | SQLite tables, register, password hashing, log in, log out | Duplicate email, 7-character password, blank fields | Client: are the error messages clear? |
| 2. Admin dashboard | Role check, add / edit / delete animal, image upload | Non-admin opening the page, age 0, wrong file type | Shelter staff: is the form quick to use? |
| 3. Home and browse | Animal cards, profile page, search, species and size filters | Empty search, a filter with no results, unknown animal ID | 2 or 3 survey respondents |
| 4. Questionnaire | Sectioned questions, validation, saving responses | Skipped question, 25 hours left alone | An adopter |
| 5. Matching and results | Weighted score, hard rules, sorting, top results, unmet-needs messages | Your hand-worked example, ties, no matches | Client: are the rankings sensible? |

## Every stage, the same six parts in the write-up

1. Aim, and which part of the Design it builds.
2. Code: screenshots of your annotated code (comments say why, not just what).
3. Tests from your development test plan, each with a screenshot.
4. At least one failed test: what happened, the cause, the fix, the re-test.
5. Review: who you showed it to, what you asked, what they said.
6. What you changed because of the review.

## Saving each stage

Your teacher asks for a saved copy of every version. At the end of each stage:

```bash
git add -A
git commit -m "Stage 2: admin dashboard - add, edit and delete working"
git tag stage-2
```

Also screenshot the running app at the end of each stage; those screenshots are your prototype evidence.
Write commit messages yourself, in your own words: they are part of the record of how the project was built.
