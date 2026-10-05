import type { ReactNode } from 'react';
import { Navigate, useLocation, useOutletContext } from 'react-router-dom';

import type { AppContext } from '../app/AppShell';
import { LoadingState } from './AsyncStates';

type RequireRoleProps = {
  children: ReactNode;
  role: 'CUSTOMER' | 'ADMIN';
};

export function RequireRole({ children, role }: RequireRoleProps) {
  const { authReady, user } = useOutletContext<AppContext>();
  const location = useLocation();

  if (!authReady) return <LoadingState />;
  if (!user) return <Navigate replace state={{ from: location.pathname }} to="/login" />;
  if (user.role !== role) return <Navigate replace to="/" />;
  return children;
}
