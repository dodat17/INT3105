import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { ErrorState, LoadingState } from '../components/AsyncStates';
import { movieApi } from '../lib/apiClient';
import type { Movie } from '../types';

export function MovieDetailPage() {
  const { movieId = '' } = useParams();
  const [movie, setMovie] = useState<Movie | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    movieApi.get(movieId).then(setMovie).catch((requestError: unknown) => {
      setError(requestError instanceof Error ? requestError.message : 'Không thể tải thông tin phim.');
    });
  }, [movieId]);

  if (error) return <ErrorState message={error} />;
  if (!movie) return <LoadingState />;

  return (
    <section className="movie-detail">
      <Link className="back-link" to="/">← Danh sách phim</Link>
      <p className="section-index">CHI TIẾT PHIM</p>
      <h1>{movie.title}</h1>
      <p className="movie-meta">{movie.genre || 'Chưa phân loại'} · {movie.durationMinutes} phút · {movie.ageRating || 'P'}</p>
      <p className="movie-synopsis">{movie.description || 'Phim chưa có mô tả.'}</p>
      <div className="schedule-state">
        <h2>Lịch chiếu</h2>
        <p>Backend chưa cung cấp API suất chiếu. Lịch chiếu sẽ xuất hiện tại đây khi API sẵn sàng.</p>
      </div>
    </section>
  );
}
