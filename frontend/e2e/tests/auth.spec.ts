import { test, expect } from '@playwright/test';
import { TEST_CREDENTIALS, loginViaUI } from '../utils/auth';

test.describe('认证流程', () => {
  test('登录页可访问', async ({ page }) => {
    await page.goto('/login');

    // 验证登录页加载（标题与提交按钮）
    await expect(page.getByRole('heading', { name: '登录' })).toBeVisible();
    await expect(page.getByRole('button', { name: '登录' })).toBeVisible();
  });

  test('用户可以登录并跳转到首页', async ({ page }) => {
    await loginViaUI(page);

    await expect(page).toHaveURL('/');
    // 登录后应渲染主布局（侧边导航）
    await expect(page.getByRole('heading', { name: /工作台|首页|AI 训练平台/ }).first()).toBeVisible();
  });

  test('未认证用户访问受保护页面被重定向到登录页', async ({ page }) => {
    await page.goto('/training-jobs');
    await expect(page).toHaveURL(/.*login/);
  });

  test('登录失败显示错误提示', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    await page.locator('input').first().fill('wronguser');
    await page.locator('input[type="password"]').fill('WrongPassword1!');
    await page.getByRole('button', { name: '登录' }).click();

    // 仍停留在登录页并出现错误提示（后端返回 "Invalid credentials"）
    await expect(page).toHaveURL(/.*login/);
    await expect(
      page.getByText(/Invalid credentials|用户名或密码|登录失败/i).first(),
    ).toBeVisible({ timeout: 10000 });
  });

  test('用户可以登出', async ({ page }) => {
    await loginViaUI(page, TEST_CREDENTIALS);

    // Cloudscape TopNavigation 渲染桌面/移动两份菜单，取可见的那个
    await page.locator('[aria-label="用户菜单"]:visible').first().click();
    await page.getByText('退出登录').first().click();

    await expect(page).toHaveURL(/.*login/, { timeout: 10000 });
  });
});
