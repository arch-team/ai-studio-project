/**
 * Auth Store
 *
 * 认证状态管理，供路由守卫和 API 客户端使用
 */

import { create } from "zustand";
import type { User, UserRole } from "@/types/common";
import type { LoginResponse, UserResponse } from "../types";
import { fetchCurrentUser, logoutUser, refreshAccessToken } from "../api";

// === 类型 ===

interface AuthState {
  // 状态
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;

  // Token (均仅保存在内存，禁止持久化到 localStorage)
  accessToken: string | null;
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

// refreshToken 使用 sessionStorage 持久化（标签页级别会话）：
// - accessToken 仅内存，刷新页面即失效，泄露面最小
// - refreshToken 存 sessionStorage，使整页刷新/导航后可静默续期，避免用户被登出
// - 标签页关闭即清除，不使用 localStorage（见 .claude/rules/security.md）
const REFRESH_TOKEN_KEY = "auth.refresh_token";

function readStoredRefreshToken(): string | null {
  try {
    return sessionStorage.getItem(REFRESH_TOKEN_KEY);
  } catch {
    return null;
  }
}

function writeStoredRefreshToken(token: string | null): void {
  try {
    if (token === null) {
      sessionStorage.removeItem(REFRESH_TOKEN_KEY);
    } else {
      sessionStorage.setItem(REFRESH_TOKEN_KEY, token);
    }
  } catch {
    // sessionStorage 不可用（隐私模式等）时退化为纯内存会话
  }
}

// === Store ===

export const useAuthStore = create<AuthState>((set, get) => ({
  // 初始状态 - isLoading=true 直到 initializeAuth 完成
  isAuthenticated: false,
  user: null,
  isLoading: true,
  accessToken: null,
  refreshToken: readStoredRefreshToken(),

  // 登录 - 保存 tokens 和用户信息
  login: (response: LoginResponse) => {
    const { tokens, user } = response;

    writeStoredRefreshToken(tokens.refresh_token);
    set({
      isAuthenticated: true,
      user: toUser(user),
      isLoading: false,
      // accessToken 仅保存在内存
      accessToken: tokens.access_token,
      refreshToken: tokens.refresh_token,
    });
  },

  // 登出 - 清除所有认证状态
  logout: async () => {
    try {
      // 尝试通知后端（忽略错误）
      await logoutUser().catch(() => {});
    } finally {
      writeStoredRefreshToken(null);
      set({
        isAuthenticated: false,
        user: null,
        isLoading: false,
        accessToken: null,
        refreshToken: null,
      });
    }
  },

  // 设置加载状态
  setLoading: (loading: boolean) => set({ isLoading: loading }),

  // 应用启动时初始化认证状态
  initializeAuth: async () => {
    const { accessToken, refreshToken } = get();

    if (!accessToken) {
      // 内存中无 accessToken，尝试用 refreshToken 刷新
      if (refreshToken) {
        const refreshed = await get().tryRefreshToken();
        if (refreshed) {
          try {
            const userResponse = await fetchCurrentUser();
            set({
              isAuthenticated: true,
              user: toUser(userResponse),
              isLoading: false,
            });
            return;
          } catch {
            // 刷新后仍然失败，清除状态
          }
        }
      }
      writeStoredRefreshToken(null);
      set({
        isAuthenticated: false,
        user: null,
        isLoading: false,
        accessToken: null,
        refreshToken: null,
      });
      return;
    }

    try {
      // 用内存中的 token 验证用户身份
      const userResponse = await fetchCurrentUser();
      set({
        isAuthenticated: true,
        user: toUser(userResponse),
        isLoading: false,
      });
    } catch {
      // token 无效或过期，清除状态
      writeStoredRefreshToken(null);
      set({
        isAuthenticated: false,
        user: null,
        isLoading: false,
        accessToken: null,
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
      writeStoredRefreshToken(tokens.refresh_token);
      set({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
      });
      return true;
    } catch {
      // 刷新失败，清除状态
      writeStoredRefreshToken(null);
      set({
        isAuthenticated: false,
        user: null,
        accessToken: null,
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
