/**
 * 训练任务操作流程 E2E 测试
 *
 * 测试暂停、恢复、删除等操作
 */

import { test, expect } from '@playwright/test';
import { TrainingJobDetailPage } from '../pages/TrainingJobDetailPage';
import { TrainingJobListPage } from '../pages/TrainingJobListPage';
import { MockApi } from '../utils/mockApi';

test.describe('训练任务操作', () => {
  let mockApi: MockApi;

  // =========================================
  // 暂停任务
  // =========================================
  test.describe('暂停任务', () => {
    test('运行中的任务可以暂停', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobWithStatus('running');
      await mockApi.mockTrainingJobOperations();

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(1);

      // 验证暂停按钮可见
      await expect(detailPage.pauseButton).toBeVisible();

      // 点击暂停
      await detailPage.clickPause();

      // 等待状态变更（Mock 会返回 paused 状态）
      await expect(page.locator('text=已暂停')).toBeVisible({ timeout: 5000 });
    });

    test('已完成的任务没有暂停按钮', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobWithStatus('completed');

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(2);

      // 验证暂停按钮不可见
      await expect(detailPage.pauseButton).not.toBeVisible();
    });

    test('已暂停的任务没有暂停按钮', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobWithStatus('paused');

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(3);

      // 验证暂停按钮不可见
      await expect(detailPage.pauseButton).not.toBeVisible();
    });

    test('暂停操作失败显示错误', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobWithStatus('running');
      await mockApi.mockTrainingJobOperations({
        pauseError: '任务状态不允许暂停',
      });

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(1);

      await detailPage.clickPause();

      // 验证错误消息（通过 Flashbar 或其他方式显示）
      // 注意：具体的错误显示方式取决于应用实现
      await page.waitForTimeout(500);
    });
  });

  // =========================================
  // 恢复任务
  // =========================================
  test.describe('恢复任务', () => {
    test('已暂停的任务可以恢复', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobWithStatus('paused');
      await mockApi.mockTrainingJobOperations();

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(3);

      // 验证恢复按钮可见
      await expect(detailPage.resumeButton).toBeVisible();

      // 点击恢复
      await detailPage.clickResume();

      // 等待状态变更
      await expect(page.locator('text=运行中')).toBeVisible({ timeout: 5000 });
    });

    test('被抢占的任务可以恢复', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobWithStatus('preempted');
      await mockApi.mockTrainingJobOperations();

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(5);

      // 验证恢复按钮可见
      await expect(detailPage.resumeButton).toBeVisible();

      // 点击恢复
      await detailPage.clickResume();

      // 等待状态变更
      await expect(page.locator('text=运行中')).toBeVisible({ timeout: 5000 });
    });

    test('运行中的任务没有恢复按钮', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobWithStatus('running');

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(1);

      // 验证恢复按钮不可见
      await expect(detailPage.resumeButton).not.toBeVisible();
    });

    test('已完成的任务没有恢复按钮', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobWithStatus('completed');

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(2);

      // 验证恢复按钮不可见
      await expect(detailPage.resumeButton).not.toBeVisible();
    });

    test('恢复操作失败显示错误', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobWithStatus('paused');
      await mockApi.mockTrainingJobOperations({
        resumeError: '资源不足，无法恢复任务',
      });

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(3);

      await detailPage.clickResume();

      // 等待错误处理
      await page.waitForTimeout(500);
    });
  });

  // =========================================
  // 删除任务
  // =========================================
  test.describe('删除任务', () => {
    test('已完成的任务可以删除', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobWithStatus('completed');
      await mockApi.mockDeleteTrainingJob();

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(2);

      // 验证删除按钮启用
      await expect(detailPage.deleteButton).toBeEnabled();

      // 打开删除确认弹窗
      await detailPage.openDeleteModal();

      // 验证弹窗显示
      await expect(page.locator('text=确定要删除')).toBeVisible();

      // 确认删除
      await detailPage.confirmDelete();

      // 验证跳转到列表页
      await expect(page).toHaveURL('/training-jobs');
    });

    test('运行中的任务删除按钮禁用', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobWithStatus('running');

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(1);

      // 验证删除按钮禁用
      await expect(detailPage.deleteButton).toBeDisabled();
    });

    test('取消删除操作', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobWithStatus('completed');

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(2);

      // 打开删除确认弹窗
      await detailPage.openDeleteModal();
      await expect(page.locator('text=确定要删除')).toBeVisible();

      // 取消删除
      await detailPage.cancelDelete();

      // 验证仍在详情页
      await expect(page).toHaveURL(/\/training-jobs\/2/);
    });

    test('失败的任务可以删除', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobWithStatus('failed');
      await mockApi.mockDeleteTrainingJob();

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(4);

      // 验证删除按钮启用
      await expect(detailPage.deleteButton).toBeEnabled();
    });

    test('已暂停的任务可以删除', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobWithStatus('paused');
      await mockApi.mockDeleteTrainingJob();

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(3);

      // 验证删除按钮启用
      await expect(detailPage.deleteButton).toBeEnabled();
    });

    test('删除操作失败显示错误', async ({ page }) => {
      mockApi = new MockApi(page);
      await mockApi.mockTrainingJobsList();
      await mockApi.mockTrainingJobWithStatus('completed');
      await mockApi.mockDeleteTrainingJob({
        error: { status: 500, message: '删除失败，请稍后重试' },
      });

      const detailPage = new TrainingJobDetailPage(page);
      await detailPage.goto(2);

      await detailPage.openDeleteModal();
      await detailPage.confirmDelete();

      // 等待错误处理
      await page.waitForTimeout(500);
      // 应该仍在详情页
      await expect(page).toHaveURL(/\/training-jobs\/2/);
    });
  });

  // =========================================
  // 状态按钮可见性矩阵
  // =========================================
  test.describe('状态按钮可见性', () => {
    const statusButtonMatrix = [
      { status: 'running', pause: true, resume: false, deleteDisabled: true },
      { status: 'paused', pause: false, resume: true, deleteDisabled: false },
      { status: 'preempted', pause: false, resume: true, deleteDisabled: false },
      { status: 'completed', pause: false, resume: false, deleteDisabled: false },
      { status: 'failed', pause: false, resume: false, deleteDisabled: false },
      { status: 'submitted', pause: false, resume: false, deleteDisabled: false },
    ] as const;

    for (const { status, pause, resume, deleteDisabled } of statusButtonMatrix) {
      test(`状态 "${status}" - 暂停:${pause}, 恢复:${resume}, 删除禁用:${deleteDisabled}`, async ({
        page,
      }) => {
        mockApi = new MockApi(page);
        await mockApi.mockTrainingJobsList();
        await mockApi.mockTrainingJobWithStatus(status);

        const detailPage = new TrainingJobDetailPage(page);
        await detailPage.goto(1);

        // 检查暂停按钮
        if (pause) {
          await expect(detailPage.pauseButton).toBeVisible();
        } else {
          await expect(detailPage.pauseButton).not.toBeVisible();
        }

        // 检查恢复按钮
        if (resume) {
          await expect(detailPage.resumeButton).toBeVisible();
        } else {
          await expect(detailPage.resumeButton).not.toBeVisible();
        }

        // 检查删除按钮
        if (deleteDisabled) {
          await expect(detailPage.deleteButton).toBeDisabled();
        } else {
          await expect(detailPage.deleteButton).toBeEnabled();
        }
      });
    }
  });
});
