/**
 * 通用实体 CRUD Hooks
 *
 * 提供基础的实体操作 hooks，减少重复代码。
 */

import { useCallback, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import type { AppError } from '../types/errors';

// === 类型定义 ===

export interface EntityOperations<T, CreateDTO, UpdateDTO> {
  create: (data: CreateDTO) => Promise<T>;
  update: (id: string | number, data: UpdateDTO) => Promise<T>;
  delete: (id: string | number) => Promise<void>;
}

export interface UseEntityMutationsOptions<T> {
  queryKey: readonly unknown[];
  onCreateSuccess?: (entity: T) => void;
  onUpdateSuccess?: (entity: T) => void;
  onDeleteSuccess?: (id: string | number) => void;
  onError?: (error: AppError) => void;
}

// === Hooks ===

/**
 * 通用实体 CRUD 操作 Hooks
 *
 * @example
 * ```tsx
 * const { createMutation, updateMutation, deleteMutation } = useEntityMutations({
 *   queryKey: queryKeys.trainingJobs.all,
 *   create: (data) => trainingJobApi.create(data),
 *   update: (id, data) => trainingJobApi.update(id, data),
 *   delete: (id) => trainingJobApi.delete(id),
 *   onCreateSuccess: (job) => navigate(`/training-jobs/${job.id}`),
 * });
 * ```
 */
export function useEntityMutations<T, CreateDTO, UpdateDTO>(
  operations: EntityOperations<T, CreateDTO, UpdateDTO>,
  options: UseEntityMutationsOptions<T>
) {
  const queryClient = useQueryClient();
  const { queryKey, onCreateSuccess, onUpdateSuccess, onDeleteSuccess, onError } =
    options;

  const createMutation = useMutation({
    mutationFn: operations.create,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey });
      onCreateSuccess?.(data);
    },
    onError: onError as (error: Error) => void,
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string | number; data: UpdateDTO }) =>
      operations.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey });
      onUpdateSuccess?.(data);
    },
    onError: onError as (error: Error) => void,
  });

  const deleteMutation = useMutation({
    mutationFn: operations.delete,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey });
      onDeleteSuccess?.(id);
    },
    onError: onError as (error: Error) => void,
  });

  return {
    createMutation,
    updateMutation,
    deleteMutation,
  };
}

/**
 * 乐观更新 Hook
 *
 * 在等待服务器响应时立即更新 UI，失败时自动回滚。
 *
 * @example
 * ```tsx
 * const { mutate, isOptimisticUpdating } = useOptimisticUpdate({
 *   queryKey: queryKeys.trainingJobs.detail(jobId),
 *   updateFn: (current, variables) => ({ ...current, status: variables.status }),
 *   mutationFn: (variables) => updateTrainingJob(jobId, variables),
 * });
 * ```
 */
export function useOptimisticUpdate<TData, TVariables>({
  queryKey,
  updateFn,
  mutationFn,
  onSuccess,
  onError,
}: {
  queryKey: readonly unknown[];
  updateFn: (current: TData, variables: TVariables) => TData;
  mutationFn: (variables: TVariables) => Promise<TData>;
  onSuccess?: (data: TData, variables: TVariables) => void;
  onError?: (error: Error, variables: TVariables, rollback: () => void) => void;
}) {
  const queryClient = useQueryClient();
  const [isOptimisticUpdating, setIsOptimisticUpdating] = useState(false);

  const mutation = useMutation({
    mutationFn,
    onMutate: async (variables) => {
      setIsOptimisticUpdating(true);

      // 取消正在进行的查询
      await queryClient.cancelQueries({ queryKey });

      // 保存当前数据用于回滚
      const previousData = queryClient.getQueryData<TData>(queryKey);

      // 乐观更新
      if (previousData) {
        queryClient.setQueryData<TData>(queryKey, updateFn(previousData, variables));
      }

      return { previousData };
    },
    onSuccess: (data, variables) => {
      setIsOptimisticUpdating(false);
      // 用服务器返回的数据更新缓存
      queryClient.setQueryData(queryKey, data);
      onSuccess?.(data, variables);
    },
    onError: (error, variables, context) => {
      setIsOptimisticUpdating(false);

      // 回滚到之前的数据
      const rollback = () => {
        if (context?.previousData) {
          queryClient.setQueryData(queryKey, context.previousData);
        }
      };

      rollback();
      onError?.(error as Error, variables, rollback);
    },
    onSettled: () => {
      setIsOptimisticUpdating(false);
    },
  });

  return {
    mutate: mutation.mutate,
    mutateAsync: mutation.mutateAsync,
    isOptimisticUpdating,
    isPending: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error,
  };
}

/**
 * 批量操作 Hook
 *
 * 支持批量选择和批量操作。
 *
 * @example
 * ```tsx
 * const { selectedIds, toggleSelect, selectAll, clearSelection, batchDelete } =
 *   useBatchOperations({
 *     items: jobs,
 *     getItemId: (job) => job.id,
 *     onBatchDelete: (ids) => deleteTrainingJobs(ids),
 *   });
 * ```
 */
export function useBatchOperations<T>({
  items,
  getItemId,
  onBatchDelete,
  onBatchUpdate,
}: {
  items: T[] | undefined;
  getItemId: (item: T) => string | number;
  onBatchDelete?: (ids: (string | number)[]) => Promise<void>;
  onBatchUpdate?: (ids: (string | number)[], data: Partial<T>) => Promise<void>;
}) {
  const [selectedIds, setSelectedIds] = useState<Set<string | number>>(new Set());

  const toggleSelect = useCallback((id: string | number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const selectAll = useCallback(() => {
    if (!items) return;
    setSelectedIds(new Set(items.map(getItemId)));
  }, [items, getItemId]);

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  const isSelected = useCallback(
    (id: string | number) => selectedIds.has(id),
    [selectedIds]
  );

  const isAllSelected =
    items && items.length > 0 && selectedIds.size === items.length;
  const isSomeSelected = selectedIds.size > 0;

  const batchDeleteMutation = useMutation({
    mutationFn: async () => {
      if (!onBatchDelete) throw new Error('onBatchDelete not provided');
      await onBatchDelete(Array.from(selectedIds));
    },
    onSuccess: () => {
      clearSelection();
    },
  });

  const batchUpdateMutation = useMutation({
    mutationFn: async (data: Partial<T>) => {
      if (!onBatchUpdate) throw new Error('onBatchUpdate not provided');
      await onBatchUpdate(Array.from(selectedIds), data);
    },
    onSuccess: () => {
      clearSelection();
    },
  });

  return {
    selectedIds: Array.from(selectedIds),
    selectedCount: selectedIds.size,
    toggleSelect,
    selectAll,
    clearSelection,
    isSelected,
    isAllSelected,
    isSomeSelected,
    batchDelete: batchDeleteMutation.mutate,
    batchUpdate: batchUpdateMutation.mutate,
    isBatchDeleting: batchDeleteMutation.isPending,
    isBatchUpdating: batchUpdateMutation.isPending,
  };
}
