@part S Development
# 3 Development and testing to inform development {#development}

## 3.1 How development was organised {#s-method}
PawMatch was built iteratively, one component at a time, in the order of the decomposition on [[d-decomp]]. Every stage follows the same cycle, and every stage ends with a working, tested program saved as a Git commit:

1. **Aim:** what the stage builds and which design pages and success criteria it covers.
2. **Build:** the code, with annotated excerpts and screenshots.
3. **Test to inform development:** the T tests from the plan on [[d-testplan]], run with pytest. Any failure is shown with its cause, the fix and the retest.
4. **Client feedback:** the client reviews the stage's screens and answers my questions.
5. **Changes:** what I changed because of the feedback, and what I decided not to change and why.
6. **Development assessment:** what now works, what does not yet, and what the next stage must do.

@widths 0.6 2.4 2.6 1.1
| Stage | Built | Commits | Saved test run at the end of the stage |
|---|---|---|---|
| P1 | First working prototype on the tested engine | `ffd0ad5`, `10e84e7`, `b76527c` | 73 engine tests (`stage1-pytest.txt`), then 117 with the first page tests (`stage3-pytest.txt`) |
| 1 | Accounts and login in her design | `847920a`, `f3d44f9` | 103 (`stage2-pytest.txt`: accounts, database and staff access added) |
| 2 | Staff animal management | `10e84e7`, `847920a` | 103 (same run: the staff rules were built with the accounts) |
| 3 | Home page, browse and profile | `847920a` | 117 (`stage3-pytest.txt`: page tests added) |
| 4 | Questionnaire | `e2f5c6a`, `69b2648` | run together with stage 5 |
| 5 | Matching and results, design re-check | `fdef5a0`, `e2f5c6a` | 134 (`stage5-pytest.txt`) |
| 6 | Accessibility audit and final checks | `5c09de3` | browser audit (`rendered-audit-*.json`) and 4 style tests |
| 7 | Changes from all the reviews; staying signed in after a reload | `77ef20a`, `b0e302a` | 191 (`review-pytest.txt`), then {{tests_total}} (`pytest-junit.xml`) |

The engine and the database were built and tested first, and her interface was then ported onto them in one commit (`847920a`). That is why stages 1 to 3 share a commit: each stage's own tests, failures and fixes are in its section.

### Program files {#s-files}
The finished program is split into the five components from the decomposition on [[d-decomp]]. The rules (`pawmatch/`) never import Streamlit, so they can be tested without a browser; the pages (`webui/`) call the rules but contain none.

@widths 1.6 0.5 3.4
| File | Lines | What it does |
|---|---|---|
| `streamlit_app.py` | 28 | Starts the app, prepares the database and lists the pages each role may open |
| `pawmatch/models.py` | 132 | The records (User, Animal, Answers, MatchResult) and the fixed answer scales |
| `pawmatch/validation.py` | 272 | Every validation rule V1 to V16 ([[d-validation]]) |
| `pawmatch/auth.py` | 109 | Registration, password hashing with scrypt, login |
| `pawmatch/matching.py` | 166 | Weights, scoring, warnings, allergy cap and ranking (D6) |
| `pawmatch/db.py` | 345 | The SQLite tables, all queries, sign-in tokens |
| `pawmatch/services.py` | 102 | Submitting a questionnaire: validate, score, store (D9) |
| `pawmatch/seed.py` | 146 | Demo animals and the first staff account |
| `webui/state.py` | 182 | Who is signed in, access checks, sign in and out |
| `webui/views/*.py` | 1,484 | One file per page: login, registration, home, browse, questionnaire, matches, account, admin |
| `webui/pawmatch_style.py` | 1,944 | Her pink design as one stylesheet |
| `tests/*.py` | {{tests_total}} tests | Unit, database, access and page tests run with pytest |

