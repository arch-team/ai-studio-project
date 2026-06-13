/**
 * 审计状态 Mock 引擎
 *
 * 注册顺序约定（Playwright 后注册者优先匹配）：
 *   1. 兜底 catch-all（最先注册，最低优先级）
 *   2. extras（页面依赖的次要 API）
 *   3. primary（主数据 API，按状态切换）
 * 认证 mock 在 setupAuditAuth 中注册（晚于 catch-all 即可生效）。
 */

import { Page } from '@playwright/test';
import { AuditState, PageSpec } from './routes-manifest';

const EMPTY_LIST = { items: [], total: 0, page: 1, page_size: 20 };

function json(body: unknown, status = 200) {
  return { status, contentType: 'application/json', body: JSON.stringify(body) };
}

/**
 * 兜底：未声明的 GET API 返回空列表形状，避免页面因未 mock 的请求而崩溃。
 * 非 GET 请求 fallback 后若无更低优先级 handler 会放行到真实网络——
 * 审计场景下可接受：auth 的 POST 由更高优先级的 setupAuditAuth 拦截，页面初始渲染基本只发 GET。
 */
export async function setupCatchAll(page: Page) {
  await page.route('**/api/v1/**', (route, request) => {
    if (request.method() !== 'GET') return route.fallback();
    return route.fulfill(json(EMPTY_LIST));
  });
}

/**
 * 按页面声明与目标状态注册 mock。
 * 无主数据 API 的页面（spec.primary 为 undefined，如登录页/404/IDE）仅注册 extras。
 */
export async function setupStateMocks(page: Page, spec: PageSpec, state: AuditState) {
  for (const extra of spec.extras ?? []) {
    await page.route(extra.pattern, (route, request) => {
      if (request.method() !== 'GET') return route.fallback();
      return route.fulfill(json(extra.resolveBody?.(request.url()) ?? extra.defaultBody));
    });
  }

  if (!spec.primary) return;
  const primary = spec.primary;

  await page.route(primary.pattern, (route, request) => {
    if (request.method() !== 'GET') return route.fallback();
    switch (state) {
      case 'default':
        return route.fulfill(json(primary.resolveBody?.(request.url()) ?? primary.defaultBody));
      case 'empty':
        return route.fulfill(json(primary.emptyBody ?? EMPTY_LIST));
      case 'error':
        // 详情页用 404（spec §5.4），其余用 500
        return spec.pageType === 'detail'
          ? route.fulfill(json({ detail: '资源不存在' }, 404))
          : route.fulfill(json({ detail: '服务器内部错误' }, 500));
      case 'loading':
        // 永不返回，页面停留在加载态
        return new Promise<void>(() => {});
    }
  });
}
