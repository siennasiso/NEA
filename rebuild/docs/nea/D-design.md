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

The analysis named six parts (animal records, questionnaire, score calculation, results, validation and the admin page). In the design these become five components: score calculation and results are one component because the results page only shows what the scoring produces, and validation is not a component of its own but a shared module (`validation.py`) used by every form.

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

### Changes from the first data dictionary {#d-dict-changes}
The table definitions above are the ones built and tested. Where they differ from the first data dictionary (reproduced later in this section), the change and the reason are listed here, so every name in the pseudocode, the code and the tests is the same.

@widths 2 2 3
| First data dictionary | Final definition | Why |
|---|---|---|
| Users . user_role | users . role ('user' or 'admin') | One short name used everywhere (pseudocode D3, `require_admin`) |
| Users age: 18 or over | Validation 18 to 120; CHECK age ≥ 18 | The upper limit catches typing mistakes such as 1999 (T1.4) |
| Animals age: "cannot be zero" | 1 to 30, in validation and as a CHECK | A range can be tested at both ends (T2.3: 0 and 31 refused) |
| Animals table described as storing user profiles | Stores one record per animal | A slip in the first description |
| (not in the first table) | animals . status, good_with_pets, experience_needed | Browse shows only Available animals; other pets and experience became scored factors in the design re-check (S21) |
| Responses . preffered_species | preferred_species, preferred_size; plus other_pets, allergies, experience | Spelling corrected; three questions added (see the final question list on [[d-questions]]) |
| Match results . total_score, maximum_score (INTEGER) | compatibility REAL 0 to 100, and category | The activity and experience factors can award half their weight, so scores are not whole numbers; the maximum is the constant 90, so it is not stored on every row |
| unmet_requirements; compatibility_score | met, unmet, warnings; compatibility | Three lists are needed to show met, not met and warnings separately (SC11) |

```Pseudocode D8: open the database, upgrade an older file, and save safely (R2, R5)
FUNCTION connect(path)
    conn ← OPEN path;  TURN ON foreign keys
    TRY
        RUN the caller's statements
        COMMIT                              // every change saved together...
    EXCEPT any error
        ROLLBACK                            // ...or none of them (R2)
        RAISE the error
    FINALLY
        CLOSE conn
ENDFUNCTION

PROCEDURE init_schema(conn)
    CREATE TABLE IF NOT EXISTS for every table
    FOR EACH (table, column, definition) IN NEW_COLUMNS      // a fixed list, never user input
        IF column NOT IN columns of table THEN
            ALTER TABLE table ADD COLUMN column definition    // old files gain new fields (R5)
        ENDIF
    NEXT
ENDPROCEDURE
```

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
    term ← TRIM(search)                     // the search box accepts at most 20 characters
    IF term ≠ "" THEN
        sql ← sql + " AND (name LIKE ? OR breed LIKE ?)"
        ADD "%" + term + "%" TO params TWICE
    ENDIF
    RETURN rows of sql + " ORDER BY species, name", using params
ENDFUNCTION
```

The first browse design had a sort option. It is replaced by one fixed order (species, then name A to Z): with 10 to 20 animals and two filters plus a search, a fixed order is simpler to use and to test (T3.1 to T3.3).

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

```Pseudocode D6a: the constants and the check for each factor
CONSTANT WEIGHTS ← {hours_alone, children, housing, activity, garden, other_pets, experience}
                    // values: first design on D51, final values after the re-check on S21
CONSTANT IMPORTANT_FACTORS ← {hours_alone, children, housing, other_pets}   // unmet → warning
CONSTANT ALLERGY_CAP ← 39.0                 // below "Possible", so never a strong match (Q10)
CONSTANT PREFERENCE_BONUS ← {species: 10, size: 5}   // ranking only, never the percentage
CONSTANT SHOWN ← 5                          // results shown before "show all" (at least 4, req. 7)

