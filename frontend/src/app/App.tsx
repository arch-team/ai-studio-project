/**
 * App Component
 *
 * 应用根组件
 */

import { useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';
import { AppProviders } from './providers';
import { router } from './router';
import { useAuthStore } from '@features/auth';

// 引入 Cloudscape 全局样式
import '@cloudscape-design/global-styles/index.css';

/**
 * App 组件
 *
 * 应用入口组件，包含：
 * - 认证初始化
 * - AppProviders: 全局 Provider（Query 等）
 * - RouterProvider: React Router
 */
export function App() {
  const initializeAuth = useAuthStore((s) => s.initializeAuth);

  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  return (
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>
  );
}
