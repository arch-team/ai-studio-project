/**
 * RoleGuard Component
 *
 * Task: T017 - 配置 React Router
 * TDD Step 2: Green - 实现代码
 *
 * 角色守卫，保护需要特定角色的路由
 */

import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@features/auth/store/authStore';
import type { UserRole } from '@/types/common';
import { ROUTES } from '../routes';

interface RoleGuardProps {
  children: React.ReactNode;
  allowedRoles: UserRole[];
  redirectTo?: string;
}

/**
 * RoleGuard 组件
 *
 * 功能：
 * - 检查用户角色是否匹配允许的角色列表
 * - 角色不匹配时重定向到指定页面（默认为未授权页面）
 * - 角色匹配时渲染子组件
 */
export function RoleGuard({
  children,
  allowedRoles,
  redirectTo = ROUTES.UNAUTHORIZED,
}: RoleGuardProps) {
  const { user } = useAuthStore();

  // 用户不存在或角色不在允许列表中
  if (!user || !allowedRoles.includes(user.role)) {
    return <Navigate to={redirectTo} replace />;
  }

  // 角色匹配，渲染子组件
  return <>{children}</>;
}
