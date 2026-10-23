@part i Front matter
@her 1 2 3

@img 12-matches-desktop.png | PawMatch: the ranked matches page from the finished system | 15 | key=fig-cover

| Item | Detail |
|---|---|
| Qualification | OCR A Level Computer Science (H446), Component 03/04 Programming Project |
| Project | PawMatch: an adoption matching and animal-records tool for one small rescue |
| Language and tools | Python 3, Streamlit, SQLite (sqlite3), pytest |
| Source code | Branch `opus-rebuild` of the project repository, folder `rebuild/` |
| Tests at hand-in | {{tests_total}} automated tests, {{tests_failed}} failing (pytest, saved in `docs/evidence/`) |

:::note About this version
This is a rebuilt model write-up of the PawMatch project, made after the original was handed in, to show how the same project can be planned, built, tested and evaluated against the OCR marking criteria. It keeps the original research, interview, survey and design work, marked where it is reused, and redesigns the weaker parts. Where AI tools were used (to role-play the client in reviews, to simulate usability testers and to help with checking), this is stated in the text and logged in Appendix A.
:::

@pagebreak
# Contents
@toc

:::note How to read this document
Pages are numbered by section: A (Analysis), D (Design), S (Development and testing to inform development), E (Testing to inform evaluation, and Evaluation), X (Appendices). A reference such as "see D14" means page 14 of the Design section. Source codes in tables: **Q** = client interview question, **S** = stakeholder survey question, **E** = existing solution, **SC** = success criterion, **T** = development test, **P** = post-development test, **U** = usability task, **R** = robustness test.
:::
