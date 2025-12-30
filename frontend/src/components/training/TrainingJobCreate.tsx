/**
 * 训练任务创建组件
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useCreateTrainingJob } from '../../hooks/useTrainingJobs';
import { FrameworkType, TrainingJobType, type TrainingJobCreateRequest } from '../../types/training';
import { frameworkLabels, jobTypeLabels } from '../../utils/training';

export function TrainingJobCreate() {
  const navigate = useNavigate();
  const createJobMutation = useCreateTrainingJob();

  // 表单状态
  const [formData, setFormData] = useState<TrainingJobCreateRequest>({
    name: '',
    description: '',
    job_type: TrainingJobType.SINGLE_NODE,
    framework: FrameworkType.PYTORCH,
    project_id: 1, // TODO: 从项目上下文获取
    config: {
      node_count: 1,
      gpu_per_node: 1,
      cpu_per_node: 8,
      memory_per_node_gb: 32,
      docker_image: '',
      command: [],
      output_path: '',
    },
  });

  // 命令行输入(字符串形式)
  const [commandInput, setCommandInput] = useState('');
  const [argsInput, setArgsInput] = useState('');
  const [envVarsInput, setEnvVarsInput] = useState('');

  // 处理表单提交
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 验证必填字段
    if (!formData.name.trim()) {
      alert('请输入任务名称');
      return;
    }
    if (!formData.config.docker_image.trim()) {
      alert('请输入Docker镜像');
      return;
    }
    if (!commandInput.trim()) {
      alert('请输入执行命令');
      return;
    }
    if (!formData.config.output_path.trim()) {
      alert('请输入输出路径');
      return;
    }

    // 解析命令和参数
    const command = commandInput
      .split(' ')
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
    const args = argsInput
      ? argsInput
          .split(' ')
          .map((s) => s.trim())
          .filter((s) => s.length > 0)
      : undefined;

    // 解析环境变量
    let envVars: Record<string, string> | undefined;
    if (envVarsInput.trim()) {
      try {
        envVars = JSON.parse(envVarsInput);
      } catch {
        alert('环境变量格式错误,请使用JSON格式');
        return;
      }
    }

    // 构建提交数据
    const submitData: TrainingJobCreateRequest = {
      ...formData,
      config: {
        ...formData.config,
        command,
        args,
        env_vars: envVars,
      },
    };

    try {
      const job = await createJobMutation.mutateAsync(submitData);
      alert('任务创建成功!');
      navigate(`/training/${job.id}`);
    } catch (error: any) {
      alert(`创建失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 头部 */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/training')}
          className="p-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-2xl font-bold text-gray-900">创建训练任务</h1>
      </div>

      {/* 创建表单 */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 基本信息 */}
        <div className="p-6 bg-white border border-gray-200 rounded-lg shadow">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">基本信息</h2>
          <div className="space-y-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700">
                任务名称 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="输入任务名称"
                required
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700">任务描述</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="输入任务描述"
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700">
                  训练框架 <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.framework}
                  onChange={(e) =>
                    setFormData({ ...formData, framework: e.target.value as FrameworkType })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {Object.entries(frameworkLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block mb-2 text-sm font-medium text-gray-700">
                  任务类型 <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.job_type}
                  onChange={(e) =>
                    setFormData({ ...formData, job_type: e.target.value as TrainingJobType })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {Object.entries(jobTypeLabels).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* 资源配置 */}
        <div className="p-6 bg-white border border-gray-200 rounded-lg shadow">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">资源配置</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700">节点数量</label>
              <input
                type="number"
                value={formData.config.node_count}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    config: { ...formData.config, node_count: parseInt(e.target.value) },
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                min="1"
                max="100"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700">每节点GPU数</label>
              <input
                type="number"
                value={formData.config.gpu_per_node}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    config: { ...formData.config, gpu_per_node: parseInt(e.target.value) },
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                min="0"
                max="8"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700">
                每节点CPU核心数
              </label>
              <input
                type="number"
                value={formData.config.cpu_per_node}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    config: { ...formData.config, cpu_per_node: parseInt(e.target.value) },
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                min="1"
                max="64"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700">
                每节点内存(GB)
              </label>
              <input
                type="number"
                value={formData.config.memory_per_node_gb}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    config: {
                      ...formData.config,
                      memory_per_node_gb: parseInt(e.target.value),
                    },
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                min="1"
                max="512"
              />
            </div>

            <div className="col-span-2">
              <label className="block mb-2 text-sm font-medium text-gray-700">GPU型号</label>
              <input
                type="text"
                value={formData.config.gpu_type || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    config: { ...formData.config, gpu_type: e.target.value || undefined },
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="例如: nvidia-a100, nvidia-v100"
              />
            </div>
          </div>
        </div>

        {/* 容器配置 */}
        <div className="p-6 bg-white border border-gray-200 rounded-lg shadow">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">容器配置</h2>
          <div className="space-y-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700">
                Docker镜像 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.config.docker_image}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    config: { ...formData.config, docker_image: e.target.value },
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="例如: pytorch/pytorch:2.0.0-cuda11.7-cudnn8-runtime"
                required
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700">
                执行命令 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={commandInput}
                onChange={(e) => setCommandInput(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="例如: python train.py"
                required
              />
              <p className="mt-1 text-xs text-gray-500">命令以空格分隔</p>
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700">命令参数</label>
              <input
                type="text"
                value={argsInput}
                onChange={(e) => setArgsInput(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="例如: --batch-size 32 --epochs 100"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700">环境变量</label>
              <textarea
                value={envVarsInput}
                onChange={(e) => setEnvVarsInput(e.target.value)}
                className="w-full px-3 py-2 font-mono text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder='{"ENV_VAR": "value"}'
                rows={3}
              />
              <p className="mt-1 text-xs text-gray-500">JSON格式的键值对</p>
            </div>
          </div>
        </div>

        {/* 数据配置 */}
        <div className="p-6 bg-white border border-gray-200 rounded-lg shadow">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">数据配置</h2>
          <div className="space-y-4">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700">数据集路径</label>
              <input
                type="text"
                value={formData.config.dataset_path || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    config: { ...formData.config, dataset_path: e.target.value || undefined },
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="/data/datasets/imagenet"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700">检查点路径</label>
              <input
                type="text"
                value={formData.config.checkpoint_path || ''}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    config: {
                      ...formData.config,
                      checkpoint_path: e.target.value || undefined,
                    },
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="/data/checkpoints/model.pth"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-gray-700">
                输出路径 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.config.output_path}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    config: { ...formData.config, output_path: e.target.value },
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="/data/output/experiment-001"
                required
              />
            </div>
          </div>
        </div>

        {/* 提交按钮 */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/training')}
            className="px-6 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            取消
          </button>
          <button
            type="submit"
            disabled={createJobMutation.isPending}
            className="px-6 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {createJobMutation.isPending ? '创建中...' : '创建任务'}
          </button>
        </div>
      </form>
    </div>
  );
}
