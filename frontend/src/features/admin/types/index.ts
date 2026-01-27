/**
 * Admin module type definitions.
 *
 * 用户管理模块 - 支持用户 CRUD 和配额关联
 */

// === Enums ===

export type UserRole = 'admin' | 'project_manager' | 'engineer' | 'viewer';
export type UserStatus = 'active' | 'disabled' | 'pending';

// === User Types ===

export interface UserDetail {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  resource_quota_id: number | null;
  iam_identity_id?: string;
  created_at: string;
  updated_at: string;
}

// === Filter Types ===

export interface UserFilters {
  role?: UserRole;
  status?: UserStatus;
  page?: number;
  page_size?: number;
}

// === Response Types ===

export interface UserListResponse {
  items: UserDetail[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// === Request Types ===

export interface CreateUserRequest {
  username: string;
  email: string;
  role: UserRole;
  resource_quota_id?: number | null;
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  role?: UserRole;
  status?: UserStatus;
  resource_quota_id?: number | null;
}

// === UI Helper Types ===

// Cloudscape StatusIndicator 有效类型
type StatusIndicatorType =
  | 'success'
  | 'warning'
  | 'error'
  | 'info'
  | 'stopped'
  | 'pending'
  | 'in-progress'
  | 'loading';

export const USER_ROLE_LABELS: Record<UserRole, string> = {
  admin: '管理员',
  project_manager: '项目经理',
  engineer: '工程师',
  viewer: '查看者',
};

export const USER_ROLE_COLORS: Record<UserRole, StatusIndicatorType> = {
  admin: 'info',
  project_manager: 'success',
  engineer: 'stopped',
  viewer: 'pending',
};

export const USER_STATUS_LABELS: Record<UserStatus, string> = {
  active: '活跃',
  disabled: '已禁用',
  pending: '待激活',
};

export const USER_STATUS_COLORS: Record<UserStatus, StatusIndicatorType> = {
  active: 'success',
  disabled: 'error',
  pending: 'pending',
};
