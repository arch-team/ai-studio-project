/**
 * 模型列表组件
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Package,
  Plus,
  RefreshCw,
  Search,
  Filter,
  Trash2,
  Eye,
  Edit,
} from 'lucide-react';
import { useModels, useDeleteModel } from '@/hooks/useModels';
import type { ModelFramework, ModelQueryParams } from '@/types/model';
import {
  getStatusDisplay,
  getFrameworkDisplay,
  formatTimestamp,
  formatFileSize,
} from '@/utils/model';

export const ModelList: React.FC = () => {
  const navigate = useNavigate();

  // 查询参数状态
  const [queryParams, setQueryParams] = useState<ModelQueryParams>({
    page: 1,
    page_size: 20,
  });

  // 筛选条件状态
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFramework, setSelectedFramework] = useState<ModelFramework | ''>('');

  // 查询数据
  const { data, isLoading, error, refetch } = useModels(queryParams);
  const deleteModelMutation = useDeleteModel();

  // 处理搜索
  const handleSearch = () => {
    setQueryParams((prev) => ({
      ...prev,
      page: 1,
    }));
    refetch();
  };

  // 处理框架筛选
  const handleFrameworkFilter = (framework: ModelFramework | '') => {
    setSelectedFramework(framework);
    setQueryParams((prev) => ({
      ...prev,
      framework: framework || undefined,
      page: 1,
    }));
  };

  // 处理删除
  const handleDelete = async (modelId: number, modelName: string) => {
    if (!confirm(`确认删除模型 "${modelName}"?`)) return;

    try {
      await deleteModelMutation.mutateAsync({ modelId, force: false });
      alert('删除成功');
      refetch();
    } catch (error) {
      alert(`删除失败: ${error}`);
    }
  };

  // 处理分页
  const handlePageChange = (newPage: number) => {
    setQueryParams((prev) => ({ ...prev, page: newPage }));
  };

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <p className="text-red-600 mb-4">加载失败: {error.message}</p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  const totalPages = data ? Math.ceil(data.total / (queryParams.page_size || 20)) : 0;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* 头部 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Package className="w-8 h-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-800">模型管理</h1>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => refetch()}
            disabled={isLoading}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>刷新</span>
          </button>
          <button
            onClick={() => navigate('/models/create')}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-5 h-5" />
            <span>创建模型</span>
          </button>
        </div>
      </div>

      {/* 搜索和筛选栏 */}
      <div className="mb-6 flex items-center space-x-4">
        <div className="flex-1 flex items-center space-x-2">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="搜索模型名称..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={handleSearch}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            搜索
          </button>
        </div>

        <div className="flex items-center space-x-2">
          <Filter className="w-5 h-5 text-gray-500" />
          <select
            value={selectedFramework}
            onChange={(e) => handleFrameworkFilter(e.target.value as ModelFramework | '')}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">所有框架</option>
            <option value="PYTORCH">PyTorch</option>
            <option value="TENSORFLOW">TensorFlow</option>
            <option value="ONNX">ONNX</option>
            <option value="JFLUX">JFlux</option>
            <option value="HUGGINGFACE">HuggingFace</option>
            <option value="CUSTOM">自定义</option>
          </select>
        </div>
      </div>

      {/* 统计信息 */}
      <div className="mb-6 text-sm text-gray-600">
        共 <span className="font-semibold text-gray-800">{data?.total || 0}</span> 个模型
      </div>

      {/* 模型列表 */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : data?.items.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 bg-gray-50 rounded-lg">
          <Package className="w-16 h-16 text-gray-300 mb-4" />
          <p className="text-gray-500 text-lg mb-2">暂无模型</p>
          <button
            onClick={() => navigate('/models/create')}
            className="text-blue-600 hover:text-blue-700"
          >
            创建第一个模型
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  模型名称
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  框架
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  任务类型
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  最新版本
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  创建时间
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data?.items.map((model) => (
                <tr key={model.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {model.name}
                        </div>
                        {model.description && (
                          <div className="text-sm text-gray-500 truncate max-w-xs">
                            {model.description}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">
                      {getFrameworkDisplay(model.framework)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {model.task_type || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {model.latest_version || '无版本'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatTimestamp(model.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={() => navigate(`/models/${model.id}`)}
                        className="text-blue-600 hover:text-blue-900"
                        title="查看详情"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => navigate(`/models/${model.id}/edit`)}
                        className="text-yellow-600 hover:text-yellow-900"
                        title="编辑"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(model.id, model.name)}
                        className="text-red-600 hover:text-red-900"
                        title="删除"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 分页 */}
      {data && totalPages > 1 && (
        <div className="mt-6 flex items-center justify-between">
          <div className="text-sm text-gray-700">
            显示第 {(queryParams.page! - 1) * queryParams.page_size! + 1} 到{' '}
            {Math.min(queryParams.page! * queryParams.page_size!, data.total)} 条,共{' '}
            {data.total} 条
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => handlePageChange(queryParams.page! - 1)}
              disabled={queryParams.page === 1}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>
            <span className="px-4 py-2 border border-gray-300 rounded-lg bg-blue-50 text-blue-600">
              {queryParams.page} / {totalPages}
            </span>
            <button
              onClick={() => handlePageChange(queryParams.page! + 1)}
              disabled={queryParams.page === totalPages}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelList;
