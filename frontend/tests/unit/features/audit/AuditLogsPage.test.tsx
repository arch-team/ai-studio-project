/**
 * Audit Logs Page Tests
 *
 * Task: T067a - 审计日志查询页面
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import { renderWithProviders } from '@tests/__utils__/test-utils';
import { AuditLogsPage } from '@features/audit';
import type { AuditLog, AuditLogListResponse } from '@features/audit';

// Mock data
const mockAuditLogs: AuditLog[] = [
  {
    id: 1,
    user_id: 1,
    username: 'admin',
    ip_address: '192.168.1.1',
    user_agent: 'Mozilla/5.0',
    action: 'create',
    resource_type: 'training_job',
    resource_id: '123',
    resource_name: 'GPT-Fine-Tune',
    request_method: 'POST',
    request_path: '/api/v1/training-jobs',
    response_status: 201,
    changes: null,
    result: 'success',
    error_message: null,
    created_at: '2024-01-15T10:30:00Z',
  },
  {
    id: 2,
    user_id: 2,
    username: 'engineer',
    ip_address: '192.168.1.2',
    user_agent: 'Mozilla/5.0',
    action: 'delete',
    resource_type: 'dataset',
    resource_id: '456',
    resource_name: 'ImageNet-Subset',
    request_method: 'DELETE',
    request_path: '/api/v1/datasets/456',
    response_status: 200,
    changes: null,
    result: 'success',
    error_message: null,
    created_at: '2024-01-15T11:00:00Z',
  },
  {
    id: 3,
    user_id: 1,
    username: 'admin',
    ip_address: '192.168.1.1',
    user_agent: 'Mozilla/5.0',
    action: 'update',
    resource_type: 'model',
    resource_id: '789',
    resource_name: 'ResNet-50',
    request_method: 'PUT',
    request_path: '/api/v1/models/789',
    response_status: 500,
    changes: { status: { old: 'draft', new: 'published' } },
    result: 'failure',
    error_message: 'Internal server error',
    created_at: '2024-01-15T12:00:00Z',
  },
];

const mockListResponse: AuditLogListResponse = {
  items: mockAuditLogs,
  total: 3,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

// Mock hooks
const mockUseAuditLogs = vi.fn();
const mockUseExportAuditLogs = vi.fn();

vi.mock('@features/audit/api', () => ({
  useAuditLogs: () => mockUseAuditLogs(),
  useExportAuditLogs: () => mockUseExportAuditLogs(),
}));

describe('AuditLogsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock implementations
    mockUseAuditLogs.mockReturnValue({
      data: mockListResponse,
      isLoading: false,
      error: null,
    });

    mockUseExportAuditLogs.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
  });

  describe('基本渲染', () => {
    it('should render page header with title', () => {
      renderWithProviders(<AuditLogsPage />);
      expect(screen.getByRole('heading', { name: /审计日志/i })).toBeInTheDocument();
    });

    it('should render export button', () => {
      renderWithProviders(<AuditLogsPage />);
      expect(screen.getByRole('button', { name: /导出/i })).toBeInTheDocument();
    });

    it('should render audit logs table', () => {
      renderWithProviders(<AuditLogsPage />);
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('should display total count in table header', () => {
      renderWithProviders(<AuditLogsPage />);
      expect(screen.getByText('(3)')).toBeInTheDocument();
    });
  });

  describe('表格列', () => {
    it('should display timestamp column', () => {
      renderWithProviders(<AuditLogsPage />);
      expect(screen.getAllByText(/时间/i).length).toBeGreaterThan(0);
    });

    it('should display user column', () => {
      renderWithProviders(<AuditLogsPage />);
      expect(screen.getAllByText(/用户/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText('admin').length).toBeGreaterThan(0);
    });

    it('should display action column with Chinese label', () => {
      renderWithProviders(<AuditLogsPage />);
      expect(screen.getAllByText(/操作/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText('创建').length).toBeGreaterThan(0);
    });

    it('should display resource type column with Chinese label', () => {
      renderWithProviders(<AuditLogsPage />);
      expect(screen.getAllByText(/资源类型/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText('训练任务').length).toBeGreaterThan(0);
    });

    it('should display resource name column', () => {
      renderWithProviders(<AuditLogsPage />);
      expect(screen.getAllByText(/资源名称/i).length).toBeGreaterThan(0);
      expect(screen.getByText('GPT-Fine-Tune')).toBeInTheDocument();
    });

    it('should display result column', () => {
      renderWithProviders(<AuditLogsPage />);
      expect(screen.getAllByText(/结果/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText('成功').length).toBeGreaterThan(0);
    });
  });

  describe('过滤器', () => {
    it('should render action filter dropdown', () => {
      renderWithProviders(<AuditLogsPage />);
      // Cloudscape Select 默认显示 "全部操作"
      expect(screen.getByText('全部操作')).toBeInTheDocument();
    });

    it('should render resource type filter dropdown', () => {
      renderWithProviders(<AuditLogsPage />);
      // Cloudscape Select 默认显示 "全部资源类型"
      expect(screen.getByText('全部资源类型')).toBeInTheDocument();
    });

    it('should render result filter dropdown', () => {
      renderWithProviders(<AuditLogsPage />);
      // Cloudscape Select 默认显示 "全部结果"
      expect(screen.getByText('全部结果')).toBeInTheDocument();
    });

    it('should render date range picker', () => {
      renderWithProviders(<AuditLogsPage />);
      // 日期范围选择器 placeholder
      expect(screen.getByText('选择时间范围')).toBeInTheDocument();
    });
  });

  describe('加载状态', () => {
    it('should display loading state', () => {
      mockUseAuditLogs.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      });

      renderWithProviders(<AuditLogsPage />);
      expect(screen.getByText('加载中...')).toBeInTheDocument();
    });
  });

  describe('错误处理', () => {
    it('should display error message on failure', () => {
      mockUseAuditLogs.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('服务器内部错误'),
        refetch: vi.fn(),
      });

      renderWithProviders(<AuditLogsPage />);
      expect(screen.getByText(/加载失败/i)).toBeInTheDocument();
      // 错误态保留页面骨架（标题/面包屑）
      expect(screen.getByRole('heading', { name: /审计日志/i })).toBeInTheDocument();
    });

    it('should render retry button and invoke refetch on click', async () => {
      const mockRefetch = vi.fn();
      mockUseAuditLogs.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('服务器内部错误'),
        refetch: mockRefetch,
      });

      renderWithProviders(<AuditLogsPage />);

      const retryButton = await screen.findByRole('button', { name: /重试/i });
      expect(retryButton).toBeInTheDocument();

      fireEvent.click(retryButton);
      await waitFor(() => {
        expect(mockRefetch).toHaveBeenCalled();
      });
    });
  });

  describe('空状态', () => {
    it('should display empty state when no logs', () => {
      mockUseAuditLogs.mockReturnValue({
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

      renderWithProviders(<AuditLogsPage />);
      expect(screen.getByText(/暂无审计日志/i)).toBeInTheDocument();
    });
  });

  describe('导出功能', () => {
    it('should call export mutation when clicking export button', async () => {
      const mockMutate = vi.fn();
      mockUseExportAuditLogs.mockReturnValue({
        mutate: mockMutate,
        isPending: false,
      });

      renderWithProviders(<AuditLogsPage />);

      fireEvent.click(screen.getByRole('button', { name: /导出/i }));

      await waitFor(() => {
        expect(mockMutate).toHaveBeenCalled();
      });
    });

    it('should show loading state on export button while exporting', () => {
      mockUseExportAuditLogs.mockReturnValue({
        mutate: vi.fn(),
        isPending: true,
      });

      renderWithProviders(<AuditLogsPage />);

      // Export button should show loading state
      const exportButton = screen.getByRole('button', { name: /导出/i });
      expect(exportButton).toBeInTheDocument();
    });
  });

  describe('分页', () => {
    it('should display pagination when multiple pages', () => {
      mockUseAuditLogs.mockReturnValue({
        data: {
          ...mockListResponse,
          total: 100,
          total_pages: 5,
        },
        isLoading: false,
        error: null,
      });

      renderWithProviders(<AuditLogsPage />);

      // Cloudscape Pagination 使用 ul 元素
      expect(screen.getByRole('list')).toBeInTheDocument();
    });
  });
});
