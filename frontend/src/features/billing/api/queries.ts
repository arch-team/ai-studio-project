/**
 * TanStack Query hooks for Billing.
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import { queryKeys } from '@lib/query';
import type { CostFilters, ResourceCostFilters } from '../types';
import {
  fetchCostReport,
  fetchUserCosts,
  fetchUserCostDetail,
  fetchResourceCosts,
  exportBillingReport,
} from './billingApi';

// === Query Hooks ===

/**
 * Fetch cost report with summary and breakdown.
 */
export function useCostReport(filters: CostFilters = {}) {
  return useQuery({
    queryKey: queryKeys.billing.report(filters as Record<string, unknown>),
    queryFn: () => fetchCostReport(filters),
  });
}

/**
 * Fetch cost summary by user.
 */
export function useUserCosts(filters: CostFilters = {}) {
  return useQuery({
    queryKey: queryKeys.billing.users(filters as Record<string, unknown>),
    queryFn: () => fetchUserCosts(filters),
  });
}

/**
 * Fetch cost for a specific user.
 */
export function useUserCostDetail(userId: number | undefined, filters: CostFilters = {}) {
  return useQuery({
    queryKey: queryKeys.billing.userDetail(String(userId!), filters as Record<string, unknown>),
    queryFn: () => fetchUserCostDetail(userId!, filters),
    enabled: userId !== undefined,
  });
}

/**
 * Fetch resource-level cost details.
 */
export function useResourceCosts(filters: ResourceCostFilters = {}) {
  return useQuery({
    queryKey: queryKeys.billing.resources(filters as Record<string, unknown>),
    queryFn: () => fetchResourceCosts(filters),
  });
}

// === Mutation Hooks ===

/**
 * Export billing report as CSV.
 */
export function useExportBillingReport() {
  return useMutation({
    mutationFn: (filters: CostFilters) => exportBillingReport(filters),
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `billing-report-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  });
}
