/**
 * 开发空间 (Spaces) - CRUD 操作 E2E 测试 (Mock 模式)
 *
 * 测试对象: /spaces 列表页 + /spaces/create 创建页的全部交互
 * 覆盖: 列表展示/过滤/空态/错误态、创建表单验证与提交契约、
 *       启动/停止/删除生命周期操作、删除确认弹窗、名称导航
 *
 * Mock 模式:  npx playwright test e2e/tests/spaces-crud.spec.ts
 * (远程模式测试见 spaces-remote.spec.ts)
 */

import { test, expect, Page } from '@playwright/test';
import { SpacesPage } from '../pages/SpacesPage';
import { loginViaUI } from '../utils/auth';
import {
  mockSpaces,
  createSpaceListResponse,
  filterSpacesByStatus,
  getMockSpaceDetail,
} from '../fixtures/spaces';

const isRemote = !!process.env.E2E_BASE_URL;

// UUID 形状的路径段
const SPACE_DETAIL_RE = /\/api\/v1\/spaces\/[0-9a-f-]{36}$/;
const SPACE_ACTION_RE = /\/api\/v1\/spaces\/[0-9a-f-]{36}\/(start|stop)$/;
const SPACE_LIST_RE = /\/api\/v1\/spaces(\?.*)?$/;

/**
 * Mock 认证 API（契约对齐 LoginResponse: {tokens, user}）
 */
async function setupAuthMocks(page: Page) {
  const user = {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    display_name: '管理员',
    role: 'admin',
    status: 'active',
  };

  await page.route('**/api/v1/auth/login', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        tokens: {
          access_token: 'mock-access-token',
          refresh_token: 'mock-refresh-token',
          token_type: 'bearer',
          expires_in: 1800,
        },
        user,
      }),
    });
  });

  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(user),
    });
  });

  await page.route('**/api/v1/auth/token/refresh', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'mock-access-token-2',
        refresh_token: 'mock-refresh-token-2',
        token_type: 'bearer',
        expires_in: 1800,
      }),
    });
  });
}

/**
 * Mock Spaces 列表/详情/操作 API
 */
async function setupSpacesMocks(page: Page) {
  // 列表 + 创建
  await page.route(SPACE_LIST_RE, async (route) => {
    const request = route.request();

    if (request.method() === 'GET') {
      const url = new URL(request.url());
      const pageNum = parseInt(url.searchParams.get('page') || '1');
      const pageSize = parseInt(url.searchParams.get('page_size') || '20');
      const status = url.searchParams.get('status');

      const items = status ? filterSpacesByStatus(status) : mockSpaces;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(createSpaceListResponse(items, pageNum, pageSize)),
      });
      return;
    }

    if (request.method() === 'POST') {
      const body = request.postDataJSON();
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '99999999-9999-9999-9999-999999999999',
          space_name: body.space_name,
          owner_id: 1,
          instance_type: body.instance_type || 'ml.g5.xlarge',
          space_type: body.space_type || 'jupyter',
          status: 'pending',
          storage_size_gb: body.storage_size_gb ?? 20,
          lifecycle_config_arn: null,
          sagemaker_space_arn: null,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          deleted_at: null,
        }),
      });
      return;
    }

    await route.fallback();
  });

  // 详情 + 删除
  await page.route(SPACE_DETAIL_RE, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const id = url.pathname.split('/').pop()!;

    if (request.method() === 'GET') {
      const space = getMockSpaceDetail(id);
      if (!space) {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({
            http_status: 404,
            error_code: 'SPACE_NOT_FOUND',
            message: `Space '${id}' not found`,
          }),
        });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(space),
      });
      return;
    }

    if (request.method() === 'DELETE') {
      await route.fulfill({ status: 204, body: '' });
      return;
    }

    await route.fallback();
  });

  // 启动/停止操作
  await page.route(SPACE_ACTION_RE, async (route) => {
    const request = route.request();
    if (request.method() !== 'POST') {
      await route.fallback();
      return;
    }
    const url = new URL(request.url());
    const parts = url.pathname.split('/');
    const action = parts.pop()!;
    const id = parts.pop()!;
    const space = getMockSpaceDetail(id) || mockSpaces[0];

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        ...space,
        status: action === 'start' ? 'running' : 'stopped',
        updated_at: new Date().toISOString(),
      }),
    });
  });
}

