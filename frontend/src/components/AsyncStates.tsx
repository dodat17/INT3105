type MessageStateProps = {
  title: string;
  message: string;
  kind?: 'status' | 'loading' | 'error';
  onRetry?: () => void;
};

function MessageState({ title, message, kind = 'status', onRetry }: MessageStateProps) {
  return (
    <section
      aria-live={kind === 'error' ? 'assertive' : 'polite'}
      className={`message-state ${kind}`}
      role={kind === 'error' ? 'alert' : 'status'}
    >
      <span className="state-kicker">Rạp Màn Ảnh</span>
      <h2>{title}</h2>
      <p>{message}</p>
      {onRetry && <button className="button button-dark" onClick={onRetry} type="button">Thử lại</button>}
    </section>
  );
}

export function LoadingState() {
  return <MessageState kind="loading" title="Đang mở màn" message="Nội dung đang được chuẩn bị." />;
}

export function EmptyState({ title = 'Chưa có dữ liệu', message = 'Hãy quay lại sau.' }: Partial<MessageStateProps>) {
  return <MessageState title={title} message={message} />;
}

export function ErrorState({ message = 'Vui lòng thử lại sau ít phút.', onRetry }: Pick<Partial<MessageStateProps>, 'message' | 'onRetry'>) {
  return <MessageState kind="error" title="Có lỗi xảy ra" message={message} onRetry={onRetry} />;
}
