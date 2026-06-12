/**
 * 训练管理真实环境冒烟测试（无业务 Mock）
 *
 * 直接验证远程环境的真实数据链路：列表字段渲染、详情 Tab（检查点/日志/指标）、
 * 创建→详情→删除完整闭环。仅在 E2E_BASE_URL 指向远程环境时有意义。
 */

import { test, expect } from '@playwright/test';
import { loginViaAPI } from '../utils/auth';

test.describe('训练管理真实数据冒烟', () => {
  test.beforeEach(async ({ page }) => {
    await loginViaAPI(page);
  });

  test('列表页渲染真实数据与 GPU/进度列', async ({ page }) => {
    await page.goto('/training-jobs');
    await page.waitForLoadState('networkidle');

    // 真实种子任务可见
    await expect(page.locator('text=llama2-finetune-001')).toBeVisible({ timeout: 10000 });

    // GPU/节点列有数值（修复前后端缺失 gpu_per_node 字段时渲染为空）
    const row = page.locator('tr', { hasText: 'llama2-finetune-001' });
    const cells = row.locator('td');
    const cellTexts = await cells.allTextContents();
    // 至少有一个单元格是纯数字（节点数/GPU 列）
    expect(cellTexts.some((t) => /^\d+$/.test(t.trim()))).toBeTruthy();
  });

  test('详情页检查点 Tab 显示真实检查点', async ({ page }) => {
    await page.goto('/training-jobs/1');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('h1')).toContainText('llama2-finetune-001');

    // 切换到检查点 Tab（修复前 GET checkpoints 返回 405）
    await page.getByRole('tab', { name: /检查点/ }).click();
    // 名称列与存储路径都含 "llama2-final"，精确匹配单元格文本
    await expect(page.getByText('llama2-final', { exact: true })).toBeVisible({
      timeout: 10000,
    });
  });

  test('详情页日志 Tab 正常加载', async ({ page }) => {
    await page.goto('/training-jobs/3');
    await page.waitForLoadState('networkidle');

    await page.getByRole('tab', { name: '日志' }).click();
    // 日志区域渲染：有日志条目或空态文案，不应停留在加载错误
    await expect(
      page.locator('text=/暂无日志数据|CloudWatch|训练日志/').first()
    ).toBeVisible({ timeout: 15000 });
  });

  test('详情页训练指标 Tab 正常加载', async ({ page }) => {
    await page.goto('/training-jobs/1');
    await page.waitForLoadState('networkidle');

    await page.getByRole('tab', { name: '训练指标' }).click();
    // 指标组件渲染：空数据态或图表（修复前响应结构不匹配导致组件异常）
    await expect(
      page.locator('text=/暂无指标数据|训练进度/').first()
    ).toBeVisible({ timeout: 15000 });
  });

  test('检查点管理页选择任务后展示检查点', async ({ page }) => {
    await page.goto('/checkpoints');
    await page.waitForLoadState('networkidle');

    // 选择任务下拉（默认选中 "全部任务" 选项，Select 渲染为该文本的 button）
    await page.locator('button:has-text("全部任务")').click();
    await page.getByRole('option', { name: /llama2-finetune-001/ }).click();

    // 检查点列表加载（修复前 GET checkpoints 405 导致此页始终为空/报错）
    await expect(page.getByText('llama2-final', { exact: true })).toBeVisible({
      timeout: 10000,
    });
  });

  test('真实暂停 → 恢复闭环 (running 种子任务)', async ({ page }) => {
    // job 3 (bert-pretrain-001) 是 running 种子任务；
    // 用例结束时恢复 running 原状，避免污染共享环境
    await page.goto('/training-jobs/3');
    await page.waitForLoadState('networkidle');

    // 1. 暂停（修复前 K8s CR 不存在时此操作 500）
    await page.getByRole('button', { name: '暂停', exact: true }).click();
    await expect(page.getByText('已暂停').first()).toBeVisible({ timeout: 15000 });

    // 2. 恢复（真实向 HyperPod 重新提交任务）
    await page.getByRole('button', { name: '恢复', exact: true }).click();
    await expect(page.getByText('运行中').first()).toBeVisible({ timeout: 20000 });
  });

  test('真实创建 → 详情展示 → 删除闭环', async ({ page }) => {
    const jobName = `e2e-smoke-${Date.now()}`;

    // 1. 创建（走真实后端，验证 entry_point/gpu_per_node 契约）
    await page.goto('/training-jobs/create');
    await page.waitForLoadState('networkidle');
    await page.locator('input[placeholder="my-training-job"]').fill(jobName);
    await page.locator('input[placeholder*="ecr"]').fill(
      '123456789012.dkr.ecr.us-west-2.amazonaws.com/training:v1'
    );
    await page.locator('input[placeholder*="train.py"]').fill('/opt/ml/code/train.py');
    await page.getByRole('spinbutton', { name: '每节点 GPU 数量' }).fill('1');
    await page.locator('button:has-text("创建任务")').click();

    // 2. 创建成功跳详情，名称与配置正确展示
    await page.waitForURL(/\/training-jobs\/\d+/, { timeout: 15000 });
    await expect(page.locator('h1')).toContainText(jobName);

    // 配置信息 Tab 展示 entry_point 映射值（python /opt/ml/code/train.py）
    await page.getByRole('tab', { name: '配置信息' }).click();
    await expect(
      page.getByText('python /opt/ml/code/train.py', { exact: true })
    ).toBeVisible({ timeout: 10000 });

    // 3. 删除（submitted 状态允许删除），回到列表页
    // "删除" 与 Modal 内 "确认删除" 都含该文本，需精确匹配
    await page.getByRole('button', { name: '删除', exact: true }).click();
    await expect(page.locator('text=确定要删除')).toBeVisible({ timeout: 5000 });
    await page.getByRole('button', { name: '确认删除', exact: true }).click();
    await page.waitForURL('/training-jobs', { timeout: 15000 });

    // 4. 列表中不再出现该任务
    await page.waitForLoadState('networkidle');
    await expect(page.locator(`text=${jobName}`)).not.toBeVisible();
  });
});
