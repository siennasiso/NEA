@part D Design
# 2 Design {#design}

## 2.1 Decomposition of the problem {#d-decomp}
The system is broken down top-down until each box is small enough to design, build and test on its own. Each leaf of the chart is one module or one page, and each is built in one development stage (the stage number is shown on the chart and in the table).

@img d01-hierarchy.png | Hierarchy chart: PawMatch decomposed into five components and their sub-tasks | | key=fig-hierarchy

@her 556-565

@widths 1.6 2.6 2.2 0.8
| Component | Sub-tasks | Module(s) | Stage |
|---|---|---|---|
| Accounts and login | Register, validate, hash password, log in, keep session, log out | `pawmatch/auth.py`, `validation.py`, `webui/views/login.py`, `registration.py` | 1 |
| Staff animal management | Role check, add / edit / delete, validate every field, photo upload | `pawmatch/services.py`, `webui/views/admin.py`, `webui/images.py` | 2 |
| Home and browse | Home page, cards, filters and search, profile | `webui/views/home.py`, `browse.py`, `webui/animals.py` | 3 |
| Questionnaire | One question per screen, validate each answer, store response | `webui/questions.py`, `webui/views/questionnaire.py` | 4 |
| Matching and results | Score each animal, rank, store and show results with reasons | `pawmatch/matching.py`, `webui/views/matches.py` | 5 |
| Database (shared) | Create tables, read and write records, constraints | `pawmatch/db.py`, `models.py`, `seed.py` | 1 to 5 |

### Structure of the solution {#d-structure}
The program is split into two layers. The **domain layer** (`pawmatch/`) contains all rules: validation, scoring, accounts and the database, and has no screen code, so every rule can be tested automatically without opening a browser. The **interface layer** (`webui/`) draws the pages and calls the domain layer. This separation is what lets {{tests_total}} tests run in a few seconds.

@img d02-structure.png | Structure: the interface layer calls the domain layer, which alone touches the database | | key=fig-structure

@img d08-classes.png | Data classes used between the layers (Animal, Answers, MatchResult, User) | 15 | key=fig-classes

## 2.2 Database design {#d-database}
@her 569-573

@img d03-er.png | Entity relationship diagram: users 1 to many responses 1 to many match results; animals 1 to many match results | 15 | key=fig-er

The final table definitions are below. Every rule that validation enforces is repeated as a database constraint (CHECK, NOT NULL, UNIQUE), so even a programming mistake cannot store an impossible value. This is tested on purpose ([[d-testplan]], T2.11).

@widths 1.6 1.1 4.3
| Table . field | Type | Key / constraint and why |
|---|---|---|
| **users** . user_id | INTEGER | Primary key, auto-increment |
| users . email | TEXT | NOT NULL, UNIQUE, case-insensitive (so Sam@x.com and sam@x.com are the same account) |
| users . age | INTEGER | CHECK age ≥ 18 (adopters must be adults) |
| users . password_hash | TEXT | scrypt hash with a random salt; the password itself is never stored |
| users . role | TEXT | 'user' or 'admin'; decides what each person can see and do |
| **animals** . animal_id | INTEGER | Primary key, auto-increment |
| animals . species / sex / size / status | TEXT | Each CHECKed against its fixed list (Dog, Cat, Rabbit; Male, Female, Unknown; Small, Medium, Large; Available, Reserved, Adopted) |
| animals . age | INTEGER | CHECK 1 to 30 |
| animals . exercise_needs, min_housing_level | INTEGER | CHECK 1 to 3 (the same scale the adopter answers on) |
| animals . max_hours_alone | INTEGER | CHECK 0 to 24 |
| animals . garden_required, child_compatible, good_with_pets | INTEGER | CHECK 0 or 1 (Boolean) |
| animals . experience_needed | INTEGER | CHECK 0 to 2 (first-time owner, some, experienced) |
| **questionnaire_responses** . response_id | INTEGER | Primary key; user_id is a foreign key, deleted with its user |
| questionnaire_responses . (10 answers) | INTEGER / TEXT | Each CHECKed to the same range as the question |
| **match_results** . match_id | INTEGER | Primary key; response_id and animal_id are foreign keys (deleted with the response or animal) |
| match_results . compatibility | REAL | CHECK 0 to 100 |
| match_results . category | TEXT | Strong, Good, Possible or Low |
| match_results . met, unmet, warnings | TEXT | The reasons, stored so a result can be shown again without recalculating |

## 2.3 Component 1: accounts and login {#d-login}
@her 575-590

