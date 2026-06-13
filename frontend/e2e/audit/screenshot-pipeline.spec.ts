/**
 * UI/UX 审计截图流水线
 *
 * 运行：npm run audit:screens
 * 过滤单模块：npm run audit:screens -- --grep "training/"
 * 产出：e2e/audit/audit-output/<日期>/<module>/<page>--<state>--<theme>.png
 */

import { test } from '@playwright/test';
import { AUDIT_PAGES } from './routes-manifest';
import { setupAuditAuth, setTheme } from './auditSetup';
import { setupCatchAll, setupStateMocks } from './auditMockApi';

const THEMES = ['light', 'dark'] as const;
const RUN_DATE = process.env.AUDIT_DATE || new Date().toISOString().slice(0, 10);

for (const spec of AUDIT_PAGES) {
  for (const state of spec.states) {
    for (const theme of THEMES) {
      test(`${spec.module}/${spec.pageName} [${state}] [${theme}]`, async ({ page }) => {
        // 注册顺序：catch-all → 主题/认证 → 页面 mock（后注册优先）
        await setupCatchAll(page);
        await setTheme(page, theme);
        if (spec.requiresAuth !== false) {
          await setupAuditAuth(page);
        }
        await setupStateMocks(page, spec, state);

        await page.goto(spec.route);

        if (state === 'loading') {
          // 主 API 永不返回，等待加载指示渲染稳定
          await page.waitForTimeout(1500);
        } else {
          await page.waitForLoadState('networkidle');
          await page.waitForTimeout(500); // 等待图表/动画静止
        }

        await page.screenshot({
          path: `e2e/audit/audit-output/${RUN_DATE}/${spec.module}/${spec.pageName}--${state}--${theme}.png`,
          fullPage: true,
        });
      });
    }
  }
}
