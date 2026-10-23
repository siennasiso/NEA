@part X Appendices
# Appendices {#appendices}

## Appendix A: Use of AI tools {#x-ai}
AI tools were used for the tasks below. Every output was checked before it was used, and nothing an AI produced was accepted as evidence without a test or a measurement behind it.

@widths 1.6 2.6 2.6
| Task | What the AI did | How it was checked |
|---|---|---|
| Client reviews 1 to 6 ([[s-feedback1]] to [[s-feedback6]]) | Role-played the client. It was given only the client interview from the analysis and the screenshots of the stage being reviewed, and answered the review questions. | Each answer was compared with what the client said in the interview. Requests were weighed against the design rather than accepted automatically: for example, address and phone fields were declined for data minimisation. Every change that was made is in stage 7 and is tested. |
| Usability testers P1 to P4 ([[e-usability]]) | Simulated four tester profiles doing tasks U1 to U5 from screenshots, rating each task and answering the SUS statements. | The SUS scores were calculated by code from the answers (`nea_data.sus_score`). Findings were acted on only where they pointed to something visible in the screenshots. Treated as a limitation (SC15 partly met). |
| Writing and testing code | An AI coding assistant helped write the code and the tests, working from the original design and code. | Every rule is covered by an automated test written from the design's test plan, and failing runs were saved before each fix (Appendix C). Nothing was kept that did not pass the tests. |
| Research | Searched for further existing solutions (E4 to E8) and summarised their public pages. | Every source was opened and read; the links are in Appendix B. |
| Proofreading | Suggested shorter, plainer wording in this write-up. | All technical claims were checked against the code, the tests and the measurements. |

The AI did **not** decide the success criteria, the weights or the design; those come from the client interview, the survey and the design section.

## Appendix B: References {#x-refs}
@widths 0.7 2.2 3.8
| Ref | Source | Link |
|---|---|---|
| E1 to E3 | Dogs Trust, RSPCA Find a Pet, Petfinder | See the references on [[a-refs]] |
| E4 | ASPCA Meet Your Match (Canine-ality) | https://www.aspca.org/meet-your-match/canine-ality-quiz<br>Guide: https://www.aspcapro.org/sites/default/files/aspca-canine-ality-guide-2015.pdf |
| E5 | Battersea Dogs and Cats Home | https://www.battersea.org.uk/adopt |
| E6 | Woodgreen Pets Charity | https://woodgreen.org.uk/adoption-and-rehoming |
| E7 | Shelterluv shelter software | https://www.shelterluv.com |
| E8 | OkCupid (question-based matching) | https://www.okcupid.com/ |
| Also read | Blue Cross rehoming | https://www.bluecross.org.uk/rehoming |
| SUS | Brooke, J. (1996) "SUS: a quick and dirty usability scale", in *Usability Evaluation in Industry*, Taylor and Francis | The average score of 68 is used as the target |
| WCAG | W3C Web Content Accessibility Guidelines 2.2 (contrast minimum 4.5:1) | https://www.w3.org/TR/WCAG22/ |
| scrypt | Python `hashlib.scrypt` | https://docs.python.org/3/library/hashlib.html |
| Passwords | OWASP Password Storage Cheat Sheet | https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html |
| Streamlit | Streamlit documentation, including AppTest | https://docs.streamlit.io |
| SQLite | SQLite documentation | https://www.sqlite.org/docs.html |

## Appendix C: Evidence files {#x-evidence}
All files are in the project repository under `docs/evidence/`, so every result in this document can be checked or re-run.

@widths 2.6 4.2
| File | What it holds |
|---|---|
| `pytest-junit.xml` | The final run of all {{tests_total}} automated tests ({{tests_failed}} failures) |
| `stage1-pytest.txt`, `stage2-pytest.txt`, `stage3-pytest.txt`, `stage5-pytest.txt`, `review-pytest.txt` | The test run at the end of each stage |
| `stage3-fail1-apptest-path.txt`, `stage3-fail2-error-box.txt`, `stage5-fail-design-recheck.txt`, `stage5-fail-regression-auth.txt`, `style-test-before.txt`, `review-fail1-confirm-blank.txt`, `review-fail2-hours-prefilled.txt` | The failing runs shown in the fail, fix and retest boxes, saved before each fix |
| `rendered-audit-desktop.json`, `rendered-audit-tablet.json` | The browser audit of contrast, text size and keyboard focus on every screen at 1440 and 1024 px |
| `measurements.json` | Capacity and speed results from `docs/tools/measure_v2.py` |
| `client-reviews.json` | The client review answers, and the usability testers' ratings and SUS answers |

## Appendix D: How to install and run {#x-run}
1. Install Python 3.13, then in the `rebuild/` folder run `pip install -r requirements.txt`.
2. To create the first staff account, set `PAWMATCH_ADMIN_EMAIL` and `PAWMATCH_ADMIN_PASSWORD` before starting.
3. Start the system with `streamlit run streamlit_app.py`. The first start creates `data/pawmatch.db` and fills it with demo animals.
4. Run the tests with `pip install -r requirements-dev.txt` and then `pytest`.
5. Back up the system by copying `data/pawmatch.db`.

## Appendix E: Program listing {#x-code}
The full listing of the rules layer (`pawmatch/`) follows. This is where every success criterion about data, scoring, security and storage is met. The screens (`webui/`) and the stylesheet (`webui/pawmatch_style.py`, mostly the pink theme carried over from the original design) are in the repository; the important parts are shown in the development section.

@widths 2 4.6
| File | Purpose |
|---|---|
| `streamlit_app.py` | Starts the system, prepares the database and opens the page asked for |
| `pawmatch/models.py` | The data classes and fixed lists (species, sizes, statuses, roles) |
| `pawmatch/validation.py` | Every validation rule from the design, with clear messages |
| `pawmatch/auth.py` | Registration, login and password hashing |
| `pawmatch/matching.py` | The weighted score, warnings, allergy cap, categories and ranking |
| `pawmatch/db.py` | The only module that runs SQL: schema, upgrades and queries |
| `pawmatch/services.py` | Staff-only actions, each checking the user's role first |
| `pawmatch/seed.py` | Demo animals and the first staff account |

@pagebreak
@code streamlit_app.py:1-28 | Entry point
@code pawmatch/models.py:1-132 | Data classes and fixed lists
@code pawmatch/validation.py:1-272 | Validation rules
@code pawmatch/auth.py:1-109 | Accounts and password hashing
@code pawmatch/matching.py:1-166 | Matching algorithm
@code pawmatch/services.py:1-102 | Staff-only actions
@code pawmatch/db.py:1-311 | Database access
