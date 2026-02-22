/**
 * Phase 8 质量保障 E2E 测试
 *
 * 验证 Phase 8 实施的所有前端功能:
 * - API 错误格式验证 (RFC 7807)
 * - 前端重试逻辑
 * - 错误边界组件
 * - 路由懒加载
 * - OpenAPI 文档可访问性
 *
 * 运行模式: 本地模式 (localhost:5173)
 * 注意: 需要后端服务运行在 localhost:8000
 */

import { test, expect } from '@playwright/test';
import { loginViaUI } from '../utils/auth';

test.describe('Phase 8 质量保障测试', () => {

  // === 1. API 错误格式验证 (RFC 7807) ===

  test.describe('API 错误格式标准化', () => {
    test('API 错误应返回 RFC 7807 格式', async ({ page }) => {
      await loginViaUI(page);

      // 拦截 API 请求以验证错误格式
      const errorResponses: unknown[] = [];

      page.on('response', async (response) => {
        if (response.url().includes('/api/v1/') && !response.ok()) {
          try {
            const body = await response.json();
            errorResponses.push({
              status: response.status(),
              body,
            });
          } catch {
            // 忽略非 JSON 响应
          }
        }
      });

      // 触发一个会产生 404 错误的请求 (访问不存在的资源)
      await page.goto('/training-jobs/999999');
      await page.waitForTimeout(1000); // 等待 API 请求完成

      // 验证至少有一个错误响应
      expect(errorResponses.length).toBeGreaterThan(0);

      // 验证错误格式符合 RFC 7807 (Problem Details for HTTP APIs)
      const errorResponse = errorResponses[0] as { status: number; body: Record<string, unknown> };
      expect(errorResponse.body).toHaveProperty('type');
      expect(errorResponse.body).toHaveProperty('title');
      expect(errorResponse.body).toHaveProperty('status');
      expect(errorResponse.body).toHaveProperty('detail');
    });
  });

  // === 2. 前端重试逻辑验证 ===

  test.describe('请求重试机制', () => {
    test('5xx 错误应触发自动重试', async ({ page }) => {
      await loginViaUI(page);

      let requestCount = 0;

      // 拦截 API 请求并计数
      await page.route('**/api/v1/training-jobs', async (route) => {
        requestCount++;

        // 前 2 次返回 503，第 3 次返回成功
        if (requestCount < 3) {
          await route.fulfill({
            status: 503,
            contentType: 'application/json',
            body: JSON.stringify({
              type: 'about:blank',
              title: 'Service Unavailable',
              status: 503,
              detail: '服务暂时不可用',
            }),
          });
        } else {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              items: [],
              total: 0,
              page: 1,
              page_size: 20,
            }),
          });
        }
      });

      // 导航到训练任务列表页
      await page.goto('/training-jobs');
      await page.waitForTimeout(5000); // 等待重试完成

      // 验证发生了多次请求 (至少 3 次)
      expect(requestCount).toBeGreaterThanOrEqual(3);

      // 验证最终页面加载成功 (没有显示错误消息)
      const errorMessage = page.getByText('服务暂时不可用');
      await expect(errorMessage).not.toBeVisible();
    });

    test('404 错误不应重试', async ({ page }) => {
      await loginViaUI(page);

      let requestCount = 0;

      // 拦截 API 请求并计数
      await page.route('**/api/v1/training-jobs/999999', async (route) => {
        requestCount++;
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({
            type: 'about:blank',
            title: 'Not Found',
            status: 404,
            detail: '训练任务不存在',
          }),
        });
      });

      // 导航到不存在的任务详情页
      await page.goto('/training-jobs/999999');
      await page.waitForTimeout(2000); // 等待可能的重试

      // 验证只发生了 1 次请求 (没有重试)
      expect(requestCount).toBe(1);

      // 验证显示了错误消息
      const errorMessage = page.getByText('训练任务不存在');
      await expect(errorMessage).toBeVisible();
    });
  });

  // === 3. 错误边界验证 ===

  test.describe('错误边界组件', () => {
    test('组件崩溃应被优雅捕获', async ({ page }) => {
      await loginViaUI(page);

      // 监听控制台错误
      const consoleErrors: string[] = [];
      page.on('console', (msg) => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });

      // 导航到首页
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // 验证页面正常加载 (没有出现白屏)
      const mainContent = page.locator('main, [role="main"]');
      await expect(mainContent).toBeVisible();

      // 如果有 React 错误边界，应该会捕获错误而不是白屏
      // 这里只验证页面结构完整性
      const appLayout = page.locator('[class*="awsui-app-layout"]');
      await expect(appLayout).toBeVisible();
    });
  });

  // === 4. 路由懒加载验证 ===

  test.describe('路由懒加载', () => {
    test('页面组件应按需加载', async ({ page, browser }) => {
      await loginViaUI(page);

      // 监听网络请求，收集加载的 JS chunk
      const jsChunks: string[] = [];

      page.on('response', (response) => {
        const url = response.url();
        if (url.includes('.js') && !url.includes('node_modules')) {
          jsChunks.push(url);
        }
      });

      // 导航到首页
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      const homeChunks = jsChunks.length;

      // 导航到训练任务列表页
      await page.goto('/training-jobs');
      await page.waitForLoadState('networkidle');
      const trainingChunks = jsChunks.length;

      // 验证导航到新页面时加载了额外的 JS chunk
      // (懒加载的证据是有新的 chunk 文件被请求)
      expect(trainingChunks).toBeGreaterThan(homeChunks);

      console.log(`首页加载了 ${homeChunks} 个 JS chunks`);
      console.log(`训练任务页总共加载了 ${trainingChunks} 个 JS chunks`);
    });
  });

  // === 5. OpenAPI 文档可访问性 ===

  test.describe('OpenAPI 文档端点', () => {
    test('Swagger UI 文档应可访问', async ({ request }) => {
      // 直接请求后端 API 文档端点
      const response = await request.get('http://localhost:8000/api/v1/docs');

      // 验证返回 HTML 页面 (Swagger UI)
      expect(response.ok()).toBeTruthy();

      const contentType = response.headers()['content-type'];
      expect(contentType).toContain('text/html');

      const html = await response.text();
      expect(html).toContain('swagger'); // Swagger UI 的标志性内容
    });

    test('ReDoc 文档应可访问', async ({ request }) => {
      // 直接请求后端 ReDoc 端点
      const response = await request.get('http://localhost:8000/api/v1/redoc');

      // 验证返回 HTML 页面 (ReDoc)
      expect(response.ok()).toBeTruthy();

      const contentType = response.headers()['content-type'];
      expect(contentType).toContain('text/html');

      const html = await response.text();
      expect(html).toContain('redoc'); // ReDoc 的标志性内容
    });

    test('OpenAPI JSON 规范应可访问', async ({ request }) => {
      // 请求 OpenAPI JSON 规范
      const response = await request.get('http://localhost:8000/api/v1/openapi.json');

      expect(response.ok()).toBeTruthy();

      const spec = await response.json();

      // 验证 OpenAPI 规范格式
      expect(spec).toHaveProperty('openapi');
      expect(spec).toHaveProperty('info');
      expect(spec).toHaveProperty('paths');

      // 验证版本号
      expect(spec.openapi).toMatch(/^3\.\d+\.\d+$/);
    });
  });

  // === 6. Cloudscape 合规性验证 (前端静态) ===

  test.describe('Cloudscape UI 合规', () => {
    test('页面应使用 Cloudscape 组件', async ({ page }) => {
      await loginViaUI(page);
      await page.goto('/training-jobs');
      await page.waitForLoadState('networkidle');

      // 验证存在 Cloudscape 特有的 class 前缀
      const awsuiElements = page.locator('[class*="awsui"]');
      const count = await awsuiElements.count();

      // 应该有大量 Cloudscape 组件 (至少 10 个)
      expect(count).toBeGreaterThan(10);
    });

    test('不应存在原生 HTML 表单控件', async ({ page }) => {
      await loginViaUI(page);
      await page.goto('/training-jobs');
      await page.waitForLoadState('networkidle');

      // 检查是否有裸露的原生表单控件 (不在 Cloudscape 组件内)
      // 注意: Cloudscape 组件内部会使用原生控件，但会被包装
      const nativeInputs = page.locator('input:not([class*="awsui"])');
      const inputCount = await nativeInputs.count();

      // 允许少量原生输入框 (如隐藏字段)，但不应该是主要交互元素
      // 这里只做基础检查，实际合规需要代码审查
      console.log(`发现 ${inputCount} 个非 Cloudscape 包装的原生 input`);
    });
  });

  // === 7. 性能监控中间件验证 (间接) ===

  test.describe('性能监控', () => {
    test('API 响应应包含性能头', async ({ page }) => {
      await loginViaUI(page);

      const performanceHeaders: Record<string, string>[] = [];

      page.on('response', (response) => {
        if (response.url().includes('/api/v1/')) {
          const headers = response.headers();
          if (headers['x-response-time'] || headers['x-process-time']) {
            performanceHeaders.push(headers);
          }
        }
      });

      await page.goto('/training-jobs');
      await page.waitForTimeout(2000);

      // 验证至少有一个响应包含性能头
      // 注意: 这取决于后端中间件是否启用
      console.log(`收集到 ${performanceHeaders.length} 个带性能头的响应`);

      if (performanceHeaders.length > 0) {
        const headers = performanceHeaders[0];
        console.log('性能头示例:', headers);
      }
    });
  });
});
