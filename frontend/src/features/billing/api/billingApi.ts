/**
 * Billing API client functions.
 */

import { apiClient } from '@shared/api/client';
import type {
  CostReportResponse,
  CostFilters,
  UserCostListResponse,
  ResourceCostListResponse,
  ResourceCostFilters,
} from '../types';

/**
 * Fetch cost report with summary and breakdown.
 */
export async function fetchCostReport(
  filters: CostFilters = {}
): Promise<CostReportResponse> {
  return apiClient.get<CostReportResponse>('/billing/report', {
    params: {
      period: filters.period,
      start_date: filters.start_date,
      end_date: filters.end_date,
      user_id: filters.user_id,
      resource_type: filters.resource_type,
      category: filters.category,
    },
  });
}

/**
 * Fetch cost summary by user.
 */
export async function fetchUserCosts(
  filters: CostFilters = {}
): Promise<UserCostListResponse> {
  return apiClient.get<UserCostListResponse>('/billing/users', {
    params: {
      start_date: filters.start_date,
      end_date: filters.end_date,
    },
  });
}

/**
 * Fetch cost for a specific user.
 */
export async function fetchUserCostDetail(
  userId: number,
  filters: CostFilters = {}
): Promise<CostReportResponse> {
  return apiClient.get<CostReportResponse>(`/billing/users/${userId}`, {
    params: {
      period: filters.period,
      start_date: filters.start_date,
      end_date: filters.end_date,
    },
  });
}

/**
 * Fetch resource-level cost details.
 */
export async function fetchResourceCosts(
  filters: ResourceCostFilters = {}
): Promise<ResourceCostListResponse> {
  return apiClient.get<ResourceCostListResponse>('/billing/resources', {
    params: {
      resource_type: filters.resource_type,
      user_id: filters.user_id,
      start_date: filters.start_date,
      end_date: filters.end_date,
      min_cost: filters.min_cost,
      page: filters.page,
      page_size: filters.page_size,
      sort_by: filters.sort_by,
      sort_order: filters.sort_order,
    },
  });
}

/**
 * Export billing report as CSV.
 */
export async function exportBillingReport(
  filters: CostFilters = {}
): Promise<Blob> {
  return apiClient.download('/billing/export', {
    params: {
      period: filters.period,
      start_date: filters.start_date,
      end_date: filters.end_date,
      user_id: filters.user_id,
    },
  });
}
