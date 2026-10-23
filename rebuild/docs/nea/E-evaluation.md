@part E Evaluation
# 4 Testing to inform evaluation {#e-testing}

## 4.1 Post-development tests {#e-results}
The finished system (commit `77ef20a` plus the worked-example test) was tested against every success criterion using the plan on [[d-postplan]]. First, the whole automated suite was run again on the final build: **{{tests_total}} tests, {{tests_failed}} failures** (`docs/evidence/pytest-junit.xml`). This re-runs every development test T1.1 to T6.3, so nothing built in an early stage was broken by a later one.

@widths 0.9 1.1 1.1 1 1 1.1 1
| Test file | Validation | Matching | Accounts | Database | Staff access | Pages and style |
|---|---|---|---|---|---|---|
| Tests | {{tests_test_validation}} | {{tests_test_matching}} | {{tests_test_auth}} | {{tests_test_repository}} | {{tests_test_admin_access}} | {{tests_test_ui_smoke}} + {{tests_test_style}} |

### Capacity and speed (SC10, SC14) {#e-speed}
`docs/tools/measure_v2.py` builds a separate database far larger than the rescue needs, then times the slow operations.

| Measurement | Result | Target | Verdict |
|---|---|---|---|
| Animals in the test database | {{animals}} | at least 500 | Met |
| Adopter accounts | {{users}} | at least 100 | Met |
| Questionnaire submission: score, rank and store every Available animal ({{scored}} animals) | mean {{submit_mean}} s, worst {{submit_max}} s | under 1 s | Met |
| Browse query returning {{browse_found}} animals | {{browse_query}} s | n/a | Met |
| Browse page drawn in full by Streamlit's test runner (worst of 3; a browser adds network time) | {{browse_page}} s | under 3 s | Met |

### Results against each success criterion {#e-ptests}
@widths 0.45 2.2 3.3 0.8
| P | What was tested on the finished system | Evidence | Result |
|---|---|---|---|
| P1 | Contrast and text size on every screen | Audit of {{audit_screens}} screens at 1440 px and 16 at 1024 px (the two extra questionnaire screens were only captured at laptop width): 0 low-contrast, 0 small (T6.1 to T6.3) | Pass |
| P2 | One menu; staff items hidden from adopters | Figures E1 and E2 below; T2.8, T3.5 | Pass |
| P3 | Home page explains suitability and that staff decide | Page [[fig-s3-home]]; `test_review3_home_says_staff_make_the_decision` | Pass |
| P4 | Browse with species, size and search | Page [[fig-s3-browse]]; T3.1 to T3.3 | Pass |
| P5 | Profile from the database | Page [[fig-s3-profile]]; T3.4 | Pass |
| P6 | Registration validation | Page [[fig-s1-errors]]; T1.1 to T1.8 | Pass |
| P7 | Hashed passwords; one login error | Figure E3 below; T1.9, T1.10, `test_register_stores_hash_not_password` | Pass |
| P8 | Questionnaire: 10 screens, cannot skip | T4.1 to T4.6; timing not measured with real users | Partly |
| P9 | Score equals the hand calculation | [[s-worked]]; T5.8 | Pass |
| P10 | Ranking order and speed | T5.7, T5.9 (`test_matches_page_shows_the_top_five_and_can_show_all`), T5.10; speed table above | Pass |
| P11 | Every match explains itself | Page [[fig-s5-matches]]; T5.5, T5.6 | Pass |
| P12 | Staff add / edit / delete with validation | Pages [[fig-s2-add]], [[fig-s2-manage]]; T2.1 to T2.7, T2.9; photo type and size `test_image_type_and_size` | Pass |
| P13 | Adopters cannot use staff functions | T2.8 (every action, both adopter and signed out) | Pass |
| P14 | Storage and capacity | T2.11, T4.5; 500 animals / 100 users above | Pass |
| P15 | Usability (SUS ≥ 68) and client sign-off | Section 4.3: mean SUS {{sus_mean}} from simulated testers; the AI role-played client signed off, not the real client | Partly |
| P16 | Laptop and tablet widths | Page [[fig-s6-tablet]]; audit of {{audit_screens}} screens at 1440 px and 16 at 1024 px | Pass |

@img 06-home-desktop.png | The adopter's menu: home, browse, questionnaire, matches, account (no staff items) | 12 | key=fig-e-menu-adopter crop=0-700
@img 15-admin-overview-desktop.png | The staff menu after a staff login: dashboard, manage, add | 12 | key=fig-e-menu-staff crop=0-700
@img 02-login-error-desktop.png | A wrong password and an unknown email give the same message | 12 | key=fig-e-login-error

