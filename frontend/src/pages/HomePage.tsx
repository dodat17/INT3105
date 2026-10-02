export function HomePage() {
  return (
    <section className="hero">
      <div className="hero-copy">
        <p className="eyebrow">Khung dự án đã sẵn sàng</p>
        <h1>Chọn câu chuyện.<br />Giữ chỗ của bạn.</h1>
        <p className="hero-description">
          Nền tảng đặt vé đang được xây dựng. Danh mục phim và lịch chiếu sẽ xuất hiện ở
          mốc tiếp theo.
        </p>
      </div>
      <div className="screen-card" aria-hidden="true">
        <span>01</span>
        <div className="screen-glow" />
        <strong>COMING SOON</strong>
      </div>
    </section>
  );
}
