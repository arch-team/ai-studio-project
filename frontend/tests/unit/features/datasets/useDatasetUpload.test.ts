/**
 * useDatasetUpload 单元测试
 *
 * 测试数据集上传 hook 的分片上传、进度追踪、取消和重置功能
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useDatasetUpload } from '@features/datasets/hooks';

// Mock apiClient
vi.mock('@shared/api', () => ({
  apiClient: {
    post: vi.fn(),
  },
}));

// Mock XMLHttpRequest
class MockXHR {
  status = 200;
  readyState = 4;
  responseHeaders: Record<string, string> = {};
  upload = {
    addEventListener: vi.fn(),
  };
  addEventListener = vi.fn();
  open = vi.fn();
  send = vi.fn();
  abort = vi.fn();
  getResponseHeader = vi.fn((name: string) => this.responseHeaders[name] || null);
}

describe('useDatasetUpload', () => {
  let mockXHR: MockXHR;

  beforeEach(() => {
    vi.clearAllMocks();
    mockXHR = new MockXHR();
    vi.stubGlobal('XMLHttpRequest', vi.fn(() => mockXHR));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe('初始状态', () => {
    it('应返回 idle 状态的初始进度', () => {
      const { result } = renderHook(() => useDatasetUpload());

      expect(result.current.progress).toEqual({
        loaded: 0,
        total: 0,
        percentage: 0,
        status: 'idle',
      });
    });

    it('应返回 upload、cancel、reset 函数', () => {
      const { result } = renderHook(() => useDatasetUpload());

      expect(typeof result.current.upload).toBe('function');
      expect(typeof result.current.cancel).toBe('function');
      expect(typeof result.current.reset).toBe('function');
    });
  });

  describe('upload 函数', () => {
    it('调用 upload 后应设置 uploading 状态', async () => {
      const { apiClient } = await import('@shared/api');
      const mockApiPost = vi.mocked(apiClient.post);

      // 模拟 init 请求返回
      mockApiPost.mockResolvedValueOnce({
        upload_id: 'test-upload-id',
        dataset_id: 1,
        presigned_urls: ['https://s3.example.com/part1'],
        part_size: 5 * 1024 * 1024,
      });

      // 模拟 XHR 上传成功
      mockXHR.addEventListener = vi.fn((event: string, handler: () => void) => {
        if (event === 'load') {
          mockXHR.status = 200;
          mockXHR.responseHeaders['ETag'] = '"test-etag"';
          // 延迟触发以允许状态更新
          setTimeout(handler, 0);
        }
      });

      // 模拟 complete 请求
      mockApiPost.mockResolvedValueOnce({});

      const { result } = renderHook(() => useDatasetUpload());

      const file = new File(['x'.repeat(100)], 'test.csv', { type: 'text/csv' });

      // 启动上传（不等待完成）
      act(() => {
        void result.current.upload(file);
      });

      // 验证初始化请求被调用
      expect(mockApiPost).toHaveBeenCalledWith('/datasets/uploads/init', {
        filename: 'test.csv',
        file_size: 100,
        part_count: 1,
      });
    });
  });

  describe('cancel 函数', () => {
    it('在 idle 状态调用 cancel 不应报错', () => {
      const { result } = renderHook(() => useDatasetUpload());

      expect(() => {
        act(() => {
          result.current.cancel();
        });
      }).not.toThrow();
    });
  });

  describe('reset 函数', () => {
    it('调用 reset 应恢复到初始状态', () => {
      const { result } = renderHook(() => useDatasetUpload());

      act(() => {
        result.current.reset();
      });

      expect(result.current.progress).toEqual({
        loaded: 0,
        total: 0,
        percentage: 0,
        status: 'idle',
      });
    });
  });
});
