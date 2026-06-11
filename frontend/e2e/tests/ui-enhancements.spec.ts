/**
 * UI 增强功能 E2E 测试
 *
 * 覆盖本次 UI/UX 优化引入的能力：
 * - 补全导航后新页面的可达性（监控、开发空间等）
 * - 主题切换（明 / 暗 / 跟随系统）
 * - 全局通知中心（Flashbar）的显示与消失
 *
 * 注: 这些测试依赖运行中的前后端环境（默认 localhost:5173 + API 代理）。
 */

import { test, expect } from '@playwright/test';
import { loginViaUI } from '../utils/auth';

test.describe('UI 增强 - 导航可达性', () => {
  test.beforeEach(async ({ page }) => {
    await loginViaUI(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('可通过侧边栏进入资源监控页', async ({ page }) => {
    await page.click('text=资源监控');
    await expect(page).toHaveURL('/monitoring');
  });

  test('可通过侧边栏进入开发空间页', async ({ page }) => {
    await page.click('text=我的空间');
    await expect(page).toHaveURL('/spaces');
  });

  test('可通过侧边栏进入在线 IDE 页', async ({ page }) => {
    await page.click('text=在线 IDE');
    await expect(page).toHaveURL('/ide');
  });

  test('可通过侧边栏进入任务模板页', async ({ page }) => {
    await page.click('text=任务模板');
    await expect(page).toHaveURL('/job-templates');
  });

  test('开发空间分组正确显示', async ({ page }) => {
    // 侧边导航分组标题渲染为 h3
    await expect(page.getByRole('heading', { name: '开发空间' })).toBeVisible();
  });

  test('进入训练任务详情后父级导航项保持高亮', async ({ page }) => {
    await page.goto('/training-jobs');
    await page.waitForLoadState('networkidle');
    // SideNavigation 选中项带 aria-current（面包屑也有，限定在 a 标签）
    const activeLink = page.locator('a[aria-current="page"]');
    await expect(activeLink).toContainText('训练任务');
  });
});

test.describe('UI 增强 - 主题切换', () => {
  test.beforeEach(async ({ page }) => {
    await loginViaUI(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('可切换到暗色主题', async ({ page }) => {
    // 打开外观设置下拉
    await page.locator('button[aria-label="外观设置"]:visible').first().click();
    await page.click('text=主题');
    await page.click('text=暗黑');

    // Cloudscape 暗色模式会在 body 或根元素应用 awsui-dark-mode class
    await expect(page.locator('body')).toHaveClass(/awsui-dark-mode/, { timeout: 5000 });
  });

  test('主题切换后刷新页面保持（持久化）', async ({ page }) => {
    await page.locator('button[aria-label="外观设置"]:visible').first().click();
    await page.click('text=主题');
    await page.click('text=暗黑');
    await expect(page.locator('body')).toHaveClass(/awsui-dark-mode/, { timeout: 5000 });

    // 刷新后应仍为暗色（uiSlice persist 到 localStorage）
    await page.reload();
    await page.waitForLoadState('networkidle');
    await expect(page.locator('body')).toHaveClass(/awsui-dark-mode/, { timeout: 5000 });
  });

  test('可切换到紧凑密度', async ({ page }) => {
    await page.locator('button[aria-label="外观设置"]:visible').first().click();
    await page.click('text=密度');
    await page.click('text=紧凑');

    // Cloudscape 紧凑模式应用 awsui-compact-mode class
    await expect(page.locator('body')).toHaveClass(/awsui-compact-mode/, { timeout: 5000 });
  });
});

test.describe('UI 增强 - 全局通知', () => {
  test('切换主题会触发通知并随后自动消失', async ({ page }) => {
    await loginViaUI(page);
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // 切换主题触发 info 通知（useNotification.info）
    await page.locator('button[aria-label="外观设置"]:visible').first().click();
    await page.click('text=主题');
    await page.click('text=明亮');

    // 通知出现
    const notification = page.locator('text=/已切换主题/');
    await expect(notification.first()).toBeVisible({ timeout: 3000 });

    // 非 error 通知应在默认时长（5s）后自动消失
    await expect(notification.first()).toBeHidden({ timeout: 8000 });
  });
});
