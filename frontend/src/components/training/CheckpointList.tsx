/**
 * 检查点列表组件
 *
 * 展示训练任务的所有检查点,支持查看详情和下载
 */

import React from 'react';
import { Card } from '../shared/Card';
import { Button } from '../shared/Button';

export interface Checkpoint {
  id: number;
  step: number;
  epoch?: number;
  storage_path: string;
  storage_type: 'LOCAL' | 'FSX' | 'S3';
  size_bytes: number;
  checkpoint_metadata?: Record<string, any>;
  checkpoint_metrics?: Record<string, number>;
  created_at: string;
}

interface CheckpointListProps {
  checkpoints: Checkpoint[];
  loading?: boolean;
  onDownload?: (checkpoint: Checkpoint) => void;
  onRestore?: (checkpoint: Checkpoint) => void;
  onDelete?: (checkpoint: Checkpoint) => void;
}

// 存储类型对应的颜色和图标
const STORAGE_TYPE_CONFIG: Record<string, { color: string; label: string }> = {
  LOCAL: { color: 'bg-green-100 text-green-800', label: 'NVMe本地' },
  FSX: { color: 'bg-blue-100 text-blue-800', label: 'FSx高速' },
  S3: { color: 'bg-purple-100 text-purple-800', label: 'S3存储' },
};

// 格式化文件大小
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
};

// 格式化时间
const formatTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

export const CheckpointList: React.FC<CheckpointListProps> = ({
  checkpoints,
  loading = false,
  onDownload,
  onRestore,
  onDelete,
}) => {
  if (loading) {
    return (
      <Card>
        <h3 className="text-lg font-semibold mb-4">训练检查点</h3>
        <div className="p-8 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">加载检查点...</p>
        </div>
      </Card>
    );
  }

  if (checkpoints.length === 0) {
    return (
      <Card>
        <h3 className="text-lg font-semibold mb-4">训练检查点</h3>
        <div className="p-8 text-center text-gray-500">
          暂无检查点
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">训练检查点</h3>
        <span className="text-sm text-gray-600">
          共 {checkpoints.length} 个检查点
        </span>
      </div>

      <div className="space-y-3">
        {checkpoints.map((checkpoint) => {
          const storageConfig = STORAGE_TYPE_CONFIG[checkpoint.storage_type];

          return (
            <div
              key={checkpoint.id}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                {/* 左侧信息 */}
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h4 className="font-semibold text-gray-900">
                      Step {checkpoint.step}
                      {checkpoint.epoch !== undefined &&
                        ` (Epoch ${checkpoint.epoch})`}
                    </h4>
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded ${storageConfig.color}`}
                    >
                      {storageConfig.label}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                    <div>
                      <span className="font-medium">大小:</span>{' '}
                      {formatBytes(checkpoint.size_bytes)}
                    </div>
                    <div>
                      <span className="font-medium">创建时间:</span>{' '}
                      {formatTime(checkpoint.created_at)}
                    </div>
                    <div className="col-span-2">
                      <span className="font-medium">存储路径:</span>{' '}
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {checkpoint.storage_path}
                      </code>
                    </div>
                  </div>

                  {/* 检查点指标 */}
                  {checkpoint.checkpoint_metrics &&
                    Object.keys(checkpoint.checkpoint_metrics).length > 0 && (
                      <div className="mt-3 p-3 bg-gray-50 rounded">
                        <p className="text-xs font-medium text-gray-700 mb-2">
                          训练指标:
                        </p>
                        <div className="grid grid-cols-3 gap-2 text-xs">
                          {Object.entries(checkpoint.checkpoint_metrics).map(
                            ([key, value]) => (
                              <div key={key}>
                                <span className="text-gray-600">{key}:</span>{' '}
                                <span className="font-mono text-gray-900">
                                  {typeof value === 'number'
                                    ? value.toFixed(4)
                                    : value}
                                </span>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )}
                </div>

                {/* 右侧操作按钮 */}
                <div className="ml-4 flex flex-col space-y-2">
                  {onDownload && (
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => onDownload(checkpoint)}
                    >
                      下载
                    </Button>
                  )}
                  {onRestore && (
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => onRestore(checkpoint)}
                    >
                      恢复训练
                    </Button>
                  )}
                  {onDelete && (
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => onDelete(checkpoint)}
                    >
                      删除
                    </Button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* 存储类型说明 */}
      <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-xs font-medium text-blue-900 mb-2">
          分层存储说明:
        </p>
        <ul className="text-xs text-blue-800 space-y-1">
          <li>• <strong>NVMe本地</strong>: 最快的访问速度,用于活跃训练</li>
          <li>• <strong>FSx高速</strong>: 共享高性能存储,用于近期检查点</li>
          <li>• <strong>S3存储</strong>: 长期归档存储,成本最低</li>
        </ul>
      </div>
    </Card>
  );
};

export default CheckpointList;
