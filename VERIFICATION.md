# Verification of this package

- Backend: **23 tests passed**, covering exact turnaround boundaries, overlap, opening/closing times, invalid inputs, Central summer/winter and DST transition dates, ship independence, persistence, transactional import rollback, repeat import refusal, and eight concurrent booking attempts.
- Frontend: **2 interaction tests passed**, covering server availability, booking submission, fleet display, all-history selection, conflict refresh, and a preserved conflict message.
- Production React build: passed with Vite 7.3.6 and React dependencies recorded in package-lock.json.
- Original seed generation and import: passed, five ships and 3,000 bookings.
- Production server smoke check: HTML, five-ship fleet, 3,000 bookings, and dedicated availability endpoint passed.
- Python 3.12, Node 24.19.0. Direct Python versions are pinned in requirements.txt.
- A Starlette test-client deprecation warning was emitted for its httpx integration. Tests passed; this is a future compatibility note.
- **Real-browser visual verification remains pending.** The environment lacked a Chromium executable, and the browser download returned an invalid archive. DOM interaction tests ran successfully, but desktop/mobile appearance and browser-console checks must be completed using the manual steps in README.md.
- GitHub publication and remote CI execution have not been performed.

No generated database, dependencies, seed JSON, virtual environment, or frontend build is included in the source archive. Run the setup commands before launching.
