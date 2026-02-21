/**
 * App Component Tests
 *
 * 测试应用根组件渲染
 */

import { describe, it, expect, vi } from 'vitest';

// Mock router 模块，避免加载完整路由配置
vi.mock('@app/router', () => ({
  router: {
    // createBrowserRouter 返回的最小 mock
  },
}));

// Mock RouterProvider，避免需要真实 router 对象
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    RouterProvider: ({ router: _router }: { router: unknown }) => (
      <div data-testid="router-provider">Router Active</div>
    ),
  };
});

import { render, screen } from '@testing-library/react';
import { App } from '@app/App';

describe('App', () => {
  it('should render without crashing', () => {
    render(<App />);
    expect(screen.getByTestId('router-provider')).toBeInTheDocument();
  });

  it('should render RouterProvider inside AppProviders', () => {
    render(<App />);
    expect(screen.getByText('Router Active')).toBeInTheDocument();
  });
});
