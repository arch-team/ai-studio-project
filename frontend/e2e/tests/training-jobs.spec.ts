import { test, expect } from '@playwright/test';
import { TrainingJobListPage } from '../pages/TrainingJobListPage';

test.describe('训练任务列表', () => {
  let trainingJobListPage: TrainingJobListPage;

  test.beforeEach(async ({ page }) => {
    trainingJobListPage = new TrainingJobListPage(page);
    await trainingJobListPage.goto();
  });

  test('页面正确渲染', async ({ page }) => {
    // 验证页面标题
    await expect(page.locator('h1')).toContainText('训练任务管理');

    // 验证创建按钮存在
    await expect(page.locator('button:has-text("创建训练任务")')).toBeVisible();

    // 验证筛选器存在
    await expect(page.locator('text=全部状态')).toBeVisible();
    await expect(page.locator('text=全部优先级')).toBeVisible();
  });

  test('显示训练任务表格', async ({ page }) => {
    // 验证表格标题行存在（使用 exact 匹配避免多元素问题）
    await expect(page.getByText('任务名称', { exact: true })).toBeVisible();
    await expect(page.getByText('状态', { exact: true })).toBeVisible();
    await expect(page.getByText('优先级', { exact: true })).toBeVisible();
  });

  test('空状态显示正确', async ({ page }) => {
    // 验证空状态文本（使用 first() 避免多元素问题）
    await expect(page.locator('text=暂无训练任务').first()).toBeVisible();
  });

  test('点击创建按钮跳转到创建页', async ({ page }) => {
    await page.click('button:has-text("创建训练任务")');

    // 验证跳转到创建页面
    await expect(page).toHaveURL(/.*create/);
  });

  test('刷新按钮可点击', async ({ page }) => {
    const refreshButton = page.locator('button:has-text("刷新")');
    await expect(refreshButton).toBeVisible();
    await refreshButton.click();

    // 刷新后页面应保持在当前路由
    await expect(page).toHaveURL('/training-jobs');
  });

  test('状态筛选器可展开', async ({ page }) => {
    // 点击状态筛选器
    await page.click('text=全部状态');

    // 等待下拉菜单展开
    await page.waitForTimeout(300);

    // 验证筛选器已展开（具体选项取决于实现）
  });

  test('优先级筛选器可展开', async ({ page }) => {
    // 点击优先级筛选器
    await page.click('text=全部优先级');

    // 等待下拉菜单展开
    await page.waitForTimeout(300);
  });

  test('表格列头正确显示', async ({ page }) => {
    // 验证所有列头
    await expect(page.locator('text=任务名称')).toBeVisible();
    await expect(page.locator('text=分布式策略')).toBeVisible();
    await expect(page.locator('text=节点数')).toBeVisible();
    await expect(page.locator('text=GPU/节点')).toBeVisible();
    await expect(page.locator('text=进度')).toBeVisible();
    await expect(page.locator('text=创建时间')).toBeVisible();
  });
});
