/**
 * Reports API client functions.
 *
 * Task: T075 - 成本分析仪表盘前端页面
 * 调用后端报表 API 端点
 */

import type {
  CostAnalysisResponse,
  CostAnalysisFilters,
  ResourceUsageResponse,
  ResourceUsageFilters,
  ReportExportFilters,
} from '../types';

const API_BASE = '/api/v1';

/**
 * 构建查询参数字符串
 */
function buildQueryString(
  params: Record<string, string | number | boolean | undefined>
): string {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value));
    }
  });
  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
}

/**
 * 获取成本分析报表
 */
export async function fetchCostAnalysis(
  filters: CostAnalysisFilters = {}
): Promise<CostAnalysisResponse> {
  const queryString = buildQueryString({
    start_date: filters.start_date,
    end_date: filters.end_date,
    group_by: filters.group_by,
    user_id: filters.user_id,
    project_id: filters.project_id,
  });

  const response = await fetch(`${API_BASE}/reports/cost-analysis${queryString}`);
  if (!response.ok) {
    throw new Error(`获取成本分析报表失败: ${response.statusText}`);
  }
  return response.json();
}

/**
 * 获取资源使用报表
 */
export async function fetchResourceUsage(
  filters: ResourceUsageFilters = {}
): Promise<ResourceUsageResponse> {
  const queryString = buildQueryString({
    start_date: filters.start_date,
    end_date: filters.end_date,
    group_by: filters.group_by,
    user_id: filters.user_id,
    resource_type: filters.resource_type,
  });

  const response = await fetch(`${API_BASE}/reports/resource-usage${queryString}`);
  if (!response.ok) {
    throw new Error(`获取资源使用报表失败: ${response.statusText}`);
  }
  return response.json();
}

/**
 * 导出报表 (CSV 或 JSON)
 */
export async function exportReport(
  filters: ReportExportFilters
): Promise<Blob> {
  const queryString = buildQueryString({
    report_type: filters.report_type,
    format: filters.format,
    start_date: filters.start_date,
    end_date: filters.end_date,
    group_by: filters.group_by,
  });

  const response = await fetch(`${API_BASE}/reports/export${queryString}`);
  if (!response.ok) {
    throw new Error(`导出报表失败: ${response.statusText}`);
  }
  return response.blob();
}
