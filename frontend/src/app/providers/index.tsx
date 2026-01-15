/**
 * Global Providers
 *
 * Task: T017 - 配置 React Router
 * 统一管理全局 Providers
 */

import { QueryProvider } from './QueryProvider';

interface AppProvidersProps {
  children: React.ReactNode;
}

/**
 * AppProviders 组件
 *
 * 组合所有全局 Provider：
 * - QueryProvider: TanStack Query
 * - 其他 Provider 可以按需添加
 */
export function AppProviders({ children }: AppProvidersProps) {
  return <QueryProvider>{children}</QueryProvider>;
}
