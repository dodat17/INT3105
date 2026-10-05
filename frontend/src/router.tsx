import { createBrowserRouter } from 'react-router-dom';

import { AppShell } from './app/AppShell';
import { RequireRole } from './components/RequireRole';
import { AdminPage } from './pages/AdminPage';
import { AuthPage } from './pages/AuthPage';
import { HomePage } from './pages/HomePage';
import { MovieDetailPage } from './pages/MovieDetailPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { TicketsPage } from './pages/TicketsPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    errorElement: <NotFoundPage />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'movies/:movieId', element: <MovieDetailPage /> },
      { path: 'login', element: <AuthPage mode="login" /> },
      { path: 'register', element: <AuthPage mode="register" /> },
      { path: 'tickets', element: <RequireRole role="CUSTOMER"><TicketsPage /></RequireRole> },
      { path: 'admin', element: <RequireRole role="ADMIN"><AdminPage /></RequireRole> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);
