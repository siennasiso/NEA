# Tester pack: real usability testing in 15 minutes

The write-up's usability results (section 4.3) currently come from AI role-played testers. This pack swaps them for real ones. You need five people (friends, family, a teacher, a rescue volunteer if possible), a phone and a stopwatch.

1. **Print** `tester-script.pdf` (one copy, for you) and `feedback-form.pdf` (one per tester, two pages each).
2. **Set up (1 minute).** Open https://pawmatch.dtc-storefront.workers.dev on the device and check nobody is signed in. For task U4, sign in with the staff demo account first; ask whoever set up the app for its login, which is never written in this repo.
3. **Test each person (about 3 minutes each, 15 in all).** Read the five tasks word for word. Time them and count wrong taps, but don't help. Then they rate each task and fill in the SUS page alone.
4. **Type it in (5 minutes).** Put each form into `evidence-table.xlsx`: one row per tester and task on **Tasks**, ten answers per tester on **SUS**. The **For write-up** sheet works out completion, mean times, SUS and each verdict.
5. **Paste it into the write-up.** Copy the block in `drop-in.md` into section 4.3 of `docs/nea/E-evaluation.md`, fill each `{{...}}` from the For write-up sheet, and write the "What testers found" cells from their comments.
6. **Keep the evidence and rebuild.** Save photos of the filled forms in `docs/evidence/usability-real/` and the workbook as `docs/evidence/usability-real.xlsx`, then run `.venv/bin/python docs/tools/build_nea_v2.py`.

Files: `tester-script.md/.pdf`, `feedback-form.md/.pdf`, `evidence-table.xlsx`, `drop-in.md`. To regenerate them: `make_pdfs.py` (needs pandoc and Playwright) and `make_xlsx.py` (needs openpyxl).