@img d04-flow-login.png | Flowchart: login and registration | 14 | key=fig-flow-login

### Pseudocode: registration and login {#d-login-pseudo}
```Pseudocode D1: register a new adopter
FUNCTION register(name, email, age, password, confirm)
    errors ← validate_registration(name, email, age, password, confirm)
    IF errors is not empty THEN
        RETURN (null, errors)                // each message shown under its own box
    ENDIF
    IF a user with LOWER(email) already exists THEN
        RETURN (null, {email: "An account with this email already exists."})
    ENDIF
    salt ← 16 random bytes
    hash ← scrypt(password, salt)
    INSERT INTO users (name, email, age, hash, role = 'user', now)
    RETURN (new user, no errors)              // signed straight in
ENDFUNCTION
```

```Pseudocode D2: log in (the same message for every failure)
FUNCTION login(email, password)
    IF email is blank THEN RETURN "Enter your email address."
    IF password is blank THEN RETURN "Enter your password."
    user ← SELECT * FROM users WHERE email = LOWER(TRIM(email))
    IF user is null OR verify(password, user.password_hash) = false THEN
        RETURN "Incorrect email or password."  // never says which part was wrong
    ENDIF
    session.user_id ← user.user_id
    IF user.role = 'admin' THEN open staff dashboard ELSE open home page
ENDFUNCTION
```

@her 592-618

@design login | Annotated design: login screen (her layout and colours) | fig-design-login
@design register | Annotated design: registration with a message under each field | fig-design-register

## 2.4 Component 2: staff animal management {#d-admin}
@her 620-630

### Pseudocode: add, edit and delete an animal {#d-admin-pseudo}
```Pseudocode D3: every staff action checks the role first
FUNCTION save_animal(current_user, form, animal_id = null)
    IF current_user is null OR current_user.role ≠ 'admin' THEN
        STOP with an access error (require_admin)
    ENDIF
    (values, errors) ← validate_animal(form)      // 14 field checks, below
    IF form.photo is present THEN
        problem ← validate_image(form.photo.name, form.photo.size)
        IF problem ≠ null THEN errors.image ← problem
    ENDIF
    IF errors is not empty THEN RETURN errors          // nothing is saved
    IF animal_id = null THEN
        INSERT INTO animals VALUES (values)            // parameterised query
    ELSE
        rows ← UPDATE animals SET values WHERE animal_id = ?
        IF rows = 0 THEN RETURN "That animal no longer exists."
    ENDIF
    RETURN "Saved"
ENDFUNCTION

FUNCTION delete_animal(current_user, animal_id, confirmed)
    IF current_user.role ≠ 'admin' THEN STOP with an access error (require_admin)
    IF confirmed = false THEN RETURN "Tick the box to confirm."
    DELETE FROM animals WHERE animal_id = ?            // its stored match results go too
ENDFUNCTION
```

@her 634-691

@design admin-list | Annotated design: staff table of animals | fig-design-admin-list
@design admin-add | Annotated design: add-animal form with grouped sections | fig-design-admin-add

## 2.5 Component 3: home page and browsing {#d-browse}
@her 693-703

```Pseudocode D4: home page (main menu)
IF session.user_id is null THEN go to login page
user ← SELECT name, role FROM users WHERE user_id = session.user_id
SHOW "Welcome, " + user.name, the three "how it works" steps and "staff make the final decision"
IF the user has a stored questionnaire THEN show "See my matches" ELSE show "Take the questionnaire"
MENU ← [Home, Browse animals, Questionnaire, My matches, My account]
IF user.role = 'admin' THEN MENU ← [Dashboard, Manage animals, Add animal]
```

@her 706-729

```Pseudocode D5: browse with filters (search text is data, never SQL)
FUNCTION browse(species, size, search)
    sql ← "SELECT * FROM animals WHERE status = 'Available'"
    params ← []
    IF species ≠ "All species" THEN sql ← sql + " AND species = ?"; ADD species TO params
    IF size ≠ "All sizes" THEN sql ← sql + " AND size = ?"; ADD size TO params
    term ← TRIM(search)
    IF term ≠ "" THEN
        sql ← sql + " AND (name LIKE ? OR breed LIKE ?)"
        ADD "%" + term + "%" TO params TWICE
    ENDIF
    RETURN rows of sql + " ORDER BY species, name", using params
ENDFUNCTION
```

@her 733-746

@design home | Annotated design: home page | fig-design-home
@design browse | Annotated design: browse cards with species and size filters | fig-design-browse
@design profile | Annotated design: animal profile with its needs | fig-design-profile

