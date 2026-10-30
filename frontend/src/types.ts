export type Movie = {
  id: string;
  title: string;
  genre: string;
  durationMinutes: number;
  ageRating: string;
  description: string;
};

export type MoviePage = {
  items: Movie[];
  page: number;
  pageSize: number;
  totalItems: number;
};

export type User = {
  id: string;
  email: string;
  fullName: string;
  role: 'CUSTOMER' | 'ADMIN';
  createdAt: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type RegisterPayload = LoginPayload & {
  fullName: string;
};

export type MoviePayload = {
  title: string;
  description: string;
  durationMinutes: number;
  genre: string;
  ageRating: string;
};

export type Room = {
  id: string;
  name: string;
  rows: number;
  cols: number;
  seatCount: number;
};

export type RoomPayload = {
  name: string;
  rows: number;
  cols: number;
  vipRows: number[];
};

export type Showtime = {
  id: string;
  movieId: string;
  auditoriumId: string;
  startsAt: string;
  endsAt: string;
  basePrice: number;
  isOpenForBooking: boolean;
};

export type ShowtimePage = {
  items: Showtime[];
  page: number;
  pageSize: number;
  totalItems: number;
};

export type ShowtimePayload = {
  movieId: string;
  auditoriumId: string;
  startsAt: string;
  basePrice: number;
};

export type Seat = {
  id: string;
  rowLabel: string;
  number: number;
  label: string;
  seatType: 'STANDARD' | 'VIP';
  price: number;
  status: 'AVAILABLE' | 'HELD' | 'BOOKED';
};

export type SeatMap = {
  showtimeId: string;
  movie: Pick<Movie, 'id' | 'title'>;
  auditorium: Pick<Room, 'id' | 'name'>;
  startsAt: string;
  endsAt: string;
  basePrice: number;
  currency: 'VND';
  isOpenForBooking: boolean;
  seats: Seat[];
};



export type BookingStatus = 'HELD' | 'CONFIRMED' | 'CANCELLED' | 'EXPIRED';

export type BookingItem = {
  seatId: string;
  label: string;
  seatType: 'STANDARD' | 'VIP';
  unitPrice: number;
};

export type Booking = {
  id: string;
  showtimeId: string;
  status: BookingStatus;
  createdAt: string;
  expiresAt: string;
  confirmedAt: string | null;
  cancelledAt: string | null;
  totalAmount: number;
  currency: 'VND';
  bookingCode: string | null;
  items: BookingItem[];
};

export type BookingPage = {
  items: Booking[];
  page: number;
  pageSize: number;
  totalItems: number;
};
