/**
 * Create Training Job Page - Page Object
 *
 * 创建训练任务页面 Page Object
 */

import { Page, Locator } from '@playwright/test';
import { BasePage } from './BasePage';

/**
 * 创建训练任务页面 Page Object
 */
export class CreateTrainingJobPage extends BasePage {
  // === Basic Config ===
  readonly jobNameInput: Locator;
  readonly descriptionTextarea: Locator;
  readonly prioritySelect: Locator;

  // === Container Config ===
  readonly imageUriInput: Locator;
  readonly entryPointInput: Locator;

  // === Distributed Config ===
  readonly ddpTile: Locator;
  readonly fsdpTile: Locator;
  readonly deepspeedTile: Locator;
  readonly horovodTile: Locator;
  readonly instanceTypeSelect: Locator;
  readonly nodeCountInput: Locator;
  readonly gpuPerNodeInput: Locator;

  // === Actions ===
  readonly createButton: Locator;
  readonly cancelButton: Locator;

  // === Error Messages ===
  readonly jobNameError: Locator;
  readonly imageUriError: Locator;
  readonly entryPointError: Locator;
  readonly errorContainer: Locator;

  constructor(page: Page) {
    super(page);

    // Basic Config
    this.jobNameInput = page.locator('input[placeholder="my-training-job"]');
    this.descriptionTextarea = page.locator('textarea[placeholder*="训练任务描述"]');
    // Cloudscape Select 组件使用 button 触发下拉
    this.prioritySelect = page.locator('[class*="form-field"]:has-text("优先级")').locator('button').first();

    // Container Config
    this.imageUriInput = page.locator('input[placeholder*="ecr"]');
    this.entryPointInput = page.locator('input[placeholder*="train.py"]');

    // Distributed Strategy Tiles
    this.ddpTile = page.locator('text=PyTorch DDP');
    this.fsdpTile = page.locator('text=PyTorch FSDP');
    this.deepspeedTile = page.locator('text=DeepSpeed');
    this.horovodTile = page.locator('text=Horovod');

    // Instance Config
    this.instanceTypeSelect = page.locator('[class*="form-field"]:has-text("实例类型")').locator('button').first();
    // Cloudscape Input type=number 渲染为 role=spinbutton，aria-label 来自 FormField label
    this.nodeCountInput = page.getByRole('spinbutton', { name: '节点数量' });
    this.gpuPerNodeInput = page.getByRole('spinbutton', { name: '每节点 GPU 数量' });

    // Actions
    this.createButton = page.locator('button:has-text("创建任务")');
    this.cancelButton = page.locator('button:has-text("取消")');

    // Error Messages
    this.jobNameError = page.locator('text=请输入任务名称');
    this.imageUriError = page.locator('text=请输入容器镜像');
    this.entryPointError = page.locator('text=请输入训练脚本');
    this.errorContainer = page.locator('[color="text-status-error"]');
  }

  /**
   * 导航到创建页面
   */
  async goto() {
    await this.page.goto('/training-jobs/create');
    await this.waitForPageLoad();
  }

  /**
   * 填写任务名称
   */
  async fillJobName(name: string) {
    await this.jobNameInput.fill(name);
  }

  /**
   * 填写描述
   */
  async fillDescription(description: string) {
    await this.descriptionTextarea.fill(description);
  }

  /**
   * 选择优先级
   */
  async selectPriority(priority: 'high' | 'medium' | 'low') {
    // 找到优先级标签旁边的 select 按钮
    const formField = this.page.locator('label:has-text("优先级")').locator('..').locator('..');
    const selectButton = formField.locator('button[class*="select"], button[class*="trigger"]').first();
    await selectButton.click();

    // 等待下拉菜单出现并选择选项
    const labelMap = { high: '高', medium: '中', low: '低' };
    await this.page.locator(`[role="option"]:has-text("${labelMap[priority]}")`).click();
  }

  /**
   * 填写容器镜像 URI
   */
  async fillImageUri(uri: string) {
    await this.imageUriInput.fill(uri);
  }

