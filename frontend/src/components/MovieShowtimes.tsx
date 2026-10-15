import { useEffect, useState } from 'react';
import { Link, useOutletContext } from 'react-router-dom';

import type { AppContext } from '../app/AppShell';
import { bookingApi, ApiError, showtimeApi } from '../lib/apiClient';
import type { Booking, SeatMap, Showtime } from '../types';
import { BookingSummary } from './BookingSummary';
import { EmptyState, ErrorState, LoadingState } from './AsyncStates';
import { SeatMapView } from './SeatMapView';

type MovieShowtimesProps = { movieId: string };
const dateTime = new Intl.DateTimeFormat('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', weekday: 'short', day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
const time = new Intl.DateTimeFormat('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', hour: '2-digit', minute: '2-digit' });
const currency = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 });

export function MovieShowtimes({ movieId }: MovieShowtimesProps) {
  const { authenticated, user } = useOutletContext<AppContext>();
  const [date, setDate] = useState('');
  const [showtimes, setShowtimes] = useState<Showtime[]>([]);
  const [seatMap, setSeatMap] = useState<SeatMap | null>(null);
  const [selectedId, setSelectedId] = useState('');
  const [selectedSeats, setSelectedSeats] = useState<string[]>([]);
  const [booking, setBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [seatLoading, setSeatLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    showtimeApi.list(movieId, date).then((page) => setShowtimes(page.items)).catch((requestError: unknown) => {
      setError(requestError instanceof Error ? requestError.message : 'Không thể tải lịch chiếu.');
    }).finally(() => setLoading(false));
  }, [date, movieId]);

  const changeDate = (value: string) => { setLoading(true); setError(''); setSeatMap(null); setSelectedId(''); setSelectedSeats([]); setDate(value); };
  const viewSeats = async (showtimeId: string) => {
    setSelectedId(showtimeId); setSeatMap(null); setSelectedSeats([]); setBooking(null); setSeatLoading(true); setError('');
    try { setSeatMap(await showtimeApi.seats(showtimeId)); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Không thể tải sơ đồ ghế.'); }
    finally { setSeatLoading(false); }
  };
  const toggleSeat = (seatId: string) => {
    setError('');
    setSelectedSeats((current) => current.includes(seatId) ? current.filter((id) => id !== seatId) : current.length < 8 ? [...current, seatId] : current);
  };
  const createBooking = async () => {
    if (!seatMap || !selectedSeats.length) return;
    setSubmitting(true); setError('');
    try {
      setBooking(await authenticated((token) => bookingApi.create(token, seatMap.showtimeId, selectedSeats)));
      setSelectedSeats([]);
      setSeatMap(await showtimeApi.seats(seatMap.showtimeId));
    } catch (requestError) {
      if (requestError instanceof ApiError && requestError.code === 'SEAT_UNAVAILABLE') {
        setSeatMap(await showtimeApi.seats(seatMap.showtimeId)); setSelectedSeats([]);
      }
      setError(requestError instanceof Error ? requestError.message : 'Không thể giữ ghế.');
    } finally { setSubmitting(false); }
  };
  const selected = seatMap?.seats.filter((seat) => selectedSeats.includes(seat.id)) ?? [];

  return (
    <div className="schedule-state">
      <div className="schedule-heading"><h2>Lịch chiếu</h2><label>Ngày chiếu<input type="date" value={date} onChange={(event) => changeDate(event.target.value)} /></label></div>
      {date && <button className="text-button" type="button" onClick={() => changeDate('')}>Xem tất cả ngày</button>}
      {loading ? <LoadingState /> : error && !selectedId ? <ErrorState message={error} /> : showtimes.length ? (
        <div className="showtime-cards">{showtimes.map((showtime) => (
          <button className={`showtime-card ${selectedId === showtime.id ? 'active' : ''}`} key={showtime.id} type="button" onClick={() => void viewSeats(showtime.id)}>
            <strong>{dateTime.format(new Date(showtime.startsAt))}</strong><span>Đến {time.format(new Date(showtime.endsAt))}</span><small>Từ {currency.format(showtime.basePrice)}</small>
          </button>
        ))}</div>
      ) : <EmptyState title="Chưa có suất chiếu" message="Thử chọn ngày khác." />}
      {selectedId && <div className="seat-map-section">
        <div><p className="section-index">SƠ ĐỒ GHẾ</p><h3>{seatMap?.room.name ?? 'Đang tải phòng chiếu...'}</h3></div>
        {seatLoading ? <LoadingState /> : seatMap && <><SeatMapView seatMap={seatMap} selected={selectedSeats} onToggle={toggleSeat} />
          {user?.role === 'CUSTOMER' ? <BookingSummary seats={selected} submitting={submitting} onSubmit={() => void createBooking()} /> : <p><Link to="/login">Đăng nhập tài khoản khách hàng</Link> để giữ ghế.</p>}
        </>}
        {error && <ErrorState message={error} />}
        {booking && <div className="booking-success" role="status"><strong>Đã giữ {booking.items.map((item) => item.label).join(', ')}</strong><span>Hết hạn lúc {time.format(new Date(booking.expiresAt))}</span><Link to={`/tickets/${booking.id}`}>Xem booking</Link></div>}
      </div>}
    </div>
  );
}
