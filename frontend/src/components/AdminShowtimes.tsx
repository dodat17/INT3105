import { useCallback, useEffect, useState, type FormEvent } from 'react';

import type { AppContext } from '../app/AppShell';
import { ApiError, roomApi, showtimeApi } from '../lib/apiClient';
import type { MoviePage, Room, Showtime } from '../types';

type AdminShowtimesProps = Pick<AppContext, 'authenticated'> & {
  movies: MoviePage;
};

const dateTime = new Intl.DateTimeFormat('vi-VN', {
  timeZone: 'Asia/Ho_Chi_Minh',
  dateStyle: 'short',
  timeStyle: 'short',
});

const currency = new Intl.NumberFormat('vi-VN', {
  style: 'currency',
  currency: 'VND',
  maximumFractionDigits: 0,
});

const cinemaDateTime = (value: string) => new Date(`${value}:00+07:00`);

export function AdminShowtimes({ authenticated, movies }: AdminShowtimesProps) {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [showtimes, setShowtimes] = useState<Showtime[]>([]);
  const [movieId, setMovieId] = useState('');
  const [roomId, setRoomId] = useState('');
  const [startsAt, setStartsAt] = useState('');
  const [notice, setNotice] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadData = useCallback(async () => {
    const [roomList, showtimePage] = await Promise.all([
      authenticated((token) => roomApi.list(token)),
      showtimeApi.list(),
    ]);
    setRooms(roomList);
    setShowtimes(showtimePage.items);
  }, [authenticated]);

  useEffect(() => {
    Promise.all([
      authenticated((token) => roomApi.list(token)),
      showtimeApi.list(),
    ]).then(([roomList, showtimePage]) => {
      setRooms(roomList);
      setShowtimes(showtimePage.items);
    }).catch((error: unknown) => {
      setNotice(error instanceof Error ? error.message : 'Không thể tải dữ liệu suất chiếu.');
    });
  }, [authenticated]);

  const submitShowtime = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setNotice('');
    setSubmitting(true);
    try {
      await authenticated((token) => showtimeApi.create(token, {
        movieId: activeMovieId,
        roomId: activeRoomId,
        startsAt: cinemaDateTime(startsAt).toISOString(),
        basePrice: Number(form.get('basePrice')),
      }));
      setStartsAt('');
      await loadData();
      setNotice('Đã tạo suất chiếu.');
    } catch (error) {
      if (error instanceof ApiError && error.code === 'SHOWTIME_OVERLAP') {
        setNotice('Phòng đã có suất chiếu trùng khoảng thời gian này.');
      } else {
        setNotice(error instanceof Error ? error.message : 'Không thể tạo suất chiếu.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const removeShowtime = async (showtime: Showtime) => {
    if (!window.confirm(`Xóa suất chiếu lúc ${dateTime.format(new Date(showtime.startsAt))}?`)) return;
    try {
      await authenticated((token) => showtimeApi.delete(token, showtime.id));
      await loadData();
      setNotice('Đã xóa suất chiếu.');
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Không thể xóa suất chiếu.');
    }
  };

  const activeMovieId = movieId || movies.items[0]?.id || '';
  const activeRoomId = roomId || rooms[0]?.id || '';
  const selectedMovie = movies.items.find((movie) => movie.id === activeMovieId);
  const expectedEnd = startsAt && selectedMovie
    ? new Date(cinemaDateTime(startsAt).getTime() + selectedMovie.durationMinutes * 60_000)
    : null;
  const movieNames = new Map(movies.items.map((movie) => [movie.id, movie.title]));
  const roomNames = new Map(rooms.map((room) => [room.id, room.name]));

  return (
    <div className="admin-grid">
      <form className="admin-form" onSubmit={submitShowtime}>
        <h2>Tạo suất chiếu</h2>
        <label>Phim<select value={activeMovieId} onChange={(event) => setMovieId(event.target.value)} required>
          {movies.items.map((movie) => <option key={movie.id} value={movie.id}>{movie.title}</option>)}
        </select></label>
        <label>Phòng<select value={activeRoomId} onChange={(event) => setRoomId(event.target.value)} required>
          {rooms.map((room) => <option key={room.id} value={room.id}>{room.name} · {room.seatCount} ghế</option>)}
        </select></label>
        <label>Bắt đầu<input type="datetime-local" value={startsAt} onChange={(event) => setStartsAt(event.target.value)} required /></label>
        <label>Giá ghế thường<input defaultValue="90000" min="1000" max="10000000" name="basePrice" step="1000" type="number" required /></label>
        <div className="expected-end"><span>Kết thúc dự kiến</span><strong>{expectedEnd ? dateTime.format(expectedEnd) : '—'}</strong></div>
        <button className="button button-accent" disabled={submitting || !activeMovieId || !activeRoomId} type="submit">{submitting ? 'Đang tạo...' : 'Tạo suất chiếu'}</button>
        {notice && <p className="form-notice" role="status">{notice}</p>}
      </form>
      <div className="admin-list">
        <div className="admin-list-heading"><h2>Lịch chiếu</h2><span>{showtimes.length} suất</span></div>
        <div className="showtime-admin-list">
          {showtimes.map((showtime) => (
            <article className="showtime-admin-row" key={showtime.id}>
              <time dateTime={showtime.startsAt}><strong>{dateTime.format(new Date(showtime.startsAt))}</strong><span>đến {dateTime.format(new Date(showtime.endsAt))}</span></time>
              <div><strong>{movieNames.get(showtime.movieId) ?? 'Phim không còn trong danh mục'}</strong><span>{roomNames.get(showtime.roomId) ?? 'Phòng không xác định'} · {currency.format(showtime.basePrice)}</span></div>
              <button className="text-button danger" type="button" onClick={() => void removeShowtime(showtime)}>Xóa</button>
            </article>
          ))}
        </div>
      </div>
    </div>
  );
}
