/**
 * 开发空间 (Spaces) - 远程环境全生命周期 E2E 测试
 *
 * 仅在远程模式运行（需要真实后端 + SageMaker）:
 *   E2E_BASE_URL=http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com \
 *     npx playwright test e2e/tests/spaces-remote.spec.ts
 *
 * 覆盖:
 * 1. 列表页加载真实数据
 * 2. UI 创建空间 → 列表可见
 * 3. 状态同步 pending → running（通过详情 lazy sync）
 * 4. 停止 → 启动 → 停止 → 删除 完整生命周期
 * 5. 测试后清理所有 e2e- 前缀的遗留空间
 *
 * 注意: 测试串行执行（生命周期有顺序依赖），共享一个测试空间以减少 AWS 资源开销
 */

import { test, expect, APIRequestContext } from '@playwright/test';
import { SpacesPage } from '../pages/SpacesPage';
import { loginViaUI, TEST_CREDENTIALS } from '../utils/auth';
import { generateTestSpaceName } from '../fixtures/spaces';

const isRemote = !!process.env.E2E_BASE_URL;

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

/** API 辅助: 轮询空间状态直到达到期望值（通过详情端点触发 lazy sync） */
async function waitForSpaceStatus(
  request: APIRequestContext,
  token: string,
  spaceId: string,
  expected: string,
  timeoutMs = 180_000,
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
      // 创建中途失败直接报错，避免空等
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

/** API 辅助: 强制清理一个空间（容错，尽力而为） */
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

test.describe('开发空间 - 远程环境完整生命周期', () => {
  test.skip(!isRemote, '此组测试仅在远程模式下运行 (设置 E2E_BASE_URL)');

  const spaceName = generateTestSpaceName('e2e');
  let spaceId = '';
  let token = '';

  test.afterAll(async ({ request }) => {
    // 兜底清理本测试创建的空间
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
    // 表格或空状态二选一
    const hasTable = await spacesPage.table.isVisible().catch(() => false);
    const hasEmpty = await spacesPage.emptyState.isVisible().catch(() => false);
    expect(hasTable || hasEmpty).toBe(true);
  });

  test('2. UI 创建空间成功并出现在列表', async ({ page, request }) => {
    token = await apiLogin(request);

    const spacesPage = new SpacesPage(page);
    await loginViaUI(page);
    await spacesPage.gotoCreate();

    await spacesPage.fillCreateForm({
      name: spaceName,
      // 默认 jupyter + ml.g5.xlarge，存储用最小 5GB 控制成本
      storageGb: '5',
    });
    await spacesPage.submitCreateForm();

    // 创建成功跳回列表页（SageMaker create_space 同步调用，给足超时）
    await page.waitForURL(/\/spaces$/, { timeout: 120_000 });

    // 表格行异步加载，用自动重试断言避免竞态
    await expect(spacesPage.rowByName(spaceName)).toBeVisible({
      timeout: 20_000,
    });

    // 通过 API 获取空间 ID 供后续步骤使用
    const res = await request.get('/api/v1/spaces?page=1&page_size=100', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBe(true);
    const list = await res.json();
    const created = list.items.find(
      (s: { space_name: string }) => s.space_name === spaceName,
    );
    expect(created, '新建空间应出现在列表 API').toBeTruthy();
    spaceId = created.id;
  });

  test('3. 状态同步: pending → running', async ({ request }) => {
    expect(spaceId, '依赖步骤 2 创建的空间').toBeTruthy();

    const detail = await waitForSpaceStatus(request, token, spaceId, 'running');
    expect(detail.status).toBe('running');
    expect(detail.sagemaker_space_arn).toBeTruthy();
  });

  test('4. 列表页显示 running 状态并提供停止按钮', async ({ page }) => {
    const spacesPage = new SpacesPage(page);
    await loginViaUI(page);
    await spacesPage.goto();
    await spacesPage.waitForPageReady();

    const status = await spacesPage.getStatusOfSpace(spaceName);
    expect(status).toContain('运行中');
    expect(await spacesPage.hasRowAction(spaceName, '停止')).toBe(true);
  });

  test('4b. 点击空间名称进入详情页且显示配置信息', async ({ page }) => {
    const spacesPage = new SpacesPage(page);
    await loginViaUI(page);
    await spacesPage.goto();
    await spacesPage.waitForPageReady();

    await spacesPage.clickSpaceName(spaceName);
    await page.waitForLoadState('networkidle');

    // 详情页路由已注册，不应跳 404
    await expect(page.getByText('页面未找到')).not.toBeVisible();
    expect(page.url()).toContain(`/spaces/${spaceId}`);

    // 详情字段渲染
    await expect(page.getByText('基本信息')).toBeVisible({ timeout: 15000 });
    await expect(page.getByText('存储大小')).toBeVisible();
    await expect(page.getByText('SageMaker ARN')).toBeVisible();
  });

  test('5. UI 停止空间 → 状态变为已停止', async ({ page }) => {
    const spacesPage = new SpacesPage(page);
    await loginViaUI(page);
    await spacesPage.goto();
    await spacesPage.waitForPageReady();

    await spacesPage.clickRowAction(spaceName, '停止');

    // 等待列表刷新后状态变更
    await expect
      .poll(
        async () => {
          return spacesPage.getStatusOfSpace(spaceName);
        },
        { timeout: 30_000 },
      )
      .toContain('已停止');

    expect(await spacesPage.hasRowAction(spaceName, '启动')).toBe(true);
    expect(await spacesPage.hasRowAction(spaceName, '删除')).toBe(true);
  });

  test('6. UI 重新启动空间 → 状态恢复运行中', async ({ page }) => {
    const spacesPage = new SpacesPage(page);
    await loginViaUI(page);
    await spacesPage.goto();
    await spacesPage.waitForPageReady();

    await spacesPage.clickRowAction(spaceName, '启动');

    await expect
      .poll(
        async () => {
          return spacesPage.getStatusOfSpace(spaceName);
        },
        { timeout: 60_000 },
      )
      .toContain('运行中');
  });

  test('7. API 验证: running 状态不能直接删除 (409)', async ({ request }) => {
    const res = await request.delete(`/api/v1/spaces/${spaceId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status()).toBe(409);
  });

  test('8. UI 停止后删除空间 → 从列表消失', async ({ page }) => {
    const spacesPage = new SpacesPage(page);
    await loginViaUI(page);
    await spacesPage.goto();
    await spacesPage.waitForPageReady();

    // 停止
    await spacesPage.clickRowAction(spaceName, '停止');
    await expect
      .poll(async () => spacesPage.getStatusOfSpace(spaceName), {
        timeout: 30_000,
      })
      .toContain('已停止');

    // 删除（带确认弹窗）
    await spacesPage.deleteSpace(spaceName);

    // 从列表消失
    await expect
      .poll(async () => spacesPage.hasSpace(spaceName), { timeout: 30_000 })
      .toBe(false);
  });

  test('9. API 验证: 删除后详情返回 404', async ({ request }) => {
    const res = await request.get(`/api/v1/spaces/${spaceId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status()).toBe(404);
  });
});

test.describe('开发空间 - 远程 API 契约验证', () => {
  test.skip(!isRemote, '此组测试仅在远程模式下运行');

  let token = '';

  test.beforeAll(async ({ request }) => {
    token = await apiLogin(request);
  });

  test('未认证请求返回 401', async ({ request }) => {
    const res = await request.get('/api/v1/spaces');
    expect(res.status()).toBe(401);
  });

  test('列表响应契约: items/total/page/page_size/total_pages', async ({
    request,
  }) => {
    const res = await request.get('/api/v1/spaces?page=1&page_size=5', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBe(true);
    const data = await res.json();
    expect(data).toHaveProperty('items');
    expect(data).toHaveProperty('total');
    expect(data).toHaveProperty('page', 1);
    expect(data).toHaveProperty('page_size', 5);
    expect(data).toHaveProperty('total_pages');
    expect(Array.isArray(data.items)).toBe(true);
    if (data.items.length > 0) {
      const item = data.items[0];
      for (const field of [
        'id',
        'space_name',
        'owner_id',
        'instance_type',
        'space_type',
        'status',
        'created_at',
      ]) {
        expect(item, `列表项缺少字段 ${field}`).toHaveProperty(field);
      }
    }
  });

  test('创建请求验证: 非法实例类型返回 422', async ({ request }) => {
    const res = await request.post('/api/v1/spaces', {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        space_name: generateTestSpaceName('e2e-invalid'),
        instance_type: 'ml.nonexistent.型号',
      },
    });
    expect(res.status()).toBe(422);
  });

  test('创建请求验证: 名称过短返回 422', async ({ request }) => {
    const res = await request.post('/api/v1/spaces', {
      headers: { Authorization: `Bearer ${token}` },
      data: { space_name: 'ab' },
    });
    expect(res.status()).toBe(422);
  });

  test('创建请求验证: 存储越界返回 422', async ({ request }) => {
    const res = await request.post('/api/v1/spaces', {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        space_name: generateTestSpaceName('e2e-storage'),
        storage_size_gb: 9999,
      },
    });
    expect(res.status()).toBe(422);
  });

  test('不存在的空间详情返回 404', async ({ request }) => {
    const res = await request.get(
      '/api/v1/spaces/00000000-0000-0000-0000-000000000000',
      { headers: { Authorization: `Bearer ${token}` } },
    );
    expect(res.status()).toBe(404);
  });

  test('不存在的空间 start 返回 404', async ({ request }) => {
    const res = await request.post(
      '/api/v1/spaces/00000000-0000-0000-0000-000000000000/start',
      { headers: { Authorization: `Bearer ${token}` } },
    );
    expect(res.status()).toBe(404);
  });

  test('状态过滤参数生效', async ({ request }) => {
    const res = await request.get('/api/v1/spaces?status=running', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.ok()).toBe(true);
    const data = await res.json();
    for (const item of data.items) {
      expect(item.status).toBe('running');
    }
  });

  test('非法状态过滤参数返回 422', async ({ request }) => {
    const res = await request.get('/api/v1/spaces?status=不存在的状态', {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(res.status()).toBe(422);
  });
});

test.describe('开发空间 - 遗留资源清理', () => {
  test.skip(!isRemote, '此组测试仅在远程模式下运行');

  test('清理所有 e2e- 前缀的测试空间', async ({ request }) => {
    const token = await apiLogin(request);
    const headers = { Authorization: `Bearer ${token}` };

    const res = await request.get('/api/v1/spaces?page=1&page_size=100', {
      headers,
    });
    expect(res.ok()).toBe(true);
    const list = await res.json();

    const leftovers = list.items.filter((s: { space_name: string }) =>
      s.space_name.startsWith('e2e-'),
    );

    for (const space of leftovers) {
      await forceCleanupSpace(request, token, space.id);
    }
  });
});
