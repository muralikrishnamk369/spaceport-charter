# Spaceport Dispatch

A React + FastAPI application for reserving charter ships and reviewing the fleet schedule. SQLite stores reservations. The original client assignment is in `ASSIGNMENT.md`; the supplied `seed.py` is unchanged.

## Requirements

Python 3.12+ and Node.js 22.12+ (tested with Python 3.12 and Node 24). Use Windows **Command Prompt**, not PowerShell, for the commands below. Run one command at a time from this folder.

## Windows setup

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe seed.py > seed.json
.venv\Scripts\python.exe -m backend.import_seed seed.json
cd frontend
npm ci
npm run build
cd ..
.venv\Scripts\python.exe -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

Open http://localhost:8000. API documentation: http://localhost:8000/docs. Keep the server window open. Stop with Ctrl+C; restart using the last command. Saved data is in `data/charters.sqlite3`. Import requires an empty database and refuses to overwrite existing records. Expect five ships and 3,000 bookings. The generator uses relative dates and largely historical bookings; choose **All dates** on the dashboard to see them.

## macOS / Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python seed.py > seed.json
.venv/bin/python -m backend.import_seed seed.json
cd frontend
npm ci
npm run build
cd ..
.venv/bin/python -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

## Development

Run the Python server as above. In another terminal run `npm run dev` inside `frontend` and open the Vite URL. Its `/api` proxy forwards to port 8000. For production, build React before starting Python; FastAPI serves the build and API from the same origin. Rebuild and restart after frontend edits.

## Verify

From the project root on Windows:

```bat
.venv\Scripts\python.exe -m pytest -q
cd frontend
npm test
npm run build
```

On Linux/macOS, substitute `.venv/bin/python` for `.venv\Scripts\python.exe`.

Manual check: choose Serenity and a future date, book a 10–11 AM flight, and find it in Fleet manager on the same date. Return to Charter and select a 30-minute duration. With no other bookings, 9 AM and 11:30 AM should be available; 9:30 AM through 11 AM should be disabled. Test with your computer in Eastern Time: all displayed times must remain Central. Check a narrow browser window and console errors.

## API

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/ships` | Fleet list |
| GET | `/api/availability?shipId=1&day=2026-07-14&duration=60` | Blocked intervals and backend-evaluated departure slots |
| POST | `/api/bookings` | Validate and reserve a flight |
| GET | `/api/bookings?day=2026-07-14` | Dashboard bookings for one Central date |
| GET | `/api/bookings` | Full booking history |

Example POST body (timestamps must include offsets):

```json
{"shipId":1,"pilotName":"Demo Pilot","startTime":"2026-07-14T10:00:00-05:00","endTime":"2026-07-14T11:00:00-05:00"}
```

Unknown ships return 404, conflicts return 409, invalid requests return 422, and database contention after the wait timeout returns 503. Slots are offered every 30 minutes; the API also accepts other flight lengths and departures if all required rules hold. Availability duration is an integer multiple of 30 minutes between 30 and 960. Pilot names are trimmed and limited to 100 characters.

## Design walkthrough

Read `DESIGN.md` for the decisions, concurrency guarantees, limitations, and interview walkthrough. See `VERIFICATION.md` for actual checks performed on this package.

## Troubleshooting

- `python` not found: install Python with PATH enabled; try `py -m venv .venv`.
- Home page 404: run the frontend build, then restart Python.
- Port 8000 occupied: start Python on 8001; production URL becomes http://localhost:8001. For Vite development, also update the proxy target.
- No ships: import seed data before using the app.
- Seed import refuses an existing database: this is intentional. Keep your bookings, or stop the server and explicitly remove `data/charters.sqlite3` and its sidecars if you want a reset.

## Submission

Publish this source folder to your own public GitHub repository after reviewing the code. Do not commit the database, generated seed JSON, dependencies, or environment. `.gitignore` excludes them. The GitHub Actions workflow runs backend tests, frontend tests, and the build. This package has not been published to GitHub.

AI assistance is permitted by the assignment. Review each module and be prepared to justify its behavior and modify it during the technical call.
