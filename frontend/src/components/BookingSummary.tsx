import type { Seat } from '../types';
import { currency } from '../lib/formatters';

type BookingSummaryProps = {
  seats: Seat[];
  submitting: boolean;
  onSubmit: () => void;
};

export function BookingSummary({ seats, submitting, onSubmit }: BookingSummaryProps) {
  const total = seats.reduce((sum, seat) => sum + seat.price, 0);
  return (
    <aside className="booking-summary" aria-live="polite">
      <div><span>Ghế đã chọn</span><strong>{seats.length ? seats.map((seat) => seat.label).join(', ') : 'Chưa chọn'}</strong></div>
      {seats.length > 0 && <ul className="seat-price-list">{seats.map((seat) => (
        <li key={seat.id}><span>{seat.label} · {seat.seatType}</span><strong>{currency.format(seat.price)}</strong></li>
      ))}</ul>}
      <div><span>Tổng dự kiến</span><strong>{currency.format(total)}</strong></div>
      <small>Giá cuối cùng do hệ thống xác nhận.</small>
      <button className="button button-accent" disabled={!seats.length || submitting} onClick={onSubmit} type="button">
        {submitting ? 'Đang giữ ghế...' : 'Giữ ghế 5 phút'}
      </button>
    </aside>
  );
}
