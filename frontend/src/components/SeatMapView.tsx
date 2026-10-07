import type { CSSProperties } from 'react';

import type { SeatMap } from '../types';

type SeatMapViewProps = {
  seatMap: SeatMap;
};

const currency = new Intl.NumberFormat('vi-VN', {
  style: 'currency',
  currency: 'VND',
  maximumFractionDigits: 0,
});

export function SeatMapView({ seatMap }: SeatMapViewProps) {
  const rows = seatMap.seats.reduce<Map<string, typeof seatMap.seats>>((grouped, seat) => {
    const row = grouped.get(seat.rowLabel) ?? [];
    row.push(seat);
    grouped.set(seat.rowLabel, row);
    return grouped;
  }, new Map());
  const columns = Math.max(...seatMap.seats.map((seat) => seat.number), 1);
  const rowStyle = { '--seat-columns': columns } as CSSProperties;

  return (
    <div className="seat-map-panel">
      <div className="screen"><span>MÀN HÌNH</span></div>
      <div className="seat-map" aria-label={`Sơ đồ ghế ${seatMap.room.name}`}>
        {[...rows].map(([rowLabel, seats]) => (
          <div className="seat-row" key={rowLabel} style={rowStyle}>
            <span>{rowLabel}</span>
            {seats.map((seat) => (
              <span
                className={`seat ${seat.seatType.toLowerCase()} ${seat.status.toLowerCase()}`}
                key={seat.id}
                title={`${seat.label} · ${seat.seatType} · ${currency.format(seat.price)}`}
              >
                {seat.number}
              </span>
            ))}
          </div>
        ))}
      </div>
      <div className="seat-legend" aria-label="Chú thích sơ đồ ghế">
        <span><i className="legend-dot" />Ghế thường</span>
        <span><i className="legend-dot vip" />Ghế VIP</span>
        <span><i className="legend-dot booked" />Đã đặt</span>
      </div>
    </div>
  );
}
