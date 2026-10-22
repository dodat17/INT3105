import type { Seat } from '../types';

type BookingSummaryProps = {
  seats: Seat[];
  submitting: boolean;
  onSubmit: () => void;
};

const currency = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 });

export function BookingSummary({ seats, submitting, onSubmit }: BookingSummaryProps) {
  const total = seats.reduce((sum, seat) => sum + seat.price, 0);
  return (
    <aside className="booking-summary" aria-live="polite">
      <div><span>Ghế đã chọn</span><strong>{seats.length ? seats.map((seat) => seat.label).join(', ') : 'Chưa chọn'}</strong></div>
      <div><span>Tổng dự kiến</span><strong>{currency.format(total)}</strong></div>
      <small>Giá cuối cùng do hệ thống xác nhận.</small>
      <button className="button button-accent" disabled={!seats.length || submitting} onClick={onSubmit} type="button">
        {submitting ? 'Đang giữ ghế...' : 'Giữ ghế 5 phút'}
      </button>
    </aside>
  );
}
