/**
 * 资源配额管理页面 Page Object
 *
 * 封装资源配额管理页面的所有交互操作
 */

import { Page, Locator, expect } from "@playwright/test";
import { BasePage } from "./BasePage";

export class ResourceQuotasPage extends BasePage {
  // 页面元素
  readonly pageTitle: Locator;
  readonly createButton: Locator;
  readonly table: Locator;
  readonly tableRows: Locator;
  readonly loadingIndicator: Locator;
  readonly emptyState: Locator;
  readonly errorState: Locator;
  readonly pagination: Locator;

  // 表格列头
  readonly headerConfigName: Locator;
  readonly headerRole: Locator;
  readonly headerMaxGpu: Locator;
  readonly headerMaxCpu: Locator;
  readonly headerMaxMemory: Locator;
  readonly headerMaxNodes: Locator;
  readonly headerPriority: Locator;
  readonly headerActions: Locator;

  // Modal 元素
  readonly modal: Locator;
  readonly modalTitle: Locator;
  readonly configNameInput: Locator;
  readonly roleSelect: Locator;
  readonly maxGpuInput: Locator;
  readonly maxCpuInput: Locator;
  readonly maxMemoryInput: Locator;
  readonly maxStorageInput: Locator;
  readonly maxNodesInput: Locator;
  readonly prioritySelect: Locator;
  readonly submitButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    super(page);

    // 页面元素
    this.pageTitle = page.locator("h1").filter({ hasText: "资源配额管理" });
    this.createButton = page.getByRole("button", { name: "新建配置" });
    this.table = page.locator("table").first();
    this.tableRows = page.locator("table tbody tr");
    this.loadingIndicator = page.getByText("加载中...");
    this.emptyState = page.getByText("暂无配置");
    this.errorState = page.getByText("加载失败");
    this.pagination = page.locator('[class*="pagination"]');

    // 表格列头
    this.headerConfigName = page.getByRole("columnheader", {
      name: "配置名称",
    });
    this.headerRole = page.getByRole("columnheader", { name: "适用角色" });
    this.headerMaxGpu = page.getByRole("columnheader", { name: /最大 GPU/ });
    this.headerMaxCpu = page.getByRole("columnheader", { name: /最大 CPU/ });
    this.headerMaxMemory = page.getByRole("columnheader", { name: /最大内存/ });
    this.headerMaxNodes = page.getByRole("columnheader", { name: /最大节点/ });
    this.headerPriority = page.getByRole("columnheader", {
      name: "默认优先级",
    });
    this.headerActions = page.getByRole("columnheader", { name: "操作" });

