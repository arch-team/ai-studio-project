/**
 * Resource Limit Config TanStack Query Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@lib/query';
import {
  fetchResourceLimitConfigs,
  createResourceLimitConfig,
  updateResourceLimitConfig,
  deleteResourceLimitConfig,
} from './resourceQuotasApi';
import type {
  ResourceLimitConfigFilters,
  CreateResourceLimitConfigRequest,
  UpdateResourceLimitConfigRequest,
} from '../types';

/**
 * 获取资源限制配置列表
 */
export function useResourceLimitConfigs(filters: ResourceLimitConfigFilters = {}) {
  return useQuery({
    queryKey: queryKeys.resourceQuotas.list(filters as Record<string, unknown>),
    queryFn: () => fetchResourceLimitConfigs(filters),
  });
}

/**
 * 创建资源限制配置
 */
export function useCreateResourceLimitConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateResourceLimitConfigRequest) =>
      createResourceLimitConfig(data),
    onSuccess: () => {
      // 创建成功后刷新列表
      queryClient.invalidateQueries({
        queryKey: queryKeys.resourceQuotas.lists(),
      });
    },
  });
}

/**
 * 更新资源限制配置
 */
export function useUpdateResourceLimitConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateResourceLimitConfigRequest }) =>
      updateResourceLimitConfig(id, data),
    onSuccess: () => {
      // 更新成功后刷新列表
      queryClient.invalidateQueries({
        queryKey: queryKeys.resourceQuotas.lists(),
      });
    },
  });
}

/**
 * 删除资源限制配置
 */
export function useDeleteResourceLimitConfig() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deleteResourceLimitConfig(id),
    onSuccess: () => {
      // 删除成功后刷新列表
      queryClient.invalidateQueries({
        queryKey: queryKeys.resourceQuotas.lists(),
      });
    },
  });
}
