import React, { useEffect, useState } from 'react';
import { centralDay, centralDate, centralTime, request } from '../api';

export default function Fleet({ ships }) {
  const [day, setDay] = useState(centralDay);
  const [history, setHistory] = useState(false);
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(''); setBookings([]);
    if (!history && !day) { setLoading(false); return () => controller.abort(); }
    request(`/bookings${history ? '' : `?day=${day}`}`, { signal: controller.signal })
      .then(value => { if (!controller.signal.aborted) setBookings(value); })
      .catch(reason => { if (!controller.signal.aborted) setError(reason.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [day, history]);
  return <section><div className="panel dashboard-header"><div><span className="eyebrow">FLEET OPERATIONS</span><h2>Fleet manager</h2><p>Reservations organized by ship. All times are Central.</p></div><div className="filters"><label>View date<input type="date" value={day} disabled={history} onChange={event => setDay(event.target.value)}/></label><label className="checkbox"><input type="checkbox" checked={history} onChange={event => setHistory(event.target.checked)}/>All dates</label></div></div>
    {loading && <p role="status">Loading reservations…</p>}{error && <p role="alert" className="error">{error}</p>}
    {!loading && !error && <div className="fleet-grid">{ships.map(ship => {
      const flights = bookings.filter(item => item.shipId === ship.id);
      return <article className="panel ship-card" key={ship.id}><div className="ship-heading"><h3>{ship.name}</h3><span className="badge">{flights.length} bookings</span></div>{flights.length === 0 ? <p className="empty">No reservations in this view.</p> : <div className="table-scroll"><table><thead><tr><th>Pilot</th><th>Date</th><th>Departure</th><th>Return</th></tr></thead><tbody>{flights.map(flight => <tr key={flight.id}><td>{flight.pilotName}</td><td>{centralDate(flight.startTime)}</td><td>{centralTime(flight.startTime)}</td><td>{centralTime(flight.endTime)}</td></tr>)}</tbody></table></div>}</article>;
    })}</div>}
  </section>;
}
