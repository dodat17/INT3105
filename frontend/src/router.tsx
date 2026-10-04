import { createBrowserRouter } from 'react-router-dom';

import { AppShell } from './app/AppShell';
import { AdminPage } from './pages/AdminPage';
import { BookingPage } from './pages/BookingPage';
import { HomePage } from './pages/HomePage';
import { NotFoundPage } from './pages/NotFoundPage';
import { TicketsPage } from './pages/TicketsPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    errorElement: <NotFoundPage />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'booking/:showtimeId', element: <BookingPage /> },
      { path: 'tickets', element: <TicketsPage /> },
      { path: 'admin', element: <AdminPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);
