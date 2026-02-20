/**
 * User Management API
 *
 * 用户管理 API - 用户 CRUD 操作
 */

import { apiClient } from '@shared/api';
import type {
  UserDetail,
  UserListResponse,
  UserFilters,
  CreateUserRequest,
  UpdateUserRequest,
} from '../types';

/**
 * 获取用户列表
 */
export async function fetchUsers(filters: UserFilters = {}): Promise<UserListResponse> {
  return apiClient.get<UserListResponse>('/users', {
    params: filters as Record<string, string | number | boolean | undefined>,
  });
}

/**
 * 获取单个用户
 */
export async function fetchUser(id: number): Promise<UserDetail> {
  return apiClient.get<UserDetail>(`/users/${id}`);
}

/**
 * 创建用户
 */
export async function createUser(data: CreateUserRequest): Promise<UserDetail> {
  return apiClient.post<UserDetail>('/users', data);
}

/**
 * 更新用户
 */
export async function updateUser(id: number, data: UpdateUserRequest): Promise<UserDetail> {
  return apiClient.put<UserDetail>(`/users/${id}`, data);
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
