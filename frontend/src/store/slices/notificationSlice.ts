/**
 * Notification Slice
 *
 * Task: T019 - 配置 Zustand store
 * 管理全局通知状态
 */

import { create } from 'zustand';
import type { Notification, NotificationType } from '@/types/common';

// 生成唯一 ID
const generateId = (): string => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

// 新增通知参数（不含 id）
interface AddNotificationParams {
  type: NotificationType;
  content: string;
  dismissible?: boolean;
  action?: React.ReactNode;
}

// Notification 状态接口
interface NotificationState {
  // 状态
  notifications: Notification[];

  // 操作
  addNotification: (params: AddNotificationParams) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

// 创建 Notification Store
export const useNotificationStore = create<NotificationState>((set) => ({
  // 初始状态
  notifications: [],

  // 添加通知
  addNotification: (params) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        {
          id: generateId(),
          ...params,
        },
      ],
    })),

  // 移除指定通知
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),

  // 清空所有通知
  clearNotifications: () => set({ notifications: [] }),
}));
