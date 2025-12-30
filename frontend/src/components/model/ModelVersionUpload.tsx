/**
 * 模型版本上传组件
 */

import React, { useState } from 'react';
import { Upload, X, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import { useCreateModelVersion } from '@/hooks/useModels';
import type { ModelVersionCreateRequest } from '@/types/model';
import { formatFileSize, validateVersion } from '@/utils/model';

interface ModelVersionUploadProps {
  modelId: number;
  onClose: () => void;
  onSuccess: () => void;
}

export const ModelVersionUpload: React.FC<ModelVersionUploadProps> = ({
  modelId,
  onClose,
  onSuccess,
}) => {
  // 表单状态
  const [formData, setFormData] = useState<ModelVersionCreateRequest>({
    version: '',
    description: '',
    model_format: '',
    model_architecture: '',
  });

  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const createVersionMutation = useCreateModelVersion();

  // 处理文件选择
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setErrors((prev) => ({ ...prev, file: '' }));
    }
  };

  // 处理拖拽
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setErrors((prev) => ({ ...prev, file: '' }));
    }
  };

  // 表单字段变化
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: '' }));
  };

  // 表单验证
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.version) {
      newErrors.version = '版本号不能为空';
    } else if (!validateVersion(formData.version)) {
      newErrors.version = '版本号格式不正确(例: v1.0.0, 1.0.0)';
    }

    if (!file) {
      newErrors.file = '请选择要上传的文件';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 提交表单
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm() || !file) return;

    try {
      await createVersionMutation.mutateAsync({
        modelId,
        file,
        data: formData,
      });

      onSuccess();
    } catch (error: any) {
      alert(`上传失败: ${error.response?.data?.detail || error.message}`);
    }
  };

  const isUploading = createVersionMutation.isPending;
  const uploadProgress = 0; // 实际应该从上传进度获取

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* 头部 */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-2xl font-semibold text-gray-800">上传模型版本</h2>
          <button
            onClick={onClose}
            disabled={isUploading}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* 表单内容 */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* 版本号 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              版本号 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="version"
              value={formData.version}
              onChange={handleChange}
              placeholder="例: v1.0.0 或 1.0.0"
              disabled={isUploading}
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 ${
                errors.version ? 'border-red-500' : 'border-gray-300'
              }`}
            />
            {errors.version && (
              <p className="mt-1 text-sm text-red-600">{errors.version}</p>
            )}
          </div>

          {/* 描述 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              版本描述
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={3}
              placeholder="描述此版本的主要变更和特性..."
              disabled={isUploading}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
            />
          </div>

          {/* 模型格式 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                模型格式
              </label>
              <input
                type="text"
                name="model_format"
                value={formData.model_format}
                onChange={handleChange}
                placeholder="例: pth, ckpt, pb, onnx"
                disabled={isUploading}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                模型架构
              </label>
              <input
                type="text"
                name="model_architecture"
                value={formData.model_architecture}
                onChange={handleChange}
                placeholder="例: ResNet50, BERT-base"
                disabled={isUploading}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              />
            </div>
          </div>

          {/* 文件上传区域 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              模型文件 <span className="text-red-500">*</span>
            </label>

            {!file ? (
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-8 text-center ${
                  dragActive
                    ? 'border-blue-500 bg-blue-50'
                    : errors.file
                    ? 'border-red-500'
                    : 'border-gray-300'
                } ${isUploading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
              >
                <input
                  type="file"
                  onChange={handleFileChange}
                  disabled={isUploading}
                  className="hidden"
                  id="file-upload"
                  accept=".pth,.pt,.ckpt,.pb,.onnx,.h5,.pkl,.safetensors"
                />
                <label
                  htmlFor="file-upload"
                  className={`flex flex-col items-center ${
                    isUploading ? 'cursor-not-allowed' : 'cursor-pointer'
                  }`}
                >
                  <Upload
                    className={`w-12 h-12 mb-3 ${
                      dragActive ? 'text-blue-600' : 'text-gray-400'
                    }`}
                  />
                  <p className="text-sm text-gray-600 mb-1">
                    点击选择文件或拖拽文件到此处
                  </p>
                  <p className="text-xs text-gray-500">
                    支持 .pth, .pt, .ckpt, .pb, .onnx, .h5, .pkl, .safetensors
                  </p>
                </label>
              </div>
            ) : (
              <div className="border border-gray-300 rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <FileText className="w-8 h-8 text-blue-600" />
                  <div>
                    <p className="text-sm font-medium text-gray-800">{file.name}</p>
                    <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                {!isUploading && (
                  <button
                    type="button"
                    onClick={() => {
                      setFile(null);
                      setErrors((prev) => ({ ...prev, file: '' }));
                    }}
                    className="text-red-600 hover:text-red-800"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>
            )}

            {errors.file && (
              <p className="mt-1 text-sm text-red-600 flex items-center">
                <AlertCircle className="w-4 h-4 mr-1" />
                {errors.file}
              </p>
            )}
          </div>

          {/* 上传进度 */}
          {isUploading && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center mb-2">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-3"></div>
                <span className="text-sm font-medium text-blue-800">
                  正在上传... {uploadProgress}%
                </span>
              </div>
              <div className="w-full bg-blue-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}

          {/* 提示信息 */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start">
              <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 mr-3 flex-shrink-0" />
              <div className="text-sm text-yellow-800">
                <p className="font-medium mb-1">上传注意事项:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>文件上传可能需要较长时间,请耐心等待</li>
                  <li>上传过程中请勿关闭浏览器或刷新页面</li>
                  <li>建议使用稳定的网络连接</li>
                  <li>大文件建议分批上传或使用压缩格式</li>
                </ul>
              </div>
            </div>
          </div>

          {/* 按钮组 */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              disabled={isUploading}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={isUploading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {isUploading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>上传中...</span>
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  <span>开始上传</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ModelVersionUpload;
