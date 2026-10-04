import { Link, useOutletContext } from 'react-router-dom';

import type { AppContext } from '../app/AppShell';
import { showtimes } from '../data/mockData';

const currency = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' });

export function TicketsPage() {
  const { bookings, cancelBooking, movies, user, login } = useOutletContext<AppContext>();

  if (!user) {
    return (
      <section className="centered-state">
        <p className="section-index">VÉ CỦA TÔI</p>
        <h1>Đăng nhập để xem vé.</h1>
        <button className="button button-dark" type="button" onClick={() => login('CUSTOMER')}>
          Đăng nhập tài khoản thử
        </button>
      </section>
    );
  }

  return (
    <section className="tickets-page">
      <div className="page-heading">
        <div><p className="section-index">03 / VÉ CỦA TÔI</p><h1>Lịch hẹn với màn ảnh.</h1></div>
        <span>{bookings.length} đặt chỗ</span>
      </div>
      {bookings.length ? (
        <div className="ticket-list">
          {bookings.map((booking) => {
            const movie = movies.find(({ id }) => id === booking.movieId);
            const showtime = showtimes.find(({ id }) => id === booking.showtimeId);
            return (
              <article className={`ticket-card ${booking.status.toLowerCase()}`} key={booking.id}>
                <div className="ticket-code"><span>MÃ ĐẶT CHỖ</span><strong>{booking.id}</strong></div>
                <div className="ticket-main">
                  <span className="status-badge">{booking.status === 'HELD' ? 'Đang giữ' : 'Đã hủy'}</span>
                  <h2>{movie?.title}</h2>
                  <p>{showtime?.date} · {showtime?.time} · {showtime?.room}</p>
                  <div className="ticket-details"><span>Ghế <strong>{booking.seats.join(', ')}</strong></span><span>{currency.format(booking.total)}</span></div>
                </div>
                {booking.status === 'HELD' && (
                  <button className="text-button danger" type="button" onClick={() => cancelBooking(booking.id)}>
                    Hủy giữ chỗ
                  </button>
                )}
              </article>
            );
          })}
        </div>
      ) : (
        <div className="centered-state compact"><h2>Bạn chưa có vé nào.</h2><Link className="button button-dark" to="/">Chọn phim</Link></div>
      )}
    </section>
  );
}

