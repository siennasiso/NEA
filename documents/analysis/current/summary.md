# Analysis summary

Source: `analysis.pdf` (42 pages, PawMatch, Sienna Sisodia).

PawMatch is proposed as an animal-adoption and maintenance tool for one shelter. Adopters register, browse multi-species profiles, answer a lifestyle questionnaire and receive ranked compatibility results. Staff use a private administration area to add, edit and remove animals and inspect suitability information. Shelter staff retain the final adoption decision.

## Evidence and requirements

- Competitor research covers Dogs Trust, RSPCA and Petfinder.
- Primary research includes a client interview and a 27-response stakeholder survey.
- The survey strongly supports detailed research before adoption, a simple interface and compatibility scoring. The most selected matching factors were living space, time, income, garden access and experience.
- The feature list covers navigation, profiles, multi-species browsing, a step-by-step questionnaire, validation, numerical compatibility scoring, ranked recommendations, warnings, authentication, staff CRUD operations, persistent storage and a responsive Streamlit interface.
- Success criteria require at least four ranked matches, clear met/unmet requirements, staff-only administration and correct persistent database retrieval.

## Technical direction

The selected stack is Python, Streamlit and SQLite, developed in VS Code and tested primarily in Chrome. The solution uses abstraction, decomposition, validation, weighted scoring, iteration and sorting. It is deliberately rule-based rather than AI/ML and does not cover payments, contracts, home checks, live chat or final adoption approval.

## Useful next extraction work

Turn the success-criteria table into executable acceptance tests, formalise the exact weighting and normalisation rules, and map each requirement to one implementation component and one evidence item.

