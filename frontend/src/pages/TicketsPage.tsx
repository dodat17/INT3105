import { useCallback, useEffect, useState } from 'react';
import { Link, useOutletContext } from 'react-router-dom';

import type { AppContext } from '../app/AppShell';
import { EmptyState, ErrorState, LoadingState } from '../components/AsyncStates';
import { bookingApi } from '../lib/apiClient';
import { cinemaDateTime, currency } from '../lib/formatters';
import type { Booking, BookingStatus } from '../types';


export function TicketsPage() {
  const { authenticated } = useOutletContext<AppContext>();
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [status, setStatus] = useState<BookingStatus | ''>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { setBookings((await authenticated((token) => bookingApi.list(token, status || undefined))).items); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Không thể tải booking.'); }
    finally { setLoading(false); }
  }, [authenticated, status]);
  useEffect(() => {
    authenticated((token) => bookingApi.list(token, status || undefined))
      .then((page) => setBookings(page.items))
      .catch((requestError: unknown) => setError(requestError instanceof Error ? requestError.message : 'Không thể tải booking.'))
      .finally(() => setLoading(false));
  }, [authenticated, status]);
  const cancel = async (id: string) => {
    setNotice('');
    try { await authenticated((token) => bookingApi.cancel(token, id)); await load(); setNotice('Đã hủy giữ chỗ và trả ghế.'); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Không thể hủy booking.'); }
  };
  return <section className="tickets-page">
    <p className="section-index">VÉ CỦA TÔI</p><h1>Booking của bạn</h1>
    <label>Lọc trạng thái<select value={status} onChange={(event) => { setLoading(true); setError(''); setStatus(event.target.value as BookingStatus | ''); }}><option value="">Tất cả</option><option value="HELD">Đang giữ</option><option value="CONFIRMED">Đã xác nhận</option><option value="CANCELLED">Đã hủy</option><option value="EXPIRED">Hết hạn</option></select></label>
    {notice && <p className="form-notice success" role="status">{notice}</p>}
    {loading ? <LoadingState /> : error ? <ErrorState message={error} onRetry={() => void load()} /> : bookings.length ? <div className="ticket-list">{bookings.map((booking) => <article className="ticket-card" key={booking.id}>
      <div><strong>{booking.items.map((item) => item.label).join(', ')}</strong><span>{currency.format(booking.totalAmount)} · {booking.status}</span><small>Tạo {cinemaDateTime.format(new Date(booking.createdAt))}</small></div>
      <div><Link className="text-button" to={`/tickets/${booking.id}`}>Chi tiết</Link>{booking.status === 'HELD' && <button className="text-button danger" onClick={() => void cancel(booking.id)} type="button">Hủy giữ chỗ</button>}</div>
    </article>)}</div> : <EmptyState title="Chưa có booking" message="Chọn một suất chiếu và giữ ghế để bắt đầu." />}
  </section>;
}
