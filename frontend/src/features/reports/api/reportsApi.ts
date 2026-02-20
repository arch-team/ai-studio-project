/**
 * Reports API client functions.
 *
 * Task: T075 - 成本分析仪表盘前端页面
 * 调用后端报表 API 端点
 */

import { apiClient } from '@shared/api';
import type {
  CostAnalysisResponse,
  CostAnalysisFilters,
  ResourceUsageResponse,
  ResourceUsageFilters,
  ReportExportFilters,
} from '../types';

/**
 * 获取成本分析报表
 */
export async function fetchCostAnalysis(
  filters: CostAnalysisFilters = {}
): Promise<CostAnalysisResponse> {
  return apiClient.get<CostAnalysisResponse>('/reports/cost-analysis', {
    params: {
      start_date: filters.start_date,
      end_date: filters.end_date,
      group_by: filters.group_by,
      user_id: filters.user_id,
      project_id: filters.project_id,
    },
  });
}

/**
 * 获取资源使用报表
 */
export async function fetchResourceUsage(
  filters: ResourceUsageFilters = {}
): Promise<ResourceUsageResponse> {
  return apiClient.get<ResourceUsageResponse>('/reports/resource-usage', {
    params: {
      start_date: filters.start_date,
      end_date: filters.end_date,
      group_by: filters.group_by,
      user_id: filters.user_id,
      resource_type: filters.resource_type,
    },
  });
}

/**
 * 导出报表 (CSV 或 JSON)
 */
export async function exportReport(
  filters: ReportExportFilters
): Promise<Blob> {
  return apiClient.download('/reports/export', {
    params: {
      report_type: filters.report_type,
      format: filters.format,
      start_date: filters.start_date,
      end_date: filters.end_date,
      group_by: filters.group_by,
    },
  });
}
