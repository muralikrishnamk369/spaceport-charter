# Implementation decisions

## Structure

`backend/scheduling.py` expresses interval and operating-hour rules without FastAPI or SQL. `backend/storage.py` owns SQLite queries and transaction scope. `backend/api.py` translates HTTP inputs and errors into domain operations. `backend/import_seed.py` imports the supplied seed data atomically using the same reservation rules.

React is divided into `Charter`, `Fleet`, and shared API/time-format helpers. JavaScript keeps this small assessment focused; runtime server validation remains authoritative. React escapes pilot names when rendering them.

## Intervals and turnaround

A booking is the half-open interval [departure, arrival). For an existing flight, a new one is allowed only if the existing arrival is at or before the proposed departure minus 30 minutes, or the existing departure is at or after the proposed arrival plus 30 minutes. Taking the negation of these alternatives finds a conflict. Equality permits an exact 30-minute gap. Different ships are independent.

Availability expands existing flights 30 minutes in both directions, clips those spans to opening hours, and merges touching or overlapping spans. The backend tests each proposed departure and duration against that union. The browser never downloads dashboard bookings to derive availability. Availability contains no pilot names.

## Time zones

`America/Chicago` determines 6 AM–10 PM operating hours, including summer and winter offsets. All accepted requests carry explicit offsets. Storage uses UTC epoch seconds. Availability departures carry Central offsets and server-generated labels; the dashboard explicitly uses Central Intl formatting. A booking cannot cross the operating day's closing time. Refueling may extend beyond closing; the flight itself must fit within the operating hours. Historical bookings are allowed because the brief does not prohibit them.

## Concurrency

The repository acquires SQLite's writer lock with `BEGIN IMMEDIATE` before reading conflicts. Both the conflict check and insert run inside that transaction. A competing reservation waits for the first commit, then sees the saved reservation. The concurrency test submits eight simultaneous attempts for the same slot and requires exactly one success and seven conflicts.

SQLite serializes writes even for different ships. That is acceptable for five vessels. Direct writes bypassing this repository do not receive its scheduling validation. For a larger deployment, use PostgreSQL and enforce nonoverlapping buffered ranges in the database, with migrations and operational monitoring.

## UI behavior

Changing the vessel, day, or duration clears the selected departure and cancels stale availability requests. Submission disables form controls and duplicate clicks. A 409 response clears the selection, refreshes availability, and keeps the conflict explanation visible. Confirmed reservations persist across restarts. Switching to Fleet manager fetches current reservations rather than reusing a stale booking cache.

The dashboard supports a single Central date or all history, with ship-grouped tables and empty states. Date and duration selectors are implementation choices, not additional assessment requirements.

## Limits and next steps

No authentication is included, as requested. This is a local assessment app, not a hardened public service. Full history has no pagination; 3,000 seeded rows are manageable, but server pagination and narrower queries would help at scale. There are no cancellation/edit endpoints because the assignment requires booking and viewing only. The 30-minute departure grid is a UI choice; the POST endpoint validates arbitrary aware timestamps. Automated UI tests cover the core flow and conflicts, but not every error or accessibility scenario.

## Explain it during the call

1. Start in scheduling.py: explain operating hours and exact turnaround boundaries.
2. Show storage.py: explain why the writer lock precedes the conflict query.
3. Show api.py: explain input validation, response codes, and dedicated availability.
4. Open Charter.jsx: trace a selection, reservation, and conflict recovery.
5. Open Fleet.jsx: demonstrate grouped bookings and explicit Central formatting.
6. Run tests and describe the database and pagination tradeoffs honestly.

Useful live changes to practice: add a 150-minute UI duration, change the turnaround constant, add a ship filter to the dashboard, or paginate booking history.
