/**
 * 集群监控页面 Page Object
 *
 * 封装监控仪表盘 (/monitoring) 的所有交互操作。
 * 页面由 4 个 Cloudscape Tab 组成: 概览 / 指标趋势 / Grafana / 告警。
 */

import { Page, Locator, expect } from "@playwright/test";
import { BasePage } from "./BasePage";

/** Tab 名称类型 (用于 switchToTab) */
export type MonitoringTabName = "概览" | "指标趋势" | "Grafana" | "告警";

export class MonitoringPage extends BasePage {
  // === 页面级元素 ===
  readonly pageTitle: Locator;
  readonly dashboard: Locator;
  readonly loadingIndicator: Locator;
  readonly errorState: Locator;

  // === 时间范围 / 自动刷新控件 ===
  readonly dateRangePicker: Locator;
  readonly refreshControl: Locator;

  // === Tab 元素 (role=tab) ===
  readonly tabOverview: Locator;
  readonly tabMetrics: Locator;
  readonly tabGrafana: Locator;
  readonly tabAlerts: Locator;

  // === 概览 Tab 内容 ===
  readonly clusterSummaryCard: Locator;
  readonly utilizationCard: Locator;

  // === 指标趋势 Tab 内容 ===
  readonly metricsCharts: Locator;
  readonly metricsTrendChart: Locator;

  // === Grafana Tab 内容 ===
  readonly grafanaToggle: Locator;
  readonly grafanaFallback: Locator;

  // === 告警 Tab 内容 ===
  readonly alertsEmptyState: Locator;

  constructor(page: Page) {
    super(page);

    // 页面级
    this.pageTitle = page.locator("h1").filter({ hasText: "集群监控" });
    this.dashboard = page.locator('[data-testid="monitoring-dashboard"]');
    this.loadingIndicator = page.getByText("加载中...");
    // 集群查询失败时 InlineErrorState 渲染重试按钮
    this.errorState = page.getByRole("button", { name: /重试|重新加载/ });

    // 时间范围 / 自动刷新
    // DateRangePicker 触发按钮使用占位文本，relative 默认值下展示已选区间
    this.dateRangePicker = page.getByRole("button", {
      name: /选择时间范围|最近|Last|分钟|小时|天/,
    });
    // SegmentedControl "自动刷新" 渲染为 role=toolbar，选项: 关闭 / 30秒 / 1分钟 / 5分钟
    this.refreshControl = page.getByRole("toolbar", { name: "自动刷新" });

    // Tabs (role=tab)
    this.tabOverview = page.getByRole("tab", { name: "概览" });
    this.tabMetrics = page.getByRole("tab", { name: "指标趋势" });
    this.tabGrafana = page.getByRole("tab", { name: "Grafana" });
    // 告警 Tab label 可能带计数后缀，用前缀匹配
    this.tabAlerts = page.getByRole("tab", { name: /^告警/ });

    // 概览 Tab
    this.clusterSummaryCard = page
      .locator('[class*="container"]')
      .filter({ has: page.getByRole("heading", { name: "集群概览" }) });
    this.utilizationCard = page
      .locator('[class*="container"]')
      .filter({ has: page.getByRole("heading", { name: "资源利用率" }) });

    // 指标趋势 Tab — MetricsCharts 容器统一带 data-testid="metrics-chart"
    this.metricsCharts = page.locator('[data-testid="metrics-chart"]');
    // 折线图容器（标题「资源利用率趋势」），用于断言趋势图有真实数据点
    this.metricsTrendChart = page
      .locator('[data-testid="metrics-chart"]')
      .filter({ has: page.getByRole("heading", { name: "资源利用率趋势" }) });

    // Grafana Tab
    this.grafanaToggle = page.getByText("显示 Grafana 仪表盘");
    // 未配置降级: Alert header "Grafana 监控大盘未启用"
    this.grafanaFallback = page.getByText("Grafana 监控大盘未启用");

    // 告警 Tab — 空态 StatusIndicator "暂无告警"
    this.alertsEmptyState = page.getByText("暂无告警");
  }