### Agreement with hand-written expectations and weight sensitivity {#e-sensitivity}

The tests above show each rule works on its own. To check that the **whole ranking** gives the answers a person would expect, I wrote ten adopter profiles (A1 to A10) and, before running the program, wrote down for each one which demo animals must be in its top three and which must never be (for example, a dog must never be offered to someone out 8 hours a day). `tests/test_agreement.py` checks the program's top three against them; the results are saved in `docs/evidence/agreement-sensitivity.json`.

@widths 0.4 2.2 2.4 0.6
| ID | Profile | Program's top three | Agrees |
|---|---|---|---|
| A1 | Flat, out 8 h a day, first pet, low activity | Milo, Poppy, Teddy (all suitable) | Yes |
| A2 | Family house with garden, wants a dog | Archie, Luna, Oscar | Yes |
| A3 | Same family, allergic to dogs, wants a rabbit | Clover, Daisy, Poppy | Yes |
| A4 | Older experienced owner, flat, out 10 h, likes cats | Willow; then Milo and Poppy with a warning | Yes |
| A5 | Already has a pet, wants a second dog | Archie, Oscar, Luna | Yes |
| A6 | First-time owner, out 6 h, wants a rabbit | Daisy, Poppy, Clover | Yes |
| A7 | Experienced runner, large house, wants a large dog | Luna, Archie, Nala | Yes |
| A8 | Flat with children and a cat, out 5 h | Milo, Poppy, Willow | Yes |
| A9 | Allergic to cats and rabbits, house with garden | Archie, Oscar, Luna | Yes |
| A10 | Out 12 h with children and a pet | Three animals, every one with a warning: none is called suitable | Yes |

All ten agree. A4 shows the important-factor rule working: only one animal can safely be left 10 hours, so the next two are shown below it with a warning instead of being hidden.

**Sensitivity.** The weights in the design were my judgement, informed by the client interview, so I checked that the results do not depend on their exact values. Each of the seven weights was changed by 10% down and 10% up (14 runs), and the top three was recalculated for all ten profiles: **no top three changed in any run** (`test_ten_percent_weight_changes_do_not_change_any_top_three`). Even a 50% change to any one weight changed none of them, because the welfare factors decide which animals are suitable before the weights decide the order. This means the client can adjust a weight in `WEIGHTS` (section 5.4) without the matches changing unexpectedly. The limitation is that many demo animals score 100% for a given profile, so ties are broken by name; with a larger shelter the order inside a tie would matter more.

### Phone and tablet render check {#e-render}

After stage 7 the live system was opened in a headless browser at three sizes: a phone (390 px), a tablet upright (820 px) and a tablet on its side (1180 px), signed in as an adopter and as staff (`docs/evidence/render-phone-tablet.json`). On every page there was **no sideways scrolling and no text smaller than 12 px**, and the adopter's menu buttons could be reached at every size. Reloading the page kept the user signed in at all three sizes (T7.9 to T7.11). On the phone some controls were shorter than the 44 px touch target recommended by WCAG 2.2, so every input and button is now at least 44 px tall on screens narrower than 640 px. The staff sidebar takes most of a phone screen until it is closed, which is acceptable because staff use a laptop at the rescue (stakeholder analysis), but it is listed under future development (section 5.6).


## 4.2 Robustness {#e-robust}
| R | Test | Automated test | Result |
|---|---|---|---|
| R1 | Search for `' OR 1=1 --` | `test_search_text_is_treated_as_data_not_sql` | Pass: no results, no rows lost |
| R2 | Error halfway through saving | `test_connect_rolls_back_on_error` | Pass: nothing half-saved |
| R3 | Bad row inserted directly into the database | `test_database_constraints_back_up_validation` | Pass: refused |
| R4 | Edit an animal another staff member deleted | `test_edit_of_deleted_animal_reports_error` | Pass: clear message |
| R5 | Open a database from an earlier version | `test_old_database_gains_calculated_at_column`, `test_old_database_gains_the_stage_9_columns_and_demo_values` | Pass: upgraded |
| R6 | 500 animals and 100 users | `measure_v2.py` (above) | Pass |

