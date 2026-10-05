import React from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from './main';

const slot = { startTime:'2026-07-14T10:00:00-05:00', endTime:'2026-07-14T11:00:00-05:00', label:'10:00 AM', available:true };
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
function mockServer(conflict = false) {
  let reserved = false;
  const fetch = vi.fn(async (url, options = {}) => {
    if (url === '/api/ships') return { ok:true, json:async () => [{ id:1, name:'Serenity' }] };
    if (url.startsWith('/api/availability')) return { ok:true, json:async () => ({ slots:[{...slot, available:!reserved}] }) };
    if (options.method === 'POST') {
      reserved = true;
      return { ok:!conflict, status:conflict ? 409 : 201, json:async () => conflict ? { detail:'Departure was taken.' } : { id:1 } };
    }
    return { ok:true, json:async () => [{ id:1, shipId:1, pilotName:'Demo Pilot', startTime:slot.startTime, endTime:slot.endTime }] };
  });
  vi.stubGlobal('fetch', fetch);
  return fetch;
}
describe('dispatcher flow', () => {
  it('books using server availability and shows the reservation in fleet manager', async () => {
    const fetch = mockServer(); const user = userEvent.setup(); render(<App/>);
    await user.click(await screen.findByRole('button', { name:'10:00 AM' }));
    await user.type(screen.getByLabelText('Pilot name'), 'Demo Pilot');
    await user.click(screen.getByRole('button', { name:'Confirm reservation' }));
    await screen.findByText(/Reservation confirmed/);
    expect(fetch.mock.calls.some(([url]) => url.startsWith('/api/bookings?'))).toBe(false);
    const [, options] = fetch.mock.calls.find(([,options]) => options?.method === 'POST');
    expect(JSON.parse(options.body)).toEqual({ shipId:1, pilotName:'Demo Pilot', startTime:slot.startTime, endTime:slot.endTime });
    await user.click(screen.getByRole('button', { name:'Fleet manager' }));
    await screen.findByText('Demo Pilot');
    await user.click(screen.getByLabelText('All dates'));
    await waitFor(() => expect(fetch.mock.calls.some(([url]) => url === '/api/bookings')).toBe(true));
  });
  it('refreshes after a conflict and preserves the explanatory error', async () => {
    const fetch = mockServer(true); const user = userEvent.setup(); render(<App/>);
    await user.click(await screen.findByRole('button', { name:'10:00 AM' }));
    await user.type(screen.getByLabelText('Pilot name'), 'Demo Pilot');
    await user.click(screen.getByRole('button', { name:'Confirm reservation' }));
    await screen.findByRole('alert');
    await waitFor(() => expect(fetch.mock.calls.filter(([url]) => url.startsWith('/api/availability')).length).toBe(2));
    expect(screen.getByRole('alert').textContent).toBe('Departure was taken.');
    expect(screen.getByRole('button', { name:'10:00 AM' }).disabled).toBe(true);
  });
});
