import { useState, type FormEvent } from 'react';
import { useOutletContext } from 'react-router-dom';

import type { AppContext } from '../app/AppShell';

export function AdminPage() {
  const { addMovie, deleteMovie, login, movies, user } = useOutletContext<AppContext>();
  const [notice, setNotice] = useState('');

  if (user?.role !== 'ADMIN') {
    return (
      <section className="centered-state">
        <p className="section-index">KHU VỰC QUẢN TRỊ</p>
        <h1>Dành cho người vận hành rạp.</h1>
        <p>Chuyển sang tài khoản admin giả lập để thử các thao tác quản lý.</p>
        <button className="button button-accent" type="button" onClick={() => login('ADMIN')}>
          Vào với quyền Admin
        </button>
      </section>
    );
  }

  const submitMovie = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const title = String(form.get('title') ?? '').trim();
    if (!title) return;
    addMovie({
      id: `${title.toLocaleLowerCase('vi').replaceAll(' ', '-')}-${Date.now()}`,
      title,
      genre: String(form.get('genre') ?? 'Chưa phân loại'),
      duration: Number(form.get('duration')) || 90,
      ageRating: 'T13',
      description: 'Phim mới được thêm từ giao diện quản trị mock.',
      accent: '#295d73',
      posterLabel: 'NEW / SẮP RA MẮT',
    });
    event.currentTarget.reset();
    setNotice(`Đã thêm “${title}” vào danh sách mock.`);
  };

  return (
    <section className="admin-page">
      <div className="page-heading">
        <div><p className="section-index">04 / QUẢN TRỊ</p><h1>Điều hành suất chiếu.</h1></div>
        <span>Admin mock</span>
      </div>
      <div className="admin-grid">
        <form className="admin-form" onSubmit={submitMovie}>
          <h2>Thêm phim</h2>
          <label>Tên phim<input name="title" required /></label>
          <label>Thể loại<input name="genre" placeholder="Ví dụ: Tâm lý" required /></label>
          <label>Thời lượng (phút)<input min="30" name="duration" type="number" defaultValue="100" required /></label>
          <button className="button button-accent" type="submit">Thêm vào danh mục</button>
          {notice && <p className="form-notice" role="status">{notice}</p>}
        </form>
        <div className="admin-list">
          <div className="admin-list-heading"><h2>Danh mục phim</h2><span>{movies.length} phim</span></div>
          {movies.map((movie) => (
            <div className="admin-movie-row" key={movie.id}>
              <i style={{ background: movie.accent }} />
              <div><strong>{movie.title}</strong><span>{movie.genre} · {movie.duration} phút</span></div>
              <button className="text-button danger" type="button" onClick={() => deleteMovie(movie.id)}>Xóa</button>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
