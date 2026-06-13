/**
 * Cost Analysis Page Tests
 *
 * Task: T075 - 成本分析仪表盘前端页面
 * 覆盖：基本渲染、加载状态、错误处理（InlineErrorState + 重试）
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import { renderWithProviders } from '@tests/__utils__/test-utils';
import { CostAnalysisPage } from '@features/reports';
import type { CostAnalysisResponse } from '@features/reports';

// Mock data
const mockCostAnalysisData: CostAnalysisResponse = {
  summary: {
    total_cost_usd: 1234.56,
    compute_cost_usd: 900.0,
    storage_cost_usd: 234.56,
    network_cost_usd: 100.0,
    data_transfer_cost_usd: 0,
    other_cost_usd: 0,
    period_start: '2024-01-01',
    period_end: '2024-01-31',
  },
  breakdown: [
    {
      category: 'compute',
      name: '计算资源',
      cost_usd: 900.0,
      percentage: 72.9,
      item_count: 10,
    },
    {
      category: 'storage',
      name: '存储资源',
      cost_usd: 234.56,
      percentage: 19.0,
      item_count: 5,
    },
  ],
  daily_costs: [
    {
      date: '2024-01-01',
      total_cost_usd: 40.0,
      compute_cost_usd: 30.0,
      storage_cost_usd: 8.0,
      network_cost_usd: 2.0,
      other_cost_usd: 0,
    },
  ],
  period: {
    start_date: '2024-01-01',
    end_date: '2024-01-31',
  },
};

// Mock hooks
const mockUseCostAnalysis = vi.fn();
const mockUseExportReport = vi.fn();

vi.mock('@features/reports/api', () => ({
  useCostAnalysis: () => mockUseCostAnalysis(),
  useExportReport: () => mockUseExportReport(),
}));

describe('CostAnalysisPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseCostAnalysis.mockReturnValue({
      data: mockCostAnalysisData,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    mockUseExportReport.mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    });
  });

  describe('基本渲染', () => {
    it('should render page header with title', () => {
      renderWithProviders(<CostAnalysisPage />);
      expect(
        screen.getByRole('heading', { name: /成本分析/i }),
      ).toBeInTheDocument();
    });

    it('should render page with testid', () => {
      renderWithProviders(<CostAnalysisPage />);
      expect(screen.getByTestId('cost-analysis-page')).toBeInTheDocument();
    });

    it('should render refresh button', () => {
      renderWithProviders(<CostAnalysisPage />);
      expect(
        screen.getByRole('button', { name: /刷新/i }),
      ).toBeInTheDocument();
    });

    it('should render export button', () => {
      renderWithProviders(<CostAnalysisPage />);
      expect(
        screen.getByRole('button', { name: /导出/i }),
      ).toBeInTheDocument();
    });

    it('should render cost summary cards', () => {
      renderWithProviders(<CostAnalysisPage />);
      expect(screen.getByText('总成本')).toBeInTheDocument();
      expect(screen.getByText('计算成本')).toBeInTheDocument();
      expect(screen.getByText('存储成本')).toBeInTheDocument();
      expect(screen.getByText('网络成本')).toBeInTheDocument();
    });
  });

  describe('加载状态', () => {
    it('should display loading state on summary cards', () => {
      mockUseCostAnalysis.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(<CostAnalysisPage />);
      // 概要卡片在加载时显示加载指示
      expect(screen.getAllByText('加载中').length).toBeGreaterThan(0);
    });
  });

  describe('错误处理', () => {
    it('should render InlineErrorState with retry inside page skeleton on failure', async () => {
      const mockRefetch = vi.fn();
      mockUseCostAnalysis.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('服务器内部错误'),
        refetch: mockRefetch,
      });

      renderWithProviders(<CostAnalysisPage />);

      // InlineErrorState 标题
      expect(await screen.findByText('加载失败')).toBeInTheDocument();
      // error.message 作为错误描述渲染
      expect(screen.getByText('服务器内部错误')).toBeInTheDocument();
      // 重试按钮（onRetry → refetch）
      expect(
        screen.getByRole('button', { name: '重试' }),
      ).toBeInTheDocument();
    });
  });

  describe('刷新功能', () => {
    it('should call refetch when clicking refresh button', async () => {
      const mockRefetch = vi.fn();
      mockUseCostAnalysis.mockReturnValue({
        data: mockCostAnalysisData,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });

      renderWithProviders(<CostAnalysisPage />);

      fireEvent.click(screen.getByRole('button', { name: /刷新/i }));

      await waitFor(() => {
        expect(mockRefetch).toHaveBeenCalled();
      });
    });
  });

  describe('导出功能', () => {
    it('should call export mutation when clicking export button', async () => {
      const mockMutate = vi.fn();
      mockUseExportReport.mockReturnValue({
        mutate: mockMutate,
        isPending: false,
      });

      renderWithProviders(<CostAnalysisPage />);

      fireEvent.click(screen.getByRole('button', { name: /导出/i }));

      await waitFor(() => {
        expect(mockMutate).toHaveBeenCalledWith(
          expect.objectContaining({
            report_type: 'cost_analysis',
            format: 'csv',
          }),
        );
      });
    });
  });
});
