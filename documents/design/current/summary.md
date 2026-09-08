# Design first draft summary

Source: `design-first-draft.pdf` (57 pages, Sienna Sisodia).

The design decomposes PawMatch into authentication, a user homepage, staff animal management, animal browsing/profiles and a questionnaire-driven matching system. It specifies Streamlit pages, SQLite tables, validation, password hashing, sessions, role-based access and parameterised SQL.

## Proposed data model

- `Users`: identity, email, age, password hash, role and creation date.
- `Animals`: identity, profile, care requirements, compatibility constraints, image path and date added.
- `QuestionnaireResponses`: the user's home, lifestyle and preferences.
- `MatchResults`: animal score, category, unmet requirements and calculation date.

One user can have many questionnaire responses; each response can produce many match results; each animal can appear in many results.

## Proposed scoring weights

- Hours left alone: 20
- Child compatibility: 15
- Housing space: 15
- Activity level: 12
- Garden access: 10
- Species preference: 10
- Size preference: 5

Species and size are intended to guide ranking without artificially inflating the core suitability percentage. Results should be sorted and the top three to five shown.

## Issues to resolve

- Email and username are used inconsistently for authentication.
- Password length alternates between at least eight and more than eight characters.
- Several schema and variable names contain inconsistent spelling.
- The listed weights and final percentage normalisation are not fully defined.
- The compatibility algorithm still needs precise pseudocode and a flowchart.
- The Development Test Plan pages contain headings but no test cases.

