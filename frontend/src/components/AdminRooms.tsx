import { useCallback, useEffect, useState, type CSSProperties, type FormEvent } from 'react';

import type { AppContext } from '../app/AppShell';
import { roomApi } from '../lib/apiClient';
import type { Room } from '../types';
import { EmptyState, ErrorState, LoadingState } from './AsyncStates';

type AdminRoomsProps = Pick<AppContext, 'authenticated'>;

const parseVipRows = (value: string) => value
  .split(',')
  .map((item) => Number(item.trim()))
  .filter((item) => Number.isInteger(item) && item > 0);

export function AdminRooms({ authenticated }: AdminRoomsProps) {
  const [rooms, setRooms] = useState<Room[]>([]);
  const [rows, setRows] = useState(6);
  const [cols, setCols] = useState(10);
  const [vipRows, setVipRows] = useState('5');
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const loadRooms = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setRooms(await authenticated((token) => roomApi.list(token)));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Không thể tải danh sách phòng.');
    } finally {
      setLoading(false);
    }
  }, [authenticated]);

  useEffect(() => {
    authenticated((token) => roomApi.list(token))
      .then(setRooms)
      .catch((requestError: unknown) => setError(requestError instanceof Error ? requestError.message : 'Không thể tải danh sách phòng.'))
      .finally(() => setLoading(false));
  }, [authenticated]);

  const submitRoom = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setNotice('');
    setError('');
    setSubmitting(true);
    try {
      const room = await authenticated((token) => roomApi.create(token, {
        name: String(form.get('name') ?? '').trim(),
        rows,
        cols,
        vipRows: parseVipRows(vipRows),
      }));
      formElement.reset();
      setRows(6);
      setCols(10);
      setVipRows('5');
      await loadRooms();
      setNotice(`Đã tạo ${room.name} với ${room.seatCount} ghế.`);
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Không thể tạo phòng.');
    } finally {
      setSubmitting(false);
    }
  };

  const vipRowSet = new Set(parseVipRows(vipRows));
  const previewStyle = { '--preview-columns': cols } as CSSProperties;

  return (
    <div className="admin-grid">
      <form className="admin-form" onSubmit={submitRoom}>
        <h2>Tạo phòng chiếu</h2>
        <label>Tên phòng<input name="name" placeholder="Phòng 3" required /></label>
        <div className="form-columns">
          <label>Số hàng<input min="1" max="26" type="number" value={rows} onChange={(event) => setRows(Number(event.target.value))} required /></label>
          <label>Số cột<input min="1" max="30" type="number" value={cols} onChange={(event) => setCols(Number(event.target.value))} required /></label>
        </div>
        <label>Hàng VIP<input value={vipRows} onChange={(event) => setVipRows(event.target.value)} placeholder="5, 6" /><small>Nhập số thứ tự hàng, 1 là hàng A.</small></label>
        <div className="room-preview" aria-label="Xem trước sơ đồ phòng">
          <span>MÀN HÌNH</span>
          {Array.from({ length: rows }, (_, rowIndex) => (
            <div className="preview-row" key={rowIndex} style={previewStyle}>
              <b>{String.fromCharCode(65 + rowIndex)}</b>
              {Array.from({ length: cols }, (_, colIndex) => (
                <i className={vipRowSet.has(rowIndex + 1) ? 'vip' : ''} key={colIndex} />
              ))}
            </div>
          ))}
        </div>
        <button className="button button-accent" disabled={submitting} type="submit">{submitting ? 'Đang tạo...' : 'Tạo phòng và ghế'}</button>
        {notice && <p className="form-notice success" role="status">{notice}</p>}
      </form>
      <div className="admin-list">
        <div className="admin-list-heading"><h2>Phòng chiếu</h2><span>{rooms.length} phòng</span></div>
        {loading ? <LoadingState /> : error ? <ErrorState message={error} onRetry={() => void loadRooms()} /> : rooms.length ? rooms.map((room) => (
          <div className="room-card" key={room.id}>
            <span>{room.rows} × {room.cols}</span>
            <div><strong>{room.name}</strong><small>{room.seatCount} ghế được sinh tự động</small></div>
          </div>
        )) : <EmptyState title="Chưa có phòng chiếu" message="Tạo phòng đầu tiên bằng biểu mẫu." />}
      </div>
    </div>
  );
}
