"""Atomic, one-time import of the original assessment seed data."""
import argparse
import json
import os
from pathlib import Path
from .api import ReservationRequest
from .scheduling import Period, validate_flight
from .storage import Repository


def import_seed(source, database):
    payload = json.loads(Path(source).read_text(encoding='utf-8'))
    repo = Repository(str(database))
    repo.initialize()
    with repo.connection(writing=True) as db:
        if db.execute('SELECT 1 FROM ship').fetchone() or db.execute('SELECT 1 FROM reservation').fetchone():
            raise ValueError('Database is not empty; refusing to overwrite existing data.')
        db.executemany('INSERT INTO ship(id,name) VALUES(:id,:name)', payload['ships'])
        for item in payload['bookings']:
            booking = ReservationRequest(**item)
            validate_flight(Period(booking.startTime, booking.endTime))
            repo.reserve(db, booking.shipId, booking.pilotName,
                         booking.startTime.timestamp(), booking.endTime.timestamp())
    return len(payload['ships']), len(payload['bookings'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('--database', default=os.environ.get('SPACEPORT_DB',
        str(Path(__file__).resolve().parents[1] / 'data' / 'charters.sqlite3')))
    args = parser.parse_args()
    ships, bookings = import_seed(args.source, args.database)
    print(f'Loaded {ships} ships and {bookings} bookings.')
