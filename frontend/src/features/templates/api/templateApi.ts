/**
 * Job Templates API
 *
 * API 调用函数
 * 对应后端端点: /api/v1/job-templates
 */

import { apiClient } from '@shared/api';
import type {
  CreateJobFromTemplateRequest,
  CreateJobTemplateRequest,
  JobTemplateDetail,
  JobTemplateSummary,
  TemplateFilters,
  TemplateListResponse,
  UpdateJobTemplateRequest,
} from '../types';

// === Query APIs ===

/**
 * 获取模板列表
 */
export async function fetchJobTemplates(
  filters: TemplateFilters = {}
): Promise<TemplateListResponse> {
  return apiClient.get<TemplateListResponse>('/job-templates', {
    params: {
      search: filters.search,
      page: filters.page,
      page_size: filters.page_size,
      sort_by: filters.sort_by,
      sort_order: filters.sort_order,
    },
  });
}

/**
 * 获取单个模板详情
 */
export async function fetchJobTemplate(id: number): Promise<JobTemplateDetail> {
  return apiClient.get<JobTemplateDetail>(`/job-templates/${id}`);
}

/**
 * 获取热门模板
 */
export async function fetchPopularTemplates(
  limit: number = 10
): Promise<JobTemplateSummary[]> {
  return apiClient.get<JobTemplateSummary[]>('/job-templates/popular', {
    params: { limit },
  });
}

// === Mutation APIs ===

/**
 * 创建模板
 */
export async function createJobTemplate(
  data: CreateJobTemplateRequest
): Promise<JobTemplateDetail> {
  return apiClient.post<JobTemplateDetail>('/job-templates', data);
}

/**
 * 更新模板
 */
export async function updateJobTemplate(
  id: number,
  data: UpdateJobTemplateRequest
): Promise<JobTemplateDetail> {
  return apiClient.put<JobTemplateDetail>(`/job-templates/${id}`, data);
}

/**
 * 删除模板
 */
export async function deleteJobTemplate(id: number): Promise<void> {
  return apiClient.delete(`/job-templates/${id}`);
}

/**
 * 基于模板创建训练任务
 */
export async function createJobFromTemplate(
  templateId: number,
  data: CreateJobFromTemplateRequest
): Promise<unknown> {
  return apiClient.post<unknown>(`/training-jobs/from-template/${templateId}`, data);
}
