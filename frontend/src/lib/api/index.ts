/**
 * API 基础设施导出
 *
 * Task: T098 - 请求重试逻辑
 */

export {
  // 重试配置
  DEFAULT_RETRY_CONFIG,
  calculateRetryDelay,
  isRetryableError,
  queryRetryFn,
  queryRetryDelay,
  // 拦截器
  interceptorManager,
} from './interceptors';

export type {
  RetryConfig,
  RequestInterceptor,
  ResponseInterceptor,
  ErrorInterceptor,
} from './interceptors';
