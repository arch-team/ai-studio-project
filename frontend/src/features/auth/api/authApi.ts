/**
 * Auth API 函数
 *
 * 对接后端 /api/v1/auth 端点
 */

import { apiClient } from '@shared/api';
import type {
  LoginRequest,
  LoginResponse,
  TokenResponse,
  UserResponse,
  MessageResponse,
} from '../types';

/**
 * 用户名密码登录
 */
export async function loginWithCredentials(
  username: string,
  password: string
): Promise<LoginResponse> {
  const body: LoginRequest = { username, password };
  return apiClient.post<LoginResponse>('/auth/login', body);
}

/**
 * 刷新 Access Token
 */
export async function refreshAccessToken(
  refreshToken: string
): Promise<TokenResponse> {
  return apiClient.post<TokenResponse>('/auth/token/refresh', {
    refresh_token: refreshToken,
  });
}

/**
 * 获取当前用户信息
 */
export async function fetchCurrentUser(): Promise<UserResponse> {
  return apiClient.get<UserResponse>('/auth/me');
}

/**
 * 登出
 */
export async function logoutUser(): Promise<MessageResponse> {
  return apiClient.post<MessageResponse>('/auth/logout');
}
