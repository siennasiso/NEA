# Design fixes

Page numbers refer to `documents/design/current/design-first-draft.pdf`. If you have a newer draft, use that.

- [ ] **Pseudocode on the five empty pages** (pp. 14, 21, 32, 39, 48): login and registration, admin add/edit/delete,
      main menu, browse and filter, compatibility score. Turn each flowchart you already drew into pseudocode.
- [ ] **Define the score exactly.** The five weights total 72 (20 + 15 + 15 + 12 + 10). Write down how points become a
      percentage, whether failing a hard rule (children, garden) makes the animal unsuitable or only loses points,
      and the cut-offs for strong / good / possible / low.
- [ ] **One worked example**: one adopter and two animals, scored by hand. Reuse it later as test data.
- [ ] **Usability features section**: each feature, where it appears, and why (point to the survey or interview).
- [ ] **Development test plan** (p. 57 is only a heading): 8 to 12 tests per component, mixing normal, boundary and
      invalid data. Columns are in the template.
- [ ] **Post-development test plan**: one test per success criterion, plus usability tests with stakeholders.
- [ ] **Hierarchy chart** at the start of Design: the five components broken into sub-tasks.
- [ ] **Consistency pass**
      - Login uses email or username? The draft uses both.
      - Password "at least 8" or "more than 8" characters? The draft says both.
      - Results show the top 3, top 4 or top 5? Analysis says at least 4; design says 3 or 5.
      - Spellings in names: `booleen`, `preffered_species`, `questionaire_completed`, `reccomended_animals`,
        `QuestionaireReponses`.

Also in Analysis: make the success criteria measurable (a time, a number, or a rating from testers), e.g. "results
appear within 2 seconds", "stores at least 50 animals", "ease of use rated 8/10 or higher by 5 testers".
