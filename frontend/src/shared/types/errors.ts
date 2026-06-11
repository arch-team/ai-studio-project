/**
 * 统一错误类型定义
 *
 * 对应后端的 DomainError 体系，保持前后端错误处理一致性。
 * @see backend/src/shared/domain/errors.py
 */

// === 错误代码枚举 ===

export enum ErrorCode {
  // 通用错误 (1xxx)
  UNKNOWN = 'UNKNOWN',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  NOT_FOUND = 'NOT_FOUND',
  CONFLICT = 'CONFLICT',
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',
  RATE_LIMITED = 'RATE_LIMITED',

  // 训练任务错误 (2xxx)
  JOB_NOT_FOUND = 'JOB_NOT_FOUND',
  JOB_ALREADY_EXISTS = 'JOB_ALREADY_EXISTS',
  JOB_INVALID_STATE = 'JOB_INVALID_STATE',
  JOB_QUOTA_EXCEEDED = 'JOB_QUOTA_EXCEEDED',
  JOB_SUBMISSION_FAILED = 'JOB_SUBMISSION_FAILED',

  // 数据集错误 (3xxx)
  DATASET_NOT_FOUND = 'DATASET_NOT_FOUND',
  DATASET_ALREADY_EXISTS = 'DATASET_ALREADY_EXISTS',
  DATASET_INVALID_FORMAT = 'DATASET_INVALID_FORMAT',
  DATASET_STORAGE_ERROR = 'DATASET_STORAGE_ERROR',

  // 检查点错误 (4xxx)
  CHECKPOINT_NOT_FOUND = 'CHECKPOINT_NOT_FOUND',
  CHECKPOINT_CORRUPTED = 'CHECKPOINT_CORRUPTED',
  CHECKPOINT_RESTORE_FAILED = 'CHECKPOINT_RESTORE_FAILED',

  // 模型错误 (5xxx)
  MODEL_NOT_FOUND = 'MODEL_NOT_FOUND',
  MODEL_REGISTRY_ERROR = 'MODEL_REGISTRY_ERROR',
  MODEL_APPROVAL_REQUIRED = 'MODEL_APPROVAL_REQUIRED',

  // 资源配额错误 (6xxx)
  QUOTA_EXCEEDED = 'QUOTA_EXCEEDED',
  QUOTA_NOT_FOUND = 'QUOTA_NOT_FOUND',
  QUOTA_INVALID = 'QUOTA_INVALID',

  // 开发空间错误 (7xxx)
  SPACE_NOT_FOUND = 'SPACE_NOT_FOUND',
  SPACE_ALREADY_RUNNING = 'SPACE_ALREADY_RUNNING',
  SPACE_NOT_RUNNING = 'SPACE_NOT_RUNNING',
  SPACE_START_FAILED = 'SPACE_START_FAILED',

  // 集群错误 (8xxx)
  CLUSTER_NOT_FOUND = 'CLUSTER_NOT_FOUND',
  CLUSTER_UNHEALTHY = 'CLUSTER_UNHEALTHY',
  CLUSTER_NO_CAPACITY = 'CLUSTER_NO_CAPACITY',

  // 网络错误 (9xxx)
  NETWORK_ERROR = 'NETWORK_ERROR',
  TIMEOUT = 'TIMEOUT',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
}

// === 错误类型接口 ===

/**
 * API 错误响应结构
 * 对应后端的错误响应格式
 */
export interface ApiErrorResponse {
  error: {
    code: ErrorCode | string;
    message: string;
    details?: Record<string, unknown>;
    field_errors?: FieldError[];
    trace_id?: string;
  };
}

/**
 * 字段级别错误
 */
export interface FieldError {
  field: string;
  message: string;
  code?: string;
}

// === 错误基类 ===

/**
 * 应用错误基类
 *
 * 所有前端错误应该继承此类，保持错误处理一致性。
 */
