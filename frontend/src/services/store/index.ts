/**
 * 全局状态管理(Zustand)
 *
 * 提供全局UI状态和其他非认证相关的状态管理
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

/**
 * 通知类型
 */
export type NotificationType = 'success' | 'error' | 'warning' | 'info';

/**
 * 通知接口
 */
export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number;
}

/**
 * 全局状态接口
 */
interface GlobalState {
  // 侧边栏状态
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;

  // 通知
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;

  // 加载状态
  loadingState: Record<string, boolean>;
  setLoading: (key: string, loading: boolean) => void;
  isLoading: (key: string) => boolean;

  // 主题
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

/**
 * 全局状态Store
 */
export const useGlobalStore = create<GlobalState>()(
  devtools(
    persist(
      (set, get) => ({
        // 侧边栏状态
        sidebarOpen: true,
        toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
        setSidebarOpen: (open) => set({ sidebarOpen: open }),

        // 通知
        notifications: [],
        addNotification: (notification) => {
          const id = `notification-${Date.now()}-${Math.random()}`;
          const newNotification: Notification = { id, ...notification };

          set((state) => ({
            notifications: [...state.notifications, newNotification],
          }));

          // 自动移除通知
          if (notification.duration !== 0) {
            setTimeout(() => {
              get().removeNotification(id);
            }, notification.duration || 5000);
          }
        },
        removeNotification: (id) => {
          set((state) => ({
            notifications: state.notifications.filter((n) => n.id !== id),
          }));
        },
        clearNotifications: () => set({ notifications: [] }),

        // 加载状态
        loadingState: {},
        setLoading: (key, loading) => {
          set((state) => ({
            loadingState: {
              ...state.loadingState,
              [key]: loading,
            },
          }));
        },
        isLoading: (key) => get().loadingState[key] || false,

        // 主题
        theme: 'system',
        setTheme: (theme) => set({ theme }),
      }),
      {
        name: 'global-store',
        // 只持久化部分状态
        partialize: (state) => ({
          sidebarOpen: state.sidebarOpen,
          theme: state.theme,
        }),
      }
    ),
    { name: 'GlobalStore' }
  )
);

/**
 * 通知便捷方法
 */
export const notify = {
  success: (title: string, message?: string, duration?: number) => {
    useGlobalStore.getState().addNotification({ type: 'success', title, message, duration });
  },
  error: (title: string, message?: string, duration?: number) => {
    useGlobalStore.getState().addNotification({ type: 'error', title, message, duration });
  },
  warning: (title: string, message?: string, duration?: number) => {
    useGlobalStore.getState().addNotification({ type: 'warning', title, message, duration });
  },
  info: (title: string, message?: string, duration?: number) => {
    useGlobalStore.getState().addNotification({ type: 'info', title, message, duration });
  },
};
