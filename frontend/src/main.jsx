import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import Charter from './components/Charter';
import Fleet from './components/Fleet';
import { request } from './api';
import './styles.css';

export function App() {
  const [screen, setScreen] = useState('charter');
  const [ships, setShips] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    request('/ships', { signal: controller.signal }).then(value => { if (!controller.signal.aborted) setShips(value); })
      .catch(reason => { if (!controller.signal.aborted) setError(reason.message); });
    return () => controller.abort();
  }, []);
  return <div className="shell"><header><div className="brand"><span className="brand-icon">✦</span><div><h1>Spaceport Dispatch</h1><p>Pacific Spaceport · Charter operations</p></div></div><nav aria-label="Application views"><button aria-current={screen === 'charter' ? 'page' : undefined} onClick={() => setScreen('charter')}>Charter a ship</button><button aria-current={screen === 'fleet' ? 'page' : undefined} onClick={() => setScreen('fleet')}>Fleet manager</button></nav></header><main>{error ? <p role="alert" className="error">{error}</p> : !ships ? <p role="status">Loading fleet…</p> : ships.length === 0 ? <p>Fleet is empty. Import the seed data before booking.</p> : screen === 'charter' ? <Charter ships={ships}/> : <Fleet ships={ships}/>}</main><footer>Central Time · 30-minute refueling · Reservations saved locally</footer></div>;
}
if (document.getElementById('root')) createRoot(document.getElementById('root')).render(<App/>);
