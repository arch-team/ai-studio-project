/**
 * 测试工具模块
 *
 * 提供测试所需的渲染包装器和工具函数
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, RenderOptions } from '@testing-library/react';
import { ReactElement, ReactNode } from 'react';
import { MemoryRouter, MemoryRouterProps } from 'react-router-dom';

/**
 * 创建测试用 QueryClient
 * 禁用重试和缓存，确保测试隔离性
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
        staleTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

interface WrapperProps {
  children: ReactNode;
}

interface RenderWithProvidersOptions extends Omit<RenderOptions, 'wrapper'> {
  routerProps?: MemoryRouterProps;
  queryClient?: QueryClient;
}

/**
 * 带完整 Provider 的渲染函数
 * 包含 QueryClientProvider 和 MemoryRouter
 */
export function renderWithProviders(
  ui: ReactElement,
  options: RenderWithProvidersOptions = {}
) {
  const { routerProps = {}, queryClient = createTestQueryClient(), ...renderOptions } = options;

  function Wrapper({ children }: WrapperProps) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter {...routerProps}>{children}</MemoryRouter>
      </QueryClientProvider>
    );
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    queryClient,
  };
}

/**
 * 仅带 QueryClient 的渲染函数
 * 用于不需要路由的组件测试
 */
export function renderWithQuery(ui: ReactElement, options: RenderWithProvidersOptions = {}) {
  const { queryClient = createTestQueryClient(), ...renderOptions } = options;

  function Wrapper({ children }: WrapperProps) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  }

  return {
    ...render(ui, { wrapper: Wrapper, ...renderOptions }),
    queryClient,
  };
}

// Re-export testing-library utilities
export * from '@testing-library/react';
export { renderWithProviders as render };