:::note How the client reviews were carried out
The client's answers in this section were produced by an AI model role-playing the client: it was given only the client interview from the analysis and the screenshots of each stage, and answered my questions in her voice. This was done because the client was not available for six separate review sessions. It is a limitation, discussed in the evaluation ([[e-limits]]) and logged in Appendix A ([[x-ai]]). The reviews were all held after the build, one per stage, so the changes they asked for were made together in stage 7 (commit `77ef20a`). They are reported under the stage they belong to so each stage's story is complete.
:::

## 3.2 Prototype 1: the engine with a plain interface {#s-proto1}
**Aim.** Before building the real pages, prove that the hardest parts work together: the database, validation, accounts and the weighted matching, with a plain Streamlit interface on top. The domain layer was written first with its tests (73 tests at commit `ffd0ad5`, 103 at `10e84e7`), then simple pages (117 tests at `b76527c`).

@img prototype-1/01-home.png | Prototype 1: plain home page in Streamlit's default style | 12 | key=fig-p1-home
@img prototype-1/10-results.png | Prototype 1: ranked results with a reason for each requirement (five factors at this point) | 12 | key=fig-p1-results crop=0-1300

:::fail Two failures in prototype 1
- **Every page test failed (9 of 9):** `FileNotFoundError: AppTest script not found at rebuild/tests/streamlit_app.py`. Cause: Streamlit's testing tool looks for the app file relative to the test file, not the folder the tests are run from.
- **A questionnaire test failed:** `assert (1 == 2)`. The test expected two error boxes for two unanswered questions; I had merged the messages into one box so the user sees one clear list.
:::

:::fix Fixes and retest
- The tests now build the absolute path to `streamlit_app.py` from the test file's own location. Retest: 9 of 9 passed.
- The test was changed to check for one box containing both messages, because one box is the better design. This is a change to the design's expected result, recorded here: the questionnaire later moved to one question per screen (stage 4), so T4.6 checks that Next stays disabled instead. Retest: passed (evidence `docs/evidence/stage3-fail1-apptest-path.txt`, `stage3-fail2-error-box.txt`).
:::

:::verdict Development assessment P1
**Working:** accounts, validation, the database, scoring and ranking, all tested. **Not right:** the interface looks nothing like my design or the client's request for a soft pink, friendly look (Q11), and it only scored five factors. **Decision:** keep the tested engine and rebuild every page in my own design (pink palette, Nunito font, card layout) on top of it, starting with login. Re-check the scoring design against the interview before the matching stage.
:::

## 3.3 Stage 1: accounts and login {#s-stage1}
**Aim.** Build the login and registration pages from my designs ([[d-login]]) on the tested account functions. Covers SC6 and SC7.

@code pawmatch/validation.py::validate_registration | every registration field is checked and each error is stored against its own field

@code pawmatch/auth.py::hash_password | passwords are stored as salted scrypt hashes, never as text

@img 01-login-desktop.png | Login page in her design, with the Log in / Create an account switch | 14 | key=fig-s1-login
@img 04-register-errors-desktop.png | Registration with every box left empty: a message appears under each box | 14 | key=fig-s1-errors

### Tests for stage 1 {#s-tests1}
@widths 0.5 2.6 3 0.6
| ID | Test | Automated test (pytest) | Result |
|---|---|---|---|
| T1.1 | Register a valid adopter | `test_valid_registration_is_cleaned`, `test_registration_creates_an_adopter_account_and_signs_it_in` | Pass |
| T1.2 | Required fields blank | `test_registration_rejects_blank_required_fields` (4 cases), `test_registration_reports_every_missing_field` | Pass |
| T1.3 | Email format | `test_registration_rejects_bad_email_format` (4 cases) | Pass |
| T1.4 | Age 17, 18, 120, 121, 2.5, abc | `test_registration_age_boundaries` (6 cases) | Pass |
| T1.5 | Password 7 and 8 characters | `test_password_minimum_length_boundary` | Pass |
| T1.6 | Confirm password | `test_password_confirmation_must_match`, `test_registration_reports_a_password_mismatch_under_confirm` | Pass |
| T1.7 | Duplicate email, different case | `test_register_rejects_duplicate_email_case_insensitively` | Pass after fix |
| T1.8 | Name format | `test_registration_name_is_letters_spaces_and_hyphens` (6 cases) | Pass |
| T1.9 | Correct login, both roles | `test_adopter_login_opens_the_home_page`, `test_staff_login_opens_the_dashboard` | Pass |
| T1.10 | Wrong password and unknown email | `test_wrong_password_and_unknown_email_give_the_same_message` and two page tests | Pass |

