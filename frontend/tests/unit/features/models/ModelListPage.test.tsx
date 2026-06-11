/**
 * ModelListPage 单元测试
 *
 * 测试模型列表页面的渲染、过滤、分页和交互
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, fireEvent } from '@testing-library/react';
import { renderWithProviders } from '@tests/__utils__/test-utils';
import { ModelListPage } from '@features/models/pages';
import type { ModelSummary, ModelListResponse } from '@features/models/types';

// Mock 数据
const mockModels: ModelSummary[] = [
  {
    id: 1,
    model_name: 'bert-base-v1',
    version: 'v1.0.0',
    display_name: 'BERT Base',
    owner_id: 100,
    training_job_id: 10,
    status: 'registered',
    framework: 'pytorch',
    metrics: { accuracy: 0.95 },
    tags: ['nlp'],
    created_at: '2024-01-15T10:00:00Z',
    registered_at: '2024-01-15T12:00:00Z',
  },
  {
    id: 2,
    model_name: 'resnet50-v2',
    version: 'v2.0.0',
    display_name: 'ResNet50',
    owner_id: 101,
    training_job_id: 20,
    status: 'training',
    framework: 'tensorflow',
    metrics: null,
    tags: null,
    created_at: '2024-02-01T08:00:00Z',
    registered_at: null,
  },
];

const mockListResponse: ModelListResponse = {
  items: mockModels,
  total: 2,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

// Mock hooks
const mockUseModels = vi.fn();
const mockUseBatchArchiveModels = vi.fn();

vi.mock('@features/models/api', () => ({
  useModels: () => mockUseModels(),
  useBatchArchiveModels: () => mockUseBatchArchiveModels(),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('ModelListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseModels.mockReturnValue({
      data: mockListResponse,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    mockUseBatchArchiveModels.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
  });

  describe('基本渲染', () => {
    it('应该渲染页面标题', () => {
      renderWithProviders(<ModelListPage />);
      expect(screen.getByText('模型管理')).toBeInTheDocument();
    });

    it('应该渲染刷新按钮', () => {
      renderWithProviders(<ModelListPage />);
      expect(screen.getByRole('button', { name: /刷新/ })).toBeInTheDocument();
    });

    it('应该渲染模型表格', () => {
      renderWithProviders(<ModelListPage />);
      expect(screen.getByRole('table')).toBeInTheDocument();
    });

    it('应该显示模型数据', () => {
      renderWithProviders(<ModelListPage />);
      expect(screen.getByText('bert-base-v1')).toBeInTheDocument();
      expect(screen.getByText('resnet50-v2')).toBeInTheDocument();
    });
  });

  describe('过滤器', () => {
    it('应该渲染状态过滤下拉框', () => {
      renderWithProviders(<ModelListPage />);
      expect(screen.getByText('全部状态')).toBeInTheDocument();
    });

    it('应该渲染框架过滤下拉框', () => {
      renderWithProviders(<ModelListPage />);
      expect(screen.getByText('全部框架')).toBeInTheDocument();
    });

    it('应该渲染训练任务 ID 过滤输入框', () => {
      renderWithProviders(<ModelListPage />);
      expect(screen.getByText('训练任务 ID')).toBeInTheDocument();
    });
  });

  describe('加载状态', () => {
    it('应该显示加载状态', () => {
      mockUseModels.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(<ModelListPage />);
      expect(screen.getByText('加载中...')).toBeInTheDocument();
    });
  });

  describe('错误处理', () => {
    it('应该显示错误消息', () => {
      mockUseModels.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Network error'),
        refetch: vi.fn(),
      });

      renderWithProviders(<ModelListPage />);
      expect(screen.getByText(/加载失败/)).toBeInTheDocument();
    });
  });

  describe('空状态', () => {
    it('应该显示空状态提示', () => {
      mockUseModels.mockReturnValue({
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
          total_pages: 0,
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(<ModelListPage />);
      expect(screen.getByText('暂无模型')).toBeInTheDocument();
    });
  });

  describe('刷新操作', () => {
    it('点击刷新按钮应触发 refetch', () => {
      const mockRefetch = vi.fn();
      mockUseModels.mockReturnValue({
        data: mockListResponse,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });

      renderWithProviders(<ModelListPage />);
      fireEvent.click(screen.getByRole('button', { name: /刷新/ }));
      expect(mockRefetch).toHaveBeenCalled();
    });
  });

  describe('批量归档', () => {
    it('无选中项时不应该显示批量归档按钮', () => {
      renderWithProviders(<ModelListPage />);
      expect(screen.queryByText(/批量归档/)).not.toBeInTheDocument();
    });
  });
});
