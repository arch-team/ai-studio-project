/**
 * Query Provider
 *
 * Task: T020 - 配置 TanStack Query
 * TanStack Query 全局 Provider
 */

import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { queryClient } from '@lib/query/queryClient';

interface QueryProviderProps {
  children: React.ReactNode;
}

/**
 * QueryProvider 组件
 *
 * 提供 TanStack Query 的上下文，包含：
 * - QueryClientProvider: Query 客户端
 * - ReactQueryDevtools: 开发工具（仅开发环境）
 */
export function QueryProvider({ children }: QueryProviderProps) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
