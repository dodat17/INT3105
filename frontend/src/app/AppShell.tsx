import { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';

import { movies as initialMovies } from '../data/mockData';
import type { Booking, MockUser, Movie } from '../types';

export type AppContext = {
  bookings: Booking[];
  movies: Movie[];
  user: MockUser | null;
  addBooking: (booking: Booking) => void;
  cancelBooking: (bookingId: string) => void;
  addMovie: (movie: Movie) => void;
  deleteMovie: (movieId: string) => void;
  login: (role: MockUser['role']) => void;
  logout: () => void;
};

export function AppShell() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [movies, setMovies] = useState<Movie[]>(initialMovies);
  const [user, setUser] = useState<MockUser | null>(null);

  const context: AppContext = {
    bookings,
    movies,
    user,
    addBooking: (booking) => setBookings((current) => [booking, ...current]),
    cancelBooking: (bookingId) =>
      setBookings((current) =>
        current.map((booking) =>
          booking.id === bookingId ? { ...booking, status: 'CANCELLED' } : booking,
        ),
      ),
    addMovie: (movie) => setMovies((current) => [movie, ...current]),
    deleteMovie: (movieId) => setMovies((current) => current.filter(({ id }) => id !== movieId)),
    login: (role) =>
      setUser({
        name: role === 'ADMIN' ? 'Quản trị viên' : 'Minh Anh',
        email: role === 'ADMIN' ? 'admin@mananh.vn' : 'minhanh@example.com',
        role,
      }),
    logout: () => setUser(null),
  };

  return (
    <div className="app-shell">
      <header className="site-header">
        <NavLink className="brand" to="/" aria-label="Trang chủ Rạp Màn Ảnh">
          <span className="brand-mark" aria-hidden="true"><i /><i /></span>
          <span className="brand-name"><strong>MÀN ẢNH</strong><small>CINEMA</small></span>
        </NavLink>
        <nav aria-label="Điều hướng chính" className="main-nav">
          <NavLink to="/">Phim</NavLink>
          <NavLink to="/tickets">Vé của tôi</NavLink>
          <NavLink to="/admin">Quản trị</NavLink>
        </nav>
        <div className="account-actions">
          {user ? (
            <>
              <span>{user.name}</span>
              <button className="text-button" type="button" onClick={context.logout}>Đăng xuất</button>
            </>
          ) : (
            <button className="button button-dark" type="button" onClick={() => context.login('CUSTOMER')}>
              Đăng nhập thử
            </button>
          )}
        </div>
      </header>
      <main>
        <Outlet context={context} />
      </main>
      <footer className="site-footer">
        <span>Rạp Màn Ảnh · Mock frontend</span>
        <span>Dữ liệu đang được mô phỏng cục bộ</span>
      </footer>
    </div>
  );
}
