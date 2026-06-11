/**
 * useEventSubscription / useEventPublisher / useNotification / useMultiEventSubscription / useEventHistory / useEventWaiter 单元测试
 */

import { renderHook, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { eventBus } from '@shared/events';
import {
  useEventSubscription,
  useEventPublisher,
  useNotification,
  useMultiEventSubscription,
  useEventHistory,
  useEventWaiter,
} from '@shared/events';

describe('useEvent hooks', () => {
  beforeEach(() => {
    eventBus.clearAllSubscriptions();
    eventBus.clearHistory();
  });

  // === useEventSubscription ===

  describe('useEventSubscription', () => {
    it('应在挂载时订阅事件', () => {
      const handler = vi.fn();

      renderHook(() => useEventSubscription('notification:show', handler));

      eventBus.publish('notification:show', { type: 'success', message: 'test' });

      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'notification:show',
          payload: { type: 'success', message: 'test' },
        })
      );
    });

    it('应在卸载时取消订阅', () => {
      const handler = vi.fn();

      const { unmount } = renderHook(() =>
        useEventSubscription('notification:show', handler)
      );

      unmount();

      eventBus.publish('notification:show', { type: 'info', message: 'after-unmount' });

      expect(handler).not.toHaveBeenCalled();
    });

    it('应始终使用最新的 handler 引用', () => {
      const results: string[] = [];

      const { rerender } = renderHook(
        ({ handler }) => useEventSubscription('notification:show', handler),
        {
          initialProps: {
            handler: vi.fn(() => results.push('handler-v1')),
          },
        }
      );

      eventBus.publish('notification:show', { type: 'info', message: 'test' });
      expect(results).toEqual(['handler-v1']);

      rerender({
        handler: vi.fn(() => results.push('handler-v2')),
      });

      eventBus.publish('notification:show', { type: 'info', message: 'test2' });
      expect(results).toEqual(['handler-v1', 'handler-v2']);
    });
  });

  // === useEventPublisher ===

  describe('useEventPublisher', () => {
    it('应返回发布函数', () => {
      const { result } = renderHook(() => useEventPublisher());

      expect(typeof result.current).toBe('function');
    });

    it('应通过 eventBus 发布事件', () => {
      const handler = vi.fn();
      eventBus.subscribe('training-job:created', handler);

      const { result } = renderHook(() => useEventPublisher());

      act(() => {
        result.current('training-job:created', {
          jobId: 1,
          jobName: 'test-job',
          ownerId: 1,
        });
      });

      expect(handler).toHaveBeenCalledTimes(1);
      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          payload: { jobId: 1, jobName: 'test-job', ownerId: 1 },
        })
      );
    });

    it('应传递 source 参数', () => {
      const handler = vi.fn();
      eventBus.subscribe('notification:show', handler);

      const { result } = renderHook(() => useEventPublisher());

      act(() => {
        result.current('notification:show', { type: 'info', message: 'test' }, 'my-component');
      });

      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({ source: 'my-component' })
      );
    });
  });

  // === useNotification ===

  describe('useNotification', () => {
    it('应提供 success/error/warning/info 方法', () => {
      const { result } = renderHook(() => useNotification());

      expect(typeof result.current.success).toBe('function');
      expect(typeof result.current.error).toBe('function');
      expect(typeof result.current.warning).toBe('function');
      expect(typeof result.current.info).toBe('function');
    });

    it('success 应发布 success 类型的通知事件', () => {
      const handler = vi.fn();
      eventBus.subscribe('notification:show', handler);

      const { result } = renderHook(() => useNotification());

      act(() => {
        result.current.success('操作成功');
      });

      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          payload: { type: 'success', message: '操作成功', duration: undefined },
        })
      );
    });

    it('error 应发布 error 类型的通知事件', () => {
      const handler = vi.fn();
      eventBus.subscribe('notification:show', handler);

      const { result } = renderHook(() => useNotification());

      act(() => {
        result.current.error('操作失败', 5000);
      });

      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          payload: { type: 'error', message: '操作失败', duration: 5000 },
        })
      );
    });

    it('warning 应发布 warning 类型的通知事件', () => {
      const handler = vi.fn();
      eventBus.subscribe('notification:show', handler);

      const { result } = renderHook(() => useNotification());

      act(() => {
        result.current.warning('注意');
      });

      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          payload: expect.objectContaining({ type: 'warning', message: '注意' }),
        })
      );
    });

    it('info 应发布 info 类型的通知事件', () => {
      const handler = vi.fn();
      eventBus.subscribe('notification:show', handler);

      const { result } = renderHook(() => useNotification());

      act(() => {
        result.current.info('提示信息');
      });

      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          payload: expect.objectContaining({ type: 'info', message: '提示信息' }),
        })
      );
    });
  });

  // === useMultiEventSubscription ===

  describe('useMultiEventSubscription', () => {
    it('应同时订阅多个事件', () => {
      const notifyHandler = vi.fn();
      const jobHandler = vi.fn();

      renderHook(() =>
        useMultiEventSubscription([
          ['notification:show', notifyHandler],
          ['training-job:created', jobHandler],
        ])
      );

      eventBus.publish('notification:show', { type: 'info', message: 'test' });
      eventBus.publish('training-job:created', { jobId: 1, jobName: 'job1', ownerId: 1 });

      expect(notifyHandler).toHaveBeenCalledTimes(1);
      expect(jobHandler).toHaveBeenCalledTimes(1);
    });

    it('应在卸载时取消所有订阅', () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();

      const { unmount } = renderHook(() =>
        useMultiEventSubscription([
          ['notification:show', handler1],
          ['training-job:created', handler2],
        ])
      );

      unmount();

      eventBus.publish('notification:show', { type: 'info', message: 'test' });
      eventBus.publish('training-job:created', { jobId: 1, jobName: 'job1', ownerId: 1 });

      expect(handler1).not.toHaveBeenCalled();
      expect(handler2).not.toHaveBeenCalled();
    });
  });

  // === useEventHistory ===

  describe('useEventHistory', () => {
    it('应返回事件历史', () => {
      eventBus.publish('notification:show', { type: 'success', message: 'msg1' });
      eventBus.publish('notification:show', { type: 'error', message: 'msg2' });

      const { result } = renderHook(() => useEventHistory('notification:show'));

      expect(result.current).toHaveLength(2);
      expect(result.current[0].type).toBe('notification:show');
    });

    it('无事件类型参数时应返回所有历史', () => {
      eventBus.publish('notification:show', { type: 'info', message: 'msg' });
      eventBus.publish('training-job:created', { jobId: 1, jobName: 'job', ownerId: 1 });

      const { result } = renderHook(() => useEventHistory());

      expect(result.current).toHaveLength(2);
    });
  });

  // === useEventWaiter ===

  describe('useEventWaiter', () => {
    beforeEach(() => vi.useFakeTimers());
    afterEach(() => vi.useRealTimers());

    it('应返回等待函数', () => {
      const { result } = renderHook(() => useEventWaiter());
      expect(typeof result.current).toBe('function');
    });

    it('应在收到事件时 resolve', async () => {
      vi.useRealTimers(); // 本测试使用真实定时器

      const { result } = renderHook(() => useEventWaiter());

      const waitPromise = result.current('training-job:completed');

      // 稍后发布事件
      setTimeout(() => {
        eventBus.publish('training-job:completed', {
          jobId: 1,
          duration: 100,
          cost: 5.0,
        });
      }, 10);

      const event = await waitPromise;

      expect(event.type).toBe('training-job:completed');
      expect(event.payload).toEqual({ jobId: 1, duration: 100, cost: 5.0 });
    });

    it('应在超时后 reject', async () => {
      const { result } = renderHook(() => useEventWaiter());

      const waitPromise = result.current('training-job:completed', 1000);

      // 推进时间超过超时
      act(() => {
        vi.advanceTimersByTime(1001);
      });

      await expect(waitPromise).rejects.toThrow('Timeout waiting for event: training-job:completed');
    });
  });
});
