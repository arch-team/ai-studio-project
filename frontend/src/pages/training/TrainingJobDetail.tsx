/**
 * 训练任务详情页面
 */

import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import trainingApi from '../../api/training';
import type {
  TrainingJob,
  TrainingJobStatusResponse,
  TrainingJobMetrics,
  Checkpoint
} from '../../types/training';
import { TrainingJobStatus } from '../../types/training';

export default function TrainingJobDetail() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [job, setJob] = useState<TrainingJob | null>(null);
  const [status, setStatus] = useState<TrainingJobStatusResponse | null>(null);
  const [metrics, setMetrics] = useState<TrainingJobMetrics[]>([]);
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [logs, setLogs] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'metrics' | 'logs' | 'checkpoints'>('overview');

  // 加载任务详情
  const loadJobDetail = async () => {
    if (!jobId) return;

    try {
      setLoading(true);
      setError(null);

      const [jobData, statusData] = await Promise.all([
        trainingApi.getJob(Number(jobId)),
        trainingApi.getJobStatus(Number(jobId)),
      ]);

      setJob(jobData);
      setStatus(statusData);
    } catch (err: any) {
      setError(err.response?.data?.detail || '加载任务详情失败');
      console.error('Failed to load job detail:', err);
    } finally {
      setLoading(false);
    }
  };

  // 加载指标数据
  const loadMetrics = async () => {
    if (!jobId) return;

    try {
      const metricsData = await trainingApi.getJobMetrics(Number(jobId), { limit: 100 });
      setMetrics(metricsData);
    } catch (err) {
      console.error('Failed to load metrics:', err);
    }
  };

  // 加载检查点
  const loadCheckpoints = async () => {
    if (!jobId) return;

    try {
      const checkpointsData = await trainingApi.getJobCheckpoints(Number(jobId), { limit: 10 });
      setCheckpoints(checkpointsData);
    } catch (err) {
      console.error('Failed to load checkpoints:', err);
    }
  };

  // 加载日志
  const loadLogs = async () => {
    if (!jobId) return;

    try {
      const logsData = await trainingApi.getJobLogs(Number(jobId), { tail_lines: 100 });
      setLogs(logsData.logs);
    } catch (err) {
      console.error('Failed to load logs:', err);
    }
  };

  useEffect(() => {
    loadJobDetail();
  }, [jobId]);

  useEffect(() => {
    if (activeTab === 'metrics') loadMetrics();
    if (activeTab === 'checkpoints') loadCheckpoints();
    if (activeTab === 'logs') loadLogs();
  }, [activeTab]);

  // 启动任务
  const handleStart = async () => {
    if (!jobId || !window.confirm('确定要启动此训练任务吗?')) return;

    try {
      await trainingApi.startJob(Number(jobId));
      await loadJobDetail();
    } catch (err: any) {
      alert(err.response?.data?.detail || '启动任务失败');
    }
  };

  // 停止任务
  const handleStop = async () => {
    if (!jobId || !window.confirm('确定要停止此训练任务吗?')) return;

    try {
      await trainingApi.stopJob(Number(jobId));
      await loadJobDetail();
    } catch (err: any) {
      alert(err.response?.data?.detail || '停止任务失败');
    }
  };

  // 同步状态
  const handleSync = async () => {
    if (!jobId) return;

    try {
      await trainingApi.syncJobStatus(Number(jobId));
      await loadJobDetail();
    } catch (err: any) {
      alert(err.response?.data?.detail || '同步状态失败');
    }
  };

  // 状态徽章样式
  const getStatusBadgeClass = (jobStatus: TrainingJobStatus) => {
    const baseClass = 'px-3 py-1 rounded-full text-sm font-medium';
    switch (jobStatus) {
      case TrainingJobStatus.RUNNING:
        return `${baseClass} bg-blue-100 text-blue-800`;
      case TrainingJobStatus.COMPLETED:
        return `${baseClass} bg-green-100 text-green-800`;
      case TrainingJobStatus.FAILED:
        return `${baseClass} bg-red-100 text-red-800`;
      case TrainingJobStatus.CANCELLED:
        return `${baseClass} bg-gray-100 text-gray-800`;
      case TrainingJobStatus.PENDING:
      case TrainingJobStatus.QUEUED:
        return `${baseClass} bg-yellow-100 text-yellow-800`;
      default:
        return `${baseClass} bg-gray-100 text-gray-800`;
    }
  };

  // 格式化时间
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  // 格式化文件大小
  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-gray-500">加载中...</div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded">
          {error || '任务不存在'}
        </div>
        <button
          onClick={() => navigate('/training')}
          className="mt-4 px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
        >
          返回列表
        </button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* 页面标题和操作 */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/training')}
            className="text-gray-600 hover:text-gray-900"
          >
            ← 返回
          </button>
          <h1 className="text-2xl font-bold text-gray-900">{job.name}</h1>
          <span className={getStatusBadgeClass(job.status)}>{job.status}</span>
        </div>

        <div className="flex gap-2">
          {job.status === TrainingJobStatus.PENDING && (
            <button
              onClick={handleStart}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              启动
            </button>
          )}
          {job.status === TrainingJobStatus.RUNNING && (
            <button
              onClick={handleStop}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              停止
            </button>
          )}
          <button
            onClick={handleSync}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
          >
            同步状态
          </button>
        </div>
      </div>

      {/* 标签页 */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-8">
          {['overview', 'metrics', 'logs', 'checkpoints'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab === 'overview' && '概览'}
              {tab === 'metrics' && '训练指标'}
              {tab === 'logs' && '日志'}
              {tab === 'checkpoints' && '检查点'}
            </button>
          ))}
        </nav>
      </div>

      {/* 概览标签 */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* 基本信息 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">基本信息</h2>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-gray-500">任务ID:</dt>
                <dd className="font-medium">{job.id}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">任务类型:</dt>
                <dd className="font-medium">{job.job_type}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">训练框架:</dt>
                <dd className="font-medium">{job.framework}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">项目ID:</dt>
                <dd className="font-medium">{job.project_id}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">创建者ID:</dt>
                <dd className="font-medium">{job.creator_id}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">创建时间:</dt>
                <dd className="font-medium">{formatDate(job.created_at)}</dd>
              </div>
              {job.description && (
                <div>
                  <dt className="text-gray-500 mb-1">描述:</dt>
                  <dd className="text-sm">{job.description}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* 执行状态 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">执行状态</h2>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-gray-500">当前状态:</dt>
                <dd>
                  <span className={getStatusBadgeClass(job.status)}>{job.status}</span>
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">排队时间:</dt>
                <dd className="font-medium">{formatDate(job.queued_at)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">开始时间:</dt>
                <dd className="font-medium">{formatDate(job.started_at)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">完成时间:</dt>
                <dd className="font-medium">{formatDate(job.completed_at)}</dd>
              </div>
              {status?.duration_seconds && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">执行时长:</dt>
                  <dd className="font-medium">{Math.floor(status.duration_seconds / 60)}分钟</dd>
                </div>
              )}
              {job.error_message && (
                <div>
                  <dt className="text-red-500 mb-1">错误信息:</dt>
                  <dd className="text-sm text-red-600 bg-red-50 p-2 rounded">
                    {job.error_message}
                  </dd>
                </div>
              )}
            </dl>
          </div>

          {/* K8s信息 */}
          {job.k8s_job_name && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Kubernetes信息</h2>
              <dl className="space-y-3">
                <div className="flex justify-between">
                  <dt className="text-gray-500">命名空间:</dt>
                  <dd className="font-medium font-mono text-sm">{job.k8s_namespace}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Job名称:</dt>
                  <dd className="font-medium font-mono text-sm">{job.k8s_job_name}</dd>
                </div>
                {job.k8s_pod_names && job.k8s_pod_names.length > 0 && (
                  <div>
                    <dt className="text-gray-500 mb-2">Pod列表:</dt>
                    <dd className="space-y-1">
                      {job.k8s_pod_names.map((pod) => (
                        <div key={pod} className="font-mono text-sm bg-gray-50 p-2 rounded">
                          {pod}
                        </div>
                      ))}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          )}

          {/* 资源配置 */}
          {job.config && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">资源配置</h2>
              <dl className="space-y-3">
                <div className="flex justify-between">
                  <dt className="text-gray-500">节点数:</dt>
                  <dd className="font-medium">{job.config.node_count}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">每节点GPU:</dt>
                  <dd className="font-medium">{job.config.gpu_per_node}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">每节点CPU:</dt>
                  <dd className="font-medium">{job.config.cpu_per_node} cores</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">每节点内存:</dt>
                  <dd className="font-medium">{job.config.memory_per_node_gb} GB</dd>
                </div>
                {job.config.gpu_type && (
                  <div className="flex justify-between">
                    <dt className="text-gray-500">GPU型号:</dt>
                    <dd className="font-medium">{job.config.gpu_type}</dd>
                  </div>
                )}
                <div>
                  <dt className="text-gray-500 mb-1">Docker镜像:</dt>
                  <dd className="font-mono text-sm bg-gray-50 p-2 rounded break-all">
                    {job.config.docker_image}
                  </dd>
                </div>
              </dl>
            </div>
          )}
        </div>
      )}

      {/* 训练指标标签 */}
      {activeTab === 'metrics' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">训练指标</h2>
          {metrics.length === 0 ? (
            <p className="text-gray-500 text-center py-8">暂无指标数据</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Step</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Epoch</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Loss</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Accuracy</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">LR</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">时间</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {metrics.map((m) => (
                    <tr key={m.id}>
                      <td className="px-4 py-2 text-sm">{m.step}</td>
                      <td className="px-4 py-2 text-sm">{m.epoch ?? '-'}</td>
                      <td className="px-4 py-2 text-sm">{m.loss?.toFixed(4) ?? '-'}</td>
                      <td className="px-4 py-2 text-sm">{m.accuracy?.toFixed(4) ?? '-'}</td>
                      <td className="px-4 py-2 text-sm">{m.learning_rate?.toExponential(2) ?? '-'}</td>
                      <td className="px-4 py-2 text-sm text-gray-500">{formatDate(m.timestamp)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* 日志标签 */}
      {activeTab === 'logs' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">训练日志</h2>
          {Object.keys(logs).length === 0 ? (
            <p className="text-gray-500 text-center py-8">暂无日志数据</p>
          ) : (
            <div className="space-y-4">
              {Object.entries(logs).map(([podName, logContent]) => (
                <div key={podName}>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Pod: {podName}</h3>
                  <pre className="bg-gray-900 text-gray-100 p-4 rounded text-xs overflow-x-auto">
                    {logContent}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 检查点标签 */}
      {activeTab === 'checkpoints' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">训练检查点</h2>
          {checkpoints.length === 0 ? (
            <p className="text-gray-500 text-center py-8">暂无检查点</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Step</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">Epoch</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">存储类型</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">大小</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">路径</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500">创建时间</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {checkpoints.map((cp) => (
                    <tr key={cp.id}>
                      <td className="px-4 py-2 text-sm font-medium">{cp.step}</td>
                      <td className="px-4 py-2 text-sm">{cp.epoch ?? '-'}</td>
                      <td className="px-4 py-2">
                        <span className="px-2 py-1 rounded text-xs bg-blue-100 text-blue-800">
                          {cp.storage_type}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-sm">{formatBytes(cp.size_bytes)}</td>
                      <td className="px-4 py-2 text-sm font-mono text-gray-600 max-w-xs truncate">
                        {cp.storage_path}
                      </td>
                      <td className="px-4 py-2 text-sm text-gray-500">{formatDate(cp.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
