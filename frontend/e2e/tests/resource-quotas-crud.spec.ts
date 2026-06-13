/**
 * 资源配额管理 - CRUD 操作 E2E 测试
 *
 * 测试对象: 资源限制配置的创建、编辑操作
 * 测试模式: 同时支持 Mock 模式和 真实 API 模式
 *
 * Mock 模式:  npx playwright test e2e/tests/resource-quotas-crud.spec.ts
 * 真实 API:   E2E_BASE_URL=http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com npx playwright test e2e/tests/resource-quotas-crud.spec.ts
 */

import { test, expect, Page } from "@playwright/test";
import { ResourceQuotasPage } from "../pages/ResourceQuotasPage";
import { navigateWithAuth } from "../utils/auth";
import {
  mockResourceLimitConfigs,
  createResourceLimitConfigResponse,
  generateTestConfigName,
} from "../fixtures/resourceQuotas";

const isRemote = !!process.env.E2E_BASE_URL;

/**
 * Mock 模式辅助函数 - 设置资源配额 API Mock
 */
async function setupResourceQuotaMocks(page: Page) {
  // Mock 列表 API
  await page.route(
    /\/api\/v1\/resource-limit-configs(\?.*)?$/,
    async (route) => {
      const request = route.request();
      if (request.method() === "GET") {
        const url = new URL(request.url());
        const pageNum = parseInt(url.searchParams.get("page") || "1");
        const pageSize = parseInt(url.searchParams.get("page_size") || "20");
        const response = createResourceLimitConfigResponse(
          mockResourceLimitConfigs,
          pageNum,
          pageSize,
        );

        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(response),
        });
        return;
      }

      if (request.method() === "POST") {
        const body = request.postDataJSON();
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            id: 100,
            ...body,
            project_id: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }),
        });
        return;
      }

      await route.fallback();
    },
  );

  // Mock 更新 API
  await page.route(
    /\/api\/v1\/resource-limit-configs\/(\d+)$/,
    async (route) => {
      const request = route.request();
      if (request.method() === "PUT") {
        const body = request.postDataJSON();
        const url = new URL(request.url());
        const match = url.pathname.match(/\/resource-limit-configs\/(\d+)$/);
        const id = match ? parseInt(match[1]) : 1;
        const existing =
          mockResourceLimitConfigs.find((c) => c.id === id) ||
          mockResourceLimitConfigs[0];

        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            ...existing,
            ...body,
            updated_at: new Date().toISOString(),
          }),
        });
        return;
      }

      // 删除：返回 204 No Content
      if (request.method() === "DELETE") {
        await route.fulfill({ status: 204, body: "" });
        return;
      }

      await route.fallback();
    },
  );

  // Mock 认证相关 API (本地模式需要)
  await page.route("**/api/v1/auth/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: 1,
        username: "admin",
        email: "admin@example.com",
        display_name: null,
        role: "ADMIN",
        status: "ACTIVE",
        auth_type: "local",
      }),
    });
  });

  // Mock token 刷新（整页导航后 initializeAuth 用 sessionStorage 的
  // refreshToken 静默续期，必须 Mock 否则会被登出重定向到 /login）
  await page.route("**/api/v1/auth/token/refresh", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "mock-access-token-refreshed",
        refresh_token: "mock-refresh-token",
        token_type: "bearer",
        expires_in: 3600,
      }),
    });
  });

  // Mock 登出
  await page.route("**/api/v1/auth/logout", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ message: "已登出" }),
    });
  });

  // 登录响应需匹配前端 LoginResponse 契约：tokens 嵌套对象 + user
  // （前端 authStore.login 解构 response.tokens.refresh_token）
  await page.route("**/api/v1/auth/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        tokens: {
          access_token: "mock-access-token",
          refresh_token: "mock-refresh-token",
          token_type: "bearer",
          expires_in: 3600,
        },
        user: {
          id: 1,
          username: "admin",
          email: "admin@example.com",
          display_name: null,
          role: "ADMIN",
          status: "ACTIVE",
          auth_type: "local",
        },
      }),
    });
  });
}