## 2.6 Component 4 and 5: questionnaire and compatibility algorithm {#d-matching}
@her 749-763

@img d05-flow-questionnaire.png | Flowchart: one question per screen, Next only when answered | 14 | key=fig-flow-q

@img d06-flow-matching.png | Flowchart: scoring and ranking every available animal | 14 | key=fig-flow-match

### Pseudocode: scoring and ranking {#d-score-pseudo}
The score is a weighted sum normalised to a percentage, so the scale stays 0 to 100 however many factors there are or however the weights are changed.

```Pseudocode D6: score one animal
FUNCTION score_animal(animal, answers)
    earned ← 0;  met ← [];  unmet ← [];  warnings ← []
    FOR EACH factor IN WEIGHTS
        fraction ← check(factor, animal, answers)   // 1 = met, 0 = not met, 0.5 = one level short
        earned ← earned + WEIGHTS[factor] × fraction
        IF fraction = 1 THEN
            ADD reason TO met
        ELSE
            ADD reason TO unmet
            IF factor IN IMPORTANT_FACTORS THEN ADD reason TO warnings
        ENDIF
    NEXT factor
    compatibility ← ROUND(100 × earned ÷ SUM(WEIGHTS), 1)
    category ← "Strong" IF compatibility ≥ 80, "Good" IF ≥ 60, "Possible" IF ≥ 40, ELSE "Low"
    bonus ← 10 IF animal.species = answers.preferred_species, + 5 IF animal.size = answers.preferred_size
    RETURN (compatibility, category, bonus, met, unmet, warnings)
ENDFUNCTION
```

```Pseudocode D7: rank every available animal
FUNCTION rank_animals(animals, answers)
    results ← [score_animal(a, answers) FOR EACH a IN animals]
    SORT results BY
        1. has no warnings first           // a welfare risk is never above a safe match (Q3)
        2. compatibility + bonus, highest first
        3. compatibility, highest first
        4. name A to Z, then animal_id     // identical animals always come out in the same order
    RETURN results
ENDFUNCTION
```

Sorting uses Python's built-in sort (Timsort, O(n log n)), which is stable and far faster than needed for 20 animals; the measured time for 500 animals is on [[e-results]].

@her 767-810

### Weights {#d-weights}
@her 811-822

:::note Design decision: preferences do not change the percentage
Species and size preferences only add to a separate ranking total. If they were added to the percentage, an unsuitable animal of the preferred species could show a misleadingly high score, which is exactly what the client wanted to avoid (Q10). The final weights, after the design re-check in development stage 5, are on [[s-weights]].
:::

@design questionnaire | Annotated design: one question per screen with card answers and progress | fig-design-q
@design matches | Annotated design: ranked matches with met and not-met reasons | fig-design-matches

## 2.7 Usability features {#d-usability}
@widths 1.8 2.2 3 1
| Usability feature | Where it appears | Why (source) | Evaluated |
|---|---|---|---|
| Soft pink palette, Nunito font, large photos | Every page | Client asked for a cute, friendly, pastel look with lots of photos (Q11) | SC1, U5 |
| Contrast at least 4.5:1 and text at least 12 px | Every page | Readable for older and low-vision users (WCAG 2.2 AA, E5) | SC1 |
| One consistent menu; staff see only staff items | Sidebar | Find things quickly without clicking through many pages (Q6) | SC2 |
| One question per screen with progress "Question N of 10" | Questionnaire | Less overwhelming than a long form (E3, S6) | SC8, U2 |
| Card buttons instead of dropdowns | Questionnaire | Fewer clicks and a bigger target than a dropdown; the selected card is highlighted | U2 |
| Next disabled until the question is answered | Questionnaire | Cannot submit an incomplete questionnaire (Q15, S8) | SC8 |
| Error message under the box that caused it | Register, login, staff forms | The user sees exactly what to fix | SC6, U1 |
| One generic login error | Login | Security: does not reveal which emails have accounts (Q12) | SC7 |
| Met / not met / warning lists on each match | Matches, profile | Explains the score (Q3, E5) | SC11, U3 |
| "Staff make the final decision" wording | Home, matches | Sets the right expectation (Q4) | SC3 |
| Tick-box confirmation before delete | Staff manage page | Stops an accidental delete | SC12, U4 |
| Keyboard focus outline | Every control | Usable without a mouse | SC1 |

## 2.8 Development test plan {#d-testplan}
These tests are run during development, stage by stage, to inform it. Each has an ID used in the development section, and almost all are automated with pytest so they can be re-run after every change (regression testing). Types: **N** = normal, **B** = boundary, **I** = invalid / erroneous.

