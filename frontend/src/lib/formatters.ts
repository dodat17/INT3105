export const CINEMA_TIME_ZONE = 'Asia/Ho_Chi_Minh';

export const currency = new Intl.NumberFormat('vi-VN', {
  style: 'currency',
  currency: 'VND',
  maximumFractionDigits: 0,
});

export const cinemaDateTime = new Intl.DateTimeFormat('vi-VN', {
  timeZone: CINEMA_TIME_ZONE,
  dateStyle: 'short',
  timeStyle: 'short',
});

export const cinemaTime = new Intl.DateTimeFormat('vi-VN', {
  timeZone: CINEMA_TIME_ZONE,
  hour: '2-digit',
  minute: '2-digit',
});
