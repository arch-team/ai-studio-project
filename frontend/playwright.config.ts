import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E 测试配置
 *
 * 支持两种运行模式:
 * - 本地模式: 自动启动 dev server (默认)
 * - 远程模式: 通过 E2E_BASE_URL 指向已部署的 AWS 环境
 *
 * 使用示例:
 *   本地: npx playwright test
 *   远程: E2E_BASE_URL=http://alb-dns.elb.amazonaws.com npx playwright test
 *
 * @see https://playwright.dev/docs/test-configuration
 */
const baseURL = process.env.E2E_BASE_URL || 'http://localhost:5173';
const isRemote = !!process.env.E2E_BASE_URL;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // 远程模式下不启动本地 dev server
  ...(isRemote
    ? {}
    : {
        webServer: {
          command: 'npm run dev',
          url: 'http://localhost:5173',
          reuseExistingServer: !process.env.CI,
        },
      }),
});
