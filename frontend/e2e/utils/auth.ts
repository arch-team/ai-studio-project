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
 * 通过 API 登录并设置 Token
 *
 * 直接调用后端 API 获取 token，然后在页面中注入认证状态
 * 比 UI 登录更快，适合大量测试场景
 */
export async function loginViaAPI(
  page: Page,
  credentials: { username: string; password: string } = TEST_CREDENTIALS,
) {
  // 先获取 baseURL
  const baseURL = page.url() || '';
  const apiBase = baseURL.replace(/\/$/, '');

  // 通过 API 获取 token
  const response = await page.request.post(`${apiBase}/api/v1/auth/login`, {
    data: {
      username: credentials.username,
      password: credentials.password,
    },
  });

  if (!response.ok()) {
    throw new Error(`登录失败: ${response.status()} ${await response.text()}`);
  }

  const loginData = await response.json();

  // 在页面中注入认证状态到 Zustand store
  await page.goto('/');
  await page.evaluate((data) => {
    // 设置 localStorage 或直接调用 store
    // Zustand 不持久化 token，需要通过 API 设置
    window.__TEST_AUTH_DATA__ = data;
  }, loginData);

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
