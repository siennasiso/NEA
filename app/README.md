# PawMatch Streamlit prototype

This project contains the connected login, registration, adopter dashboard and administrator dashboard.

## Run the app

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Create the administrator account

Public registrations always receive the role `user`. Create the shelter administrator separately:

```bash
python create_admin.py
```

The password is stored as a salted scrypt hash. After logging in, an administrator is redirected to `pages/7_Admin_Dashboard.py`; a normal user is redirected to the adopter homepage.

## Optional demonstration data

```bash
python load_demo_animals.py
```

This inserts four sample records only when the animals table is empty. Remove demonstration records before the final submission if they are not part of the shelter's real data.

## Admin functions

- role-based access check;
- overview totals and data-quality feedback;
- search and filtering by name, breed, species and status;
- create, read, update and delete animal records;
- matching-requirement fields used by the compatibility algorithm;
- field validation and parameterised SQLite statements;
- explicit confirmation before permanent deletion.
