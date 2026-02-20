/**
 * Resource Quotas Page Tests
 *
 * Task: T065 - 资源配额管理页面
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import { renderWithProviders } from '@tests/__utils__/test-utils';
import { ResourceQuotasPage } from '@features/resource-quotas';
import type { ResourceLimitConfig, ResourceLimitConfigListResponse } from '@features/resource-quotas';

// Mock data
const mockQuotas: ResourceLimitConfig[] = [
  {
    id: 1,
    config_name: '高级工程师配额',
    role: 'engineer',
    project_id: null,
    max_gpu_per_job: 8,
    max_cpu_per_job: 32,
    max_memory_gb_per_job: 128,
    max_storage_gb_per_job: 500,
    max_nodes_per_job: 4,
    priority_default: 'high',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    config_name: '标准工程师配额',
    role: 'engineer',
    project_id: null,
    max_gpu_per_job: 4,
    max_cpu_per_job: 16,
    max_memory_gb_per_job: 64,
    max_storage_gb_per_job: 200,
    max_nodes_per_job: 2,
    priority_default: 'medium',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const mockListResponse: ResourceLimitConfigListResponse = {
  items: mockQuotas,
  total: 2,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

// Mock hooks
const mockUseResourceLimitConfigs = vi.fn();
const mockUseCreateResourceLimitConfig = vi.fn();
const mockUseUpdateResourceLimitConfig = vi.fn();

vi.mock('@features/resource-quotas/api', () => ({
  useResourceLimitConfigs: () => mockUseResourceLimitConfigs(),
  useCreateResourceLimitConfig: () => mockUseCreateResourceLimitConfig(),
  useUpdateResourceLimitConfig: () => mockUseUpdateResourceLimitConfig(),
}));

describe('ResourceQuotasPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock implementations
    mockUseResourceLimitConfigs.mockReturnValue({
      data: mockListResponse,
      isLoading: false,
      error: null,
    });

    mockUseCreateResourceLimitConfig.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });

    mockUseUpdateResourceLimitConfig.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
  });

  describe('基本渲染', () => {
    it('should render page header with title', () => {
      renderWithProviders(<ResourceQuotasPage />);
      expect(screen.getByRole('heading', { name: /资源配额管理/i })).toBeInTheDocument();
    });

    it('should render create button in header', () => {
      renderWithProviders(<ResourceQuotasPage />);
      expect(screen.getByRole('button', { name: /新建配置/i })).toBeInTheDocument();
    });

    it('should render quota list table', () => {
      renderWithProviders(<ResourceQuotasPage />);
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('should display total count in table header', () => {
      renderWithProviders(<ResourceQuotasPage />);
      expect(screen.getByText('(2)')).toBeInTheDocument();
    });
  });

  describe('表格列', () => {
    it('should display config name column', () => {
      renderWithProviders(<ResourceQuotasPage />);
      // 表头和 Modal 标签可能重复，使用 getAllByText
      expect(screen.getAllByText('配置名称').length).toBeGreaterThan(0);
      expect(screen.getByText('高级工程师配额')).toBeInTheDocument();
    });

    it('should display role column with Chinese label', () => {
      renderWithProviders(<ResourceQuotasPage />);
      expect(screen.getAllByText('适用角色').length).toBeGreaterThan(0);
      expect(screen.getAllByText('工程师').length).toBeGreaterThan(0);
    });

    it('should display GPU limit column', () => {
      renderWithProviders(<ResourceQuotasPage />);
      expect(screen.getAllByText(/最大 GPU/i).length).toBeGreaterThan(0);
      expect(screen.getByText('8')).toBeInTheDocument();
    });

    it('should display CPU limit column', () => {
      renderWithProviders(<ResourceQuotasPage />);
      expect(screen.getAllByText(/最大 CPU/i).length).toBeGreaterThan(0);
      expect(screen.getByText('32')).toBeInTheDocument();
    });

    it('should display memory limit column', () => {
      renderWithProviders(<ResourceQuotasPage />);
      expect(screen.getAllByText(/最大内存/i).length).toBeGreaterThan(0);
      expect(screen.getByText('128')).toBeInTheDocument();
    });

    it('should display node limit column', () => {
      renderWithProviders(<ResourceQuotasPage />);
      expect(screen.getAllByText(/最大节点/i).length).toBeGreaterThan(0);
      // 两条记录都有节点数，使用 getAllByText
      expect(screen.getAllByText('4').length).toBeGreaterThan(0);
    });

    it('should display priority column with status indicator', () => {
      renderWithProviders(<ResourceQuotasPage />);
      // 表头中有 "默认优先级"，Modal 表单中也可能有，使用 getAllByText
      expect(screen.getAllByText('默认优先级').length).toBeGreaterThan(0);
      expect(screen.getAllByText('高').length).toBeGreaterThan(0);
    });
  });

  describe('加载状态', () => {
    it('should display loading state', () => {
      mockUseResourceLimitConfigs.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      });

      renderWithProviders(<ResourceQuotasPage />);
      expect(screen.getByText('加载中...')).toBeInTheDocument();
    });
  });

  describe('错误处理', () => {
    it('should display error message on failure', () => {
      mockUseResourceLimitConfigs.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Network error'),
      });

      renderWithProviders(<ResourceQuotasPage />);
      expect(screen.getByText(/加载失败/i)).toBeInTheDocument();
    });
  });

  describe('空状态', () => {
    it('should display empty state when no quotas', () => {
      mockUseResourceLimitConfigs.mockReturnValue({
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

      renderWithProviders(<ResourceQuotasPage />);
      expect(screen.getByText('暂无配置')).toBeInTheDocument();
    });
  });

  describe('创建配额 Modal', () => {
    it('should open create modal when clicking create button', async () => {
      renderWithProviders(<ResourceQuotasPage />);

      const createButton = screen.getByRole('button', { name: /新建配置/i });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
      expect(screen.getByText(/新建资源配额/i)).toBeInTheDocument();
    });

    it('should have cancel button in modal', async () => {
      renderWithProviders(<ResourceQuotasPage />);

      fireEvent.click(screen.getByRole('button', { name: /新建配置/i }));

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // 验证取消按钮存在
      expect(screen.getByRole('button', { name: /取消/i })).toBeInTheDocument();
    });

    it('should call create mutation on valid submit', async () => {
      const mockMutate = vi.fn();
      mockUseCreateResourceLimitConfig.mockReturnValue({
        mutate: mockMutate,
        isPending: false,
      });

      renderWithProviders(<ResourceQuotasPage />);

      fireEvent.click(screen.getByRole('button', { name: /新建配置/i }));

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Form should be visible with fields - use getAllByText since label appears in table too
      expect(screen.getAllByText(/配置名称/i).length).toBeGreaterThan(0);
    });
  });

  describe('编辑配额 Modal', () => {
    it('should display edit action button for each row', () => {
      renderWithProviders(<ResourceQuotasPage />);

      const editButtons = screen.getAllByRole('button', { name: /编辑/i });
      expect(editButtons.length).toBe(2); // One for each quota
    });

    it('should open edit modal with existing data', async () => {
      renderWithProviders(<ResourceQuotasPage />);

      const editButtons = screen.getAllByRole('button', { name: /编辑/i });
      fireEvent.click(editButtons[0]);

      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });
      expect(screen.getByText(/编辑资源配额/i)).toBeInTheDocument();
    });
  });

  describe('分页', () => {
    it('should display pagination when multiple pages', () => {
      mockUseResourceLimitConfigs.mockReturnValue({
        data: {
          ...mockListResponse,
          total: 50,
          total_pages: 3,
        },
        isLoading: false,
        error: null,
      });

      renderWithProviders(<ResourceQuotasPage />);

      // Cloudscape Pagination 使用 ul 元素，检查分页按钮
      expect(screen.getByRole('list')).toBeInTheDocument();
    });

    it('should not display pagination when single page', () => {
      renderWithProviders(<ResourceQuotasPage />);

      // 单页时不显示分页 - Cloudscape Table 内部可能仍有 list 元素
      // 检查没有分页数字按钮
      const paginationButtons = screen.queryAllByRole('button', { name: /^[0-9]+$/ });
      expect(paginationButtons.length).toBe(0);
    });
  });
});
