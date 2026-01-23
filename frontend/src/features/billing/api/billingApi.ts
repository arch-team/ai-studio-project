/**
 * Billing API client functions.
 */

import type {
  CostReportResponse,
  CostFilters,
  UserCostListResponse,
  ResourceCostListResponse,
  ResourceCostFilters,
} from '../types';

const API_BASE = '/api/v1';

/**
 * Fetch cost report with summary and breakdown.
 */
export async function fetchCostReport(
  filters: CostFilters = {}
): Promise<CostReportResponse> {
  const params = new URLSearchParams();

  if (filters.period) params.append('period', filters.period);
  if (filters.start_date) params.append('start_date', filters.start_date);
  if (filters.end_date) params.append('end_date', filters.end_date);
  if (filters.user_id) params.append('user_id', String(filters.user_id));
  if (filters.resource_type) params.append('resource_type', filters.resource_type);
  if (filters.category) params.append('category', filters.category);

  const response = await fetch(`${API_BASE}/billing/report?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch cost report: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch cost summary by user.
 */
export async function fetchUserCosts(
  filters: CostFilters = {}
): Promise<UserCostListResponse> {
  const params = new URLSearchParams();

  if (filters.start_date) params.append('start_date', filters.start_date);
  if (filters.end_date) params.append('end_date', filters.end_date);

  const response = await fetch(`${API_BASE}/billing/users?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch user costs: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch cost for a specific user.
 */
export async function fetchUserCostDetail(
  userId: number,
  filters: CostFilters = {}
): Promise<CostReportResponse> {
  const params = new URLSearchParams();

  if (filters.period) params.append('period', filters.period);
  if (filters.start_date) params.append('start_date', filters.start_date);
  if (filters.end_date) params.append('end_date', filters.end_date);

  const response = await fetch(
    `${API_BASE}/billing/users/${userId}?${params.toString()}`
  );
  if (!response.ok) {
    throw new Error(`Failed to fetch user cost detail: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch resource-level cost details.
 */
export async function fetchResourceCosts(
  filters: ResourceCostFilters = {}
): Promise<ResourceCostListResponse> {
  const params = new URLSearchParams();

  if (filters.resource_type) params.append('resource_type', filters.resource_type);
  if (filters.user_id) params.append('user_id', String(filters.user_id));
  if (filters.start_date) params.append('start_date', filters.start_date);
  if (filters.end_date) params.append('end_date', filters.end_date);
  if (filters.min_cost) params.append('min_cost', String(filters.min_cost));
  if (filters.page) params.append('page', String(filters.page));
  if (filters.page_size) params.append('page_size', String(filters.page_size));
  if (filters.sort_by) params.append('sort_by', filters.sort_by);
  if (filters.sort_order) params.append('sort_order', filters.sort_order);

  const response = await fetch(`${API_BASE}/billing/resources?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch resource costs: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Export billing report as CSV.
 */
export async function exportBillingReport(
  filters: CostFilters = {}
): Promise<Blob> {
  const params = new URLSearchParams();

  if (filters.period) params.append('period', filters.period);
  if (filters.start_date) params.append('start_date', filters.start_date);
  if (filters.end_date) params.append('end_date', filters.end_date);
  if (filters.user_id) params.append('user_id', String(filters.user_id));

  const response = await fetch(`${API_BASE}/billing/export?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Failed to export billing report: ${response.statusText}`);
  }
  return response.blob();
}
