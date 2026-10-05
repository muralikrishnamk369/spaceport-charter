import React, { useEffect, useState } from 'react';
import { centralDay, request } from '../api';

export default function Charter({ ships }) {
  const [ship, setShip] = useState(String(ships[0]?.id ?? ''));
  const [day, setDay] = useState(centralDay);
  const [duration, setDuration] = useState('60');
  const [pilot, setPilot] = useState('');
  const [selection, setSelection] = useState(null);
  const [availability, setAvailability] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [revision, setRevision] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setSelection(null); setAvailability(null); setLoading(true);
    if (!ship || !day) { setLoading(false); return () => controller.abort(); }
    request(`/availability?shipId=${ship}&day=${day}&duration=${duration}`, { signal: controller.signal })
      .then(value => { if (!controller.signal.aborted) setAvailability(value); })
      .catch(reason => { if (!controller.signal.aborted) setError(reason.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [ship, day, duration, revision]);

  function change(update) { update(); setSelection(null); setNotice(''); setError(''); }
  async function submit(event) {
    event.preventDefault();
    if (!selection || saving) return;
    setSaving(true); setError(''); setNotice('');
    try {
      await request('/bookings', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shipId: Number(ship), pilotName: pilot.trim(), startTime: selection.startTime, endTime: selection.endTime }) });
      setNotice(`Reservation confirmed for ${pilot.trim()} at ${selection.label} Central.`);
      setPilot(''); setSelection(null); setRevision(value => value + 1);
    } catch (reason) {
      setError(reason.message);
      if (reason.status === 409) { setSelection(null); setRevision(value => value + 1); }
    } finally { setSaving(false); }
  }
  return <section className="panel">
    <div className="section-heading"><span className="eyebrow">PLAN YOUR DEPARTURE</span><h2>Charter a ship</h2><p>Choose a vessel and an available departure. Every flight includes a 30-minute refueling gap.</p></div>
    <form onSubmit={submit}>
      <fieldset disabled={saving}>
        <div className="controls">
          <label>Ship<select value={ship} onChange={event => change(() => setShip(event.target.value))}>{ships.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
          <label>Flight date<input type="date" required value={day} onChange={event => change(() => setDay(event.target.value))}/></label>
          <label>Flight duration<select value={duration} onChange={event => change(() => setDuration(event.target.value))}>{[30,60,90,120,180,240].map(value => <option key={value} value={value}>{value} minutes</option>)}</select></label>
        </div>
        <h3>Departure times <small>Central Time · 6 AM–10 PM</small></h3>
        {loading && <p role="status">Checking availability…</p>}
        {!loading && availability && <div className="slots">{availability.slots.map(slot => <button type="button" key={slot.startTime} disabled={!slot.available} aria-pressed={selection?.startTime === slot.startTime} title={slot.available ? 'Available' : 'Booked or refueling'} onClick={() => setSelection(slot)}>{slot.label}</button>)}</div>}
        {!loading && availability && !availability.slots.some(slot => slot.available) && <p>No departures are available for this duration. Try another date or a shorter flight.</p>}
        <div className="booking-footer"><label>Pilot name<input required maxLength={100} value={pilot} onChange={event => setPilot(event.target.value)} placeholder="Enter pilot name"/></label><button className="primary" disabled={!selection || !pilot.trim() || loading || saving}>{saving ? 'Reserving…' : 'Confirm reservation'}</button></div>
      </fieldset>
      {error && <p className="error" role="alert">{error}</p>}
      {notice && <p className="success" role="status">{notice}</p>}
    </form>
  </section>;
}
