/**
 * App Component
 *
 * Task: T017 - 配置 React Router
 * TDD Step 2: Green - 实现代码
 *
 * 应用根组件
 */

import { RouterProvider } from 'react-router-dom';
import { AppProviders } from './providers';
import { router } from './router';

// 引入 Cloudscape 全局样式
import '@cloudscape-design/global-styles/index.css';

/**
 * App 组件
 *
 * 应用入口组件，包含：
 * - AppProviders: 全局 Provider（Query 等）
 * - RouterProvider: React Router
 */
export function App() {
  return (
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>
  );
}
