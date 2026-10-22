import { useState, type KeyboardEvent } from 'react';
import { useOutletContext } from 'react-router-dom';

import type { AppContext } from '../app/AppShell';
import { AdminMovies } from '../components/AdminMovies';
import { AdminRooms } from '../components/AdminRooms';
import { AdminShowtimes } from '../components/AdminShowtimes';

type AdminSection = 'movies' | 'rooms' | 'showtimes';

export function AdminPage() {
  const context = useOutletContext<AppContext>();
  const [section, setSection] = useState<AdminSection>('movies');

  const navigateTabs = (event: KeyboardEvent<HTMLDivElement>) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    const tabs = Array.from(event.currentTarget.querySelectorAll<HTMLButtonElement>('[role="tab"]'));
    const current = tabs.indexOf(document.activeElement as HTMLButtonElement);
    const next = event.key === 'Home'
      ? 0
      : event.key === 'End'
        ? tabs.length - 1
        : (current + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
    event.preventDefault();
    tabs[next]?.focus();
    tabs[next]?.click();
  };

  return (
    <section className="admin-page">
      <div className="page-heading">
        <div><p className="section-index">04 / QUẢN TRỊ</p><h1>Vận hành rạp chiếu.</h1></div>
        <span>Admin</span>
      </div>
      <div className="admin-tabs" role="tablist" aria-label="Khu vực quản trị" onKeyDown={navigateTabs}>
        <button aria-controls="admin-panel" aria-selected={section === 'movies'} className={section === 'movies' ? 'active' : ''} role="tab" tabIndex={section === 'movies' ? 0 : -1} type="button" onClick={() => setSection('movies')}>Phim</button>
        <button aria-controls="admin-panel" aria-selected={section === 'rooms'} className={section === 'rooms' ? 'active' : ''} role="tab" tabIndex={section === 'rooms' ? 0 : -1} type="button" onClick={() => setSection('rooms')}>Phòng chiếu</button>
        <button aria-controls="admin-panel" aria-selected={section === 'showtimes'} className={section === 'showtimes' ? 'active' : ''} role="tab" tabIndex={section === 'showtimes' ? 0 : -1} type="button" onClick={() => setSection('showtimes')}>Suất chiếu</button>
      </div>
      <div id="admin-panel" role="tabpanel">
        {section === 'movies' && <AdminMovies addMovie={context.addMovie} deleteMovie={context.deleteMovie} movies={context.movies} />}
        {section === 'rooms' && <AdminRooms authenticated={context.authenticated} />}
        {section === 'showtimes' && <AdminShowtimes authenticated={context.authenticated} movies={context.movies} />}
      </div>
    </section>
  );
}
