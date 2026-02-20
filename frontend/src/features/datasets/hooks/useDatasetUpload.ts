/**
 * 数据集文件上传 Hook
 *
 * 实现分片上传逻辑，支持进度追踪和取消操作。
 * 使用 XMLHttpRequest 实现上传以支持实时进度回调和 abort 取消。
 *
 * 分片策略: 每片 5MB，通过后端获取预签名 URL 后逐片上传，
 * 全部完成后调用 complete 接口合并分片。
 *
 * 状态流转: idle → uploading → completing → completed / error / cancelled
 */

import { useCallback, useRef, useState } from 'react';
import { apiClient } from '@shared/api';
import type {
  UploadProgress,
  UploadInitResponse,
  UploadPartResult,
  UploadCompleteRequest,
} from '../types';

/** 分片大小: 5MB */
const CHUNK_SIZE = 5 * 1024 * 1024;

/** Hook 返回值类型 */
export interface UseDatasetUploadReturn {
  /** 当前上传进度 */
  progress: UploadProgress;
  /** 开始上传文件 */
  upload: (file: File) => Promise<void>;
  /** 取消当前上传 */
  cancel: () => void;
  /** 重置上传状态 */
  reset: () => void;
}

/** 初始进度状态 */
const INITIAL_PROGRESS: UploadProgress = {
  loaded: 0,
  total: 0,
  percentage: 0,
  status: 'idle',
};

/**
 * 使用 XMLHttpRequest 上传单个分片到预签名 URL
 *
 * @param url 预签名上传 URL
 * @param chunk 文件分片数据
 * @param onProgress 进度回调（当前分片已上传字节数）
 * @param abortController 用于外部取消
 * @returns 分片上传完成后的 ETag
 */
function uploadChunk(
  url: string,
  chunk: Blob,
  onProgress: (loaded: number) => void,
  abortController: AbortController
): Promise<string> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // 监听上传进度
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        onProgress(event.loaded);
      }
    });

    // 上传完成
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        // 从响应头中获取 ETag
        const etag = xhr.getResponseHeader('ETag') ?? '';
        resolve(etag.replace(/"/g, ''));
      } else {
        reject(new Error(`分片上传失败: HTTP ${xhr.status}`));
      }
    });

    // 网络错误
    xhr.addEventListener('error', () => {
      reject(new Error('网络错误，分片上传失败'));
    });

    // 上传被取消
    xhr.addEventListener('abort', () => {
      reject(new Error('上传已取消'));
    });

    // 绑定外部 abort 信号
    const onAbort = () => {
      xhr.abort();
    };
    abortController.signal.addEventListener('abort', onAbort);

    xhr.open('PUT', url);
    xhr.send(chunk);
  });
}

/**
 * 数据集文件上传 Hook
 *
 * 提供分片上传、进度追踪、取消和重置功能。
 * 上传流程:
 * 1. 初始化上传，获取 upload_id 和预签名 URL 列表
 * 2. 按 5MB 分片逐片上传到预签名 URL
 * 3. 所有分片完成后，调用 complete 接口通知后端合并
 *
 * @returns 上传控制接口
 *
 * @example
 * ```tsx
 * const { progress, upload, cancel, reset } = useDatasetUpload();
 *
 * // 开始上传
 * await upload(file);
 *
 * // 取消上传
 * cancel();
 *
 * // 重置状态
 * reset();
 * ```
 */
export function useDatasetUpload(): UseDatasetUploadReturn {
  const [progress, setProgress] = useState<UploadProgress>(INITIAL_PROGRESS);
  const abortControllerRef = useRef<AbortController | null>(null);

  /**
   * 上传文件
   *
   * 流程:
   * 1. 调用 /datasets/uploads/init 获取 upload_id、dataset_id 和预签名 URL
   * 2. 按分片大小切分文件，逐片上传到对应的预签名 URL
   * 3. 所有分片完成后，调用 /datasets/{dataset_id}/uploads/complete 合并
   */
  const upload = useCallback(async (file: File): Promise<void> => {
    // 创建新的 AbortController 用于取消控制
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const totalSize = file.size;
    const chunkCount = Math.ceil(totalSize / CHUNK_SIZE);

    // 设置初始上传状态
    setProgress({
      loaded: 0,
      total: totalSize,
      percentage: 0,
      status: 'uploading',
    });

    try {
      // 第一步: 初始化分片上传，获取预签名 URL
      const initResponse = await apiClient.post<UploadInitResponse>(
        '/datasets/uploads/init',
        {
          filename: file.name,
          file_size: totalSize,
          part_count: chunkCount,
        }
      );

      const { upload_id, dataset_id, presigned_urls } = initResponse;
      const completedParts: UploadPartResult[] = [];

      // 已完成的累计字节数（不包含当前正在上传的分片）
      let completedBytes = 0;

      // 第二步: 逐片上传
      for (let i = 0; i < chunkCount; i++) {
        // 检查是否已取消
        if (controller.signal.aborted) {
          return;
        }

        const start = i * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, totalSize);
        const chunk = file.slice(start, end);
        const partNumber = i + 1;

        // 上传当前分片，实时更新进度
        const capturedCompletedBytes = completedBytes;
        const etag = await uploadChunk(
          presigned_urls[i],
          chunk,
          (chunkLoaded: number) => {
            const totalLoaded = capturedCompletedBytes + chunkLoaded;
            const percentage =
              totalSize > 0
                ? Math.round((totalLoaded / totalSize) * 100)
                : 0;
            setProgress({
              loaded: totalLoaded,
              total: totalSize,
              percentage: Math.min(percentage, 99), // 保留 100% 给完成阶段
              status: 'uploading',
            });
          },
          controller
        );

        completedParts.push({ part_number: partNumber, etag });
        completedBytes += end - start;
      }

      // 第三步: 通知后端合并分片
      setProgress((prev) => ({
        ...prev,
        percentage: 99,
        status: 'completing',
      }));

      const completeRequest: UploadCompleteRequest = {
        upload_id,
        parts: completedParts,
      };

      await apiClient.post(
        `/datasets/${dataset_id}/uploads/complete`,
        completeRequest
      );

      // 上传成功
      setProgress({
        loaded: totalSize,
        total: totalSize,
        percentage: 100,
        status: 'completed',
      });
    } catch (error: unknown) {
      // 取消导致的错误不设为 error 状态
      if (controller.signal.aborted) {
        setProgress((prev) => ({
          ...prev,
          status: 'cancelled',
        }));
        return;
      }

      const errorMessage =
        error instanceof Error ? error.message : '上传失败，请重试';

      setProgress((prev) => ({
        ...prev,
        status: 'error',
        error: errorMessage,
      }));
    } finally {
      abortControllerRef.current = null;
    }
  }, []);

  /** 取消当前上传 */
  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  /** 重置上传状态 */
  const reset = useCallback(() => {
    // 如果正在上传，先取消
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setProgress(INITIAL_PROGRESS);
  }, []);

  return { progress, upload, cancel, reset };
}
