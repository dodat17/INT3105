import type { Movie, Showtime } from '../types';
import demKhongTenPoster from '../assets/posters/dem-khong-ten.jpg';
import duongChanTroiPoster from '../assets/posters/duong-chan-troi.jpg';
import motNgayXaPoster from '../assets/posters/mot-ngay-xa.jpg';
import muaHeCuaBePoster from '../assets/posters/mua-he-cua-be.jpg';

export const movies: Movie[] = [
  {
    id: 'mot-ngay-xa',
    title: 'Một Ngày Rất Xa',
    genre: 'Tâm lý · Chính kịch',
    duration: 124,
    ageRating: 'T13',
    description: 'Hai người xa lạ gặp nhau trên chuyến tàu cuối và cùng tìm lại một điều đã mất.',
    accent: '#e2583e',
    posterLabel: '01 / PHÍA SAU HOÀNG HÔN',
    poster: motNgayXaPoster,
  },
  {
    id: 'duong-chan-troi',
    title: 'Đường Chân Trời',
    genre: 'Phiêu lưu · Khoa học viễn tưởng',
    duration: 138,
    ageRating: 'T16',
    description: 'Một phi hành đoàn đi qua vùng tối để tìm nơi ở mới cho những người cuối cùng.',
    accent: '#167a78',
    posterLabel: '02 / TÍN HIỆU CUỐI CÙNG',
    poster: duongChanTroiPoster,
  },
  {
    id: 'dem-khong-ten',
    title: 'Đêm Không Tên',
    genre: 'Bí ẩn · Giật gân',
    duration: 106,
    ageRating: 'T18',
    description: 'Một căn phòng khóa kín, sáu vị khách và lời nhắn không ai muốn nhận.',
    accent: '#bd8b32',
    posterLabel: '03 / KHÔNG AI VÔ TỘI',
    poster: demKhongTenPoster,
  },
  {
    id: 'mua-he-cua-be',
    title: 'Mùa Hè Của Bé',
    genre: 'Gia đình · Hoạt hình',
    duration: 92,
    ageRating: 'P',
    description: 'Chuyến phiêu lưu tí hon qua khu vườn rộng lớn trong một mùa hè khó quên.',
    accent: '#4d7e45',
    posterLabel: '04 / THẾ GIỚI TRONG VƯỜN',
    poster: muaHeCuaBePoster,
  },
];

const today = new Date();
const formatDate = (offset: number) => {
  const date = new Date(today);
  date.setDate(today.getDate() + offset);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const dates = [0, 1, 2, 3].map(formatDate);

export const showtimes: Showtime[] = movies.flatMap((movie, movieIndex) =>
  dates.flatMap((date, dateIndex) => [
    {
      id: `${movie.id}-${dateIndex}-1`,
      movieId: movie.id,
      date,
      time: ['09:30', '10:15', '11:00', '09:45'][movieIndex],
      room: `Phòng ${movieIndex + 1}`,
      price: 75000 + movieIndex * 5000,
    },
    {
      id: `${movie.id}-${dateIndex}-2`,
      movieId: movie.id,
      date,
      time: ['18:45', '19:30', '20:15', '17:50'][movieIndex],
      room: `Phòng ${movieIndex + 1}`,
      price: 90000 + movieIndex * 5000,
    },
  ]),
);

export const bookedSeats = new Set(['A3', 'A4', 'B7', 'C2', 'C3', 'D8', 'E5']);

