/**
 * NotificationCenter Component
 *
 * 全局通知中心，订阅 EventBus 的 'notification:show' 事件，
 * 使用 Cloudscape Flashbar 统一渲染应用级通知。
 *
 * 接入点: MainLayout 的 AppLayout notifications 槽位。
 *
 * 解决的问题:
 * - 此前 mutation 全局 onError 通过 eventBus 发布 'notification:show'，
 *   但无任何消费者，导致错误通知无法显示。
 */

import { Flashbar, type FlashbarProps } from '@cloudscape-design/components';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useEventSubscription } from '@shared/events';

/** 单条通知的默认自动消失时间（毫秒），error 类型默认不自动消失 */
const DEFAULT_AUTO_DISMISS_MS = 5000;

let notificationCounter = 0;

/**
 * 生成稳定且唯一的通知 ID。
 * 避免使用 Date.now()/Math.random() 之外的依赖，这里用递增计数器。
 */
function nextId(): string {
  notificationCounter += 1;
  return `notification-${notificationCounter}`;
}

/**
 * NotificationCenter 组件
 *
 * 无可见的固定布局，依赖父级 AppLayout 的 notifications 区域定位。
 */
export function NotificationCenter() {
  const [items, setItems] = useState<FlashbarProps.MessageDefinition[]>([]);
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const dismiss = useCallback((id: string) => {
    setItems((prev) => prev.filter((item) => item.id !== id));
    const timer = timersRef.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timersRef.current.delete(id);
    }
  }, []);

  useEventSubscription('notification:show', (event) => {
    const { type, message, duration } = event.payload;
    const id = nextId();

    const item: FlashbarProps.MessageDefinition = {
      id,
      type,
      content: message,
      dismissible: true,
      dismissLabel: '关闭通知',
      onDismiss: () => dismiss(id),
    };

    setItems((prev) => [item, ...prev]);

    // error 类型保持常驻（除非显式传入 duration），其余自动消失
    const autoDismissMs =
      duration ?? (type === 'error' ? undefined : DEFAULT_AUTO_DISMISS_MS);

    if (autoDismissMs && autoDismissMs > 0) {
      const timer = setTimeout(() => dismiss(id), autoDismissMs);
      timersRef.current.set(id, timer);
    }
  });

  // 卸载时清理所有计时器
  useEffect(() => {
    const timers = timersRef.current;
    return () => {
      timers.forEach((timer) => clearTimeout(timer));
      timers.clear();
    };
  }, []);

  return <Flashbar items={items} />;
}
