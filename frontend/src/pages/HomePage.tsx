import { useState, type FormEvent } from 'react';
import { Link, useOutletContext } from 'react-router-dom';

import type { AppContext } from '../app/AppShell';
import { EmptyState, ErrorState, LoadingState } from '../components/AsyncStates';

const movieAccent = (movieId: string) => {
  const colors = ['#e2583e', '#167a78', '#bd8b32', '#4d7e45', '#295d73'];
  const sum = [...movieId].reduce((total, character) => total + character.charCodeAt(0), 0);
  return colors[sum % colors.length];
};

export function HomePage() {
  const { loadMovies, movies, moviesError, moviesLoading } = useOutletContext<AppContext>();
  const [query, setQuery] = useState('');
  const [activeQuery, setActiveQuery] = useState('');

  const search = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setActiveQuery(query.trim());
    void loadMovies(query, 1);
  };

  const changePage = (page: number) => {
    void loadMovies(activeQuery, page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <section className="catalog-section" aria-labelledby="catalog-title">
      <div className="catalog-toolbar">
        <h2 id="catalog-title">Phim đang chiếu</h2>
        <form className="search-field" onSubmit={search}>
          <span>Tìm phim</span>
          <div className="search-control">
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Tên phim"
            />
            <button className="button button-dark" type="submit">Tìm</button>
          </div>
        </form>
      </div>

      {moviesLoading ? <LoadingState /> : moviesError ? <ErrorState message={moviesError} /> :
        movies.items.length ? (
          <>
            <div className="movie-grid">
              {movies.items.map((movie, index) => (
                <article className="movie-card" key={movie.id}>
                  <div className="poster poster-placeholder" style={{ background: movieAccent(movie.id) }}>
                    <span>{String((movies.page - 1) * movies.pageSize + index + 1).padStart(2, '0')}</span>
                    <small>{movie.ageRating || 'P'}</small>
                    <strong>{movie.title}</strong>
                  </div>
                  <div className="movie-info">
                    <h3>{movie.title}</h3>
                    <p>{movie.genre || 'Chưa phân loại'} · {movie.durationMinutes} phút</p>
                    <p className="movie-description">{movie.description}</p>
                    <Link className="button button-dark" to={`/movies/${movie.id}`}>Xem chi tiết</Link>
                  </div>
                </article>
              ))}
            </div>
            {movies.totalItems > movies.pageSize && (
              <div className="pagination" aria-label="Phân trang phim">
                <button className="text-button" disabled={movies.page === 1} onClick={() => changePage(movies.page - 1)} type="button">Trang trước</button>
                <span>Trang {movies.page} / {Math.ceil(movies.totalItems / movies.pageSize)}</span>
                <button className="text-button" disabled={movies.page * movies.pageSize >= movies.totalItems} onClick={() => changePage(movies.page + 1)} type="button">Trang sau</button>
              </div>
            )}
          </>
        ) : <EmptyState title="Không tìm thấy phim" message="Thử tìm với một tên phim khác." />}
    </section>
  );
}