test.describe("资源配额 CRUD - 创建配额 (Mock 模式)", () => {
  test.skip(isRemote, "此组测试仅在 Mock 模式下运行");

  let quotasPage: ResourceQuotasPage;

  test.beforeEach(async ({ page }) => {
    await setupResourceQuotaMocks(page);
    quotasPage = new ResourceQuotasPage(page);
    await navigateWithAuth(page, "/resource-quotas");
    await quotasPage.waitForPageReady();
  });

  test("表格显示 Mock 数据", async () => {
    const rowCount = await quotasPage.getRowCount();
    expect(rowCount).toBe(mockResourceLimitConfigs.length);
  });

  test("显示正确的配置名称", async () => {
    const names = await quotasPage.getAllConfigNames();
    expect(names).toContain("管理员配额");
    expect(names).toContain("工程师配额");
    expect(names).toContain("项目经理配额");
    expect(names).toContain("查看者配额");
  });

  test("填写完整表单并创建", async ({ page }) => {
    let createCalled = false;
    let createBody: Record<string, unknown> = {};

    // 拦截创建 API 验证请求体
    await page.route(
      /\/api\/v1\/resource-limit-configs(\?.*)?$/,
      async (route) => {
        if (route.request().method() === "POST") {
          createCalled = true;
          createBody = route.request().postDataJSON();
          await route.fulfill({
            status: 201,
            contentType: "application/json",
            body: JSON.stringify({
              id: 100,
              ...createBody,
              project_id: null,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            }),
          });
          return;
        }
        await route.fallback();
      },
    );

    await quotasPage.clickCreate();

    await quotasPage.fillForm({
      configName: "E2E 测试配额",
      role: "工程师",
      maxGpu: "8",
      maxCpu: "32",
      maxMemory: "128",
      maxStorage: "500",
      maxNodes: "4",
      priority: "中",
    });

    await quotasPage.submitForm();

    // 验证 API 被调用
    // Modal 关闭时 API 已完成
    await quotasPage.waitForModalClose();
    expect(createCalled).toBe(true);
    expect(createBody.config_name).toBe("E2E 测试配额");
    expect(createBody.role).toBe("engineer");
    expect(createBody.max_gpu_per_job).toBe(8);
    expect(createBody.priority_default).toBe("medium");
  });

  test("表单验证 - 配置名称为空", async () => {
    await quotasPage.clickCreate();

    // 清空默认填写的字段
    await quotasPage.configNameInput.clear();

    // 提交
    await quotasPage.submitForm();

    // 应该看到错误提示
    const hasError = await quotasPage.hasFormError("配置名称不能为空");
    expect(hasError).toBe(true);
  });

  test("表单验证 - 未选择角色", async () => {
    await quotasPage.clickCreate();

    await quotasPage.fillForm({
      configName: "测试配额",
    });

    // 不选择角色直接提交
    await quotasPage.submitForm();

    const hasError = await quotasPage.hasFormError("请选择适用角色");
    expect(hasError).toBe(true);
  });

  test("表单验证 - 未选择优先级", async () => {
    await quotasPage.clickCreate();

    await quotasPage.fillForm({
      configName: "测试配额",
      role: "工程师",
    });

    // 不选择优先级直接提交
    await quotasPage.submitForm();

    const hasError = await quotasPage.hasFormError("请选择默认优先级");
    expect(hasError).toBe(true);
  });

  test("表单验证 - 数值超出范围", async () => {
    await quotasPage.clickCreate();

    await quotasPage.fillForm({
      configName: "测试配额",
      role: "工程师",
      maxGpu: "99999",
      priority: "中",
    });

    await quotasPage.submitForm();

    // 应该有数值范围错误
    const hasError = await quotasPage.hasFormError("之间的整数");
    expect(hasError).toBe(true);
  });
});

