/**
 * 模块间事件通信机制
 *
 * 提供轻量级的发布-订阅模式，支持模块间解耦通信。
 * 对应后端的 DomainEvent 和 EventBus 机制。
 */

// === 类型定义 ===

/**
 * 事件基础接口
 */
export interface DomainEvent<T = unknown> {
  type: string;
  payload: T;
  timestamp: number;
  source?: string;
}

/**
 * 事件处理器类型
 */
export type EventHandler<T = unknown> = (event: DomainEvent<T>) => void | Promise<void>;

/**
 * 事件订阅取消函数
 */
export type Unsubscribe = () => void;

// === 事件类型定义 ===

/**
 * 训练任务事件
 */
export interface TrainingJobCreatedEvent {
  jobId: number;
  jobName: string;
  ownerId: number;
}

export interface TrainingJobStatusChangedEvent {
  jobId: number;
  oldStatus: string;
  newStatus: string;
}

export interface TrainingJobCompletedEvent {
  jobId: number;
  duration: number;
  cost: number;
}

/**
 * 数据集事件
 */
export interface DatasetCreatedEvent {
  datasetId: number;
  name: string;
  ownerId: number;
}

export interface DatasetDeletedEvent {
  datasetId: number;
}

/**
 * 开发空间事件
 */
export interface SpaceStartedEvent {
  spaceId: number;
  url: string;
}

export interface SpaceStoppedEvent {
  spaceId: number;
}

/**
 * 配额事件
 */
export interface QuotaExceededEvent {
  userId: number;
  quotaType: string;
  current: number;
  limit: number;
}

/**
 * 认证事件
 */
export interface UserLoggedInEvent {
  userId: number;
  username: string;
}

export interface UserLoggedOutEvent {
  userId: number;
}

/**
 * 通知事件
 */
export interface NotificationEvent {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
}

// === 事件类型映射 ===

export interface EventMap {
  // 训练任务
  'training-job:created': TrainingJobCreatedEvent;
  'training-job:status-changed': TrainingJobStatusChangedEvent;
  'training-job:completed': TrainingJobCompletedEvent;

  // 数据集
  'dataset:created': DatasetCreatedEvent;
  'dataset:deleted': DatasetDeletedEvent;

  // 开发空间
  'space:started': SpaceStartedEvent;
  'space:stopped': SpaceStoppedEvent;

  // 配额
  'quota:exceeded': QuotaExceededEvent;

  // 认证
  'auth:logged-in': UserLoggedInEvent;
  'auth:logged-out': UserLoggedOutEvent;

  // 通知
  'notification:show': NotificationEvent;

  // 通用
  [key: string]: unknown;
}

// === EventBus 实现 ===

class EventBus {
  private handlers: Map<string, Set<EventHandler<unknown>>> = new Map();
  private eventHistory: DomainEvent<unknown>[] = [];
  private maxHistorySize: number = 100;

  /**
   * 订阅事件
   */
  subscribe<K extends keyof EventMap>(
    eventType: K,
    handler: EventHandler<EventMap[K]>
  ): Unsubscribe {
    if (!this.handlers.has(eventType as string)) {
      this.handlers.set(eventType as string, new Set());
    }

    const handlers = this.handlers.get(eventType as string)!;
    handlers.add(handler as EventHandler<unknown>);

    // 返回取消订阅函数
    return () => {
      handlers.delete(handler as EventHandler<unknown>);
      if (handlers.size === 0) {
        this.handlers.delete(eventType as string);
      }
    };
  }

  /**
   * 订阅一次性事件
   */
  once<K extends keyof EventMap>(
    eventType: K,
    handler: EventHandler<EventMap[K]>
  ): Unsubscribe {
    const wrappedHandler: EventHandler<EventMap[K]> = (event) => {
      unsubscribe();
      handler(event);
    };

    const unsubscribe = this.subscribe(eventType, wrappedHandler);
    return unsubscribe;
  }

  /**
   * 发布事件
   */
  publish<K extends keyof EventMap>(
    eventType: K,
    payload: EventMap[K],
    source?: string
  ): void {
    const event: DomainEvent<EventMap[K]> = {
      type: eventType as string,
      payload,
      timestamp: Date.now(),
      source,
    };

    // 记录事件历史
    this.addToHistory(event);

    // 通知所有订阅者
    const handlers = this.handlers.get(eventType as string);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          handler(event);
        } catch (error) {
          console.error(`Error in event handler for ${eventType as string}:`, error);
        }
      });
    }
  }

  /**
   * 异步发布事件
   */
  async publishAsync<K extends keyof EventMap>(
    eventType: K,
    payload: EventMap[K],
    source?: string
  ): Promise<void> {
    const event: DomainEvent<EventMap[K]> = {
      type: eventType as string,
      payload,
      timestamp: Date.now(),
      source,
    };

    this.addToHistory(event);

    const handlers = this.handlers.get(eventType as string);
    if (handlers) {
      await Promise.all(
        Array.from(handlers).map(async (handler) => {
          try {
            await handler(event);
          } catch (error) {
            console.error(`Error in async event handler for ${eventType as string}:`, error);
          }
        })
      );
    }
  }

  /**
   * 获取事件历史
   */
  getHistory(eventType?: string): DomainEvent<unknown>[] {
    if (eventType) {
      return this.eventHistory.filter((e) => e.type === eventType);
    }
    return [...this.eventHistory];
  }

  /**
   * 清除事件历史
   */
  clearHistory(): void {
    this.eventHistory = [];
  }

  /**
   * 清除所有订阅
   */
  clearAllSubscriptions(): void {
    this.handlers.clear();
  }

  /**
   * 获取订阅者数量
   */
  getSubscriberCount(eventType?: string): number {
    if (eventType) {
      return this.handlers.get(eventType)?.size || 0;
    }
    let count = 0;
    this.handlers.forEach((handlers) => {
      count += handlers.size;
    });
    return count;
  }

  private addToHistory(event: DomainEvent<unknown>): void {
    this.eventHistory.push(event);
    if (this.eventHistory.length > this.maxHistorySize) {
      this.eventHistory.shift();
    }
  }
}

// === 导出单例实例 ===

export const eventBus = new EventBus();

// === 导出类用于测试 ===

export { EventBus };
