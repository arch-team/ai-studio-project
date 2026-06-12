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
import { loginViaAPI } from '../utils/auth';

test.describe('训练任务 CRUD 流程', () => {
  let mockApi: MockApi;

  test.beforeEach(async ({ page }) => {
    // 真实登录获取会话（auth 接口不被 mock），业务接口由 MockApi 拦截
    await loginViaAPI(page);
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
      // 默认 8 GPU/节点会超出 dev 环境配额（engineer 上限 4），降到配额内
      await createPage.fillGpuPerNode(1);

      // 提交并验证跳转
      await createPage.submitAndWaitForRedirect();
      await expect(page).toHaveURL(/\/training-jobs\/\d+/);
    });

    test('成功创建训练任务 - 完整配置', async ({ page }) => {
      const createPage = new CreateTrainingJobPage(page);
      await createPage.goto();

      // 节点/GPU 受 dev 配额限制（engineer 上限 4 GPU），用配额内组合
      await createPage.fillCompleteForm({
        jobName: 'llama2-finetuning',
        description: 'LLaMA 2 微调训练任务',
        priority: 'high',
        imageUri: '123456789012.dkr.ecr.us-west-2.amazonaws.com/training:v1',
        entryPoint: '/opt/ml/code/train.py',
        distributionStrategy: 'fsdp',
        nodeCount: 2,
        gpuPerNode: 2,
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

      // 必须通过前端校验（合法 ECR URI / 路径 / 配额内 GPU），请求才会发出并收到 mock 的 400
      await createPage.fillRequiredFields({
        jobName: 'duplicate-name',
        imageUri: '123456789012.dkr.ecr.us-west-2.amazonaws.com/training:v1',
        entryPoint: '/opt/ml/code/train.py',
      });
      await createPage.fillGpuPerNode(1);

      await createPage.clickCreate();

      // 等待并验证错误信息（Flashbar 含 header 与 content 两个同文本节点，取第一个）
      await expect(page.locator('text=任务名称已存在').first()).toBeVisible({ timeout: 5000 });
    });
  });

  // =========================================
  // 查看任务列表
  // =========================================
  test.describe('查看任务列表', () => {
    test('显示任务列表数据', async ({ page }) => {
      // 表格名称列渲染 job_name（非 display_name），断言以 job_name 为准
      await page.goto('/training-jobs');
      await page.waitForLoadState('networkidle');

      await expect(page.locator('text=llama2-finetune-001')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('text=bert-pretrain-002')).toBeVisible({ timeout: 10000 });
    });

    test('状态筛选 - 运行中', async ({ page }) => {
      const listPage = new TrainingJobListPage(page);
      await listPage.goto();
      await listPage.waitForTableLoad();

      await listPage.selectStatusFilter('运行中');

      // 验证只显示运行中的任务
      await expect(page.locator('text=llama2-finetune-001')).toBeVisible();
      // 已完成的任务不应显示
      await expect(page.locator('text=bert-pretrain-002')).not.toBeVisible();
    });

    test('状态筛选 - 已完成', async ({ page }) => {
      const listPage = new TrainingJobListPage(page);
      await listPage.goto();
      await listPage.waitForTableLoad();

      await listPage.selectStatusFilter('已完成');

      // 验证只显示已完成的任务
      await expect(page.locator('text=bert-pretrain-002')).toBeVisible();
      // 运行中的任务不应显示
      await expect(page.locator('text=llama2-finetune-001')).not.toBeVisible();
    });

    test('优先级筛选 - 高优先级', async ({ page }) => {
      const listPage = new TrainingJobListPage(page);
      await listPage.goto();
      await listPage.waitForTableLoad();

      await listPage.selectPriorityFilter('高');

      // 验证只显示高优先级任务
      await expect(page.locator('text=llama2-finetune-001')).toBeVisible();
    });

    test('点击任务跳转到详情页', async ({ page }) => {
      const listPage = new TrainingJobListPage(page);
      await listPage.goto();
      await listPage.waitForTableLoad();

      await listPage.clickJobLink('llama2-finetune-001');

      // 验证跳转到详情页
      await expect(page).toHaveURL(/\/training-jobs\/1/);
    });

    test('刷新列表', async ({ page }) => {
      const listPage = new TrainingJobListPage(page);
      await listPage.goto();
      await listPage.waitForTableLoad();

      await listPage.clickRefresh();

      // 验证仍在列表页
      await expect(page).toHaveURL('/training-jobs');
      // 验证数据仍然显示
      await expect(page.locator('text=llama2-finetune-001')).toBeVisible({ timeout: 5000 });
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

    test('任务不存在显示错误', async ({ page }) => {
      // 真实后端对不存在 ID 返回 404，详情页应渲染错误信息而非一直 loading
      await page.goto('/training-jobs/99999');
      await page.waitForLoadState('networkidle');

      // 验证错误信息（详情页错误态渲染 error.message）
      await expect(
        page.locator('text=/不存在|not found|加载失败/i').first()
      ).toBeVisible({ timeout: 15000 });
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
    test('完整导航流程', async ({ page }) => {
      // 1. 打开列表页
      const listPage = new TrainingJobListPage(page);
      await listPage.goto();
      await listPage.waitForTableLoad();
      await expect(page).toHaveURL('/training-jobs');

      // 2. 点击任务进入详情页
      await listPage.clickJobLink('llama2-finetune-001');
      await expect(page).toHaveURL(/\/training-jobs\/1/);

      // 3. 通过面包屑返回列表页（侧边导航有同名链接，限定在面包屑区域内）
      await page
        .locator('nav[aria-label="面包屑导航"]')
        .getByRole('link', { name: '训练任务' })
        .click();
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
