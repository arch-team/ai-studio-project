/**
 * Auth Store
 *
 * Task: T017 - 配置 React Router
 * 认证状态管理，供路由守卫使用
 */

import { create } from 'zustand';
import type { User, UserRole } from '@/types/common';

// 认证状态接口
interface AuthState {
  // 状态
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;

  // 操作
  login: (user: User) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
}

// 开发模式默认用户
const DEV_USER: User = {
  id: 'dev-user-1',
  name: '开发用户',
  email: 'dev@example.com',
  role: 'admin',
};

// 是否为开发模式
const isDev = import.meta.env.DEV;

/**
 * 创建 Auth Store
 *
 * 管理用户认证状态：
 * - isAuthenticated: 是否已认证
 * - user: 当前用户信息
 * - isLoading: 加载状态（用于认证检查中）
 */
export const useAuthStore = create<AuthState>((set) => ({
  // 初始状态 - 开发模式下自动认证
  isAuthenticated: isDev,
  user: isDev ? DEV_USER : null,
  isLoading: false, // 开发模式下无需加载

  // 登录
  login: (user) =>
    set({
      isAuthenticated: true,
      user,
      isLoading: false,
    }),

  // 登出
  logout: () =>
    set({
      isAuthenticated: false,
      user: null,
      isLoading: false,
    }),

  // 设置加载状态
  setLoading: (loading) => set({ isLoading: loading }),
}));

/**
 * 检查用户是否拥有指定角色
 */
export function hasRole(user: User | null, roles: UserRole[]): boolean {
  if (!user) return false;
  return roles.includes(user.role);
}