## 4.3 Usability testing {#e-usability}
**Method.** Four tester profiles were chosen to cover the stakeholders in the analysis: a young first-time adopter (P1), a parent (P2), an older user with low confidence online (P3, the hardest test of readability) and a staff volunteer (P4). Each was given the five tasks on [[d-utasks]] with screenshots of the system as it was before the stage 7 changes, and no help, rated each task out of 10, and answered the ten SUS statements.

**Same starting data for every tester.** The screenshots were taken by `docs/tools/capture_screens.py`, which starts PawMatch on a new temporary database each time; `prepare` in `seed.py` fills it with the same demo animals and one staff account. So every tester saw the same animals and the same results, and nothing left over from an earlier run could change what they saw.

:::note Honest limitation
These four testers were **simulated by an AI model** given each profile, not real people (logged in Appendix A). Simulated testers can spot unclear wording and missing feedback, but cannot show how long tasks really take or where real people hesitate. One real person did use the live system during development, and found the sign-up problem fixed in stage 1 ([[s-stage1]]); that is the only real-user evidence, so SC15 is treated as partly met below.
:::

@personas

@suschart SUS score for each tester; the dashed line is the average website (68)

### What the usability testing showed {#e-ufindings}
@widths 1 1.1 0.6 2.8 2.1 0.8
| Task | Screen | Criterion | What testers found | What happened | Verdict |
|---|---|---|---|---|---|
| U1 register and log in | Register, login | SC6, SC7 | All four completed it without help (P1 rated it 9/10). P1 noticed that an empty confirm box was not flagged. | Fixed in stage 7 (confirm box flagged) | Met |
| U2 questionnaire | Questionnaire (10 screens) | SC8 | Completed by all; the progress bar and "Question N of 10" were liked. The hours box started at 0. | Fixed: hours box starts empty | Met |
| U3 explain the top match | Matches | SC11 | The lowest-rated task (5 to 7 out of 10). Testers did not know what "welfare need" meant, could not see why a warned animal ranked lower, and wanted the warning to stand out. | Fixed: red welfare box in plain words, a line explaining the order, and a score key | Partly met |
| U4 staff add, edit, delete | Staff manage, add animal | SC12 | P4 completed add and edit, but rated it 6/10: the Delete button was not visible enough. | Partly met: the tick-box confirmation stays; making Delete more visible is future development | Partly met |
| U5 browse and return | Browse, profile | SC4, SC5 | Easy for everyone (8 to 9 out of 10); "Back to all animals" kept the list. | No change needed | Met |

The verdict is for the task's success criterion after the stage 7 changes. U3 is only partly met because the plain-words fix was made after the testing and has not been re-tested; U4 is partly met because Delete is still not easy to see.

The common request from all four testers was the same as the client's in review 5: say in plain words what a warning means. That is the strongest evidence that the stage 7 change to the matches page was the right one.

### Stakeholder survey after the build (planned, not yet run) {#e-survey}
The analysis survey of 27 adopters ([[a-survey]]) is the baseline for what adopters wanted before the build. No survey of real stakeholders has been run on the finished system yet, so there are **no results to report here**; this is limitation 1 ([[e-limits]]). The survey below is ready to send as soon as the client can share it with the rescue's adopters and volunteers.

| | Plan |
|---|---|
| Who | At least 10 people who used the live system: adopters who completed the questionnaire, and two or more rescue staff or volunteers |
| When | After a week of using the live system at the rescue, before any further changes |
| Questions | 1. Did the matches page explain why each animal suits you? (1 to 5) 2. Did any warning stop you from choosing an animal you would otherwise have chosen? (yes / no, why) 3. How long did the questionnaire take? (under 2 / 2 to 3 / over 3 minutes) 4. Was any question unclear? (which) 5. Staff only: did any match shown to an adopter look wrong to you? (which, why) 6. The ten SUS statements |
| Compared with | The baseline answers from the analysis survey and the simulated testers' SUS scores above |

# 5 Evaluation {#e-eval}

