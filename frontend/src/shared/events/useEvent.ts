/**
 * 事件 Hooks
 *
 * 提供 React 组件中使用事件总线的便捷 hooks。
 */

import { useCallback, useEffect, useRef } from 'react';
import { eventBus, EventHandler, EventMap, DomainEvent, Unsubscribe } from './eventBus';

/**
 * 订阅事件 Hook
 *
 * 在组件挂载时自动订阅，卸载时自动取消订阅。
 *
 * @example
 * ```tsx
 * function NotificationListener() {
 *   useEventSubscription('notification:show', (event) => {
 *     showToast(event.payload.message, event.payload.type);
 *   });
 *
 *   return null;
 * }
 * ```
 */
export function useEventSubscription<K extends keyof EventMap>(
  eventType: K,
  handler: EventHandler<EventMap[K]>,
  deps: React.DependencyList = []
) {
  const handlerRef = useRef(handler);

  // 保持 handler 引用最新
  useEffect(() => {
    handlerRef.current = handler;
  }, [handler]);

  useEffect(() => {
    const unsubscribe = eventBus.subscribe(eventType, (event) => {
      handlerRef.current(event);
    });

    return unsubscribe;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventType, ...deps]);
}

/**
 * 发布事件 Hook
 *
 * @example
 * ```tsx
 * function CreateJobButton() {
 *   const publishEvent = useEventPublisher();
 *
 *   const handleCreate = async () => {
 *     const job = await createTrainingJob(data);
 *     publishEvent('training-job:created', {
 *       jobId: job.id,
 *       jobName: job.name,
 *       ownerId: job.owner_id,
 *     });
 *   };
 *
 *   return <Button onClick={handleCreate}>创建任务</Button>;
 * }
 * ```
 */
export function useEventPublisher() {
  return useCallback(
    <K extends keyof EventMap>(
      eventType: K,
      payload: EventMap[K],
      source?: string
    ) => {
      eventBus.publish(eventType, payload, source);
    },
    []
  );
}

/**
 * 发布通知事件 Hook
 *
 * 简化发送通知的操作。
 *
 * @example
 * ```tsx
 * function SaveButton() {
 *   const notify = useNotification();
 *
 *   const handleSave = async () => {
 *     try {
 *       await save();
 *       notify.success('保存成功');
 *     } catch (error) {
 *       notify.error('保存失败');
 *     }
 *   };
 *
 *   return <Button onClick={handleSave}>保存</Button>;
 * }
 * ```
 */
export function useNotification() {
  const publish = useEventPublisher();

  return {
    success: (message: string, duration?: number) => {
      publish('notification:show', { type: 'success', message, duration });
    },
    error: (message: string, duration?: number) => {
      publish('notification:show', { type: 'error', message, duration });
    },
    warning: (message: string, duration?: number) => {
      publish('notification:show', { type: 'warning', message, duration });
    },
    info: (message: string, duration?: number) => {
      publish('notification:show', { type: 'info', message, duration });
    },
  };
}

/**
 * 多事件订阅 Hook
 *
 * 同时订阅多个事件。
 *
 * @example
 * ```tsx
 * useMultiEventSubscription([
 *   ['training-job:created', handleJobCreated],
 *   ['training-job:completed', handleJobCompleted],
 * ]);
 * ```
 */
export function useMultiEventSubscription<K extends keyof EventMap>(
  subscriptions: Array<[K, EventHandler<EventMap[K]>]>
) {
  useEffect(() => {
    const unsubscribes: Unsubscribe[] = subscriptions.map(([eventType, handler]) =>
      eventBus.subscribe(eventType, handler)
    );

    return () => {
      unsubscribes.forEach((unsubscribe) => unsubscribe());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}

/**
 * 事件历史 Hook
 *
 * 获取事件历史记录。
 *
 * @example
 * ```tsx
 * function EventLog() {
 *   const history = useEventHistory('training-job:status-changed');
 *
 *   return (
 *     <ul>
 *       {history.map((event, index) => (
 *         <li key={index}>
 *           {event.payload.newStatus} at {new Date(event.timestamp).toLocaleString()}
 *         </li>
 *       ))}
 *     </ul>
 *   );
 * }
 * ```
 */
export function useEventHistory<K extends keyof EventMap>(
  eventType?: K
): DomainEvent<EventMap[K]>[] {
  return eventBus.getHistory(eventType as string) as DomainEvent<EventMap[K]>[];
}

/**
 * 等待特定事件 Hook
 *
 * 返回一个 Promise，在收到特定事件时 resolve。
 *
 * @example
 * ```tsx
 * function WaitForJob() {
 *   const waitForEvent = useEventWaiter();
 *
 *   const handleWait = async () => {
 *     const event = await waitForEvent('training-job:completed', 60000);
 *     console.log('Job completed:', event.payload);
 *   };
 *
 *   return <Button onClick={handleWait}>等待任务完成</Button>;
 * }
 * ```
 */
export function useEventWaiter() {
  return useCallback(
    <K extends keyof EventMap>(
      eventType: K,
      timeout?: number
    ): Promise<DomainEvent<EventMap[K]>> => {
      return new Promise((resolve, reject) => {
        let timeoutId: ReturnType<typeof setTimeout> | undefined;

        const unsubscribe = eventBus.once(eventType, (event) => {
          if (timeoutId) {
            clearTimeout(timeoutId);
          }
          resolve(event as DomainEvent<EventMap[K]>);
        });

        if (timeout) {
          timeoutId = setTimeout(() => {
            unsubscribe();
            reject(new Error(`Timeout waiting for event: ${eventType as string}`));
          }, timeout);
        }
      });
    },
    []
  );
}
