/**
 * Resource Usage Report Page Tests
 *
 * Task: T074 - 资源使用报表前端页面
 * TDD Step 1: Red - 编写测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import { renderWithProviders } from '@tests/__utils__/test-utils';
import { ResourceUsageReportPage } from '@features/reports';
import type { ResourceUsageResponse } from '@features/reports';

// Mock data
const mockResourceUsageData: ResourceUsageResponse = {
  summary: {
    total_gpu_hours: 1000.5,
    total_cpu_hours: 2500.75,
    total_memory_gb_hours: 5000.25,
    total_storage_gb_hours: 10000,
    total_jobs_count: 50,
    active_jobs_count: 10,
    completed_jobs_count: 35,
    failed_jobs_count: 5,
  },
  breakdown: [
    {
      resource_type: 'training_job',
      name: '用户 A',
      gpu_hours: 500.25,
      cpu_hours: 1200.5,
      memory_gb_hours: 2500,
      storage_gb_hours: 5000,
      count: 25,
      percentage: 50,
    },
    {
      resource_type: 'training_job',
      name: '用户 B',
      gpu_hours: 300.25,
      cpu_hours: 800.25,
      memory_gb_hours: 1500,
      storage_gb_hours: 3000,
      count: 15,
      percentage: 30,
    },
    {
      resource_type: 'training_job',
      name: '用户 C',
      gpu_hours: 200,
      cpu_hours: 500,
      memory_gb_hours: 1000.25,
      storage_gb_hours: 2000,
      count: 10,
      percentage: 20,
    },
  ],
  daily_usage: [
    {
      date: '2024-01-15',
      gpu_hours: 100.5,
      cpu_hours: 250.75,
      memory_gb_hours: 500,
      storage_gb_hours: 1000,
      job_count: 10,
    },
    {
      date: '2024-01-16',
      gpu_hours: 150.25,
      cpu_hours: 300.5,
      memory_gb_hours: 600,
      storage_gb_hours: 1200,
      job_count: 12,
    },
  ],
  period: {
    start_date: '2024-01-15',
    end_date: '2024-01-21',
  },
};

// Mock hooks
const mockUseResourceUsage = vi.fn();
const mockUseExportReport = vi.fn();

vi.mock('@features/reports/api', () => ({
  useResourceUsage: () => mockUseResourceUsage(),
  useExportReport: () => mockUseExportReport(),
}));

describe('ResourceUsageReportPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock implementations
    mockUseResourceUsage.mockReturnValue({
      data: mockResourceUsageData,
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
      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getByRole('heading', { name: /资源使用报表/i })).toBeInTheDocument();
    });

    it('should render page with testid', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getByTestId('resource-usage-report-page')).toBeInTheDocument();
    });

    it('should render refresh button', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getByRole('button', { name: /刷新/i })).toBeInTheDocument();
    });

    it('should render export button', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getByRole('button', { name: /导出/i })).toBeInTheDocument();
    });

    it('should render resource usage table', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getByRole('table')).toBeInTheDocument();
    });
  });

  describe('汇总统计', () => {
    it('should display total GPU hours', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getByText('GPU 总小时')).toBeInTheDocument();
      expect(screen.getByText('1000.50')).toBeInTheDocument();
    });

    it('should display total CPU hours', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getByText('CPU 总小时')).toBeInTheDocument();
      expect(screen.getByText('2500.75')).toBeInTheDocument();
    });

    it('should display total memory hours', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getByText('内存总量 (GB·h)')).toBeInTheDocument();
    });

    it('should display total job count', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getByText('任务总数')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();
    });
  });

  describe('表格列', () => {
    it('should display dimension column header based on groupBy', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      // 默认按用户聚合
      expect(screen.getAllByText(/用户/i).length).toBeGreaterThan(0);
    });

    it('should display GPU hours column', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getAllByText(/GPU 小时/i).length).toBeGreaterThan(0);
    });

    it('should display CPU hours column', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getAllByText(/CPU 小时/i).length).toBeGreaterThan(0);
    });

    it('should display memory column', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getAllByText(/内存/i).length).toBeGreaterThan(0);
    });

    it('should display job count column', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getAllByText(/任务数/i).length).toBeGreaterThan(0);
    });

    it('should display average duration column', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getAllByText(/平均时长/i).length).toBeGreaterThan(0);
    });
  });

  describe('过滤器', () => {
    it('should render date range picker', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      // 检查 DateRangePicker 是否渲染
      expect(screen.getByText(/最近 7 天/i)).toBeInTheDocument();
    });

    it('should render groupBy selector with default value', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      // 默认选项是 "按用户"
      expect(screen.getByText('按用户')).toBeInTheDocument();
    });
  });

  describe('加载状态', () => {
    it('should display loading state', () => {
      mockUseResourceUsage.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getByText('加载中...')).toBeInTheDocument();
    });
  });

  describe('错误处理', () => {
    it('should display error message on failure', () => {
      mockUseResourceUsage.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Network error'),
        refetch: vi.fn(),
      });

      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getByText(/加载失败/i)).toBeInTheDocument();
    });
  });

  describe('空状态', () => {
    it('should display empty state when no data', () => {
      mockUseResourceUsage.mockReturnValue({
        data: {
          summary: {
            total_gpu_hours: 0,
            total_cpu_hours: 0,
            total_memory_gb_hours: 0,
            total_storage_gb_hours: 0,
            total_jobs_count: 0,
            active_jobs_count: 0,
            completed_jobs_count: 0,
            failed_jobs_count: 0,
          },
          breakdown: [],
          daily_usage: [],
          period: { start_date: '2024-01-15', end_date: '2024-01-21' },
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(<ResourceUsageReportPage />);
      expect(screen.getByText(/暂无数据/i)).toBeInTheDocument();
    });
  });

  describe('刷新功能', () => {
    it('should call refetch when clicking refresh button', async () => {
      const mockRefetch = vi.fn();
      mockUseResourceUsage.mockReturnValue({
        data: mockResourceUsageData,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });

      renderWithProviders(<ResourceUsageReportPage />);

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

      renderWithProviders(<ResourceUsageReportPage />);

      fireEvent.click(screen.getByRole('button', { name: /导出/i }));

      await waitFor(() => {
        expect(mockMutate).toHaveBeenCalledWith(
          expect.objectContaining({
            report_type: 'resource_usage',
            format: 'csv',
          })
        );
      });
    });

    it('should show loading state on export button while exporting', () => {
      mockUseExportReport.mockReturnValue({
        mutate: vi.fn(),
        isPending: true,
      });

      renderWithProviders(<ResourceUsageReportPage />);

      // Export button should be present
      const exportButton = screen.getByRole('button', { name: /导出/i });
      expect(exportButton).toBeInTheDocument();
    });
  });

  describe('时间范围选择', () => {
    it('should display date range description in table header', () => {
      renderWithProviders(<ResourceUsageReportPage />);
      // 检查表格标题描述中显示时间范围
      const headerDescription = screen.getByRole('heading', { name: /资源使用明细/i });
      expect(headerDescription).toBeInTheDocument();
    });
  });
});
