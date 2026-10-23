"""Text for the model NEA write-up (used by build_nea_opus.py). Pseudocode uses the Design's variable names."""

PSEUDO_REGISTER = """\
FUNCTION Register(user_name, email, age, password, confirm_password)
    errors ← empty dictionary                       // field name → message
    user_name ← TRIM(user_name)
    IF user_name = "" THEN
        errors["name"] ← "Enter a name."
    ELSE IF LENGTH(user_name) < 2 OR LENGTH(user_name) > 50 THEN
        errors["name"] ← "Name must be 2 to 50 characters."
    ELSE IF user_name has a character that is not a letter, space, hyphen or apostrophe THEN
        errors["name"] ← "Name can only use letters, spaces, hyphens and apostrophes."
    ENDIF
    email ← LOWER(TRIM(email))
    IF email = "" THEN
        errors["email"] ← "Enter an email address."
    ELSE IF email does not match  text "@" text "." letters  THEN
        errors["email"] ← "Enter a valid email address, like name@domain.com."
    ENDIF
    IF age is blank THEN
        errors["age"] ← "Age is required."
    ELSE IF age is not a whole number THEN
        errors["age"] ← "Age must be a whole number."
    ELSE IF age < 18 THEN
        errors["age"] ← "You must be 18 or over to adopt."
    ELSE IF age > 120 THEN
        errors["age"] ← "Age must be between 18 and 120."
    ENDIF
    IF TRIM(password) = "" THEN
        errors["password"] ← "Enter a password."
    ELSE IF LENGTH(password) < 8 THEN
        errors["password"] ← "Password must be at least 8 characters."
    ELSE IF password ≠ confirm_password THEN
        errors["confirm"] ← "The two passwords do not match."
    ENDIF
    IF errors is empty AND EmailExists(email) THEN       // SELECT 1 FROM users WHERE email = ?
        errors["email"] ← "An account with this email already exists."
    ENDIF
    IF errors is not empty THEN
        RETURN NULL, errors                              // page shows all messages in one box
    ENDIF
    salt ← 16 random bytes
    password_hash ← "scrypt$16384$8$1$" + HEX(salt) + "$" + HEX(SCRYPT(password, salt))
    user_id ← INSERT INTO users (name, email, age, password_hash, role, created_at)
                VALUES (?, ?, ?, ?, 'user', NOW())        // parameterised
    RETURN user, empty dictionary
ENDFUNCTION"""

PSEUDO_LOGIN = """\
FUNCTION Login(login_email, login_password)
    login_email ← LOWER(TRIM(login_email))
    IF login_email = "" OR login_password = "" THEN
        RETURN NULL, "Enter your email address." / "Enter your password."
    ENDIF
    record ← SELECT * FROM users WHERE email = ?          // login_email bound, never joined into SQL
    is_authenticated ← FALSE
    IF record ≠ NULL THEN
        salt, stored_digest ← SPLIT(record.password_hash)
        is_authenticated ← CONSTANT_TIME_EQUAL(SCRYPT(login_password, salt), stored_digest)
    ENDIF
    IF NOT is_authenticated THEN
        error_message ← "Incorrect email or password."    // same message: no hint which part was wrong
        RETURN NULL, error_message
    ENDIF
    CLEAR session
    session.user_id ← record.user_id
    RETURN record, empty dictionary
ENDFUNCTION

FUNCTION CurrentUser()                                  // runs at the top of every page
    IF session.user_id is not set THEN
        RETURN NULL
    ENDIF
    RETURN SELECT * FROM users WHERE user_id = session.user_id
ENDFUNCTION                                             // user_role is re-read on every page

FUNCTION RequireStaff()                                 // the session/role check
    user ← CurrentUser()
    IF user = NULL THEN
        SHOW "Please log in or register to use this page." and a login link
        STOP page
    ELSE IF user.user_role ≠ "admin" THEN
        SHOW "This page is for shelter staff only."
        STOP page
    ENDIF
    RETURN user
ENDFUNCTION

PROCEDURE Logout()
    CLEAR session                                       // user_id and any half-finished questionnaire
    GO TO Home
ENDPROCEDURE"""