:::fail T1.7 failed when name checking was tightened
`KeyError: 'email'` in `test_register_rejects_duplicate_email_case_insensitively`. When the name rules were made stricter (letters, spaces, hyphens and apostrophes only), the test's sample name contained a digit, so registration stopped at the name error and never reached the duplicate-email check.
:::

:::fix Fix and retest
The sample data was corrected to a valid name so the test checks what it is meant to check, the duplicate email. Retest: passed; the whole suite was re-run to check nothing else had changed (evidence `stage5-fail-regression-auth.txt`).
:::

:::fail A real tester found a problem the tests did not
A person trying the live system created an account and was sent back to the login screen, so they thought sign-up had failed. The tests only checked that the account was stored.
:::

:::fix Fix and retest
A new account is now signed in straight away and taken to the home page (commit `f3d44f9`). The test was extended to check this: `test_registration_creates_an_adopter_account_and_signs_it_in` now asserts the user is signed in. Retest: passed.
:::

### Client feedback 1 {#s-feedback1}
@feedback 1

### Changes made after feedback 1 {#s-changes1}
:::change Changed
- **Blank confirm box now flagged.** If the confirm box is empty, it gets its own message, "Type your password again to confirm it." This changed the expected result of `test_registration_reports_every_missing_field`, which failed as expected (an extra `confirm_password` error, evidence `review-fail1-confirm-blank.txt`); the test was updated to the new requirement and passed.
- **Age rule written on the form.** The hidden "?" help icon was replaced with the visible line "You must be 18 or over to adopt." Test: `test_review1_age_rule_is_written_on_the_form`, passed.
:::

:::note Not changed, with reasons
- **Address and phone number fields.** The client mentioned these in the interview (Q9) and again here. I decided not to collect them: the matching never uses them, storing less personal data is safer (UK GDPR data minimisation), and the rescue collects them at the home visit. This is a partly met requirement in the evaluation.
- **Red outline on the box with the error.** Streamlit does not let a program colour a single input box, so the message under the box is used instead. Listed as future development.
:::

:::verdict Development assessment 1
**Working:** registration and login meet SC6 and SC7 in automated tests; new adopters are signed in straight away. **Next:** the staff side, because adopters need animal records to browse.
:::

## 3.4 Stage 2: staff animal management {#s-stage2}
**Aim.** Give staff a dashboard to add, edit and delete animals ([[d-admin]]), with every field validated and every action limited to staff. Covers SC12 and SC13.

@code pawmatch/auth.py::require_admin | the gate called first by every staff action

@code pawmatch/services.py::edit_animal | an edit is validated, then saved only if the animal still exists

@img 15-admin-overview-desktop.png | Staff dashboard: counts and records that need attention | 14 | key=fig-s2-overview
@img 17-admin-add-errors-desktop.png | Add-animal form submitted empty: a message for each missing field | 14 | key=fig-s2-add crop=0-1300

### Tests for stage 2 {#s-tests2}
@widths 0.5 2.6 3 0.6
| ID | Test | Automated test (pytest) | Result |
|---|---|---|---|
| T2.1 | Add, edit, delete as staff | `test_admin_can_add_edit_and_delete`, `test_staff_can_add_an_animal_and_then_delete_it` | Pass |
| T2.2 | Required fields blank | `test_staff_add_form_reports_missing_fields`, `test_admin_add_still_validates` | Pass |
| T2.3 | Age 0/31, hours −1/25 | `test_invalid_animal_fields_are_rejected` (age, hours cases) | Pass |
| T2.4 | Fixed lists | `test_invalid_animal_fields_are_rejected` (species, size, sex, exercise cases) | Pass |
| T2.5 | Photo type and size | `test_image_type_and_size` (4 cases) | Pass |
| T2.6 | Medical notes 501 characters | `test_invalid_animal_fields_are_rejected` (medical notes case) | Pass |
| T2.7 | Edit a deleted animal | `test_edit_of_deleted_animal_reports_error` | Pass |
| T2.8 | Adopter or signed-out user | `test_non_admins_are_refused_every_change` (2 cases), `test_admin_page_stops_adopters` | Pass |
| T2.9 | Delete removes stored results | `test_delete_removes_animal_and_its_stored_results` | Pass |
| T2.10 | Overview flags weak records | `test_profile_issues_flag_missing_photo_and_short_description` | Pass |
| T2.11 | Database rejects a bad row | `test_database_constraints_back_up_validation` | Pass |

