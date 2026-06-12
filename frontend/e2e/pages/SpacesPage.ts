/**
 * 开发空间页面 Page Object
 *
 * 封装 /spaces 列表页与 /spaces/create 创建页的交互操作
 */

import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class SpacesPage extends BasePage {
  // 列表页元素
  readonly pageTitle: Locator;
  readonly createButton: Locator;
  readonly refreshButton: Locator;
  readonly table: Locator;
  readonly tableRows: Locator;
  readonly loadingIndicator: Locator;
  readonly emptyState: Locator;
  readonly errorAlert: Locator;
  readonly statusFilter: Locator;

  // 创建页元素
  readonly nameInput: Locator;
  readonly spaceTypeSelect: Locator;
  readonly instanceTypeSelect: Locator;
  readonly storageInput: Locator;
  readonly submitButton: Locator;
  readonly cancelButton: Locator;

  // 删除确认 Modal
  readonly deleteModal: Locator;
  readonly confirmDeleteButton: Locator;
  readonly cancelDeleteButton: Locator;

  constructor(page: Page) {
    super(page);

    // 列表页
    this.pageTitle = page.locator('h1').filter({ hasText: '在线开发环境' });
    this.createButton = page.getByRole('button', { name: '创建开发空间' });
    this.refreshButton = page.getByRole('button', { name: '刷新' });
    this.table = page.locator('table').first();
    this.tableRows = page.locator('table tbody tr');
    this.loadingIndicator = page.getByText('加载中...');
    this.emptyState = page.getByText('暂无开发空间');
    this.errorAlert = page.getByText('加载失败');
    this.statusFilter = page.getByText('全部状态').first();

    // 创建页（Cloudscape FormField label 不自动关联 input，用占位符定位）
    this.nameInput = page.getByPlaceholder('my-dev-space');
    // 创建页只有两个 Select：第 1 个是 IDE 类型，第 2 个是实例类型
    this.spaceTypeSelect = page
      .locator('button[aria-haspopup="listbox"]')
      .first();
    this.instanceTypeSelect = page
      .locator('button[aria-haspopup="listbox"]')
      .nth(1);
    this.storageInput = page.locator('input[type="number"]');
    this.submitButton = page.getByRole('button', { name: '创建空间' });
    this.cancelButton = page.getByRole('button', { name: '取消' });

    // 删除 Modal
    this.deleteModal = page.getByRole('dialog').filter({ hasText: '确认删除' });
    this.confirmDeleteButton = this.deleteModal.getByRole('button', {
      name: '确认删除',
    });
    this.cancelDeleteButton = this.deleteModal.getByRole('button', {
      name: '取消',
    });
  }

  // ===== 导航 =====

  async goto() {
    await this.page.goto('/spaces');
    await this.page.waitForLoadState('networkidle');
  }

  async gotoCreate() {
    await this.page.goto('/spaces/create');
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 等待列表页就绪（表格 / 空状态 / 错误三态之一可见）
   */
  async waitForPageReady() {
    await this.loadingIndicator
      .waitFor({ state: 'hidden', timeout: 20000 })
      .catch(() => {});
    await Promise.race([
      this.table.waitFor({ state: 'visible', timeout: 15000 }),
      this.emptyState.waitFor({ state: 'visible', timeout: 15000 }),
      this.errorAlert.waitFor({ state: 'visible', timeout: 15000 }),
    ]).catch(() => {});
  }

  // ===== 列表操作 =====

  async getRowCount(): Promise<number> {
    return this.tableRows.count();
  }

  async getAllSpaceNames(): Promise<string[]> {
    const rows = await this.tableRows.all();
    const names: string[] = [];
    for (const row of rows) {
      const name = await row.locator('td').first().textContent();
      if (name) names.push(name.trim());
    }
    return names;
  }

  /** 按名称定位行 */
  rowByName(spaceName: string): Locator {
    return this.tableRows.filter({ hasText: spaceName });
  }

  async hasSpace(spaceName: string): Promise<boolean> {
    return (await this.rowByName(spaceName).count()) > 0;
  }

  /** 获取某行的状态文本 */
  async getStatusOfSpace(spaceName: string): Promise<string | null> {
    // 状态列是第 4 列 (名称/IDE类型/实例类型/状态/创建时间/操作)
    return this.rowByName(spaceName).locator('td').nth(3).textContent();
  }

  /** 按状态过滤 */
  async filterByStatus(statusLabel: string) {
    await this.statusFilter.click();
    const option = this.page.getByRole('option', { name: statusLabel });
    await option.waitFor({ state: 'visible', timeout: 3000 });
    await option.click();
    await this.page.waitForLoadState('networkidle');
  }

  /** 行内操作按钮 */
  async clickRowAction(spaceName: string, action: '启动' | '停止' | '删除' | '打开') {
    await this.rowByName(spaceName)
      .getByRole('button', { name: action })
      .click();
  }

  /** 行内是否存在某操作按钮 */
  async hasRowAction(
    spaceName: string,
    action: '启动' | '停止' | '删除' | '打开',
  ): Promise<boolean> {
    return (
      (await this.rowByName(spaceName)
        .getByRole('button', { name: action })
        .count()) > 0
    );
  }

  /** 删除流程（含确认弹窗） */
  async deleteSpace(spaceName: string) {
    await this.clickRowAction(spaceName, '删除');
    await this.deleteModal.waitFor({ state: 'visible', timeout: 5000 });
    await this.confirmDeleteButton.click();
    await this.deleteModal
      .waitFor({ state: 'hidden', timeout: 15000 })
      .catch(() => {});
  }

  /** 点击空间名称进入详情 */
  async clickSpaceName(spaceName: string) {
    await this.rowByName(spaceName).locator('a').first().click();
  }

  // ===== 创建表单操作 =====

  async fillCreateForm(data: {
    name?: string;
    spaceTypeLabel?: string;
    instanceTypeLabel?: string;
    storageGb?: string;
  }) {
    if (data.name !== undefined) {
      await this.nameInput.clear();
      await this.nameInput.fill(data.name);
    }
    if (data.spaceTypeLabel) {
      await this.selectDropdown(this.spaceTypeSelect, data.spaceTypeLabel);
    }
    if (data.instanceTypeLabel) {
      await this.selectDropdown(this.instanceTypeSelect, data.instanceTypeLabel);
    }
    if (data.storageGb !== undefined) {
      await this.storageInput.clear();
      await this.storageInput.fill(data.storageGb);
    }
  }

  /**
   * 选择 Cloudscape Select 下拉选项
   */
  private async selectDropdown(trigger: Locator, optionText: string) {
    await trigger.scrollIntoViewIfNeeded();
    await trigger.click();
    const option = this.page
      .getByRole('option', { name: optionText })
      .first();
    await option.waitFor({ state: 'visible', timeout: 3000 });
    await option.click();
  }

  async submitCreateForm() {
    await this.submitButton.click();
  }

  async hasFormError(errorText: string | RegExp): Promise<boolean> {
    const error = this.page.getByText(errorText);
    return error
      .first()
      .isVisible()
      .catch(() => false);
  }

  /** 完整创建流程 */
  async createSpace(data: {
    name: string;
    spaceTypeLabel?: string;
    instanceTypeLabel?: string;
    storageGb?: string;
  }) {
    await this.gotoCreate();
    await this.fillCreateForm(data);
    await this.submitCreateForm();
  }

  // ===== 断言辅助 =====

  async verifyTableHeaders() {
    await expect(
      this.page.getByRole('columnheader', { name: '名称' }),
    ).toBeVisible();
    await expect(
      this.page.getByRole('columnheader', { name: 'IDE 类型' }),
    ).toBeVisible();
    await expect(
      this.page.getByRole('columnheader', { name: '实例类型' }),
    ).toBeVisible();
    await expect(
      this.page.getByRole('columnheader', { name: '状态' }),
    ).toBeVisible();
    await expect(
      this.page.getByRole('columnheader', { name: '创建时间' }),
    ).toBeVisible();
    await expect(
      this.page.getByRole('columnheader', { name: '操作' }),
    ).toBeVisible();
  }
}
