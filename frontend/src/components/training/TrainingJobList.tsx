/**
 * 训练任务列表组件
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Play, Square, Trash2, RefreshCw, Eye } from 'lucide-react';
import { useTrainingJobs, useStartTrainingJob, useStopTrainingJob, useDeleteTrainingJob } from '../../hooks/useTrainingJobs';
import { TrainingJobStatus, type TrainingJobQueryParams } from '../../types/training';
import {
  statusColors,
  statusLabels,
  isJobActive,
  formatTimestamp,
  formatDuration,
  frameworkLabels,
  jobTypeLabels,
} from '../../utils/training';

export function TrainingJobList() {
  const [queryParams, setQueryParams] = useState<TrainingJobQueryParams>({
    page: 1,
    page_size: 20,
  });

  const { data, isLoading, error, refetch } = useTrainingJobs(queryParams);
  const startJobMutation = useStartTrainingJob();
  const stopJobMutation = useStopTrainingJob();
  const deleteJobMutation = useDeleteTrainingJob();

  // 处理启动任务
  const handleStart = async (jobId: number) => {
    if (!confirm('确定要启动此训练任务吗?')) return;
    try {
      await startJobMutation.mutateAsync(jobId);
      alert('任务启动成功');
    } catch (error: any) {
      alert(`启动失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 处理停止任务
  const handleStop = async (jobId: number) => {
    if (!confirm('确定要停止此训练任务吗?')) return;
    try {
      await stopJobMutation.mutateAsync(jobId);
      alert('任务已停止');
    } catch (error: any) {
      alert(`停止失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 处理删除任务
  const handleDelete = async (jobId: number) => {
    if (!confirm('确定要删除此训练任务吗?')) return;
    try {
      await deleteJobMutation.mutateAsync({ jobId });
      alert('任务已删除');
    } catch (error: any) {
      alert(`删除失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 处理状态过滤
  const handleStatusFilter = (status: string | undefined) => {
    setQueryParams((prev) => ({ ...prev, status_filter: status, page: 1 }));
  };

  // 处理分页
  const handlePageChange = (page: number) => {
    setQueryParams((prev) => ({ ...prev, page }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-gray-600">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg text-red-600">加载失败: {(error as Error).message}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 头部操作栏 */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">训练任务</h1>
        <div className="flex items-center gap-4">
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4" />
            刷新
          </button>
          <Link
            to="/training/new"
            className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            创建任务
          </Link>
        </div>
      </div>

      {/* 状态过滤 */}
      <div className="flex gap-2">
        <button
          onClick={() => handleStatusFilter(undefined)}
          className={`px-4 py-2 rounded-lg ${
            !queryParams.status_filter
              ? 'bg-blue-100 text-blue-800'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          全部
        </button>
        {Object.values(TrainingJobStatus).map((status) => (
          <button
            key={status}
            onClick={() => handleStatusFilter(status)}
            className={`px-4 py-2 rounded-lg ${
              queryParams.status_filter === status
                ? statusColors[status]
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {statusLabels[status]}
          </button>
        ))}
      </div>

      {/* 任务列表 */}
      <div className="overflow-hidden bg-white border border-gray-200 rounded-lg shadow">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                任务名称
              </th>
              <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                状态
              </th>
              <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                框架
              </th>
              <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                类型
              </th>
              <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                创建时间
              </th>
              <th className="px-6 py-3 text-xs font-medium tracking-wider text-left text-gray-500 uppercase">
                运行时长
              </th>
              <th className="px-6 py-3 text-xs font-medium tracking-wider text-right text-gray-500 uppercase">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {data?.items.map((job) => (
              <tr key={job.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <Link
                    to={`/training/${job.id}`}
                    className="text-sm font-medium text-blue-600 hover:text-blue-800"
                  >
                    {job.name}
                  </Link>
                  {job.description && (
                    <p className="text-sm text-gray-500">{job.description}</p>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      statusColors[job.status]
                    }`}
                  >
                    {statusLabels[job.status]}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-900 whitespace-nowrap">
                  {frameworkLabels[job.framework]}
                </td>
                <td className="px-6 py-4 text-sm text-gray-900 whitespace-nowrap">
                  {jobTypeLabels[job.job_type]}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500 whitespace-nowrap">
                  {formatTimestamp(job.created_at)}
                </td>
                <td className="px-6 py-4 text-sm text-gray-500 whitespace-nowrap">
                  {job.started_at && job.completed_at
                    ? formatDuration(
                        Math.floor(
                          (new Date(job.completed_at).getTime() -
                            new Date(job.started_at).getTime()) /
                            1000
                        )
                      )
                    : '-'}
                </td>
                <td className="px-6 py-4 text-sm font-medium text-right whitespace-nowrap">
                  <div className="flex justify-end gap-2">
                    <Link
                      to={`/training/${job.id}`}
                      className="text-blue-600 hover:text-blue-900"
                      title="查看详情"
                    >
                      <Eye className="w-4 h-4" />
                    </Link>
                    {job.status === TrainingJobStatus.PENDING && (
                      <button
                        onClick={() => handleStart(job.id)}
                        className="text-green-600 hover:text-green-900"
                        disabled={startJobMutation.isPending}
                        title="启动任务"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                    )}
                    {isJobActive(job.status) && job.status !== TrainingJobStatus.PENDING && (
                      <button
                        onClick={() => handleStop(job.id)}
                        className="text-orange-600 hover:text-orange-900"
                        disabled={stopJobMutation.isPending}
                        title="停止任务"
                      >
                        <Square className="w-4 h-4" />
                      </button>
                    )}
                    {!isJobActive(job.status) && (
                      <button
                        onClick={() => handleDelete(job.id)}
                        className="text-red-600 hover:text-red-900"
                        disabled={deleteJobMutation.isPending}
                        title="删除任务"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* 分页 */}
        {data && data.total > 0 && (
          <div className="flex items-center justify-between px-6 py-3 bg-gray-50">
            <div className="text-sm text-gray-700">
              共 {data.total} 条记录,第 {data.page} / {Math.ceil(data.total / data.page_size)}{' '}
              页
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => handlePageChange(data.page - 1)}
                disabled={data.page <= 1}
                className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50 hover:bg-gray-100"
              >
                上一页
              </button>
              <button
                onClick={() => handlePageChange(data.page + 1)}
                disabled={data.page >= Math.ceil(data.total / data.page_size)}
                className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50 hover:bg-gray-100"
              >
                下一页
              </button>
            </div>
          </div>
        )}

        {data?.items.length === 0 && (
          <div className="py-12 text-center text-gray-500">暂无训练任务</div>
        )}
      </div>
    </div>
  );
}
