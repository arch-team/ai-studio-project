/**
 * 模型创建表单组件
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Package, ArrowLeft, Save } from 'lucide-react';
import { useCreateModel } from '@/hooks/useModels';
import type { ModelCreateRequest, ModelFramework } from '@/types/model';
import { validateModelName, parseTags } from '@/utils/model';

export const ModelCreate: React.FC = () => {
  const navigate = useNavigate();
  const createModelMutation = useCreateModel();

  // 表单状态
  const [formData, setFormData] = useState<ModelCreateRequest>({
    name: '',
    description: '',
    framework: 'PYTORCH' as ModelFramework,
    task_type: '',
    project_id: 1, // 临时hardcode,实际应该从用户选择获取
    tags: [],
  });

  const [tagsInput, setTagsInput] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  // 处理基本字段变化
  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: '' }));
  };

  // 处理标签输入
  const handleTagsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTagsInput(e.target.value);
    const tags = parseTags(e.target.value);
    setFormData((prev) => ({ ...prev, tags }));
  };

  // 表单验证
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name) {
      newErrors.name = '模型名称不能为空';
    } else if (!validateModelName(formData.name)) {
      newErrors.name = '模型名称格式不正确(1-100字符,允许中英文、数字、下划线、中划线)';
    }

    if (!formData.framework) {
      newErrors.framework = '请选择模型框架';
    }

    if (!formData.project_id) {
      newErrors.project_id = '请选择所属项目';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 提交表单
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    try {
      const model = await createModelMutation.mutateAsync(formData);
      alert('创建成功');
      navigate(`/models/${model.id}`);
    } catch (error: any) {
      alert(`创建失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  const isSubmitting = createModelMutation.isPending;

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      {/* 头部 */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/models')}
          className="flex items-center space-x-2 text-gray-600 hover:text-gray-800 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>返回列表</span>
        </button>

        <div className="flex items-center space-x-3">
          <Package className="w-10 h-10 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-800">创建新模型</h1>
        </div>
      </div>

      {/* 表单 */}
      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow">
        {/* 基本信息部分 */}
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">基本信息</h2>

          <div className="space-y-4">
            {/* 模型名称 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                模型名称 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="输入模型名称"
                disabled={isSubmitting}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 ${
                  errors.name ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-600">{errors.name}</p>
              )}
            </div>

            {/* 描述 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                模型描述
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={3}
                placeholder="描述模型的用途、特点等..."
                disabled={isSubmitting}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              />
            </div>

            {/* 框架和任务类型 */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  模型框架 <span className="text-red-500">*</span>
                </label>
                <select
                  name="framework"
                  value={formData.framework}
                  onChange={handleChange}
                  disabled={isSubmitting}
                  className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 ${
                    errors.framework ? 'border-red-500' : 'border-gray-300'
                  }`}
                >
                  <option value="PYTORCH">PyTorch</option>
                  <option value="TENSORFLOW">TensorFlow</option>
                  <option value="ONNX">ONNX</option>
                  <option value="JFLUX">JFlux</option>
                  <option value="HUGGINGFACE">HuggingFace</option>
                  <option value="CUSTOM">自定义</option>
                </select>
                {errors.framework && (
                  <p className="mt-1 text-sm text-red-600">{errors.framework}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  任务类型
                </label>
                <input
                  type="text"
                  name="task_type"
                  value={formData.task_type}
                  onChange={handleChange}
                  placeholder="例: 图像分类、文本生成"
                  disabled={isSubmitting}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
                />
              </div>
            </div>

            {/* 标签 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                标签
              </label>
              <input
                type="text"
                value={tagsInput}
                onChange={handleTagsChange}
                placeholder="输入标签,用逗号分隔,例: cv, resnet, imagenet"
                disabled={isSubmitting}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              />
              {formData.tags && formData.tags.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {formData.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 关联信息部分 */}
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">关联信息</h2>

          <div className="space-y-4">
            {/* 所属项目 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                所属项目 <span className="text-red-500">*</span>
              </label>
              <select
                name="project_id"
                value={formData.project_id}
                onChange={handleChange}
                disabled={isSubmitting}
                className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 ${
                  errors.project_id ? 'border-red-500' : 'border-gray-300'
                }`}
              >
                <option value={1}>默认项目</option>
                {/* 实际应该从API获取项目列表 */}
              </select>
              {errors.project_id && (
                <p className="mt-1 text-sm text-red-600">{errors.project_id}</p>
              )}
            </div>

            {/* 来源训练任务 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                来源训练任务 (可选)
              </label>
              <input
                type="number"
                name="source_training_job_id"
                value={formData.source_training_job_id || ''}
                onChange={handleChange}
                placeholder="如果模型来自训练任务,输入任务ID"
                disabled={isSubmitting}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              />
              <p className="mt-1 text-xs text-gray-500">
                如果此模型是从训练任务产出的,可以关联任务ID以便追溯
              </p>
            </div>
          </div>
        </div>

        {/* 提示信息 */}
        <div className="p-6 bg-blue-50">
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-2">创建后的下一步:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>创建完成后可以立即上传模型版本</li>
              <li>支持多个版本管理,可以随时切换</li>
              <li>每个版本会自动计算MD5校验和</li>
              <li>可以为版本添加性能指标和超参数信息</li>
            </ul>
          </div>
        </div>

        {/* 按钮组 */}
        <div className="flex items-center justify-end space-x-3 px-6 py-4 bg-gray-50">
          <button
            type="button"
            onClick={() => navigate('/models')}
            disabled={isSubmitting}
            className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            取消
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>创建中...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>创建模型</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default ModelCreate;
