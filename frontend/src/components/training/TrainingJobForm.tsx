/**
 * 训练任务创建/编辑表单组件
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import trainingApi from '../../api/training';
import { TrainingJobType, FrameworkType } from '../../types/training';
import type { TrainingJobCreateRequest } from '../../types/training';

export default function TrainingJobForm() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 表单状态
  const [formData, setFormData] = useState<TrainingJobCreateRequest>({
    name: '',
    description: '',
    job_type: TrainingJobType.SINGLE_NODE,
    framework: FrameworkType.PYTORCH,
    project_id: 1, // TODO: 从上下文获取
    config: {
      node_count: 1,
      gpu_per_node: 1,
      cpu_per_node: 8,
      memory_per_node_gb: 32,
      gpu_type: 'p4d.24xlarge',
      docker_image: 'pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime',
      command: ['python', 'train.py'],
      args: [],
      env_vars: {},
      dataset_path: '/mnt/dataset',
      checkpoint_path: '',
      output_path: '/mnt/output',
      hyperparameters: {},
      distributed_config: {},
      timeout_seconds: 86400,
      max_retries: 0,
    },
  });

  // 处理表单提交
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const job = await trainingApi.createJob(formData);
      navigate(`/training/${job.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || '创建任务失败');
      console.error('Failed to create job:', err);
    } finally {
      setSubmitting(false);
    }
  };

  // 更新表单字段
  const updateField = (field: keyof TrainingJobCreateRequest, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  // 更新配置字段
  const updateConfigField = (field: string, value: any) => {
    setFormData((prev) => ({
      ...prev,
      config: { ...prev.config, [field]: value },
    }));
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* 标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">创建训练任务</h1>
          <p className="text-gray-600 mt-2">配置并提交新的训练任务</p>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* 表单 */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 基本信息 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">基本信息</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  任务名称 *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => updateField('name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: bert-training-v1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  任务描述
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => updateField('description', e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="简要描述训练任务目标和配置..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    任务类型 *
                  </label>
                  <select
                    required
                    value={formData.job_type}
                    onChange={(e) => updateField('job_type', e.target.value as TrainingJobType)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={TrainingJobType.SINGLE_NODE}>单节点训练</option>
                    <option value={TrainingJobType.DATA_PARALLEL}>数据并行</option>
                    <option value={TrainingJobType.MODEL_PARALLEL}>模型并行</option>
                    <option value={TrainingJobType.HYBRID_PARALLEL}>混合并行</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    训练框架 *
                  </label>
                  <select
                    required
                    value={formData.framework}
                    onChange={(e) => updateField('framework', e.target.value as FrameworkType)}
                    className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={FrameworkType.PYTORCH}>PyTorch</option>
                    <option value={FrameworkType.TENSORFLOW}>TensorFlow</option>
                    <option value={FrameworkType.JFLUX}>JFlux</option>
                    <option value={FrameworkType.DEEPSPEED}>DeepSpeed</option>
                    <option value={FrameworkType.MEGATRON}>Megatron</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* 资源配置 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">资源配置</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  节点数量 *
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  max="100"
                  value={formData.config.node_count}
                  onChange={(e) => updateConfigField('node_count', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  每节点GPU数 *
                </label>
                <input
                  type="number"
                  required
                  min="0"
                  max="8"
                  value={formData.config.gpu_per_node}
                  onChange={(e) => updateConfigField('gpu_per_node', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  每节点CPU核心数 *
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  max="64"
                  value={formData.config.cpu_per_node}
                  onChange={(e) => updateConfigField('cpu_per_node', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  每节点内存(GB) *
                </label>
                <input
                  type="number"
                  required
                  min="1"
                  max="512"
                  value={formData.config.memory_per_node_gb}
                  onChange={(e) => updateConfigField('memory_per_node_gb', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  GPU实例类型
                </label>
                <input
                  type="text"
                  value={formData.config.gpu_type}
                  onChange={(e) => updateConfigField('gpu_type', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: p4d.24xlarge"
                />
              </div>
            </div>
          </div>

          {/* 容器配置 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">容器配置</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Docker镜像 *
                </label>
                <input
                  type="text"
                  required
                  value={formData.config.docker_image}
                  onChange={(e) => updateConfigField('docker_image', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  执行命令 *
                </label>
                <input
                  type="text"
                  required
                  value={formData.config.command.join(' ')}
                  onChange={(e) => updateConfigField('command', e.target.value.split(' '))}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: python train.py"
                />
                <p className="text-xs text-gray-500 mt-1">用空格分隔多个参数</p>
              </div>
            </div>
          </div>

          {/* 数据配置 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">数据配置</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  数据集路径
                </label>
                <input
                  type="text"
                  value={formData.config.dataset_path}
                  onChange={(e) => updateConfigField('dataset_path', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="/mnt/dataset"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  检查点路径(恢复训练)
                </label>
                <input
                  type="text"
                  value={formData.config.checkpoint_path}
                  onChange={(e) => updateConfigField('checkpoint_path', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="留空表示从头开始训练"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  输出路径 *
                </label>
                <input
                  type="text"
                  required
                  value={formData.config.output_path}
                  onChange={(e) => updateConfigField('output_path', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="/mnt/output"
                />
              </div>
            </div>
          </div>

          {/* 执行配置 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">执行配置</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  超时时间(秒)
                </label>
                <input
                  type="number"
                  min="60"
                  max="604800"
                  value={formData.config.timeout_seconds || ''}
                  onChange={(e) => updateConfigField('timeout_seconds', e.target.value ? Number(e.target.value) : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="86400 (1天)"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  最大重试次数
                </label>
                <input
                  type="number"
                  min="0"
                  max="5"
                  value={formData.config.max_retries}
                  onChange={(e) => updateConfigField('max_retries', Number(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="flex justify-end gap-4">
            <button
              type="button"
              onClick={() => navigate('/training')}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded hover:bg-gray-50"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? '创建中...' : '创建任务'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
