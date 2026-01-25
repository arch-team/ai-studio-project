/**
 * Training Job Detail Page - Page Object
 *
 * 训练任务详情页 Page Object
 */

import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * 训练任务详情页 Page Object
 */
export class TrainingJobDetailPage extends BasePage {
  // === Header ===
  readonly jobNameHeader: Locator;
  readonly refreshButton: Locator;
  readonly pauseButton: Locator;
  readonly resumeButton: Locator;
  readonly deleteButton: Locator;

  // === Overview ===
  readonly overviewContainer: Locator;
  readonly statusLabel: Locator;
  readonly priorityLabel: Locator;
  readonly distributionStrategyLabel: Locator;
  readonly durationLabel: Locator;

  // === Progress ===
  readonly progressContainer: Locator;
  readonly currentEpochLabel: Locator;
  readonly currentStepLabel: Locator;

  // === Tabs ===
  readonly configTab: Locator;
  readonly checkpointsTab: Locator;
  readonly logsTab: Locator;
  readonly metricsTab: Locator;

  // === Delete Modal ===
  readonly deleteModal: Locator;
  readonly confirmDeleteButton: Locator;
  readonly cancelDeleteButton: Locator;

  // === Error State ===
  readonly errorMessage: Locator;
  readonly loadingSpinner: Locator;

  constructor(page: Page) {
    super(page);

    // Header
    this.jobNameHeader = page.locator('h1');
    this.refreshButton = page.locator('button:has-text("刷新")');
    this.pauseButton = page.locator('button:has-text("暂停")');
    this.resumeButton = page.locator('button:has-text("恢复")');
    this.deleteButton = page.locator('button:has-text("删除")');

    // Overview Container
    this.overviewContainer = page.locator('text=概览').locator('..').locator('..');
    this.statusLabel = page.locator('text=状态').locator('..').locator('..');
    this.priorityLabel = page.locator('text=优先级').locator('..').locator('..');
    this.distributionStrategyLabel = page.locator('text=分布式策略').locator('..').locator('..');
    this.durationLabel = page.locator('text=持续时间').locator('..').locator('..');

    // Progress Container
    this.progressContainer = page.locator('text=训练进度').locator('..').locator('..');
    this.currentEpochLabel = page.locator('text=当前 Epoch').locator('..');
    this.currentStepLabel = page.locator('text=当前 Step').locator('..');

    // Tabs
    this.configTab = page.locator('button[role="tab"]:has-text("配置信息")');
    this.checkpointsTab = page.locator('button[role="tab"]:has-text("检查点")');
    this.logsTab = page.locator('button[role="tab"]:has-text("日志")');
    this.metricsTab = page.locator('button[role="tab"]:has-text("训练指标")');

    // Delete Modal
    this.deleteModal = page.locator('[class*="modal"]:has-text("确认删除")');
    this.confirmDeleteButton = page.locator('button:has-text("确认删除")');
    this.cancelDeleteButton = this.deleteModal.locator('button:has-text("取消")');

    // Error and Loading
    this.errorMessage = page.locator('[color="text-status-error"]');
    this.loadingSpinner = page.locator('text=加载中...');
  }

  /**
   * 导航到指定任务的详情页
   */
  async goto(jobId: number) {
    await this.page.goto(`/training-jobs/${jobId}`);
    await this.waitForPageLoad();
  }

  /**
   * 等待页面内容加载完成
   */
  async waitForContentLoad() {
    await this.page.waitForSelector('h1', { state: 'visible' });
    await this.waitForLoadingComplete();
  }

  /**
   * 获取任务名称
   */
  async getJobName(): Promise<string | null> {
    return this.jobNameHeader.textContent();
  }

  /**
   * 点击刷新按钮
   */
  async clickRefresh() {
    await this.refreshButton.click();
    await this.waitForPageLoad();
  }

  /**
   * 点击暂停按钮
   */
  async clickPause() {
    await this.pauseButton.click();
  }

  /**
   * 点击恢复按钮
   */
  async clickResume() {
    await this.resumeButton.click();
  }

  /**
   * 点击删除按钮打开确认弹窗
   */
  async openDeleteModal() {
    await this.deleteButton.click();
  }

  /**
   * 确认删除
   */
  async confirmDelete() {
    await this.confirmDeleteButton.click();
  }

  /**
   * 取消删除
   */
  async cancelDelete() {
    await this.cancelDeleteButton.click();
  }

  /**
   * 切换到指定 Tab
   */
  async switchToTab(tabName: 'config' | 'checkpoints' | 'logs' | 'metrics') {
    const tabMap = {
      config: this.configTab,
      checkpoints: this.checkpointsTab,
      logs: this.logsTab,
      metrics: this.metricsTab,
    };
    await tabMap[tabName].click();
  }

  /**
   * 检查暂停按钮是否可见
   */
  async isPauseButtonVisible(): Promise<boolean> {
    return this.pauseButton.isVisible();
  }

  /**
   * 检查恢复按钮是否可见
   */
  async isResumeButtonVisible(): Promise<boolean> {
    return this.resumeButton.isVisible();
  }

  /**
   * 检查删除按钮是否禁用
   */
  async isDeleteButtonDisabled(): Promise<boolean> {
    return this.deleteButton.isDisabled();
  }

  /**
   * 检查删除按钮是否启用
   */
  async isDeleteButtonEnabled(): Promise<boolean> {
    return this.deleteButton.isEnabled();
  }

  /**
   * 检查是否显示错误状态
   */
  async hasError(): Promise<boolean> {
    return this.errorMessage.isVisible();
  }

  /**
   * 获取错误消息
   */
  async getErrorMessage(): Promise<string | null> {
    return this.errorMessage.textContent();
  }

  /**
   * 检查是否显示加载状态
   */
  async isLoading(): Promise<boolean> {
    return this.loadingSpinner.isVisible();
  }

  /**
   * 获取状态文本（通过页面定位）
   */
  async getStatusText(): Promise<string | null> {
    // 状态通常显示在 Badge 组件中
    const statusBadge = this.page.locator('text=状态').locator('..').locator('span[class*="badge"]');
    if (await statusBadge.isVisible()) {
      return statusBadge.textContent();
    }
    // 备选方案：直接查找状态文本
    const statusTexts = ['运行中', '已完成', '已失败', '已暂停', '被抢占', '已提交'];
    for (const text of statusTexts) {
      const element = this.page.locator(`text=${text}`).first();
      if (await element.isVisible()) {
        return text;
      }
    }
    return null;
  }

  /**
   * 等待状态变更
   */
  async waitForStatus(expectedStatus: string, timeout: number = 5000) {
    await this.page.waitForSelector(`text=${expectedStatus}`, { timeout });
  }

  /**
   * 检查配置信息 Tab 内容是否可见
   */
  async isConfigTabContentVisible(): Promise<boolean> {
    const configContent = this.page.locator('text=实例类型');
    return configContent.isVisible();
  }

  /**
   * 检查检查点 Tab 内容是否可见
   */
  async isCheckpointsTabContentVisible(): Promise<boolean> {
    // 检查点表格或空状态
    const checkpointTable = this.page.locator('text=检查点名称');
    const emptyState = this.page.locator('text=暂无检查点');
    return (await checkpointTable.isVisible()) || (await emptyState.isVisible());
  }
}
