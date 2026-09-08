# Authentication and validation

> RECOVERED NOTES — newly organised on 7 September 2026 from the visible source excerpts. This is not an original document, a full transcript, or proof of completed work.

The following rules are transcribed into a table from the visible registration-validation request in CHAT-02. They are user-stated design rules, not a completed implementation or an independent security assessment.

| Field/process | Visible rule |
|---|---|
| Name | Reject empty/space-only input; length between 2 and 50 characters; trim leading/trailing spaces. |
| Email | Reject empty/space-only input; require an @ and a domain; query the database for uniqueness; trim leading/trailing spaces; convert to lowercase. |
| Age | Presence check; whole-number type check; age at least 18. |
| Password | Reject empty/space-only input; the August excerpt says more than 8 characters. |
| Password confirmation | Must exactly match the original password. |
| Password storage | Hash a valid password before insertion; do not store the original password. |

CHAT-10 additionally describes collecting name, email, age and password during registration, feedback for missing/invalid input, errors for incorrect login details, nonblank login fields, comparing login details against user records and establishing a session. Its source text ends mid-sentence.

**Unresolved source difference:** CHAT-10 says “Password minimum 8 characters”; CHAT-02 says “password must be more than 8 characters”. These differ at a length of exactly eight. Both are preserved; no final decision is inferred.

The requested A-level design pseudocode and earlier assistant responses were not recoverable. No hashing algorithm, implementation code, lockout policy or recovery mechanism is specified in the available text.

Sources: CHAT-02 and CHAT-10.