test.describe('开发空间 - 列表展示 (Mock 模式)', () => {
  test.skip(isRemote, '此组测试仅在 Mock 模式下运行');

  let spacesPage: SpacesPage;

  test.beforeEach(async ({ page }) => {
    await setupAuthMocks(page);
    await setupSpacesMocks(page);
    spacesPage = new SpacesPage(page);
    await loginViaUI(page);
    await spacesPage.goto();
    await spacesPage.waitForPageReady();
  });

  test('页面标题和创建按钮可见', async () => {
    await expect(spacesPage.pageTitle).toBeVisible();
    await expect(spacesPage.createButton).toBeVisible();
    await expect(spacesPage.refreshButton).toBeVisible();
  });

  test('表格列头完整', async () => {
    await spacesPage.verifyTableHeaders();
  });

  test('表格显示全部 Mock 数据', async () => {
    const rowCount = await spacesPage.getRowCount();
    expect(rowCount).toBe(mockSpaces.length);

    const names = await spacesPage.getAllSpaceNames();
    expect(names).toContain('running-jupyter-space');
    expect(names).toContain('stopped-vscode-space');
    expect(names).toContain('pending-new-space');
    expect(names).toContain('failed-rstudio-space');
  });

  test('状态徽章中文文案正确', async () => {
    expect(await spacesPage.getStatusOfSpace('running-jupyter-space')).toContain('运行中');
    expect(await spacesPage.getStatusOfSpace('stopped-vscode-space')).toContain('已停止');
    expect(await spacesPage.getStatusOfSpace('pending-new-space')).toContain('创建中');
    expect(await spacesPage.getStatusOfSpace('failed-rstudio-space')).toContain('失败');
  });

  test('IDE 类型显示中文标签', async () => {
    await expect(
      spacesPage.rowByName('running-jupyter-space').getByText('JupyterLab'),
    ).toBeVisible();
    await expect(
      spacesPage.rowByName('stopped-vscode-space').getByText('Code Editor (VS Code)'),
    ).toBeVisible();
  });

  test('空列表显示空状态和引导按钮', async ({ page }) => {
    await page.route(SPACE_LIST_RE, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createSpaceListResponse([], 1, 20)),
        });
        return;
      }
      await route.fallback();
    });

    await spacesPage.goto();
    await expect(spacesPage.emptyState).toBeVisible();
  });

  test('API 错误显示错误提示和重试按钮', async ({ page }) => {
    await page.route(SPACE_LIST_RE, async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: '服务器内部错误' }),
        });
        return;
      }
      await route.fallback();
    });

    await spacesPage.goto();
    await expect(spacesPage.errorAlert).toBeVisible();
    await expect(spacesPage.page.getByRole('button', { name: '重试' })).toBeVisible();
  });

  test('按状态过滤 - 运行中', async ({ page }) => {
    await spacesPage.filterByStatus('运行中');

    // 等待过滤后的请求完成
    await page.waitForTimeout(500);
    const names = await spacesPage.getAllSpaceNames();
    expect(names).toContain('running-jupyter-space');
    expect(names).not.toContain('stopped-vscode-space');
  });

  test('点击空间名称导航到详情且不出现 404', async ({ page }) => {
    await spacesPage.clickSpaceName('running-jupyter-space');
    await page.waitForLoadState('networkidle');

    // 不应跳到 404 错误页
    await expect(page.getByText('页面未找到')).not.toBeVisible();
    expect(page.url()).toContain('/spaces/11111111-1111-1111-1111-111111111111');
  });
});