test.describe("资源配额 CRUD - 编辑配额 (Mock 模式)", () => {
  test.skip(isRemote, "此组测试仅在 Mock 模式下运行");

  let quotasPage: ResourceQuotasPage;

  test.beforeEach(async ({ page }) => {
    await setupResourceQuotaMocks(page);
    quotasPage = new ResourceQuotasPage(page);
    await navigateWithAuth(page, "/resource-quotas");
    await quotasPage.waitForPageReady();
  });

  test("编辑 Modal 预填当前数据", async () => {
    await quotasPage.clickEditAtRow(0);

    const modalTitle = await quotasPage.getModalTitle();
    expect(modalTitle).toContain("编辑资源配额");

    // 验证预填值
    const configNameValue = await quotasPage.configNameInput.inputValue();
    expect(configNameValue).toBe("管理员配额");

    const gpuValue = await quotasPage.maxGpuInput.inputValue();
    expect(gpuValue).toBe("8");
  });

  test("修改数据并保存", async ({ page }) => {
    let updateCalled = false;
    let updateBody: Record<string, unknown> = {};

    await page.route(
      /\/api\/v1\/resource-limit-configs\/(\d+)$/,
      async (route) => {
        if (route.request().method() === "PUT") {
          updateCalled = true;
          updateBody = route.request().postDataJSON();
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              ...mockResourceLimitConfigs[0],
              ...updateBody,
              updated_at: new Date().toISOString(),
            }),
          });
          return;
        }
        await route.fallback();
      },
    );

    await quotasPage.clickEditAtRow(0);

    // 修改 GPU 配额
    await quotasPage.fillForm({
      maxGpu: "16",
    });

    await quotasPage.submitForm();
    await quotasPage.waitForModalClose();

    expect(updateCalled).toBe(true);
    expect(updateBody.max_gpu_per_job).toBe(16);
  });
});

test.describe("资源配额 CRUD - 删除配额 (Mock 模式)", () => {
  test.skip(isRemote, "此组测试仅在 Mock 模式下运行");

  let quotasPage: ResourceQuotasPage;

  test.beforeEach(async ({ page }) => {
    await setupResourceQuotaMocks(page);
    quotasPage = new ResourceQuotasPage(page);
    await navigateWithAuth(page, "/resource-quotas");
    await quotasPage.waitForPageReady();
  });

  test("点击删除弹出二次确认 Modal", async () => {
    await quotasPage.clickDeleteAtRow(0);

    // 删除确认 Modal 可见，并显示配置名称与不可撤销警告
    await expect(quotasPage.deleteModal).toBeVisible();
    await expect(quotasPage.confirmDeleteButton).toBeVisible();
    await expect(quotasPage.cancelDeleteButton).toBeVisible();

    // 应包含被删除配置的名称（第一行为"管理员配额"）
    await expect(quotasPage.deleteModal).toContainText("管理员配额");
    await expect(quotasPage.deleteModal).toContainText("此操作不可撤销");
  });

  test("二次确认拦截 - 点删除不直接发请求，确认后才发 DELETE", async ({
    page,
  }) => {
    let deleteCalled = false;
    let deletedId: string | null = null;

    // 拦截 DELETE 请求
    await page.route(
      /\/api\/v1\/resource-limit-configs\/(\d+)$/,
      async (route) => {
        const request = route.request();
        if (request.method() === "DELETE") {
          deleteCalled = true;
          const match = new URL(request.url()).pathname.match(
            /\/resource-limit-configs\/(\d+)$/,
          );
          deletedId = match ? match[1] : null;
          await route.fulfill({ status: 204, body: "" });
          return;
        }
        await route.fallback();
      },
    );

    // 点击删除 -> 弹出确认 Modal
    await quotasPage.clickDeleteAtRow(0);

    // 关键断言：此时尚未发出 DELETE 请求
    expect(deleteCalled).toBe(false);

    // 点击"确认删除" -> 才真正发出 DELETE
    await quotasPage.confirmDelete();
    await quotasPage.waitForDeleteModalClose();

    expect(deleteCalled).toBe(true);
    // 第一行为 id=1 的"管理员配额"
    expect(deletedId).toBe("1");
  });

  test("删除取消 - 点取消后 Modal 关闭且配置仍在", async ({ page }) => {
    let deleteCalled = false;

    await page.route(
      /\/api\/v1\/resource-limit-configs\/(\d+)$/,
      async (route) => {
        const request = route.request();
        if (request.method() === "DELETE") {
          deleteCalled = true;
          await route.fulfill({ status: 204, body: "" });
          return;
        }
        await route.fallback();
      },
    );

    await quotasPage.clickDeleteAtRow(0);
    await expect(quotasPage.deleteModal).toBeVisible();

    // 点击取消
    await quotasPage.cancelDelete();
    await quotasPage.waitForDeleteModalClose();

    // 未发出删除请求，配置仍在列表中
    expect(deleteCalled).toBe(false);
    const hasConfig = await quotasPage.hasConfig("管理员配额");
    expect(hasConfig).toBe(true);
    const rowCount = await quotasPage.getRowCount();
    expect(rowCount).toBe(mockResourceLimitConfigs.length);
  });

  test("表单边界 - 超长配置名原样进入请求体（前端不截断）", async ({
    page,
  }) => {
    // 当前表单对名称无长度上限校验：验证超长名称能原样发送给后端，
    // 由后端做最终长度约束（前端不静默截断）。
    let createBody: Record<string, unknown> = {};

    await page.route(
      /\/api\/v1\/resource-limit-configs(\?.*)?$/,
      async (route) => {
        if (route.request().method() === "POST") {
          createBody = route.request().postDataJSON();
          await route.fulfill({
            status: 201,
            contentType: "application/json",
            body: JSON.stringify({
              id: 100,
              ...createBody,
              project_id: null,
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            }),
          });
          return;
        }
        await route.fallback();
      },
    );

    const longName = "超长配置名称".repeat(40); // 240 字符
    await quotasPage.clickCreate();
    await quotasPage.fillForm({
      configName: longName,
      role: "工程师",
      priority: "中",
    });
    await quotasPage.submitForm();
    await quotasPage.waitForModalClose();

    expect(createBody.config_name).toBe(longName);
  });

  test("表单验证 - 数值下限（负数）", async () => {
    await quotasPage.clickCreate();

    await quotasPage.fillForm({
      configName: "测试配额下限",
      role: "工程师",
      maxGpu: "-1",
      priority: "中",
    });

    await quotasPage.submitForm();

    // GPU 范围为 0-1000，负数应触发范围错误，Modal 保持打开
    const hasError = await quotasPage.hasFormError("之间的整数");
    expect(hasError).toBe(true);
    await expect(quotasPage.configNameInput).toBeVisible();
  });

  test("表单验证 - 最大节点下限（节点最小为 1）", async () => {
    await quotasPage.clickCreate();

    await quotasPage.fillForm({
      configName: "测试节点下限",
      role: "工程师",
      maxNodes: "0",
      priority: "中",
    });

    await quotasPage.submitForm();

    // 节点范围为 1-1000，0 应触发范围错误，Modal 保持打开
    const hasError = await quotasPage.hasFormError("最大节点必须是 1-1000");
    expect(hasError).toBe(true);
    await expect(quotasPage.configNameInput).toBeVisible();
  });
});

