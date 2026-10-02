import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <section className="not-found">
      <p className="eyebrow">404 · Lạc suất chiếu</p>
      <h1>Trang này không có trong lịch.</h1>
      <Link className="button-link" to="/">Trở về trang chủ</Link>
    </section>
  );
}
