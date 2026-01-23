/**
 * Mock Auth Store
 *
 * 模拟认证状态用于测试
 */

import { vi } from 'vitest';

/**
 * 用户角色类型
 */
export type UserRole = 'admin' | 'developer' | 'viewer';

/**
 * 模拟用户信息
 */
export interface MockUser {
  id: number;
  username: string;
  email: string;
  role: UserRole;
}

/**
 * 预设测试用户
 */
export const mockUsers: Record<UserRole, MockUser> = {
  admin: {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    role: 'admin',
  },
  developer: {
    id: 2,
    username: 'developer',
    email: 'dev@example.com',
    role: 'developer',
  },
  viewer: {
    id: 3,
    username: 'viewer',
    email: 'viewer@example.com',
    role: 'viewer',
  },
};

/**
 * 创建 Mock Auth Store
 */
export function createMockAuthStore(user: MockUser | null = mockUsers.admin) {
  return {
    user,
    isAuthenticated: user !== null,
    isLoading: false,
    error: null,
    login: vi.fn(),
    logout: vi.fn(),
    checkAuth: vi.fn(),
  };
}

/**
 * 设置 localStorage 模拟 token
 */
export function setMockToken(token: string = 'mock-access-token'): void {
  localStorage.setItem('access_token', token);
}

/**
 * 清除模拟 token
 */
export function clearMockToken(): void {
  localStorage.removeItem('access_token');
}
