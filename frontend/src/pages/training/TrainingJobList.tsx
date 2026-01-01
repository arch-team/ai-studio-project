/**
 * 训练任务列表页面
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import trainingApi from '../../api/training';
import type { TrainingJob, TrainingJobQueryParams } from '../../types/training';
import { TrainingJobStatus } from '../../types/training';

export default function TrainingJobList() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<TrainingJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [projectId, setProjectId] = useState<number | undefined>();

  // 加载训练任务列表
  const loadJobs = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: TrainingJobQueryParams = {
        page,
        page_size: pageSize,
      };

      if (statusFilter) {
        params.status_filter = statusFilter;
      }
      if (projectId) {
        params.project_id = projectId;
      }

      const response = await trainingApi.listJobs(params);
      setJobs(response.items);
      setTotal(response.total);
    } catch (err: any) {
      setError(err.response?.data?.detail || '加载训练任务列表失败');
      console.error('Failed to load training jobs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, [page, statusFilter, projectId]);

  // 状态徽章样式
  const getStatusBadgeClass = (status: TrainingJobStatus) => {
    const baseClass = 'px-2 py-1 rounded text-xs font-medium';
    switch (status) {
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

  // 计算执行时长
  const calculateDuration = (job: TrainingJob) => {
    if (!job.started_at) return '-';
    const start = new Date(job.started_at).getTime();
    const end = job.completed_at ? new Date(job.completed_at).getTime() : Date.now();
    const duration = Math.floor((end - start) / 1000);

    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    const seconds = duration % 60;

    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${seconds}s`;
    return `${seconds}s`;
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* 页面标题 */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">训练任务</h1>
        <button
          onClick={() => navigate('/training/new')}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
        >
          创建任务
        </button>
      </div>

      {/* 过滤器 */}
      <div className="bg-white rounded-lg shadow mb-6 p-4">
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              状态过滤
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">全部状态</option>
              <option value={TrainingJobStatus.PENDING}>等待中</option>
              <option value={TrainingJobStatus.QUEUED}>已排队</option>
              <option value={TrainingJobStatus.RUNNING}>运行中</option>
              <option value={TrainingJobStatus.COMPLETED}>已完成</option>
              <option value={TrainingJobStatus.FAILED}>失败</option>
              <option value={TrainingJobStatus.CANCELLED}>已取消</option>
            </select>
          </div>

          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              项目ID
            </label>
            <input
              type="number"
              value={projectId || ''}
              onChange={(e) => setProjectId(e.target.value ? Number(e.target.value) : undefined)}
              placeholder="输入项目ID过滤"
              className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={loadJobs}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition"
            >
              刷新
            </button>
          </div>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {/* 训练任务表格 */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-500">
            加载中...
          </div>
        ) : jobs.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            暂无训练任务
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  任务名称
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  类型/框架
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  创建时间
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  执行时长
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {jobs.map((job) => (
                <tr
                  key={job.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/training/${job.id}`)}
                >
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">{job.name}</div>
                    <div className="text-sm text-gray-500">ID: {job.id}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={getStatusBadgeClass(job.status)}>
                      {job.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    <div>{job.job_type}</div>
                    <div className="text-gray-500">{job.framework}</div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {formatDate(job.created_at)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {calculateDuration(job)}
                  </td>
                  <td className="px-6 py-4 text-right text-sm font-medium">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/training/${job.id}`);
                      }}
                      className="text-blue-600 hover:text-blue-900 mr-4"
                    >
                      查看
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* 分页 */}
        {!loading && total > 0 && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                上一页
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page * pageSize >= total}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                下一页
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  显示 <span className="font-medium">{(page - 1) * pageSize + 1}</span> 到{' '}
                  <span className="font-medium">{Math.min(page * pageSize, total)}</span> 条，共{' '}
                  <span className="font-medium">{total}</span> 条记录
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  上一页
                </button>
                <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white">
                  第 {page} 页
                </span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page * pageSize >= total}
                  className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
                >
                  下一页
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
