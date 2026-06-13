/**
 * 集群监控页 (/monitoring) E2E 测试
 *
 * 测试对象: 监控仪表盘四个 Tab (概览 / 指标趋势 / Grafana / 告警) 全功能
 * 测试模式: 同时支持 Mock 模式 和 真实 API 模式
 *
 * Mock 模式 (本地 dev server，最新前端代码):
 *   npx playwright test e2e/tests/monitoring.spec.ts
 * 真实 API (后端已部署，验证真实集群/利用率数据):
 *   E2E_BASE_URL=http://ai-platform-dev-alb-1343863355.us-east-1.elb.amazonaws.com \
 *     npx playwright test e2e/tests/monitoring.spec.ts
 *
 * 分组策略 (isRemote):
 * - Mock 组: 页面加载 / Tab 切换 / Grafana 降级 / 告警空态 — 不依赖真实数据，本地跑。
 * - Remote 组: 真实集群名/状态/节点数 + CPU/内存/GPU 利用率数值 — 依赖后端，远程跑。
 *
 * ⚠️ 待部署说明: dev 前端为 v1.0.18，不含本轮「Grafana 死链降级」改动。
 *   故 remote 组不断言 Grafana 降级文案 (留待 v1.0.19 部署后)；
 *   Grafana 降级文案的验证完整放在 Mock 组 (本地最新代码) 中。
 */

import { test, expect, Page } from "@playwright/test";
import { MonitoringPage } from "../pages/MonitoringPage";
import { navigateWithAuth } from "../utils/auth";
import {
  mockClusterListResponse,
  mockUtilization,
  buildMockMetricSeries,
  mockEmptyAlertResponse,
} from "../fixtures/monitoring";

const isRemote = !!process.env.E2E_BASE_URL;

/**
 * Mock 模式辅助函数 - 设置监控页四端点 + 认证 API Mock
 *
 * 注意: 必须在 navigateWithAuth 之前调用 (route 拦截需先于导航注册)。
 */
async function setupMonitoringMocks(page: Page) {
  // --- 监控四端点 ---

  // 1. 集群列表 GET /clusters
  await page.route(/\/api\/v1\/clusters(\?.*)?$/, async (route) => {
    if (route.request().method() !== "GET") {
      await route.fallback();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockClusterListResponse),
    });
  });

  // 2. 资源利用率 GET /monitoring/utilization
  await page.route(
    /\/api\/v1\/monitoring\/utilization(\?.*)?$/,
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockUtilization),
      });
    },
  );

  // 3. 时间序列 GET /monitoring/metrics?metric_names=...
  await page.route(/\/api\/v1\/monitoring\/metrics(\?.*)?$/, async (route) => {
    const url = new URL(route.request().url());
    // metric_names 可能以重复 query 参数形式出现
    const names = url.searchParams.getAll("metric_names");
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(
        buildMockMetricSeries(names.length > 0 ? names : undefined),
      ),
    });
  });

  // 4. 告警 GET /monitoring/alerts → 空集
  await page.route(/\/api\/v1\/monitoring\/alerts(\?.*)?$/, async (route) => {
    if (route.request().method() !== "GET") {
      await route.fallback();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(mockEmptyAlertResponse),
    });
  });

  // --- 认证相关 (本地模式需要) ---

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

  // token 刷新 (整页导航后 initializeAuth 静默续期)
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

  await page.route("**/api/v1/auth/logout", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ message: "已登出" }),
    });
  });

  // 登录响应需匹配前端 LoginResponse 契约: tokens 嵌套对象 + user
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

