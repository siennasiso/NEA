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
| P1 | Contrast and text size on every screen | Audit of {{audit_screens}} screens at 1440 and 1024 px: 0 low-contrast, 0 small (T6.1 to T6.3) | Pass |
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
| P15 | Usability (SUS ≥ 68) and client sign-off | Section 4.3: mean SUS {{sus_mean}} from simulated testers; AI role-played client signed off | Partly |
| P16 | Laptop and tablet widths | Page [[fig-s6-tablet]] and audit at both widths | Pass |

@img 06-home-desktop.png | The adopter's menu: home, browse, questionnaire, matches, account (no staff items) | 12 | key=fig-e-menu-adopter crop=0-700
@img 15-admin-overview-desktop.png | The staff menu after a staff login: dashboard, manage, add | 12 | key=fig-e-menu-staff crop=0-700
@img 02-login-error-desktop.png | A wrong password and an unknown email give the same message | 12 | key=fig-e-login-error

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

:::note Honest limitation
These four testers were **simulated by an AI model** given each profile, not real people (logged in Appendix A). Simulated testers can spot unclear wording and missing feedback, but cannot show how long tasks really take or where real people hesitate. One real person did use the live system during development, and found the sign-up problem fixed in stage 1 ([[s-stage1]]); that is the only real-user evidence, so SC15 is treated as partly met below.
:::

@personas

@suschart SUS score for each tester; the dashed line is the average website (68)

### What the usability testing showed {#e-ufindings}
@widths 1 3.2 3
| Task | What testers found | What happened |
|---|---|---|
| U1 register and log in | All four completed it without help (P1 rated it 9/10). P1 noticed that an empty confirm box was not flagged. | Fixed in stage 7 (confirm box flagged) |
| U2 questionnaire | Completed by all; the progress bar and "Question N of 10" were liked. The hours box started at 0. | Fixed: hours box starts empty |
| U3 explain the top match | The lowest-rated task (5 to 7 out of 10). Testers did not know what "welfare need" meant, could not see why a warned animal ranked lower, and wanted the warning to stand out. | Fixed: red welfare box in plain words, a line explaining the order, and a score key |
| U4 staff add, edit, delete | P4 completed add and edit, but rated it 6/10: the Delete button was not visible enough. | Partly met: the tick-box confirmation stays; making Delete more visible is future development |
| U5 browse and return | Easy for everyone (8 to 9 out of 10); "Back to all animals" kept the list. | No change needed |

The common request from all four testers was the same as the client's in review 5: say in plain words what a warning means. That is the strongest evidence that the stage 7 change to the matches page was the right one.

# 5 Evaluation {#e-eval}

## 5.1 Success criteria {#e-sc}
@widths 0.5 1.8 0.8 4.4
| SC | Criterion | Verdict | Evidence and comment |
|---|---|---|---|
| SC1 | Pink palette, readable | Met | 0 low-contrast and 0 small texts on all {{audit_screens}} screens (P1). The AI role-played client liked the look in every review, but the audit is the evidence. The client finds Streamlit's own placeholder text and disabled buttons faint, which my stylesheet does not control. |
| SC2 | One consistent menu | Met | Every page one click from the menu; staff items never appear for adopters (P2). |
| SC3 | Home explains suitability, staff decide | Met | P3. |
| SC4 | Browse and filter | Met | All Available animals, three species, species and size filters and search (P4). |
| SC5 | Full profile from the database | Met | P5. |
| SC6 | Registration validation | Met | Normal, boundary and invalid data for every field, duplicate emails refused (P6). |
| SC7 | Secure accounts | Met | Salted scrypt hashes, one generic error, sign-out clears the session (P7). |
| SC8 | 10-question questionnaire, cannot skip | Partly met | 10 screens in 4 sections and cannot be skipped (P8). The 3-minute target could not be measured, because the testers were simulated. |
| SC9 | Correct score | Met | Hand calculation equals the program (P9); every weight and boundary tested. |
| SC10 | Ranked quickly and safely | Met | Warned animals never above safe ones (T5.7); the top 5 shown, at least 4 as required, with "show all" (T5.9); 500 animals in {{submit_max}} s at worst (P10). |
| SC11 | Each result explains itself | Met | Met, not-met and warning lists on every match, plus the score key (P11). |
| SC12 | Staff CRUD with validation | Met | P12. The staff tester wanted Delete to be more visible. |
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
| Pink palette, Nunito, large photos | Liked by the client in every review and by all four testers | Yes |
| Contrast and text size | Audit passes; P3 (older user) could read every page | Yes |
| One consistent menu | Every tester found every page | Yes |
| One question per screen with progress | Liked in U2; no tester got lost | Yes |
| Card buttons | Every choice visible at once and easy to tap; the selected state could be stronger (client review 4) | Partly |
| Next disabled until answered | No incomplete questionnaire stored (T4.6); disabled buttons look faint | Partly |
| Error under each box | Every tester fixed errors without help in U1; no red outline on the box | Partly |
| One generic login error | Client agreed it was right for security | Yes |
| Met / not met / warnings | Lowest task score (U3, on the pre-stage-7 screenshots); clearer after the stage 7 changes, but not re-tested | Partly |
| "Staff make the final decision" | On home, profile and matches pages | Yes |
| Tick-box before delete | No accidental deletes; Delete button not visible enough (U4) | Partly |
| Keyboard focus outline | Audit shows a focus outline on every control | Yes |