test.describe('开发空间 - 操作按钮条件渲染 (Mock 模式)', () => {
  test.skip(isRemote, '此组测试仅在 Mock 模式下运行');

  let spacesPage: SpacesPage;

  test.beforeEach(async ({ page }) => {
    await setupAuthMocks(page);
    await setupSpacesMocks(page);
    spacesPage = new SpacesPage(page);
    await loginViaUI(page);
    await spacesPage.goto();
    await spacesPage.waitForPageReady();
  });

  test('running 行只显示停止按钮', async () => {
    expect(await spacesPage.hasRowAction('running-jupyter-space', '停止')).toBe(true);
    expect(await spacesPage.hasRowAction('running-jupyter-space', '启动')).toBe(false);
    expect(await spacesPage.hasRowAction('running-jupyter-space', '删除')).toBe(false);
  });

  test('stopped 行显示启动和删除按钮', async () => {
    expect(await spacesPage.hasRowAction('stopped-vscode-space', '启动')).toBe(true);
    expect(await spacesPage.hasRowAction('stopped-vscode-space', '删除')).toBe(true);
    expect(await spacesPage.hasRowAction('stopped-vscode-space', '停止')).toBe(false);
  });

  test('failed 行显示删除按钮', async () => {
    expect(await spacesPage.hasRowAction('failed-rstudio-space', '删除')).toBe(true);
    expect(await spacesPage.hasRowAction('failed-rstudio-space', '启动')).toBe(false);
  });
});

test.describe('开发空间 - 生命周期操作 (Mock 模式)', () => {
  test.skip(isRemote, '此组测试仅在 Mock 模式下运行');

  let spacesPage: SpacesPage;

  test.beforeEach(async ({ page }) => {
    await setupAuthMocks(page);
    await setupSpacesMocks(page);
    spacesPage = new SpacesPage(page);
    await loginViaUI(page);
    await spacesPage.goto();
    await spacesPage.waitForPageReady();
  });

  test('启动 stopped 空间调用 start API', async ({ page }) => {
    let startCalled = false;
    await page.route(SPACE_ACTION_RE, async (route) => {
      if (route.request().url().endsWith('/start')) {
        startCalled = true;
        const space = getMockSpaceDetail('22222222-2222-2222-2222-222222222222')!;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...space, status: 'running' }),
        });
        return;
      }
      await route.fallback();
    });

    await spacesPage.clickRowAction('stopped-vscode-space', '启动');
    await expect.poll(() => startCalled, { timeout: 5000 }).toBe(true);
  });

  test('停止 running 空间调用 stop API', async ({ page }) => {
    let stopCalled = false;
    await page.route(SPACE_ACTION_RE, async (route) => {
      if (route.request().url().endsWith('/stop')) {
        stopCalled = true;
        const space = getMockSpaceDetail('11111111-1111-1111-1111-111111111111')!;
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ ...space, status: 'stopped' }),
        });
        return;
      }
      await route.fallback();
    });

    await spacesPage.clickRowAction('running-jupyter-space', '停止');
    await expect.poll(() => stopCalled, { timeout: 5000 }).toBe(true);
  });

  test('删除空间显示确认弹窗并调用 DELETE API', async ({ page }) => {
    let deleteCalled = false;
    await page.route(SPACE_DETAIL_RE, async (route) => {
      if (route.request().method() === 'DELETE') {
        deleteCalled = true;
        await route.fulfill({ status: 204, body: '' });
        return;
      }
      await route.fallback();
    });

    await spacesPage.clickRowAction('stopped-vscode-space', '删除');
    await expect(spacesPage.deleteModal).toBeVisible();
    await expect(
      spacesPage.deleteModal.getByText(/stopped-vscode-space/),
    ).toBeVisible();

    await spacesPage.confirmDeleteButton.click();
    await expect.poll(() => deleteCalled, { timeout: 5000 }).toBe(true);
  });

  test('删除弹窗点击取消不调用 DELETE API', async ({ page }) => {
    let deleteCalled = false;
    await page.route(SPACE_DETAIL_RE, async (route) => {
      if (route.request().method() === 'DELETE') {
        deleteCalled = true;
        await route.fulfill({ status: 204, body: '' });
        return;
      }
      await route.fallback();
    });

    await spacesPage.clickRowAction('stopped-vscode-space', '删除');
    await expect(spacesPage.deleteModal).toBeVisible();
    await spacesPage.cancelDeleteButton.click();
    await expect(spacesPage.deleteModal).not.toBeVisible();

    expect(deleteCalled).toBe(false);
  });
});

