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

export function EmptyState({ title = 'Chưa có dữ liệu', message = 'Hãy quay lại sau.' }: Partial<MessageStateProps>) {
  return <MessageState title={title} message={message} />;
}

export function ErrorState({ message = 'Vui lòng thử lại sau ít phút.' }: Pick<Partial<MessageStateProps>, 'message'>) {
  return <MessageState title="Có lỗi xảy ra" message={message} />;
}
