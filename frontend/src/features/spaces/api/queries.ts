/**
 * TanStack Query hooks for Spaces.
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
  openSpace,
} from './spaceApi';

// === Query Hooks ===

/**
 * Fetch paginated list of spaces.
 */
export function useSpaces(filters: SpaceFilters = {}) {
  return useQuery({
    queryKey: queryKeys.spaces.list(filters as Record<string, unknown>),
    queryFn: () => fetchSpaces(filters),
  });
}

/**
 * Fetch a single space by ID.
 */
export function useSpace(id: number | undefined) {
  return useQuery({
    queryKey: queryKeys.spaces.detail(String(id!)),
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
    mutationFn: ({ id, data }: { id: number; data: UpdateSpaceRequest }) =>
      updateSpace(id, data),
    onSuccess: (result) => {
      queryClient.setQueryData(queryKeys.spaces.detail(String(result.id)), result);
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
    mutationFn: (id: number) => deleteSpace(id),
    onSuccess: (_result, id) => {
      queryClient.removeQueries({ queryKey: queryKeys.spaces.detail(String(id)) });
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
    mutationFn: (id: number) => startSpace(id),
    onSuccess: (result) => {
      queryClient.setQueryData(queryKeys.spaces.detail(String(result.id)), result);
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
    mutationFn: (id: number) => stopSpace(id),
    onSuccess: (result) => {
      queryClient.setQueryData(queryKeys.spaces.detail(String(result.id)), result);
      queryClient.invalidateQueries({ queryKey: queryKeys.spaces.lists() });
    },
  });
}

/**
 * Open space URL.
 */
export function useOpenSpace() {
  return useMutation({
    mutationFn: (id: number) => openSpace(id),
    onSuccess: (result) => {
      // 在新窗口打开空间
      window.open(result.url, '_blank');
    },
  });
}
