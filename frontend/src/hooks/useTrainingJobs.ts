/**
 * 训练任务React Query Hooks
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { trainingApi } from '../api/training';
import type {
  TrainingJobCreateRequest,
  TrainingJobQueryParams,
  TrainingJobUpdateRequest,
} from '../types/training';

// Query Keys
export const trainingQueryKeys = {
  all: ['training'] as const,
  lists: () => [...trainingQueryKeys.all, 'list'] as const,
  list: (params?: TrainingJobQueryParams) =>
    [...trainingQueryKeys.lists(), params] as const,
  details: () => [...trainingQueryKeys.all, 'detail'] as const,
  detail: (id: number) => [...trainingQueryKeys.details(), id] as const,
  status: (id: number) => [...trainingQueryKeys.all, 'status', id] as const,
};

/**
 * 查询训练任务列表
 */
export function useTrainingJobs(params?: TrainingJobQueryParams) {
  return useQuery({
    queryKey: trainingQueryKeys.list(params),
    queryFn: () => trainingApi.listJobs(params),
    staleTime: 30000, // 30秒内不重新请求
  });
}

/**
 * 查询训练任务详情
 */
export function useTrainingJob(jobId: number) {
  return useQuery({
    queryKey: trainingQueryKeys.detail(jobId),
    queryFn: () => trainingApi.getJob(jobId),
    enabled: !!jobId,
  });
}

/**
 * 查询训练任务状态
 */
export function useTrainingJobStatus(jobId: number, enabled = true) {
  return useQuery({
    queryKey: trainingQueryKeys.status(jobId),
    queryFn: () => trainingApi.getJobStatus(jobId),
    enabled: !!jobId && enabled,
    refetchInterval: 5000, // 每5秒自动刷新
  });
}

/**
 * 创建训练任务
 */
export function useCreateTrainingJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TrainingJobCreateRequest) => trainingApi.createJob(data),
    onSuccess: () => {
      // 创建成功后,使列表查询失效
      queryClient.invalidateQueries({ queryKey: trainingQueryKeys.lists() });
    },
  });
}

/**
 * 更新训练任务
 */
export function useUpdateTrainingJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ jobId, data }: { jobId: number; data: TrainingJobUpdateRequest }) =>
      trainingApi.updateJob(jobId, data),
    onSuccess: (_, variables) => {
      // 更新成功后,使详情和列表查询失效
      queryClient.invalidateQueries({ queryKey: trainingQueryKeys.detail(variables.jobId) });
      queryClient.invalidateQueries({ queryKey: trainingQueryKeys.lists() });
    },
  });
}

/**
 * 启动训练任务
 */
export function useStartTrainingJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: number) => trainingApi.startJob(jobId),
    onSuccess: (_, jobId) => {
      queryClient.invalidateQueries({ queryKey: trainingQueryKeys.detail(jobId) });
      queryClient.invalidateQueries({ queryKey: trainingQueryKeys.status(jobId) });
      queryClient.invalidateQueries({ queryKey: trainingQueryKeys.lists() });
    },
  });
}

/**
 * 停止训练任务
 */
export function useStopTrainingJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: number) => trainingApi.stopJob(jobId),
    onSuccess: (_, jobId) => {
      queryClient.invalidateQueries({ queryKey: trainingQueryKeys.detail(jobId) });
      queryClient.invalidateQueries({ queryKey: trainingQueryKeys.status(jobId) });
      queryClient.invalidateQueries({ queryKey: trainingQueryKeys.lists() });
    },
  });
}

/**
 * 删除训练任务
 */
export function useDeleteTrainingJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ jobId, force }: { jobId: number; force?: boolean }) =>
      trainingApi.deleteJob(jobId, force),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: trainingQueryKeys.detail(variables.jobId) });
      queryClient.invalidateQueries({ queryKey: trainingQueryKeys.lists() });
    },
  });
}

/**
 * 同步训练任务状态
 */
export function useSyncTrainingJobStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: number) => trainingApi.syncJobStatus(jobId),
    onSuccess: (_, jobId) => {
      queryClient.invalidateQueries({ queryKey: trainingQueryKeys.detail(jobId) });
      queryClient.invalidateQueries({ queryKey: trainingQueryKeys.status(jobId) });
      queryClient.invalidateQueries({ queryKey: trainingQueryKeys.lists() });
    },
  });
}
