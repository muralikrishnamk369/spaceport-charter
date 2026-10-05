"""Framework-independent rules. Intervals are half-open: [start, end)."""
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

SPACEPORT_ZONE = ZoneInfo('America/Chicago')
TURNAROUND = timedelta(minutes=30)


@dataclass(frozen=True)
class Period:
    start: datetime
    end: datetime


def operating_day(day: date) -> Period:
    return Period(datetime.combine(day, time(6), SPACEPORT_ZONE),
                  datetime.combine(day, time(22), SPACEPORT_ZONE))


def validate_flight(flight: Period) -> None:
    if any(value.tzinfo is None or value.utcoffset() is None
           for value in (flight.start, flight.end)):
        raise ValueError('Include a time-zone offset in both timestamps.')
    hours = operating_day(flight.start.astimezone(SPACEPORT_ZONE).date())
    if not hours.start.timestamp() <= flight.start.timestamp() < flight.end.timestamp() <= hours.end.timestamp():
        raise ValueError('Flights must fit within 6 AM–10 PM Central on one day.')


def blocked_periods(hours: Period, flights: list[Period]) -> list[Period]:
    """Expand flights for turnaround, clip to opening hours, then union them."""
    result: list[Period] = []
    for flight in sorted(flights, key=lambda item: item.start):
        left = max(hours.start, flight.start.astimezone(SPACEPORT_ZONE) - TURNAROUND)
        right = min(hours.end, flight.end.astimezone(SPACEPORT_ZONE) + TURNAROUND)
        if left >= right:
            continue
        if result and left <= result[-1].end:
            result[-1] = Period(result[-1].start, max(result[-1].end, right))
        else:
            result.append(Period(left, right))
    return result


def departure_options(hours: Period, blocked: list[Period], minutes: int) -> list[dict]:
    options = []
    departure = hours.start
    while departure + timedelta(minutes=minutes) <= hours.end:
        arrival = departure + timedelta(minutes=minutes)
        options.append({
            'startTime': departure.isoformat(), 'endTime': arrival.isoformat(),
            'label': departure.strftime('%I:%M %p').lstrip('0'),
            'available': all(arrival <= span.start or departure >= span.end for span in blocked),
        })
        departure += timedelta(minutes=30)
    return options
