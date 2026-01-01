/**
 * 训练任务详情页面
 */

import React from 'react';
import { TrainingJobDetail } from '../../components/training/TrainingJobDetail';

const TrainingJobDetailPage: React.FC = () => {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">训练任务详情</h1>
      </div>
      <TrainingJobDetail />
    </div>
  );
};

export default TrainingJobDetailPage;