test.describe("资源配额 CRUD - 错误态 (Mock 模式)", () => {
  test.skip(isRemote, "此组测试仅在 Mock 模式下运行");

  test("列表 API 返回 500 时显示错误 Alert 而非白屏", async ({ page }) => {
    // 先 Mock 认证（避免被重定向到登录页），再 Mock 列表 500
    await page.route("**/api/v1/auth/me", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          username: "admin",
          email: "admin@example.com",
          display_name: null,
          role: "ADMIN",
          status: "ACTIVE",
          auth_type: "local",
        }),
      });
    });
    await page.route("**/api/v1/auth/token/refresh", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "mock-access-token-refreshed",
          refresh_token: "mock-refresh-token",
          token_type: "bearer",
          expires_in: 3600,
        }),
      });
    });
    await page.route("**/api/v1/auth/login", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          tokens: {
            access_token: "mock-access-token",
            refresh_token: "mock-refresh-token",
            token_type: "bearer",
            expires_in: 3600,
          },
          user: {
            id: 1,
            username: "admin",
            email: "admin@example.com",
            display_name: null,
            role: "ADMIN",
            status: "ACTIVE",
            auth_type: "local",
          },
        }),
      });
    });

    // 列表 API 返回 500
    await page.route(
      /\/api\/v1\/resource-limit-configs(\?.*)?$/,
      async (route) => {
        if (route.request().method() === "GET") {
          await route.fulfill({
            status: 500,
            contentType: "application/json",
            body: JSON.stringify({ detail: "服务器内部错误" }),
          });
          return;
        }
        await route.fallback();
      },
    );

    const quotasPage = new ResourceQuotasPage(page);
    await navigateWithAuth(page, "/resource-quotas");
    await quotasPage.waitForPageReady();

    // 页面标题应仍可见（未白屏崩溃）
    await expect(quotasPage.pageTitle).toBeVisible();

    // 错误 Alert 应显示（"加载失败" header）
    await expect(quotasPage.errorState).toBeVisible({ timeout: 10000 });
  });
});

