/**
 * EventBus 单元测试
 */

import { vi, describe, it, expect, beforeEach } from 'vitest';
import { EventBus } from '@shared/events';
import type { NotificationEvent, TrainingJobCreatedEvent } from '@shared/events';

describe('EventBus', () => {
  let bus: EventBus;

  beforeEach(() => {
    bus = new EventBus();
  });

  // === subscribe / publish ===

  describe('subscribe / publish', () => {
    it('应将事件发送给订阅者', () => {
      const handler = vi.fn();
      bus.subscribe('notification:show', handler);

      const payload: NotificationEvent = { type: 'success', message: '操作成功' };
      bus.publish('notification:show', payload);

      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'notification:show',
          payload,
          timestamp: expect.any(Number),
        })
      );
    });

    it('应支持多个订阅者', () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();

      bus.subscribe('notification:show', handler1);
      bus.subscribe('notification:show', handler2);

      bus.publish('notification:show', { type: 'info', message: 'test' });

      expect(handler1).toHaveBeenCalledTimes(1);
      expect(handler2).toHaveBeenCalledTimes(1);
    });

    it('不同事件类型的订阅者应互不影响', () => {
      const notificationHandler = vi.fn();
      const jobHandler = vi.fn();

      bus.subscribe('notification:show', notificationHandler);
      bus.subscribe('training-job:created', jobHandler);

      bus.publish('notification:show', { type: 'success', message: 'test' });

      expect(notificationHandler).toHaveBeenCalledTimes(1);
      expect(jobHandler).not.toHaveBeenCalled();
    });

    it('publish 应包含 source 字段', () => {
      const handler = vi.fn();
      bus.subscribe('notification:show', handler);

      bus.publish('notification:show', { type: 'info', message: 'test' }, 'test-source');

      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({ source: 'test-source' })
      );
    });

    it('事件处理器抛出异常时不应影响其他处理器', () => {
      const errorHandler = vi.fn().mockImplementation(() => {
        throw new Error('处理器错误');
      });
      const normalHandler = vi.fn();
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      bus.subscribe('notification:show', errorHandler);
      bus.subscribe('notification:show', normalHandler);

      bus.publish('notification:show', { type: 'info', message: 'test' });

      expect(errorHandler).toHaveBeenCalled();
      expect(normalHandler).toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });
  });

  // === unsubscribe ===

  describe('unsubscribe', () => {
    it('取消订阅后应不再收到事件', () => {
      const handler = vi.fn();
      const unsubscribe = bus.subscribe('notification:show', handler);

      bus.publish('notification:show', { type: 'info', message: 'first' });
      expect(handler).toHaveBeenCalledTimes(1);

      unsubscribe();

      bus.publish('notification:show', { type: 'info', message: 'second' });
      expect(handler).toHaveBeenCalledTimes(1);
    });

    it('取消最后一个订阅者时应清理事件类型', () => {
      const handler = vi.fn();
      const unsubscribe = bus.subscribe('notification:show', handler);

      expect(bus.getSubscriberCount('notification:show')).toBe(1);

      unsubscribe();

      expect(bus.getSubscriberCount('notification:show')).toBe(0);
    });
  });

  // === once ===

  describe('once', () => {
    it('应只触发一次', () => {
      const handler = vi.fn();
      bus.once('notification:show', handler);

      bus.publish('notification:show', { type: 'info', message: 'first' });
      bus.publish('notification:show', { type: 'info', message: 'second' });

      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          payload: { type: 'info', message: 'first' },
        })
      );
    });

    it('once 返回的 unsubscribe 应在触发前取消', () => {
      const handler = vi.fn();
      const unsubscribe = bus.once('notification:show', handler);

      unsubscribe();

      bus.publish('notification:show', { type: 'info', message: 'test' });
      expect(handler).not.toHaveBeenCalled();
    });
  });

  // === publishAsync ===

  describe('publishAsync', () => {
    it('应等待所有异步处理器完成', async () => {
      const results: string[] = [];

      bus.subscribe('training-job:created', async () => {
        await new Promise((resolve) => setTimeout(resolve, 10));
        results.push('handler1');
      });

      bus.subscribe('training-job:created', async () => {
        await new Promise((resolve) => setTimeout(resolve, 5));
        results.push('handler2');
      });

      const payload: TrainingJobCreatedEvent = {
        jobId: 1,
        jobName: 'test',
        ownerId: 1,
      };

      await bus.publishAsync('training-job:created', payload);

      expect(results).toContain('handler1');
      expect(results).toContain('handler2');
    });

    it('异步处理器抛出异常不应影响其他处理器', async () => {
      const normalHandler = vi.fn();
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      bus.subscribe('training-job:created', async () => {
        throw new Error('异步错误');
      });
      bus.subscribe('training-job:created', normalHandler);

      await bus.publishAsync('training-job:created', {
        jobId: 1,
        jobName: 'test',
        ownerId: 1,
      });

      expect(normalHandler).toHaveBeenCalled();
      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });
  });

  // === getHistory ===

  describe('getHistory', () => {
    it('应记录发布的事件历史', () => {
      bus.publish('notification:show', { type: 'success', message: 'test1' });
      bus.publish('notification:show', { type: 'error', message: 'test2' });

      const history = bus.getHistory();

      expect(history).toHaveLength(2);
      expect(history[0].type).toBe('notification:show');
      expect(history[1].type).toBe('notification:show');
    });

    it('应支持按事件类型过滤历史', () => {
      bus.publish('notification:show', { type: 'success', message: 'notify' });
      bus.publish('training-job:created', { jobId: 1, jobName: 'job', ownerId: 1 });
      bus.publish('notification:show', { type: 'error', message: 'error' });

      const filtered = bus.getHistory('notification:show');

      expect(filtered).toHaveLength(2);
      filtered.forEach((event) => {
        expect(event.type).toBe('notification:show');
      });
    });

    it('应限制历史记录最大数量', () => {
      // EventBus 默认 maxHistorySize = 100
      for (let i = 0; i < 110; i++) {
        bus.publish('notification:show', { type: 'info', message: `msg-${i}` });
      }

      const history = bus.getHistory();
      expect(history).toHaveLength(100);

      // 最早的 10 条应被移除
      const firstPayload = history[0].payload as NotificationEvent;
      expect(firstPayload.message).toBe('msg-10');
    });

    it('返回的历史应为副本，修改不影响内部状态', () => {
      bus.publish('notification:show', { type: 'info', message: 'test' });

      const history = bus.getHistory();
      history.length = 0;

      expect(bus.getHistory()).toHaveLength(1);
    });
  });

  // === clearHistory ===

  describe('clearHistory', () => {
    it('应清除所有事件历史', () => {
      bus.publish('notification:show', { type: 'info', message: 'test' });
      expect(bus.getHistory()).toHaveLength(1);

      bus.clearHistory();
      expect(bus.getHistory()).toHaveLength(0);
    });
  });

  // === clearAllSubscriptions ===

  describe('clearAllSubscriptions', () => {
    it('应清除所有订阅', () => {
      bus.subscribe('notification:show', vi.fn());
      bus.subscribe('training-job:created', vi.fn());
      expect(bus.getSubscriberCount()).toBe(2);

      bus.clearAllSubscriptions();
      expect(bus.getSubscriberCount()).toBe(0);
    });
  });

  // === getSubscriberCount ===

  describe('getSubscriberCount', () => {
    it('应返回特定事件类型的订阅者数量', () => {
      bus.subscribe('notification:show', vi.fn());
      bus.subscribe('notification:show', vi.fn());
      bus.subscribe('training-job:created', vi.fn());

      expect(bus.getSubscriberCount('notification:show')).toBe(2);
      expect(bus.getSubscriberCount('training-job:created')).toBe(1);
      expect(bus.getSubscriberCount('dataset:created')).toBe(0);
    });

    it('不传参数时应返回总订阅者数量', () => {
      bus.subscribe('notification:show', vi.fn());
      bus.subscribe('notification:show', vi.fn());
      bus.subscribe('training-job:created', vi.fn());

      expect(bus.getSubscriberCount()).toBe(3);
    });
  });
});
