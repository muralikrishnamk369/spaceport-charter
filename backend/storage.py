"""SQLite persistence; reservations acquire the writer lock before checking conflicts."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from .scheduling import TURNAROUND

BUFFER_SECONDS = TURNAROUND.total_seconds()

SCHEMA = '''
CREATE TABLE IF NOT EXISTS ship(id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS reservation(
 id INTEGER PRIMARY KEY,
 ship_id INTEGER NOT NULL REFERENCES ship(id),
 pilot TEXT NOT NULL CHECK(length(trim(pilot)) BETWEEN 1 AND 100),
 departure REAL NOT NULL,
 arrival REAL NOT NULL CHECK(arrival > departure)
);
CREATE INDEX IF NOT EXISTS reservation_ship_departure ON reservation(ship_id, departure);
'''


class UnknownShip(Exception):
    pass


class SlotTaken(Exception):
    pass


class Repository:
    def __init__(self, path: str):
        self.path = path

    @contextmanager
    def connection(self, writing=False):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        try:
            if writing:
                db.execute('BEGIN IMMEDIATE')
            yield db
            if writing:
                db.commit()
        except Exception:
            if writing:
                db.rollback()
            raise
        finally:
            db.close()

    def initialize(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.executescript(SCHEMA)

    def ships(self):
        with self.connection() as db:
            return [dict(row) for row in db.execute('SELECT id,name FROM ship ORDER BY id')]

    @staticmethod
    def require_ship(db, ship_id):
        if db.execute('SELECT id FROM ship WHERE id=?', (ship_id,)).fetchone() is None:
            raise UnknownShip

    def flight_times(self, ship_id, opening, closing):
        with self.connection() as db:
            self.require_ship(db, ship_id)
            rows = db.execute('SELECT departure,arrival FROM reservation WHERE ship_id=? '
                              'AND arrival > ? AND departure < ? ORDER BY departure',
                              (ship_id, opening - BUFFER_SECONDS, closing + BUFFER_SECONDS)).fetchall()
        return [(datetime.fromtimestamp(row['departure'], timezone.utc),
                 datetime.fromtimestamp(row['arrival'], timezone.utc)) for row in rows]

    @staticmethod
    def reserve(db, ship_id, pilot, departure, arrival):
        Repository.require_ship(db, ship_id)
        # Reject unless the proposed flight is at least 30 minutes away in either direction.
        collision = db.execute('SELECT id FROM reservation WHERE ship_id=? '
                               'AND NOT (arrival <= ? OR departure >= ?) LIMIT 1',
                               (ship_id, departure - BUFFER_SECONDS, arrival + BUFFER_SECONDS)).fetchone()
        if collision:
            raise SlotTaken
        cursor = db.execute('INSERT INTO reservation(ship_id,pilot,departure,arrival) VALUES(?,?,?,?)',
                            (ship_id, pilot, departure, arrival))
        return Repository.serialize(db.execute('SELECT * FROM reservation WHERE id=?',
                                               (cursor.lastrowid,)).fetchone())

    def create(self, ship_id, pilot, departure, arrival):
        with self.connection(writing=True) as db:
            return self.reserve(db, ship_id, pilot, departure, arrival)

    @staticmethod
    def serialize(row):
        return {'id': row['id'], 'shipId': row['ship_id'], 'pilotName': row['pilot'],
                'startTime': datetime.fromtimestamp(row['departure'], timezone.utc).isoformat(),
                'endTime': datetime.fromtimestamp(row['arrival'], timezone.utc).isoformat()}

    def bookings(self, hours=None):
        with self.connection() as db:
            sql = 'SELECT * FROM reservation'
            args = ()
            if hours:
                sql += ' WHERE departure >= ? AND departure < ?'
                args = (hours.start.timestamp(), hours.end.timestamp())
            return [self.serialize(row) for row in db.execute(sql + ' ORDER BY ship_id,departure,id', args)]
