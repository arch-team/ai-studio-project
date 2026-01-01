/**
 * 训练指标图表组件
 *
 * 实时展示训练过程中的指标变化,支持多指标展示和交互式图表
 */

import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Card } from '../shared/Card';

export interface MetricsData {
  step: number;
  epoch?: number;
  timestamp: string;
  metrics: Record<string, number>;
}

interface MetricsChartProps {
  data: MetricsData[];
  title?: string;
  selectedMetrics?: string[];
  height?: number;
  loading?: boolean;
}

// 预定义的指标颜色
const METRIC_COLORS: Record<string, string> = {
  loss: '#ef4444',
  accuracy: '#10b981',
  learning_rate: '#3b82f6',
  val_loss: '#f59e0b',
  val_accuracy: '#8b5cf6',
};

export const MetricsChart: React.FC<MetricsChartProps> = ({
  data,
  title = '训练指标',
  selectedMetrics,
  height = 400,
  loading = false,
}) => {
  // 处理数据格式:将嵌套的metrics展平
  const chartData = useMemo(() => {
    return data.map((item) => ({
      step: item.step,
      epoch: item.epoch,
      timestamp: item.timestamp,
      ...item.metrics,
    }));
  }, [data]);

  // 提取所有可用的指标名称
  const availableMetrics = useMemo(() => {
    if (data.length === 0) return [];
    const metricsSet = new Set<string>();
    data.forEach((item) => {
      Object.keys(item.metrics).forEach((key) => metricsSet.add(key));
    });
    return Array.from(metricsSet);
  }, [data]);

  // 确定要展示的指标
  const displayMetrics = useMemo(() => {
    if (selectedMetrics && selectedMetrics.length > 0) {
      return selectedMetrics.filter((m) => availableMetrics.includes(m));
    }
    return availableMetrics;
  }, [selectedMetrics, availableMetrics]);

  // 为每个指标分配颜色
  const getMetricColor = (metric: string, index: number): string => {
    return METRIC_COLORS[metric] || `hsl(${(index * 137.5) % 360}, 70%, 50%)`;
  };

  if (loading) {
    return (
      <Card>
        <div className="p-8 text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">加载指标数据...</p>
        </div>
      </Card>
    );
  }

  if (data.length === 0) {
    return (
      <Card>
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <div className="p-8 text-center text-gray-500">
          暂无指标数据
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <h3 className="text-lg font-semibold mb-4">{title}</h3>

      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="step"
            label={{ value: '训练步数', position: 'insideBottom', offset: -5 }}
            stroke="#6b7280"
          />
          <YAxis
            label={{ value: '指标值', angle: -90, position: 'insideLeft' }}
            stroke="#6b7280"
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '0.5rem',
            }}
            formatter={(value: number) => value.toFixed(4)}
          />
          <Legend />

          {displayMetrics.map((metric, index) => (
            <Line
              key={metric}
              type="monotone"
              dataKey={metric}
              stroke={getMetricColor(metric, index)}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
              name={metric}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {displayMetrics.length === 0 && (
        <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            未选择任何指标。可用指标: {availableMetrics.join(', ')}
          </p>
        </div>
      )}
    </Card>
  );
};

export default MetricsChart;
