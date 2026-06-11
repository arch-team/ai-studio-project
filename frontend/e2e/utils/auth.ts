/**
 * E2E 测试认证工具
 *
 * 提供登录辅助函数，用于测试受保护的页面
 */

import { Page } from '@playwright/test';

/**
 * 默认测试账户凭据
 */
export const TEST_CREDENTIALS = {
  username: process.env.E2E_USERNAME || 'admin',
  password: process.env.E2E_PASSWORD || 'Admin123!',
};

/**
 * 通过 UI 登录
 *
 * 导航到登录页面，填写凭据，提交登录
 */
export async function loginViaUI(
  page: Page,
  credentials: { username: string; password: string } = TEST_CREDENTIALS,
) {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');

  // 填写用户名
  const usernameInput = page.locator('input').first();
  await usernameInput.fill(credentials.username);

  // 填写密码
  const passwordInput = page.locator('input[type="password"]');
  await passwordInput.fill(credentials.password);

  // 点击登录按钮
  const loginButton = page.getByRole('button', { name: '登录' });
  await loginButton.click();

  // 等待登录完成（重定向到首页或目标页面）
  await page.waitForURL((url) => !url.pathname.includes('/login'), {
    timeout: 15000,
  });
  await page.waitForLoadState('networkidle');
}

/**
 * 通过 API 登录并注入认证状态
 *
 * 调用后端 API 获取 refresh token，通过 addInitScript 写入 sessionStorage。
 * 应用启动时 initializeAuth 会用 refreshToken 静默续期并恢复登录态。
 * 比 UI 登录快约 5 秒/测试，适合大量测试场景。
 *
 * 注意：必须在 page.goto() 之前调用。
 */
export async function loginViaAPI(
  page: Page,
  credentials: { username: string; password: string } = TEST_CREDENTIALS,
) {
  const response = await page.request.post('/api/v1/auth/login', {
    data: {
      username: credentials.username,
      password: credentials.password,
    },
  });

  if (!response.ok()) {
    throw new Error(`登录失败: ${response.status()} ${await response.text()}`);
  }

  const loginData = await response.json();
  const refreshToken: string = loginData.tokens.refresh_token;

  // 每次导航前注入 refreshToken，与 authStore 的 sessionStorage key 保持一致
  await page.addInitScript((token: string) => {
    sessionStorage.setItem('auth.refresh_token', token);
  }, refreshToken);

  return loginData;
}

/**
 * 确保已登录状态
 *
 * 检查当前页面是否在登录页，如果是则执行登录
 */
export async function ensureLoggedIn(
  page: Page,
  credentials: { username: string; password: string } = TEST_CREDENTIALS,
) {
  const currentUrl = page.url();
  if (currentUrl.includes('/login') || currentUrl === 'about:blank') {
    await loginViaUI(page, credentials);
  }
}

/**
 * 带登录的页面导航
 *
 * 导航到指定路径，如果被重定向到登录页则自动登录
 */
export async function navigateWithAuth(
  page: Page,
  path: string,
  credentials: { username: string; password: string } = TEST_CREDENTIALS,
) {
  await page.goto(path);
  await page.waitForLoadState('networkidle');

  // 检查是否被重定向到登录页
  if (page.url().includes('/login')) {
    await loginViaUI(page, credentials);

    // 登录后导航到目标页面
    await page.goto(path);
    await page.waitForLoadState('networkidle');
  }
}