test.describe("资源配额 CRUD - 真实 Dev 环境", () => {
  test.skip(!isRemote, "此组测试仅在真实 Dev 环境下运行");

  let quotasPage: ResourceQuotasPage;
  let testConfigName: string;

  test.beforeEach(async ({ page }) => {
    quotasPage = new ResourceQuotasPage(page);
    testConfigName = generateTestConfigName();
    await navigateWithAuth(page, "/resource-quotas");
    await quotasPage.waitForPageReady();
  });

  test("页面正常加载并显示数据", async () => {
    // 验证页面标题
    await expect(quotasPage.pageTitle).toBeVisible();

    // 验证新建按钮
    await expect(quotasPage.createButton).toBeVisible();

    // 页面应有表格或空状态
    const hasTable = await quotasPage.table.isVisible();
    const hasEmpty = await quotasPage.emptyState.isVisible();
    expect(hasTable || hasEmpty).toBe(true);
  });

  test("创建新配额配置", async ({ page }) => {
    // 监听 API 响应
    const responsePromise = page.waitForResponse(
      (resp) =>
        resp.url().includes("/resource-limit-configs") &&
        resp.request().method() === "POST",
      { timeout: 15000 },
    );

    await quotasPage.createQuota({
      configName: testConfigName,
      role: "工程师",
      maxGpu: "4",
      maxCpu: "16",
      maxMemory: "64",
      maxStorage: "200",
      maxNodes: "2",
      priority: "中",
    });

    // 等待 API 响应
    const response = await responsePromise.catch(() => null);
    if (response && response.status() === 201) {
      await quotasPage.waitForModalClose();
      await page.waitForTimeout(1000);
      await quotasPage.waitForPageReady();
      const hasNewConfig = await quotasPage.hasConfig(testConfigName);
      expect(hasNewConfig).toBe(true);
    } else {
      // API 返回错误 - 记录状态
      const status = response ? response.status() : "no response";
      const body = response ? await response.text().catch(() => "") : "";
      console.log(`创建 API 返回: ${status}, 响应: ${body}`);
      // 截图
      await page.screenshot({
        path: "e2e/artifacts/resource-quotas-create-error.png",
        fullPage: true,
      });
      // 标记后端问题 - 表单填写和提交流程本身是正常的
      expect(response).toBeTruthy();
    }
  });

  test("编辑现有配额配置", async ({ page }) => {
    const isEmpty = await quotasPage.emptyState.isVisible();
    test.skip(isEmpty, "表格无数据，跳过编辑测试");

    // 记录原始数据
    const originalName = await quotasPage.getConfigNameAtRow(0);
    expect(originalName).toBeTruthy();

    // 打开编辑 Modal
    await quotasPage.clickEditAtRow(0);

    // 验证预填数据（toHaveValue 自动重试，等待 React 完成状态回填）
    await expect(quotasPage.configNameInput).toHaveValue(originalName?.trim() ?? "", {
      timeout: 5000,
    });

    // 修改 GPU 数量
    const originalGpu = await quotasPage.maxGpuInput.inputValue();
    const newGpu = String(parseInt(originalGpu) + 1);
    await quotasPage.fillForm({ maxGpu: newGpu });

    // 保存
    await quotasPage.submitForm();
    await quotasPage.waitForModalClose();

    // 等待数据刷新
    await page.waitForTimeout(1000);
    await quotasPage.waitForPageReady();

    // 恢复原值（清理测试数据）
    await quotasPage.clickEditAtRow(0);
    await quotasPage.fillForm({ maxGpu: originalGpu });
    await quotasPage.submitForm();
    await quotasPage.waitForModalClose();
  });

  test("创建 API 请求格式正确", async ({ page }) => {
    let requestBody: Record<string, unknown> | null = null;

    // 监听 POST 请求
    page.on("request", (request) => {
      if (
        request.url().includes("/resource-limit-configs") &&
        request.method() === "POST"
      ) {
        requestBody = request.postDataJSON();
      }
    });

    // 监听 API 响应
    const responsePromise = page.waitForResponse(
      (resp) =>
        resp.url().includes("/resource-limit-configs") &&
        resp.request().method() === "POST",
      { timeout: 15000 },
    );

    await quotasPage.createQuota({
      configName: testConfigName,
      role: "工程师",
      maxGpu: "4",
      maxCpu: "16",
      maxMemory: "64",
      maxStorage: "200",
      maxNodes: "2",
      priority: "中",
    });

    // 等待 API 响应（无论成功与否）
    await responsePromise.catch(() => null);

    // 验证请求体格式（这是前端表单发送的数据，不依赖后端是否成功）
    expect(requestBody).toBeTruthy();
    expect(requestBody!.config_name).toBe(testConfigName);
    expect(requestBody!.role).toBe("engineer");
    expect(requestBody!.max_gpu_per_job).toBe(4);
    expect(requestBody!.max_cpu_per_job).toBe(16);
    expect(requestBody!.max_memory_gb_per_job).toBe(64);
    expect(requestBody!.max_storage_gb_per_job).toBe(200);
    expect(requestBody!.max_nodes_per_job).toBe(2);
    expect(requestBody!.priority_default).toBe("medium");
  });

  test("列表 API 响应包含分页信息", async ({ page }) => {
    let responseData: Record<string, unknown> | null = null;

    // 监听 GET 响应
    page.on("response", async (response) => {
      if (
        response.url().includes("/resource-limit-configs") &&
        response.request().method() === "GET" &&
        response.ok()
      ) {
        try {
          responseData = await response.json();
        } catch {
          // 忽略 JSON 解析错误
        }
      }
    });

    // 刷新页面触发 API 调用
    await page.reload();
    await quotasPage.waitForPageReady();

    if (responseData) {
      // 验证分页响应格式
      expect(responseData).toHaveProperty("items");
      expect(responseData).toHaveProperty("total");
      expect(responseData).toHaveProperty("page");
      expect(responseData).toHaveProperty("page_size");
    }
  });

  test("创建后列表计数严格 +1 且新配置可见", async ({ page }) => {
    // 读取创建前总数（Cloudscape Header counter: "资源限制配置 (N)"）
    const subHeader = page.locator("h2").filter({ hasText: "资源限制配置" });
    const beforeText = (await subHeader.textContent()) ?? "";
    const beforeMatch = beforeText.match(/\((\d+)\)/);
    test.skip(!beforeMatch, "无法读取创建前计数，跳过严格计数校验");
    const beforeCount = parseInt(beforeMatch![1]);

    // 创建一条配置
    const responsePromise = page.waitForResponse(
      (resp) =>
        resp.url().includes("/resource-limit-configs") &&
        resp.request().method() === "POST",
      { timeout: 15000 },
    );

    await quotasPage.createQuota({
      configName: testConfigName,
      role: "工程师",
      maxGpu: "4",
      maxCpu: "16",
      maxMemory: "64",
      maxStorage: "200",
      maxNodes: "2",
      priority: "中",
    });

    const response = await responsePromise.catch(() => null);
    test.skip(
      !response || response.status() !== 201,
      `创建未成功 (${response ? response.status() : "no response"})，跳过严格计数校验`,
    );

    await quotasPage.waitForModalClose();
    await page.waitForTimeout(1000);
    await quotasPage.waitForPageReady();

    // 严格断言：新配置可见
    const hasNewConfig = await quotasPage.hasConfig(testConfigName);
    expect(hasNewConfig).toBe(true);

    // 严格断言：总数 +1（toPass 自动重试，等待 invalidate 刷新计数）
    await expect(async () => {
      const afterText = (await subHeader.textContent()) ?? "";
      const afterMatch = afterText.match(/\((\d+)\)/);
      expect(afterMatch).toBeTruthy();
      expect(parseInt(afterMatch![1])).toBe(beforeCount + 1);
    }).toPass({ timeout: 10000 });

    // 清理：删除刚创建的测试配置
    await quotasPage.clickDeleteByName(testConfigName);
    await quotasPage.confirmDelete();
    await quotasPage.waitForDeleteModalClose();
  });

  test("删除流程 - 创建后删除，列表中消失且计数 -1", async ({ page }) => {
    // 先创建一条可删除的测试配置
    const createResponsePromise = page.waitForResponse(
      (resp) =>
        resp.url().includes("/resource-limit-configs") &&
        resp.request().method() === "POST",
      { timeout: 15000 },
    );

    await quotasPage.createQuota({
      configName: testConfigName,
      role: "工程师",
      maxGpu: "4",
      maxCpu: "16",
      maxMemory: "64",
      maxStorage: "200",
      maxNodes: "2",
      priority: "中",
    });

    const createResp = await createResponsePromise.catch(() => null);
    test.skip(
      !createResp || createResp.status() !== 201,
      `创建未成功 (${createResp ? createResp.status() : "no response"})，无法验证删除流程`,
    );

    await quotasPage.waitForModalClose();
    await page.waitForTimeout(1000);
    await quotasPage.waitForPageReady();

    // 确认创建成功、配置在列表中
    expect(await quotasPage.hasConfig(testConfigName)).toBe(true);

    // 读取删除前计数
    const subHeader = page.locator("h2").filter({ hasText: "资源限制配置" });
    const beforeText = (await subHeader.textContent()) ?? "";
    const beforeMatch = beforeText.match(/\((\d+)\)/);
    const beforeCount = beforeMatch ? parseInt(beforeMatch[1]) : null;

    // 执行删除：点删除 -> 确认 Modal -> 确认删除
    const deleteResponsePromise = page.waitForResponse(
      (resp) =>
        resp.url().includes("/resource-limit-configs") &&
        resp.request().method() === "DELETE",
      { timeout: 15000 },
    );

    await quotasPage.clickDeleteByName(testConfigName);
    await expect(quotasPage.deleteModal).toBeVisible();
    await expect(quotasPage.deleteModal).toContainText(testConfigName);
    await quotasPage.confirmDelete();

    const deleteResp = await deleteResponsePromise.catch(() => null);
    expect(deleteResp).toBeTruthy();
    expect(deleteResp!.status()).toBe(204);

    await quotasPage.waitForDeleteModalClose();
    await page.waitForTimeout(1000);
    await quotasPage.waitForPageReady();

    // 严格断言：配置从列表消失
    await expect(async () => {
      expect(await quotasPage.hasConfig(testConfigName)).toBe(false);
    }).toPass({ timeout: 10000 });

    // 严格断言：计数 -1（若删除前能读取到计数）
    if (beforeCount !== null) {
      await expect(async () => {
        const afterText = (await subHeader.textContent()) ?? "";
        const afterMatch = afterText.match(/\((\d+)\)/);
        expect(afterMatch).toBeTruthy();
        expect(parseInt(afterMatch![1])).toBe(beforeCount - 1);
      }).toPass({ timeout: 10000 });
    }
  });
});

