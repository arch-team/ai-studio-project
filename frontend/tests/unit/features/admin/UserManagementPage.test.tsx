/**
 * User Management Page Tests
 *
 * Task: T064 - 用户管理页面
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import { renderWithProviders } from '@tests/__utils__/test-utils';
import { UserManagementPage } from '@features/admin';
import type { UserDetail, UserListResponse } from '@features/admin';

// Mock data
const mockUsers: UserDetail[] = [
  {
    id: 1,
    username: 'admin',
    email: 'admin@company.com',
    role: 'admin',
    status: 'active',
    resource_quota_id: 1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    username: 'engineer1',
    email: 'engineer1@company.com',
    role: 'engineer',
    status: 'active',
    resource_quota_id: 2,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
  {
    id: 3,
    username: 'viewer1',
    email: 'viewer1@company.com',
    role: 'viewer',
    status: 'disabled',
    resource_quota_id: null,
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z',
  },
];

const mockListResponse: UserListResponse = {
  items: mockUsers,
  total: 3,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

// Mock hooks
const mockUseUsers = vi.fn();
const mockUseCreateUser = vi.fn();
const mockUseUpdateUser = vi.fn();

vi.mock('@features/admin/hooks', () => ({
  useUsers: () => mockUseUsers(),
  useCreateUser: () => mockUseCreateUser(),
  useUpdateUser: () => mockUseUpdateUser(),
}));

describe('UserManagementPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock implementations
    mockUseUsers.mockReturnValue({
      data: mockListResponse,
      isLoading: false,
      error: null,
    });

    mockUseCreateUser.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });

    mockUseUpdateUser.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
  });

  describe('基本渲染', () => {
    it('should render page header with title', () => {
      renderWithProviders(<UserManagementPage />);
      expect(screen.getByRole('heading', { name: /用户管理/i })).toBeInTheDocument();
    });

    it('should render create user button', () => {
      renderWithProviders(<UserManagementPage />);
      expect(screen.getByRole('button', { name: /新建用户/i })).toBeInTheDocument();
    });

    it('should render users table', () => {
      renderWithProviders(<UserManagementPage />);
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('should display total count in table header', () => {
      renderWithProviders(<UserManagementPage />);
      expect(screen.getByText('(3)')).toBeInTheDocument();
    });
  });

  describe('表格列', () => {
    it('should display username column', () => {
      renderWithProviders(<UserManagementPage />);
      expect(screen.getAllByText(/用户名/i).length).toBeGreaterThan(0);
      expect(screen.getByText('admin')).toBeInTheDocument();
    });

    it('should display email column', () => {
      renderWithProviders(<UserManagementPage />);
      expect(screen.getAllByText(/邮箱/i).length).toBeGreaterThan(0);
      expect(screen.getByText('admin@company.com')).toBeInTheDocument();
    });

    it('should display role column with Chinese label', () => {
      renderWithProviders(<UserManagementPage />);
      expect(screen.getAllByText(/角色/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText('管理员').length).toBeGreaterThan(0);
    });

    it('should display status column', () => {
      renderWithProviders(<UserManagementPage />);
      expect(screen.getAllByText(/状态/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText('活跃').length).toBeGreaterThan(0);
    });
  });

  describe('过滤器', () => {
    it('should render role filter dropdown', () => {
      renderWithProviders(<UserManagementPage />);
      expect(screen.getByText('全部角色')).toBeInTheDocument();
    });

    it('should render status filter dropdown', () => {
      renderWithProviders(<UserManagementPage />);
      expect(screen.getByText('全部状态')).toBeInTheDocument();
    });
  });

  describe('加载状态', () => {
    it('should display loading state', () => {
      mockUseUsers.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      });

      renderWithProviders(<UserManagementPage />);
      expect(screen.getByText('加载中...')).toBeInTheDocument();
    });
  });

  describe('错误处理', () => {
    it('should display error message on failure', () => {
      mockUseUsers.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('服务器内部错误'),
        refetch: vi.fn(),
      });

      renderWithProviders(<UserManagementPage />);
      expect(screen.getByText(/加载失败/i)).toBeInTheDocument();
      // 错误态保留页面骨架（标题/面包屑）
      expect(screen.getByRole('heading', { name: /用户管理/i })).toBeInTheDocument();
    });

    it('should render retry button and invoke refetch on click', async () => {
      const mockRefetch = vi.fn();
      mockUseUsers.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('服务器内部错误'),
        refetch: mockRefetch,
      });

      renderWithProviders(<UserManagementPage />);

      const retryButton = await screen.findByRole('button', { name: /重试/i });
      expect(retryButton).toBeInTheDocument();

      fireEvent.click(retryButton);
      await waitFor(() => {
        expect(mockRefetch).toHaveBeenCalled();
      });
    });
  });

  describe('空状态', () => {
    it('should display empty state when no users', () => {
      mockUseUsers.mockReturnValue({
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
          total_pages: 0,
        },
        isLoading: false,
        error: null,
      });

      renderWithProviders(<UserManagementPage />);
      expect(screen.getByText(/暂无用户/i)).toBeInTheDocument();
    });
  });

  describe('创建用户 Modal', () => {
    it('should open create modal when clicking create button', async () => {
      renderWithProviders(<UserManagementPage />);

      fireEvent.click(screen.getByRole('button', { name: /新建用户/i }));

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
      // Modal 标题和按钮都有 "新建用户"，使用 getAllByText
      expect(screen.getAllByText(/新建用户/i).length).toBeGreaterThan(1);
    });

    it('should have cancel button in modal', async () => {
      renderWithProviders(<UserManagementPage />);

      fireEvent.click(screen.getByRole('button', { name: /新建用户/i }));

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: /取消/i })).toBeInTheDocument();
    });
  });

  describe('编辑用户 Modal', () => {
    it('should display edit action button for each row', () => {
      renderWithProviders(<UserManagementPage />);

      const editButtons = screen.getAllByRole('button', { name: /编辑/i });
      expect(editButtons.length).toBe(3); // One for each user
    });

    it('should open edit modal when clicking edit button', async () => {
      renderWithProviders(<UserManagementPage />);

      const editButtons = screen.getAllByRole('button', { name: /编辑/i });
      fireEvent.click(editButtons[0]);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
      expect(screen.getByText(/编辑用户/i)).toBeInTheDocument();
    });
  });

  describe('分页', () => {
    it('should display pagination when multiple pages', () => {
      mockUseUsers.mockReturnValue({
        data: {
          ...mockListResponse,
          total: 100,
          total_pages: 5,
        },
        isLoading: false,
        error: null,
      });

      renderWithProviders(<UserManagementPage />);

      expect(screen.getByRole('list')).toBeInTheDocument();
    });
  });
});
