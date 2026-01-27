/**
 * User Management API
 *
 * 用户管理 API - 用户 CRUD 操作
 */

import type {
  UserDetail,
  UserListResponse,
  UserFilters,
  CreateUserRequest,
  UpdateUserRequest,
} from '../types';

const API_BASE = '/api/v1';

/**
 * 获取认证请求头
 */
function getAuthHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
  };
}

/**
 * 构建带参数的 URL
 */
function buildUrl(path: string, params?: Record<string, unknown>): string {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    });
  }
  return url.toString();
}

/**
 * 处理响应
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP Error: ${response.status}`);
  }
  return response.json();
}

/**
 * 获取用户列表
 */
export async function fetchUsers(filters: UserFilters = {}): Promise<UserListResponse> {
  const url = buildUrl('/users', filters as Record<string, unknown>);
  const response = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse<UserListResponse>(response);
}

/**
 * 获取单个用户
 */
export async function fetchUser(id: number): Promise<UserDetail> {
  const response = await fetch(`${API_BASE}/users/${id}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });
  return handleResponse<UserDetail>(response);
}

/**
 * 创建用户
 */
export async function createUser(data: CreateUserRequest): Promise<UserDetail> {
  const response = await fetch(`${API_BASE}/users`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  return handleResponse<UserDetail>(response);
}

/**
 * 更新用户
 */
export async function updateUser(id: number, data: UpdateUserRequest): Promise<UserDetail> {
  const response = await fetch(`${API_BASE}/users/${id}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  return handleResponse<UserDetail>(response);
}

/**
 * 禁用用户
 */
export async function disableUser(id: number): Promise<UserDetail> {
  return updateUser(id, { status: 'disabled' });
}

/**
 * 启用用户
 */
export async function enableUser(id: number): Promise<UserDetail> {
  return updateUser(id, { status: 'active' });
}
