---
title: "What top-band sections look like: a worked model"
subtitle: "Different project (GymSlot, a gym class booking app). Pattern only: do not copy wording into PawMatch."
---

Every example below is for an imaginary project, GymSlot, where members book gym classes. It shows the *shape* and
*depth* the OCR marksheet rewards. Your PawMatch sections should follow the same shape with your own algorithms,
your own data and your own words.

# 1. Hierarchy chart (Design: decomposition)

Drawn as boxes in the real write-up; shown here as an indented list.

- GymSlot
    - Accounts
        - Register (validate inputs, check email unique, hash password, store)
        - Log in (find user, verify hash, start session, route by role)
    - Timetable
        - Load classes for a week
        - Filter by day and class type
    - Booking
        - Check class not full
        - Check member has no clash
        - Store booking, update spaces
    - Staff area
        - Add / edit / cancel class

*Why this breakdown:* each box is small enough to build and test on its own, and the order (Accounts, then
Timetable, then Booking) matches what each part depends on.

# 2. Pseudocode with explanation (Design: algorithms)

```
FUNCTION BookClass(member_id, class_id)
    class_record ← GetClass(class_id)
    IF class_record = NULL THEN
        RETURN "Class not found"
    ENDIF
    IF class_record.booked >= class_record.capacity THEN
        RETURN "Class is full"
    ENDIF
    member_bookings ← GetBookings(member_id, class_record.date)
    FOR EACH booking IN member_bookings
        IF booking.start < class_record.end AND class_record.start < booking.end THEN
            RETURN "Clashes with " + booking.class_name
        ENDIF
    NEXT booking
    InsertBooking(member_id, class_id)
    class_record.booked ← class_record.booked + 1
    UpdateClass(class_record)
    RETURN "Booked"
ENDFUNCTION
```

*How it fits the whole solution:* `BookClass` is called by the Booking page. It uses `GetClass` and `GetBookings`
from the database module, so the page never runs SQL itself. The capacity check runs before the clash check because
it needs no extra query.

# 3. Usability features (Design)

| Feature | Where | Why (evidence) |
| --- | --- | --- |
| Full classes greyed out, button disabled | Timetable | 7 of 12 survey replies said booking a full class was the most annoying thing about the current system (S4) |
| Error shown under the field it refers to | Register, Log in | Client asked that errors are clear without reading the whole page (Q6) |
| Same top menu on every page | All pages | Competitor sites E1 and E2 both do this; testers found pages faster |

# 4. Development test plan (Design: test data)

| Test | What and why | Input | Expected | Type |
| --- | --- | --- | --- | --- |
| 1.1 | Register with valid details: core path must work | name "Ama Lee", email ama@x.com, password Gym12345 | Account created, message shown | Normal |
| 1.2 | Password at minimum length: boundary of the 8-character rule | password "Gym12345" (8 chars) | Accepted | Boundary |
| 1.3 | Password one under: boundary on the invalid side | "Gym1234" (7 chars) | Rejected, "at least 8 characters" | Boundary |
| 1.4 | Duplicate email: uniqueness check | email already registered | Rejected, "email already in use" | Invalid |
| 3.2 | Book a full class: capacity check | class with booked = capacity | "Class is full", no booking stored | Invalid |
| 3.4 | Book overlapping classes: clash check | 18:00–19:00 then 18:30–19:30 same day | Second booking refused, names the clash | Invalid |

# 5. One development stage written up (Development)

**Stage 3: Booking. Aim:** implement `BookClass` from Design p. 21 so members can book a class, with the
capacity and clash rules.

**Code:** screenshot of `booking.py` lines 1–48, with comments explaining the overlap condition (why `start < end`
on both sides catches every overlap, including one class inside another).

**Testing:**

| Test | Input | Expected | Actual | Result |
| --- | --- | --- | --- | --- |
| 3.1 | Book a class with spaces | "Booked", spaces down by 1 | As expected (Fig 3.1) | Pass |
| 3.2 | Book a full class | "Class is full" | As expected (Fig 3.2) | Pass |
| 3.4 | Overlapping classes | Refused | **Second booking accepted** (Fig 3.3) | **Fail** |

**Failed test 3.4 and the fix:** the clash check compared only start times (`booking.start = class.start`), so
classes that overlap but start at different times got through. I changed it to the overlap condition in the design
and re-ran 3.4: refused, with the message naming the clash (Fig 3.4). I also added test 3.5 (one class entirely
inside another) because the fix made me realise that case existed.

**Review:** showed the client on 12 March. She asked for the clash message to say *which* class clashes. Change
made: the message now includes the class name (Fig 3.5).

# 6. Evaluation rows (Evaluation)

| Criterion | Evidence | Verdict | Explanation |
| --- | --- | --- | --- |
| Members cannot book a full class | Test 3.2, final test F7 | Met | Both tests refused the booking and showed the message; no booking row stored (Fig F7) |
| Timetable loads in under 2 seconds | Final test F2: 1.4 s with 200 classes | Met | Measured with a timer over 5 runs; slowest was 1.7 s |
| Staff can export attendance | Not built | Not met | Dropped for time. Further development: a CSV export button on the staff page using the existing bookings query |
