/**
 * Auth Store
 *
 * 认证状态管理，供路由守卫和 API 客户端使用
 */

import { create } from 'zustand';
import type { User, UserRole } from '@/types/common';
import type { LoginResponse, UserResponse } from '../types';
import { fetchCurrentUser, logoutUser, refreshAccessToken } from '../api';

// === 类型 ===

interface AuthState {
  // 状态
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;

  // Token (refresh_token 仅保存在内存)
  refreshToken: string | null;

  // 操作
  login: (response: LoginResponse) => void;
  logout: () => Promise<void>;
  setLoading: (loading: boolean) => void;
  initializeAuth: () => Promise<void>;
  tryRefreshToken: () => Promise<boolean>;
}

// === 辅助函数 ===

/** 将后端 UserResponse 转换为前端 User 类型 */
function toUser(response: UserResponse): User {
  return {
    id: String(response.id),
    name: response.display_name || response.username,
    email: response.email,
    role: response.role as UserRole,
  };
}

// === Store ===

export const useAuthStore = create<AuthState>((set, get) => ({
  // 初始状态 - isLoading=true 直到 initializeAuth 完成
  isAuthenticated: false,
  user: null,
  isLoading: true,
  refreshToken: null,

  // 登录 - 保存 tokens 和用户信息
  login: (response: LoginResponse) => {
    const { tokens, user } = response;

    // access_token 存 localStorage (ALB 反向代理场景)
    localStorage.setItem('access_token', tokens.access_token);

    set({
      isAuthenticated: true,
      user: toUser(user),
      isLoading: false,
      // refresh_token 仅保存在内存
      refreshToken: tokens.refresh_token,
    });
  },

  // 登出 - 清除所有认证状态
  logout: async () => {
    try {
      // 尝试通知后端（忽略错误）
      await logoutUser().catch(() => {});
    } finally {
      localStorage.removeItem('access_token');
      set({
        isAuthenticated: false,
        user: null,
        isLoading: false,
        refreshToken: null,
      });
    }
  },

  // 设置加载状态
  setLoading: (loading: boolean) => set({ isLoading: loading }),

  // 应用启动时初始化认证状态
  initializeAuth: async () => {
    const token = localStorage.getItem('access_token');

    if (!token) {
      set({ isAuthenticated: false, user: null, isLoading: false });
      return;
    }

    try {
      // 用现有 token 验证用户身份
      const userResponse = await fetchCurrentUser();
      set({
        isAuthenticated: true,
        user: toUser(userResponse),
        isLoading: false,
      });
    } catch {
      // token 无效或过期，清除状态
      localStorage.removeItem('access_token');
      set({
        isAuthenticated: false,
        user: null,
        isLoading: false,
        refreshToken: null,
      });
    }
  },

  // 尝试刷新 token，返回是否成功
  tryRefreshToken: async () => {
    const { refreshToken } = get();
    if (!refreshToken) return false;

    try {
      const tokens = await refreshAccessToken(refreshToken);
      localStorage.setItem('access_token', tokens.access_token);
      set({ refreshToken: tokens.refresh_token });
      return true;
    } catch {
      // 刷新失败，清除状态
      localStorage.removeItem('access_token');
      set({
        isAuthenticated: false,
        user: null,
        refreshToken: null,
      });
      return false;
    }
  },
}));

/**
 * 检查用户是否拥有指定角色
 */
export function hasRole(user: User | null, roles: UserRole[]): boolean {
  if (!user) return false;
  return roles.includes(user.role);
}
