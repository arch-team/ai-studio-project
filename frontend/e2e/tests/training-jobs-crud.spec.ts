/**
 * 训练任务 CRUD 流程 E2E 测试
 *
 * 测试创建、查看、筛选等核心流程
 */

import { test, expect } from '@playwright/test';
import { TrainingJobListPage } from '../pages/TrainingJobListPage';
import { TrainingJobDetailPage } from '../pages/TrainingJobDetailPage';
import { CreateTrainingJobPage } from '../pages/CreateTrainingJobPage';
import { MockApi } from '../utils/mockApi';

test.describe('训练任务 CRUD 流程', () => {
  let mockApi: MockApi;

  test.beforeEach(async ({ page }) => {
    mockApi = new MockApi(page);
    await mockApi.setupDefaultMocks();
  });

  // =========================================
  // 创建训练任务
  // =========================================
  test.describe('创建训练任务', () => {
    test('成功创建训练任务 - 必填字段', async ({ page }) => {
      const createPage = new CreateTrainingJobPage(page);
      await createPage.goto();

      // 验证页面标题
      await expect(page.locator('h1')).toContainText('创建训练任务');

      // 填写必填字段
      await createPage.fillRequiredFields({
        jobName: 'test-job-001',
        imageUri: '123456789012.dkr.ecr.us-west-2.amazonaws.com/training:v1',
        entryPoint: '/opt/ml/code/train.py',
      });

      // 提交并验证跳转
      await createPage.submitAndWaitForRedirect();
      await expect(page).toHaveURL(/\/training-jobs\/\d+/);
    });

    test.skip('成功创建训练任务 - 完整配置', async ({ page }) => {
      // TODO: 需要为 Cloudscape Select 组件添加 data-testid 后启用
      const createPage = new CreateTrainingJobPage(page);
      await createPage.goto();

      await createPage.fillCompleteForm({
        jobName: 'llama2-finetuning',
        description: 'LLaMA 2 微调训练任务',
        priority: 'high',
        imageUri: '123456789012.dkr.ecr.us-west-2.amazonaws.com/training:v1',
        entryPoint: '/opt/ml/code/train.py',
        distributionStrategy: 'fsdp',
        nodeCount: 4,
        gpuPerNode: 8,
      });

      await createPage.submitAndWaitForRedirect();
      await expect(page).toHaveURL(/\/training-jobs\/\d+/);
    });

    test('表单验证 - 必填字段为空', async ({ page }) => {
      const createPage = new CreateTrainingJobPage(page);
      await createPage.goto();

      // 直接点击创建
      await createPage.clickCreate();

      // 验证错误提示显示
      await expect(createPage.jobNameError).toBeVisible();
      await expect(createPage.imageUriError).toBeVisible();
      await expect(createPage.entryPointError).toBeVisible();
    });

    test('表单验证 - 任务名称过长', async ({ page }) => {
      const createPage = new CreateTrainingJobPage(page);
      await createPage.goto();

      // 填写超长名称 (超过 100 字符)
      const longName = 'a'.repeat(101);
      await createPage.fillJobName(longName);
      await createPage.fillImageUri('image:v1');
      await createPage.fillEntryPoint('train.py');

      await createPage.clickCreate();

      // 验证名称长度错误
      await expect(page.locator('text=任务名称不能超过')).toBeVisible();
    });

    test('取消创建返回列表页', async ({ page }) => {
      const createPage = new CreateTrainingJobPage(page);
      await createPage.goto();

      // 填写部分内容
      await createPage.fillJobName('test-job');

      // 点击取消
      await createPage.clickCancel();

      // 验证返回列表页
      await expect(page).toHaveURL('/training-jobs');
    });

    test('创建失败显示错误信息', async ({ page }) => {
      // 设置 Mock 返回错误
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockCreateTrainingJob({
        error: { status: 400, message: '任务名称已存在' },
      });

      const createPage = new CreateTrainingJobPage(page);
      await createPage.goto();

      await createPage.fillRequiredFields({
        jobName: 'duplicate-name',
        imageUri: 'image:v1',
        entryPoint: 'train.py',
      });

      await createPage.clickCreate();

      // 等待并验证错误信息
      await expect(page.locator('text=任务名称已存在')).toBeVisible({ timeout: 5000 });
    });
  });

  // =========================================
  // 查看任务列表
  // =========================================
  test.describe('查看任务列表', () => {
    test.skip('显示任务列表数据', async ({ page }) => {
      // TODO: 列表页 Mock 需要更复杂的设置，暂时跳过
      // Mock 必须在页面导航前设置，以拦截初始 API 请求
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();

      // 导航到列表页（Mock 会拦截 API 请求）
      await page.goto('/training-jobs');
      await page.waitForLoadState('networkidle');

      // 等待表格数据加载（可能是空状态或实际数据）
      await page.waitForTimeout(1000);

      // 验证任务列表显示（使用 display_name 字段）
      await expect(page.locator('text=LLaMA 2 微调训练')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('text=BERT 预训练')).toBeVisible({ timeout: 10000 });
    });

    test.skip('状态筛选 - 运行中', async ({ page }) => {
      // TODO: 筛选功能需要后端配合或更复杂的 Mock 逻辑
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();

      const listPage = new TrainingJobListPage(page);
      await listPage.goto();
      await listPage.waitForTableLoad();

      await listPage.selectStatusFilter('运行中');

      // 验证只显示运行中的任务
      await expect(page.locator('text=LLaMA 2 微调训练')).toBeVisible();
      // 已完成的任务不应显示
      await expect(page.locator('text=BERT 预训练')).not.toBeVisible();
    });

    test.skip('状态筛选 - 已完成', async ({ page }) => {
      // TODO: 筛选功能需要后端配合或更复杂的 Mock 逻辑
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();

      const listPage = new TrainingJobListPage(page);
      await listPage.goto();
      await listPage.waitForTableLoad();

      await listPage.selectStatusFilter('已完成');

      // 验证只显示已完成的任务
      await expect(page.locator('text=BERT 预训练')).toBeVisible();
      // 运行中的任务不应显示
      await expect(page.locator('text=LLaMA 2 微调训练')).not.toBeVisible();
    });

    test.skip('优先级筛选 - 高优先级', async ({ page }) => {
      // TODO: 筛选功能需要后端配合或更复杂的 Mock 逻辑
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();

      const listPage = new TrainingJobListPage(page);
      await listPage.goto();
      await listPage.waitForTableLoad();

      await listPage.selectPriorityFilter('高');

      // 验证只显示高优先级任务
      await expect(page.locator('text=LLaMA 2 微调训练')).toBeVisible();
    });

    test.skip('点击任务跳转到详情页', async ({ page }) => {
      // TODO: 需要列表页 Mock 工作后才能测试
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobDetail();

      const listPage = new TrainingJobListPage(page);
      await listPage.goto();
      await listPage.waitForTableLoad();

      await listPage.clickJobLink('LLaMA 2 微调训练');

      // 验证跳转到详情页
      await expect(page).toHaveURL(/\/training-jobs\/1/);
    });

    test.skip('刷新列表', async ({ page }) => {
      // TODO: 需要列表页 Mock 工作后才能测试
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();

      const listPage = new TrainingJobListPage(page);
      await listPage.goto();
      await listPage.waitForTableLoad();

      await listPage.clickRefresh();

      // 验证仍在列表页
      await expect(page).toHaveURL('/training-jobs');
      // 验证数据仍然显示
      await expect(page.locator('text=LLaMA 2 微调训练')).toBeVisible({ timeout: 5000 });
    });

    test('点击创建按钮跳转到创建页', async ({ page }) => {
      const listPage = new TrainingJobListPage(page);
      await listPage.goto();

      await listPage.clickCreate();

      // 验证跳转到创建页
      await expect(page).toHaveURL(/.*create/);
    });
  });

  // =========================================
  // 查看任务详情
  // =========================================
  test.describe('查看任务详情', () => {
    test('显示任务概览信息', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobDetail();

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(1);
      await detailPage.waitForContentLoad();

      // 验证任务名称
      await expect(page.locator('h1')).toContainText('llama2-finetune-001');

      // 验证状态显示
      await expect(page.locator('text=运行中')).toBeVisible({ timeout: 5000 });

      // 验证优先级显示
      await expect(page.locator('text=高')).toBeVisible({ timeout: 5000 });
    });

    test('显示训练进度', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobDetail();

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(1);
      await detailPage.waitForContentLoad();

      // 验证进度信息
      await expect(page.locator('text=当前 Epoch')).toBeVisible({ timeout: 5000 });
      await expect(page.locator('text=3 / 10')).toBeVisible({ timeout: 5000 });
    });

    test('切换到配置信息 Tab', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobDetail();

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(1);
      await detailPage.waitForContentLoad();

      await detailPage.switchToTab('config');

      // 验证配置信息显示
      await expect(page.locator('text=ml.p4d.24xlarge')).toBeVisible({ timeout: 5000 });
      await expect(page.locator('text=实例类型')).toBeVisible({ timeout: 5000 });
    });

    test('切换到检查点 Tab', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobDetail();

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(1);
      await detailPage.waitForContentLoad();

      await detailPage.switchToTab('checkpoints');

      // 验证检查点表格或空状态
      const hasTable = await page.locator('text=检查点名称').isVisible();
      const hasEmpty = await page.locator('text=暂无检查点').isVisible();
      expect(hasTable || hasEmpty).toBeTruthy();
    });

    test.skip('任务不存在显示错误', async ({ page }) => {
      // TODO: 需要更精确的 Mock 设置
      // 设置 Mock 返回 404
      mockApi = new MockApi(page);
      await mockApi.mockApiError('training-jobs/999', 404, '任务不存在');

      await page.goto('/training-jobs/999');

      // 验证错误信息
      await expect(page.locator('text=任务不存在')).toBeVisible({ timeout: 5000 });
    });

    test('刷新任务详情', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobDetail();

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(1);
      await detailPage.waitForContentLoad();

      await detailPage.clickRefresh();

      // 验证数据仍然显示
      await expect(page.locator('h1')).toContainText('llama2-finetune-001');
    });
  });

  // =========================================
  // 从列表导航到详情再返回
  // =========================================
  test.describe('列表与详情页导航', () => {
    test.skip('完整导航流程', async ({ page }) => {
      // TODO: 需要列表页 Mock 工作后才能测试
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobDetail();

      // 1. 打开列表页
      const listPage = new TrainingJobListPage(page);
      await listPage.goto();
      await listPage.waitForTableLoad();
      await expect(page).toHaveURL('/training-jobs');

      // 2. 点击任务进入详情页
      await listPage.clickJobLink('LLaMA 2 微调训练');
      await expect(page).toHaveURL(/\/training-jobs\/1/);

      // 3. 通过面包屑返回列表页
      await page.click('text=训练任务');
      await expect(page).toHaveURL('/training-jobs');
    });

    test('从列表页创建任务后返回列表', async ({ page }) => {
      // 1. 打开列表页
      const listPage = new TrainingJobListPage(page);
      await listPage.goto();

      // 2. 点击创建
      await listPage.clickCreate();
      await expect(page).toHaveURL(/.*create/);

      // 3. 取消创建
      const createPage = new CreateTrainingJobPage(page);
      await createPage.clickCancel();

      // 4. 验证返回列表页
      await expect(page).toHaveURL('/training-jobs');
    });
  });
});
