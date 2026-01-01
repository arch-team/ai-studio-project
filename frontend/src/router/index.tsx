/**
 * React Router配置
 *
 * 定义应用路由结构和导航逻辑
 */

import React, { Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from '../services/auth/AuthContext';

// 布局组件(延迟加载)
const MainLayout = React.lazy(() => import('../layouts/MainLayout'));
const AuthLayout = React.lazy(() => import('../layouts/AuthLayout'));

// 页面组件(延迟加载)
const LoginPage = React.lazy(() => import('../pages/auth/LoginPage'));
const DashboardPage = React.lazy(() => import('../pages/dashboard/DashboardPage'));
const NotFoundPage = React.lazy(() => import('../pages/error/NotFoundPage'));

// 训练任务页面
const TrainingJobsPage = React.lazy(() => import('../pages/training/TrainingJobsPage'));
const CreateTrainingJobPage = React.lazy(() => import('../pages/training/CreateTrainingJobPage'));
const TrainingJobDetailPage = React.lazy(() => import('../pages/training/TrainingJobDetailPage'));

/**
 * 加载组件
 */
const LoadingFallback: React.FC = () => (
  <div className="flex items-center justify-center h-screen">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
      <p className="mt-4 text-gray-600">加载中...</p>
    </div>
  </div>
);

/**
 * 受保护的路由组件
 * 需要用户已认证
 */
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <LoadingFallback />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

/**
 * 公开路由组件
 * 已认证用户访问将跳转到首页
 */
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <LoadingFallback />;
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

/**
 * 路由配置组件
 */
const AppRouter: React.FC = () => {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingFallback />}>
        <Routes>
          {/* 认证路由 */}
          <Route
            path="/login"
            element={
              <PublicRoute>
                <AuthLayout>
                  <LoginPage />
                </AuthLayout>
              </PublicRoute>
            }
          />

          {/* 受保护的应用路由 */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            {/* 首页/仪表盘 */}
            <Route index element={<DashboardPage />} />

            {/* 训练任务路由 */}
            <Route path="training-jobs" element={<TrainingJobsPage />} />
            <Route path="training-jobs/create" element={<CreateTrainingJobPage />} />
            <Route path="training-jobs/:id" element={<TrainingJobDetailPage />} />

            {/* 这里后续会添加更多路由 */}
            {/* <Route path="projects" element={<ProjectsPage />} /> */}
            {/* <Route path="datasets" element={<DatasetsPage />} /> */}
          </Route>

          {/* 404页面 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
};

export default AppRouter;