export class AppError extends Error {
  readonly code: ErrorCode | string;
  readonly details?: Record<string, unknown>;
  readonly fieldErrors?: FieldError[];
  readonly traceId?: string;
  readonly isAppError = true;
  cause?: Error;

  constructor(
    code: ErrorCode | string,
    message: string,
    options?: {
      details?: Record<string, unknown>;
      fieldErrors?: FieldError[];
      traceId?: string;
      cause?: Error;
    }
  ) {
    super(message);
    this.code = code;
    // ES2022+ cause 支持 - 手动设置
    if (options?.cause) {
      this.cause = options.cause;
    }
    this.details = options?.details;
    this.fieldErrors = options?.fieldErrors;
    this.traceId = options?.traceId;
    this.name = 'AppError';
  }

  /**
   * 从 API 错误响应创建 AppError
   */
  static fromApiResponse(response: ApiErrorResponse, cause?: Error): AppError {
    const { error } = response;
    return new AppError(error.code, error.message, {
      details: error.details,
      fieldErrors: error.field_errors,
      traceId: error.trace_id,
      cause,
    });
  }

  /**
   * 从 HTTP 响应创建 AppError
   *
   * 支持两种后端错误格式:
   * - 业务错误: { error: { code, message, ... } }
   * - FastAPI 422 验证错误: { detail: [{ loc, msg, type }] }
   */
  static async fromResponse(response: Response): Promise<AppError> {
    try {
      const data = await response.json();
      if (data.error) {
        return AppError.fromApiResponse(data);
      }
      // FastAPI RequestValidationError: detail 为字段错误数组
      if (Array.isArray(data.detail)) {
        const fieldErrors: FieldError[] = data.detail.map(
          (item: { loc?: (string | number)[]; msg?: string; type?: string }) => ({
            // loc 形如 ["body", "space_name"]，取末段作为字段名
            field: String(item.loc?.[item.loc.length - 1] ?? ''),
            message: item.msg ?? '验证失败',
            code: item.type,
          })
        );
        const summary = fieldErrors
          .map((e) => (e.field ? `${e.field}: ${e.message}` : e.message))
          .join('；');
        return new AppError(
          ErrorCode.VALIDATION_ERROR,
          summary || '输入数据验证失败',
          { fieldErrors }
        );
      }
      return new AppError(
        ErrorCode.UNKNOWN,
        data.message || (typeof data.detail === 'string' ? data.detail : '') || response.statusText
      );
    } catch {
      return new AppError(ErrorCode.UNKNOWN, response.statusText);
    }
  }

  /**
   * 检查是否为特定错误代码
   */
  is(code: ErrorCode | string): boolean {
    return this.code === code;
  }

  /**
   * 检查是否为验证错误
   */
  isValidationError(): boolean {
    return this.code === ErrorCode.VALIDATION_ERROR;
  }

  /**
   * 检查是否为未授权错误
   */
  isUnauthorized(): boolean {
    return this.code === ErrorCode.UNAUTHORIZED;
  }

  /**
   * 检查是否为禁止访问错误
   */
  isForbidden(): boolean {
    return this.code === ErrorCode.FORBIDDEN;
  }

  /**
   * 检查是否为未找到错误
   */
  isNotFound(): boolean {
    return this.code === ErrorCode.NOT_FOUND || this.code.endsWith('_NOT_FOUND');
  }

  /**
   * 检查是否为网络错误
   */
  isNetworkError(): boolean {
    return (
      this.code === ErrorCode.NETWORK_ERROR ||
      this.code === ErrorCode.TIMEOUT ||
      this.code === ErrorCode.SERVICE_UNAVAILABLE
    );
  }
}

// === 类型守卫 ===

/**
 * 检查是否为 AppError 实例
 */
export function isAppError(error: unknown): error is AppError {
  return (
    error instanceof AppError ||
    (typeof error === 'object' &&
      error !== null &&
      'isAppError' in error &&
      (error as { isAppError: boolean }).isAppError === true)
  );
}

/**
 * 检查是否为 API 错误响应
 */
