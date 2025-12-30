/**
 * 模型管理API客户端
 */

import axios, { AxiosError } from 'axios';
import type {
  Model,
  ModelCreateRequest,
  ModelUpdateRequest,
  ModelListResponse,
  ModelQueryParams,
  ModelVersion,
  ModelVersionCreateRequest,
  ModelVersionUpdateRequest,
  ModelVersionListResponse,
  ModelFilesResponse,
  ModelStorageStats,
  ModelStatus,
} from '@/types/model';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器:添加认证token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器:统一错误处理
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token过期,清除并跳转登录
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ==================== 模型管理API ====================

export const modelApi = {
  /**
   * 创建模型
   */
  async createModel(data: ModelCreateRequest): Promise<Model> {
    const response = await apiClient.post<Model>('/api/v1/models/', data);
    return response.data;
  },

  /**
   * 查询模型列表
   */
  async listModels(params?: ModelQueryParams): Promise<ModelListResponse> {
    const response = await apiClient.get<ModelListResponse>('/api/v1/models/', {
      params: {
        project_id: params?.project_id,
        framework: params?.framework,
        task_type: params?.task_type,
        page: params?.page || 1,
        page_size: params?.page_size || 20,
      },
    });
    return response.data;
  },

  /**
   * 获取模型详情
   */
  async getModel(modelId: number): Promise<Model> {
    const response = await apiClient.get<Model>(`/api/v1/models/${modelId}`);
    return response.data;
  },

  /**
   * 更新模型信息
   */
  async updateModel(modelId: number, data: ModelUpdateRequest): Promise<Model> {
    const response = await apiClient.patch<Model>(`/api/v1/models/${modelId}`, data);
    return response.data;
  },

  /**
   * 删除模型
   */
  async deleteModel(modelId: number, force: boolean = false): Promise<void> {
    await apiClient.delete(`/api/v1/models/${modelId}`, {
      params: { force },
    });
  },

  /**
   * 获取模型存储统计
   */
  async getModelStats(modelId: number): Promise<ModelStorageStats> {
    const response = await apiClient.get<ModelStorageStats>(
      `/api/v1/models/${modelId}/stats`
    );
    return response.data;
  },
};

// ==================== 模型版本管理API ====================

export const modelVersionApi = {
  /**
   * 上传文件创建模型版本
   */
  async createVersionWithUpload(
    modelId: number,
    file: File,
    data: ModelVersionCreateRequest
  ): Promise<ModelVersion> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('version', data.version);

    if (data.description) formData.append('description', data.description);
    if (data.model_format) formData.append('model_format', data.model_format);
    if (data.model_architecture)
      formData.append('model_architecture', data.model_architecture);

    const response = await apiClient.post<ModelVersion>(
      `/api/v1/models/${modelId}/versions`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 300000, // 5分钟超时
      }
    );
    return response.data;
  },

  /**
   * 查询模型的所有版本
   */
  async listVersions(
    modelId: number,
    status?: ModelStatus
  ): Promise<ModelVersionListResponse> {
    const response = await apiClient.get<ModelVersionListResponse>(
      `/api/v1/models/${modelId}/versions`,
      {
        params: status ? { status_filter: status } : undefined,
      }
    );
    return response.data;
  },

  /**
   * 获取模型版本详情
   */
  async getVersion(modelId: number, versionId: number): Promise<ModelVersion> {
    const response = await apiClient.get<ModelVersion>(
      `/api/v1/models/${modelId}/versions/${versionId}`
    );
    return response.data;
  },

  /**
   * 更新模型版本信息
   */
  async updateVersion(
    modelId: number,
    versionId: number,
    data: ModelVersionUpdateRequest
  ): Promise<ModelVersion> {
    const response = await apiClient.patch<ModelVersion>(
      `/api/v1/models/${modelId}/versions/${versionId}`,
      data
    );
    return response.data;
  },

  /**
   * 发布模型版本
   */
  async publishVersion(modelId: number, versionId: number): Promise<ModelVersion> {
    const response = await apiClient.post<ModelVersion>(
      `/api/v1/models/${modelId}/versions/${versionId}/publish`
    );
    return response.data;
  },

  /**
   * 删除模型版本
   */
  async deleteVersion(
    modelId: number,
    versionId: number,
    force: boolean = false
  ): Promise<void> {
    await apiClient.delete(`/api/v1/models/${modelId}/versions/${versionId}`, {
      params: { force },
    });
  },

  /**
   * 获取模型版本的文件列表
   */
  async listVersionFiles(modelId: number, version: string): Promise<ModelFilesResponse> {
    const response = await apiClient.get<ModelFilesResponse>(
      `/api/v1/models/${modelId}/versions/${version}/files`
    );
    return response.data;
  },
};

export default {
  ...modelApi,
  ...modelVersionApi,
};
