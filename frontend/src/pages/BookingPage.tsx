import { useMemo, useState } from 'react';
import { Link, useNavigate, useOutletContext, useParams } from 'react-router-dom';

import type { AppContext } from '../app/AppShell';
import { bookedSeats, showtimes } from '../data/mockData';

const seatRows = ['A', 'B', 'C', 'D', 'E'];
const seatNumbers = Array.from({ length: 10 }, (_, index) => index + 1);
const currency = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' });

export function BookingPage() {
  const { showtimeId } = useParams();
  const navigate = useNavigate();
  const { addBooking, movies, user, login } = useOutletContext<AppContext>();
  const [selectedSeats, setSelectedSeats] = useState<string[]>([]);
  const [notice, setNotice] = useState('');
  const showtime = showtimes.find(({ id }) => id === showtimeId);
  const movie = movies.find(({ id }) => id === showtime?.movieId);

  const total = useMemo(
    () => selectedSeats.length * (showtime?.price ?? 0),
    [selectedSeats.length, showtime?.price],
  );

  if (!showtime || !movie) {
    return <section className="not-found"><h1>Không tìm thấy suất chiếu.</h1><Link to="/">Về trang phim</Link></section>;
  }

  const toggleSeat = (seat: string) => {
    if (bookedSeats.has(seat)) return;
    setNotice('');
    setSelectedSeats((current) => {
      if (current.includes(seat)) return current.filter((item) => item !== seat);
      if (current.length === 8) {
        setNotice('Mỗi lần đặt tối đa 8 ghế.');
        return current;
      }
      return [...current, seat];
    });
  };

  const createBooking = () => {
    if (!user) {
      login('CUSTOMER');
      setNotice('Đã đăng nhập bằng tài khoản thử. Bấm giữ ghế lần nữa để tiếp tục.');
      return;
    }
    if (!selectedSeats.length) {
      setNotice('Vui lòng chọn ít nhất một ghế.');
      return;
    }
    addBooking({
      id: `BK-${Date.now().toString().slice(-6)}`,
      movieId: movie.id,
      showtimeId: showtime.id,
      seats: selectedSeats,
      total,
      status: 'HELD',
      createdAt: new Date().toISOString(),
    });
    navigate('/tickets');
  };

  return (
    <section className="booking-layout">
      <div className="seat-area">
        <Link className="back-link" to="/">← Đổi suất chiếu</Link>
        <p className="section-index">02 / CHỌN GHẾ</p>
        <h1>{movie.title}</h1>
        <p className="showtime-meta">{showtime.time} · {showtime.date} · {showtime.room}</p>
        <div className="screen"><span>MÀN HÌNH</span></div>
        <div className="seat-map" aria-label="Sơ đồ ghế">
          {seatRows.map((row) => (
            <div className="seat-row" key={row}>
              <span>{row}</span>
              {seatNumbers.map((number) => {
                const seat = `${row}${number}`;
                const isBooked = bookedSeats.has(seat);
                const isSelected = selectedSeats.includes(seat);
                return (
                  <button
                    aria-label={`Ghế ${seat}${isBooked ? ', đã đặt' : isSelected ? ', đang chọn' : ', còn trống'}`}
                    className={`seat${isBooked ? ' booked' : ''}${isSelected ? ' selected' : ''}`}
                    disabled={isBooked}
                    key={seat}
                    type="button"
                    onClick={() => toggleSeat(seat)}
                  >
                    {number}
                  </button>
                );
              })}
            </div>
          ))}
        </div>
        <div className="seat-legend">
          <span><i className="legend-dot" />Còn trống</span>
          <span><i className="legend-dot selected" />Đang chọn</span>
          <span><i className="legend-dot booked" />Đã đặt</span>
        </div>
      </div>

      <aside className="booking-summary">
        <p className="section-index">TÓM TẮT</p>
        <h2>Chỗ của bạn</h2>
        <dl>
          <div><dt>Phim</dt><dd>{movie.title}</dd></div>
          <div><dt>Suất</dt><dd>{showtime.time}</dd></div>
          <div><dt>Ghế</dt><dd>{selectedSeats.join(', ') || 'Chưa chọn'}</dd></div>
          <div><dt>Đơn giá</dt><dd>{currency.format(showtime.price)}</dd></div>
        </dl>
        <div className="summary-total"><span>Tạm tính</span><strong>{currency.format(total)}</strong></div>
        {notice && <p className="form-notice" role="status">{notice}</p>}
        <button className="button button-accent full-width" type="button" onClick={createBooking}>
          Giữ ghế 5 phút
        </button>
        <p className="summary-note">Đây là thao tác mô phỏng, chưa phát sinh thanh toán.</p>
      </aside>
    </section>
  );
}