// =====================================================================
// Mock 模式: 页面结构 / Tab 切换 / Grafana 降级 / 告警空态
// 使用本地最新前端代码 + Mock 数据，不依赖后端真实数据。
// =====================================================================
test.describe("集群监控 - 页面结构与 Tab 交互 (Mock 模式)", () => {
  test.skip(isRemote, "此组测试仅在 Mock 模式下运行");

  let monitoringPage: MonitoringPage;

  test.beforeEach(async ({ page }) => {
    await setupMonitoringMocks(page);
    monitoringPage = new MonitoringPage(page);
    await navigateWithAuth(page, "/monitoring");
    await monitoringPage.waitForPageReady();
  });

  test("页面加载不报错 - 标题可见 (404 回归)", async () => {
    // 核心回归: 修复前 /monitoring 后端 404 导致整页崩坏
    await expect(monitoringPage.pageTitle).toBeVisible();
    await expect(monitoringPage.dashboard).toBeVisible();
    // 不应出现错误重试态
    await expect(monitoringPage.errorState).toHaveCount(0);
  });

  test("四个 Tab 全部存在", async () => {
    await expect(monitoringPage.tabOverview).toBeVisible();
    await expect(monitoringPage.tabMetrics).toBeVisible();
    await expect(monitoringPage.tabGrafana).toBeVisible();
    await expect(monitoringPage.tabAlerts).toBeVisible();
  });

  test("概览 Tab - 集群概览与资源利用率卡片渲染", async () => {
    await monitoringPage.switchToTab("概览");
    await expect(monitoringPage.clusterSummaryCard).toBeVisible();
    await expect(monitoringPage.utilizationCard).toBeVisible();
    // Mock 集群名应展示
    expect(
      await monitoringPage.clusterSummaryContains("ai-platform-dev-hyperpod"),
    ).toBe(true);
    // 资源利用率卡片应含 CPU / 内存 / GPU
    const utilText = await monitoringPage.getUtilizationText();
    expect(utilText).toContain("CPU");
    expect(utilText).toContain("内存");
    expect(utilText).toContain("GPU");
  });

  test("指标趋势 Tab - 图表区域渲染", async () => {
    await monitoringPage.switchToTab("指标趋势");
    // MetricsCharts 容器应渲染 (折线 + 柱状 + 饼图)
    const chartCount = await monitoringPage.getMetricsChartCount();
    expect(chartCount).toBeGreaterThan(0);
  });

  test("指标趋势 Tab - 折线图有真实数据点 (非空态)", async () => {
    // Mock /monitoring/metrics 返回非空 data_points → 折线图应渲染数据而非「暂无数据」
    await monitoringPage.switchToTab("指标趋势");
    await expect(monitoringPage.metricsTrendChart).toBeVisible();
    // 折线图容器不应出现「暂无数据」空态文案
    await expect(
      monitoringPage.metricsTrendChart.getByText("暂无数据"),
    ).toHaveCount(0);
    expect(await monitoringPage.trendChartHasData()).toBe(true);
  });

  test("Grafana Tab - 未配置时显示降级引导文案", async () => {
    // 依赖本轮前端「Grafana 死链降级」改动 (v1.0.19)
    await monitoringPage.switchToTab("Grafana");
    await expect(monitoringPage.grafanaToggle).toBeVisible();
    // 测试环境未配置 VITE_GRAFANA_URL → 应展示降级 Alert
    await expect(monitoringPage.grafanaFallback).toBeVisible();
  });

  test("告警 Tab - 显示暂无告警空态", async () => {
    await monitoringPage.switchToTab("告警");
    await expect(monitoringPage.alertsEmptyState).toBeVisible();
  });

  test("时间范围选择器与自动刷新控件可交互", async () => {
    // 时间范围选择器可见且可点击展开
    await expect(monitoringPage.dateRangePicker.first()).toBeVisible();
    await monitoringPage.dateRangePicker.first().click();
    // 展开后应出现相对范围预设选项 (如「最近 1 小时」radio/option)
    const presetOption = monitoringPage.page
      .getByRole("radio")
      .or(monitoringPage.page.getByText(/最近 1 小时|最近 24 小时|最近 6 小时/))
      .first();
    await expect(presetOption).toBeVisible({ timeout: 5000 });
    // 关闭弹层 (Esc)
    await monitoringPage.page.keyboard.press("Escape");

    // 自动刷新 SegmentedControl 切换间隔 (默认选中「1分钟」→ 切到「关闭」)
    await expect(monitoringPage.refreshControl).toBeVisible();
    await monitoringPage.selectRefreshInterval("关闭");
    // 再切到「30秒」验证可继续交互
    await monitoringPage.selectRefreshInterval("30秒");
  });
});

