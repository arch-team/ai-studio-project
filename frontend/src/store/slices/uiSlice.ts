/**
 * UI Slice
 *
 * Task: T019 - 配置 Zustand store
 * 管理全局 UI 状态：侧边栏、主题、面包屑
 */

import { create } from 'zustand';
import type { BreadcrumbItem, ThemeMode } from '@/types/common';

// UI 状态接口
interface UIState {
  // 状态
  sidebarOpen: boolean;
  theme: ThemeMode;
  breadcrumbs: BreadcrumbItem[];

  // 操作
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setTheme: (theme: ThemeMode) => void;
  setBreadcrumbs: (items: BreadcrumbItem[]) => void;
}

// 创建 UI Store
export const useUIStore = create<UIState>((set) => ({
  // 初始状态
  sidebarOpen: true,
  theme: 'system',
  breadcrumbs: [],

  // 切换侧边栏
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  // 设置侧边栏状态
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  // 设置主题
  setTheme: (theme) => set({ theme }),

  // 设置面包屑
  setBreadcrumbs: (items) => set({ breadcrumbs: items }),
}));