PSEUDO_ADMIN = """\
FUNCTION ValidateAnimal(form)
    errors ← empty dictionary
    name ← TRIM(form.name)
    IF name = "" OR LENGTH(name) NOT IN 2..50 OR name has no letter
       OR name has a character other than letters, digits, spaces, ' and - THEN
        errors["name"] ← message
    ENDIF
    IF form.species NOT IN ["Dog", "Cat", "Rabbit"] THEN errors["species"] ← "Choose a species."
    breed ← TRIM(form.breed)
    IF breed = "" OR LENGTH(breed) NOT IN 2..50 OR breed has no letter THEN errors["breed"] ← message
    IF form.age is not a whole number OR form.age NOT IN 1..30 THEN errors["age"] ← message
    IF form.sex NOT IN ["Male", "Female", "Unknown"] THEN errors["sex"] ← "Choose a sex."
    IF form.size NOT IN ["Small", "Medium", "Large"] THEN errors["size"] ← "Choose a size."
    IF TRIM(form.personality) = "" OR LENGTH > 500 THEN errors["personality"] ← message
    IF form.exercise_needs NOT IN 1..3 THEN errors["exercise_needs"] ← message
    IF form.min_housing_level NOT IN 1..3 THEN errors["min_housing_level"] ← message
    IF form.garden_required NOT IN [Yes, No] THEN errors["garden_required"] ← message
    IF form.child_compatible NOT IN [Yes, No] THEN errors["child_compatible"] ← message
    IF form.max_hours_alone NOT IN 0..24 THEN errors["max_hours_alone"] ← message
    IF LENGTH(form.medical_notes) > 500 THEN errors["medical_notes"] ← message
    RETURN cleaned values, errors
ENDFUNCTION

FUNCTION StoreUpload(upload)                            // optional photo
    IF upload = NULL THEN RETURN NULL
    IF EXTENSION(upload.name) NOT IN ["png", "jpg", "jpeg"] THEN RETURN "Images must be PNG or JPG."
    IF upload.size > 2 MB THEN RETURN "Images must be 2 MB or smaller."
    safe_name ← RANDOM_HEX(32) + "." + EXTENSION(upload.name)   // never the user's file name
    WRITE upload TO "data/uploads/" + safe_name
    form.image_path ← "data/uploads/" + safe_name
    RETURN NULL
ENDFUNCTION

FUNCTION AddAnimal(actor, form)
    IF actor = NULL OR actor.user_role ≠ "admin" THEN RAISE AccessDenied   // checked again here, not only on the page
    values, errors ← ValidateAnimal(form)
    IF errors is not empty THEN RETURN NULL, errors
    animal_id ← INSERT INTO animals (...14 fields..., date_added) VALUES (?, ?, ...)
    RETURN animal_id, empty dictionary
ENDFUNCTION

FUNCTION EditAnimal(actor, animal_id, form)
    IF actor.user_role ≠ "admin" THEN RAISE AccessDenied
    values, errors ← ValidateAnimal(form)
    IF errors is not empty THEN RETURN errors
    rows ← UPDATE animals SET name = ?, ... WHERE animal_id = ?
    IF rows = 0 THEN RETURN {"animal": "That animal no longer exists."}
    RETURN empty dictionary
ENDFUNCTION

FUNCTION DeleteAnimal(actor, animal_id, confirmed)
    IF actor.user_role ≠ "admin" THEN RAISE AccessDenied
    IF NOT confirmed THEN RETURN                         // Delete button disabled until the box is ticked
    DELETE FROM animals WHERE animal_id = ?              // its stored match results go too (CASCADE)
ENDFUNCTION"""

