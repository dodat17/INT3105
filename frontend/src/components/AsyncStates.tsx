type MessageStateProps = {
  title: string;
  message: string;
};

function MessageState({ title, message }: MessageStateProps) {
  return (
    <section className="message-state" role="status">
      <span className="state-kicker">Rạp Màn Ảnh</span>
      <h2>{title}</h2>
      <p>{message}</p>
    </section>
  );
}

export function LoadingState() {
  return <MessageState title="Đang mở màn" message="Nội dung đang được chuẩn bị." />;
}

export function EmptyState() {
  return <MessageState title="Chưa có suất chiếu" message="Hãy quay lại sau để xem lịch mới." />;
}

export function ErrorState() {
  return <MessageState title="Có lỗi xảy ra" message="Vui lòng thử lại sau ít phút." />;
}
