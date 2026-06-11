/**
 * App Component
 *
 * 应用根组件
 * Task: T099 - 添加全局错误边界
 */

import { useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';
import { AppProviders } from './providers';
import { router } from './router';
import { useAuthStore } from '@features/auth';
import { ErrorBoundary } from '@shared/components/feedback';
import { useThemeEffect } from '@shared/hooks';

// 引入 Cloudscape 全局样式
import '@cloudscape-design/global-styles/index.css';

/**
 * App 组件
 *
 * 应用入口组件，包含：
 * - ErrorBoundary: 全局错误边界
 * - 认证初始化
 * - AppProviders: 全局 Provider（Query 等）
 * - RouterProvider: React Router
 */
export function App() {
  const initializeAuth = useAuthStore((s) => s.initializeAuth);

  // 应用主题与密度偏好到 Cloudscape 全局样式
  useThemeEffect();

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  return (
    <ErrorBoundary title="应用错误">
      <AppProviders>
        <RouterProvider router={router} />
      </AppProviders>
    </ErrorBoundary>
  );
}
