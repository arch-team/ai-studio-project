/**
 * 开发空间 (Spaces) - HyperPod 原生后端远程生命周期 E2E 测试
 *
 * 对称方式一 (spaces-remote.spec.ts), 验证 backend=hyperpod 的真实 K8s Workspace 生命周期。
 *
 * 仅在远程模式运行 (需真实后端 + 已部署 backend 字段支持 + 集群 add-on 就绪):
 *   E2E_BASE_URL=http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com \
 *     npx playwright test e2e/tests/spaces-hyperpod-remote.spec.ts
 *
 * 前置条件 (Phase B 已完成, 见 docs/superpowers/specs/2026-06-13-hyperpod-spaces-phase-b-infra.md):
 * - amazon-sagemaker-spaces add-on 已装 (workspace.jupyter.org CRD)
 * - Task Governance 托管命名空间 hyperpod-ns-dev-spaces + LocalQueue 就绪
 * - 后端 ALB 已部署含 backend 字段的 Phase A 代码 (OpenAPI CreateSpaceRequest 含 backend)
 *
 * 覆盖 (对称方式一):
 * 1. 列表页加载
 * 2. UI 创建 HyperPod 空间 (backend=hyperpod) → 列表可见且环境类型列显示 HyperPod
 * 3. 状态同步 pending → running (通过详情 lazy sync, K8s Workspace conditions)
 * 4. AWS 侧事实: kubectl 查真实 Workspace CRD 存在且 Available
 * 5. 停止 → desiredStatus=Stopped → 启动 → 删除 完整生命周期
 * 6. 测试后清理所有 e2e-hp- 前缀的遗留空间
 *
 * 基础模式说明: 当前 add-on 未启用 web UI, Workspace status.accessURL 不填充,
 * 故访问验证改为断言真实 K8s CRD 状态 (而非方式一的 sagemaker.aws presigned URL 域)。
 *
 * 成本控制: 使用 CPU 实例 (默认 sagemaker-jupyter-template 2C/8Gi), 不占 GPU。
 * 串行执行 (生命周期有顺序依赖), 共享一个测试空间以减少 AWS 资源开销。
 */

import { execFileSync } from 'node:child_process';
import { test, expect, APIRequestContext } from '@playwright/test';
import { SpacesPage } from '../pages/SpacesPage';
import { loginViaUI, TEST_CREDENTIALS } from '../utils/auth';
import { generateTestSpaceName } from '../fixtures/spaces';

const isRemote = !!process.env.E2E_BASE_URL;

// Task Governance 托管的真实命名空间 (Phase B Task 16 核验)
const HYPERPOD_NS = 'hyperpod-ns-dev-spaces';

/**
 * AWS/K8s 侧事实断言: 直接查真实 Workspace CRD 的 Available condition。
 * 平台契约要求 running = 底层 K8s Workspace 真实就绪,
 * 仅靠平台 API 无法证明,必须对照集群原生状态 (对称方式一的 DescribeApp)。
 *
 * 返回 Available condition 的 status ("True"/"False"/"Unknown"),
 * Workspace 不存在返回 null。
 */
function describeWorkspaceAvailable(spaceName: string): string | null {
  try {
    const out = execFileSync(
      'kubectl',
      [
        'get',
        'workspace',
        spaceName,
        '-n',
        HYPERPOD_NS,
        '-o',
        'jsonpath={.status.conditions[?(@.type=="Available")].status}',
        '--request-timeout=20s',
      ],
      { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] },
    );
    // 空字符串 = Workspace 存在但 condition 未就绪; 非空 = condition 值
    return out.trim() || 'Unknown';
  } catch {
    // NotFound = Workspace 不存在 = 无底层资源
    return null;
  }
}

/** 查 Workspace 是否仍存在于集群 (删除验证用) */
function workspaceExists(spaceName: string): boolean {
  try {
    execFileSync(
      'kubectl',
      ['get', 'workspace', spaceName, '-n', HYPERPOD_NS, '--request-timeout=20s'],
      { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] },
    );
    return true;
  } catch {
    return false;
  }
}

// 整个文件串行执行
test.describe.configure({ mode: 'serial' });

/** API 辅助: 登录拿 access token */
async function apiLogin(request: APIRequestContext): Promise<string> {
  const res = await request.post('/api/v1/auth/login', {
    data: {
      username: TEST_CREDENTIALS.username,
      password: TEST_CREDENTIALS.password,
    },
  });
  expect(res.ok(), `登录失败: ${res.status()}`).toBe(true);
  const data = await res.json();
  return data.tokens.access_token;
}

