@part A Analysis
# 1 Analysis {#analysis}

## 1.1 Problem definition and stakeholders {#a-problem}
@her 30-46

### The client, made smaller {#a-client}
To keep the project to a size that one person can build and test properly, the scope is fixed as follows.

| Decision | What it means for PawMatch |
|---|---|
| **One client organisation** | PawMatch is built for **one small, single-site rescue**: about 10 to 20 animals at any time (dogs, cats and rabbits), run by two or three staff or volunteers. My client does not work for a rescue, but her pet-care job means she has looked after a wide range of animals and knows what each needs. She therefore acts as the rescue's welfare adviser: she defines the welfare rules and approves each stage. |
| **Adopters are users, not the client** | Members of the public use PawMatch to browse and to see how well they suit each animal. Their needs come from the survey (27 responses) and from usability testing, but the client decides the rules. |
| **Not in scope** | Several branches, online applications or payments, fostering, vet records, or any species other than dogs, cats and rabbits. These are explained under Limitations ([[a-limits]]). |

### Stakeholders and how each will use the system {#a-stakeholders}
@widths 1.3 3 3 2.2
| Stakeholder | How they will use PawMatch | Why PawMatch is appropriate for them | Evidence |
|---|---|---|---|
| **Rescue staff and volunteers** (the client's side) | Sign in with a staff account; add, edit and delete animal records with photos; change an animal's status to Reserved or Adopted; see an overview of records that need attention. | Without a shared system, assessments are manual and records easily go out of date (Q5, Q15). One validated form per animal keeps records consistent, and the same rules are applied to every adopter, which removes the subjective judgement the client described. | Q5, Q6, Q12, Q15 |
| **Potential adopters** (primary users) | Create an account, browse available animals with filters, open profiles, answer a 10-question lifestyle questionnaire once, then see every animal ranked by suitability with reasons. | Many choose on looks (S3: only 48.1% choose on lifestyle). They need a quick, friendly way to see which animals fit their home *before* they contact the rescue, and an explanation they can act on. Experience ranges from first-time owners to experienced carers, so the language must be plain. | Q1, Q3, Q7, S3, S5, S6, S7 |
| **The animals** (indirect) | Never use the system, but are affected by its output. | Every scoring rule protects an animal's welfare: the client named space, allergies and young children as the most important things to check (Q10). | Q1, Q10, S9 |
| **The client** | Reviews each development stage and signs off the final system. | She has the animal-care knowledge to judge whether a match is sensible. | Q1 to Q15 |

### Why this problem is amenable to a computational approach {#a-amenable}
@her 50-102

The table below ties each computational method to a specific part of PawMatch, so it is clear *why* a program solves this problem better than the current paper process.

@widths 1.4 3.6 3
| Feature of the problem | Why a computer handles it well | Where it appears in PawMatch |
|---|---|---|
| The suitability of every adopter for every animal must be judged the same way each time | A fixed algorithm applies identical weighted rules to every pair, which a busy volunteer cannot do consistently by hand | `score_animal` and `rank_animals` (pseudocode on [[d-matching]]) |
| 20 animals × 7 factors = 140 comparisons for every adopter, repeated whenever an animal is added | Repetitive arithmetic and sorting are instant for a computer (500 animals scored in {{submit_max}} s at worst, measured in section 4.1, page [[e-speed]]) | Questionnaire submit: every Available animal is scored and stored |
| The information is structured (yes/no, numbered levels, ranges) | It can be stored in typed database fields and validated on entry, so the algorithm never receives impossible values | Four SQLite tables with CHECK constraints ([[d-database]]) |
| Records change often (new arrivals, adoptions) | A database with an admin form updates everything at once; old match results are recalculated on the next submission | Staff dashboard and status field |
| The output must explain itself | The program can list exactly which rules passed and failed for each animal | Met / not met / warning lists on each match |
| Passwords and staff powers must be protected | Hashing and role checks are things software does reliably | scrypt hashing, role checked on every staff action |

What the computer should **not** decide is also clear from the interview: the final adoption decision stays with people (Q4), so PawMatch ranks and explains but never approves or refuses anyone.

## 1.2 Research {#a-research}
@her 105-123

### Existing solution 1: Dogs Trust {#a-e1}
@her 126-143

:::verdict Features I will take from Dogs Trust (E1)
- **Adopt:** collecting information about the adopter's home and lifestyle before matching; a calm, consistent colour scheme with clear headings.
- **Adapt:** its matching is done by phone with staff. PawMatch automates the first sift so staff time goes on the best-matched adopters.
- **Reject:** dog-only scope and long pages.
:::

### Existing solution 2: RSPCA Find a Pet {#a-e2}
@her 154-170

:::verdict Features I will take from the RSPCA (E2)
- **Adopt:** several species organised into clear categories; large animal photos on compact cards; a species filter.
- **Adapt:** the RSPCA shows suitability notes as free text. PawMatch turns these into structured fields (child-safe, good with pets, hours alone) so they can be scored.
- **Reject:** the per-pet application form, which the client does not want (Q4).
:::

### Existing solution 3: Petfinder {#a-e3}
@her 185-197

:::verdict Features I will take from Petfinder (E3)
- **Adopt:** an adopter questionnaire; filters for species and size.
- **Adapt:** Petfinder uses answers to filter, not to score. PawMatch gives a percentage and a reason for every animal.
- **Reject:** the very large national listing, which is the opposite of a single small rescue.
:::

@her 200-203

### Existing solutions 4 to 8: wider research {#a-more}
Three existing solutions do not show enough of the range of approaches, so I looked at five more, chosen to cover the three parts of PawMatch: the adopter questionnaire (E4, E6), the staff back office (E7), the public listing (E5) and weighted matching outside animal adoption (E8).

@widths 1.5 3.4 3.1
| Solution | What it does (checked October 2026) | Lesson for PawMatch |
|---|---|---|
| **E4 ASPCA Meet Your Match** (US) | An 18-question adopter survey for dogs, combined with a staff behaviour assessment, puts each dog into one of nine colour-coded types. Counsellors use the result as guidance. | The closest idea to PawMatch, and it confirms the client's view that a score should *guide* staff, not decide. But it classifies dogs into types rather than ranking every animal with reasons. |
| **E5 Battersea rehoming** (UK) | Keyword search and a "best match" claim with no stated method; clear "Meet the dogs" route; accessibility policy (skip link, alt text). | An unexplained match is not trusted. PawMatch must say *why*. Battersea's accessibility commitments set the bar for contrast and text size. |
| **E6 Woodgreen Pets Charity** (UK) | An online questionnaire on home, lifestyle and type of dog that stays valid for six weeks; staff make contact only on a potential match. | Answer once and reuse the answers: PawMatch stores the questionnaire so adopters do not repeat it, and lets them update it later. |
| **E7 Shelterluv** (shelter software) | Staff suite: medical records, fosters, adoption checkout. Staff log in; fosters have limited rights. No public matching. | Separate staff and public roles with different rights. Its feature list is far bigger than a small rescue needs, which is why a simple tool is justified. |
| **E8 OkCupid** (dating analogue) | Each question has an importance weight; a percentage is calculated over shared answers and used to rank people. | Weighted scoring normalised to a percentage is a proven way to rank. PawMatch avoids its weakness (the percentage looks high when few questions are shared) because every adopter answers every question. |

### Features selected from all eight solutions {#a-select}
@widths 2.6 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.5 0.9
| Feature | E1 | E2 | E3 | E4 | E5 | E6 | E7 | E8 | Decision |
|---|---|---|---|---|---|---|---|---|---|
| Lifestyle questionnaire before matching | ✓ | | ✓ | ✓ | | ✓ | | ✓ | Adopt |
| Weighted score shown as a percentage | | | | ~ | | | | ✓ | Adopt |
| Every animal ranked, best first, with reasons | | | | | ~ | | | ~ | Adopt (gap none fill) |
| Warning for a welfare risk instead of blocking | ✓ | | | ✓ | | | | | Adopt |
| Species and size filters on browse | | ✓ | ✓ | | ✓ | | | | Adopt |
| Answers stored and reusable | | | | | | ✓ | | ✓ | Adopt |
| Staff add / edit / delete animal records | | | | | | | ✓ | | Adopt |
| Separate staff and adopter roles | | | | | | | ✓ | | Adopt |
| Apply or pay online | | ✓ | | | | | ✓ | | Reject (Q4) |
| Staff behaviour assessment feeding the score | | | | ✓ | | | | | Adapt: staff enter needs as fields |
| Location search across many centres | | ✓ | ✓ | | ✓ | | | | Reject (one site) |

✓ = has it, ~ = partly. Sources E1 to E8 are listed in Appendix B.

## 1.3 Client interview {#a-interview}
@her 220-266

## 1.4 Stakeholder survey {#a-survey}
@her 281-404

## 1.5 Proposed solution {#a-solution}
@her 429-432

### The solution in specific terms {#a-specific}
@widths 1.6 5.4
| Part | Exactly what will be built |
|---|---|
| Accounts | Register with name, email, age (18 or over) and a password of at least 8 characters, typed twice. Passwords stored as salted scrypt hashes. One login form for everyone; the role stored in the database decides what each person sees. Optional "Continue with Google". |
| Browse | Cards for every Available animal (photo, name, species, breed, age, size), filtered by species, size and a text search; a profile page per animal. |
| Questionnaire | 10 questions, one per screen, in four sections (home, household, lifestyle, preferences); card buttons for choices, a number box for hours alone; Next is disabled until the question is answered. |
| Matching | Weighted welfare factors (time alone, children, space, activity, garden and the others the client named), normalised to a percentage: points earned ÷ total points × 100. An unmet welfare requirement raises a warning rather than hiding the animal (Q3); an allergy can never give a strong match (Q10). Species and size preferences change the order only. Weights are designed on [[d-weights]] and finalised on [[s-weights]]. |
| Results | At least 4 animals (top 5 shown, "show all" toggle), animals without warnings first, each with met and not-met reasons and a statement that staff make the final decision. |
| Staff dashboard | Overview of records, a table of all animals, and add / edit / delete forms with the same validation as the database; photos PNG or JPG up to 2 MB; delete needs a tick-box confirmation. |

## 1.6 Hardware and software requirements {#a-hardware}
@her 445-485

### Minimum requirements for running PawMatch {#a-minimum}
The section above describes the computer I develop on. The requirements for the *users* and for the machine that runs the system are below, with the reason for each.

@widths 1.4 2.6 3
| Who | Minimum | Justification |
|---|---|---|
| Adopter or staff device | Any laptop, desktop or tablet (screen at least 1024 px wide) with a current browser (Chrome, Edge, Safari or Firefox); internet connection | Streamlit runs in the browser, so nothing is installed. 1024 px is a landscape tablet, the smallest screen tested (section 4.1, page [[e-results]]). |
| Input | Mouse or trackpad and keyboard, or touch | Card buttons are large enough to tap; every control can also be reached with the Tab key. |
| Server (runs the app) | Python 3.11 or later; 1 CPU core, 1 GB RAM; 100 MB disk for the program and database plus up to 2 MB per animal photo | Measured on 500 animals: a submission takes under 0.1 s (section 4.1, page [[e-speed]]). Photos are limited to 2 MB each, so 20 animals need at most 40 MB. |
| Software (server) | `streamlit 1.66.1`, `pillow 13.0.0`, `Authlib 1.9.1`, `httpx 0.28.1` (pinned in `requirements.txt`); SQLite is built into Python | Exact versions mean every install behaves like the tested one. |
| Developer tools | Visual Studio Code, pytest, Git | pytest runs the {{tests_total}} automated tests; Git records each stage as a commit. |

## 1.7 Limitations {#a-limits}
Each limitation from my original list is shown with its cause, its effect, and how PawMatch reduces the risk.

@widths 1.6 1.9 1.9 2.6
| Limitation | Cause | Effect | How it is reduced |
|---|---|---|---|
| One rescue only | Built for a small single-site client | Cannot be shared by several branches | Data model has no branch field; adding one later is listed as future development |
| Dogs, cats and rabbits only | Matching rules researched for these three | Other species cannot be listed | Species are a fixed list checked by validation and the database; adding one is a single change |
| The score is guidance, not a decision | A short questionnaire cannot capture everything (Q4) | An adopter might over-trust a high score | Every results page says staff make the final decision; warnings are shown first |
| No online adoption process | Client wants staff to meet adopters (Q4) | Adopters still contact the rescue themselves | "What happens next" text on the home and results pages |
| Accuracy depends on honest answers | Answers cannot be checked by the system | A dishonest adopter can score highly | Staff home check remains part of the real process |
| Rule-based, not machine learning | No past adoption data to learn from | Weights are set by judgement, not proven by data | Weights come from the client and survey and are easy to change in one place ([[d-weights]]) |
| Records are updated by hand | Staff enter every change | Out-of-date records give wrong matches | Overview flags records missing a photo or with a short description |
| No live chat or animations | Time available and Streamlit's design | Less engaging than large charity sites | Friendly pastel style and photos instead (Q11) |

## 1.8 Requirements and success criteria {#a-criteria}
My research produced the detailed requirements below (numbered by feature area, 1 to 9). The list is long and its items cannot each be measured, so it is kept as the **requirements list**, and the **success criteria** that follow combine them into 16 measurable statements. Each success criterion states how it will be measured and links to the post-development tests on [[d-postplan]].

@her 521-523

### Success criteria {#a-sc}
@widths 0.5 2.6 2.8 0.9 0.9
| SC | Success criterion | How it will be measured (target) | Requirements | Source |
|---|---|---|---|---|
| SC1 | The interface uses the client's soft pink palette, clear headings and obvious buttons | Every text colour reaches a contrast of 4.5:1 and no text is below 12 px, on every screen (automated audit of all screens); client approves the look | 1 | Q11, S6 |
| SC2 | Every page can be reached from one consistent menu | Each page reachable in 1 click from the menu; staff items never shown to adopters | 1, 8 | Q6, E1 to E3 |
| SC3 | The home page explains that PawMatch is about suitability and that staff decide | Text present; a button opens the questionnaire in 1 click | 2 | Q1, Q3, Q7 |
| SC4 | Adopters can browse every Available animal and narrow the list | All Available animals shown as cards with photo, name, species, breed, age; filters for species and size and a search; at least 3 species | 3 | Q8, E2, E3 |
| SC5 | Each animal has a full profile loaded from the database | Profile shows all stored fields and needs; back link returns to the list | 4 | Q2 |
| SC6 | Registration rejects every invalid input with a message beside the field | Each of name, email, age, password and confirm tested with normal, boundary and invalid data; duplicate email refused | 5 | Q9, Q12 |
| SC7 | Accounts are secure | Passwords stored only as salted hashes; one message for a wrong email or a wrong password; sign-out ends the session | 5 | Q12 |
| SC8 | The questionnaire collects all 10 answers, one question per screen, and cannot be skipped | 10 screens in 4 sections; Next disabled until answered; completed in under 3 minutes | 6 | Q1, S5, S6 |
| SC9 | The score is calculated correctly from the weighted factors | Matches a hand calculation exactly ([[s-worked]]); each factor changes the score by its weight; allergy caps at 39% | 7 | Q10, S5 |
| SC10 | Results are ranked quickly and safely | At least 4 shown; animals with warnings never above those without; 500 animals scored in under 1 s | 7 | Q3, Q14 |
| SC11 | Each result explains itself | Every match lists requirements met, not met and welfare warnings, with a statement that staff decide | 7 | Q3, E5 |
| SC12 | Staff can add, edit and delete animals with full validation | Each field rejects invalid data; photo PNG/JPG up to 2 MB; delete needs confirmation | 8, 9 | Q5 |
| SC13 | Adopters can never reach or use staff functions | Every staff action refused for adopter and signed-out users (automated tests) | 8 | Q12 |
| SC14 | Data is stored reliably and scales beyond the rescue's size | 4 tables with constraints; works with 500 animals and 100 users; browse page loads in under 3 s | 9 | Q15 |
| SC15 | Users find the system easy to use | Average System Usability Scale score of 68 or more (the average for websites: Brooke, 1996, Appendix B); client signs off the final stage | 1, 6, 7 | Q6, S6 |
| SC16 | Works on laptop and tablet screens | No clipped text or controls at 1440 px and 1024 px widths | 1 | Q6, Q13 |

## 1.9 References {#a-refs}
@her 539-547

The sources for E4 to E8 are listed in Appendix B ([[x-refs]]).

### Glossary {#a-glossary}
@widths 1.5 4.5
| Term | Meaning in this project |
|---|---|
| CRUD | Create, read, update and delete: the four things staff can do to an animal record |
| Hash | A one-way scrambled version of a password. The program can check a typed password against it, but the password cannot be worked back out from it |
| Salt | Random data added to each password before hashing, so two people with the same password get different hashes |
| scrypt | The hashing method used for passwords (Python's `hashlib.scrypt`). It is deliberately slow, which makes guessing many passwords expensive |
| Streamlit | The Python library that turns the program's pages into a website in the browser |
| SQLite | The database. It keeps all tables in one file and comes with Python, so nothing extra has to be installed |
| Primary key / foreign key | A primary key is the unique ID of a row (for example animal_id). A foreign key is a column that stores another table's primary key, which links the two rows |
| Session token | A long random code created at sign-in and stored in the database. It keeps the user signed in when the page is reloaded, and ends at sign-out or after 12 hours |
| WCAG | Web Content Accessibility Guidelines, the standard for readable and accessible websites (contrast, text size, focus) |
| SUS | System Usability Scale: ten statements, each rated 1 to 5, that give a usability score out of 100 (Brooke, 1996) |
