/**
 * Test Setup
 *
 * Vitest 测试环境配置
 * 包含 MSW Server 启动、DOM Mock、全局清理
 */

import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterAll, afterEach, beforeAll, vi } from 'vitest';
import { server } from './__utils__/server';

// === MSW Server 生命周期 ===

// 测试开始前启动 MSW Server
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));

// 每个测试后重置 handlers (清除 server.use() 添加的临时 handlers)
afterEach(() => server.resetHandlers());

// 测试结束后关闭 MSW Server
afterAll(() => server.close());

// 每个测试后自动清理 DOM
afterEach(() => {
  cleanup();
});

// Mock matchMedia for Cloudscape Design System
// Cloudscape 组件依赖 matchMedia 进行响应式布局
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock ResizeObserver for Cloudscape components
class ResizeObserverMock {
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
}

window.ResizeObserver = ResizeObserverMock;

// Mock IntersectionObserver
class IntersectionObserverMock {
  constructor(callback: IntersectionObserverCallback) {
    this.callback = callback;
  }
  callback: IntersectionObserverCallback;
  observe = vi.fn();
  unobserve = vi.fn();
  disconnect = vi.fn();
  root = null;
  rootMargin = '';
  thresholds = [];
  takeRecords = vi.fn().mockReturnValue([]);
}

window.IntersectionObserver = IntersectionObserverMock as unknown as typeof IntersectionObserver;

// Mock scrollTo
window.scrollTo = vi.fn() as unknown as typeof window.scrollTo;
