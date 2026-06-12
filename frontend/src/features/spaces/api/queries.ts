/**
 * TanStack Query hooks for Spaces.
 *
 * Space ID 为 UUID 字符串（契约对齐后端）。
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@lib/query';
import type {
  SpaceFilters,
  CreateSpaceRequest,
  UpdateSpaceRequest,
} from '../types';
import {
  fetchSpaces,
  fetchSpace,
  createSpace,
  updateSpace,
  deleteSpace,
  startSpace,
  stopSpace,
} from './spaceApi';

// === Query Hooks ===

/**
 * Fetch paginated list of spaces.
 */
export function useSpaces(filters: SpaceFilters = {}) {
  return useQuery({
    queryKey: queryKeys.spaces.list(filters as Record<string, unknown>),
    queryFn: () => fetchSpaces(filters),
    // 启动/创建后 App 拉起需 1-3 分钟，存在启动中条目时轮询推进状态
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? [];
      return items.some((s) => s.status === 'pending') ? 10_000 : false;
    },
  });
}

/**
 * Fetch a single space by ID.
 */
export function useSpace(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.spaces.detail(id!),
    queryFn: () => fetchSpace(id!),
    enabled: id !== undefined,
  });
}

// === Mutation Hooks ===

/**
 * Create a new space.
 */
export function useCreateSpace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateSpaceRequest) => createSpace(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.spaces.lists() });
    },
  });
}

/**
 * Update an existing space.
 */
export function useUpdateSpace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateSpaceRequest }) =>
      updateSpace(id, data),
    onSuccess: (result) => {
      queryClient.setQueryData(queryKeys.spaces.detail(result.id), result);
      queryClient.invalidateQueries({ queryKey: queryKeys.spaces.lists() });
    },
  });
}

/**
 * Delete a space.
 */
export function useDeleteSpace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteSpace(id),
    onSuccess: (_result, id) => {
      queryClient.removeQueries({ queryKey: queryKeys.spaces.detail(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.spaces.lists() });
    },
  });
}

/**
 * Start a stopped space.
 */
export function useStartSpace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => startSpace(id),
    onSuccess: (result) => {
      queryClient.setQueryData(queryKeys.spaces.detail(result.id), result);
      queryClient.invalidateQueries({ queryKey: queryKeys.spaces.lists() });
    },
  });
}

/**
 * Stop a running space.
 */
export function useStopSpace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => stopSpace(id),
    onSuccess: (result) => {
      queryClient.setQueryData(queryKeys.spaces.detail(result.id), result);
      queryClient.invalidateQueries({ queryKey: queryKeys.spaces.lists() });
    },
  });
}