The saved run at the end of this stage (`stage2-pytest.txt`) shows **103 passed, 0 failed**. No failure was recorded in this stage beyond those shown above, because the staff rules were built on the account functions already tested in stage 1.

### Client feedback 2 {#s-feedback2}
@feedback 2

### Changes made after feedback 2 {#s-changes2}
:::change Changed
- **Table columns sized to fit.** The ID, Age, Status, Profile and Added columns are now narrow so the table fits a laptop screen and "Added" is no longer cut off.
- **Clearer label.** "Read-only table" was replaced by "Pick a record below to edit or delete it", which tells staff what to do.
:::

:::note Not changed, with reasons
- **A Cancel button on the form.** Leaving the page already discards the form; listed as future development.
- **Red outline on the box with the error.** Same Streamlit limitation as stage 1.
:::

@img 16-admin-manage-desktop.png | Staff table after the change: every column fits | 14 | key=fig-s2-manage crop=0-1100

:::verdict Development assessment 2
**Working:** SC12 and SC13 pass their automated tests; adopters cannot reach any staff action even by calling the functions directly. **Next:** the adopter pages that show these records.
:::

## 3.5 Stage 3: home page, browse and profile {#s-stage3}
**Aim.** Build the home page, the browse page with filters and the profile page ([[d-browse]]). Covers SC3, SC4 and SC5.

@code pawmatch/db.py::list_animals | filters are added as `?` parameters, so search text can never run as SQL

@img 06-home-desktop.png | Home page: what PawMatch does and that staff make the decision | 14 | key=fig-s3-home
@img 07-browse-desktop.png | Browse: a card for each available animal, with species, size and search filters | 14 | key=fig-s3-browse crop=0-1250
@img 08-profile-desktop.png | Profile: all of the animal's details and needs | 14 | key=fig-s3-profile

### Tests for stage 3 {#s-tests3}
@widths 0.5 2.6 3 0.6
| ID | Test | Automated test (pytest) | Result |
|---|---|---|---|
| T3.1 | Every Available animal has a card | `test_browse_shows_a_card_for_every_available_animal` | Pass |
| T3.2 | Species, size and search filters | `test_filters_by_species_size_and_search`, `test_review3_size_filter_narrows_the_list` | Pass |
| T3.3 | Search text is data | `test_search_text_is_treated_as_data_not_sql` | Pass |
| T3.4 | Profile shows needs | `test_view_profile_opens_the_animal_with_its_needs` | Pass |
| T3.5 | Signed-out visitor | `test_adopter_pages_send_visitors_to_log_in` | Pass |

The saved run at the end of this stage (`stage3-pytest.txt`) shows **117 passed, 0 failed**. The two failures saved as `stage3-fail1-apptest-path.txt` and `stage3-fail2-error-box.txt` came from the first page tests and are shown with their fixes under prototype 1 (page [[s-proto1]]); no other failure was recorded in this stage.

### Client feedback 3 {#s-feedback3}
@feedback 3

### Changes made after feedback 3 {#s-changes3}
:::change Changed
- **Size filter added** next to species (the client asked for "type of animal and size" in Q8 too). Test `test_review3_size_filter_narrows_the_list`, passed.
- **"Take the questionnaire" button on the profile** in place of a sentence, so the next step is one click. Test `test_review3_profile_offers_the_questionnaire_as_a_button`, passed.
- **Home page says people decide:** "PawMatch suggests, people decide… the shelter team meets you, checks your home and makes the final decision." Test `test_review3_home_says_staff_make_the_decision`, passed.
:::

