/**
 * RoleGuard Tests
 *
 * Task: T017 - 配置 React Router
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { RoleGuard } from '@app/router/guards/RoleGuard';
import { useAuthStore } from '@features/auth/store/authStore';

// Mock useAuthStore
vi.mock('@features/auth/store/authStore', () => ({
  useAuthStore: vi.fn(),
}));

describe('RoleGuard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('角色匹配', () => {
    it('should render children when user has required role', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', name: 'Admin', role: 'admin' },
        isLoading: false,
      } as ReturnType<typeof useAuthStore>);

      render(
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route
              path="/admin"
              element={
                <RoleGuard allowedRoles={['admin']}>
                  <div>管理页面</div>
                </RoleGuard>
              }
            />
            <Route path="/unauthorized" element={<div>无权限</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('管理页面')).toBeInTheDocument();
    });

    it('should render when user has one of multiple allowed roles', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', name: 'Leader', role: 'team_lead' },
        isLoading: false,
      } as ReturnType<typeof useAuthStore>);

      render(
        <MemoryRouter initialEntries={['/reports']}>
          <Routes>
            <Route
              path="/reports"
              element={
                <RoleGuard allowedRoles={['admin', 'team_lead']}>
                  <div>报表页面</div>
                </RoleGuard>
              }
            />
            <Route path="/unauthorized" element={<div>无权限</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('报表页面')).toBeInTheDocument();
    });
  });

  describe('角色不匹配', () => {
    it('should redirect when user lacks required role', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', name: 'User', role: 'engineer' },
        isLoading: false,
      } as ReturnType<typeof useAuthStore>);

      render(
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route
              path="/admin"
              element={
                <RoleGuard allowedRoles={['admin']}>
                  <div>管理页面</div>
                </RoleGuard>
              }
            />
            <Route path="/unauthorized" element={<div>无权限</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('无权限')).toBeInTheDocument();
    });

    it('should not render protected content when role mismatches', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', name: 'User', role: 'engineer' },
        isLoading: false,
      } as ReturnType<typeof useAuthStore>);

      render(
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route
              path="/admin"
              element={
                <RoleGuard allowedRoles={['admin']}>
                  <div>管理页面</div>
                </RoleGuard>
              }
            />
            <Route path="/unauthorized" element={<div>无权限</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.queryByText('管理页面')).not.toBeInTheDocument();
    });
  });

  describe('未认证用户', () => {
    it('should redirect to unauthorized when user is null', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: false,
        user: null,
        isLoading: false,
      } as ReturnType<typeof useAuthStore>);

      render(
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route
              path="/admin"
              element={
                <RoleGuard allowedRoles={['admin']}>
                  <div>管理页面</div>
                </RoleGuard>
              }
            />
            <Route path="/unauthorized" element={<div>无权限</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('无权限')).toBeInTheDocument();
    });
  });

  describe('自定义重定向', () => {
    it('should redirect to custom path when specified', () => {
      vi.mocked(useAuthStore).mockReturnValue({
        isAuthenticated: true,
        user: { id: '1', name: 'User', role: 'engineer' },
        isLoading: false,
      } as ReturnType<typeof useAuthStore>);

      render(
        <MemoryRouter initialEntries={['/admin']}>
          <Routes>
            <Route
              path="/admin"
              element={
                <RoleGuard allowedRoles={['admin']} redirectTo="/home">
                  <div>管理页面</div>
                </RoleGuard>
              }
            />
            <Route path="/home" element={<div>首页</div>} />
            <Route path="/unauthorized" element={<div>无权限</div>} />
          </Routes>
        </MemoryRouter>
      );

      expect(screen.getByText('首页')).toBeInTheDocument();
    });
  });
});
