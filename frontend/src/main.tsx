import { StrictMode, Suspense } from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';

import { LoadingState } from './components/AsyncStates';
import { router } from './router';
import './styles/tokens.css';
import './styles/global.css';
import './styles/catalog.css';
import './styles/pages.css';
import './styles/management.css';
import './styles/responsive.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Suspense fallback={<LoadingState />}>
      <RouterProvider router={router} />
    </Suspense>
  </StrictMode>,
);