  /**
   * 导航到监控页
   */
  async goto() {
    await this.page.goto("/monitoring");
    await this.page.waitForLoadState("networkidle");
  }

  /**
   * 等待页面加载完成
   *
   * 页面初始展示 loading StatusIndicator，所有查询完成后渲染 Tabs。
   * 等待逻辑: loading 消失 + (Tab 出现 或 错误态出现)。
   */
  async waitForPageReady() {
    // 标题应始终可见 (PageLayout 骨架)
    await this.pageTitle.waitFor({ state: "visible", timeout: 15000 });
    // 等待加载指示器消失
    await this.loadingIndicator
      .waitFor({ state: "hidden", timeout: 20000 })
      .catch(() => {});
    // 等待 Tabs 或错误态出现
    await Promise.race([
      this.tabOverview.waitFor({ state: "visible", timeout: 15000 }),
      this.errorState.waitFor({ state: "visible", timeout: 15000 }),
    ]).catch(() => {});
  }

  /**
   * 切换到指定 Tab，并等待其内容挂载
   */
  async switchToTab(name: MonitoringTabName) {
    const tabMap: Record<MonitoringTabName, Locator> = {
      概览: this.tabOverview,
      指标趋势: this.tabMetrics,
      Grafana: this.tabGrafana,
      告警: this.tabAlerts,
    };
    const tab = tabMap[name];
    await tab.click();
    // 等待选中态生效 (aria-selected)
    await expect(tab).toHaveAttribute("aria-selected", "true", {
      timeout: 5000,
    });
  }

  /**
   * 概览 Tab — 集群概览卡片文本是否包含指定内容
   */
  async clusterSummaryContains(text: string): Promise<boolean> {
    const content = await this.clusterSummaryCard.textContent();
    return content?.includes(text) ?? false;
  }

  /**
   * 概览 Tab — 获取资源利用率卡片完整文本
   */
  async getUtilizationText(): Promise<string> {
    return (await this.utilizationCard.textContent()) ?? "";
  }

  /**
   * 指标趋势 Tab — 渲染的图表数量
   */
  async getMetricsChartCount(): Promise<number> {
    return this.metricsCharts.count();
  }

  /**
   * 指标趋势 Tab — 折线图是否有真实数据点（而非「暂无数据」空态）。
   *
   * 判据：折线图容器内无「暂无数据」文案，且渲染了 SVG 图表。覆盖语义指标名
   * 映射裂缝——后端若把 cpu/memory/gpu_utilization 字面量当 PromQL 查询将返空，
   * MetricsCharts 折线图据此显示「暂无数据」（data_points 全空时）。
   */
  async trendChartHasData(): Promise<boolean> {
    const emptyCount = await this.metricsTrendChart
      .getByText("暂无数据")
      .count();
    if (emptyCount > 0) {
      return false;
    }
    // 有数据时 Cloudscape LineChart 渲染 SVG（空态则只有文案、无图表 SVG）
    const svgCount = await this.metricsTrendChart.locator("svg").count();
    return svgCount > 0;
  }

  /**
   * 自动刷新 SegmentedControl — 获取指定间隔选项按钮 (限定在 toolbar 内)
   *
   * 必须限定在 refreshControl 内，否则「关闭」会与导航栏「关闭导航」按钮冲突。
   */
  refreshOption(label: "关闭" | "30秒" | "1分钟" | "5分钟"): Locator {
    return this.refreshControl.getByRole("button", { name: label, exact: true });
  }

  /**
   * 切换自动刷新间隔，并断言选中态 (aria-pressed)
   */
  async selectRefreshInterval(label: "关闭" | "30秒" | "1分钟" | "5分钟") {
    const option = this.refreshOption(label);
    await option.click();
    await expect(option).toHaveAttribute("aria-pressed", "true", {
      timeout: 5000,
    });
  }

  /**
   * 是否整页报错 (无标题 = 页面崩坏)
   */
  async hasPageTitle(): Promise<boolean> {
    return this.pageTitle.isVisible();
  }
}
