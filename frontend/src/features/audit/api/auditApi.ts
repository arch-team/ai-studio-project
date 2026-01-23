/**
 * Audit API client functions.
 *
 * 审计日志 API - 只读查询接口
 */

import type { AuditLogListResponse, AuditLogFilters, AuditLog } from '../types';

const API_BASE = '/api/v1';

/**
 * Fetch paginated list of audit logs.
 */
export async function fetchAuditLogs(
  filters: AuditLogFilters = {}
): Promise<AuditLogListResponse> {
  const params = new URLSearchParams();

  if (filters.user_id) params.append('user_id', String(filters.user_id));
  if (filters.username) params.append('username', filters.username);
  if (filters.action) params.append('action', filters.action);
  if (filters.resource_type) params.append('resource_type', filters.resource_type);
  if (filters.resource_id) params.append('resource_id', filters.resource_id);
  if (filters.result) params.append('result', filters.result);
  if (filters.start_date) params.append('start_date', filters.start_date);
  if (filters.end_date) params.append('end_date', filters.end_date);
  if (filters.page) params.append('page', String(filters.page));
  if (filters.page_size) params.append('page_size', String(filters.page_size));
  if (filters.sort_order) params.append('sort_order', filters.sort_order);

  const response = await fetch(`${API_BASE}/audit-logs?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch audit logs: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch a single audit log by ID.
 */
export async function fetchAuditLog(id: number): Promise<AuditLog> {
  const response = await fetch(`${API_BASE}/audit-logs/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch audit log: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch audit logs for a specific resource.
 */
export async function fetchResourceAuditLogs(
  resourceType: string,
  resourceId: string,
  filters: Omit<AuditLogFilters, 'resource_type' | 'resource_id'> = {}
): Promise<AuditLogListResponse> {
  return fetchAuditLogs({
    ...filters,
    resource_type: resourceType as AuditLogFilters['resource_type'],
    resource_id: resourceId,
  });
}

/**
 * Fetch audit logs for a specific user.
 */
export async function fetchUserAuditLogs(
  userId: number,
  filters: Omit<AuditLogFilters, 'user_id'> = {}
): Promise<AuditLogListResponse> {
  return fetchAuditLogs({
    ...filters,
    user_id: userId,
  });
}

/**
 * Export audit logs as CSV.
 */
export async function exportAuditLogs(
  filters: AuditLogFilters = {}
): Promise<Blob> {
  const params = new URLSearchParams();

  if (filters.user_id) params.append('user_id', String(filters.user_id));
  if (filters.action) params.append('action', filters.action);
  if (filters.resource_type) params.append('resource_type', filters.resource_type);
  if (filters.result) params.append('result', filters.result);
  if (filters.start_date) params.append('start_date', filters.start_date);
  if (filters.end_date) params.append('end_date', filters.end_date);

  const response = await fetch(`${API_BASE}/audit-logs/export?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Failed to export audit logs: ${response.statusText}`);
  }
  return response.blob();
}
