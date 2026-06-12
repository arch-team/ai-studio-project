/**
 * 审计用审计日志 fixture
 * 形状对照: src/features/audit/types/index.ts (AuditLog / AuditLogListResponse)
 * API 路径对照: src/features/audit/api/auditApi.ts
 *   GET /audit-logs | GET /audit-logs/{id}
 */

const chromeUA =
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36';

export const mockAuditLogs = [
  { id: 101, user_id: 1, username: 'admin', ip_address: '10.20.8.41', user_agent: chromeUA, action: 'submit', resource_type: 'training_job', resource_id: '128', resource_name: 'qwen2-7b-sft-0612', request_method: 'POST', request_path: '/api/v1/training-jobs', response_status: 201, changes: null, result: 'success', error_message: null, created_at: '2026-06-12T09:42:18Z' },
  { id: 100, user_id: 3, username: 'mlops-zhang', ip_address: '10.20.8.57', user_agent: chromeUA, action: 'update', resource_type: 'resource_quota', resource_id: '5', resource_name: '算法团队配额', request_method: 'PATCH', request_path: '/api/v1/resource-quotas/5', response_status: 200, changes: { max_gpu_count: { old: 32, new: 48 }, max_concurrent_jobs: { old: 8, new: 12 } }, result: 'success', error_message: null, created_at: '2026-06-12T08:15:02Z' },
  { id: 99, user_id: 4, username: 'cv-team-wang', ip_address: '10.20.9.102', user_agent: chromeUA, action: 'delete', resource_type: 'dataset', resource_id: '23', resource_name: '废弃标注集-旧版', request_method: 'DELETE', request_path: '/api/v1/datasets/23', response_status: 204, changes: null, result: 'success', error_message: null, created_at: '2026-06-11T17:30:44Z' },
  { id: 98, user_id: 2, username: 'developer-li', ip_address: '10.20.8.88', user_agent: chromeUA, action: 'cancel', resource_type: 'training_job', resource_id: '121', resource_name: 'rec-ranker-nightly', request_method: 'POST', request_path: '/api/v1/training-jobs/121/cancel', response_status: 409, changes: null, result: 'failure', error_message: '任务已处于终态，无法取消', created_at: '2026-06-11T14:05:31Z' },
  { id: 97, user_id: 1, username: 'admin', ip_address: '10.20.8.41', user_agent: chromeUA, action: 'create', resource_type: 'user', resource_id: '12', resource_name: 'intern-chen', request_method: 'POST', request_path: '/api/v1/users', response_status: 201, changes: null, result: 'success', error_message: null, created_at: '2026-06-11T10:22:09Z' },
  { id: 96, user_id: 5, username: 'audio-team-liu', ip_address: '10.20.10.15', user_agent: chromeUA, action: 'update', resource_type: 'model', resource_id: '3', resource_name: 'voice-cmd-asr-conformer', request_method: 'PUT', request_path: '/api/v1/models/3', response_status: 200, changes: { display_name: { old: '语音识别', new: '语音指令识别' }, tags: { old: ['语音'], new: ['语音', 'ASR'] } }, result: 'success', error_message: null, created_at: '2026-06-10T16:48:55Z' },
  { id: 95, user_id: null, username: null, ip_address: '172.30.4.9', user_agent: 'python-requests/2.32.0', action: 'login', resource_type: 'user', resource_id: null, resource_name: null, request_method: 'POST', request_path: '/api/v1/auth/token', response_status: 401, changes: null, result: 'failure', error_message: '用户名或密码错误', created_at: '2026-06-10T03:12:40Z' },
  { id: 94, user_id: 3, username: 'mlops-zhang', ip_address: '10.20.8.57', user_agent: chromeUA, action: 'delete', resource_type: 'checkpoint', resource_id: '88', resource_name: 'ckpt-epoch-2-legacy', request_method: 'DELETE', request_path: '/api/v1/checkpoints/88', response_status: 207, changes: null, result: 'partial', error_message: 'S3 对象删除成功，FSx 缓存清理超时', created_at: '2026-06-09T20:33:17Z' },
  { id: 93, user_id: 2, username: 'developer-li', ip_address: '10.20.8.88', user_agent: chromeUA, action: 'logout', resource_type: 'user', resource_id: '2', resource_name: 'developer-li', request_method: 'POST', request_path: '/api/v1/auth/logout', response_status: 200, changes: null, result: 'success', error_message: null, created_at: '2026-06-09T18:00:02Z' },
];

export const auditLogListResponse = {
  items: mockAuditLogs,
  total: 247,
  page: 1,
  page_size: 20,
  total_pages: 13,
};
