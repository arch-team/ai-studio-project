/**
 * 创建训练任务页面
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';

const CreateTrainingJobPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">创建训练任务</h1>
      </div>

      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <p className="text-gray-600">创建训练任务表单 (待实现)</p>
          <button
            onClick={() => navigate('/training-jobs')}
            className="mt-4 inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            返回列表
          </button>
        </div>
      </div>
    </div>
  );
};

export default CreateTrainingJobPage;
