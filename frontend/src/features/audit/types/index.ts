/**
 * Audit module type definitions.
 * Maps to backend schemas: src/modules/audit/
 *
 * 审计日志模块 - 只读查询，用于安全审计和问题追溯
 */

// === Enums ===

export type AuditAction =
  | 'create'
  | 'read'
  | 'update'
  | 'delete'
  | 'submit'
  | 'cancel'
  | 'pause'
  | 'resume'
  | 'start'
  | 'stop'
  | 'login'
  | 'logout';

export type AuditResourceType =
  | 'training_job'
  | 'dataset'
  | 'checkpoint'
  | 'model'
  | 'space'
  | 'user'
  | 'resource_quota'
  | 'job_template';

export type AuditResult = 'success' | 'failure' | 'partial';

// === Audit Log Types ===

export interface AuditLog {
  id: number;
  user_id: number | null;
  username: string | null;
  ip_address: string | null;
  user_agent: string | null;
  action: AuditAction;
  resource_type: AuditResourceType;
  resource_id: string | null;
  resource_name: string | null;
  request_method: string | null;
  request_path: string | null;
  response_status: number | null;
  changes: Record<string, { old: unknown; new: unknown }> | null;
  result: AuditResult;
  error_message: string | null;
  created_at: string;
}

// === Filter Types ===

export interface AuditLogFilters {
  user_id?: number;
  username?: string;
  action?: AuditAction;
  resource_type?: AuditResourceType;
  resource_id?: string;
  result?: AuditResult;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
  sort_order?: 'asc' | 'desc';
}

// === Response Types ===

export interface AuditLogListResponse {
  items: AuditLog[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// === UI Helper Types ===

// Cloudscape StatusIndicator 有效类型
type StatusIndicatorType =
  | 'success'
  | 'warning'
  | 'error'
  | 'info'
  | 'stopped'
  | 'pending'
  | 'in-progress'
  | 'loading';

export const AUDIT_ACTION_LABELS: Record<AuditAction, string> = {
  create: '创建',
  read: '查看',
  update: '更新',
  delete: '删除',
  submit: '提交',
  cancel: '取消',
  pause: '暂停',
  resume: '恢复',
  start: '启动',
  stop: '停止',
  login: '登录',
  logout: '登出',
};

export const AUDIT_ACTION_COLORS: Record<AuditAction, StatusIndicatorType> = {
  create: 'success',
  read: 'stopped',
  update: 'info',
  delete: 'error',
  submit: 'info',
  cancel: 'pending',
  pause: 'pending',
  resume: 'success',
  start: 'success',
  stop: 'error',
  login: 'success',
  logout: 'stopped',
};

export const AUDIT_RESOURCE_TYPE_LABELS: Record<AuditResourceType, string> = {
  training_job: '训练任务',
  dataset: '数据集',
  checkpoint: '检查点',
  model: '模型',
  space: '开发空间',
  user: '用户',
  resource_quota: '资源配额',
  job_template: '任务模板',
};

export const AUDIT_RESULT_LABELS: Record<AuditResult, string> = {
  success: '成功',
  failure: '失败',
  partial: '部分成功',
};

export const AUDIT_RESULT_COLORS: Record<AuditResult, StatusIndicatorType> = {
  success: 'success',
  failure: 'error',
  partial: 'warning',
};
