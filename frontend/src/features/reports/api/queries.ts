/**
 * TanStack Query hooks for Reports.
 *
 * Task: T075 - 成本分析仪表盘前端页面
 * 提供成本分析和资源使用报表的数据获取 hooks
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import type { CostAnalysisFilters, ResourceUsageFilters, ReportExportFilters } from '../types';
import {
  fetchCostAnalysis,
  fetchResourceUsage,
  exportReport,
} from './reportsApi';

// === Query Keys ===

export const reportQueryKeys = {
  all: ['reports'] as const,
  costAnalysis: (filters: Record<string, unknown>) =>
    [...reportQueryKeys.all, 'costAnalysis', filters] as const,
  resourceUsage: (filters: Record<string, unknown>) =>
    [...reportQueryKeys.all, 'resourceUsage', filters] as const,
} as const;

// === Query Hooks ===

/**
 * 获取成本分析报表
 */
export function useCostAnalysis(filters: CostAnalysisFilters = {}) {
  return useQuery({
    queryKey: reportQueryKeys.costAnalysis(filters as Record<string, unknown>),
    queryFn: () => fetchCostAnalysis(filters),
    // 每 5 分钟刷新一次
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * 获取资源使用报表
 */
export function useResourceUsage(filters: ResourceUsageFilters = {}) {
  return useQuery({
    queryKey: reportQueryKeys.resourceUsage(filters as Record<string, unknown>),
    queryFn: () => fetchResourceUsage(filters),
    staleTime: 5 * 60 * 1000,
  });
}

// === Mutation Hooks ===

/**
 * 导出报表
 */
export function useExportReport() {
  return useMutation({
    mutationFn: (filters: ReportExportFilters) => exportReport(filters),
    onSuccess: (blob, filters) => {
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;

      // 生成文件名
      const dateStr = new Date().toISOString().split('T')[0];
      const extension = filters.format === 'csv' ? 'csv' : 'json';
      const reportType = filters.report_type === 'cost_analysis' ? 'cost-analysis' : 'resource-usage';
      a.download = `${reportType}-${dateStr}.${extension}`;

      // 触发下载
      document.body.appendChild(a);
      a.click();

      // 清理
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });
}
