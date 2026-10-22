import { lazy } from 'react';
/* eslint-disable react-refresh/only-export-components */
import { createBrowserRouter } from 'react-router-dom';

import { AppShell } from './app/AppShell';
import { RequireRole } from './components/RequireRole';
import { NotFoundPage } from './pages/NotFoundPage';

const AdminPage = lazy(() => import('./pages/AdminPage').then((module) => ({ default: module.AdminPage })));
const AuthPage = lazy(() => import('./pages/AuthPage').then((module) => ({ default: module.AuthPage })));
const HomePage = lazy(() => import('./pages/HomePage').then((module) => ({ default: module.HomePage })));
const MovieDetailPage = lazy(() => import('./pages/MovieDetailPage').then((module) => ({ default: module.MovieDetailPage })));
const TicketDetailPage = lazy(() => import('./pages/TicketDetailPage').then((module) => ({ default: module.TicketDetailPage })));
const TicketsPage = lazy(() => import('./pages/TicketsPage').then((module) => ({ default: module.TicketsPage })));

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
      { path: 'tickets/:bookingId', element: <RequireRole role="CUSTOMER"><TicketDetailPage /></RequireRole> },
      { path: 'admin', element: <RequireRole role="ADMIN"><AdminPage /></RequireRole> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);
