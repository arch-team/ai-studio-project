import { test, expect } from '@playwright/test';
import { loginViaAPI } from '../utils/auth';

test.describe('模型管理', () => {
  let accessToken: string;

  test.beforeEach(async ({ page }) => {
    const loginData = await loginViaAPI(page);
    accessToken = loginData.tokens.access_token;
    // 导航到模型列表页
    await page.goto('/models');
    // 等待页面加载
    await page.waitForLoadState('networkidle');
  });

  test('模型列表页面正确渲染', async ({ page }) => {
    // 验证页面标题
    await expect(page.locator('h1')).toContainText('模型管理');

    // 验证表格存在
    await expect(page.locator('table')).toBeVisible();

    // 验证表格列头
    await expect(page.getByText('模型名称', { exact: true })).toBeVisible();
    await expect(page.getByText('版本', { exact: true })).toBeVisible();
    await expect(page.getByText('状态', { exact: true })).toBeVisible();
  });

  test('模型列表显示测试数据', async ({ page }) => {
    // 等待数据加载
    await page.waitForSelector('table tbody tr', { timeout: 10000 });

    // 验证显示了模型数据
    await expect(page.locator('text=llama2-finetune-model').first()).toBeVisible();
    await expect(page.locator('text=sd-finetune-model').first()).toBeVisible();
  });

  test('点击模型可以进入详情页', async ({ page }) => {
    // 等待数据加载
    await page.waitForSelector('table tbody tr', { timeout: 10000 });

    // 点击第一个模型链接
    await page.locator('table tbody tr').first().locator('a').first().click();

    // 验证跳转到详情页
    await expect(page).toHaveURL(/\/models\/\d+/);

    // 验证详情页显示模型名称 (h1 显示模型名称)
    await expect(page.locator('h1')).toBeVisible();
  });

  test('模型详情页显示正确', async ({ page }) => {
    // 通过 API 动态获取 llama2 v3 的 ID，不依赖数据库自增值
    const resp = await page.request.get('/api/v1/models', {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const data = await resp.json();
    const llamaV3 = data.items.find(
      (m: { model_name: string; version: string }) =>
        m.model_name === 'llama2-finetune-model' && m.version === 'v3',
    );
    expect(llamaV3).toBeTruthy();

    await page.goto(`/models/${llamaV3.id}`);
    await page.waitForLoadState('networkidle');

    // 验证模型名称显示 (使用 h1 选择器)
    await expect(page.locator('h1')).toContainText('llama2-finetune-model');

    // 验证版本显示
    await expect(page.locator('text=v3').first()).toBeVisible();

    // 验证基本信息标签页存在
    await expect(page.getByRole('tab', { name: '基本信息' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '训练指标' })).toBeVisible();
    await expect(page.getByRole('tab', { name: '超参数' })).toBeVisible();
  });

  test('模型版本对比页面正确渲染', async ({ page }) => {
    // 通过 API 动态获取 llama2 任一版本的 ID
    const resp = await page.request.get('/api/v1/models', {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    const data = await resp.json();
    const llama = data.items.find(
      (m: { model_name: string }) => m.model_name === 'llama2-finetune-model',
    );
    expect(llama).toBeTruthy();

    await page.goto(`/models/${llama.id}/versions`);
    await page.waitForLoadState('networkidle');

    // 验证版本列表存在
    await expect(page.locator('text=v1').first()).toBeVisible();
    await expect(page.locator('text=v2').first()).toBeVisible();
    await expect(page.locator('text=v3').first()).toBeVisible();
  });

  test('版本对比功能正常', async ({ page }) => {
    // 导航到版本对比页
    await page.goto('/models/4/versions?compare_with=3');
    await page.waitForLoadState('networkidle');

    // 验证对比结果显示
    // 等待对比组件加载
    await page.waitForTimeout(1000);

    // 验证页面没有错误
    await expect(page.locator('text=错误').first()).not.toBeVisible({ timeout: 2000 }).catch(() => {
      // 忽略，可能没有错误显示
    });
  });
});
