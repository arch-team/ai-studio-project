/**
 * 审计流水线基础设施：认证 Mock + 主题注入
 *
 * 完全脱离真实后端：mock 刷新/用户端点，注入 refresh token 触发应用静默续期。
 * 端点形状参照 src/features/auth/types/index.ts (TokenResponse/UserResponse)。
 */

import { Page } from '@playwright/test';

/** Mock 认证端点并注入登录态（admin 角色，保证可访问全部页面） */
export async function setupAuditAuth(page: Page) {
  await page.route('**/api/v1/auth/token/refresh', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'audit-access-token',
        refresh_token: 'audit-refresh-token',
        token_type: 'bearer',
        expires_in: 3600,
      }),
    }),
  );

  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        id: 1,
        username: 'admin',
        email: 'admin@example.com',
        display_name: '平台管理员',
        role: 'admin',
        status: 'active',
        auth_type: 'local',
      }),
    }),
  );

  await page.addInitScript(() => {
    sessionStorage.setItem('auth.refresh_token', 'audit-refresh-token');
  });
}

/** 注入主题偏好（zustand persist 格式，key 与 store/slices/uiSlice.ts 一致） */
export async function setTheme(page: Page, theme: 'light' | 'dark') {
  await page.addInitScript((t: string) => {
    localStorage.setItem(
      'ui-storage',
      JSON.stringify({
        state: { sidebarOpen: true, theme: t, density: 'comfortable' },
        version: 0,
      }),
    );
  }, theme);
}