PSEUDO_MENU = """\
// streamlit_app.py runs first on every page load
PROCEDURE BuildMenu()
    PrepareDatabaseOnce()                               // create tables and demo animals if missing
    user ← CurrentUser()
    pages ← [Home, Animals, Animal profile (hidden), Questionnaire, My matches]
    IF user = NULL THEN
        APPEND "Log in" TO pages
    ELSE
        APPEND "My account" TO pages
    ENDIF
    IF user ≠ NULL AND user.user_role = "admin" THEN
        APPEND "Manage animals" TO pages                // the staff page does not exist for anyone else
    ENDIF
    selected_page ← page chosen in the top menu (Home by default)
    RUN selected_page
ENDPROCEDURE

PROCEDURE HomePage()
    SHOW title, purpose and "Scores are guidance only. Shelter staff make the final decision."
    IF "Start the questionnaire" clicked THEN GO TO Questionnaire
    animal_results ← SELECT * FROM animals
    FOR species IN ["Dog", "Cat", "Rabbit"]
        SHOW COUNT of animal_results with that species
    NEXT species
    IF CurrentUser() = NULL THEN SHOW link "Log in or register"
ENDPROCEDURE

PROCEDURE MyMatchesPage()
    user ← RequireLogin()
    latest ← SELECT newest response FROM questionnaire_responses WHERE user_id = ?
    IF latest = NULL THEN                               // questionnaire not completed yet
        SHOW "You haven't completed the questionnaire yet." and a link to it
        STOP
    ENDIF
    results ← stored match_results for latest, ORDER BY rank
    SHOW first MAX(4, 5) results (all of them if "Show every animal" is on)
ENDPROCEDURE"""

PSEUDO_BROWSE = """\
PROCEDURE AnimalViewingPage()
    species_filter ← drop-down: All species / Dog / Cat / Rabbit
    size_filter ← drop-down: All sizes / Small / Medium / Large
    search_term ← text box (at most 20 characters)
    animal_results ← ListAnimals(species_filter, size_filter, search_term)
    no_results ← LENGTH(animal_results) = 0
    IF no_results THEN SHOW "No animals match those filters."
    FOR EACH animal IN animal_results                   // 4 cards per row
        SHOW card: image, name, species, breed, age, "View profile" button
        IF "View profile" clicked THEN
            selected_animal_id ← animal.animal_id
            GO TO ProfilePage(id = selected_animal_id, back = "browse")
        ENDIF
    NEXT animal
ENDPROCEDURE

FUNCTION ListAnimals(species_filter, size_filter, search_term)
    sql ← "SELECT * FROM animals WHERE 1 = 1"
    params ← empty list
    IF species_filter chosen THEN sql ← sql + " AND species = ?"; APPEND species_filter TO params
    IF size_filter chosen THEN sql ← sql + " AND size = ?"; APPEND size_filter TO params
    search_term ← TRIM(search_term)
    IF search_term ≠ "" THEN                            // empty search = show every animal
        sql ← sql + " AND (name LIKE ? OR breed LIKE ?)"
        APPEND "%" + search_term + "%" TO params (twice)  // the text is data, never part of the SQL
    ENDIF
    RETURN EXECUTE(sql + " ORDER BY species, name", params)
ENDFUNCTION

PROCEDURE ProfilePage(id, back)
    SHOW link "Back to animals" (or "Back to my matches" if back = "results")
    IF id is not a whole number THEN animal ← NULL ELSE animal ← SELECT * FROM animals WHERE animal_id = ?
    IF animal = NULL THEN SHOW "That animal could not be found. It may have been adopted."; STOP
    SHOW image, name, species, breed, age, sex, size, personality, medical needs
    SHOW needs: exercise level, minimum home, garden, children, maximum hours alone
ENDPROCEDURE"""

