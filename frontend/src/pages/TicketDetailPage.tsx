import { useEffect, useState } from 'react';
import { Link, useOutletContext, useParams } from 'react-router-dom';

import type { AppContext } from '../app/AppShell';
import { ErrorState, LoadingState } from '../components/AsyncStates';
import { bookingApi } from '../lib/apiClient';
import type { Booking } from '../types';

const currency = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 });

export function TicketDetailPage() {
  const { bookingId = '' } = useParams();
  const { authenticated } = useOutletContext<AppContext>();
  const [booking, setBooking] = useState<Booking | null>(null);
  const [error, setError] = useState('');
  const load = () => authenticated((token) => bookingApi.get(token, bookingId)).then(setBooking).catch((requestError: unknown) => setError(requestError instanceof Error ? requestError.message : 'Không thể tải booking.'));
  useEffect(() => {
    authenticated((token) => bookingApi.get(token, bookingId))
      .then(setBooking)
      .catch((requestError: unknown) => setError(requestError instanceof Error ? requestError.message : 'Không thể tải booking.'));
  }, [authenticated, bookingId]);
  const confirm = async () => { try { setBooking(await authenticated((token) => bookingApi.confirm(token, bookingId))); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Không thể xác nhận booking.'); } };
  const cancel = async () => { try { await authenticated((token) => bookingApi.cancel(token, bookingId)); await load(); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : 'Không thể hủy booking.'); } };
  if (error) return <ErrorState message={error} />;
  if (!booking) return <LoadingState />;
  return <section className="ticket-detail"><Link className="back-link" to="/tickets">← Vé của tôi</Link><p className="section-index">BOOKING</p><h1>{booking.bookingCode ?? booking.status}</h1><p>Ghế: {booking.items.map((item) => item.label).join(', ')}</p><p>Tổng tiền: {currency.format(booking.totalAmount)}</p>{booking.status === 'HELD' && <div><button className="button button-accent" onClick={() => void confirm()} type="button">Xác nhận đặt vé</button><button className="text-button danger" onClick={() => void cancel()} type="button">Hủy giữ chỗ</button></div>}</section>;
}