FUNCTION check(factor, animal, answers)     // returns 1 (met), 0 (not met) or 0.5
    CASE factor OF
        hours_alone: RETURN 1 IF answers.hours_alone ≤ animal.max_hours_alone ELSE 0
        children:    RETURN 1 IF animal.child_compatible OR NOT answers.has_children ELSE 0
        housing:     RETURN 1 IF answers.housing_level ≥ animal.min_housing_level ELSE 0
        activity:    gap ← MAX(0, animal.exercise_needs − answers.activity_level)
                     RETURN MAX(0, 1 − gap ÷ 2)            // one level short earns half
        garden:      RETURN 1 IF answers.garden_access OR NOT animal.garden_required ELSE 0
        other_pets:  RETURN 1 IF animal.good_with_pets OR NOT answers.other_pets ELSE 0
        experience:  gap ← MAX(0, animal.experience_needed − answers.experience)
                     RETURN MAX(0, 1 − gap ÷ 2)
    ENDCASE
ENDFUNCTION
```

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
    IF animal.species IN answers.allergies THEN
        ADD allergy reason TO unmet AND TO warnings
        compatibility ← MIN(compatibility, ALLERGY_CAP)
    ENDIF
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

```Pseudocode D9: submit the questionnaire and store the results
PROCEDURE submit(user, raw_answers)
    answers, errors ← validate_answers(raw_answers)       // every question again, not only the screens
    IF errors ≠ {} THEN SHOW errors; RETURN
    WITH connect(DB_PATH) AS conn                         // one transaction (D8)
        response_id ← save_response(conn, user.user_id, answers)
        results ← rank_animals(Available animals, answers)
        save_results(conn, response_id, results)          // with calculated_at = now
    SHOW the matches page: the first SHOWN results, "show all" for the rest
