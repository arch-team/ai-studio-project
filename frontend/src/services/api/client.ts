/**
 * API客户端服务
 *
 * 提供统一的HTTP请求封装,处理认证、错误和响应格式
 */

import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

// API基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// 认证令牌存储键
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

/**
 * API响应格式
 */
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  request_id?: string;
}

/**
 * API错误响应格式
 */
export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    field?: string;
  };
  request_id?: string;
}

/**
 * 分页元数据
 */
export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

/**
 * 分页响应格式
 */
export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  pagination: PaginationMeta;
  request_id?: string;
}

/**
 * 创建Axios实例
 */
const createApiClient = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // 请求拦截器:添加认证令牌
  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem(ACCESS_TOKEN_KEY);
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // 响应拦截器:处理错误和令牌刷新
  instance.interceptors.response.use(
    (response) => {
      return response;
    },
    async (error: AxiosError<ApiError>) => {
      const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

      // 401错误:令牌过期,尝试刷新
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;

        try {
          const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
          if (!refreshToken) {
            throw new Error('No refresh token');
          }

          // 刷新令牌
          const response = await axios.post<ApiResponse<{
            access_token: string;
            refresh_token: string;
          }>>(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token } = response.data.data;

          // 保存新令牌
          localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
          localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token);

          // 重试原请求
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return instance(originalRequest);
        } catch (refreshError) {
          // 刷新失败,清除令牌并跳转登录
          localStorage.removeItem(ACCESS_TOKEN_KEY);
          localStorage.removeItem(REFRESH_TOKEN_KEY);
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }

      return Promise.reject(error);
    }
  );

  return instance;
};

// 创建API客户端实例
const apiClient = createApiClient();

/**
 * 通用请求方法
 */
export const request = async <T = any>(
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
  url: string,
  data?: any,
  config?: AxiosRequestConfig
): Promise<T> => {
  try {
    const response: AxiosResponse<ApiResponse<T>> = await apiClient.request({
      method,
      url,
      data,
      ...config,
    });
    return response.data.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      const apiError = error.response.data as ApiError;
      throw new Error(apiError.error.message);
    }
    throw error;
  }
};

/**
 * GET请求
 */
export const get = <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>('GET', url, undefined, config);
};

/**
 * POST请求
 */
export const post = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>('POST', url, data, config);
};

/**
 * PUT请求
 */
export const put = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>('PUT', url, data, config);
};

/**
 * DELETE请求
 */
export const del = <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>('DELETE', url, undefined, config);
};

/**
 * PATCH请求
 */
export const patch = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request<T>('PATCH', url, data, config);
};

/**
 * 保存认证令牌
 */
export const setAuthTokens = (accessToken: string, refreshToken: string): void => {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
};

/**
 * 获取访问令牌
 */
export const getAccessToken = (): string | null => {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
};

/**
 * 获取刷新令牌
 */
export const getRefreshToken = (): string | null => {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

/**
 * 清除认证令牌
 */
export const clearAuthTokens = (): void => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
};

/**
 * 检查是否已认证
 */
export const isAuthenticated = (): boolean => {
  return !!getAccessToken();
};

export default apiClient;
