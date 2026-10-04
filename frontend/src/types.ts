export type Movie = {
  id: string;
  title: string;
  genre: string;
  duration: number;
  ageRating: string;
  description: string;
  accent: string;
  posterLabel: string;
  poster?: string;
};

export type Showtime = {
  id: string;
  movieId: string;
  date: string;
  time: string;
  room: string;
  price: number;
};

export type BookingStatus = 'HELD' | 'CONFIRMED' | 'CANCELLED';

export type Booking = {
  id: string;
  movieId: string;
  showtimeId: string;
  seats: string[];
  total: number;
  status: BookingStatus;
  createdAt: string;
};

export type UserRole = 'CUSTOMER' | 'ADMIN';

export type MockUser = {
  name: string;
  email: string;
  role: UserRole;
};