:::verdict Development assessment 3
**Working:** SC3 to SC5. **Next:** the questionnaire, which the browse and profile pages now point to.
:::

## 3.6 Stage 4: questionnaire {#s-stage4}
**Aim.** One question per screen in four sections, with card answers and Next disabled until a question is answered ([[d-matching]]). Covers SC8. While building it, the design re-check (next stage) added three questions, so the questionnaire has ten.

@code pawmatch/validation.py::validate_answers | the whole questionnaire is checked again on submit, so nothing incomplete is ever stored

@img 09-questionnaire-desktop.png | Question 1 of 10: card answers, progress and section name | 14 | key=fig-s4-q1
@img 10b-questionnaire-allergies-desktop.png | The allergies question allows several answers; "No allergies" clears the others | 14 | key=fig-s4-allergy

### Tests for stage 4 {#s-tests4}
@widths 0.5 2.6 3 0.6
| ID | Test | Automated test (pytest) | Result |
|---|---|---|---|
| T4.1 | Next waits for an answer | `test_questionnaire_waits_for_an_answer_before_next`, `test_step_validation_only_checks_that_step` | Pass |
| T4.2 | Hours −1, 0, 24, 25 | `test_hours_alone_range` (4 cases) | Pass |
| T4.3 | Allergies | `test_allergies_accept_none_or_some_species_in_a_fixed_order` (5), `test_allergies_reject_…` (4) | Pass |
| T4.4 | "No allergies" clears others | `test_allergy_cards_turn_on_and_off_and_no_allergies_clears_them` | Pass |
| T4.5 | Complete questionnaire | `test_questionnaire_completes_and_ranks_every_available_animal`, `test_adopter_submission_stores_ranked_results` | Pass |
| T4.6 | Incomplete submission | `test_unanswered_question_blocks_submission`, `test_incomplete_submission_saves_nothing` | Pass |

### Client feedback 4 {#s-feedback4}
@feedback 4

### Changes made after feedback 4 {#s-changes4}
:::fail New test failed: the hours question was already filled in
The client noticed the hours box already showed 0, so someone could press Next without thinking. I wrote the test first: `test_review4_hours_question_starts_empty` failed with `assert (0 is None)` (evidence `review-fail2-hours-prefilled.txt`). Cause: the function that sets up the answers gave the typed question a starting value of 0.
:::

:::fix Fix and retest
Every answer now starts empty (`None`); the hours box shows the hint "Type a number from 0 to 24" and Next stays disabled until a number is typed. Retest: passed, and the full suite still passed.
:::

@img 10-questionnaire-hours-desktop.png | After the change: the hours box starts empty with a hint | 14 | key=fig-s4-hours

:::note Not changed, with reasons
- **"No allergies" behaviour.** It already cleared the other answers (T4.4); the review was looking at a screenshot taken before a card was clicked.
- **Number of matches on the "done" screen, and fainter disabled buttons.** Not done in time; both are in the evaluation.
:::

:::verdict Development assessment 4
**Working:** SC8 in automated tests (the timing part is measured in the evaluation). **Next:** use the answers to score and rank.
:::

## 3.7 Stage 5: matching and results {#s-stage5}
**Aim.** Score and rank every available animal and show each result with its reasons ([[d-score-pseudo]]). Covers SC9, SC10 and SC11.

### Design re-check before building {#s-recheck}
Before building this stage I checked the design against every interview answer again. Three things the client said were missing from my five-factor plan:

| Client said | Missing from the plan | Change |
|---|---|---|
| "If someone is allergic to cats, they should not be strongly matched with a cat" (Q10) | No allergy question | New multiple-choice question; an allergy caps the score at 39% (Low) and adds a warning |
| Animals "get along with children or other pets" (Q2, Q10 summary) | Other pets not scored | New question and factor, weight 10, warns if unmet |
| People forget "whether they have experience" (Q1) | Experience not scored | New question and factor, weight 8, half points for one level short |

