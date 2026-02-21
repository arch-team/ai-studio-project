/**
 * API 客户端抽象
 *
 * 提供统一的 HTTP 请求封装，包含错误处理、认证、重试等功能。
 */

import { AppError, ErrorCode, isApiErrorResponse } from "../types/errors";

// === 配置 ===

const API_BASE_URL =
  (typeof import.meta !== "undefined" &&
    (import.meta as unknown as { env?: { VITE_API_BASE_URL?: string } }).env
      ?.VITE_API_BASE_URL) ||
  "/api/v1";
const DEFAULT_TIMEOUT = 30000; // 30 seconds

// === 类型定义 ===

export type ParamValue =
  | string
  | number
  | boolean
  | undefined
  | null
  | (string | number | boolean)[];

export interface RequestConfig extends Omit<RequestInit, "body"> {
  params?: Record<string, ParamValue>;
  timeout?: number;
  retries?: number;
  retryDelay?: number;
}

export interface ApiResponse<T> {
  data: T;
  status: number;
  headers: Headers;
}

// === 工具函数 ===

/**
 * 构建 URL 查询参数（支持数组参数）
 */
function buildQueryString(params: Record<string, ParamValue>): string {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    if (Array.isArray(value)) {
      value.forEach((v) => searchParams.append(key, String(v)));
    } else {
      searchParams.append(key, String(value));
    }
  });
  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : "";
}

/**
 * 创建带超时的 fetch
 */
function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeout: number,
): Promise<Response> {
  return new Promise((resolve, reject) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
      reject(new AppError(ErrorCode.TIMEOUT, "请求超时"));
    }, timeout);

    fetch(url, { ...options, signal: controller.signal })
      .then((response) => {
        clearTimeout(timeoutId);
        resolve(response);
      })
      .catch((error) => {
        clearTimeout(timeoutId);
        if (error.name === "AbortError") {
          reject(new AppError(ErrorCode.TIMEOUT, "请求超时"));
        } else {
          reject(
            new AppError(ErrorCode.NETWORK_ERROR, "网络连接错误", {
              cause: error,
            }),
          );
        }
      });
  });
}

/**
 * 延迟函数
 */
function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// === API 客户端类 ===

