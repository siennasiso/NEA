# Drop-in for section 4.3 (after real testing)

How to use it:
1. Run the five testers with `tester-script.pdf` and one `feedback-form.pdf` each (about 3 minutes per tester).
2. Type each form into `evidence-table.xlsx`: sheet **Tasks** (one row per tester and task) and sheet **SUS** (ten answers per tester).
3. Open the **For write-up** sheet; every number and verdict below comes from there.
4. In `docs/nea/E-evaluation.md`, paste the block below **above** the "Honest limitation" note in 4.3, replace each `{{...}}` with the number from the sheet, and write the "What testers found" cells from the comment boxes.
5. Change the limitation note to say the role-played results came first and the real results below replace them. Save the filled forms (photos or scans) as `docs/evidence/usability-real/` and the workbook as `docs/evidence/usability-real.xlsx`, then rebuild.

---

### Usability testing with real users {#e-ureal}
**Method.** {{n}} real people tested the live system on {{date}}: {{profiles, e.g. two first-time adopters, a parent, an older user and a rescue volunteer}}. They used {{devices, e.g. three phones and two laptops}}. Each was given the five tasks on [[d-utasks]] read aloud from a fixed script, with no help. I timed each task and counted wrong taps as errors. Afterwards each tester rated every task from 1 (very easy) to 10 (very hard) and filled in the ten SUS statements on their own. The blank script, form and workbook are in `docs/tester-pack/`; the filled forms are in `docs/evidence/usability-real/`.

@widths 1 1.1 0.6 0.6 0.7 0.6 0.7 2.2 0.8
| Task | Screen | Criterion | Completed | Mean time (s) | Errors | Difficulty | What testers found | Verdict |
|---|---|---|---|---|---|---|---|---|
| U1 register and log in | Register, login | SC6, SC7 | {{U1 completion}} | {{U1 time}} | {{U1 errors}} | {{U1 difficulty}} | {{from the comments}} | {{U1 verdict}} |
| U2 questionnaire | Questionnaire (10 screens) | SC8 | {{U2 completion}} | {{U2 time}} | {{U2 errors}} | {{U2 difficulty}} | {{from the comments; target under 180 s}} | {{U2 verdict}} |
| U3 explain the top match | Matches | SC11 | {{U3 completion}} | {{U3 time}} | {{U3 errors}} | {{U3 difficulty}} | {{did they explain the warning correctly?}} | {{U3 verdict}} |
| U4 staff add, edit, delete | Staff manage, add animal | SC12 | {{U4 completion}} | {{U4 time}} | {{U4 errors}} | {{U4 difficulty}} | {{from the comments}} | {{U4 verdict}} |
| U5 browse and return | Browse, profile | SC4, SC5 | {{U5 completion}} | {{U5 time}} | {{U5 errors}} | {{U5 difficulty}} | {{from the comments}} | {{U5 verdict}} |

**Verdict rule** (set before testing): Met means at least 80% of testers completed the task with a mean difficulty of 4 or less, and for U2 also a mean time of 3 minutes or less (SC8). Partly met means at least 50% completed it. Anything lower is Not met.

**SUS.** The mean SUS score was **{{SUS mean}}** (lowest {{SUS lowest}}, highest {{SUS highest}}); {{k}} of {{n}} testers scored 68 or more. So SC15 is **{{Met / Not met}}**. {{One sentence comparing this with the role-played testers' mean above.}}

**What I changed or would change.** {{For each task that was Partly met or Not met: what went wrong, the change made (with a retest), or why it goes to future development.}}