The re-check also found two smaller gaps, each shown by a test written first that failed: match results did not record *when* they were calculated (`no such column: calculated_at`), and animal names accepted symbols (`assert ('name' not in {}) is False`). Both were fixed, with an automatic upgrade that adds the column to older database files (R5) (evidence `stage5-fail-design-recheck.txt`, then 134 passed).

### Final weights {#s-weights}
@weights

### Worked example: checking the program by hand {#s-worked}
An adopter in a flat with limited space and no garden, with children and another pet, some experience, activity level 1, out 6 hours a day, preferring a cat. Oscar is a dog who needs activity level 2 and can be left for at most 4 hours.

@worked Oscar

So Oscar scores **{{worked_Oscar}}** (Good) but has {{worked_Oscar_warnings}} welfare warning, because 6 hours alone is more than his 4. The ranking rule puts every animal *without* a warning above him, even though his percentage is higher than some of them: this is the client's rule that a welfare risk must not be presented as a top match (Q3). The automated test `test_worked_example_in_the_write_up_matches_the_program` checks that the program gives exactly this result (T5.8).

@code pawmatch/matching.py::score_animal | each factor adds its weight times the fraction met; the allergy cap is applied last

@code pawmatch/matching.py::rank_key | the sort key: animals without warnings first, then points, then a fixed tie-break

@img 12-matches-desktop.png | My matches: score key, ranked cards, met and not-met reasons, welfare warnings | 14 | key=fig-s5-matches crop=0-1500

### Tests for stage 5 {#s-tests5}
@widths 0.5 2.6 3 0.6
| ID | Test | Automated test (pytest) | Result |
|---|---|---|---|
| T5.1 | Perfect match | `test_perfect_match_scores_100` | Pass |
| T5.2 | Each factor loses its weight | `test_each_factor_loses_its_weight` (10 cases) | Pass |
| T5.3 | Boundaries count as met | `test_boundaries_count_as_met` | Pass |
| T5.4 | Category thresholds | `test_category_thresholds` (8 cases) | Pass |
| T5.5 | Important factor warns | `test_important_unmet_requirements_raise_warnings`, `test_garden_and_activity_shortfalls_do_not_warn` | Pass |
| T5.6 | Allergy | `test_an_allergy_caps_the_score_in_the_low_band_and_warns_first` and 3 more | Pass |
| T5.7 | Ranking order | `test_unsuitable_animals_always_rank_after_suitable`, `test_preferences_change_rank_but_not_percentage` | Pass |
| T5.8 | Hand calculation | `test_worked_example_in_the_write_up_matches_the_program` | Pass |
| T5.9 | Results page | `test_matches_page_shows_the_top_five_and_can_show_all` | Pass |
| T5.10 | Empty and identical lists | `test_ranking_empty_list`, `test_ranking_is_deterministic_for_identical_animals` | Pass |

### Client feedback 5 {#s-feedback5}
@feedback 5

### Changes made after feedback 5 {#s-changes5}
:::change Changed
- **Welfare warnings stand out.** Unmet welfare needs now appear first, in a red box headed "Welfare needs your home may not meet: talk to the shelter first". The amber "Requirements not met" box appears only when there is something in it; when everything is met, a green box says so.
- **The order is explained.** A line appears once, above the first animal with a warning, saying these animals are listed after the others even if their score is higher. This answers the client's worry that ranking "ignored" warnings: it did not, but it did not say so.
- **Score key** under the heading: "Strong 80% or more · Good 60 to 79% · Possible 40 to 59% · Low under 40%", with "the shelter team… makes the final decision".
- **Update answers from My account.** Test `test_review5_account_lets_answers_be_updated`, passed. Test for the first three: `test_review5_matches_explain_the_score_and_the_order`, passed.
:::

:::verdict Development assessment 5
**Working:** SC9 to SC11, including a hand-checked example. **Next:** check that every screen is readable for every user, which the client and my research (E5) both asked for.
:::

