/**
 * Resource Limit Config Hooks
 */

import { useQuery } from '@tanstack/react-query';
import { queryKeys } from '@lib/query';
import { fetchResourceLimitConfigs } from './api';
import type { ResourceLimitConfigFilters } from './types';

export function useResourceLimitConfigs(filters: ResourceLimitConfigFilters = {}) {
  return useQuery({
    queryKey: queryKeys.resourceQuotas.list(filters as Record<string, unknown>),
    queryFn: () => fetchResourceLimitConfigs(filters),
  });
}
