import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * 训练任务列表页 Page Object
 */
export class TrainingJobListPage extends BasePage {
  readonly searchInput: Locator;
  readonly createButton: Locator;
  readonly table: Locator;
  readonly tableRows: Locator;
  readonly pagination: Locator;

  constructor(page: Page) {
    super(page);
    this.searchInput = page.locator('input[placeholder*="搜索"]');
    this.createButton = page.locator('button:has-text("创建训练任务")');
    this.table = page.locator('table');
    this.tableRows = page.locator('table tbody tr');
    this.pagination = page.locator('[data-testid="pagination"]');
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
    return this.page.locator('text=暂无数据').isVisible().catch(() => false);
  }
}