PSEUDO_MATCH = """\
CONSTANT WEIGHTS ← {hours_alone: 20, children: 15, housing: 15, activity: 12, garden: 10}   // total 72
CONSTANT IMPORTANT ← {hours_alone, children, housing}    // unmet → warning

FUNCTION ScoreAnimal(animal, answers)
    total_score ← 0
    met ← empty list; unmet ← empty list; warnings ← empty list
    fraction["hours_alone"] ← 1 IF answers.hours_alone ≤ animal.max_hours_alone ELSE 0
    fraction["children"]    ← 1 IF animal.child_compatible OR NOT answers.has_children ELSE 0
    fraction["housing"]     ← 1 IF answers.housing_level ≥ animal.min_housing_level ELSE 0
    gap ← MAX(0, animal.exercise_needs − answers.activity_level)
    fraction["activity"]    ← MAX(0, 1 − gap / 2)          // 1, 0.5 or 0
    fraction["garden"]      ← 1 IF answers.garden_access OR NOT animal.garden_required ELSE 0
    FOR EACH factor IN WEIGHTS
        total_score ← total_score + WEIGHTS[factor] × fraction[factor]
        IF fraction[factor] = 1 THEN
            APPEND reason TO met
        ELSE
            APPEND reason TO unmet
            IF factor IN IMPORTANT THEN APPEND reason TO warnings
        ENDIF
    NEXT factor
    compatibility_score ← ROUND(100 × total_score / 72, 1)
    IF compatibility_score ≥ 80 THEN match_category ← "Strong"
    ELSE IF compatibility_score ≥ 60 THEN match_category ← "Good"
    ELSE IF compatibility_score ≥ 40 THEN match_category ← "Possible"
    ELSE match_category ← "Low"
    ENDIF
    bonus ← 0                                           // preferences order the list but never change the %
    IF answers.preferred_species = animal.species THEN bonus ← bonus + 10
    IF answers.preferred_size = animal.size THEN bonus ← bonus + 5
    RETURN compatibility_score, match_category, bonus, met, unmet, warnings
ENDFUNCTION

FUNCTION RankAnimals(animal_results, answers)
    results ← empty list
    FOR EACH animal IN animal_results
        APPEND ScoreAnimal(animal, answers) TO results
    NEXT animal
    SORT results BY, in order:
        1. animals with no warnings first
        2. (compatibility_score + bonus), highest first
        3. compatibility_score, highest first
        4. name A-Z, then animal_id                     // ties always come out in the same order
    RETURN results
ENDFUNCTION

FUNCTION SubmitQuestionnaire(user, raw_answers)
    answers, errors ← ValidateAnswers(raw_answers)
    IF errors is not empty THEN RETURN errors           // nothing is saved
    response_id ← INSERT INTO questionnaire_responses (...) VALUES (?, ...)
    results ← RankAnimals(SELECT * FROM animals, answers)
    DELETE FROM match_results WHERE response_id = ?
    calculated_at ← NOW()
    FOR rank ← 1 TO LENGTH(results)
        INSERT INTO match_results (response_id, animal_id, rank, compatibility, category, bonus,
                                   met, unmet, warnings, calculated_at) VALUES (?, ...)
    NEXT rank
    GO TO My matches
ENDFUNCTION"""

PSEUDO_QUESTIONNAIRE = """\
CONSTANT QUESTION_STEPS ← [
    ("Your home",        [housing_level, garden_access]),
    ("Your household",   [has_children, other_pets]),
    ("Your lifestyle",   [activity_level, hours_alone, experience]),
    ("Your preferences", [preferred_species, preferred_size]) ]

PROCEDURE QuestionnairePage()
    user ← RequireLogin()
    step ← session.q_step (0 if not set)
    answers ← session.q_answers (empty if not set)
    IF step < 4 THEN
        SHOW progress "Step (step + 1) of 5" and the questions of QUESTION_STEPS[step] as drop-downs
        IF "Back" clicked AND step > 0 THEN session.q_step ← step − 1
        IF "Next" clicked THEN
            errors ← ValidateStep(step, answers)
            IF errors is empty THEN session.q_step ← step + 1 ELSE SHOW errors
        ENDIF
    ELSE
        SHOW every question with its answer        // review step
        IF "Change answers" clicked THEN session.q_step ← 0
        IF "Submit and see my matches" clicked THEN SubmitQuestionnaire(user, answers)
    ENDIF
ENDPROCEDURE

FUNCTION ValidateStep(step, answers)
    errors ← empty dictionary
    FOR EACH question IN QUESTION_STEPS[step]
        CHECK answers[question] with that question's rule:
            housing_level, activity_level: one of 1, 2, 3
            garden_access, has_children, other_pets: Yes or No
            hours_alone: whole number 0 to 24
            experience: one of the three listed levels
            preferred_species: Dog, Cat, Rabbit or No preference
            preferred_size: Small, Medium, Large or No preference
        IF it fails THEN errors[question] ← that question's message
    NEXT question
    RETURN errors
ENDFUNCTION

FUNCTION ValidateAnswers(answers)                   // all nine questions again before saving
    errors ← ValidateStep(0) ∪ ValidateStep(1) ∪ ValidateStep(2) ∪ ValidateStep(3)
    IF errors is empty THEN RETURN Answers(answers), errors ELSE RETURN NULL, errors
ENDFUNCTION"""

