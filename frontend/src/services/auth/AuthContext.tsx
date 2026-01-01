/**
 * 认证上下文
 *
 * 提供全局认证状态管理和认证操作
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import axios from 'axios';
import { clearAuthTokens, get, isAuthenticated, setAuthTokens } from '../api/client';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

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
      // 直接使用axios调用，因为返回格式不是标准的包装格式
      const token = localStorage.getItem('access_token');
      const response = await axios.get<User>(`${API_BASE_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      setUser(response.data);
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
      // 直接使用axios调用登录API，因为返回格式不是标准的包装格式
      const response = await axios.post<LoginResponse>(
        `${API_BASE_URL}/auth/login`,
        credentials
      );

      // 保存令牌
      setAuthTokens(response.data.access_token, response.data.refresh_token);

      // 加载用户信息
      await loadUser();
    } catch (error: any) {
      console.error('登录失败:', error);
      const message = error.response?.data?.error?.message || error.message || '登录失败';
      throw new Error(message);
    }
  };

  /**
   * 登出
   */
  const logout = async () => {
    try {
      await axios.post(`${API_BASE_URL}/auth/logout`);
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
