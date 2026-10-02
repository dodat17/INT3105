import { NavLink, Outlet } from 'react-router-dom';

export function AppShell() {
  return (
    <div className="app-shell">
      <header className="site-header">
        <NavLink className="brand" to="/" aria-label="Trang chủ Rạp Màn Ảnh">
          <span className="brand-mark">M</span>
          <span>Rạp Màn Ảnh</span>
        </NavLink>
        <nav aria-label="Điều hướng chính">
          <NavLink to="/">Phim đang chiếu</NavLink>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
      <footer className="site-footer">Khung dự án INT3105 · Mốc A</footer>
    </div>
  );
}
