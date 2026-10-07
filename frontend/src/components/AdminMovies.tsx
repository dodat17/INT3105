import { useState, type FormEvent } from 'react';

import type { AppContext } from '../app/AppShell';

type AdminMoviesProps = Pick<AppContext, 'addMovie' | 'deleteMovie' | 'movies'>;

export function AdminMovies({ addMovie, deleteMovie, movies }: AdminMoviesProps) {
  const [notice, setNotice] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const submitMovie = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setNotice('');
    setSubmitting(true);
    try {
      const movie = await addMovie({
        title: String(form.get('title') ?? '').trim(),
        genre: String(form.get('genre') ?? '').trim(),
        durationMinutes: Number(form.get('durationMinutes')),
        ageRating: String(form.get('ageRating') ?? '').trim(),
        description: String(form.get('description') ?? '').trim(),
      });
      formElement.reset();
      setNotice(`Đã thêm “${movie.title}”.`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Không thể thêm phim.');
    } finally {
      setSubmitting(false);
    }
  };

  const removeMovie = async (movieId: string, title: string) => {
    if (!window.confirm(`Xóa “${title}” khỏi danh mục?`)) return;
    try {
      await deleteMovie(movieId);
      setNotice(`Đã xóa “${title}”.`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Không thể xóa phim.');
    }
  };

  return (
    <div className="admin-grid">
      <form className="admin-form" onSubmit={submitMovie}>
        <h2>Thêm phim</h2>
        <label>Tên phim<input name="title" required /></label>
        <label>Thể loại<input name="genre" placeholder="Ví dụ: Tâm lý" /></label>
        <label>Thời lượng (phút)<input min="1" max="600" name="durationMinutes" type="number" required /></label>
        <label>Phân loại tuổi<input maxLength={10} name="ageRating" placeholder="T13" /></label>
        <label>Mô tả<textarea maxLength={5000} name="description" rows={4} /></label>
        <button className="button button-accent" disabled={submitting} type="submit">{submitting ? 'Đang thêm...' : 'Thêm vào danh mục'}</button>
        {notice && <p className="form-notice" role="status">{notice}</p>}
      </form>
      <div className="admin-list">
        <div className="admin-list-heading"><h2>Danh mục phim</h2><span>{movies.totalItems} phim</span></div>
        {movies.items.map((movie) => (
          <div className="admin-movie-row" key={movie.id}>
            <i />
            <div><strong>{movie.title}</strong><span>{movie.genre || 'Chưa phân loại'} · {movie.durationMinutes} phút</span></div>
            <button className="text-button danger" type="button" onClick={() => void removeMovie(movie.id, movie.title)}>Xóa</button>
          </div>
        ))}
      </div>
    </div>
  );
}