  /**
   * 填写训练脚本路径
   */
  async fillEntryPoint(path: string) {
    await this.entryPointInput.fill(path);
  }

  /**
   * 选择分布式策略
   */
  async selectDistributionStrategy(strategy: 'ddp' | 'fsdp' | 'deepspeed' | 'horovod') {
    const tileMap = {
      ddp: this.ddpTile,
      fsdp: this.fsdpTile,
      deepspeed: this.deepspeedTile,
      horovod: this.horovodTile,
    };
    await tileMap[strategy].click();
  }

  /**
   * 选择实例类型
   */
  async selectInstanceType(instanceType: string) {
    await this.instanceTypeSelect.click();
    await this.page.locator(`[role="option"]:has-text("${instanceType}")`).click();
  }

  /**
   * 填写节点数量
   */
  async fillNodeCount(count: number) {
    await this.nodeCountInput.fill(String(count));
  }

  /**
   * 填写每节点 GPU 数量
   */
  async fillGpuPerNode(count: number) {
    await this.gpuPerNodeInput.fill(String(count));
  }

  /**
   * 点击创建按钮
   */
  async clickCreate() {
    await this.createButton.click();
  }

  /**
   * 点击取消按钮
   */
  async clickCancel() {
    await this.cancelButton.click();
  }

  /**
   * 填写必填字段
   */
  async fillRequiredFields(data: { jobName: string; imageUri: string; entryPoint: string }) {
    await this.fillJobName(data.jobName);
    await this.fillImageUri(data.imageUri);
    await this.fillEntryPoint(data.entryPoint);
  }

  /**
   * 填写完整表单
   */
  async fillCompleteForm(data: {
    jobName: string;
    description?: string;
    priority?: 'high' | 'medium' | 'low';
    imageUri: string;
    entryPoint: string;
    distributionStrategy?: 'ddp' | 'fsdp' | 'deepspeed' | 'horovod';
    instanceType?: string;
    nodeCount?: number;
    gpuPerNode?: number;
  }) {
    await this.fillJobName(data.jobName);
    if (data.description) {
      await this.fillDescription(data.description);
    }
    if (data.priority) {
      await this.selectPriority(data.priority);
    }
    await this.fillImageUri(data.imageUri);
    await this.fillEntryPoint(data.entryPoint);
    if (data.distributionStrategy) {
      await this.selectDistributionStrategy(data.distributionStrategy);
    }
    if (data.instanceType) {
      await this.selectInstanceType(data.instanceType);
    }
    if (data.nodeCount !== undefined) {
      await this.fillNodeCount(data.nodeCount);
    }
    if (data.gpuPerNode !== undefined) {
      await this.fillGpuPerNode(data.gpuPerNode);
    }
  }

  /**
   * 提交表单并等待跳转
   */
  async submitAndWaitForRedirect() {
    await this.clickCreate();
    await this.page.waitForURL(/\/training-jobs\/\d+/, { timeout: 10000 });
  }

  /**
   * 检查任务名称错误是否显示
   */
  async hasJobNameError(): Promise<boolean> {
    return this.jobNameError.isVisible();
  }

  /**
   * 检查容器镜像错误是否显示
   */
  async hasImageUriError(): Promise<boolean> {
    return this.imageUriError.isVisible();
  }

  /**
   * 检查训练脚本错误是否显示
   */
  async hasEntryPointError(): Promise<boolean> {
    return this.entryPointError.isVisible();
  }

  /**
   * 检查是否显示 API 错误
   */
  async hasApiError(): Promise<boolean> {
    return this.errorContainer.isVisible();
  }

  /**
   * 获取 API 错误消息
   */
  async getApiErrorMessage(): Promise<string | null> {
    return this.errorContainer.textContent();
  }

  /**
   * 检查创建按钮是否正在加载
   */
  async isSubmitting(): Promise<boolean> {
    // Cloudscape Button loading 状态会改变 aria 属性
    const ariaDisabled = await this.createButton.getAttribute('aria-disabled');
    return ariaDisabled === 'true';
  }
}
