/**
 * Query Client Configuration
 *
 * Task: T020 - 配置 TanStack Query
 * Task: T098 - 请求重试逻辑 (增强重试策略)
 *
 * 配置全局 QueryClient 实例，包含智能重试策略。
 */

import { QueryClient } from "@tanstack/react-query";
import { queryRetryFn, queryRetryDelay } from "@lib/api/interceptors";
import { AppError, getErrorMessage } from "@shared/types";
import { eventBus } from "@shared/events/eventBus";

/**
 * 创建全局 QueryClient 实例
 *
 * 默认配置:
 * - staleTime: 5分钟 - 数据被认为是新鲜的时间
 * - gcTime: 30分钟 - 未使用数据的垃圾回收时间
 * - retry: 智能重试 - 根据错误类型决定是否重试
 * - retryDelay: 指数退避 - 1s, 2s, 4s
 * - refetchOnWindowFocus: false - 禁用窗口聚焦时自动重新获取
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 数据新鲜时间: 5分钟
      staleTime: 1000 * 60 * 5,
      // 垃圾回收时间: 30分钟
      gcTime: 1000 * 60 * 30,
      // 智能重试: 根据错误类型判断是否重试，最多 3 次
      retry: queryRetryFn,
      // 指数退避延迟: 1s → 2s → 4s
      retryDelay: queryRetryDelay,
      // 禁用窗口聚焦时重新获取
      refetchOnWindowFocus: false,
    },
    mutations: {
      // Mutation 默认不重试 (写操作需谨慎)
      retry: false,
      // Mutation 全局错误处理: 控制台日志 + UI 通知
      onError: (error: Error) => {
        if (error instanceof AppError) {
          console.error(
            `[Mutation Error] ${error.code}: ${error.message}`,
            error.details,
          );
        } else {
          console.error(`[Mutation Error] ${getErrorMessage(error)}`);
        }

        // 通过 EventBus 发布通知，让 UI 层显示错误提示
        eventBus.publish("notification:show", {
          type: "error",
          message: getErrorMessage(error),
        });
      },
    },
  },
});
