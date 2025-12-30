/**
 * 模型详情和版本管理组件
 */

import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Package,
  Upload,
  Download,
  Trash2,
  CheckCircle,
  Clock,
  AlertCircle,
  FileText,
  Tag,
  Calendar,
  HardDrive,
  ArrowLeft,
  RefreshCw,
} from 'lucide-react';
import {
  useModel,
  useModelVersions,
  useModelStats,
  useDeleteModelVersion,
  usePublishModelVersion,
} from '@/hooks/useModels';
import {
  getStatusDisplay,
  getFrameworkDisplay,
  formatTimestamp,
  formatFileSize,
  formatVersion,
  canPublishVersion,
  stringifyTags,
} from '@/utils/model';
import type { ModelVersion } from '@/types/model';

export const ModelDetail: React.FC = () => {
  const { modelId } = useParams<{ modelId: string }>();
  const navigate = useNavigate();
  const [showUploadModal, setShowUploadModal] = useState(false);

  // 查询数据
  const {
    data: model,
    isLoading: modelLoading,
    error: modelError,
    refetch: refetchModel,
  } = useModel(Number(modelId));

  const {
    data: versionsData,
    isLoading: versionsLoading,
    error: versionsError,
    refetch: refetchVersions,
  } = useModelVersions(Number(modelId));

  const {
    data: stats,
    isLoading: statsLoading,
    refetch: refetchStats,
  } = useModelStats(Number(modelId));

  const deleteVersionMutation = useDeleteModelVersion();
  const publishVersionMutation = usePublishModelVersion();

  // 处理删除版本
  const handleDeleteVersion = async (version: ModelVersion) => {
    if (!confirm(`确认删除版本 ${formatVersion(version.version)}?`)) return;

    try {
      await deleteVersionMutation.mutateAsync({
        modelId: Number(modelId),
        versionId: version.id,
        force: false,
      });
      alert('删除成功');
      refetchVersions();
      refetchStats();
    } catch (error) {
      alert(`删除失败: ${error}`);
    }
  };

  // 处理发布版本
  const handlePublishVersion = async (version: ModelVersion) => {
    if (!confirm(`确认发布版本 ${formatVersion(version.version)}?`)) return;

    try {
      await publishVersionMutation.mutateAsync({
        modelId: Number(modelId),
        versionId: version.id,
      });
      alert('发布成功');
      refetchVersions();
    } catch (error) {
      alert(`发布失败: ${error}`);
    }
  };

  // 刷新所有数据
  const handleRefreshAll = () => {
    refetchModel();
    refetchVersions();
    refetchStats();
  };

  if (modelError || versionsError) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <p className="text-red-600 mb-4">
            加载失败: {modelError?.message || versionsError?.message}
          </p>
          <button
            onClick={handleRefreshAll}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  if (modelLoading || versionsLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!model) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-gray-500">模型不存在</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* 头部 */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/models')}
          className="flex items-center space-x-2 text-gray-600 hover:text-gray-800 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>返回列表</span>
        </button>

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Package className="w-10 h-10 text-blue-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-800">{model.name}</h1>
              {model.description && (
                <p className="text-gray-600 mt-1">{model.description}</p>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleRefreshAll}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
            >
              <RefreshCw className="w-5 h-5" />
              <span>刷新</span>
            </button>
            <button
              onClick={() => setShowUploadModal(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Upload className="w-5 h-5" />
              <span>上传版本</span>
            </button>
          </div>
        </div>
      </div>

      {/* 模型信息卡片 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* 基本信息 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">基本信息</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">框架:</span>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded">
                {getFrameworkDisplay(model.framework)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">任务类型:</span>
              <span className="text-gray-800">{model.task_type || '-'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">最新版本:</span>
              <span className="font-medium text-gray-800">
                {formatVersion(model.latest_version)}
              </span>
            </div>
            <div className="flex items-start justify-between">
              <span className="text-gray-600">标签:</span>
              <div className="flex flex-wrap gap-1 justify-end">
                {model.tags && model.tags.length > 0 ? (
                  model.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                    >
                      {tag}
                    </span>
                  ))
                ) : (
                  <span className="text-gray-500">-</span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* 存储统计 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">存储统计</h2>
          {statsLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">总大小:</span>
                <span className="font-medium text-gray-800">
                  {formatFileSize(stats?.total_size)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">文件数:</span>
                <span className="text-gray-800">{stats?.file_count || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">版本数:</span>
                <span className="text-gray-800">{stats?.version_count || 0}</span>
              </div>
            </div>
          )}
        </div>

        {/* 时间信息 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">时间信息</h2>
          <div className="space-y-3">
            <div className="flex items-start justify-between">
              <span className="text-gray-600">创建时间:</span>
              <span className="text-gray-800 text-right">
                {formatTimestamp(model.created_at)}
              </span>
            </div>
            <div className="flex items-start justify-between">
              <span className="text-gray-600">更新时间:</span>
              <span className="text-gray-800 text-right">
                {formatTimestamp(model.updated_at)}
              </span>
            </div>
            {model.source_training_job_id && (
              <div className="flex items-start justify-between">
                <span className="text-gray-600">来源训练任务:</span>
                <button
                  onClick={() =>
                    navigate(`/training/jobs/${model.source_training_job_id}`)
                  }
                  className="text-blue-600 hover:text-blue-800"
                >
                  #{model.source_training_job_id}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 版本列表 */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800">版本历史</h2>
        </div>

        {versionsData?.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16">
            <FileText className="w-16 h-16 text-gray-300 mb-4" />
            <p className="text-gray-500 text-lg mb-2">暂无版本</p>
            <button
              onClick={() => setShowUploadModal(true)}
              className="text-blue-600 hover:text-blue-700"
            >
              上传第一个版本
            </button>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {versionsData?.items.map((version) => {
              const statusInfo = getStatusDisplay(version.status);
              const canPublish = canPublishVersion(
                version.status,
                version.is_published
              );

              return (
                <div key={version.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-lg font-semibold text-gray-800">
                          {formatVersion(version.version)}
                        </h3>
                        <span
                          className={`px-2 py-1 text-xs rounded ${statusInfo.bgColor} ${statusInfo.color}`}
                        >
                          {statusInfo.label}
                        </span>
                        {version.is_published && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                            已发布
                          </span>
                        )}
                      </div>

                      {version.description && (
                        <p className="text-gray-600 mb-3">{version.description}</p>
                      )}

                      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">格式:</span>
                          <span className="ml-2 text-gray-800">
                            {version.model_format || '-'}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">架构:</span>
                          <span className="ml-2 text-gray-800">
                            {version.model_architecture || '-'}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">大小:</span>
                          <span className="ml-2 text-gray-800">
                            {formatFileSize(version.storage_size_bytes)}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">MD5:</span>
                          <span className="ml-2 text-gray-800 font-mono text-xs">
                            {version.checksum_md5?.substring(0, 8) || '-'}
                          </span>
                        </div>
                      </div>

                      {version.metrics && Object.keys(version.metrics).length > 0 && (
                        <div className="mt-3 p-3 bg-gray-50 rounded">
                          <span className="text-sm font-medium text-gray-700">
                            性能指标:
                          </span>
                          <div className="mt-2 grid grid-cols-2 lg:grid-cols-4 gap-2">
                            {Object.entries(version.metrics).map(([key, value]) => (
                              <div key={key} className="text-sm">
                                <span className="text-gray-600">{key}:</span>
                                <span className="ml-2 text-gray-800 font-medium">
                                  {String(value)}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="mt-3 text-sm text-gray-500">
                        创建于 {formatTimestamp(version.created_at)}
                        {version.published_at && (
                          <span>
                            {' '}
                            · 发布于 {formatTimestamp(version.published_at)}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center space-x-2 ml-4">
                      {canPublish && (
                        <button
                          onClick={() => handlePublishVersion(version)}
                          className="p-2 text-green-600 hover:bg-green-50 rounded"
                          title="发布版本"
                        >
                          <CheckCircle className="w-5 h-5" />
                        </button>
                      )}
                      <button
                        onClick={() =>
                          navigate(
                            `/models/${modelId}/versions/${version.id}/files`
                          )
                        }
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                        title="查看文件"
                      >
                        <FileText className="w-5 h-5" />
                      </button>
                      <button
                        onClick={() => handleDeleteVersion(version)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded"
                        title="删除版本"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 上传模态框 */}
      {showUploadModal && (
        <UploadVersionModal
          modelId={Number(modelId)}
          onClose={() => setShowUploadModal(false)}
          onSuccess={() => {
            setShowUploadModal(false);
            refetchVersions();
            refetchStats();
            refetchModel();
          }}
        />
      )}
    </div>
  );
};

// 上传版本模态框组件(简化版,实际应该独立文件)
const UploadVersionModal: React.FC<{
  modelId: number;
  onClose: () => void;
  onSuccess: () => void;
}> = ({ modelId, onClose, onSuccess }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full">
        <h3 className="text-xl font-semibold mb-4">上传模型版本</h3>
        <p className="text-gray-600 mb-4">版本上传功能即将完成...</p>
        <button
          onClick={onClose}
          className="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
        >
          关闭
        </button>
      </div>
    </div>
  );
};

export default ModelDetail;
