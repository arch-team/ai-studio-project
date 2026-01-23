/**
 * Query Client Configuration
 *
 * Task: T020 - 配置 TanStack Query
 * TDD Step 2: Green - 实现代码
 */

import { QueryClient } from '@tanstack/react-query';

/**
 * 创建全局 QueryClient 实例
 *
 * 默认配置:
 * - staleTime: 5分钟 - 数据被认为是新鲜的时间
 * - gcTime: 30分钟 - 未使用数据的垃圾回收时间
 * - retry: 3 - 失败请求的重试次数
 * - refetchOnWindowFocus: false - 禁用窗口聚焦时自动重新获取
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // 数据新鲜时间: 5分钟
      staleTime: 1000 * 60 * 5,
      // 垃圾回收时间: 30分钟
      gcTime: 1000 * 60 * 30,
      // 重试次数
      retry: 3,
      // 禁用窗口聚焦时重新获取
      refetchOnWindowFocus: false,
    },
  },
});
