/**
 * AuthGuard Tests
 *
 * Task: T017 - 配置 React Router
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuthGuard } from '@app/router/guards/AuthGuard';
import { useAuthStore } from '@features/auth/store/authStore';

// Mock useAuthStore
vi.mock('@features/auth/store/authStore', () => ({
  useAuthStore: vi.fn(),
}));

describe('AuthGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('已认证用户', () => {
    it('should render children when authenticated', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', name: 'Test User', role: 'engineer' },
        isLoading: false,
      } as ReturnType<typeof useAuthStore>);

      render(
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route
              path="/protected"
              element={
                <AuthGuard>
                  <div>受保护内容</div>
                </AuthGuard>
              }
            />
            <Route path="/login" element={<div>登录页</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('受保护内容')).toBeInTheDocument();
    });

    it('should not redirect authenticated user', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', name: 'Test User', role: 'engineer' },
        isLoading: false,
      } as ReturnType<typeof useAuthStore>);

      render(
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route
              path="/protected"
              element={
                <AuthGuard>
                  <div>受保护内容</div>
                </AuthGuard>
              }
            />
            <Route path="/login" element={<div>登录页</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.queryByText('登录页')).not.toBeInTheDocument();
    });
  });

  describe('未认证用户', () => {
    it('should redirect to login when not authenticated', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        user: null,
        isLoading: false,
      } as ReturnType<typeof useAuthStore>);

      render(
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route
              path="/protected"
              element={
                <AuthGuard>
                  <div>受保护内容</div>
                </AuthGuard>
              }
            />
            <Route path="/login" element={<div>登录页</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('登录页')).toBeInTheDocument();
    });

    it('should not render protected content when not authenticated', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        user: null,
        isLoading: false,
      } as ReturnType<typeof useAuthStore>);

      render(
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route
              path="/protected"
              element={
                <AuthGuard>
                  <div>受保护内容</div>
                </AuthGuard>
              }
            />
            <Route path="/login" element={<div>登录页</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.queryByText('受保护内容')).not.toBeInTheDocument();
    });
  });

  describe('加载状态', () => {
    it('should show loading indicator while checking auth', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        user: null,
        isLoading: true,
      } as ReturnType<typeof useAuthStore>);

      render(
        <MemoryRouter initialEntries={['/protected']}>
          <Routes>
            <Route
              path="/protected"
              element={
                <AuthGuard>
                  <div>受保护内容</div>
                </AuthGuard>
              }
            />
            <Route path="/login" element={<div>登录页</div>} />
          </Routes>
        </MemoryRouter>
      );

      // 加载时不应该显示受保护内容
      expect(screen.queryByText('受保护内容')).not.toBeInTheDocument();
      // 也不应该重定向到登录页
      expect(screen.queryByText('登录页')).not.toBeInTheDocument();
    });
  });
});