## 5.1 Success criteria {#e-sc}
@widths 0.5 1.8 0.8 4.4
| SC | Criterion | Verdict | Evidence and comment |
|---|---|---|---|
| SC1 | Pink palette, readable | Met | 0 low-contrast and 0 small texts on all {{audit_screens}} laptop screens and all 16 tablet screens (P1). The AI role-played client liked the look in every review, but the audit is the evidence. The client finds Streamlit's own placeholder text and disabled buttons faint, which my stylesheet does not control. |
| SC2 | One consistent menu | Met | Every page one click from the menu; staff items never appear for adopters (P2). |
| SC3 | Home explains suitability, staff decide | Met | The home page says what the score means and that staff make the final decision (page [[fig-s3-home]]). `test_review3_home_says_staff_make_the_decision` opens the home page as an adopter and checks for that sentence, and `test_adopter_login_opens_the_home_page` checks an adopter lands there after logging in (P3). |
| SC4 | Browse and filter | Met | All Available animals, three species, species and size filters and search (P4). |
| SC5 | Full profile from the database | Met | Clicking an animal opens its photo, details, personality and needs, all read from the database (page [[fig-s3-profile]]). `test_view_profile_opens_the_animal_with_its_needs` checks the needs shown match the stored record; `test_review3_profile_offers_the_questionnaire_as_a_button` checks the next step is offered (P5). |
| SC6 | Registration validation | Met | Normal, boundary and invalid data for every field, duplicate emails refused (P6). |
| SC7 | Secure accounts | Met | Salted scrypt hashes, one generic error, sign-out clears the session (P7). |
| SC8 | 10-question questionnaire, cannot skip | Partly met | 10 screens in 4 sections and cannot be skipped (P8). The 3-minute target could not be measured, because the testers were simulated. |
| SC9 | Correct score | Met | The worked example on [[s-worked]] gives the same percentage by hand and in the program (`test_worked_example_in_the_write_up_matches_the_program`). `test_weights_match_the_design` checks the weights are the designed ones, `test_each_factor_loses_its_weight` removes each factor in turn and checks exactly its weight is lost, and `test_boundaries_count_as_met` checks that equal values (for example 6 hours when 6 are allowed) count as met. The weight-sensitivity and fixed-profile checks below show the ranking does not depend on one exact weight (P9). |
| SC10 | Ranked quickly and safely | Met | Warned animals never above safe ones (T5.7); the top 5 shown, at least 4 as required, with "show all" (T5.9); 500 animals in {{submit_max}} s at worst (P10). |
| SC11 | Each result explains itself | Met | Met, not-met and warning lists on every match, plus the score key (P11). |
| SC12 | Staff CRUD with validation | Met | `test_admin_can_add_edit_and_delete` and `test_staff_can_add_an_animal_and_then_delete_it` (through the real page) add, edit and delete an animal; `test_admin_add_still_validates`, `test_staff_add_form_reports_missing_fields` and `test_invalid_animal_fields_are_rejected` show bad data is refused with a message; `test_image_type_and_size` refuses wrong photo types and photos over 2 MB; `test_delete_removes_animal_and_its_stored_results` shows a delete leaves no stored scores behind (P12). The staff tester wanted Delete to be more visible. |
| SC13 | Adopters cannot use staff functions | Met | Every staff action refused for adopters and signed-out users (P13). My requirements list (8.1) asked for a *separate* admin login; one login form is used, and the role stored in the database decides what opens. This is simpler and just as secure, because every staff action checks the role itself. |
| SC14 | Reliable storage, scales | Met | Constraints back up validation; 500 animals and 100 users; browse page {{browse_page}} s in Streamlit's test runner (P14). |
| SC15 | Easy to use (SUS ≥ 68), client sign-off | Partly met | Mean SUS {{sus_mean}} and every tester above 60, and the AI role-played client signed off; but neither the testers nor the client's reviews were real people. |
| SC16 | Laptop and tablet | Met | No clipped content at 1440 and 1024 px in a browser (P16), which is how the criterion is defined; a phone and tablet render check was also run. Trying it on a real iPad is future development. |
| Req. 8.1 | A separate admin login (requirements list) | Partly met | Staff use the same login form as adopters, and the role stored in the database decides what opens. Every staff action checks the role itself (T2.8), so this is as secure as a separate login, but it is not what requirement 8.1 says. A staff-only login page would be a small change: the same form that refuses non-staff accounts. |

**Summary:** 14 of 16 success criteria met, 2 partly met (SC8, SC15), none unmet. Both are partly met because of how they were tested (no real users), not because a feature is missing. From the requirements list, 8.1 (a separate admin login) is partly met by design choice.

## 5.2 How the partly met criteria would be fully met {#e-partly}
| SC | What is missing | How I would meet it |
|---|---|---|
| SC8 | Timing with real people | Ask five adopters at the rescue to complete the questionnaire while I time them; target under 3 minutes each. |
| SC15 | Real usability testers | Repeat tasks U1 to U5 and the SUS questionnaire with at least five real people from the stakeholder groups (including an older user and a staff member), then compare with the simulated results. |
| Req. 8.1 | Separate staff login | Add a staff login page that uses the same check but refuses adopter accounts, and remove the staff link from the adopter login. |