@widths 0.55 2.4 0.4 2.3 2.3
| ID | Test | Type | Test data | Expected result |
|---|---|---|---|---|
| **Stage 1** | **Accounts and login** | | | |
| T1.1 | Register a valid adopter | N | Sam Lee, sam@example.com, 30, password1 twice | Account created, password stored as a hash, signed straight in |
| T1.2 | Required fields blank | I | Every box empty | A message under each of the five boxes; nothing saved |
| T1.3 | Email format | I | no-at-sign.com, a@b, two@@x.com, spa ce@x.com | "Enter a valid email address…" |
| T1.4 | Age limits | B | 17, 18, 120, 121, 2.5, abc | 18 and 120 accepted; others refused with a reason |
| T1.5 | Password length | B | 7 characters, 8 characters | 7 refused, 8 accepted |
| T1.6 | Confirm password | I | different second password; blank second box | "The two passwords do not match." / "Type your password again…" |
| T1.7 | Duplicate email, different case | I | SAM@example.com after sam@example.com | "An account with this email already exists." |
| T1.8 | Name format | B/I | Mary-Jane, Siobhan O'Neill / Sam3, 12345, Sam! | First two accepted, the rest refused |
| T1.9 | Correct login, both roles | N | demo adopter; staff account | Adopter to home page, staff to dashboard |
| T1.10 | Wrong password and unknown email | I | right email + wrong password; unknown email | The same single message for both |
| **Stage 2** | **Staff animal management** | | | |
| T2.1 | Add, edit, delete as staff | N | A complete valid animal | Saved, changed, then removed |
| T2.2 | Required fields blank | I | Empty form | A message for each missing field; nothing saved |
| T2.3 | Animal age and hours alone | B | age 0, 1, 30, 31; hours −1, 0, 24, 25 | Values inside the range accepted, outside refused |
| T2.4 | Fixed lists | I | species Hamster, size Huge, sex ?, exercise 4 | Refused with a reason |
| T2.5 | Photo type and size | B/I | a.png 100 B, b.JPG 2 097 152 B / c.gif, d.jpg 2 097 153 B | First two accepted, last two refused |
| T2.6 | Text length | B | Medical notes of 501 characters | Refused (limit 500) |
| T2.7 | Edit an animal deleted meanwhile | I | Edit animal_id that no longer exists | "That animal no longer exists." |
| T2.8 | Adopter or signed-out user tries every staff action | I | role = user; no user | Every add, edit and delete refused |
| T2.9 | Delete removes stored results too | N | Animal with match results | Animal and its results removed |
| T2.10 | Overview flags weak records | N | Animal without a photo, short description | Listed as needing attention |
| T2.11 | Database rejects a bad row inserted directly | I | INSERT with species Hamster, bypassing validation | sqlite3.IntegrityError |
| **Stage 3** | **Home and browse** | | | |
| T3.1 | Every Available animal has a card | N | Demo data | One card per Available animal; Reserved and Adopted hidden |
| T3.2 | Species, size and search filters | N | Cat; Small; "lab" | Only matching animals shown |
| T3.3 | Search text is data, not SQL | I | `' OR 1=1 --` | No results; every animal still in the table |
| T3.4 | Profile shows the animal's needs | N | Open Milo | All fields and needs shown, back link works |
| T3.5 | Signed-out visitor opens a page | I | No session | Sent to the login page |
| **Stage 4** | **Questionnaire** | | | |
| T4.1 | Next waits for an answer | I | No card chosen | Next disabled |
| T4.2 | Hours alone limits | B | −1, 0, 24, 25 | 0 and 24 accepted, −1 and 25 refused |
| T4.3 | Allergies | N/I | none; Dog and Cat / Ferret; Dog twice | Valid answers stored in a fixed order; others refused |
| T4.4 | "No allergies" clears the others | N | Choose Cat, then No allergies | Only No allergies selected |
| T4.5 | Complete questionnaire | N | 10 valid answers | Every Available animal scored and stored |
| T4.6 | Incomplete submission | I | 9 of 10 answers | Nothing saved |
| **Stage 5** | **Matching and results** | | | |
| T5.1 | Perfect match | N | Answers meeting every need | 100%, Strong, no warnings |
| T5.2 | Each factor loses exactly its weight | N | Change one need at a time | Score drops by that weight (half for one level short) |
| T5.3 | Boundaries count as met | B | hours alone = animal's maximum | Met |
| T5.4 | Category thresholds | B | 80, 79.9, 60, 59.9, 40, 39.9 | Strong, Good, Good, Possible, Possible, Low |
| T5.5 | Important factor unmet | N | Children at home, animal not child-safe | Warning raised; garden or activity shortfall does not warn |
| T5.6 | Allergy | N | Allergic to cats, perfect cat | Score capped at 39%, warning listed first |
| T5.7 | Ranking order | N | Mixed animals | No-warning animals first; preference changes order, not percentage |
| T5.8 | Hand calculation | N | Worked example ([[s-worked]]) | Program equals hand calculation |
| T5.9 | Results page | N | Completed questionnaire | Top 5 shown, "show all" shows the rest |
| T5.10 | Empty and identical lists | B | No animals; two identical animals | No crash; same order every time |
| **Stage 6** | **Accessibility and final checks** | | | |
| T6.1 | Text contrast | N | Every text colour in the stylesheet | At least 4.5:1 |
| T6.2 | Text size | N | Every font size | At least 12 px |
| T6.3 | Rendered audit | N | Every screen at 1440 and 1024 px | 0 low-contrast texts, 0 small texts, focus visible |