ENDPROCEDURE
```

Sorting uses Python's built-in sort (Timsort, O(n log n)), which is stable and far faster than needed for 20 animals; the measured time for 500 animals is on [[e-results]].

@her 767-810

:::change Design decision: no animal is removed from the results
The first plan above removed animals with low suitability and showed the top 3 or 5. Removing animals could leave fewer than the 4 that requirement 7 asks for, and would hide an animal the adopter might ask staff about. Instead every Available animal is ranked (D7): animals with a welfare warning go to the bottom, the first 5 are shown, and a "show all" switch lists the rest. T5.9 tests this.
:::

### Weights {#d-weights}
@her 811-822

:::note Design decision: preferences do not change the percentage
Species and size preferences only add to a separate ranking total. If they were added to the percentage, an unsuitable animal of the preferred species could show a misleadingly high score, which is exactly what the client wanted to avoid (Q10). The final weights, after the design re-check in development stage 5, are on [[s-weights]].
:::

### Final question list {#d-questions}
The questionnaire plan above has seven questions. The design re-check against the interview added three, because the client named allergies as a deciding factor (Q10) and the animal records already held whether an animal can live with other pets and how much experience it needs. The final questionnaire has **10 questions in 4 sections**, one per screen:

@widths 0.9 2.1 1.6 1.7 1.4
| Section | Question (stored as) | Input | Validation | Used by |
|---|---|---|---|---|
| Your home | Living space (housing_level) | 3 cards | 1, 2 or 3 | housing |
| Your home | Garden access (garden_access) | Yes / No cards | 0 or 1 | garden |
| Your household | Children at home (has_children) | Yes / No cards | 0 or 1 | children |
| Your household | Other pets at home (other_pets) | Yes / No cards | 0 or 1 | other_pets |
| Your household | Allergies (allergies) | Tick dog, cat, rabbit, or none | Each species at most once | allergy cap |
| Your lifestyle | Activity you can offer (activity_level) | 3 cards | 1, 2 or 3 | activity |
| Your lifestyle | Hours alone on a normal day (hours_alone) | Number box, starts empty | Whole number 0 to 24 | hours_alone |
| Your lifestyle | Experience (experience) | 3 cards | first-time, some, experienced | experience |
| Your preferences | Preferred species (preferred_species) | 4 cards | Dog, Cat, Rabbit or No preference | ranking bonus |
| Your preferences | Preferred size (preferred_size) | 4 cards | Small, Medium, Large or No preference | ranking bonus |

Card buttons are used instead of the dropdowns preferred in requirement 6, because every choice is visible at once and large enough to tap on a tablet (SC16); requirement 6's aim, a suitable input for each question, is kept.

@design questionnaire | Annotated design: one question per screen with card answers and progress | fig-design-q
@design matches | Annotated design: ranked matches with met and not-met reasons | fig-design-matches

## 2.7 Validation rules {#d-validation}
Every input is checked in one place (`validation.py`) before it reaches the database, and the same rule is repeated as a database constraint. The rules below are exact; each is tested with normal, boundary and invalid data in the development test plan.

@widths 1.5 2.6 2.6 0.9
| Input | Rule | Message shown | Tests |
|---|---|---|---|
| Name (person) | Required; 2 to 50 characters; letters, spaces, hyphens and apostrophes only | "Enter a name." / "Name must be 2 to 50 characters." / "Name can only use letters, spaces, hyphens and apostrophes." | T1.1, T1.8 |
| Email | Required; the form name@domain.xx; stored in lower case; not already used | "Enter a valid email address, like name@domain.com." / "An account with this email already exists." | T1.2, T1.3 |
| Age (person) | Whole number 18 to 120 | "You must be 18 or over to adopt." / "Age must be between 18 and 120." | T1.4 |
| Password | At least 8 characters; confirm box filled and equal | "Password must be at least 8 characters." / "Type your password again to confirm it." / "The two passwords do not match." | T1.5 to T1.7 |
| Login | Both boxes filled (presence only); then one message for any wrong detail | "Enter your email address." / "Enter your password." / "Incorrect email or password." | T1.9, T1.10 |
| Animal name | As person names, but digits allowed ("R2") | As above, "(and numbers)" | T2.2 |
| Breed | Required; 2 to 50 characters; contains a letter | "Enter a breed (use 'Mixed' if unknown)." | T2.2 |
| Animal age | Whole number 1 to 30 | "Age must be between 1 and 30." | T2.3 |
| Species, sex, size, status | One of the fixed lists | "Choose a species." (and so on) | T2.4 |
| Exercise needs, minimum housing | 1 to 3 | "… must be between 1 and 3." | T2.5 |
| Hours alone (animal and adopter) | Whole number 0 to 24 | "Hours alone must be between 0 and 24." | T2.5, T4.2 |
| Experience needed | 0 to 2 | "… must be between 0 and 2." | T2.5 |
| Personality; medical notes | Personality required; both at most 500 characters | "Describe the animal's personality." / "… at most 500 characters." | T2.6 |
| Photo | PNG or JPG, at most 2 MB | "Images must be PNG or JPG." / "Images must be 2 MB or smaller." | T2.10, T2.6 |
| Questionnaire answers | Each answer in its range (final question list); Next disabled until answered | "Choose …" / "Answer yes or no for …" | T4.1 to T4.6 |
| Search box | At most 20 characters; used only as data | none (no results) | T3.3, R1 |

```Pseudocode D10: the shared checks every validator uses
FUNCTION check_range(value, low, high, field, label, errors)
    number ← whole number in value, or NULL
    IF number = NULL THEN
        errors[field] ← label + " is required." IF value is blank ELSE label + " must be a whole number."
    ELSE IF number < low OR number > high THEN
        errors[field] ← label + " must be between " + low + " and " + high + "."
    ENDIF
    RETURN number
ENDFUNCTION

FUNCTION validate_registration(name, email, age, password, confirm)
    errors ← {}
    check_name(name, errors);  check_email(email, errors);  check_range(age, 18, 120, "age", "Age", errors)
    IF password is blank THEN errors["password"] ← "Enter a password."
    ELSE IF LENGTH(password) < 8 THEN errors["password"] ← "Password must be at least 8 characters."
    IF confirm is blank THEN errors["confirm"] ← "Type your password again to confirm it."
    ELSE IF confirm ≠ password THEN errors["confirm"] ← "The two passwords do not match."
    RETURN errors                            // empty means valid; each message shows under its box
ENDFUNCTION
```

`validate_animal` (staff form) and `validate_answers` (questionnaire) follow the same pattern with the rules in the table.

## 2.8 Usability features {#d-usability}
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

## 2.9 Development test plan {#d-testplan}
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

## 2.10 Post-development test plan {#d-postplan}
After development is finished, the complete system is tested against **each success criterion** (P1 to P16). This plan is linked to the development tests: the third column shows which T tests are re-run as part of each P test, so the evidence on [[e-results]] is the final build passing them all again, plus the extra checks that only make sense on the finished system.

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
