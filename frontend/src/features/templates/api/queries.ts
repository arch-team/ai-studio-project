/**
 * Job Templates Query Hooks
 *
 * TanStack Query hooks for template operations
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type {
  CreateJobFromTemplateRequest,
  CreateJobTemplateRequest,
  TemplateFilters,
  UpdateJobTemplateRequest,
} from '../types';
import {
  createJobFromTemplate,
  createJobTemplate,
  deleteJobTemplate,
  fetchJobTemplate,
  fetchJobTemplates,
  fetchPopularTemplates,
  updateJobTemplate,
} from './templateApi';

// === Query Keys ===

export const templateKeys = {
  all: ['jobTemplates'] as const,
  lists: () => [...templateKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...templateKeys.lists(), filters] as const,
  details: () => [...templateKeys.all, 'detail'] as const,
  detail: (id: string) => [...templateKeys.details(), id] as const,
  popular: () => [...templateKeys.all, 'popular'] as const,
};

// === Query Hooks ===

/**
 * 获取模板列表
 */
export function useJobTemplates(filters: TemplateFilters = {}) {
  return useQuery({
    queryKey: templateKeys.list(filters as Record<string, unknown>),
    queryFn: () => fetchJobTemplates(filters),
  });
}

/**
 * 获取单个模板详情
 */
export function useJobTemplate(id: number | undefined) {
  return useQuery({
    queryKey: templateKeys.detail(String(id)),
    queryFn: () => fetchJobTemplate(id!),
    enabled: id !== undefined,
  });
}

/**
 * 获取热门模板
 */
export function usePopularTemplates(limit: number = 10) {
  return useQuery({
    queryKey: templateKeys.popular(),
    queryFn: () => fetchPopularTemplates(limit),
  });
}

// === Mutation Hooks ===

/**
 * 创建模板
 */
export function useCreateJobTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateJobTemplateRequest) => createJobTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
      queryClient.invalidateQueries({ queryKey: templateKeys.popular() });
    },
  });
}

/**
 * 更新模板
 */
export function useUpdateJobTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateJobTemplateRequest }) =>
      updateJobTemplate(id, data),
    onSuccess: (result) => {
      queryClient.setQueryData(templateKeys.detail(String(result.id)), result);
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
    },
  });
}

/**
 * 删除模板
 */
export function useDeleteJobTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => deleteJobTemplate(id),
    onSuccess: (_result, id) => {
      queryClient.removeQueries({ queryKey: templateKeys.detail(String(id)) });
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
      queryClient.invalidateQueries({ queryKey: templateKeys.popular() });
    },
  });
}

/**
 * 基于模板创建训练任务
 */
export function useCreateJobFromTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      templateId,
      data,
    }: {
      templateId: number;
      data: CreateJobFromTemplateRequest;
    }) => createJobFromTemplate(templateId, data),
    onSuccess: () => {
      // 刷新模板列表 (更新使用次数)
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
      queryClient.invalidateQueries({ queryKey: templateKeys.popular() });
      // 刷新训练任务列表
      queryClient.invalidateQueries({ queryKey: ['trainingJobs'] });
    },
  });
}
