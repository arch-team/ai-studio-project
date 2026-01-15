/**
 * AuthGuard Component
 *
 * Task: T017 - 配置 React Router
 * TDD Step 2: Green - 实现代码
 *
 * 认证守卫，保护需要登录的路由
 */

import { Navigate, useLocation } from 'react-router-dom';
import { Spinner } from '@cloudscape-design/components';
import { useAuthStore } from '@features/auth/store/authStore';
import { ROUTES } from '../routes';

interface AuthGuardProps {
  children: React.ReactNode;
}

/**
 * AuthGuard 组件
 *
 * 功能：
 * - 检查用户认证状态
 * - 未认证时重定向到登录页
 * - 加载时显示加载指示器
 * - 已认证时渲染子组件
 */
export function AuthGuard({ children }: AuthGuardProps) {
  const { isAuthenticated, isLoading } = useAuthStore();
  const location = useLocation();

  // 加载中，显示加载指示器
  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '48px' }}>
        <Spinner size="large" />
      </div>
    );
  }

  // 未认证，重定向到登录页
  if (!isAuthenticated) {
    // 保存当前位置，登录后可以重定向回来
    return <Navigate to={ROUTES.LOGIN} state={{ from: location }} replace />;
  }

  // 已认证，渲染子组件
  return <>{children}</>;
}