class ApiClient {
  private baseUrl: string;
  private defaultHeaders: Record<string, string>;
  private isRefreshing = false;
  private refreshPromise: Promise<boolean> | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    this.defaultHeaders = {
      "Content-Type": "application/json",
    };
  }

  /**
   * 获取带自动 token 的 headers
   */
  private getHeadersWithAuth(
    extra?: Record<string, string>,
  ): Record<string, string> {
    const headers: Record<string, string> = {
      ...this.defaultHeaders,
      ...extra,
    };
    if (!headers["Authorization"] && typeof localStorage !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }
    return headers;
  }

  /**
   * 设置认证 token
   */
  setAuthToken(token: string): void {
    this.defaultHeaders["Authorization"] = `Bearer ${token}`;
  }

  /**
   * 清除认证 token
   */
  clearAuthToken(): void {
    delete this.defaultHeaders["Authorization"];
  }

  /**
   * 处理 token 刷新（防止并发请求同时触发）
   */
  private async handleTokenRefresh(): Promise<boolean> {
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;

    // 延迟导入避免循环依赖
    const { useAuthStore } = await import("@features/auth/store/authStore");

    this.refreshPromise = useAuthStore
      .getState()
      .tryRefreshToken()
      .finally(() => {
        this.isRefreshing = false;
        this.refreshPromise = null;
      });

    return this.refreshPromise;
  }

  /**
   * 认证失败处理 - 清除状态并重定向到登录页
   */
  private handleAuthFailure(): void {
    localStorage.removeItem("access_token");
    this.clearAuthToken();

    // 延迟导入避免循环依赖
    import("@features/auth/store/authStore").then(({ useAuthStore }) => {
      const state = useAuthStore.getState();
      if (state.isAuthenticated) {
        state.logout();
      }
    });
  }

  /**
   * 发送请求
   */
  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    config: RequestConfig = {},
  ): Promise<ApiResponse<T>> {
    const {
      params,
      timeout = DEFAULT_TIMEOUT,
      retries = 0,
      retryDelay = 1000,
      headers: customHeaders,
      ...restConfig
    } = config;

    const url = `${this.baseUrl}${path}${params ? buildQueryString(params) : ""}`;
    const headers = this.getHeadersWithAuth(
      customHeaders as Record<string, string>,
    );

    const options: RequestInit = {
      method,
      headers,
      ...restConfig,
    };

    if (body !== undefined) {
      options.body = JSON.stringify(body);
    }

    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const response = await fetchWithTimeout(url, options, timeout);

        if (!response.ok) {
          // 401 时尝试刷新 token (非 auth 路径请求)
          if (response.status === 401 && !path.startsWith("/auth/")) {
            const refreshed = await this.handleTokenRefresh();
            if (refreshed) {
              // 用新 token 重试当前请求
              const retryHeaders = this.getHeadersWithAuth(
                customHeaders as Record<string, string>,
              );
              const retryOptions: RequestInit = {
                method,
                headers: retryHeaders,
                ...restConfig,
              };
              if (body !== undefined) {
                retryOptions.body = JSON.stringify(body);
              }
              const retryResponse = await fetchWithTimeout(
                url,
                retryOptions,
                timeout,
              );
              if (retryResponse.ok) {
                const retryText = await retryResponse.text();
                const retryData = retryText ? JSON.parse(retryText) : null;
                return {
                  data: retryData as T,
                  status: retryResponse.status,
                  headers: retryResponse.headers,
                };
              }
            }
            // 刷新失败或重试失败，触发登出
            this.handleAuthFailure();
          }

          const error = await AppError.fromResponse(response);

          // 不重试 4xx 错误（客户端错误）
          if (response.status >= 400 && response.status < 500) {
            throw error;
          }

          // 重试 5xx 错误
          lastError = error;
          if (attempt < retries) {
            await delay(retryDelay * (attempt + 1)); // 指数退避
            continue;
          }
          throw error;
        }

        // 处理空响应
        const text = await response.text();
        const data = text ? JSON.parse(text) : null;

        // 检查是否为错误响应格式
        if (isApiErrorResponse(data)) {
          throw AppError.fromApiResponse(data);
        }

        return {
          data: data as T,
          status: response.status,
          headers: response.headers,
        };
      } catch (error) {
        lastError = error as Error;

        // 网络错误可以重试
        if (
          error instanceof AppError &&
          error.isNetworkError() &&
          attempt < retries
        ) {
          await delay(retryDelay * (attempt + 1));
          continue;
        }

        throw error;
      }
    }

    throw lastError || new AppError(ErrorCode.UNKNOWN, "请求失败");
  }

  /**
   * GET 请求
   */
  async get<T>(path: string, config?: RequestConfig): Promise<T> {
    const response = await this.request<T>("GET", path, undefined, config);
    return response.data;
  }

  /**
   * POST 请求
   */
  async post<T>(
    path: string,
    body?: unknown,
    config?: RequestConfig,
  ): Promise<T> {
    const response = await this.request<T>("POST", path, body, config);
    return response.data;
  }

  /**
   * PUT 请求
   */
  async put<T>(
    path: string,
    body?: unknown,
    config?: RequestConfig,
  ): Promise<T> {
    const response = await this.request<T>("PUT", path, body, config);
    return response.data;
  }

  /**
   * PATCH 请求
   */
  async patch<T>(
    path: string,
    body?: unknown,
    config?: RequestConfig,
  ): Promise<T> {
    const response = await this.request<T>("PATCH", path, body, config);
    return response.data;
  }

  /**
   * DELETE 请求
   */
  async delete<T = void>(path: string, config?: RequestConfig): Promise<T> {
    const response = await this.request<T>("DELETE", path, undefined, config);
    return response.data;
  }

  /**
   * 下载文件（返回 Blob）
   */
  async download(path: string, config?: RequestConfig): Promise<Blob> {
    const { params, timeout = DEFAULT_TIMEOUT, ...restConfig } = config || {};
    const url = `${this.baseUrl}${path}${params ? buildQueryString(params) : ""}`;

    const response = await fetchWithTimeout(
      url,
      {
        method: "GET",
        headers: this.getHeadersWithAuth(),
        ...restConfig,
      },
      timeout,
    );

    if (!response.ok) {
      throw await AppError.fromResponse(response);
    }

    return response.blob();
  }

  /**
   * 上传文件
   */
  async upload<T>(
    path: string,
    file: File,
    fieldName: string = "file",
    additionalData?: Record<string, string>,
    config?: RequestConfig,
  ): Promise<T> {
    const formData = new FormData();
    formData.append(fieldName, file);

    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    const { timeout = DEFAULT_TIMEOUT * 2, ...restConfig } = config || {};
    const url = `${this.baseUrl}${path}`;

    // 上传时不设置 Content-Type，让浏览器自动设置 multipart/form-data
    const headers = this.getHeadersWithAuth();
    delete headers["Content-Type"];

    const response = await fetchWithTimeout(
      url,
      {
        method: "POST",
        headers,
        body: formData,
        ...restConfig,
      },
      timeout,
    );

    if (!response.ok) {
      throw await AppError.fromResponse(response);
    }

    return response.json();
  }
}

// === 导出单例实例 ===

export const apiClient = new ApiClient();

// === 导出类用于测试或自定义实例 ===

export { ApiClient };
