import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * 训练任务列表页 Page Object
 */
export class TrainingJobListPage extends BasePage {
  readonly searchInput: Locator;
  readonly createButton: Locator;
  readonly refreshButton: Locator;
  readonly table: Locator;
  readonly tableRows: Locator;
  readonly pagination: Locator;

  // Filters
  readonly statusFilter: Locator;
  readonly priorityFilter: Locator;

  // Empty State
  readonly emptyState: Locator;

  constructor(page: Page) {
    super(page);
    this.searchInput = page.locator('input[placeholder*="搜索"]');
    this.createButton = page.locator('button:has-text("创建训练任务")');
    this.refreshButton = page.locator('button:has-text("刷新")');
    this.table = page.locator('table');
    this.tableRows = page.locator('table tbody tr');
    this.pagination = page.locator('[data-testid="pagination"]');

    // Filters
    this.statusFilter = page.locator('text=全部状态');
    this.priorityFilter = page.locator('text=全部优先级');

    // Empty State
    this.emptyState = page.locator('text=暂无训练任务');
  }

  /**
   * 导航到训练任务列表页
   */
  async goto() {
    await this.page.goto('/training-jobs');
    await this.waitForPageLoad();
  }

  /**
   * 搜索训练任务
   */
  async search(keyword: string) {
    await this.searchInput.fill(keyword);
    await this.page.keyboard.press('Enter');
  }

  /**
   * 点击创建按钮
   */
  async clickCreate() {
    await this.createButton.click();
  }

  /**
   * 获取表格行数
   */
  async getRowCount() {
    return this.tableRows.count();
  }

  /**
   * 点击指定行的操作按钮
   */
  async clickRowAction(rowIndex: number, actionName: string) {
    const row = this.tableRows.nth(rowIndex);
    await row.locator(`button:has-text("${actionName}")`).click();
  }

  /**
   * 点击任务名称链接
   */
  async clickJobLink(jobName: string) {
    await this.page.locator(`a:has-text("${jobName}")`).click();
  }

  /**
   * 等待表格数据加载
   */
  async waitForTableLoad() {
    await this.page.waitForSelector('table tbody tr', { state: 'visible' }).catch(() => {});
  }

  /**
   * 检查空状态是否显示
   */
  async isEmptyStateVisible() {
    return this.emptyState.isVisible().catch(() => false);
  }

  /**
   * 点击刷新按钮
   */
  async clickRefresh() {
    await this.refreshButton.click();
    await this.waitForPageLoad();
  }

  /**
   * 选择状态筛选
   */
  async selectStatusFilter(status: string) {
    await this.statusFilter.click();
    await this.page.waitForTimeout(200); // 等待下拉菜单展开
    await this.page.locator(`[role="option"]:has-text("${status}")`).click();
    await this.waitForPageLoad();
  }

  /**
   * 选择优先级筛选
   */
  async selectPriorityFilter(priority: string) {
    await this.priorityFilter.click();
    await this.page.waitForTimeout(200);
    await this.page.locator(`[role="option"]:has-text("${priority}")`).click();
    await this.waitForPageLoad();
  }

  /**
   * 清除状态筛选
   */
  async clearStatusFilter() {
    await this.selectStatusFilter('全部状态');
  }

  /**
   * 清除优先级筛选
   */
  async clearPriorityFilter() {
    await this.selectPriorityFilter('全部优先级');
  }

  /**
   * 获取指定行的状态文本
   */
  async getRowStatus(rowIndex: number): Promise<string | null> {
    const row = this.tableRows.nth(rowIndex);
    // 状态通常在 Badge 组件中
    const statusBadge = row.locator('span[class*="badge"]').first();
    if (await statusBadge.isVisible()) {
      return statusBadge.textContent();
    }
    return null;
  }

  /**
   * 获取指定任务名称的行
   */
  getRowByJobName(jobName: string): Locator {
    return this.page.locator(`tr:has-text("${jobName}")`);
  }

  /**
   * 获取指定任务的状态
   */
  async getJobStatus(jobName: string): Promise<string | null> {
    const row = this.getRowByJobName(jobName);
    const statusBadge = row.locator('span[class*="badge"]').first();
    if (await statusBadge.isVisible()) {
      return statusBadge.textContent();
    }
    return null;
  }

  /**
   * 检查任务是否在列表中
   */
  async hasJob(jobName: string): Promise<boolean> {
    const row = this.getRowByJobName(jobName);
    return row.isVisible();
  }

  /**
   * 翻到下一页
   */
  async goToNextPage() {
    await this.page.locator('[aria-label="下一页"]').click();
    await this.waitForPageLoad();
  }

  /**
   * 翻到上一页
   */
  async goToPreviousPage() {
    await this.page.locator('[aria-label="上一页"]').click();
    await this.waitForPageLoad();
  }

  /**
   * 获取所有任务名称
   */
  async getAllJobNames(): Promise<string[]> {
    const rows = await this.tableRows.all();
    const names: string[] = [];
    for (const row of rows) {
      // 任务名称通常在第一列的链接中
      const nameLink = row.locator('a').first();
      const name = await nameLink.textContent();
      if (name) {
        names.push(name.trim());
      }
    }
    return names;
  }

  /**
   * 等待特定任务出现
   */
  async waitForJob(jobName: string, timeout: number = 5000) {
    await this.page.locator(`text=${jobName}`).waitFor({ state: 'visible', timeout });
  }
}
