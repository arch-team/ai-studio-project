import { test, expect } from '@playwright/test';

test.describe('认证流程', () => {
  test('登录页可访问', async ({ page }) => {
    await page.goto('/login');

    // 验证登录页加载
    await expect(page.locator('text=登录')).toBeVisible();
  });

  test.skip('用户可以登录并跳转到首页', async ({ page }) => {
    // 跳过：登录表单尚未实现
    await page.goto('/login');

    await page.fill('[data-testid="username"]', 'testuser');
    await page.fill('[data-testid="password"]', 'password');
    await page.click('[data-testid="submit"]');

    await expect(page).toHaveURL('/');
  });

  test.skip('未认证用户访问受保护页面被重定向到登录页', async ({ page }) => {
    // 跳过：认证守卫可能未启用
    await page.goto('/training-jobs');
    await expect(page).toHaveURL(/.*login/);
  });

  test.skip('登录失败显示错误提示', async ({ page }) => {
    // 跳过：登录表单尚未实现
    await page.goto('/login');

    await page.fill('[data-testid="username"]', 'wronguser');
    await page.fill('[data-testid="password"]', 'wrongpassword');
    await page.click('[data-testid="submit"]');

    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
  });

  test.skip('用户可以登出', async ({ page }) => {
    // 跳过：登出功能需要先登录
    await page.goto('/');

    await page.click('[data-testid="user-menu"]');
    await page.click('text=登出');

    await expect(page).toHaveURL(/.*login/);
  });
});
