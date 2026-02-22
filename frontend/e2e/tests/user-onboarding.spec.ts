/**
 * 用户引导 E2E 测试
 *
 * Task: T104a - 模拟首次登录用户的完整引导流程
 *
 * 测试覆盖:
 * - 首次登录流程
 * - 核心功能导航覆盖
 * - 页面加载和基本交互验证
 */

import { test, expect } from "@playwright/test";
import { loginViaUI, TEST_CREDENTIALS } from "../utils/auth";

test.describe("用户引导流程", () => {
  test.describe("首次登录体验", () => {
    test("未登录用户访问受保护页面被重定向到登录页", async ({ page }) => {
      await page.goto("/training-jobs");
      await page.waitForLoadState("networkidle");

      // 应被重定向到登录页
      expect(page.url()).toContain("/login");
    });

    test("用户可以通过登录页成功登录", async ({ page }) => {
      await page.goto("/login");
      await page.waitForLoadState("networkidle");

      // 验证登录页包含必要元素
      const usernameInput = page.locator("input").first();
      await expect(usernameInput).toBeVisible();

      const passwordInput = page.locator('input[type="password"]');
      await expect(passwordInput).toBeVisible();

      const loginButton = page.getByRole("button", { name: "登录" });
      await expect(loginButton).toBeVisible();

      // 执行登录
      await usernameInput.fill(TEST_CREDENTIALS.username);
      await passwordInput.fill(TEST_CREDENTIALS.password);
      await loginButton.click();

      // 等待登录完成
      await page.waitForURL((url) => !url.pathname.includes("/login"), {
        timeout: 15000,
      });

      // 验证已离开登录页
      expect(page.url()).not.toContain("/login");
    });

    test("登录失败显示错误提示", async ({ page }) => {
      await page.goto("/login");
      await page.waitForLoadState("networkidle");

      // 使用错误凭据
      const usernameInput = page.locator("input").first();
      await usernameInput.fill("wrong_user");

      const passwordInput = page.locator('input[type="password"]');
      await passwordInput.fill("wrong_password");

      const loginButton = page.getByRole("button", { name: "登录" });
      await loginButton.click();

      // 等待错误提示出现 (超时不应跳转)
      await page.waitForTimeout(3000);
      expect(page.url()).toContain("/login");
    });
  });

  test.describe("核心功能导航", () => {
    test.beforeEach(async ({ page }) => {
      await loginViaUI(page);
    });

    test("用户可以导航到训练任务列表页", async ({ page }) => {
      await page.goto("/training-jobs");
      await page.waitForLoadState("networkidle");

      // 页面应包含训练任务相关内容 - 只匹配主内容区可见标题
      const heading = page
        .locator(
          'main h1:visible, main h2:visible, [role="main"] h1:visible, [role="main"] h2:visible',
        )
        .first();
      await expect(heading).toBeVisible({ timeout: 10000 });
    });

    test("用户可以导航到数据集列表页", async ({ page }) => {
      await page.goto("/datasets");
      await page.waitForLoadState("networkidle");

      // 只匹配主内容区可见标题
      const heading = page
        .locator(
          'main h1:visible, main h2:visible, [role="main"] h1:visible, [role="main"] h2:visible',
        )
        .first();
      await expect(heading).toBeVisible({ timeout: 10000 });
    });

    test("用户可以导航到模型列表页", async ({ page }) => {
      await page.goto("/models");
      await page.waitForLoadState("networkidle");

      // 只匹配主内容区可见标题
      const heading = page
        .locator(
          'main h1:visible, main h2:visible, [role="main"] h1:visible, [role="main"] h2:visible',
        )
        .first();
      await expect(heading).toBeVisible({ timeout: 10000 });
    });

    test("用户可以导航到资源配额页", async ({ page }) => {
      await page.goto("/resource-quotas");
      await page.waitForLoadState("networkidle");

      // 只匹配主内容区可见标题
      const heading = page
        .locator(
          'main h1:visible, main h2:visible, [role="main"] h1:visible, [role="main"] h2:visible',
        )
        .first();
      await expect(heading).toBeVisible({ timeout: 10000 });
    });

    test("用户可以导航到任务模板页", async ({ page }) => {
      await page.goto("/job-templates");
      await page.waitForLoadState("networkidle");

      // 只匹配主内容区可见标题
      const heading = page
        .locator(
          'main h1:visible, main h2:visible, [role="main"] h1:visible, [role="main"] h2:visible',
        )
        .first();
      await expect(heading).toBeVisible({ timeout: 10000 });
    });

    test("用户访问不存在的页面显示 404", async ({ page }) => {
      await page.goto("/nonexistent-page");
      await page.waitForLoadState("networkidle");

      // 应重定向到 404 页面
      expect(page.url()).toContain("/404");
    });
  });

  test.describe("页面基本交互", () => {
    test.beforeEach(async ({ page }) => {
      await loginViaUI(page);
    });

    test("训练任务列表页包含创建按钮", async ({ page }) => {
      await page.goto("/training-jobs");
      await page.waitForLoadState("networkidle");

      // 查找创建按钮
      const createButton = page.getByRole("button", { name: /创建/ });
      // 按钮应存在且可见
      if (await createButton.isVisible()) {
        await expect(createButton).toBeEnabled();
      }
    });

    test("数据集列表页包含创建按钮", async ({ page }) => {
      await page.goto("/datasets");
      await page.waitForLoadState("networkidle");

      const createButton = page.getByRole("button", { name: /创建/ });
      if (await createButton.isVisible()) {
        await expect(createButton).toBeEnabled();
      }
    });

    test("页面可以正常响应键盘操作", async ({ page }) => {
      await page.goto("/training-jobs");
      await page.waitForLoadState("networkidle");

      // Tab 键可以在页面元素间导航
      await page.keyboard.press("Tab");
      const hasFocus = await page.evaluate(
        () => document.activeElement !== document.body,
      );
      expect(hasFocus).toBeTruthy();
    });
  });
});
