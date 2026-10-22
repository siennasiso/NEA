# PawMatch — Pre-Development Test Plan (source-linked)

**Project:** OCR H446 Computer Science Programming Project  
**Stage:** Planned testing, to be completed during development  
**Status:** The *Success?* column must remain blank until each test has actually been carried out.  
**Source:** `A2 CWk Analysis - Sien n a (1).docx`, especially pp. 31–34 (client interview), 36–43 (stakeholder survey), 13–28 (competitor research) and 55–57 (success criteria).

The test data has been selected before implementation. Normal values show that intended functions work; invalid and boundary values reveal validation errors; and integration tests check that the database, interface and matching algorithm work together. Related values are grouped into one numbered test to keep the table manageable. When carrying out a test, record a separate result for each labelled subcase (A, B, C, etc.).

**Source key:** **Q** = question from client interview; **S** = question from stakeholder survey; **E1** = Dogs Trust; **E2** = RSPCA; **E3** = Petfinder; **E4** = Blue Cross; **SC** = numbered success criterion (1–9) in the analysis.

## 1. Registration and Login

| No. | Test and why it is necessary | Planned input | Expected output | Success? |
|---|---|---|---|---|
| 1 | **Valid registration (normal).** Proves a genuine adopter can make an account and their details are saved. **Sources: Q9, Q12; SC5, SC9.** | Name `Sienna Smith`; email `sienna@test.com`; age `18`; password and confirmation `password123`. | Exactly one user is created, with a normal user role. A success message or login option is shown. | |
| 2 | **Name checks (invalid/boundary).** Protects the quality of stored account data; the short and long inputs test the design's 2–50 character rule. **Sources: Q9; SC5.** | A. blank; B. spaces only; C. `A`; D. `Al`; E. 50 characters; F. 51 characters; G. `  Sienna Smith  `. | A–C and F rejected. D and E accepted. G saved without the outside spaces. No invalid account inserted. | |
| 3 | **Email format and uniqueness (invalid/database).** An email must be correctly formatted and unique for login. **Sources: Q9, Q12; SC5.** | A. blank; B. `siennatest.com`; C. ` Sienna@Test.COM `; D. register `sienna@test.com` twice. | A and B rejected. C normalised to `sienna@test.com`. D creates only one account; the second attempt gives a clear message. | |
| 4 | **Age and password boundaries (boundary).** Tests exactly below and at the chosen age and password limits, and verifies password confirmation. **Sources: Q9, Q12; SC5.** | Age: `17` and `18`, plus `eighteen`. Password: 8 characters and 9 characters. Confirmation: a different password. | 17 and non-numeric age rejected; 18 accepted. **If the final rule remains “more than eight characters”**, 8 rejected and 9 accepted. Nonmatching confirmation rejected. | |
| 5 | **Secure passwords and authentication (security).** Ensures passwords are not stored in plain text and invalid login details cannot grant access. **Sources: Q12; SC5, SC9.** | A. Inspect a registered user's database row; B. correct credentials; C. wrong password; D. unknown email; E. `' OR '1'='1' --` as email. | A contains a password hash, not the original password. B authenticates. C–E do not authenticate or reveal a database error. | |
| 6 | **Roles, navigation and logout (integration/security).** Prevents adopters from changing shelter records and checks sessions end properly. **Sources: Q12; SC5, SC8.** | A. normal user opens admin page; B. staff member logs in; C. user navigates between pages; D. user logs out and reopens a protected page. | A denied/redirected; B sees admin functions; C stays logged in; D requires authentication again. | |

## 2. Administrator Page

| No. | Test and why it is necessary | Planned input | Expected output | Success? |
|---|---|---|---|---|
| 1 | **Add an animal (normal and invalid).** Admin records must be accurate because they appear in profiles and affect matching. **Sources: Q2, Q5, Q15; SC8, SC9.** | Add Milo, Dog, age 4, with valid required fields and a photograph. Repeat separately with a blank name, negative age, unsupported species and missing required field. | Valid record saved exactly once and visible on animal preview/profile. Each invalid record rejected without a partial database entry. | |
| 2 | **Edit and delete animal records (integration).** Tests that shelter staff can keep animal details up to date. **Sources: Q5, Q15; SC8, SC9.** | A. change Milo's age from 4 to 5; B. restart application; C. delete Milo. | A changes only Milo's age. B retains updated data. C removes Milo from saved animal records and from future browsing/recommendations. | |

## 3. Home Page and Interface

| No. | Test and why it is necessary | Planned input | Expected output | Success? |
|---|---|---|---|---|
| 1 | **Home page and navigation (normal/usability).** First-time adopters need a clear starting point and easy access to the questionnaire. **Sources: Q6, Q7, Q11, S6, E1–E4; SC1, SC2.** | Log in. Use Home, Browse Animals, Profile and Questionnaire navigation. Check on laptop-sized and tablet-sized windows. | Purpose of matching is explained; a questionnaire button is easy to find; correct pages open. Layout remains readable without clipped essential controls and follows a consistent style. | |

## 4. Animal Preview and Profile Pages

| No. | Test and why it is necessary | Planned input | Expected output | Success? |
|---|---|---|---|---|
| 1 | **Complete animal cards and profiles (normal/database).** The user needs enough information to judge suitability instead of choosing from appearance alone. **Sources: Q2, Q15, E1, E2, E4; SC3, SC4.** | Save two different animals, Luna and Milo, with photos, breed, age, sex, personality, exercise and medical information. Open Luna. | Each preview card shows the correct animal's name, species, breed, age and photo. Luna's full profile displays its correct detailed record and offers a route back. | |
| 2 | **Three supported species (normal).** Ensures the solution meets its stated dog, cat and rabbit scope. **Sources: E2, E4; SC3.** | Save one dog, one cat and one rabbit, then open animal preview. | All three species appear with correct labels and details. None is omitted simply because it is a different species. | |
| 3 | **Search and filters (normal/robustness).** Helps users find animals without opening every profile. **Sources: Q8, S6, E2, E3, E4; SC1, SC3.** | A. search `Luna` and `luna`; B. filter Dog; C. filter Dog + Small; D. select a filter combination with no match; E. clear filters. | A retrieves Luna if searching is case-insensitive; B–C only show matching records; D displays a clear no-results message; E restores all available animals. | |

## 5. Adopter Questionnaire

| No. | Test and why it is necessary | Planned input | Expected output | Success? |
|---|---|---|---|---|
| 1 | **Complete valid questionnaire (normal).** All major lifestyle factors must reach the matching algorithm. **Sources: Q1, S5, E3; SC6, SC7.** | Housing=2; garden=Yes; hours alone=4; children=Yes; activity=2; species=Dog; complete other-pets and experience questions using permitted values. | Answers accepted and saved/processed for the correct user, ready for compatibility scoring. | |
| 2 | **Required and lookup values (invalid).** Incomplete or unsupported responses could lead to false matches. **Sources: Q15, S8; SC6.** | A. skip required question; B. housing=0 or 4; C. activity=0 or 4; D. species=Horse; E. Boolean=2. | Each unsupported or missing value rejected, including if sent around the dropdown validation. No invalid response used for scoring. | |
| 3 | **Hours alone range (boundary).** Time away is an important factor in animal suitability and must be within 0–24 whole hours. **Sources: Q1, Q10, S5; SC6.** | `-1`, `0`, `4`, `24`, `25`, `four`, `4.5`. | 0, 4 and 24 accepted; all other values rejected with a message; no invalid questionnaire submitted. | |
| 4 | **Save, change and reuse questionnaire answers (database).** Users should not need to complete their lifestyle information again for every animal. **Sources: E1, Q15; SC6, SC9.** | User A submits 4 hours alone, changes it to 6, logs out and in; User B then logs in. | User A's latest saved value is 6 and remains after a new session. User B never sees or uses User A's preferences. | |

## 6. Compatibility Algorithm and Results

**Controlled data:** Create one adopter profile P1 and test animal records with known attributes. Animal A meets every requirement and preference; Animal B fails precisely one lower-priority preference; Animal C fails an important suitability requirement (e.g., suitable with children). Set every other field equal, so changes in scoring can be checked independently.

| No. | Test and why it is necessary | Planned input | Expected output | Success? |
|---|---|---|---|---|
| 1 | **Perfect match (normal/upper boundary).** Establishes the maximum output of the scoring algorithm. **Sources: Q10, S7, E3; SC7.** | Run P1 against Animal A, designed to match every scored factor. | Score is 100% under the planned formula; all tested requirements marked met. | |
| 2 | **Manual score check (calculation).** Prevents an incorrect formula from producing plausible-looking percentages. **Sources: Q10, S7; SC7.** | Manually calculate P1 vs Animal B using the exact points/weights from the final design; then run the same data. | Program total and percentage equal the independent calculation, including the defined rounding rule. | |
| 3 | **Essential requirement versus preference (controlled comparison).** The client's interview places living space, allergies and children above preferred breed or age. **Sources: Q3, Q10, S5; SC7.** | Compare Animal B, missing a soft preference, with Animal C, missing an important requirement. | Requirement failure affects scoring as designed; the correct requirement is listed as unmet and a warning appears. The system must not silently present an unsuitable animal as a strong match. | |
| 4 | **Top four in order (sorting).** The success criteria promise at least four leading matches when enough suitable records exist. **Sources: Q14, S7; SC7.** | Use five controlled animals with distinct scores (e.g. 92%, 84%, 76%, 68%, 51%) where those scores are attainable using the designed formula. | The four highest are displayed in descending score order: 92%, 84%, 76%, 68%. Every displayed score is associated with its correct animal. | |
| 5 | **Explain results and staff decision (functional).** A number alone cannot tell users which requirements they meet or whether the result is an official decision. **Sources: Q3, Q4, E3; SC7.** | View a strong match and an animal with unmet essential requirements. | Each result identifies key met/unmet requirements; an unsuitable match shows a warning. The results page clearly explains that scores are guidance and shelter staff decide on adoption. | |
| 6 | **No-match, changed data and repeatability (robustness).** Recommendations must not become misleading when the database changes. **Sources: Q5, Q15; SC7, SC8, SC9.** | A. run identical inputs twice; B. delete a test animal then rerun; C. make every animal unsuitable; D. test no animal records. | A gives identical results. B never recommends the deleted record. C/D show a clear message without crashing or displaying an unrelated animal. | |

## 7. Database

| No. | Test and why it is necessary | Planned input | Expected output | Success? |
|---|---|---|---|---|
| 1 | **Persistence and record separation (integration).** User records, animals and questionnaire results must remain accurate beyond a single Streamlit session. **Sources: Q12, Q15; SC9.** | Save a valid user, animal and questionnaire; close/restart Streamlit; log in as each user and inspect their own data. | Committed records remain. Each user's answers are correctly linked, and animal information is not mixed between records. | |

## 8. Planned Post-Development Tests

These are written before the finished solution exists but should **not** have an actual outcome recorded yet. Use fresh inputs not relied on repeatedly during development.

| No. | Test and why it is necessary | Planned input | Expected output | Success? |
|---|---|---|---|---|
| 1 | **Complete adopter journey (functional/integration).** Tests all major stages working together. **Sources: Q6, Q7, Q14; SC1–SC7.** | New user registers, logs in, completes the questionnaire, sees results, opens a profile and logs out. | All screens load, recommendations use that user's data, and protected pages require login after logout. | |
| 2 | **Unseen bad data (robustness).** Tests whether validation rules generalise beyond the examples used during development. **Sources: Q12, Q15; SC5, SC6, SC9.** | Test previously unused invalid names, emails, passwords, ages, questionnaire responses and an empty animal database. | Each invalid input is rejected safely. No partial records are added or unhandled exceptions shown. | |
| 3 | **Client and target-user trial (usability).** Checks whether users find the interface as clear as requested during research. **Sources: Q6, Q11, S6, E3; SC1, SC2, SC6.** | Ask the client and target adopters to register, complete the questionnaire, explain the strongest result and locate an animal. Record completion, requests for help and feedback. | Tasks should be completed using the intended navigation. Observed difficulties and feedback are recorded and compared with the final usability success criteria. | |

## Traceability to the Analysis

| Analysis success criterion | Sections of this test plan |
|---|---|
| SC1 — Navigation and clean interface | 3, 4, 8 |
| SC2 — Home page | 3, 8 |
| SC3 — Animal preview (including three species) | 4 |
| SC4 — Individual animal profile | 4 |
| SC5 — User/admin registration and login | 1, 8 |
| SC6 — Adopter questionnaire | 5, 8 |
| SC7 — Results and recommendations | 6, 8 |
| SC8 — Admin management | 1, 2, 6 |
| SC9 — Database | 1, 2, 5, 7 |

## Source Details

**Primary research in the analysis:** client interview Q1–Q15 (pp. 31–34); 27-response stakeholder survey S1–S9 (pp. 36–43); success criteria SC1–SC9 (pp. 55–57).

**Competitor research in the analysis:** E1 Dogs Trust (pp. 13–16), E2 RSPCA (pp. 17–20), E3 Petfinder (pp. 22–25), E4 Blue Cross (pp. 26–28).

**Bibliography sources already listed in the analysis:**

- Dogs Trust, [How to adopt a dog](https://www.dogstrust.org.uk/rehoming/how-to-adopt).
- RSPCA, [Find a pet](https://www.rspca.org.uk/findapet).
- RSPCA, [Pet adoption process guide](https://www.rspca.org.uk/findapet/adopt).
- Petfinder, [Adopter profile](https://www.petfinder.com/pet-adopter-profile/).
- Petfinder, [Petfinder quiz](https://www.petfinder.com/user/profile/create/).

**Before marking anything Pass:** Record the real output and evidence for each subcase. When something fails, explain the error, correction and retest. Exact algorithm weights and any match cut-offs must agree with the final design; this plan does not invent them.