    // Modal 元素
    // Cloudscape Modal 渲染为 [role="dialog"] 或包含 awsui_dialog 的元素
    this.modal = page.locator('[class*="modal"]').first();
    this.modalTitle = this.modal.locator("h2").first();
    // Cloudscape Input 设置 ariaLabel 到 native <input> 上
    this.configNameInput = page.locator('input[aria-label="配置名称"]');
    // Cloudscape Select - 通过占位文本定位触发器区域
    // Select 组件不一定把 ariaLabel 放在 button 上，用占位文本更可靠
    this.roleSelect = page.getByText("选择角色");
    this.maxGpuInput = page.locator('input[aria-label="最大 GPU"]');
    this.maxCpuInput = page.locator('input[aria-label="最大 CPU"]');
    this.maxMemoryInput = page.locator('input[aria-label="最大内存"]');
    this.maxStorageInput = page.locator('input[aria-label="最大存储"]');
    this.maxNodesInput = page.locator('input[aria-label="最大节点"]');
    this.prioritySelect = page.getByText("选择优先级");
    this.submitButton = page.getByRole("button", { name: /创建|保存/ });
    this.cancelButton = page.getByRole("button", { name: "取消" });
  }

  /**
   * 导航到资源配额管理页
   */
  async goto() {
    await this.page.goto("/resource-quotas");
    await this.page.waitForLoadState("networkidle");
  }

  /**
   * 等待页面完全加载（表格数据或空状态）
   */
  async waitForPageReady() {
    // 等待加载指示器消失
    await this.loadingIndicator
      .waitFor({ state: "hidden", timeout: 15000 })
      .catch(() => {});
    // 等待表格或空状态出现
    await Promise.race([
      this.table.waitFor({ state: "visible", timeout: 10000 }),
      this.emptyState.waitFor({ state: "visible", timeout: 10000 }),
      this.errorState.waitFor({ state: "visible", timeout: 10000 }),
    ]).catch(() => {});
  }

  /**
   * 获取表格行数
   */
  async getRowCount(): Promise<number> {
    return this.tableRows.count();
  }

  /**
   * 获取指定行的配置名称
   */
  async getConfigNameAtRow(rowIndex: number): Promise<string | null> {
    return this.tableRows.nth(rowIndex).locator("td").first().textContent();
  }

  /**
   * 获取所有配置名称
   */
  async getAllConfigNames(): Promise<string[]> {
    const rows = await this.tableRows.all();
    const names: string[] = [];
    for (const row of rows) {
      const name = await row.locator("td").first().textContent();
      if (name) names.push(name.trim());
    }
    return names;
  }

  /**
   * 点击新建配置按钮
   */
  async clickCreate() {
    await this.createButton.click();
    // 等待 Modal 出现
    await this.configNameInput.waitFor({ state: "visible", timeout: 5000 });
  }

  /**
   * 点击指定行的编辑按钮
   */
  async clickEditAtRow(rowIndex: number) {
    const editButton = this.tableRows
      .nth(rowIndex)
      .getByRole("button", { name: "编辑" });
    await editButton.click();
    // 等待 Modal 出现
    await this.configNameInput.waitFor({ state: "visible", timeout: 5000 });
  }

  /**
   * 通过配置名称点击编辑
   */
  async clickEditByName(configName: string) {
    const row = this.tableRows.filter({ hasText: configName });
    await row.getByRole("button", { name: "编辑" }).click();
    await this.configNameInput.waitFor({ state: "visible", timeout: 5000 });
  }

  /**
   * 填写配额表单
   */
  async fillForm(data: {
    configName?: string;
    role?: string;
    maxGpu?: string;
    maxCpu?: string;
    maxMemory?: string;
    maxStorage?: string;
    maxNodes?: string;
    priority?: string;
  }) {
    if (data.configName !== undefined) {
      await this.configNameInput.clear();
      await this.configNameInput.fill(data.configName);
    }

    if (data.role) {
      await this.selectDropdown(this.roleSelect, data.role);
    }

    if (data.maxGpu !== undefined) {
      await this.maxGpuInput.clear();
      await this.maxGpuInput.fill(data.maxGpu);
    }

    if (data.maxCpu !== undefined) {
      await this.maxCpuInput.clear();
      await this.maxCpuInput.fill(data.maxCpu);
    }

    if (data.maxMemory !== undefined) {
      await this.maxMemoryInput.clear();
      await this.maxMemoryInput.fill(data.maxMemory);
    }

    if (data.maxStorage !== undefined) {
      await this.maxStorageInput.clear();
      await this.maxStorageInput.fill(data.maxStorage);
    }

    if (data.maxNodes !== undefined) {
      await this.maxNodesInput.scrollIntoViewIfNeeded();
      await this.maxNodesInput.clear();
      await this.maxNodesInput.fill(data.maxNodes);
    }

    if (data.priority) {
      await this.prioritySelect.scrollIntoViewIfNeeded();
      await this.selectDropdown(this.prioritySelect, data.priority);
    }
  }

  /**
   * 选择 Cloudscape Select 下拉选项
   */
  private async selectDropdown(selectLocator: Locator, optionText: string) {
    // 确保 Select 触发器可见
    await selectLocator.scrollIntoViewIfNeeded();
    // Cloudscape Select 组件需要先点击打开下拉
    await selectLocator.click();
    // 等待下拉选项出现并点击
    const option = this.page.getByRole("option", { name: optionText });
    await option.waitFor({ state: "visible", timeout: 3000 });
    await option.click();
  }

  /**
   * 提交表单
   */
  async submitForm() {
    await this.submitButton.click();
  }

  /**
   * 取消表单
   */
  async cancelForm() {
    await this.cancelButton.click();
  }

  /**
   * 创建新的资源配额
   */
  async createQuota(data: {
    configName: string;
    role: string;
    maxGpu?: string;
    maxCpu?: string;
    maxMemory?: string;
    maxStorage?: string;
    maxNodes?: string;
    priority: string;
  }) {
    await this.clickCreate();
    await this.fillForm(data);
    await this.submitForm();
  }

  /**
   * 等待 Modal 关闭
   */
  async waitForModalClose() {
    await this.configNameInput.waitFor({ state: "hidden", timeout: 10000 });
  }

  /**
   * 检查表单错误信息是否显示
   */
  async hasFormError(errorText: string): Promise<boolean> {
    const error = this.page.getByText(errorText);
    return error.isVisible();
  }

  /**
   * 获取 Modal 标题
   */
  async getModalTitle(): Promise<string | null> {
    return this.page
      .locator("h2")
      .filter({ hasText: /新建资源配额|编辑资源配额/ })
      .textContent();
  }

  /**
   * 检查页面是否存在指定的配置
   */
  async hasConfig(configName: string): Promise<boolean> {
    const row = this.tableRows.filter({ hasText: configName });
    return (await row.count()) > 0;
  }

  /**
   * 检查表格是否显示了正确的列
   */
  async verifyTableHeaders() {
    await expect(this.headerConfigName).toBeVisible();
    await expect(this.headerRole).toBeVisible();
    await expect(this.headerMaxGpu).toBeVisible();
    await expect(this.headerMaxCpu).toBeVisible();
    await expect(this.headerMaxMemory).toBeVisible();
    await expect(this.headerMaxNodes).toBeVisible();
    await expect(this.headerPriority).toBeVisible();
    await expect(this.headerActions).toBeVisible();
  }
}
