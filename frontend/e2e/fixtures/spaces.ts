/**
 * 开发空间 (Spaces) E2E 测试数据 Fixtures
 *
 * 类型契约对齐 src/features/spaces/types/index.ts
 */

export interface MockSpaceSummary {
  id: string;
  space_name: string;
  owner_id: number;
  instance_type: string;
  space_type: string;
  status: string;
  created_at: string;
}

export interface MockSpaceDetail extends MockSpaceSummary {
  storage_size_gb: number;
  lifecycle_config_arn: string | null;
  sagemaker_space_arn: string | null;
  updated_at: string;
  deleted_at: string | null;
}

/**
 * Mock 空间列表 - 覆盖全部 4 个可见状态
 */
export const mockSpaces: MockSpaceDetail[] = [
  {
    id: '11111111-1111-1111-1111-111111111111',
    space_name: 'running-jupyter-space',
    owner_id: 1,
    instance_type: 'ml.g5.xlarge',
    space_type: 'jupyter',
    status: 'running',
    created_at: '2026-06-10T08:00:00Z',
    storage_size_gb: 10,
    lifecycle_config_arn: null,
    sagemaker_space_arn: 'arn:aws:sagemaker:us-east-1:123456789:space/d-test/running-jupyter-space',
    updated_at: '2026-06-10T08:05:00Z',
    deleted_at: null,
  },
  {
    id: '22222222-2222-2222-2222-222222222222',
    space_name: 'stopped-vscode-space',
    owner_id: 1,
    instance_type: 'ml.t3.medium',
    space_type: 'vscode',
    status: 'stopped',
    created_at: '2026-06-09T10:00:00Z',
    storage_size_gb: 20,
    lifecycle_config_arn: null,
    sagemaker_space_arn: 'arn:aws:sagemaker:us-east-1:123456789:space/d-test/stopped-vscode-space',
    updated_at: '2026-06-09T12:00:00Z',
    deleted_at: null,
  },
  {
    id: '33333333-3333-3333-3333-333333333333',
    space_name: 'pending-new-space',
    owner_id: 1,
    instance_type: 'ml.g5.2xlarge',
    space_type: 'jupyter',
    status: 'pending',
    created_at: '2026-06-12T01:00:00Z',
    storage_size_gb: 50,
    lifecycle_config_arn: null,
    sagemaker_space_arn: null,
    updated_at: '2026-06-12T01:00:00Z',
    deleted_at: null,
  },
  {
    id: '44444444-4444-4444-4444-444444444444',
    space_name: 'failed-rstudio-space',
    owner_id: 1,
    instance_type: 'ml.t3.large',
    space_type: 'rstudio',
    status: 'failed',
    created_at: '2026-06-08T09:00:00Z',
    storage_size_gb: 5,
    lifecycle_config_arn: null,
    sagemaker_space_arn: null,
    updated_at: '2026-06-08T09:30:00Z',
    deleted_at: null,
  },
];

/**
 * 构建分页列表响应（契约对齐 SpaceListResponse）
 */
export function createSpaceListResponse(
  items: MockSpaceSummary[],
  page = 1,
  pageSize = 20,
) {
  const start = (page - 1) * pageSize;
  const paged = items.slice(start, start + pageSize);
  return {
    items: paged.map(
      ({ id, space_name, owner_id, instance_type, space_type, status, created_at }) => ({
        id,
        space_name,
        owner_id,
        instance_type,
        space_type,
        status,
        created_at,
      }),
    ),
    total: items.length,
    page,
    page_size: pageSize,
    total_pages: Math.max(1, Math.ceil(items.length / pageSize)),
  };
}

/**
 * 按状态过滤
 */
export function filterSpacesByStatus(status: string): MockSpaceDetail[] {
  return mockSpaces.filter((s) => s.status === status);
}

/**
 * 按 ID 获取详情
 */
export function getMockSpaceDetail(id: string): MockSpaceDetail | undefined {
  return mockSpaces.find((s) => s.id === id);
}

/**
 * 生成唯一测试空间名称（符合 ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ 且 3-63 字符）
 */
export function generateTestSpaceName(prefix = 'e2e'): string {
  const ts = Date.now().toString(36);
  const rand = Math.random().toString(36).slice(2, 6);
  return `${prefix}-${ts}-${rand}`;
}
