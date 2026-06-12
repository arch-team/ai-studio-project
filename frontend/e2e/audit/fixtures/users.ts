/**
 * 审计用用户管理 fixture
 * 形状对照: src/features/admin/types/index.ts (UserDetail / UserListResponse)
 * API 路径对照: src/features/admin/api/userApi.ts
 *   GET /users | GET /users/{id}
 */

export const mockUsers = [
  { id: 1, username: 'admin', email: 'admin@ai-studio.example.com', role: 'admin', status: 'active', resource_quota_id: 1, iam_identity_id: 'AROAEXAMPLEADMIN:admin', created_at: '2025-10-01T08:00:00Z', updated_at: '2026-05-20T09:30:00Z' },
  { id: 2, username: 'developer-li', email: 'li.dev@ai-studio.example.com', role: 'engineer', status: 'active', resource_quota_id: 2, iam_identity_id: 'AROAEXAMPLEENG:developer-li', created_at: '2025-11-12T03:20:00Z', updated_at: '2026-06-01T11:05:00Z' },
  { id: 3, username: 'mlops-zhang', email: 'zhang.mlops@ai-studio.example.com', role: 'project_manager', status: 'active', resource_quota_id: 2, created_at: '2025-12-05T06:45:00Z', updated_at: '2026-04-18T14:22:00Z' },
  { id: 4, username: 'cv-team-wang', email: 'wang.cv@ai-studio.example.com', role: 'engineer', status: 'active', resource_quota_id: 3, created_at: '2026-01-08T02:10:00Z', updated_at: '2026-05-30T08:00:00Z' },
  { id: 5, username: 'audio-team-liu', email: 'liu.audio@ai-studio.example.com', role: 'engineer', status: 'disabled', resource_quota_id: 3, created_at: '2026-02-14T09:00:00Z', updated_at: '2026-06-05T16:40:00Z' },
  { id: 6, username: 'finance-zhao', email: 'zhao.finance@ai-studio.example.com', role: 'viewer', status: 'active', resource_quota_id: null, created_at: '2026-03-03T07:30:00Z', updated_at: '2026-03-03T07:30:00Z' },
  { id: 12, username: 'intern-chen', email: 'chen.intern@ai-studio.example.com', role: 'viewer', status: 'pending', resource_quota_id: null, created_at: '2026-06-11T10:22:09Z', updated_at: '2026-06-11T10:22:09Z' },
];

export const userListResponse = {
  items: mockUsers,
  total: mockUsers.length,
  page: 1,
  page_size: 20,
  total_pages: 1,
};
