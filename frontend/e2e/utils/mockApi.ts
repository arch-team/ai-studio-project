/**
 * E2E 测试 API Mock 工具
 *
 * 使用 Playwright 的 Route Interception 进行 API Mock
 */

import { Page } from '@playwright/test';
import {
  mockTrainingJobs,
  getMockTrainingJobDetail,
  filterJobsByStatus,
  filterJobsByPriority,
  createPaginatedResponse,
} from '../fixtures/trainingJobs';

/**
 * API Mock 工具类
 */
export class MockApi {
  constructor(private page: Page) {}

  /**
   * 设置默认的所有 API Mock
   */
  async setupDefaultMocks() {
    await this.mockTrainingJobsList();
    await this.mockTrainingJobDetail();
    await this.mockTrainingJobOperations();
    await this.mockCreateTrainingJob();
    await this.mockDeleteTrainingJob();
  }

  /**
   * Mock 训练任务列表 API
   */
  async mockTrainingJobsList(options?: {
    items?: typeof mockTrainingJobs;
    error?: { status: number; message: string };
  }) {
    // 使用正则表达式匹配列表 API（不匹配具体 ID 的详情 API）
    await this.page.route(/\/api\/v1\/training-jobs(\?.*)?$/, async (route) => {
      const request = route.request();
      if (request.method() !== 'GET') {
        await route.continue();
        return;
      }

      // 模拟错误响应
      if (options?.error) {
        await route.fulfill({
          status: options.error.status,
          contentType: 'application/json',
          body: JSON.stringify({ detail: options.error.message }),
        });
        return;
      }

      const url = new URL(request.url());
      const page = parseInt(url.searchParams.get('page') || '1');
      const pageSize = parseInt(url.searchParams.get('page_size') || '20');
      const status = url.searchParams.get('status');
      const priority = url.searchParams.get('priority');

      let items = options?.items || mockTrainingJobs;

      // 应用筛选
      if (status) {
        items = filterJobsByStatus(status);
      }
      if (priority) {
        items = filterJobsByPriority(priority);
      }

      const response = createPaginatedResponse(items, page, pageSize);

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response),
      });
    });
  }

  /**
   * Mock 训练任务详情 API
   */
  async mockTrainingJobDetail(overrides?: Record<string, unknown>) {
    await this.page.route('**/api/v1/training-jobs/*', async (route, request) => {
      const url = new URL(request.url());
      const pathParts = url.pathname.split('/');
      const lastPart = pathParts[pathParts.length - 1];

      // 跳过操作端点 (pause, resume, cancel, checkpoints)
      if (['pause', 'resume', 'cancel', 'checkpoints'].includes(lastPart)) {
        await route.continue();
        return;
      }

      if (request.method() !== 'GET') {
        await route.continue();
        return;
      }

      const id = parseInt(lastPart);
      const job = getMockTrainingJobDetail(id);

      if (!job) {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ detail: '训练任务不存在' }),
        });
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...job, ...overrides }),
      });
    });
  }

  /**
   * Mock 指定状态的任务详情
   */
  async mockTrainingJobWithStatus(
    status: 'running' | 'completed' | 'failed' | 'paused' | 'preempted' | 'submitted',
  ) {
    await this.page.route('**/api/v1/training-jobs/*', async (route, request) => {
      const url = new URL(request.url());
      const pathParts = url.pathname.split('/');
      const lastPart = pathParts[pathParts.length - 1];

      if (['pause', 'resume', 'cancel', 'checkpoints'].includes(lastPart)) {
        await route.continue();
        return;
      }

      if (request.method() !== 'GET') {
        await route.continue();
        return;
      }

      const id = parseInt(lastPart);
      const baseJob = getMockTrainingJobDetail(id) || getMockTrainingJobDetail(1);

      if (!baseJob) {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ detail: '训练任务不存在' }),
        });
        return;
      }

      // 根据状态调整相关字段
      const jobWithStatus = {
        ...baseJob,
        id,
        status,
        running_pods: status === 'running' ? baseJob.node_count : 0,
        failed_pods: status === 'failed' ? 1 : 0,
        preemption_count: status === 'preempted' ? 1 : 0,
        error_message: status === 'failed' ? 'CUDA OOM: 显存不足' : null,
        failure_reason: status === 'failed' ? 'ResourceExhausted' : null,
        completed_at: status === 'completed' ? new Date().toISOString() : null,
      };

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(jobWithStatus),
      });
    });
  }

  /**
   * Mock 训练任务操作 (暂停/恢复/取消)
   */
  async mockTrainingJobOperations(options?: {
    pauseError?: string;
    resumeError?: string;
    cancelError?: string;
  }) {
    // 暂停操作
    await this.page.route('**/api/v1/training-jobs/*/pause', async (route) => {
      if (options?.pauseError) {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: options.pauseError }),
        });
        return;
      }

      const url = new URL(route.request().url());
      const id = parseInt(url.pathname.split('/')[4]);
      const job = getMockTrainingJobDetail(id);

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...job, status: 'paused' }),
      });
    });

    // 恢复操作
    await this.page.route('**/api/v1/training-jobs/*/resume', async (route) => {
      if (options?.resumeError) {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: options.resumeError }),
        });
        return;
      }

      const url = new URL(route.request().url());
      const id = parseInt(url.pathname.split('/')[4]);
      const job = getMockTrainingJobDetail(id);

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...job, status: 'running' }),
      });
    });

    // 取消操作
    await this.page.route('**/api/v1/training-jobs/*/cancel', async (route) => {
      if (options?.cancelError) {
        await route.fulfill({
          status: 400,
          contentType: 'application/json',
          body: JSON.stringify({ detail: options.cancelError }),
        });
        return;
      }

      const url = new URL(route.request().url());
      const id = parseInt(url.pathname.split('/')[4]);
      const job = getMockTrainingJobDetail(id);

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ ...job, status: 'failed', failure_reason: 'UserCancelled' }),
      });
    });
  }

  /**
   * Mock 创建训练任务 API
   */
  async mockCreateTrainingJob(options?: {
    success?: boolean;
    error?: { status: number; message: string };
  }) {
    await this.page.route('**/api/v1/training-jobs', async (route, request) => {
      if (request.method() !== 'POST') {
        await route.continue();
        return;
      }

      if (options?.error) {
        await route.fulfill({
          status: options.error.status,
          contentType: 'application/json',
          body: JSON.stringify({ detail: options.error.message }),
        });
        return;
      }

      const body = request.postDataJSON();

      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 999,
          ...body,
          status: 'submitted',
          owner_id: 1,
          owner_username: 'admin',
          created_at: new Date().toISOString(),
          submitted_at: new Date().toISOString(),
          current_epoch: 0,
          total_epochs: body.max_epochs || 10,
          checkpoints_count: 0,
          duration_seconds: 0,
          estimated_cost_usd: 0,
        }),
      });
    });
  }

  /**
   * Mock 删除训练任务 API
   */
  async mockDeleteTrainingJob(options?: {
    success?: boolean;
    error?: { status: number; message: string };
  }) {
    await this.page.route('**/api/v1/training-jobs/*', async (route, request) => {
      if (request.method() !== 'DELETE') {
        await route.continue();
        return;
      }

      if (options?.error) {
        await route.fulfill({
          status: options.error.status,
          contentType: 'application/json',
          body: JSON.stringify({ detail: options.error.message }),
        });
        return;
      }

      await route.fulfill({
        status: 204,
        body: '',
      });
    });
  }

  /**
   * Mock API 错误响应
   */
  async mockApiError(pathPattern: string, statusCode: number, message: string) {
    await this.page.route(`**/api/v1/${pathPattern}`, async (route) => {
      await route.fulfill({
        status: statusCode,
        contentType: 'application/json',
        body: JSON.stringify({ detail: message }),
      });
    });
  }

  /**
   * Mock 网络超时
   */
  async mockNetworkTimeout(pathPattern: string, delayMs: number = 30000) {
    await this.page.route(`**/api/v1/${pathPattern}`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
      await route.abort('timedout');
    });
  }

  /**
   * 清除所有路由拦截
   */
  async clearMocks() {
    await this.page.unrouteAll();
  }
}
