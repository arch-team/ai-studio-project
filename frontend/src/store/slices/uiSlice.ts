/**
 * UI Slice
 *
 * Task: T019 - 配置 Zustand store
 * 管理全局 UI 状态：侧边栏、主题、密度、面包屑
 *
 * 注意: 仅持久化非敏感的 UI 偏好（主题、密度、侧边栏），
 * 不持久化面包屑（每个页面动态设置）。
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { BreadcrumbItem, ThemeMode } from '@/types/common';

/** 内容密度模式 */
export type DensityMode = 'comfortable' | 'compact';

// UI 状态接口
interface UIState {
  // 状态
  sidebarOpen: boolean;
  theme: ThemeMode;
  density: DensityMode;
  breadcrumbs: BreadcrumbItem[];

  // 操作
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: ThemeMode) => void;
  setDensity: (density: DensityMode) => void;
  setBreadcrumbs: (items: BreadcrumbItem[]) => void;
}

// 创建 UI Store（持久化非敏感 UI 偏好）
export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      // 初始状态
      sidebarOpen: true,
      theme: 'system',
      density: 'comfortable',
      breadcrumbs: [],

      // 切换侧边栏
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

      // 设置侧边栏状态
      setSidebarOpen: (open) => set({ sidebarOpen: open }),

      // 设置主题
      setTheme: (theme) => set({ theme }),

      // 设置密度
      setDensity: (density) => set({ density }),

      // 设置面包屑
      setBreadcrumbs: (items) => set({ breadcrumbs: items }),
    }),
    {
      name: 'ui-storage',
      // 仅持久化 UI 偏好，面包屑不持久化
      partialize: (state) => ({
        sidebarOpen: state.sidebarOpen,
        theme: state.theme,
        density: state.density,
      }),
    }
  )
);
