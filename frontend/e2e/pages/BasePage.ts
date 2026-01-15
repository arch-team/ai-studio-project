import { Page } from '@playwright/test';

/**
 * 基础页面对象类
 * 提供所有页面通用的方法
 */
export class BasePage {
  constructor(protected page: Page) {}

  /**
   * 等待页面加载完成（网络空闲）
   */
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 获取面包屑导航内容
   */
  async getBreadcrumbs() {
    return this.page.locator('[data-testid="breadcrumb"]').allTextContents();
  }

  /**
   * 获取页面标题
   */
  async getPageTitle() {
    return this.page.locator('h1').first().textContent();
  }

  /**
   * 等待加载指示器消失
   */
  async waitForLoadingComplete() {
    await this.page.waitForSelector('[data-testid="loading"]', { state: 'hidden' }).catch(() => {});
  }

  /**
   * 检查 Flashbar 通知消息
   */
  async getFlashbarMessage() {
    return this.page.locator('[data-testid="flashbar"]').textContent();
  }
}
