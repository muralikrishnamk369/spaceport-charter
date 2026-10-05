import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import AwareDatetime, BaseModel, Field, field_validator

from .scheduling import Period, blocked_periods, departure_options, operating_day, validate_flight
from .storage import Repository, SlotTaken, UnknownShip


class ReservationRequest(BaseModel):
    shipId: int = Field(gt=0)
    pilotName: str = Field(min_length=1, max_length=100)
    startTime: AwareDatetime
    endTime: AwareDatetime

    @field_validator('pilotName')
    @classmethod
    def normalize_pilot(cls, name):
        name = name.strip()
        if not name:
            raise ValueError('Enter a pilot name.')
        return name


def make_app(database_path=None):
    root = Path(__file__).resolve().parents[1]
    repository = Repository(str(database_path or os.environ.get('SPACEPORT_DB', root / 'data' / 'charters.sqlite3')))

    @asynccontextmanager
    async def lifespan(app):
        repository.initialize()
        yield

    app = FastAPI(title='Spaceport Charter API', lifespan=lifespan)

    @app.get('/api/ships')
    def get_ships():
        return repository.ships()

    @app.get('/api/availability')
    def get_availability(shipId: int = Query(gt=0), day: date = Query(),
                         duration: int = Query(60, ge=30, le=960, multiple_of=30)):
        hours = operating_day(day)
        try:
            flights = [Period(*times) for times in repository.flight_times(
                shipId, hours.start.timestamp(), hours.end.timestamp())]
        except UnknownShip:
            raise HTTPException(404, 'Ship not found.')
        blocked = blocked_periods(hours, flights)
        return {'shipId': shipId, 'day': day.isoformat(), 'timezone': 'America/Chicago',
                'unavailable': [{'startTime': span.start.isoformat(), 'endTime': span.end.isoformat()}
                                for span in blocked],
                'slots': departure_options(hours, blocked, duration)}

    @app.post('/api/bookings', status_code=201)
    def book(request: ReservationRequest):
        try:
            validate_flight(Period(request.startTime, request.endTime))
            return repository.create(request.shipId, request.pilotName,
                                     request.startTime.timestamp(), request.endTime.timestamp())
        except ValueError as error:
            raise HTTPException(422, str(error))
        except UnknownShip:
            raise HTTPException(404, 'Ship not found.')
        except SlotTaken:
            raise HTTPException(409, 'That flight conflicts with a reservation or refueling. Choose another departure.')
        except sqlite3.OperationalError as error:
            if 'locked' in str(error).lower():
                raise HTTPException(503, 'Booking service is busy. Please retry.', headers={'Retry-After': '1'})
            raise

    @app.get('/api/bookings')
    def get_bookings(day: date | None = None):
        return repository.bookings(operating_day(day) if day else None)

    build = root / 'frontend' / 'dist'
    if build.is_dir():
        app.mount('/', StaticFiles(directory=build, html=True), name='frontend')
    return app


app = make_app()
