import { useCallback, useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom';

import { ApiError, authApi, movieApi } from '../lib/apiClient';
import type { LoginPayload, Movie, MoviePage, MoviePayload, RegisterPayload, User } from '../types';

const TOKEN_KEY = 'man-anh-access-token';
const EMPTY_MOVIE_PAGE: MoviePage = { items: [], page: 1, pageSize: 8, totalItems: 0 };

export type AppContext = {
  authReady: boolean;
  user: User | null;
  movies: MoviePage;
  moviesLoading: boolean;
  moviesError: string;
  login: (payload: LoginPayload) => Promise<User>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => void;
  loadMovies: (query?: string, page?: number, pageSize?: number) => Promise<void>;
  addMovie: (payload: MoviePayload) => Promise<Movie>;
  deleteMovie: (movieId: string) => Promise<void>;
  authenticated: <T>(request: (accessToken: string) => Promise<T>) => Promise<T>;
};

export function AppShell() {
  const location = useLocation();
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState(!token);
  const [movies, setMovies] = useState<MoviePage>(EMPTY_MOVIE_PAGE);
  const [moviesLoading, setMoviesLoading] = useState(true);
  const [moviesError, setMoviesError] = useState('');

  useEffect(() => {
    document.getElementById('main-content')?.focus();
  }, [location.pathname]);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const loadMovies = useCallback(async (query = '', page = 1, pageSize = 8) => {
    setMoviesLoading(true);
    setMoviesError('');
    try {
      setMovies(await movieApi.list(query, page, pageSize));
    } catch (error) {
      setMoviesError(error instanceof Error ? error.message : 'Không thể tải danh sách phim.');
    } finally {
      setMoviesLoading(false);
    }
  }, []);

  useEffect(() => {
    movieApi.list()
      .then(setMovies)
      .catch((error: unknown) => {
        setMoviesError(error instanceof Error ? error.message : 'Không thể tải danh sách phim.');
      })
      .finally(() => setMoviesLoading(false));
  }, []);

  useEffect(() => {
    if (!token) return;
    authApi.me(token)
      .then((currentUser) => {
        setUser(currentUser);
        if (currentUser.role === 'ADMIN') void loadMovies('', 1, 100);
      })
      .catch(logout)
      .finally(() => setAuthReady(true));
  }, [loadMovies, logout, token]);

  const authenticated = useCallback(async <T,>(request: (accessToken: string) => Promise<T>): Promise<T> => {
    if (!token) throw new ApiError(401, 'Vui lòng đăng nhập.');
    try {
      return await request(token);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) logout();
      throw error;
    }
  }, [logout, token]);

  const context: AppContext = {
    authReady,
    user,
    movies,
    moviesLoading,
    moviesError,
    login: async (payload) => {
      const response = await authApi.login(payload);
      localStorage.setItem(TOKEN_KEY, response.accessToken);
      setToken(response.accessToken);
      const currentUser = await authApi.me(response.accessToken);
      setUser(currentUser);
      if (currentUser.role === 'ADMIN') await loadMovies('', 1, 100);
      return currentUser;
    },
    register: async (payload) => {
      await authApi.register(payload);
    },
    logout,
    loadMovies,
    addMovie: async (payload) => {
      const movie = await authenticated((accessToken) => movieApi.create(accessToken, payload));
      await loadMovies('', 1, 100);
      return movie;
    },
    deleteMovie: async (movieId) => {
      await authenticated((accessToken) => movieApi.delete(accessToken, movieId));
      await loadMovies('', 1, 100);
    },
    authenticated,
  };

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Bỏ qua đến nội dung chính</a>
      <header className="site-header">
        <NavLink className="brand" to="/" aria-label="Trang chủ Rạp Màn Ảnh">
          <span className="brand-mark" aria-hidden="true"><i /><i /></span>
          <span className="brand-name"><strong>MÀN ẢNH</strong><small>CINEMA</small></span>
        </NavLink>
        <nav aria-label="Điều hướng chính" className="main-nav">
          <NavLink to="/">Phim</NavLink>
          {user?.role === 'CUSTOMER' && <NavLink to="/tickets">Vé của tôi</NavLink>}
          {user?.role === 'ADMIN' && <NavLink to="/admin" onClick={() => void loadMovies('', 1, 100)}>Quản trị</NavLink>}
        </nav>
        <div className="account-actions">
          {user ? (
            <>
              <span>{user.fullName}</span>
              <button className="text-button" type="button" onClick={logout}>Đăng xuất</button>
            </>
          ) : (
            <>
              <Link className="text-button" to="/register">Đăng ký</Link>
              <Link className="button button-dark" to="/login">Đăng nhập</Link>
            </>
          )}
        </div>
      </header>
      <main id="main-content" tabIndex={-1}>
        <Outlet context={context} />
      </main>
      <footer className="site-footer">
        <span>Rạp Màn Ảnh</span>
        <span>Dữ liệu phim và tài khoản được cung cấp bởi hệ thống.</span>
      </footer>
    </div>
  );
}
