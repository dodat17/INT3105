import { useMemo, useState, type CSSProperties } from 'react';
import { Link, useOutletContext } from 'react-router-dom';

import type { AppContext } from '../app/AppShell';
import { dates, showtimes } from '../data/mockData';

const formatDay = (value: string) =>
  new Intl.DateTimeFormat('vi-VN', { weekday: 'short', day: '2-digit', month: '2-digit' }).format(
    new Date(`${value}T00:00:00`),
  );

export function HomePage() {
  const { movies } = useOutletContext<AppContext>();
  const [query, setQuery] = useState('');
  const [activeDate, setActiveDate] = useState(dates[0]);

  const visibleMovies = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase('vi');
    if (!normalizedQuery) return movies;
    return movies.filter((movie) =>
      `${movie.title} ${movie.genre}`.toLocaleLowerCase('vi').includes(normalizedQuery),
    );
  }, [movies, query]);

  return (
    <section className="catalog-section" aria-labelledby="catalog-title">
        <div className="catalog-toolbar">
          <h2 id="catalog-title">Phim đang chiếu</h2>
          <label className="search-field">
            <span>Tìm phim</span>
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Tên phim hoặc thể loại"
            />
          </label>
        </div>

        <div className="date-tabs" aria-label="Chọn ngày chiếu">
          {dates.map((date) => (
            <button
              className={date === activeDate ? 'date-tab active' : 'date-tab'}
              key={date}
              type="button"
              onClick={() => setActiveDate(date)}
            >
              {formatDay(date)}
            </button>
          ))}
        </div>

        {visibleMovies.length ? (
          <div className="movie-grid">
            {visibleMovies.map((movie, index) => (
              <article className="movie-card" key={movie.id}>
                <div className="poster" style={{ '--poster-accent': movie.accent } as CSSProperties}>
                  {movie.poster && <img src={movie.poster} alt={`Poster minh họa ${movie.title}`} />}
                  <span>{movie.posterLabel}</span>
                  <small>{movie.ageRating}</small>
                </div>
                <div className="movie-info">
                  <p className="movie-number">{String(index + 1).padStart(2, '0')}</p>
                  <h3>{movie.title}</h3>
                  <p>{movie.genre} · {movie.duration} phút</p>
                  <p className="movie-description">{movie.description}</p>
                  <div className="showtime-list">
                    {showtimes
                      .filter(({ movieId, date }) => movieId === movie.id && date === activeDate)
                      .map((showtime) => (
                        <Link className="showtime-link" key={showtime.id} to={`/booking/${showtime.id}`}>
                          <strong>{showtime.time}</strong>
                          <span>{showtime.room}</span>
                        </Link>
                      ))}
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-inline">Không tìm thấy phim phù hợp với “{query}”.</div>
        )}
    </section>
  );
}
