/**
 * 认证上下文
 *
 * 提供全局认证状态管理和认证操作
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import { clearAuthTokens, get, isAuthenticated, post, setAuthTokens } from '../api/client';

/**
 * 用户信息接口
 */
export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string | null;
  role: string;
  status: string;
  is_active: boolean;
  is_superuser: boolean;
}

/**
 * 登录请求接口
 */
export interface LoginRequest {
  username: string;
  password: string;
}

/**
 * 登录响应接口
 */
interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

/**
 * 认证上下文接口
 */
interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

// 创建认证上下文
const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * 认证Provider组件
 */
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  /**
   * 加载当前用户信息
   */
  const loadUser = async () => {
    if (!isAuthenticated()) {
      setLoading(false);
      return;
    }

    try {
      const userData = await get<User>('/auth/me');
      setUser(userData);
    } catch (error) {
      console.error('加载用户信息失败:', error);
      clearAuthTokens();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 登录
   */
  const login = async (credentials: LoginRequest) => {
    try {
      const response = await post<LoginResponse>('/auth/login', credentials);

      // 保存令牌
      setAuthTokens(response.access_token, response.refresh_token);

      // 加载用户信息
      await loadUser();
    } catch (error) {
      console.error('登录失败:', error);
      throw error;
    }
  };

  /**
   * 登出
   */
  const logout = async () => {
    try {
      await post('/auth/logout');
    } catch (error) {
      console.error('登出失败:', error);
    } finally {
      clearAuthTokens();
      setUser(null);
    }
  };

  /**
   * 刷新用户信息
   */
  const refreshUser = async () => {
    await loadUser();
  };

  // 组件挂载时加载用户信息
  useEffect(() => {
    loadUser();
  }, []);

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * 使用认证上下文Hook
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