// =====================================================================
// 真实 API 模式: 真实集群 / 利用率数据断言
// 监控页后端已部署，原有前端 hooks 契约在 v1.0.18 已正确，可直接验证。
// =====================================================================
test.describe("集群监控 - 真实数据 (Remote 模式)", () => {
  test.skip(!isRemote, "此组测试仅在远程模式下运行 (设置 E2E_BASE_URL)");

  let monitoringPage: MonitoringPage;

  test.beforeEach(async ({ page }) => {
    monitoringPage = new MonitoringPage(page);
    await navigateWithAuth(page, "/monitoring");
    await monitoringPage.waitForPageReady();
  });

  test("页面加载不报错 - 标题可见 (404 回归)", async () => {
    // 核心回归: 后端修复前 /monitoring 端点 404 → 整页崩坏
    await expect(monitoringPage.pageTitle).toBeVisible();
    await expect(monitoringPage.dashboard).toBeVisible();
    await expect(monitoringPage.errorState).toHaveCount(0);
  });

  test("概览 Tab - 真实集群信息 (名称/状态/节点数)", async () => {
    await monitoringPage.switchToTab("概览");
    await expect(monitoringPage.clusterSummaryCard).toBeVisible();
    const summary = await monitoringPage.clusterSummaryCard.textContent();
    // 真实集群名
    expect(summary).toContain("ai-platform-dev-hyperpod");
    // 状态字段 (active → 文案「活跃」)
    expect(summary).toContain("活跃");
    // 节点数信息 (格式 available/total，dev 为 3 节点)
    expect(summary).toMatch(/\d+\s*\/\s*3/);
  });

  test("概览 Tab - 资源利用率卡片含 CPU/内存/GPU 数值", async () => {
    await monitoringPage.switchToTab("概览");
    await expect(monitoringPage.utilizationCard).toBeVisible();
    const utilText = await monitoringPage.getUtilizationText();
    expect(utilText).toContain("CPU");
    expect(utilText).toContain("内存");
    expect(utilText).toContain("GPU");
    // 利用率以百分比展示，至少出现一个百分数
    expect(utilText).toMatch(/\d+(\.\d+)?%/);
  });

  test("指标趋势 Tab - 图表区域渲染", async () => {
    await monitoringPage.switchToTab("指标趋势");
    const chartCount = await monitoringPage.getMetricsChartCount();
    expect(chartCount).toBeGreaterThan(0);
  });

  test("指标趋势 Tab - 折线图有真实数据点 (语义指标名映射回归)", async () => {
    // 真实环境回归：后端须把 cpu/memory/gpu_utilization 映射为真实 PromQL 查 AMP，
    // 否则字面量查不到数据 → 折线图恒为「暂无数据」。此断言堵住该端到端裂缝。
    await monitoringPage.switchToTab("指标趋势");
    await expect(monitoringPage.metricsTrendChart).toBeVisible();
    await expect(
      monitoringPage.metricsTrendChart.getByText("暂无数据"),
    ).toHaveCount(0);
    expect(await monitoringPage.trendChartHasData()).toBe(true);
  });

  test("告警 Tab - 显示暂无告警空态 (告警子系统返空)", async () => {
    await monitoringPage.switchToTab("告警");
    // 后端告警端点本轮返回空集 → 空态文案
    await expect(monitoringPage.alertsEmptyState).toBeVisible();
  });

  test("四个 Tab 全部存在且可切换", async () => {
    await expect(monitoringPage.tabOverview).toBeVisible();
    await expect(monitoringPage.tabMetrics).toBeVisible();
    await expect(monitoringPage.tabGrafana).toBeVisible();
    await expect(monitoringPage.tabAlerts).toBeVisible();

    // 逐个切换不报错
    await monitoringPage.switchToTab("指标趋势");
    await monitoringPage.switchToTab("Grafana");
    await monitoringPage.switchToTab("告警");
    await monitoringPage.switchToTab("概览");
  });
});
