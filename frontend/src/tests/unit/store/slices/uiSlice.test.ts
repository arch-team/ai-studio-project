/**
 * UI Slice Tests
 *
 * Task: T019 - 配置 Zustand store
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useUIStore } from '@store/slices/uiSlice';

describe('uiSlice', () => {
  beforeEach(() => {
    // 重置 store 状态
    useUIStore.setState({
      sidebarOpen: true,
      theme: 'system',
      breadcrumbs: [],
    });
  });

  describe('初始状态', () => {
    it('should have correct initial state', () => {
      const state = useUIStore.getState();
      expect(state.sidebarOpen).toBe(true);
      expect(state.theme).toBe('system');
      expect(state.breadcrumbs).toEqual([]);
    });
  });

  describe('toggleSidebar', () => {
    it('should toggle sidebar from open to closed', () => {
      const { toggleSidebar } = useUIStore.getState();

      toggleSidebar();

      expect(useUIStore.getState().sidebarOpen).toBe(false);
    });

    it('should toggle sidebar from closed to open', () => {
      useUIStore.setState({ sidebarOpen: false });
      const { toggleSidebar } = useUIStore.getState();

      toggleSidebar();

      expect(useUIStore.getState().sidebarOpen).toBe(true);
    });

    it('should toggle sidebar multiple times', () => {
      const { toggleSidebar } = useUIStore.getState();

      toggleSidebar();
      expect(useUIStore.getState().sidebarOpen).toBe(false);

      toggleSidebar();
      expect(useUIStore.getState().sidebarOpen).toBe(true);
    });
  });

  describe('setSidebarOpen', () => {
    it('should set sidebar to open', () => {
      useUIStore.setState({ sidebarOpen: false });
      const { setSidebarOpen } = useUIStore.getState();

      setSidebarOpen(true);

      expect(useUIStore.getState().sidebarOpen).toBe(true);
    });

    it('should set sidebar to closed', () => {
      const { setSidebarOpen } = useUIStore.getState();

      setSidebarOpen(false);

      expect(useUIStore.getState().sidebarOpen).toBe(false);
    });
  });

  describe('setTheme', () => {
    it('should set theme to dark', () => {
      const { setTheme } = useUIStore.getState();

      setTheme('dark');

      expect(useUIStore.getState().theme).toBe('dark');
    });

    it('should set theme to light', () => {
      const { setTheme } = useUIStore.getState();

      setTheme('light');

      expect(useUIStore.getState().theme).toBe('light');
    });

    it('should set theme to system', () => {
      useUIStore.setState({ theme: 'dark' });
      const { setTheme } = useUIStore.getState();

      setTheme('system');

      expect(useUIStore.getState().theme).toBe('system');
    });
  });

  describe('setBreadcrumbs', () => {
    it('should set breadcrumbs', () => {
      const { setBreadcrumbs } = useUIStore.getState();
      const items = [
        { text: '首页', href: '/' },
        { text: '训练任务', href: '/training-jobs' },
      ];

      setBreadcrumbs(items);

      expect(useUIStore.getState().breadcrumbs).toEqual(items);
    });

    it('should replace existing breadcrumbs', () => {
      useUIStore.setState({
        breadcrumbs: [{ text: '旧页面', href: '/old' }],
      });
      const { setBreadcrumbs } = useUIStore.getState();
      const newItems = [{ text: '新页面', href: '/new' }];

      setBreadcrumbs(newItems);

      expect(useUIStore.getState().breadcrumbs).toEqual(newItems);
    });

    it('should handle empty breadcrumbs', () => {
      useUIStore.setState({
        breadcrumbs: [{ text: '页面', href: '/page' }],
      });
      const { setBreadcrumbs } = useUIStore.getState();

      setBreadcrumbs([]);

      expect(useUIStore.getState().breadcrumbs).toEqual([]);
    });
  });
});
