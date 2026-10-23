import type { CSSProperties } from 'react';

import { currency } from '../lib/formatters';
import type { SeatMap } from '../types';

type SeatMapViewProps = {
  seatMap: SeatMap;
  selected?: string[];
  onToggle?: (seatId: string) => void;
};

export function SeatMapView({ seatMap, selected = [], onToggle }: SeatMapViewProps) {
  const rows = seatMap.seats.reduce<Map<string, typeof seatMap.seats>>((grouped, seat) => {
    const row = grouped.get(seat.rowLabel) ?? [];
    row.push(seat); grouped.set(seat.rowLabel, row); return grouped;
  }, new Map());
  const columns = Math.max(...seatMap.seats.map((seat) => seat.number), 1);
  const rowStyle = { '--seat-columns': columns } as CSSProperties;

  return (
    <div className="seat-map-panel">
      <div className="screen"><span>MÀN HÌNH</span></div>
      <div className="seat-map" aria-label={`Sơ đồ ghế ${seatMap.auditorium.name}`}>
        {[...rows].map(([rowLabel, seats]) => (
          <div className="seat-row" key={rowLabel} style={rowStyle}>
            <span>{rowLabel}</span>
            {seats.map((seat) => {
              const isSelected = selected.includes(seat.id);
              const unavailable = seat.status !== 'AVAILABLE';
              const state = isSelected ? 'selected' : seat.status.toLowerCase();
              return (
                <button
                  aria-label={`${seat.label}, ${seat.seatType}, ${currency.format(seat.price)}, ${isSelected ? 'đã chọn' : unavailable ? seat.status === 'HELD' ? 'đang được giữ' : 'đã đặt' : 'còn trống'}`}
                  aria-pressed={isSelected}
                  className={`seat ${seat.seatType.toLowerCase()} ${state}`}
                  disabled={unavailable}
                  key={seat.id}
                  onClick={() => onToggle?.(seat.id)}
                  title={`${seat.label} · ${seat.seatType} · ${currency.format(seat.price)}`}
                  type="button"
                >{seat.number}</button>
              );
            })}
          </div>
        ))}
      </div>
      <div className="seat-legend" aria-label="Chú thích sơ đồ ghế">
        <span><i className="legend-dot" />Ghế thường</span>
        <span><i className="legend-dot vip" />Ghế VIP</span>
        <span><i className="legend-dot held" />Đang giữ</span>
        <span><i className="legend-dot booked" />Đã đặt</span>
        <span><i className="legend-dot selected" />Đã chọn</span>
      </div>
    </div>
  );
}