test.describe('开发空间 - 创建表单 (Mock 模式)', () => {
  test.skip(isRemote, '此组测试仅在 Mock 模式下运行');

  let spacesPage: SpacesPage;

  test.beforeEach(async ({ page }) => {
    await setupAuthMocks(page);
    await setupSpacesMocks(page);
    spacesPage = new SpacesPage(page);
    await loginViaUI(page);
    await spacesPage.gotoCreate();
  });

  test('创建页默认值正确', async ({ page }) => {
    await expect(page.getByRole('heading', { name: '创建开发空间' }).first()).toBeVisible();
    // 默认 IDE 类型 JupyterLab、实例 ml.g5.xlarge、存储 10GB
    await expect(page.getByText('JupyterLab').first()).toBeVisible();
    await expect(page.getByText(/ml\.g5\.xlarge/).first()).toBeVisible();
    await expect(spacesPage.storageInput).toHaveValue('10');
  });

  test('名称为空提交显示错误', async () => {
    await spacesPage.fillCreateForm({ name: '' });
    await spacesPage.submitCreateForm();
    expect(await spacesPage.hasFormError('请输入空间名称')).toBe(true);
  });

  test('名称少于 3 字符显示错误', async () => {
    await spacesPage.fillCreateForm({ name: 'ab' });
    await spacesPage.submitCreateForm();
    expect(await spacesPage.hasFormError('空间名称至少 3 个字符')).toBe(true);
  });

  test('名称含非法字符显示错误', async () => {
    await spacesPage.fillCreateForm({ name: 'My_Space!' });
    await spacesPage.submitCreateForm();
    expect(
      await spacesPage.hasFormError(/只能包含小写字母、数字和连字符/),
    ).toBe(true);
  });

  test('存储大小越界显示错误', async () => {
    await spacesPage.fillCreateForm({ name: 'valid-name', storageGb: '600' });
    await spacesPage.submitCreateForm();
    expect(
      await spacesPage.hasFormError('存储大小必须在 5-500 GB 之间'),
    ).toBe(true);
  });

  test('合法表单提交 - 请求体契约正确并跳转回列表', async ({ page }) => {
    let createBody: Record<string, unknown> = {};
    await page.route(SPACE_LIST_RE, async (route) => {
      const request = route.request();
      if (request.method() === 'POST') {
        createBody = request.postDataJSON();
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: '99999999-9999-9999-9999-999999999999',
            space_name: createBody.space_name,
            owner_id: 1,
            instance_type: createBody.instance_type,
            space_type: createBody.space_type,
            status: 'pending',
            storage_size_gb: createBody.storage_size_gb,
            lifecycle_config_arn: null,
            sagemaker_space_arn: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            deleted_at: null,
          }),
        });
        return;
      }
      if (request.method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(createSpaceListResponse(mockSpaces, 1, 20)),
        });
        return;
      }
      await route.fallback();
    });

    await spacesPage.fillCreateForm({
      name: 'my-e2e-space',
      spaceTypeLabel: 'Code Editor (VS Code)',
      instanceTypeLabel: 'ml.t3.medium (2 vCPU, 4 GB)',
      storageGb: '50',
    });
    await spacesPage.submitCreateForm();

    // 跳转回列表页
    await page.waitForURL(/\/spaces$/, { timeout: 10000 });

    // 请求体契约校验（snake_case + 正确类型）
    expect(createBody.space_name).toBe('my-e2e-space');
    expect(createBody.space_type).toBe('vscode');
    expect(createBody.instance_type).toBe('ml.t3.medium');
    expect(createBody.storage_size_gb).toBe(50);
  });

  test('创建失败 (409 重名) 显示错误信息', async ({ page }) => {
    await page.route(SPACE_LIST_RE, async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 409,
          contentType: 'application/json',
          body: JSON.stringify({
            http_status: 409,
            error_code: 'DUPLICATE_SPACE_NAME',
            message: "Space 'dup-space' already exists for this owner",
          }),
        });
        return;
      }
      await route.fallback();
    });

    await spacesPage.fillCreateForm({ name: 'dup-space' });
    await spacesPage.submitCreateForm();

    await expect(spacesPage.page.getByText(/创建失败/)).toBeVisible({
      timeout: 5000,
    });
    // 仍停留在创建页
    expect(spacesPage.page.url()).toContain('/spaces/create');
  });

  test('取消按钮返回列表页', async ({ page }) => {
    await spacesPage.cancelButton.click();
    await page.waitForURL(/\/spaces$/, { timeout: 5000 });
  });
});
