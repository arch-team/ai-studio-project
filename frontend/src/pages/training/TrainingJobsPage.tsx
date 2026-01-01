/**
 * 训练任务列表页面
 */

import React from 'react';
import TrainingJobList from './TrainingJobList';

const TrainingJobsPage: React.FC = () => {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">训练任务</h1>
      </div>
      <TrainingJobList />
    </div>
  );
};

export default TrainingJobsPage;