## 5.4 Maintenance {#e-maintenance}
- **Modular structure.** All rules live in `pawmatch/` and all screens in `webui/`. A change to how a page looks cannot break the scoring, and the {{tests_total}} tests show at once if a change to the rules does.
- **One place for each rule.** The weights, the warning factors, the allergy cap and the category bands are constants at the top of `matching.py`; the species, sizes and statuses are lists in `models.py`. Changing a weight is one edit, and the percentage stays 0 to 100 because it is divided by the total.
- **Adding a species** means adding it to `SPECIES` and to the database CHECK, then adding demo data; the tests on fixed lists show what else needs updating.
- **Database upgrades.** `init_schema` adds missing columns to an older database file automatically (R5), so the rescue never loses records when the program is updated.
- **Comments and names.** Every module and function starts with a comment saying what it does and which criterion it serves; names follow the design's data dictionary.
- **Pinned versions.** `requirements.txt` fixes the exact versions tested, so a new Streamlit release cannot break the system without warning. Updating is done deliberately: change the version, run the tests, then deploy.
- **Backups.** All data is one SQLite file, so a daily copy of that file is a complete backup.
- **Who maintains it.** A small rescue has no programmer. The README explains how to install, run, test and back up the system, so a volunteer with basic computer skills could keep it running, and a student or freelancer could change it safely because the tests protect the rules.

## 5.5 Limitations {#e-limits}
1. **The client reviews and usability testers were simulated by AI.** They found real problems that were fixed, but they cannot replace real people; the client's own sign-off and real testing are the first step of future development.
2. **The weights are judgement, not data.** They come from the client and the survey. Without records of past adoptions and returns, nobody can prove that 20 points for time alone is better than 15.
3. **Only five yes/no or level-based facts describe an animal's needs.** Real animals have needs the form cannot hold (for example a dog that is fine with cats but not with other dogs); staff have to put these in the personality text, which is not scored.
4. **Streamlit limits the interface.** It cannot outline a single box in red, change its own placeholder and disabled colours, or add a Cancel button that behaves like a normal web form. These were requested in reviews and are not done.
5. **SQLite allows one writer at a time.** That is fine for two or three staff, but would slow down a large rescue with many staff saving at once.
6. **The optional Google sign-in uses a test set-up made by the developer.** The rescue would need its own Google account settings before using it for real; the email and password login works without it.
7. **The sign-in token is in the address.** Staying signed in after a reload works by keeping a random token in the page address. Anyone who is sent that exact address within 12 hours would be signed in as that user, so users should not share the address while signed in. A browser cookie would avoid this, but Streamlit cannot set cookies itself.
8. **No contact details are stored.** I chose not to collect addresses and phone numbers (data minimisation), so the rescue cannot contact an adopter through PawMatch; the adopter has to get in touch.

## 5.6 Future development {#e-future}
@widths 2.2 3.4 1.4
| Improvement | How it would be done | Addresses |
|---|---|---|
| Real usability testing and client sign-off | Five or more real testers, timed, with SUS; client walk-through at the rescue | SC8, SC15, limitation 1 |
| Learn the weights from outcomes | Record whether each adoption succeeded or the animal was returned; after enough adoptions, compare outcomes with scores and adjust weights | Limitation 2 |
| "Good with cats / dogs / rabbits" instead of one yes/no | Three yes/no fields for each animal and a matching question; one more factor in `_factor_checks` | Limitation 3 |
| Register interest in an animal | A button that sends the adopter's details and score to staff, with the adopter's permission, then a staff list of enquiries | Limitation 8, client Q14 |
| Clearer Delete and a Cancel button; red outline on error boxes | Custom CSS for the Delete button now; the other two need a custom Streamlit component or a move to a web framework such as Flask | Limitation 4, U4 |
| Number of matches on the "done" screen | Count results without warnings and show "You have N strong or good matches" | Client review 4 |
| Several branches | Add a branches table and a branch_id on animals and staff; filter by branch | Scope |
| Real tablet and phone testing | Repeat the usability tasks on an iPad and a phone; the browser render checks already pass at those sizes | SC16 |
| Keep the sign-in in a cookie instead of the address | A small custom Streamlit component that sets a secure, HTTP-only cookie | Limitation 7 |
| PostgreSQL instead of SQLite | Only `db.py` changes, because no other module writes SQL | Limitation 5 |
