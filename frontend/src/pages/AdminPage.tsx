import { useState } from 'react';
import { useOutletContext } from 'react-router-dom';

import type { AppContext } from '../app/AppShell';
import { AdminMovies } from '../components/AdminMovies';
import { AdminRooms } from '../components/AdminRooms';
import { AdminShowtimes } from '../components/AdminShowtimes';

type AdminSection = 'movies' | 'rooms' | 'showtimes';

export function AdminPage() {
  const context = useOutletContext<AppContext>();
  const [section, setSection] = useState<AdminSection>('movies');

  return (
    <section className="admin-page">
      <div className="page-heading">
        <div><p className="section-index">04 / QUẢN TRỊ</p><h1>Vận hành rạp chiếu.</h1></div>
        <span>Admin</span>
      </div>
      <div className="admin-tabs" role="tablist" aria-label="Khu vực quản trị">
        <button className={section === 'movies' ? 'active' : ''} type="button" onClick={() => setSection('movies')}>Phim</button>
        <button className={section === 'rooms' ? 'active' : ''} type="button" onClick={() => setSection('rooms')}>Phòng chiếu</button>
        <button className={section === 'showtimes' ? 'active' : ''} type="button" onClick={() => setSection('showtimes')}>Suất chiếu</button>
      </div>
      {section === 'movies' && <AdminMovies addMovie={context.addMovie} deleteMovie={context.deleteMovie} movies={context.movies} />}
      {section === 'rooms' && <AdminRooms authenticated={context.authenticated} />}
      {section === 'showtimes' && <AdminShowtimes authenticated={context.authenticated} movies={context.movies} />}
    </section>
  );
}
