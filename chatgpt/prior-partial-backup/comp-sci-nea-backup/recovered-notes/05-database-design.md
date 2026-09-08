# Visible database design

> RECOVERED NOTES — newly organised on 7 September 2026 from the visible source excerpts. This is not an original document, a full transcript, or proof of completed work.

CHAT-07 contains this user-account table proposal. Types and validation wording are retained as design terminology, not converted into executable SQL.

| Field | Stated data type | Key/validation | Stated purpose |
|---|---|---|---|
| user_id | INTEGER | Auto-incrementing primary key | Uniquely identifies each account. |
| name | STRING | Required | Stores the user's name to personalise their experience. |
| email | STRING | Required and unique | Used to log in and contact the user. |
| age | INTEGER | Required; valid range | Stores age to confirm the required adopter age. |
| password_hash | STRING | Required | Stores the securely hashed password. |
| role | STRING | ‘User’ or ‘admin’ | Controls access to the administrator area; normal registrations should receive ‘user’. |

The original role description is cut off, and its capitalisation is inconsistent (`User` versus `user`). This note does not silently resolve that difference.

CHAT-13 identifies accounts, animal records and questionnaire answers as database content. The complete animal/questionnaire schemas, table relationships, SQL creation scripts and database files are not present.

CHAT-05 asks whether SQLite should be used with Streamlit. The answer is not included, so the final database software choice remains unverified.

Sources: CHAT-05, CHAT-07 and CHAT-13.
