/**
 * TanStack Query hooks for Audit Logs.
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import { queryKeys } from '@lib/query';
import type { AuditLogFilters } from '../types';
import {
  fetchAuditLogs,
  fetchAuditLog,
  fetchResourceAuditLogs,
  fetchUserAuditLogs,
  exportAuditLogs,
} from './auditApi';

// === Query Hooks ===

/**
 * Fetch paginated list of audit logs.
 */
export function useAuditLogs(filters: AuditLogFilters = {}) {
  return useQuery({
    queryKey: queryKeys.audit.list(filters as Record<string, unknown>),
    queryFn: () => fetchAuditLogs(filters),
  });
}

/**
 * Fetch a single audit log by ID.
 */
export function useAuditLog(id: number | undefined) {
  return useQuery({
    queryKey: queryKeys.audit.detail(String(id!)),
    queryFn: () => fetchAuditLog(id!),
    enabled: id !== undefined,
  });
}

/**
 * Fetch audit logs for a specific resource.
 */
export function useResourceAuditLogs(
  resourceType: string | undefined,
  resourceId: string | undefined,
  filters: Omit<AuditLogFilters, 'resource_type' | 'resource_id'> = {}
) {
  return useQuery({
    queryKey: queryKeys.audit.list({
      ...filters,
      resource_type: resourceType,
      resource_id: resourceId,
    } as Record<string, unknown>),
    queryFn: () => fetchResourceAuditLogs(resourceType!, resourceId!, filters),
    enabled: resourceType !== undefined && resourceId !== undefined,
  });
}

/**
 * Fetch audit logs for a specific user.
 */
export function useUserAuditLogs(
  userId: number | undefined,
  filters: Omit<AuditLogFilters, 'user_id'> = {}
) {
  return useQuery({
    queryKey: queryKeys.audit.list({
      ...filters,
      user_id: userId,
    } as Record<string, unknown>),
    queryFn: () => fetchUserAuditLogs(userId!, filters),
    enabled: userId !== undefined,
  });
}

// === Mutation Hooks ===

/**
 * Export audit logs as CSV.
 */
export function useExportAuditLogs() {
  return useMutation({
    mutationFn: (filters: AuditLogFilters) => exportAuditLogs(filters),
    onSuccess: (blob) => {
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });
}
