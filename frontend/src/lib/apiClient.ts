import type {
  LoginPayload,
  Movie,
  MoviePage,
  MoviePayload,
  RegisterPayload,
  Room,
  RoomPayload,
  SeatMap,
  Showtime,
  ShowtimePage,
  ShowtimePayload,
  User,
} from '../types';

type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
  };
};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly code?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ApiErrorBody;
    throw new ApiError(
      response.status,
      body.error?.message ?? `Yêu cầu thất bại (${response.status}).`,
      body.error?.code,
    );
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

const authorization = (token: string): HeadersInit => ({ Authorization: `Bearer ${token}` });

export const authApi = {
  register: (payload: RegisterPayload) =>
    apiRequest<User>('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  login: (payload: LoginPayload) =>
    apiRequest<{ accessToken: string; tokenType: 'Bearer'; expiresIn: number }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  me: (token: string) => apiRequest<User>('/auth/me', { headers: authorization(token) }),
};

export const movieApi = {
  list: (query = '', page = 1, pageSize = 8) => {
    const search = new URLSearchParams({ page: String(page), pageSize: String(pageSize) });
    if (query.trim()) search.set('q', query.trim());
    return apiRequest<MoviePage>(`/movies?${search}`);
  },
  get: (movieId: string) => apiRequest<Movie>(`/movies/${movieId}`),
  create: (token: string, payload: MoviePayload) =>
    apiRequest<Movie>('/movies', {
      method: 'POST',
      headers: authorization(token),
      body: JSON.stringify(payload),
    }),
  delete: (token: string, movieId: string) =>
    apiRequest<void>(`/movies/${movieId}`, {
      method: 'DELETE',
      headers: authorization(token),
    }),
};

export const roomApi = {
  list: (token: string) => apiRequest<Room[]>('/rooms', { headers: authorization(token) }),
  create: (token: string, payload: RoomPayload) =>
    apiRequest<Room>('/rooms', {
      method: 'POST',
      headers: authorization(token),
      body: JSON.stringify(payload),
    }),
};

export const showtimeApi = {
  list: (movieId = '', date = '', pageSize = 100) => {
    const search = new URLSearchParams({ page: '1', pageSize: String(pageSize) });
    if (movieId) search.set('movieId', movieId);
    if (date) search.set('date', date);
    return apiRequest<ShowtimePage>(`/showtimes?${search}`);
  },
  seats: (showtimeId: string) => apiRequest<SeatMap>(`/showtimes/${showtimeId}/seats`),
  create: (token: string, payload: ShowtimePayload) =>
    apiRequest<Showtime>('/showtimes', {
      method: 'POST',
      headers: authorization(token),
      body: JSON.stringify(payload),
    }),
  delete: (token: string, showtimeId: string) =>
    apiRequest<void>(`/showtimes/${showtimeId}`, {
      method: 'DELETE',
      headers: authorization(token),
    }),
};
