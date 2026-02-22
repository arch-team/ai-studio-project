/**
 * 请求/响应拦截器
 *
 * Task: T098 - 请求重试逻辑
 * 提供请求拦截、响应拦截和重试策略配置。
 */

import { AppError, ErrorCode } from "@shared/types";

// === 重试策略配置 ===

/**
 * 重试配置
 */
export interface RetryConfig {
  /** 最大重试次数 */
  maxRetries: number;
  /** 基础延迟时间 (毫秒) */
  baseDelay: number;
  /** 最大延迟时间 (毫秒) */
  maxDelay: number;
}

/**
 * 默认重试配置: 指数退避 (1s, 2s, 4s)，最多 3 次
 */
export const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelay: 1000,
  maxDelay: 4000,
};

// === 重试策略 ===

/**
 * 计算指数退避延迟时间
 *
 * @param attempt - 当前重试次数 (从 0 开始)
 * @param config - 重试配置
 * @returns 延迟时间 (毫秒)
 */
export function calculateRetryDelay(
  attempt: number,
  config: RetryConfig = DEFAULT_RETRY_CONFIG,
): number {
  // 指数退避: baseDelay * 2^attempt
  const delay = config.baseDelay * Math.pow(2, attempt);
  return Math.min(delay, config.maxDelay);
}

/**
 * 判断错误是否可重试
 *
 * 重试策略:
 * - 5xx 服务端错误: 可重试
 * - 408 请求超时: 可重试
 * - 429 请求频率限制: 可重试
 * - 网络错误 (NETWORK_ERROR, TIMEOUT, SERVICE_UNAVAILABLE): 可重试
 * - 4xx 客户端错误 (除 408/429): 不可重试
 * - 401/403 认证/授权错误: 不可重试
 */
export function isRetryableError(error: unknown): boolean {
  // 原生 fetch 网络错误 (断网、DNS 失败等)
  if (
    error instanceof TypeError &&
    error.message.toLowerCase().includes("fetch")
  ) {
    return true;
  }

  // 请求被中止 (超时等)
  if (error instanceof DOMException && error.name === "AbortError") {
    return true;
  }

  if (error instanceof AppError) {
    // 网络错误可重试
    if (error.isNetworkError()) {
      return true;
    }

    // 认证/授权错误不重试
    if (error.isUnauthorized() || error.isForbidden()) {
      return false;
    }

    // 资源不存在不重试
    if (error.isNotFound()) {
      return false;
    }

    // 验证错误不重试
    if (error.isValidationError()) {
      return false;
    }

    // 冲突错误不重试
    if (error.is(ErrorCode.CONFLICT)) {
      return false;
    }

    // 频率限制可重试
    if (error.is(ErrorCode.RATE_LIMITED)) {
      return true;
    }
  }

  // 未知错误默认不重试
  return false;
}

/**
 * TanStack Query 重试函数
 *
 * 用于 QueryClient 的 retry 配置，实现智能重试策略。
 *
 * @param failureCount - 已失败次数
 * @param error - 错误对象
 * @returns 是否继续重试
 */
export function queryRetryFn(failureCount: number, error: unknown): boolean {
  // 超过最大重试次数
  if (failureCount >= DEFAULT_RETRY_CONFIG.maxRetries) {
    return false;
  }

  return isRetryableError(error);
}

/**
 * TanStack Query 重试延迟函数
 *
 * @param attemptIndex - 重试次数 (从 0 开始)
 * @returns 延迟时间 (毫秒)
 */
export function queryRetryDelay(attemptIndex: number): number {
  return calculateRetryDelay(attemptIndex);
}

// === 请求拦截器 ===

/**
 * 请求拦截器类型
 */
export type RequestInterceptor = (config: {
  url: string;
  options: RequestInit;
}) =>
  | { url: string; options: RequestInit }
  | Promise<{ url: string; options: RequestInit }>;

/**
 * 响应拦截器类型
 */
export type ResponseInterceptor = (
  response: Response,
) => Response | Promise<Response>;

/**
 * 错误拦截器类型
 */
export type ErrorInterceptor = (error: unknown) => unknown | Promise<unknown>;

/**
 * 拦截器管理器
 *
 * 管理请求和响应拦截器链，支持注册和注销。
 */
class InterceptorManager {
  private requestInterceptors: Map<number, RequestInterceptor> = new Map();
  private responseInterceptors: Map<number, ResponseInterceptor> = new Map();
  private errorInterceptors: Map<number, ErrorInterceptor> = new Map();
  private nextId = 0;

  /**
   * 注册请求拦截器
   * @returns 拦截器 ID (用于注销)
   */
  addRequestInterceptor(interceptor: RequestInterceptor): number {
    const id = this.nextId++;
    this.requestInterceptors.set(id, interceptor);
    return id;
  }

  /**
   * 注册响应拦截器
   * @returns 拦截器 ID (用于注销)
   */
  addResponseInterceptor(interceptor: ResponseInterceptor): number {
    const id = this.nextId++;
    this.responseInterceptors.set(id, interceptor);
    return id;
  }

  /**
   * 注册错误拦截器
   * @returns 拦截器 ID (用于注销)
   */
  addErrorInterceptor(interceptor: ErrorInterceptor): number {
    const id = this.nextId++;
    this.errorInterceptors.set(id, interceptor);
    return id;
  }

  /**
   * 移除拦截器
   */
  removeInterceptor(id: number): void {
    this.requestInterceptors.delete(id);
    this.responseInterceptors.delete(id);
    this.errorInterceptors.delete(id);
  }

  /**
   * 执行请求拦截器链
   */
  async runRequestInterceptors(config: {
    url: string;
    options: RequestInit;
  }): Promise<{ url: string; options: RequestInit }> {
    let result = config;
    for (const interceptor of this.requestInterceptors.values()) {
      result = await interceptor(result);
    }
    return result;
  }

  /**
   * 执行响应拦截器链
   */
  async runResponseInterceptors(response: Response): Promise<Response> {
    let result = response;
    for (const interceptor of this.responseInterceptors.values()) {
      result = await interceptor(result);
    }
    return result;
  }

  /**
   * 执行错误拦截器链
   */
  async runErrorInterceptors(error: unknown): Promise<unknown> {
    let result = error;
    for (const interceptor of this.errorInterceptors.values()) {
      result = await interceptor(result);
    }
    return result;
  }
}

/**
 * 全局拦截器管理器实例
 */
export const interceptorManager = new InterceptorManager();