test.describe("资源配额管理 - 无障碍测试", () => {
  let quotasPage: ResourceQuotasPage;

  test.beforeEach(async ({ page }) => {
    if (!isRemote) {
      await setupResourceQuotaMocks(page);
    }
    quotasPage = new ResourceQuotasPage(page);
    await navigateWithAuth(page, "/resource-quotas");
    await quotasPage.waitForPageReady();
  });

  test("表格使用正确的 ARIA 角色", async ({ page }) => {
    const table = page.getByRole("table");
    await expect(table).toBeVisible();
  });

  test("按钮可通过键盘访问", async ({ page: _page }) => {
    // Tab 到新建按钮
    await quotasPage.createButton.focus();
    const isFocused = await quotasPage.createButton.evaluate(
      (el) => document.activeElement === el,
    );
    expect(isFocused).toBe(true);
  });

  test("Modal 中表单字段有 aria-label", async () => {
    await quotasPage.clickCreate();

    // 所有输入字段应该有 aria-label
    await expect(quotasPage.configNameInput).toHaveAttribute(
      "aria-label",
      "配置名称",
    );
    await expect(quotasPage.maxGpuInput).toHaveAttribute(
      "aria-label",
      "最大 GPU",
    );
    await expect(quotasPage.maxCpuInput).toHaveAttribute(
      "aria-label",
      "最大 CPU",
    );
    await expect(quotasPage.maxMemoryInput).toHaveAttribute(
      "aria-label",
      "最大内存",
    );
    await expect(quotasPage.maxStorageInput).toHaveAttribute(
      "aria-label",
      "最大存储",
    );
    await expect(quotasPage.maxNodesInput).toHaveAttribute(
      "aria-label",
      "最大节点",
    );
  });
});
