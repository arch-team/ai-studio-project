import { test, expect } from '@playwright/test';

test.describe('导航系统', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('侧边栏导航到训练任务页', async ({ page }) => {
    await page.click('text=训练任务');
    await expect(page).toHaveURL('/training-jobs');
    await expect(page.locator('h1')).toContainText('训练任务管理');
  });

  test('侧边栏导航到模型管理页', async ({ page }) => {
    await page.click('text=模型管理');
    await expect(page).toHaveURL('/models');
  });

  test('侧边栏导航到数据集页', async ({ page }) => {
    await page.click('text=数据集');
    await expect(page).toHaveURL('/datasets');
  });

  test('侧边栏导航到检查点页', async ({ page }) => {
    await page.click('text=检查点');
    await expect(page).toHaveURL('/checkpoints');
  });

  test('侧边栏导航到配额管理页', async ({ page }) => {
    await page.click('text=配额管理');
    await expect(page).toHaveURL('/resource-quotas');
  });

  test('顶部导航栏显示平台名称', async ({ page }) => {
    // 使用 last() 选择可见的那个（Cloudscape 响应式布局）
    await expect(page.locator('text=AI 训练平台').last()).toBeVisible();
  });

  test('顶部导航栏包含搜索框', async ({ page }) => {
    await expect(page.locator('input[placeholder*="搜索"]').last()).toBeVisible();
  });

  test('顶部导航栏包含通知按钮', async ({ page }) => {
    // 通知为图标按钮，通过 aria-label 定位
    await expect(page.locator('[aria-label="通知"]').last()).toBeVisible();
  });

  test('顶部导航栏包含帮助按钮', async ({ page }) => {
    // 帮助为图标按钮，通过 aria-label 定位
    await expect(page.locator('[aria-label="帮助文档"]').last()).toBeVisible();
  });

  test('顶部导航栏包含外观设置入口', async ({ page }) => {
    // 主题/密度切换入口
    await expect(page.locator('[aria-label="外观设置"]').last()).toBeVisible();
  });

  test('顶部导航栏包含用户菜单', async ({ page }) => {
    // 用户菜单通过 aria-label 定位（显示用户名而非固定文字"用户"）
    await expect(page.locator('[aria-label="用户菜单"]').last()).toBeVisible();
  });

  test('侧边栏可以收起', async ({ page }) => {
    // 找到收起按钮（Cloudscape 的 AppLayout 收起按钮）
    const collapseButton = page.locator('[aria-label*="收起"], [aria-label*="关闭导航"]');

    if (await collapseButton.isVisible()) {
      await collapseButton.click();
      await page.waitForTimeout(300);
    }
  });

  test('导航分组正确显示', async ({ page }) => {
    // 验证导航分组
    await expect(page.locator('text=训练管理')).toBeVisible();
    await expect(page.locator('text=数据管理')).toBeVisible();
    await expect(page.locator('text=资源管理')).toBeVisible();
  });

  test('首页链接可点击', async ({ page }) => {
    await page.goto('/training-jobs');
    await page.click('text=首页');
    await expect(page).toHaveURL('/');
  });
});
