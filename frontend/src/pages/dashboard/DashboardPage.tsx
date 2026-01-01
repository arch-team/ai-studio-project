/**
 * 仪表盘页面
 */

import React from 'react';
import { Link } from 'react-router-dom';

const DashboardPage: React.FC = () => {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900">仪表盘</h1>
        <p className="mt-2 text-sm text-gray-700">
          欢迎使用AI训练平台
        </p>
      </div>

      {/* 快速操作卡片 */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <Link
          to="/training-jobs/create"
          className="block p-6 bg-white rounded-lg border border-gray-200 shadow-md hover:bg-gray-50"
        >
          <h5 className="mb-2 text-xl font-bold tracking-tight text-gray-900">
            创建训练任务
          </h5>
          <p className="font-normal text-gray-700">
            提交新的分布式训练任务
          </p>
        </Link>

        <Link
          to="/training-jobs"
          className="block p-6 bg-white rounded-lg border border-gray-200 shadow-md hover:bg-gray-50"
        >
          <h5 className="mb-2 text-xl font-bold tracking-tight text-gray-900">
            查看训练任务
          </h5>
          <p className="font-normal text-gray-700">
            监控和管理训练任务
          </p>
        </Link>

        <div className="block p-6 bg-white rounded-lg border border-gray-200 shadow-md">
          <h5 className="mb-2 text-xl font-bold tracking-tight text-gray-900">
            系统状态
          </h5>
          <p className="font-normal text-gray-700">
            集群健康 | 0个运行中的任务
          </p>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
