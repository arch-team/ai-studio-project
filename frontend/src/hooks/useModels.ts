/**
 * 模型管理相关的React Query hooks
 */

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryResult,
  type UseMutationResult,
} from '@tanstack/react-query';
import { modelApi, modelVersionApi } from '@/api/model';
import type {
  Model,
  ModelCreateRequest,
  ModelUpdateRequest,
  ModelListResponse,
  ModelQueryParams,
  ModelVersion,
  ModelVersionCreateRequest,
  ModelVersionUpdateRequest,
  ModelVersionListResponse,
  ModelFilesResponse,
  ModelStorageStats,
  ModelStatus,
} from '@/types/model';

// ==================== Query Keys ====================

export const modelQueryKeys = {
  all: ['models'] as const,
  lists: () => [...modelQueryKeys.all, 'list'] as const,
  list: (params?: ModelQueryParams) => [...modelQueryKeys.lists(), params] as const,
  details: () => [...modelQueryKeys.all, 'detail'] as const,
  detail: (id: number) => [...modelQueryKeys.details(), id] as const,
  stats: (id: number) => [...modelQueryKeys.detail(id), 'stats'] as const,
  versions: (id: number) => [...modelQueryKeys.detail(id), 'versions'] as const,
  versionDetail: (modelId: number, versionId: number) =>
    [...modelQueryKeys.versions(modelId), versionId] as const,
  versionFiles: (modelId: number, version: string) =>
    [...modelQueryKeys.versions(modelId), version, 'files'] as const,
};

// ==================== 模型管理 Hooks ====================

/**
 * 查询模型列表
 */
export function useModels(
  params?: ModelQueryParams
): UseQueryResult<ModelListResponse, Error> {
  return useQuery({
    queryKey: modelQueryKeys.list(params),
    queryFn: () => modelApi.listModels(params),
    staleTime: 30000, // 30秒内认为数据新鲜
  });
}

/**
 * 获取模型详情
 */
export function useModel(modelId: number): UseQueryResult<Model, Error> {
  return useQuery({
    queryKey: modelQueryKeys.detail(modelId),
    queryFn: () => modelApi.getModel(modelId),
    enabled: !!modelId,
    staleTime: 30000,
  });
}

/**
 * 获取模型存储统计
 */
export function useModelStats(
  modelId: number
): UseQueryResult<ModelStorageStats, Error> {
  return useQuery({
    queryKey: modelQueryKeys.stats(modelId),
    queryFn: () => modelApi.getModelStats(modelId),
    enabled: !!modelId,
  });
}

/**
 * 创建模型
 */
export function useCreateModel(): UseMutationResult<
  Model,
  Error,
  ModelCreateRequest,
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ModelCreateRequest) => modelApi.createModel(data),
    onSuccess: () => {
      // 使列表缓存失效
      queryClient.invalidateQueries({ queryKey: modelQueryKeys.lists() });
    },
  });
}

/**
 * 更新模型
 */
export function useUpdateModel(): UseMutationResult<
  Model,
  Error,
  { modelId: number; data: ModelUpdateRequest },
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ modelId, data }) => modelApi.updateModel(modelId, data),
    onSuccess: (_, { modelId }) => {
      // 使详情和列表缓存失效
      queryClient.invalidateQueries({ queryKey: modelQueryKeys.detail(modelId) });
      queryClient.invalidateQueries({ queryKey: modelQueryKeys.lists() });
    },
  });
}

/**
 * 删除模型
 */
export function useDeleteModel(): UseMutationResult<
  void,
  Error,
  { modelId: number; force?: boolean },
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ modelId, force }) => modelApi.deleteModel(modelId, force),
    onSuccess: () => {
      // 使列表缓存失效
      queryClient.invalidateQueries({ queryKey: modelQueryKeys.lists() });
    },
  });
}

// ==================== 模型版本管理 Hooks ====================

/**
 * 查询模型的所有版本
 */
export function useModelVersions(
  modelId: number,
  status?: ModelStatus
): UseQueryResult<ModelVersionListResponse, Error> {
  return useQuery({
    queryKey: [...modelQueryKeys.versions(modelId), status],
    queryFn: () => modelVersionApi.listVersions(modelId, status),
    enabled: !!modelId,
  });
}

/**
 * 获取模型版本详情
 */
export function useModelVersion(
  modelId: number,
  versionId: number
): UseQueryResult<ModelVersion, Error> {
  return useQuery({
    queryKey: modelQueryKeys.versionDetail(modelId, versionId),
    queryFn: () => modelVersionApi.getVersion(modelId, versionId),
    enabled: !!modelId && !!versionId,
  });
}

/**
 * 上传文件创建模型版本
 */
export function useCreateModelVersion(): UseMutationResult<
  ModelVersion,
  Error,
  { modelId: number; file: File; data: ModelVersionCreateRequest },
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ modelId, file, data }) =>
      modelVersionApi.createVersionWithUpload(modelId, file, data),
    onSuccess: (_, { modelId }) => {
      // 使版本列表和模型详情缓存失效
      queryClient.invalidateQueries({ queryKey: modelQueryKeys.versions(modelId) });
      queryClient.invalidateQueries({ queryKey: modelQueryKeys.detail(modelId) });
    },
  });
}

/**
 * 更新模型版本
 */
export function useUpdateModelVersion(): UseMutationResult<
  ModelVersion,
  Error,
  { modelId: number; versionId: number; data: ModelVersionUpdateRequest },
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ modelId, versionId, data }) =>
      modelVersionApi.updateVersion(modelId, versionId, data),
    onSuccess: (_, { modelId, versionId }) => {
      // 使版本详情和列表缓存失效
      queryClient.invalidateQueries({
        queryKey: modelQueryKeys.versionDetail(modelId, versionId),
      });
      queryClient.invalidateQueries({ queryKey: modelQueryKeys.versions(modelId) });
    },
  });
}

/**
 * 发布模型版本
 */
export function usePublishModelVersion(): UseMutationResult<
  ModelVersion,
  Error,
  { modelId: number; versionId: number },
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ modelId, versionId }) =>
      modelVersionApi.publishVersion(modelId, versionId),
    onSuccess: (_, { modelId, versionId }) => {
      // 使版本详情和列表缓存失效
      queryClient.invalidateQueries({
        queryKey: modelQueryKeys.versionDetail(modelId, versionId),
      });
      queryClient.invalidateQueries({ queryKey: modelQueryKeys.versions(modelId) });
    },
  });
}

/**
 * 删除模型版本
 */
export function useDeleteModelVersion(): UseMutationResult<
  void,
  Error,
  { modelId: number; versionId: number; force?: boolean },
  unknown
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ modelId, versionId, force }) =>
      modelVersionApi.deleteVersion(modelId, versionId, force),
    onSuccess: (_, { modelId }) => {
      // 使版本列表缓存失效
      queryClient.invalidateQueries({ queryKey: modelQueryKeys.versions(modelId) });
      queryClient.invalidateQueries({ queryKey: modelQueryKeys.detail(modelId) });
    },
  });
}

/**
 * 获取模型版本文件列表
 */
export function useModelVersionFiles(
  modelId: number,
  version: string
): UseQueryResult<ModelFilesResponse, Error> {
  return useQuery({
    queryKey: modelQueryKeys.versionFiles(modelId, version),
    queryFn: () => modelVersionApi.listVersionFiles(modelId, version),
    enabled: !!modelId && !!version,
  });
}
