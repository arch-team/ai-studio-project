/**
 * Notification Slice Tests
 *
 * Task: T019 - 配置 Zustand store
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useNotificationStore } from '@store/slices/notificationSlice';

describe('notificationSlice', () => {
  beforeEach(() => {
    // 重置 store 状态
    useNotificationStore.setState({ notifications: [] });
  });

  describe('初始状态', () => {
    it('should have empty notifications initially', () => {
      const state = useNotificationStore.getState();
      expect(state.notifications).toEqual([]);
    });
  });

  describe('addNotification', () => {
    it('should add a success notification', () => {
      const { addNotification } = useNotificationStore.getState();

      addNotification({ type: 'success', content: '操作成功' });

      const notifications = useNotificationStore.getState().notifications;
      expect(notifications).toHaveLength(1);
      expect(notifications[0].type).toBe('success');
      expect(notifications[0].content).toBe('操作成功');
      expect(notifications[0].id).toBeDefined();
    });

    it('should add an error notification', () => {
      const { addNotification } = useNotificationStore.getState();

      addNotification({ type: 'error', content: '操作失败' });

      const notifications = useNotificationStore.getState().notifications;
      expect(notifications).toHaveLength(1);
      expect(notifications[0].type).toBe('error');
    });

    it('should add a warning notification', () => {
      const { addNotification } = useNotificationStore.getState();

      addNotification({ type: 'warning', content: '警告信息' });

      const notifications = useNotificationStore.getState().notifications;
      expect(notifications[0].type).toBe('warning');
    });

    it('should add an info notification', () => {
      const { addNotification } = useNotificationStore.getState();

      addNotification({ type: 'info', content: '提示信息' });

      const notifications = useNotificationStore.getState().notifications;
      expect(notifications[0].type).toBe('info');
    });

    it('should add multiple notifications', () => {
      const { addNotification } = useNotificationStore.getState();

      addNotification({ type: 'success', content: '消息1' });
      addNotification({ type: 'error', content: '消息2' });
      addNotification({ type: 'info', content: '消息3' });

      const notifications = useNotificationStore.getState().notifications;
      expect(notifications).toHaveLength(3);
    });

    it('should generate unique ids for each notification', () => {
      const { addNotification } = useNotificationStore.getState();

      addNotification({ type: 'success', content: '消息1' });
      addNotification({ type: 'success', content: '消息2' });

      const notifications = useNotificationStore.getState().notifications;
      expect(notifications[0].id).not.toBe(notifications[1].id);
    });

    it('should handle notification with dismissible flag', () => {
      const { addNotification } = useNotificationStore.getState();

      addNotification({ type: 'success', content: '可关闭消息', dismissible: true });

      const notifications = useNotificationStore.getState().notifications;
      expect(notifications[0].dismissible).toBe(true);
    });
  });

  describe('removeNotification', () => {
    it('should remove notification by id', () => {
      const { addNotification, removeNotification } = useNotificationStore.getState();

      addNotification({ type: 'success', content: '消息1' });
      addNotification({ type: 'error', content: '消息2' });

      const id = useNotificationStore.getState().notifications[0].id;
      removeNotification(id);

      const notifications = useNotificationStore.getState().notifications;
      expect(notifications).toHaveLength(1);
      expect(notifications[0].content).toBe('消息2');
    });

    it('should not remove anything if id does not exist', () => {
      const { addNotification, removeNotification } = useNotificationStore.getState();

      addNotification({ type: 'success', content: '消息1' });

      removeNotification('non-existent-id');

      expect(useNotificationStore.getState().notifications).toHaveLength(1);
    });

    it('should remove the only notification', () => {
      const { addNotification, removeNotification } = useNotificationStore.getState();

      addNotification({ type: 'success', content: '唯一消息' });

      const id = useNotificationStore.getState().notifications[0].id;
      removeNotification(id);

      expect(useNotificationStore.getState().notifications).toHaveLength(0);
    });
  });

  describe('clearNotifications', () => {
    it('should clear all notifications', () => {
      const { addNotification, clearNotifications } = useNotificationStore.getState();

      addNotification({ type: 'success', content: '消息1' });
      addNotification({ type: 'error', content: '消息2' });
      addNotification({ type: 'info', content: '消息3' });

      clearNotifications();

      expect(useNotificationStore.getState().notifications).toEqual([]);
    });

    it('should handle clearing when already empty', () => {
      const { clearNotifications } = useNotificationStore.getState();

      clearNotifications();

      expect(useNotificationStore.getState().notifications).toEqual([]);
    });
  });
});
