/**
 * 训练任务详情和监控组件
 */

import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Play, Square, Trash2, RefreshCw, Activity } from 'lucide-react';
import {
  useTrainingJob,
  useTrainingJobStatus,
  useStartTrainingJob,
  useStopTrainingJob,
  useDeleteTrainingJob,
  useSyncTrainingJobStatus,
} from '../../hooks/useTrainingJobs';
import {
  statusColors,
  statusLabels,
  isJobActive,
  formatTimestamp,
  formatDuration,
  calculateTotalResources,
  frameworkLabels,
  jobTypeLabels,
} from '../../utils/training';

export function TrainingJobDetail() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();

  const { data: job, isLoading, error } = useTrainingJob(Number(jobId));
  const { data: status, refetch: refetchStatus } = useTrainingJobStatus(
    Number(jobId),
    !!job && isJobActive(job.status)
  );

  const startJobMutation = useStartTrainingJob();
  const stopJobMutation = useStopTrainingJob();
  const deleteJobMutation = useDeleteTrainingJob();
  const syncStatusMutation = useSyncTrainingJobStatus();

  // 处理启动
  const handleStart = async () => {
    if (!jobId || !confirm('确定要启动此训练任务吗?')) return;
    try {
      await startJobMutation.mutateAsync(Number(jobId));
      alert('任务启动成功');
    } catch (error: any) {
      alert(`启动失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 处理停止
  const handleStop = async () => {
    if (!jobId || !confirm('确定要停止此训练任务吗?')) return;
    try {
      await stopJobMutation.mutateAsync(Number(jobId));
      alert('任务已停止');
    } catch (error: any) {
      alert(`停止失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 处理删除
  const handleDelete = async () => {
    if (!jobId || !confirm('确定要删除此训练任务吗?')) return;
    try {
      await deleteJobMutation.mutateAsync({ jobId: Number(jobId) });
      alert('任务已删除');
      navigate('/training');
    } catch (error: any) {
      alert(`删除失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 处理同步状态
  const handleSync = async () => {
    if (!jobId) return;
    try {
      await syncStatusMutation.mutateAsync(Number(jobId));
      await refetchStatus();
    } catch (error: any) {
      alert(`同步失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">加载中...</div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-red-600">加载失败或任务不存在</div>
      </div>
    );
  }

  const totalResources = job.config ? calculateTotalResources(job.config) : null;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* 头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate('/training')} className="p-2 text-gray-600 hover:text-gray-900">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{job.name}</h1>
            {job.description && <p className="text-gray-600">{job.description}</p>}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSync}
            disabled={syncStatusMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4" />
            同步状态
          </button>
          {job.status === 'PENDING' && (
            <button
              onClick={handleStart}
              disabled={startJobMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 text-white bg-green-600 rounded-lg hover:bg-green-700"
            >
              <Play className="w-4 h-4" />
              启动任务
            </button>
          )}
          {isJobActive(job.status) && job.status !== 'PENDING' && (
            <button
              onClick={handleStop}
              disabled={stopJobMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 text-white bg-orange-600 rounded-lg hover:bg-orange-700"
            >
              <Square className="w-4 h-4" />
              停止任务
            </button>
          )}
          {!isJobActive(job.status) && (
            <button
              onClick={handleDelete}
              disabled={deleteJobMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 text-white bg-red-600 rounded-lg hover:bg-red-700"
            >
              <Trash2 className="w-4 h-4" />
              删除任务
            </button>
          )}
        </div>
      </div>

      {/* 状态卡片 */}
      <div className="grid grid-cols-4 gap-4">
        <div className="p-4 bg-white border border-gray-200 rounded-lg shadow">
          <div className="text-sm text-gray-600">状态</div>
          <div className="mt-2">
            <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${statusColors[job.status]}`}>
              {statusLabels[job.status]}
            </span>
          </div>
        </div>

        <div className="p-4 bg-white border border-gray-200 rounded-lg shadow">
          <div className="text-sm text-gray-600">框架</div>
          <div className="mt-2 text-lg font-semibold text-gray-900">{frameworkLabels[job.framework]}</div>
        </div>

        <div className="p-4 bg-white border border-gray-200 rounded-lg shadow">
          <div className="text-sm text-gray-600">类型</div>
          <div className="mt-2 text-lg font-semibold text-gray-900">{jobTypeLabels[job.job_type]}</div>
        </div>

        <div className="p-4 bg-white border border-gray-200 rounded-lg shadow">
          <div className="text-sm text-gray-600">运行时长</div>
          <div className="mt-2 text-lg font-semibold text-gray-900">
            {status?.duration_seconds !== null && status?.duration_seconds !== undefined
              ? formatDuration(status.duration_seconds)
              : '-'}
          </div>
        </div>
      </div>

      {/* 实时状态(仅运行中任务) */}
      {status && isJobActive(job.status) && (
        <div className="p-6 bg-white border border-gray-200 rounded-lg shadow">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-green-600" />
            <h2 className="text-lg font-semibold text-gray-900">实时状态</h2>
          </div>

          {status.k8s_status && (
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <div className="text-sm text-gray-600">活跃Pod</div>
                <div className="text-2xl font-bold text-green-600">{status.k8s_status.active}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">成功Pod</div>
                <div className="text-2xl font-bold text-emerald-600">{status.k8s_status.succeeded}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">失败Pod</div>
                <div className="text-2xl font-bold text-red-600">{status.k8s_status.failed}</div>
              </div>
            </div>
          )}

          {status.pods && status.pods.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-medium text-gray-700">Pod列表</h3>
              <div className="space-y-2">
                {status.pods.map((pod) => (
                  <div key={pod.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="font-mono text-sm text-gray-900">{pod.name}</div>
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-gray-600">{pod.phase}</span>
                      <span className="text-xs text-gray-500">{formatTimestamp(pod.start_time)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 资源配置 */}
      {job.config && (
        <div className="p-6 bg-white border border-gray-200 rounded-lg shadow">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">资源配置</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-600">节点数量</div>
              <div className="text-lg font-semibold text-gray-900">{job.config.node_count}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">GPU总数</div>
              <div className="text-lg font-semibold text-gray-900">{totalResources?.totalGpus || 0}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">CPU总核心数</div>
              <div className="text-lg font-semibold text-gray-900">{totalResources?.totalCpus || 0}</div>
            </div>
            <div>
              <div className="text-sm text-gray-600">内存总量</div>
              <div className="text-lg font-semibold text-gray-900">{totalResources?.totalMemoryGb || 0} GB</div>
            </div>
            {job.config.gpu_type && (
              <div className="col-span-2">
                <div className="text-sm text-gray-600">GPU型号</div>
                <div className="text-lg font-semibold text-gray-900">{job.config.gpu_type}</div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 容器配置 */}
      {job.config && (
        <div className="p-6 bg-white border border-gray-200 rounded-lg shadow">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">容器配置</h2>
          <div className="space-y-4">
            <div>
              <div className="mb-1 text-sm text-gray-600">Docker镜像</div>
              <div className="font-mono text-sm text-gray-900">{job.config.docker_image}</div>
            </div>
            <div>
              <div className="mb-1 text-sm text-gray-600">执行命令</div>
              <div className="p-3 font-mono text-sm text-gray-900 bg-gray-50 rounded">
                {job.config.command.join(' ')}{' '}
                {job.config.args && job.config.args.length > 0 && job.config.args.join(' ')}
              </div>
            </div>
            {job.config.env_vars && Object.keys(job.config.env_vars).length > 0 && (
              <div>
                <div className="mb-1 text-sm text-gray-600">环境变量</div>
                <div className="p-3 font-mono text-sm text-gray-900 bg-gray-50 rounded">
                  {Object.entries(job.config.env_vars).map(([key, value]) => (
                    <div key={key}>
                      {key}={value}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 时间信息 */}
      <div className="p-6 bg-white border border-gray-200 rounded-lg shadow">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">时间信息</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-sm text-gray-600">创建时间</div>
            <div className="text-sm text-gray-900">{formatTimestamp(job.created_at)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">排队时间</div>
            <div className="text-sm text-gray-900">{formatTimestamp(job.queued_at)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">开始时间</div>
            <div className="text-sm text-gray-900">{formatTimestamp(job.started_at)}</div>
          </div>
          <div>
            <div className="text-sm text-gray-600">完成时间</div>
            <div className="text-sm text-gray-900">{formatTimestamp(job.completed_at)}</div>
          </div>
        </div>
      </div>

      {/* 错误信息 */}
      {job.error_message && (
        <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
          <h2 className="mb-2 text-lg font-semibold text-red-900">错误信息</h2>
          <div className="font-mono text-sm text-red-800">{job.error_message}</div>
        </div>
      )}
    </div>
  );
}