## 5.3 Usability features evaluated {#e-ufeatures}
@widths 2 3.5 1
| Feature (from [[d-usability]]) | Evidence of how well it worked | Effective? |
|---|---|---|
| Pink palette, Nunito, large photos | Liked by the AI role-played client in every review and by all four simulated testers; the audit shows it is readable | Yes |
| Contrast and text size | Audit passes; P3 (older user) could read every page | Yes |
| One consistent menu | Every tester found every page | Yes |
| One question per screen with progress | Liked by the simulated testers in U2; no tester got lost | Yes |
| Card buttons | Every choice visible at once and easy to tap; the selected state could be stronger (client review 4) | Partly |
| Next disabled until answered | No incomplete questionnaire stored (T4.6); disabled buttons look faint | Partly |
| Error under each box | Every tester fixed errors without help in U1; no red outline on the box | Partly |
| One generic login error | The AI role-played client agreed it was right for security; T1.4 shows both wrong cases give the same message | Yes |
| Met / not met / warnings | Lowest task score (U3, on the pre-stage-7 screenshots); clearer after the stage 7 changes, but not re-tested | Partly |
| "Staff make the final decision" | On home, profile and matches pages | Yes |
| Tick-box before delete | No accidental deletes; Delete button not visible enough (U4) | Partly |
| Keyboard focus outline | Audit shows a focus outline on every control | Yes |
| Red outline on the box with the error (asked for in the reviews) | Not possible: Streamlit cannot outline one box, so the message under the box is the only cue (limitation 4) | No |

## 5.4 Maintenance {#e-maintenance}
- **Modular structure.** All rules live in `pawmatch/` and all screens in `webui/`. A change to how a page looks cannot break the scoring, and the {{tests_total}} tests show at once if a change to the rules does.
- **One place for each rule.** The weights, the warning factors, the allergy cap and the category bands are constants at the top of `matching.py`; the species, sizes and statuses are lists in `models.py`. Changing a weight is one edit, and the percentage stays 0 to 100 because it is divided by the total.
- **Adding a species.** *Issue:* the rescue starts taking a new kind of animal. *Fix:* add it to `SPECIES` in `models.py` and to the CHECK on the animals table, then add demo data; the tests on fixed lists show what else needs updating.
- **Changing a weight.** *Issue:* the rescue finds, for example, that time alone matters more than the client thought. *Fix:* change one number in `WEIGHTS`; update `test_weights_match_the_design`, then run the tests and the sensitivity check below to see how the order of matches changes.
- **Database upgrades.** `init_schema` adds missing columns to an older database file automatically (R5), so the rescue never loses records when the program is updated.
- **Comments and names.** Every module and function starts with a comment saying what it does and which criterion it serves; names follow the design's data dictionary.
- **Pinned versions.** *Issue:* Streamlit and other libraries release new versions that can change how pages behave. *Fix:* `requirements.txt` fixes the exact versions tested, so nothing changes without warning. Updating is done deliberately: change the version, run the {{tests_total}} tests, and only deploy if they all pass.
- **Backups.** *Issue:* a broken laptop or a mistaken delete would lose every record. *Fix:* all data is one SQLite file (`data/pawmatch.db`), so a daily copy of that file to another drive is a complete backup, and restoring is copying it back.
- **Forgotten passwords.** *Issue:* PawMatch has no reset email. *Fix:* staff can delete the account so the adopter registers again; a reset email is future development.
- **Who maintains it.** A small rescue has no programmer. The README explains how to install, run, test and back up the system, so a volunteer with basic computer skills could keep it running, and a student or freelancer could change it safely because the tests protect the rules.

### Privacy and personal data {#e-privacy}
PawMatch stores personal data, so it has to follow UK GDPR: collect only what is needed, keep it safe and remove it when asked.
- **What is stored.** For each user: name, email, age, role and a password hash (`users` table); each questionnaire answer set and the scores worked out from it (`questionnaire_responses` and `match_results`); and sign-in tokens that expire after 12 hours (`sessions`). No address, phone number or payment details are collected (limitation 8).
- **How it is protected.** Passwords are never stored: each is salted and hashed with scrypt (`auth.py`), and a wrong email and a wrong password give the same message (SC7). Every query uses placeholders, so typed text cannot change the SQL (R1). Sign-in tokens are random (`secrets.token_urlsafe`) and are deleted on sign-out.
- **How a user's data is removed.** There is no "delete my account" button yet. If an adopter asks, staff remove the user's row from the database file, and the database deletes their answers, scores and sign-in tokens with it (ON DELETE CASCADE). A self-service delete button is future development (limitation 9).

