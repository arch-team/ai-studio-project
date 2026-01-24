/**
 * Job Templates API
 *
 * API 调用函数
 * 对应后端端点: /api/v1/job-templates
 */

import type {
  CreateJobFromTemplateRequest,
  CreateJobTemplateRequest,
  JobTemplateDetail,
  JobTemplateSummary,
  TemplateFilters,
  TemplateListResponse,
  UpdateJobTemplateRequest,
} from '../types';

const API_BASE = '/api/v1';

// === Helper Functions ===

function getAuthHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${localStorage.getItem('access_token') || ''}`,
  };
}

function buildUrl(path: string, params?: Record<string, unknown>): string {
  const url = new URL(`${API_BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value));
      }
    });
  }
  return url.toString();
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || errorData.message || `HTTP Error: ${response.status}`);
  }
  return response.json();
}

// === Query APIs ===

/**
 * 获取模板列表
 */
export async function fetchJobTemplates(
  filters: TemplateFilters = {}
): Promise<TemplateListResponse> {
  const url = buildUrl('/job-templates', {
    search: filters.search,
    page: filters.page,
    page_size: filters.page_size,
    sort_by: filters.sort_by,
    sort_order: filters.sort_order,
  });

  const response = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  return handleResponse<TemplateListResponse>(response);
}

/**
 * 获取单个模板详情
 */
export async function fetchJobTemplate(id: number): Promise<JobTemplateDetail> {
  const response = await fetch(`${API_BASE}/job-templates/${id}`, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  return handleResponse<JobTemplateDetail>(response);
}

/**
 * 获取热门模板
 */
export async function fetchPopularTemplates(
  limit: number = 10
): Promise<JobTemplateSummary[]> {
  const url = buildUrl('/job-templates/popular', { limit });

  const response = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(),
  });

  return handleResponse<JobTemplateSummary[]>(response);
}

// === Mutation APIs ===

/**
 * 创建模板
 */
export async function createJobTemplate(
  data: CreateJobTemplateRequest
): Promise<JobTemplateDetail> {
  const response = await fetch(`${API_BASE}/job-templates`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  return handleResponse<JobTemplateDetail>(response);
}

/**
 * 更新模板
 */
export async function updateJobTemplate(
  id: number,
  data: UpdateJobTemplateRequest
): Promise<JobTemplateDetail> {
  const response = await fetch(`${API_BASE}/job-templates/${id}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  return handleResponse<JobTemplateDetail>(response);
}

/**
 * 删除模板
 */
export async function deleteJobTemplate(id: number): Promise<void> {
  const response = await fetch(`${API_BASE}/job-templates/${id}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP Error: ${response.status}`);
  }
}

/**
 * 基于模板创建训练任务
 */
export async function createJobFromTemplate(
  templateId: number,
  data: CreateJobFromTemplateRequest
): Promise<unknown> {
  const response = await fetch(`${API_BASE}/training-jobs/from-template/${templateId}`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  return handleResponse<unknown>(response);
}
