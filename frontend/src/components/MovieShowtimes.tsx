import { useEffect, useState } from 'react';

import { showtimeApi } from '../lib/apiClient';
import type { SeatMap, Showtime } from '../types';
import { EmptyState, ErrorState, LoadingState } from './AsyncStates';
import { SeatMapView } from './SeatMapView';

type MovieShowtimesProps = {
  movieId: string;
};

const dateTime = new Intl.DateTimeFormat('vi-VN', {
  timeZone: 'Asia/Ho_Chi_Minh',
  weekday: 'short',
  day: '2-digit',
  month: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
});

const time = new Intl.DateTimeFormat('vi-VN', {
  timeZone: 'Asia/Ho_Chi_Minh',
  hour: '2-digit',
  minute: '2-digit',
});

const currency = new Intl.NumberFormat('vi-VN', {
  style: 'currency',
  currency: 'VND',
  maximumFractionDigits: 0,
});

export function MovieShowtimes({ movieId }: MovieShowtimesProps) {
  const [date, setDate] = useState('');
  const [showtimes, setShowtimes] = useState<Showtime[]>([]);
  const [seatMap, setSeatMap] = useState<SeatMap | null>(null);
  const [selectedId, setSelectedId] = useState('');
  const [loading, setLoading] = useState(true);
  const [seatLoading, setSeatLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    showtimeApi.list(movieId, date)
      .then((page) => setShowtimes(page.items))
      .catch((requestError: unknown) => {
        setError(requestError instanceof Error ? requestError.message : 'Không thể tải lịch chiếu.');
      })
      .finally(() => setLoading(false));
  }, [date, movieId]);

  const changeDate = (value: string) => {
    setLoading(true);
    setError('');
    setSeatMap(null);
    setSelectedId('');
    setDate(value);
  };

  const viewSeats = async (showtimeId: string) => {
    setSelectedId(showtimeId);
    setSeatMap(null);
    setSeatLoading(true);
    setError('');
    try {
      setSeatMap(await showtimeApi.seats(showtimeId));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Không thể tải sơ đồ ghế.');
    } finally {
      setSeatLoading(false);
    }
  };

  return (
    <div className="schedule-state">
      <div className="schedule-heading">
        <h2>Lịch chiếu</h2>
        <label>
          Ngày chiếu
          <input type="date" value={date} onChange={(event) => changeDate(event.target.value)} />
        </label>
      </div>
      {date && <button className="text-button" type="button" onClick={() => changeDate('')}>Xem tất cả ngày</button>}
      {loading ? <LoadingState /> : error && !selectedId ? <ErrorState message={error} /> :
        showtimes.length ? (
          <div className="showtime-cards">
            {showtimes.map((showtime) => (
              <button
                className={`showtime-card ${selectedId === showtime.id ? 'active' : ''}`}
                key={showtime.id}
                type="button"
                onClick={() => void viewSeats(showtime.id)}
              >
                <strong>{dateTime.format(new Date(showtime.startsAt))}</strong>
                <span>Đến {time.format(new Date(showtime.endsAt))}</span>
                <small>Từ {currency.format(showtime.basePrice)}</small>
              </button>
            ))}
          </div>
        ) : <EmptyState title="Chưa có suất chiếu" message="Thử chọn ngày khác." />}
      {selectedId && (
        <div className="seat-map-section">
          <div>
            <p className="section-index">SƠ ĐỒ GHẾ</p>
            <h3>{seatMap?.room.name ?? 'Đang tải phòng chiếu...'}</h3>
          </div>
          {seatLoading ? <LoadingState /> : error ? <ErrorState message={error} /> : seatMap && <SeatMapView seatMap={seatMap} />}
        </div>
      )}
    </div>
  );
}
