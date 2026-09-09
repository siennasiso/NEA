# PawMatch questionnaire and matching algorithm

This file explains the questionnaire, database tables and matching algorithm implemented from the final design.

## Questionnaire

The page is split into five short sections and asks seven questions:

1. **Home:** housing level — `1` Flat or limited space, `2` Small or medium house, or `3` Large house — and whether a garden is available.
2. **Household:** whether children live in the home.
3. **Lifestyle:** the activity level the user can support (`1` Low, `2` Moderate, `3` High) and the whole number of hours the animal will usually be alone (`0`–`24`).
4. **Preferences:** preferred species and size. Each includes **No preference**.
5. **Submit:** review, validate and save the answers, then calculate matches.

Boolean answers are stored as `1` for Yes and `0` for No. Input is validated both in Python and by SQLite constraints.

## Database tables

`questionnaire_responses` stores each completed set of answers. Its `user_id` foreign key connects a response to the `users` table.

`match_results` stores one calculated result for every available animal at submission time. Its foreign keys connect each result to both `questionnaire_responses` and `animals`. It stores the compatibility score, internal ranking score, category, requirements met, requirements not met and calculation time.

The `animals` table stores the requirements used by the algorithm, including minimum housing level, garden requirement, activity level, child suitability and maximum hours alone. The setup script inserts 13 sample animals and can be repeated without duplicating them.

## Welfare compatibility score

For each available animal, the algorithm starts at zero and adds the following points when the requirement is met:

| Requirement | Points | Test |
|---|---:|---|
| Hours alone | 20 | User hours are no more than the animal's maximum |
| Children | 15 | No children live at home, or the animal is marked suitable for children |
| Housing | 15 | User housing level is at least the animal's minimum |
| Activity | 12 | User-supported activity level is at least the animal's level |
| Garden | 10 | The animal does not require a garden, or the user has one |

The maximum is 72 points. The displayed percentage is:

```text
compatibility percentage = round(points earned / 72 × 100)
```

The fixed categories are:

- **Strong:** 80–100%
- **Good:** 65–79%
- **Possible:** 50–64%
- **Low:** below 50%

Low matches are stored for traceability but removed from the recommendation page.

## Preference ranking

Species and size preferences must not disguise a welfare mismatch, so they do not change the displayed compatibility percentage. Only animals with at least 60% compatibility receive preference bonuses:

- matching preferred species: `+10` ranking points;
- matching preferred size: `+5` ranking points;
- No preference: no bonus.

Results are sorted by the internal ranking score, then compatibility. The page shows the top three results from the interface design but does not display the internal ranking score.

## Program flow

```text
collect seven answers
        ↓
validate answer types and ranges
        ↓
insert questionnaire_responses row
        ↓
fetch animals with status = Available
        ↓
calculate welfare compatibility for each animal
        ↓
apply preference bonuses only when compatibility ≥ 60%
        ↓
insert match_results rows
        ↓
remove Low matches from the displayed list and show the top three
```

The implementation is in `pawmatch_matching.py`. Its functions have docstrings and keep database operations separate from the Streamlit pages.
