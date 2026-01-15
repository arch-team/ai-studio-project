/**
 * Common Types
 *
 * 全局共享类型定义
 */

// 面包屑项类型
export interface BreadcrumbItem {
  text: string;
  href: string;
}

// 通知类型
export type NotificationType = 'success' | 'error' | 'warning' | 'info';

// 通知项类型
export interface Notification {
  id: string;
  type: NotificationType;
  content: string;
  dismissible?: boolean;
  action?: React.ReactNode;
}

// 主题类型
export type ThemeMode = 'light' | 'dark' | 'system';

// 用户角色类型
export type UserRole = 'admin' | 'team_lead' | 'project_manager' | 'engineer' | 'viewer';

// 用户类型
export interface User {
  id: string;
  name: string;
  email?: string;
  role: UserRole;
}