export function isApiErrorResponse(data: unknown): data is ApiErrorResponse {
  return (
    typeof data === 'object' &&
    data !== null &&
    'error' in data &&
    typeof (data as ApiErrorResponse).error === 'object' &&
    'code' in (data as ApiErrorResponse).error &&
    'message' in (data as ApiErrorResponse).error
  );
}

// === 错误消息映射 ===

/**
 * 错误代码到用户友好消息的映射
 */
export const ERROR_MESSAGES: Record<ErrorCode, string> = {
  [ErrorCode.UNKNOWN]: '发生未知错误，请稍后重试',
  [ErrorCode.VALIDATION_ERROR]: '输入数据验证失败',
  [ErrorCode.NOT_FOUND]: '请求的资源不存在',
  [ErrorCode.CONFLICT]: '资源冲突，请刷新后重试',
  [ErrorCode.UNAUTHORIZED]: '请先登录',
  [ErrorCode.FORBIDDEN]: '您没有权限执行此操作',
  [ErrorCode.RATE_LIMITED]: '请求过于频繁，请稍后重试',

  [ErrorCode.JOB_NOT_FOUND]: '训练任务不存在',
  [ErrorCode.JOB_ALREADY_EXISTS]: '训练任务名称已存在',
  [ErrorCode.JOB_INVALID_STATE]: '训练任务当前状态不允许此操作',
  [ErrorCode.JOB_QUOTA_EXCEEDED]: '超出训练任务配额限制',
  [ErrorCode.JOB_SUBMISSION_FAILED]: '训练任务提交失败',

  [ErrorCode.DATASET_NOT_FOUND]: '数据集不存在',
  [ErrorCode.DATASET_ALREADY_EXISTS]: '数据集名称已存在',
  [ErrorCode.DATASET_INVALID_FORMAT]: '数据集格式无效',
  [ErrorCode.DATASET_STORAGE_ERROR]: '数据集存储错误',

  [ErrorCode.CHECKPOINT_NOT_FOUND]: '检查点不存在',
  [ErrorCode.CHECKPOINT_CORRUPTED]: '检查点文件已损坏',
  [ErrorCode.CHECKPOINT_RESTORE_FAILED]: '检查点恢复失败',

  [ErrorCode.MODEL_NOT_FOUND]: '模型不存在',
  [ErrorCode.MODEL_REGISTRY_ERROR]: '模型注册失败',
  [ErrorCode.MODEL_APPROVAL_REQUIRED]: '模型需要审批',

  [ErrorCode.QUOTA_EXCEEDED]: '超出资源配额限制',
  [ErrorCode.QUOTA_NOT_FOUND]: '资源配额不存在',
  [ErrorCode.QUOTA_INVALID]: '资源配额配置无效',

  [ErrorCode.SPACE_NOT_FOUND]: '开发空间不存在',
  [ErrorCode.SPACE_ALREADY_RUNNING]: '开发空间已在运行',
  [ErrorCode.SPACE_NOT_RUNNING]: '开发空间未运行',
  [ErrorCode.SPACE_START_FAILED]: '开发空间启动失败',

  [ErrorCode.CLUSTER_NOT_FOUND]: '集群不存在',
  [ErrorCode.CLUSTER_UNHEALTHY]: '集群状态异常',
  [ErrorCode.CLUSTER_NO_CAPACITY]: '集群容量不足',

  [ErrorCode.NETWORK_ERROR]: '网络连接错误，请检查网络',
  [ErrorCode.TIMEOUT]: '请求超时，请稍后重试',
  [ErrorCode.SERVICE_UNAVAILABLE]: '服务暂时不可用',
};

/**
 * 获取错误消息
 */
export function getErrorMessage(error: unknown): string {
  if (isAppError(error)) {
    return error.message || ERROR_MESSAGES[error.code as ErrorCode] || ERROR_MESSAGES[ErrorCode.UNKNOWN];
  }
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  return ERROR_MESSAGES[ErrorCode.UNKNOWN];
}