## 3.8 Stage 6: accessibility and final checks {#s-stage6}
**Aim.** Make sure every screen meets SC1 and SC16: contrast of at least 4.5:1 (WCAG 2.2 level AA) and no text under 12 px, at laptop and tablet widths.

I wrote two automated tests that read the stylesheet, work out every text colour against the background behind it, and measure its contrast with the WCAG formula. A third tool opens every screen in a real browser at 1440 and 1024 px and measures the text actually drawn, including hover and keyboard focus.

@code tests/test_style.py::contrast | contrast ratio exactly as WCAG defines it (checked against WCAG's own examples by a test)

:::fail The first run failed badly
`66 text colours below 4.5:1` and `37 font sizes below 12px` (evidence `style-test-before.txt`). The original pastel text colours looked soft but were too faint for older users (the survey and persona P3).
:::

:::fix Fix and retest
Each failing colour was darkened to the nearest shade of the same pink that reaches 4.5:1, so the palette still looks like the design, and every size under 12 px was raised. Retest: both stylesheet tests pass.
:::

:::fail The browser audit found problems the stylesheet tests had passed
Opening each page in a real browser showed faint text the stylesheet tests could not see: the side-menu text, text on see-through panels, the photo upload hint, the focus ring on the sign-in switch, and white labels on buttons while hovered.
:::

:::fix Fix and retest
Each was fixed, and the stylesheet test was improved to model the side menu, see-through fills and hover states so these problems cannot return unnoticed (commit `5c09de3`). Retest: the audit of {{audit_screens}} screens at each width reports 0 low-contrast texts, 0 small texts and no focus problems (`rendered-audit-desktop.json`, `rendered-audit-tablet.json`).
:::

@img 07-browse-tablet.png | Browse at tablet width (1024 px): cards reflow to fit | 10 | key=fig-s6-tablet crop=0-1300

### Tests for stage 6 {#s-tests6}
| ID | Test | Automated test or tool | Result |
|---|---|---|---|
| T6.1 | Text contrast | `test_every_text_colour_reaches_4_5_to_1` | Pass after fix |
| T6.2 | Text size | `test_no_text_is_smaller_than_12px` | Pass after fix |
| T6.3 | Rendered audit | `docs/tools/capture_screens.py`, both widths | Pass |

### Client feedback 6: final review {#s-feedback6}
@feedback 6

### Changes made after feedback 6 {#s-changes6}
:::change Changed
- **Allergy shown as a red warning.** It is part of the welfare box from stage 5, listed first.
- **Table clipping** fixed in stage 2's changes; retested at 1440 px in the browser audit and in the screenshot on page [[fig-s2-manage]].
:::

:::note Not changed, with reasons
- **Fainter placeholder text and disabled buttons.** These are drawn by Streamlit itself, outside my stylesheet, so the audit's "0 low-contrast texts" covers my text and controls but not Streamlit's own placeholder hints. WCAG does not require contrast for disabled controls, but the client finds them faint, so this is in the evaluation.
- **Whole-number scores.** Scores keep one decimal place so two close animals are not shown as equal; the score key explains the bands.
:::

:::verdict Development assessment 6 and sign-off
The AI role-played client signed off the final stage (rating 7 out of 10). All {{tests_total}} automated tests pass. The remaining requests are carried into the evaluation as partly met criteria and future development.
:::

## 3.9 Stage 7: changes from the reviews, and staying signed in {#s-stage7}
**Aim.** Make every change the six client reviews and the four usability testers asked for (listed under each stage's "Changes made" above), then fix the last problem on my own list: a browser reload signed the user out. Covers SC6 and SC7 (registration messages), SC4 and SC5 (browse and profile), SC8 (questionnaire), SC11 (explaining matches) and SC14 (staying signed in safely).

**What was built.**
- All review changes in one commit (`77ef20a`), each with a test named after the review that asked for it.
- **Staying signed in.** Streamlit forgets everything when the page is reloaded. Signing in now creates a random session token (32 random bytes from `secrets`), stored in a new `sessions` table with an expiry 12 hours ahead and placed in the address as `?s=…`. On a reload the token is looked up and the user is signed back in; signing out deletes the token, and an expired or made-up token signs nobody in. Only the token travels, never the user's id, so it cannot be guessed or changed into someone else's (commit `b0e302a`).

@code pawmatch/db.py::create_session | Making a session token
@code pawmatch/db.py::session_user | Looking a token up

### Tests for stage 7 {#s-tests7}
@widths 0.6 2.4 3 0.7
| Test | What it checks | Automated test | Result |
|---|---|---|---|
| T7.1 | The age rule is written on the registration form (review 1) | `test_review1_age_rule_is_written_on_the_form` | Pass |
| T7.2 | A blank confirm box gets its own message (review 1) | `test_registration_reports_every_missing_field` | Pass |
| T7.3 | The size filter narrows the list (review 3) | `test_review3_size_filter_narrows_the_list` | Pass |
| T7.4 | The profile offers the questionnaire as a button (review 3) | `test_review3_profile_offers_the_questionnaire_as_a_button` | Pass |
| T7.5 | The home page says staff make the decision (review 3) | `test_review3_home_says_staff_make_the_decision` | Pass |
| T7.6 | The hours question starts empty (review 4) | `test_review4_hours_question_starts_empty` | Pass |
| T7.7 | The matches page explains the score and the order (review 5) | `test_review5_matches_explain_the_score_and_the_order` | Pass |
| T7.8 | Answers can be updated from the account page (review 5) | `test_review5_account_lets_answers_be_updated` | Pass |
| T7.9 | A reload with the token keeps the adopter signed in | `test_reload_keeps_the_adopter_signed_in` | Pass |
| T7.10 | A made-up token signs nobody in | `test_signed_out_or_unknown_token_does_not_sign_in` | Pass |
| T7.11 | A token stops working when signed out or expired | `test_session_token_finds_its_user_until_ended_or_expired` | Pass |
| T1.3a | Valid emails are accepted (added in stage 7: the plan only had invalid cases) | `test_registration_accepts_valid_email_formats` (3 cases) | Pass |
| T2.6a | Exactly 500 characters is accepted (added in stage 7: the plan only had 501) | `test_text_of_exactly_500_characters_is_accepted` (2 cases) | Pass |
| All | Every earlier test still passes (regression) | Full suite | {{tests_total}} passed, {{tests_failed}} failed |

:::fail The blank confirm box failed first (also shown under stage 1)
The new rule for an empty confirm box changed what `test_registration_reports_every_missing_field` expected, and it failed (an extra `confirm` message). Saved before the fix: `docs/evidence/review-fail1-confirm-blank.txt`.
:::

:::fix Fix and retest
The test's expected list was updated to include the new message, because the extra message is the change the review asked for. Retest: passed, and the whole suite passed (`review-pytest.txt`).
:::

### Client feedback 7 {#s-feedback7}
No separate review was held after stage 7, because stage 7 only built what the six earlier reviews had asked for. Instead I checked each of the client's earlier requests (made by the AI role-played client, see [[s-method]]) against the stage 7 screens and tests.

@widths 2.6 1 2.4
| Earlier request (review) | Met? | Evidence |
|---|---|---|
| Say the age rule on the form; flag an empty confirm box (1) | Met | T7.1, T7.2 |
| Filter by size; the questionnaire as a button on the profile (3) | Met | T7.3, T7.4 |
| Hours box should not start at 0 (4) | Met | T7.6 |
| Explain warnings and the order in plain words (5) | Met | T7.7; still to be re-tested with real users (evaluation, U3) |
| Red outline on the box with the error; a Cancel button (1, 2) | Not met | Not possible in Streamlit; limitation 4 |

This check is mine, not a new client review; a walk-through with the real client is the first item of future development ([[e-future]]).

:::verdict Development assessment 7
Every change the reviews asked for that fits the design is built and tested, and a reload no longer signs the user out. Requests that were not built (address fields, a red outline on error boxes, a Cancel button) are explained under each stage and carried into the evaluation. Next: the post-development tests on [[e-results]].
:::
