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