## 2.9 Post-development test plan {#d-postplan}
After development is finished, the complete system is tested against **each success criterion** (P1 to P16). My teacher asked for this plan to be linked to the development tests: the third column shows which T tests are re-run as part of each P test, so the evidence on [[e-results]] is the final build passing them all again, plus the extra checks that only make sense on the finished system.

@widths 0.5 2.6 1.3 3
| P | Success criterion | Re-runs | Extra evidence on the finished system |
|---|---|---|---|
| P1 | SC1 look, contrast, text size | T6.1 to T6.3 | Rendered audit of all {{audit_screens}} screens; client sign-off |
| P2 | SC2 one menu | T3.5, T2.8 | Screenshots of the adopter and staff menus |
| P3 | SC3 home explains | T3.4 | Home screenshot; button opens questionnaire |
| P4 | SC4 browse and filters | T3.1 to T3.3 | Browse screenshot with each filter |
| P5 | SC5 profile | T3.4 | Profile screenshot |
| P6 | SC6 registration validation | T1.1 to T1.8 | Error screenshot |
| P7 | SC7 secure accounts | T1.9, T1.10 | Database row shows a hash, not a password |
| P8 | SC8 questionnaire | T4.1 to T4.6 | Timed run by testers (U2) |
| P9 | SC9 correct score | T5.1 to T5.4, T5.6, T5.8 | Worked example against the screen |
| P10 | SC10 ranking and speed | T5.7, T5.9, T5.10 | Timed with 500 animals and 100 users |
| P11 | SC11 explanations | T5.5, T5.6 | Matches screenshot |
| P12 | SC12 staff CRUD | T2.1 to T2.7, T2.9 | Add-form error screenshot |
| P13 | SC13 access control | T2.8 | Adopter opening the staff page |
| P14 | SC14 data and capacity | T2.11, T4.5 | Timed browse page with 500 animals |
| P15 | SC15 usability | n/a | Usability tasks U1 to U5 and SUS questionnaire; client final review |
| P16 | SC16 laptop and tablet | T6.3 | Screenshots at 1440 and 1024 px |

### Usability tasks {#d-utasks}
Each tester is given the task only, with no help, then answers the ten-item System Usability Scale (SUS). A SUS score of 68 is the average for websites, so SC15 needs an average of at least 68.

| U | Task | Success looks like |
|---|---|---|
| U1 | Create an account and log in | Done without help; every error understood |
| U2 | Complete the questionnaire | Done in under 3 minutes without help |
| U3 | Find your top match and explain why it suits you and what any warning means | Correct explanation in the tester's own words |
| U4 | (Staff) Add an animal, edit it, then delete it | Done without help |
| U5 | Browse, open a profile and return to the list | Done without help |

### Robustness tests {#d-robust}
| R | What could go wrong | Test | Expected |
|---|---|---|---|
| R1 | Malicious text typed into search | `' OR 1=1 --` | Treated as plain text (T3.3) |
| R2 | A database error halfway through saving | Force an error inside a transaction | Whole change rolled back |
| R3 | A row inserted without the app | Bad row inserted directly | Refused by CHECK constraints (T2.11) |
| R4 | Two staff members: one deletes while the other edits | Edit a deleted animal | Clear message, no crash (T2.7) |
| R5 | An older database file from an earlier version | Open an old database | Missing columns added automatically |
| R6 | Far more data than the rescue holds | 500 animals, 100 users | Every page still works and is fast |
