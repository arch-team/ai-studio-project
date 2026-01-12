/**
 * Main Application Component
 *
 * Task: T017 - 配置 React Router
 * 路由配置 (/training-jobs, /datasets, /admin, /reports, /ide)
 */

import { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import MainLayout from './layouts/MainLayout';
import HomePage from './pages/HomePage';

// Lazy-loaded pages for code splitting (will be implemented in later phases)
// const TrainingJobsPage = lazy(() => import('./pages/TrainingJobsPage'));
// const TrainingJobDetailPage = lazy(() => import('./pages/TrainingJobDetailPage'));
// const DatasetsPage = lazy(() => import('./pages/DatasetsPage'));
// const DatasetDetailPage = lazy(() => import('./pages/DatasetDetailPage'));
// const ModelsPage = lazy(() => import('./pages/ModelsPage'));
// const QuotasPage = lazy(() => import('./pages/QuotasPage'));
// const MonitoringPage = lazy(() => import('./pages/MonitoringPage'));
// const SpacesPage = lazy(() => import('./pages/SpacesPage'));
// const AdminPage = lazy(() => import('./pages/AdminPage'));
// const ReportsPage = lazy(() => import('./pages/ReportsPage'));

// Configure React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 30, // 30 minutes (garbage collection time)
      refetchOnWindowFocus: false,
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
    mutations: {
      retry: 1,
    },
  },
});

// Loading fallback component
function LoadingFallback() {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      Loading...
    </div>
  );
}

// Placeholder component for pages not yet implemented
function PlaceholderPage({ title }: { title: string }) {
  return (
    <div style={{ padding: '20px' }}>
      <h1>{title}</h1>
      <p>This page will be implemented in a later phase.</p>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <MainLayout>
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            {/* Home */}
            <Route path="/" element={<HomePage />} />

            {/* Training Management (Phase 3) */}
            <Route
              path="/training-jobs"
              element={<PlaceholderPage title="Training Jobs" />}
            />
            <Route
              path="/training-jobs/:id"
              element={<PlaceholderPage title="Training Job Detail" />}
            />
            <Route
              path="/models"
              element={<PlaceholderPage title="Models" />}
            />
            <Route
              path="/models/:id"
              element={<PlaceholderPage title="Model Detail" />}
            />

            {/* Data Management (Phase 4) */}
            <Route
              path="/datasets"
              element={<PlaceholderPage title="Datasets" />}
            />
            <Route
              path="/datasets/:id"
              element={<PlaceholderPage title="Dataset Detail" />}
            />

            {/* Resource Management (Phase 5) */}
            <Route
              path="/quotas"
              element={<PlaceholderPage title="Resource Quotas" />}
            />
            <Route
              path="/monitoring"
              element={<PlaceholderPage title="Cluster Monitoring" />}
            />

            {/* Admin (Phase 6) */}
            <Route
              path="/admin"
              element={<PlaceholderPage title="Admin Dashboard" />}
            />
            <Route
              path="/admin/users"
              element={<PlaceholderPage title="User Management" />}
            />
            <Route
              path="/admin/audit-logs"
              element={<PlaceholderPage title="Audit Logs" />}
            />

            {/* Development Spaces (Phase 7) */}
            <Route
              path="/spaces"
              element={<PlaceholderPage title="Development Spaces" />}
            />
            <Route
              path="/spaces/:id"
              element={<PlaceholderPage title="Space Detail" />}
            />

            {/* Reports (Phase 6) */}
            <Route
              path="/reports"
              element={<PlaceholderPage title="Reports & Analytics" />}
            />

            {/* Catch-all redirect */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </MainLayout>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;
