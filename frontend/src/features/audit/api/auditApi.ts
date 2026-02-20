/**
 * Audit API client functions.
 *
 * 审计日志 API - 只读查询接口
 */

import { apiClient } from '@shared/api';
import type { AuditLogListResponse, AuditLogFilters, AuditLog } from '../types';

/**
 * Fetch paginated list of audit logs.
 */
export async function fetchAuditLogs(
  filters: AuditLogFilters = {}
): Promise<AuditLogListResponse> {
  return apiClient.get<AuditLogListResponse>('/audit-logs', {
    params: {
      user_id: filters.user_id,
      username: filters.username,
      action: filters.action,
      resource_type: filters.resource_type,
      resource_id: filters.resource_id,
      result: filters.result,
      start_date: filters.start_date,
      end_date: filters.end_date,
      page: filters.page,
      page_size: filters.page_size,
      sort_order: filters.sort_order,
    },
  });
}

/**
 * Fetch a single audit log by ID.
 */
export async function fetchAuditLog(id: number): Promise<AuditLog> {
  return apiClient.get<AuditLog>(`/audit-logs/${id}`);
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
  return apiClient.download('/audit-logs/export', {
    params: {
      user_id: filters.user_id,
      action: filters.action,
      resource_type: filters.resource_type,
      result: filters.result,
      start_date: filters.start_date,
      end_date: filters.end_date,
    },
  });
}