## 5.5 Limitations {#e-limits}
1. **The client reviews and usability testers were simulated by AI.** They found real problems that were fixed, but they cannot replace real people; the client's own sign-off and real testing are the first step of future development.
2. **The weights are judgement, not data.** They come from the client and the survey. Without records of past adoptions and returns, nobody can prove that 20 points for time alone is better than 15.
3. **Only five yes/no or level-based facts describe an animal's needs.** Real animals have needs the form cannot hold (for example a dog that is fine with cats but not with other dogs); staff have to put these in the personality text, which is not scored.
4. **Streamlit limits the interface.** It cannot outline a single box in red, change its own placeholder and disabled colours, or add a Cancel button that behaves like a normal web form. These were requested in reviews and are not done.
5. **SQLite allows one writer at a time.** That is fine for two or three staff, but would slow down a large rescue with many staff saving at once.
6. **The optional Google sign-in uses a test set-up made by the developer.** The rescue would need its own Google account settings before using it for real; the email and password login works without it.
7. **The sign-in token is in the address.** Staying signed in after a reload works by keeping a random token in the page address. Anyone who is sent that exact address within 12 hours would be signed in as that user, so users should not share the address while signed in. A browser cookie would avoid this, but Streamlit cannot set cookies itself.
8. **No contact details are stored.** I chose not to collect addresses and phone numbers (data minimisation), so the rescue cannot contact an adopter through PawMatch; the adopter has to get in touch.
9. **Users cannot delete their own account.** Erasing a user's data needs staff to edit the database file, which a volunteer may not be confident doing.
10. **Only one site.** The system serves one rescue building; a rescue with several branches could not filter animals or staff by branch.
11. **The live system was not tried on real tablets and phones.** The browser render checks pass at phone and tablet sizes, but nobody has used it on a real device.
12. **The questionnaire has no "save and continue later".** Answers are only stored when all ten are given (T4.6), so an adopter who leaves halfway starts again.

## 5.6 Future development {#e-future}
@widths 2.2 3.4 1.4
| Improvement | How it would be done | Addresses |
|---|---|---|
| Real usability testing and client sign-off | Five or more real testers, timed, with SUS; client walk-through at the rescue | SC8, SC15, limitation 1 |
| Learn the weights from outcomes | Record whether each adoption succeeded or the animal was returned; after enough adoptions, compare outcomes with scores and adjust weights | Limitation 2 |
| "Good with cats / dogs / rabbits" instead of one yes/no | Three yes/no fields for each animal and a matching question; one more factor in `_factor_checks` | Limitation 3 |
| Register interest in an animal | A button that sends the adopter's details and score to staff, with the adopter's permission, then a staff list of enquiries | Limitation 8, client Q14 |
| Clearer Delete and a Cancel button; red outline on error boxes | Custom CSS for the Delete button now; the other two need a custom Streamlit component or a move to a web framework such as Flask | Limitation 4, U4 |
| Number of matches on the "done" screen | Count results without warnings and show "You have N strong or good matches" | SC11, client review 4 |
| Several branches | Add a branches table and a branch_id on animals and staff; filter by branch | Limitation 10, scope |
| Real tablet and phone testing | Repeat the usability tasks on an iPad and a phone; the browser render checks already pass at those sizes | SC16, limitation 11 |
| Keep the sign-in in a cookie instead of the address | A small custom Streamlit component that sets a secure, HTTP-only cookie | Limitation 7 |
| PostgreSQL instead of SQLite | Only `db.py` changes, because no other module writes SQL | Limitation 5 |
| "Delete my account" button | A button on the account page that asks for the password again, then deletes the user (their answers and scores go with it) | Limitation 9, privacy |
| Save answers part way | Store the answers given so far in a draft row and reopen the questionnaire at the first unanswered question | Limitation 12, SC8 |
| Run the stakeholder survey | Send the survey on [[e-survey]] after a week of real use and compare with the analysis baseline | Limitation 1, SC15 |
| The rescue's own Google sign-in | Create a Google Cloud project in the rescue's name, add its client ID and secret to the server's secrets file, and test the sign-in with a staff account | Limitation 6 |
