/**
 * ApiClient 单元测试
 */

import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

// 工具函数: 创建 mock Response 对象
function createResponse(
  body: unknown,
  options: { status?: number; statusText?: string; headers?: Record<string, string> } = {}
) {
  const { status = 200, statusText = 'OK', headers = {} } = options;
  const bodyStr = typeof body === 'string' ? body : JSON.stringify(body);
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText,
    headers: new Headers(headers),
    text: vi.fn().mockResolvedValue(bodyStr),
    json: vi.fn().mockResolvedValue(body),
    blob: vi.fn().mockResolvedValue(new Blob(['test'])),
  } as unknown as Response;
}

// 辅助函数: 验证 AppError 实例（跨模块边界安全）
function expectAppError(error: unknown) {
  expect(error).toBeTruthy();
  expect((error as { isAppError?: boolean }).isAppError).toBe(true);
  expect((error as { name?: string }).name).toBe('AppError');
}

describe('ApiClient', () => {
  let mockFetch: ReturnType<typeof vi.fn>;
  let ApiClient: typeof import('@shared/api/client').ApiClient;
  let client: InstanceType<typeof ApiClient>;

  beforeEach(async () => {
    mockFetch = vi.fn();
    vi.stubGlobal('fetch', mockFetch);
    vi.stubGlobal('localStorage', {
      getItem: vi.fn().mockReturnValue(null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });

    const mod = await import('@shared/api/client');
    ApiClient = mod.ApiClient;
    client = new ApiClient('https://api.test.com');
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.resetModules();
  });

  // === GET ===

  describe('get', () => {
    it('应发起 GET 请求并返回数据', async () => {
      const responseData = { items: [{ id: 1, name: 'test' }], total: 1 };
      mockFetch.mockResolvedValue(createResponse(responseData));

      const result = await client.get('/training-jobs');

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const [url, options] = mockFetch.mock.calls[0];
      expect(url).toBe('https://api.test.com/training-jobs');
      expect(options.method).toBe('GET');
      expect(result).toEqual(responseData);
    });

    it('应正确拼接查询参数', async () => {
      mockFetch.mockResolvedValue(createResponse({ items: [] }));

      await client.get('/training-jobs', {
        params: { page: 1, page_size: 20, status: 'running' },
      });

      const [url] = mockFetch.mock.calls[0];
      expect(url).toContain('page=1');
      expect(url).toContain('page_size=20');
      expect(url).toContain('status=running');
    });

    it('应跳过 undefined/null/空字符串的查询参数', async () => {
      mockFetch.mockResolvedValue(createResponse({ items: [] }));

      await client.get('/training-jobs', {
        params: { page: 1, status: undefined, name: null, empty: '' },
      });

      const [url] = mockFetch.mock.calls[0];
      expect(url).toContain('page=1');
      expect(url).not.toContain('status');
      expect(url).not.toContain('name=');
      expect(url).not.toContain('empty');
    });

    it('应支持数组查询参数', async () => {
      mockFetch.mockResolvedValue(createResponse({ items: [] }));

      await client.get('/training-jobs', {
        params: { status: ['running', 'completed'] },
      });

      const [url] = mockFetch.mock.calls[0];
      expect(url).toContain('status=running');
      expect(url).toContain('status=completed');
    });
  });

  // === POST ===

  describe('post', () => {
    it('应发起 POST 请求并发送 JSON body', async () => {
      const requestBody = { name: 'new-job', instance_type: 'ml.p4d.24xlarge' };
      const responseData = { id: 1, ...requestBody };
      mockFetch.mockResolvedValue(createResponse(responseData));

      const result = await client.post('/training-jobs', requestBody);

      const [, options] = mockFetch.mock.calls[0];
      expect(options.method).toBe('POST');
      expect(options.body).toBe(JSON.stringify(requestBody));
      expect(result).toEqual(responseData);
    });

    it('应在 body 为 undefined 时不设置 body', async () => {
      mockFetch.mockResolvedValue(createResponse(null));

      await client.post('/training-jobs/1/start');

      const [, options] = mockFetch.mock.calls[0];
      expect(options.body).toBeUndefined();
    });
  });

  // === PUT ===

  describe('put', () => {
    it('应发起 PUT 请求', async () => {
      const data = { name: 'updated' };
      mockFetch.mockResolvedValue(createResponse(data));

      await client.put('/training-jobs/1', data);

      const [, options] = mockFetch.mock.calls[0];
      expect(options.method).toBe('PUT');
    });
  });

  // === PATCH ===

  describe('patch', () => {
    it('应发起 PATCH 请求', async () => {
      const data = { status: 'paused' };
      mockFetch.mockResolvedValue(createResponse(data));

      await client.patch('/training-jobs/1', data);

      const [, options] = mockFetch.mock.calls[0];
      expect(options.method).toBe('PATCH');
    });
  });

  // === DELETE ===

  describe('delete', () => {
    it('应发起 DELETE 请求', async () => {
      mockFetch.mockResolvedValue(createResponse(''));

      await client.delete('/training-jobs/1');

      const [url, options] = mockFetch.mock.calls[0];
      expect(url).toBe('https://api.test.com/training-jobs/1');
      expect(options.method).toBe('DELETE');
    });
  });

  // === 错误处理 ===

  describe('错误处理', () => {
    it('4xx 错误应抛出 AppError', async () => {
      mockFetch.mockResolvedValue(
        createResponse(
          { error: { code: 'NOT_FOUND', message: '资源不存在' } },
          { status: 404, statusText: 'Not Found' }
        )
      );

      try {
        await client.get('/training-jobs/999');
        expect.fail('应抛出错误');
      } catch (error) {
        expectAppError(error);
        expect((error as { code: string }).code).toBe('NOT_FOUND');
      }
    });

    it('4xx 错误不应重试', async () => {
      mockFetch.mockResolvedValue(
        createResponse(
          { error: { code: 'VALIDATION_ERROR', message: '验证失败' } },
          { status: 422, statusText: 'Unprocessable Entity' }
        )
      );

      try {
        await client.get('/training-jobs', { retries: 3 });
        expect.fail('应抛出错误');
      } catch (error) {
        expectAppError(error);
      }

      // 只调用一次，不重试
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('5xx 错误应重试指定次数', async () => {
      mockFetch.mockResolvedValue(
        createResponse(
          { error: { code: 'UNKNOWN', message: '服务器错误' } },
          { status: 500, statusText: 'Internal Server Error' }
        )
      );

      try {
        await client.get('/training-jobs', { retries: 2, retryDelay: 1 });
        expect.fail('应抛出错误');
      } catch (error) {
        expectAppError(error);
      }

      // 初始 + 2 次重试 = 3 次
      expect(mockFetch).toHaveBeenCalledTimes(3);
    }, 10000);

    it('5xx 后重试成功时应返回数据', async () => {
      const successResponse = createResponse({ items: [] });

      mockFetch
        .mockResolvedValueOnce(
          createResponse(
            { error: { code: 'UNKNOWN', message: '错误' } },
            { status: 500 }
          )
        )
        .mockResolvedValueOnce(successResponse);

      const result = await client.get('/training-jobs', {
        retries: 1,
        retryDelay: 1,
      });

      expect(result).toEqual({ items: [] });
      expect(mockFetch).toHaveBeenCalledTimes(2);
    });

    it('网络错误应抛出 AppError(NETWORK_ERROR)', async () => {
      mockFetch.mockRejectedValue(new TypeError('Failed to fetch'));

      try {
        await client.get('/training-jobs');
        expect.fail('应抛出错误');
      } catch (error) {
        expectAppError(error);
        expect((error as { code: string }).code).toBe('NETWORK_ERROR');
      }
    });

    it('响应为 API 错误格式时应抛出 AppError', async () => {
      mockFetch.mockResolvedValue(
        createResponse({
          error: {
            code: 'JOB_QUOTA_EXCEEDED',
            message: '超出训练任务配额限制',
            details: { current: 10, limit: 10 },
          },
        })
      );

      try {
        await client.get('/training-jobs');
        expect.fail('应抛出错误');
      } catch (error) {
        expectAppError(error);
        expect((error as { code: string }).code).toBe('JOB_QUOTA_EXCEEDED');
      }
    });
  });

  // === 认证 ===

  describe('认证', () => {
    it('setAuthToken 应在 header 中添加 Authorization', async () => {
      mockFetch.mockResolvedValue(createResponse({ items: [] }));

      client.setAuthToken('test-token');
      await client.get('/training-jobs');

      const [, options] = mockFetch.mock.calls[0];
      expect(options.headers['Authorization']).toBe('Bearer test-token');
    });

    it('clearAuthToken 应移除 Authorization header', async () => {
      mockFetch.mockResolvedValue(createResponse({ items: [] }));

      client.setAuthToken('test-token');
      client.clearAuthToken();
      await client.get('/training-jobs');

      const [, options] = mockFetch.mock.calls[0];
      expect(options.headers['Authorization']).toBeUndefined();
    });

    it('应从 localStorage 自动获取 token', async () => {
      (localStorage.getItem as ReturnType<typeof vi.fn>).mockReturnValue('stored-token');
      mockFetch.mockResolvedValue(createResponse({ items: [] }));

      await client.get('/training-jobs');

      const [, options] = mockFetch.mock.calls[0];
      expect(options.headers['Authorization']).toBe('Bearer stored-token');
    });

    it('显式设置的 token 应优先于 localStorage', async () => {
      (localStorage.getItem as ReturnType<typeof vi.fn>).mockReturnValue('stored-token');
      mockFetch.mockResolvedValue(createResponse({ items: [] }));

      client.setAuthToken('explicit-token');
      await client.get('/training-jobs');

      const [, options] = mockFetch.mock.calls[0];
      expect(options.headers['Authorization']).toBe('Bearer explicit-token');
    });
  });

  // === download ===

  describe('download', () => {
    it('应返回 Blob', async () => {
      const blob = new Blob(['file-content'], { type: 'application/octet-stream' });
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        blob: vi.fn().mockResolvedValue(blob),
      });

      const result = await client.download('/files/export.csv');

      expect(result).toBeInstanceOf(Blob);
    });

    it('下载失败应抛出 AppError', async () => {
      mockFetch.mockResolvedValue({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: vi.fn().mockResolvedValue({
          error: { code: 'NOT_FOUND', message: '文件不存在' },
        }),
      });

      try {
        await client.download('/files/nonexistent.csv');
        expect.fail('应抛出错误');
      } catch (error) {
        expectAppError(error);
      }
    });
  });

  // === upload ===

  describe('upload', () => {
    it('应使用 FormData 上传文件', async () => {
      const file = new File(['content'], 'data.csv', { type: 'text/csv' });
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: vi.fn().mockResolvedValue({ id: 1, filename: 'data.csv' }),
      });

      const result = await client.upload('/datasets/upload', file);

      expect(result).toEqual({ id: 1, filename: 'data.csv' });

      const [, options] = mockFetch.mock.calls[0];
      expect(options.method).toBe('POST');
      expect(options.body).toBeInstanceOf(FormData);
      expect(options.headers['Content-Type']).toBeUndefined();
    });

    it('应支持自定义字段名和附加数据', async () => {
      const file = new File(['content'], 'model.pt', { type: 'application/octet-stream' });
      mockFetch.mockResolvedValue({
        ok: true,
        status: 200,
        json: vi.fn().mockResolvedValue({ id: 1 }),
      });

      await client.upload('/models/upload', file, 'model_file', {
        name: 'my-model',
        version: '1.0',
      });

      const [, options] = mockFetch.mock.calls[0];
      const formData = options.body as FormData;
      expect(formData.get('model_file')).toBeTruthy();
      expect(formData.get('name')).toBe('my-model');
      expect(formData.get('version')).toBe('1.0');
    });

    it('上传失败应抛出 AppError', async () => {
      const file = new File(['content'], 'data.csv');
      mockFetch.mockResolvedValue({
        ok: false,
        status: 413,
        statusText: 'Payload Too Large',
        json: vi.fn().mockResolvedValue({
          error: { code: 'VALIDATION_ERROR', message: '文件过大' },
        }),
      });

      try {
        await client.upload('/datasets/upload', file);
        expect.fail('应抛出错误');
      } catch (error) {
        expectAppError(error);
      }
    });
  });

  // === 空响应处理 ===

  describe('空响应处理', () => {
    it('应正确处理空响应 (204 No Content)', async () => {
      mockFetch.mockResolvedValue({
        ok: true,
        status: 204,
        statusText: 'No Content',
        headers: new Headers(),
        text: vi.fn().mockResolvedValue(''),
      });

      const result = await client.delete('/training-jobs/1');
      expect(result).toBeNull();
    });
  });
});