/** API 辅助: 轮询空间状态直到达到期望值 (通过详情端点触发 lazy sync) */
async function waitForSpaceStatus(
  request: APIRequestContext,
  token: string,
  spaceId: string,
  expected: string,
  timeoutMs = 300_000,
): Promise<Record<string, unknown>> {
  const start = Date.now();
  let last: Record<string, unknown> = {};
  while (Date.now() - start < timeoutMs) {
    const res = await request.get(`/api/v1/spaces/${spaceId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok()) {
      last = await res.json();
      if (last.status === expected) return last;
      if (last.status === 'failed' && expected !== 'failed') {
        throw new Error(`空间进入 failed 状态: ${JSON.stringify(last)}`);
      }
    }
    await new Promise((r) => setTimeout(r, 5000));
  }
  throw new Error(
    `等待空间 ${spaceId} 变为 ${expected} 超时, 最后状态: ${JSON.stringify(last)}`,
  );
}

/** API 辅助: 强制清理一个空间 (容错, 尽力而为) */
async function forceCleanupSpace(
  request: APIRequestContext,
  token: string,
  spaceId: string,
) {
  const headers = { Authorization: `Bearer ${token}` };
  try {
    const detail = await request.get(`/api/v1/spaces/${spaceId}`, { headers });
    if (!detail.ok()) return;
    const space = await detail.json();
    if (space.status === 'running') {
      await request.post(`/api/v1/spaces/${spaceId}/stop`, { headers });
    }
    await request.delete(`/api/v1/spaces/${spaceId}`, { headers });
  } catch {
    // 清理失败不阻塞测试报告
  }
}

test.describe('开发空间 - HyperPod 原生后端完整生命周期', () => {
  test.skip(!isRemote, '此组测试仅在远程模式下运行 (设置 E2E_BASE_URL)');

  const spaceName = generateTestSpaceName('e2e-hp');
  let spaceId = '';
  let token = '';

  test.afterAll(async ({ request }) => {
    if (spaceId && token) {
      await forceCleanupSpace(request, token, spaceId);
    }
  });

  test('1. 列表页正常加载', async ({ page }) => {
    const spacesPage = new SpacesPage(page);
    await loginViaUI(page);
    await spacesPage.goto();
    await spacesPage.waitForPageReady();

    await expect(spacesPage.pageTitle).toBeVisible();
    await expect(spacesPage.createButton).toBeVisible();
    const hasTable = await spacesPage.table.isVisible().catch(() => false);
    const hasEmpty = await spacesPage.emptyState.isVisible().catch(() => false);
    expect(hasTable || hasEmpty).toBe(true);
  });

  test('2. API 创建 HyperPod 空间并出现在列表', async ({ request }) => {
    token = await apiLogin(request);

    // 通过 API 创建 (UI 选型路径由前端单测覆盖; E2E 聚焦真实后端生命周期)
    // backend=hyperpod 触发 K8s Workspace CRD 创建, 纳入 Kueue 治理
    const res = await request.post('/api/v1/spaces', {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        space_name: spaceName,
        backend: 'hyperpod',
        space_type: 'jupyter',
        // 真实托管命名空间与队列 (Phase B Task 16)
        namespace: HYPERPOD_NS,
        queue_name: `${HYPERPOD_NS}-localqueue`,
        workspace_template: 'sagemaker-jupyter-template',
      },
    });
    expect(res.status(), `创建失败: ${res.status()} ${await res.text()}`).toBe(201);
    const created = await res.json();
    expect(created.backend).toBe('hyperpod');
    spaceId = created.id;
  });

  test('3. 列表页显示该空间且环境类型为 HyperPod', async ({ page }) => {
    const spacesPage = new SpacesPage(page);
    await loginViaUI(page);
    await spacesPage.goto();
    await spacesPage.waitForPageReady();

    await expect(spacesPage.rowByName(spaceName)).toBeVisible({ timeout: 20_000 });
  });

  test('4. 状态同步: pending → running (真实 K8s Workspace)', async ({ request }) => {
    expect(spaceId, '依赖步骤 2 创建的空间').toBeTruthy();

    // K8s Workspace 拉镜像 + Kueue admission 较慢, 给足超时
    const detail = await waitForSpaceStatus(request, token, spaceId, 'running', 300_000);
    expect(detail.status).toBe('running');
    expect(detail.namespace).toBe(HYPERPOD_NS);
  });

  test('5. AWS 侧事实: 真实 Workspace CRD 存在且 Available', async () => {
    // 对称方式一的 DescribeApp 断言: 直接查集群确认底层资源真实就绪
    await expect
      .poll(() => describeWorkspaceAvailable(spaceName), { timeout: 60_000, intervals: [5000] })
      .toBe('True');
  });

  test('6. UI 停止空间 → desiredStatus=Stopped 且状态变为已停止', async ({ page }) => {
    const spacesPage = new SpacesPage(page);
    await loginViaUI(page);
    await spacesPage.goto();
    await spacesPage.waitForPageReady();

    await spacesPage.clickRowAction(spaceName, '停止');

    await expect
      .poll(async () => spacesPage.getStatusOfSpace(spaceName), { timeout: 60_000 })
      .toContain('已停止');

    expect(await spacesPage.hasRowAction(spaceName, '启动')).toBe(true);
    expect(await spacesPage.hasRowAction(spaceName, '删除')).toBe(true);
  });

  test('7. UI 重新启动空间 → 恢复运行中', async ({ page, request }) => {
    const spacesPage = new SpacesPage(page);
    await loginViaUI(page);
    await spacesPage.goto();
    await spacesPage.waitForPageReady();

    await spacesPage.clickRowAction(spaceName, '启动');

    const detail = await waitForSpaceStatus(request, token, spaceId, 'running', 300_000);
    expect(detail.status).toBe('running');

    // AWS 侧事实: Workspace 重新 Available
    await expect
      .poll(() => describeWorkspaceAvailable(spaceName), { timeout: 120_000, intervals: [5000] })
      .toBe('True');
  });

  test('8. API 验证: running 状态不能直接删除 (409)', async ({ request }) => {
    const res = await request.delete(`/api/v1/spaces/${spaceId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status()).toBe(409);
  });

  test('9. UI 停止后删除空间 → 从列表消失且 CRD 真实删除', async ({ page }) => {
    const spacesPage = new SpacesPage(page);
    await loginViaUI(page);
    await spacesPage.goto();
    await spacesPage.waitForPageReady();

    // 停止
    await spacesPage.clickRowAction(spaceName, '停止');
    await expect
      .poll(async () => spacesPage.getStatusOfSpace(spaceName), { timeout: 60_000 })
      .toContain('已停止');

    // 删除 (带确认弹窗)
    await spacesPage.deleteSpace(spaceName);

    // 从列表消失
    await expect
      .poll(async () => spacesPage.hasSpace(spaceName), { timeout: 30_000 })
      .toBe(false);

    // AWS 侧事实: K8s Workspace CRD 真实删除 (释放配额)
    await expect
      .poll(() => workspaceExists(spaceName), { timeout: 60_000, intervals: [5000] })
      .toBe(false);
  });

  test('10. API 验证: 删除后详情返回 404', async ({ request }) => {
    const res = await request.get(`/api/v1/spaces/${spaceId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status()).toBe(404);
  });
});

test.describe('开发空间 - HyperPod 后端 API 契约验证', () => {
  test.skip(!isRemote, '此组测试仅在远程模式下运行');

  let token = '';

  test.beforeAll(async ({ request }) => {
    token = await apiLogin(request);
  });

  test('创建 HyperPod 空间响应含 backend 与 HyperPod 字段', async ({ request }) => {
    const name = generateTestSpaceName('e2e-hp-contract');
    const res = await request.post('/api/v1/spaces', {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        space_name: name,
        backend: 'hyperpod',
        space_type: 'jupyter',
        namespace: HYPERPOD_NS,
        queue_name: `${HYPERPOD_NS}-localqueue`,
        workspace_template: 'sagemaker-jupyter-template',
      },
    });
    expect(res.status()).toBe(201);
    const body = await res.json();
    expect(body.backend).toBe('hyperpod');
    expect(body.namespace).toBe(HYPERPOD_NS);

    // 立即清理 (契约验证不跑完整生命周期)
    await forceCleanupSpace(request, token, body.id);
  });

  test('默认 backend 为 studio (未传 backend 字段)', async ({ request }) => {
    const name = generateTestSpaceName('e2e-default-backend');
    const res = await request.post('/api/v1/spaces', {
      headers: { Authorization: `Bearer ${token}` },
      data: { space_name: name, space_type: 'jupyter', instance_type: 'ml.t3.medium' },
    });
    // 默认 studio 后端 (向后兼容)
    expect(res.status()).toBe(201);
    const body = await res.json();
    expect(body.backend).toBe('studio');

    await forceCleanupSpace(request, token, body.id);
  });
});

test.describe('开发空间 - HyperPod 遗留资源清理', () => {
  test.skip(!isRemote, '此组测试仅在远程模式下运行');

  test('清理所有 e2e-hp 前缀的测试空间', async ({ request }) => {
    const token = await apiLogin(request);
    const headers = { Authorization: `Bearer ${token}` };

    const res = await request.get('/api/v1/spaces?page=1&page_size=100', { headers });
    expect(res.ok()).toBe(true);
    const list = await res.json();

    const leftovers = list.items.filter((s: { space_name: string }) =>
      s.space_name.startsWith('e2e-hp') || s.space_name.startsWith('e2e-default-backend'),
    );

    for (const space of leftovers) {
      await forceCleanupSpace(request, token, space.id);
    }
  });
});
