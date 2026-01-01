/**
 * 训练任务API客户端
 */

import axios from 'axios';
import type {
  Checkpoint,
  TrainingJob,
  TrainingJobCreateRequest,
  TrainingJobListResponse,
  TrainingJobMetrics,
  TrainingJobQueryParams,
  TrainingJobStatusResponse,
  TrainingJobUpdateRequest,
} from '../types/training';

// API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加认证令牌
apiClient.interceptors.request.use(
  (config) => {
    // TODO: 从存储中获取认证令牌
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器 - 统一错误处理
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 未授权,跳转登录
      // TODO: 实现登录跳转
      console.error('未授权,请先登录');
    }
    return Promise.reject(error);
  }
);

/**
 * 训练任务API
 */
export const trainingApi = {
  /**
   * 创建训练任务
   */
  async createJob(data: TrainingJobCreateRequest): Promise<TrainingJob> {
    const response = await apiClient.post<TrainingJob>('/training/jobs', data);
    return response.data;
  },

  /**
   * 查询训练任务列表
   */
  async listJobs(params?: TrainingJobQueryParams): Promise<TrainingJobListResponse> {
    const response = await apiClient.get<TrainingJobListResponse>('/training/jobs', {
      params,
    });
    return response.data;
  },

  /**
   * 查询训练任务详情
   */
  async getJob(jobId: number): Promise<TrainingJob> {
    const response = await apiClient.get<TrainingJob>(`/training/jobs/${jobId}`);
    return response.data;
  },

  /**
   * 更新训练任务
   */
  async updateJob(jobId: number, data: TrainingJobUpdateRequest): Promise<TrainingJob> {
    const response = await apiClient.patch<TrainingJob>(`/training/jobs/${jobId}`, data);
    return response.data;
  },

  /**
   * 启动训练任务
   */
  async startJob(jobId: number): Promise<TrainingJob> {
    const response = await apiClient.post<TrainingJob>(`/training/jobs/${jobId}/start`);
    return response.data;
  },

  /**
   * 停止训练任务
   */
  async stopJob(jobId: number): Promise<TrainingJob> {
    const response = await apiClient.post<TrainingJob>(`/training/jobs/${jobId}/stop`);
    return response.data;
  },

  /**
   * 删除训练任务
   */
  async deleteJob(jobId: number, force = false): Promise<void> {
    await apiClient.delete(`/training/jobs/${jobId}`, {
      params: { force },
    });
  },

  /**
   * 查询训练任务状态
   */
  async getJobStatus(jobId: number): Promise<TrainingJobStatusResponse> {
    const response = await apiClient.get<TrainingJobStatusResponse>(
      `/training/jobs/${jobId}/status`
    );
    return response.data;
  },

  /**
   * 同步训练任务状态
   */
  async syncJobStatus(jobId: number): Promise<TrainingJob> {
    const response = await apiClient.post<TrainingJob>(`/training/jobs/${jobId}/sync`);
    return response.data;
  },

  /**
   * 查询训练任务指标
   */
  async getJobMetrics(
    jobId: number,
    params?: { limit?: number; offset?: number }
  ): Promise<TrainingJobMetrics[]> {
    const response = await apiClient.get<TrainingJobMetrics[]>(
      `/training/jobs/${jobId}/metrics`,
      { params }
    );
    return response.data;
  },

  /**
   * 查询训练任务日志
   */
  async getJobLogs(
    jobId: number,
    params?: { tail_lines?: number; pod_name?: string }
  ): Promise<{ job_id: number; pod_name: string | null; tail_lines: number; logs: Record<string, string> }> {
    const response = await apiClient.get(`/training/jobs/${jobId}/logs`, { params });
    return response.data;
  },

  /**
   * 查询训练任务检查点
   */
  async getJobCheckpoints(
    jobId: number,
    params?: { limit?: number; offset?: number }
  ): Promise<Checkpoint[]> {
    const response = await apiClient.get<Checkpoint[]>(
      `/training/jobs/${jobId}/checkpoints`,
      { params }
    );
    return response.data;
  },
};

export default trainingApi;