# (feature, where, why with her research codes)
USABILITY = [
    ("Calm colour scheme from one theme file (green, cream, dark text)", "Every page",
     "Survey and examples asked for a calm, clean look (S6, E1-E3). One theme file means every page matches (criterion 1.4)."),
    ("The same top menu on every page, showing only the pages the user may open", "Every page",
     "All three example sites keep one menu (E1-E3, S6). Hiding the staff page from adopters avoids a confusing 'no access' link (Q12)."),
    ("Questionnaire in four short steps plus a review step, with a progress bar", "Questionnaire",
     "E3 and S6: long forms put people off. The progress bar shows how much is left; the review step lets users check before submitting."),
    ("Drop-downs for every answer (no typing)", "Questionnaire, filters, staff form",
     "E3, S6: quicker on a tablet, and the answer can only be one of the allowed values, so fewer errors (Q15)."),
    ("All errors for a form shown together in one red box, in plain words", "Register, log in, questionnaire, staff form",
     "Q12, S6: users should see everything to fix at once instead of one message per attempt."),
    ("Compact animal cards (photo, name, species, breed, age, 'View profile')", "Animals, Home",
     "Q2, E1, E2: the examples use cards; the card holds the five facts adopters said they check first."),
    ("Score bar, category word and met / not met list on each match", "My matches",
     "Q3, E3: the client wants adopters to see why an animal suits them, not just a number."),
    ("Orange warning when an important need (time alone, children, space) is not met", "My matches",
     "Q3: welfare first. The warning cannot be missed and these animals are listed after the safer matches."),
    ("'Guidance only: staff make the final decision' note", "Home, My matches", "Q3: sets the right expectation."),
    ("Delete needs a tick-box confirmation; the button is disabled until then", "Staff area",
     "Q5: deleting is permanent, so a slip of the mouse must not remove an animal."),
    ("Back links that return to where the user came from", "Animal profile",
     "S6, E1-E3: a profile opened from the results goes back to the results, not to the start."),
]

FURTHER = [
    ("Stay logged in after a page reload", "Store a signed, expiring token in a browser cookie and check it in CurrentUser(); "
     "Streamlit has no built-in sign-in cookie, so this needs a small extra package or a reverse proxy."),
    ("Animal status (Available / Reserved / Adopted)", "Add a status column; browse and matching only use Available "
     "animals; staff change status instead of deleting, so match history and records are kept."),
    ("Separate staff entrance", "A 'Staff login' page that only accepts admin accounts, to meet requirement 8.1 to the letter."),
    ("Score other pets and experience", "Add 'good with other animals' and 'suits first-time owners' to each animal, then "
     "two more weighted factors; the weights table and tests change, nothing else does."),
    ("Password reset and login limits", "Email a one-time link (needs an email service); lock an account for a few minutes "
     "after 5 wrong passwords."),
    ("More than one shelter", "A shelters table and a shelter_id on animals and staff, so each shelter manages only its own animals."),
    ("User testing", "Run the planned usability tests U1-U5 with five adopters and the shelter client and record their ratings."),
]
