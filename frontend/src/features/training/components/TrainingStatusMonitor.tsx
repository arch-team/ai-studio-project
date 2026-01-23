/**
 * Training Status Monitor Component
 *
 * 训练状态监控组件 - 显示 GPU 利用率、训练进度和 Loss 曲线
 */

import {
  Box,
  ColumnLayout,
  Container,
  Header,
  LineChart,
  ProgressBar,
  SpaceBetween,
  StatusIndicator,
} from '@cloudscape-design/components';
import { useMemo } from 'react';
import { useTrainingJobMetrics } from '../api';
import type { TrainingJobDetail, TrainingMetric } from '../types';

interface TrainingStatusMonitorProps {
  job: TrainingJobDetail;
  pollInterval?: number;
}

/**
 * 将指标数据转换为图表格式
 */
function formatMetricsForChart(
  metrics: TrainingMetric[],
  metricName: string
): { x: number; y: number }[] {
  return metrics
    .filter((m) => m.metric_name === metricName)
    .map((m) => ({
      x: m.step,
      y: m.value,
    }))
    .sort((a, b) => a.x - b.x);
}

/**
 * 获取最新的指标值
 */
function getLatestMetricValue(
  metrics: TrainingMetric[],
  metricName: string
): number | null {
  const filtered = metrics.filter((m) => m.metric_name === metricName);
  if (filtered.length === 0) return null;
  const sorted = filtered.sort((a, b) => b.step - a.step);
  return sorted[0].value;
}

/**
 * GPU 利用率指示器
 */
function GpuUtilizationIndicator({ utilization }: { utilization: number | null }) {
  if (utilization === null) {
    return <StatusIndicator type="pending">无数据</StatusIndicator>;
  }

  const type =
    utilization >= 80
      ? 'success'
      : utilization >= 50
      ? 'warning'
      : 'error';

  return (
    <StatusIndicator type={type}>
      {utilization.toFixed(1)}%
    </StatusIndicator>
  );
}

/**
 * 训练状态监控组件
 */
export function TrainingStatusMonitor({
  job,
  pollInterval = 30000,
}: TrainingStatusMonitorProps) {
  // 获取训练指标，默认 30 秒刷新
  const { data: metricsData, isLoading } = useTrainingJobMetrics(
    job.id,
    {
      metric_names: ['loss', 'learning_rate', 'gpu_utilization', 'throughput'],
    },
    job.status === 'running' ? pollInterval : undefined
  );

  const metrics = useMemo(() => metricsData?.metrics || [], [metricsData?.metrics]);

  // 计算进度百分比
  const progress = useMemo(() => {
    if (job.total_epochs && job.current_epoch != null) {
      return Math.round((job.current_epoch / job.total_epochs) * 100);
    }
    return 0;
  }, [job.current_epoch, job.total_epochs]);

  // 获取最新指标值
  const latestLoss = getLatestMetricValue(metrics, 'loss');
  const latestLr = getLatestMetricValue(metrics, 'learning_rate');
  const latestGpuUtil = getLatestMetricValue(metrics, 'gpu_utilization');
  const latestThroughput = getLatestMetricValue(metrics, 'throughput');

  // 准备 Loss 曲线数据
  const lossChartData = useMemo(
    () => formatMetricsForChart(metrics, 'loss'),
    [metrics]
  );

  // 准备学习率曲线数据
  const lrChartData = useMemo(
    () => formatMetricsForChart(metrics, 'learning_rate'),
    [metrics]
  );

  return (
    <SpaceBetween size="l">
      {/* 训练进度 */}
      <Container header={<Header variant="h2">训练进度</Header>}>
        <SpaceBetween size="m">
          <ProgressBar
            value={progress}
            label={`Epoch ${job.current_epoch ?? 0} / ${job.total_epochs ?? '-'}`}
            description={
              job.current_step != null
                ? `Step: ${job.current_step.toLocaleString()}`
                : undefined
            }
            status={job.status === 'running' ? 'in-progress' : 'success'}
          />
          <ColumnLayout columns={4} variant="text-grid">
            <div>
              <Box variant="awsui-key-label">当前 Epoch</Box>
              <Box>{job.current_epoch ?? '-'}</Box>
            </div>
            <div>
              <Box variant="awsui-key-label">总 Epochs</Box>
              <Box>{job.total_epochs ?? '-'}</Box>
            </div>
            <div>
              <Box variant="awsui-key-label">当前 Step</Box>
              <Box>{job.current_step?.toLocaleString() ?? '-'}</Box>
            </div>
            <div>
              <Box variant="awsui-key-label">检查点数</Box>
              <Box>{job.checkpoints_count ?? 0}</Box>
            </div>
          </ColumnLayout>
        </SpaceBetween>
      </Container>

      {/* 实时指标 */}
      <Container header={<Header variant="h2">实时指标</Header>}>
        <ColumnLayout columns={4} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">GPU 利用率</Box>
            <GpuUtilizationIndicator utilization={latestGpuUtil} />
          </div>
          <div>
            <Box variant="awsui-key-label">当前 Loss</Box>
            <Box>{latestLoss?.toFixed(6) ?? '-'}</Box>
          </div>
          <div>
            <Box variant="awsui-key-label">学习率</Box>
            <Box>{latestLr?.toExponential(2) ?? '-'}</Box>
          </div>
          <div>
            <Box variant="awsui-key-label">吞吐量</Box>
            <Box>
              {latestThroughput != null
                ? `${latestThroughput.toFixed(1)} samples/s`
                : '-'}
            </Box>
          </div>
        </ColumnLayout>
      </Container>

      {/* Loss 曲线 */}
      <Container header={<Header variant="h2">Loss 曲线</Header>}>
        {lossChartData.length > 0 ? (
          <LineChart
            series={[
              {
                title: 'Training Loss',
                type: 'line',
                data: lossChartData,
              },
            ]}
            xDomain={[
              Math.min(...lossChartData.map((d) => d.x)),
              Math.max(...lossChartData.map((d) => d.x)),
            ]}
            yDomain={[
              Math.min(...lossChartData.map((d) => d.y)) * 0.9,
              Math.max(...lossChartData.map((d) => d.y)) * 1.1,
            ]}
            i18nStrings={{
              xTickFormatter: (x) => `Step ${x}`,
              yTickFormatter: (y) => y.toFixed(4),
            }}
            height={250}
            hideFilter
            hideLegend
            empty={<Box textAlign="center">暂无数据</Box>}
            noMatch={<Box textAlign="center">无匹配数据</Box>}
          />
        ) : (
          <Box textAlign="center" color="text-body-secondary" padding="l">
            {isLoading ? '加载指标数据...' : '暂无 Loss 数据'}
          </Box>
        )}
      </Container>

      {/* 学习率曲线 */}
      {lrChartData.length > 0 && (
        <Container header={<Header variant="h2">学习率曲线</Header>}>
          <LineChart
            series={[
              {
                title: 'Learning Rate',
                type: 'line',
                data: lrChartData,
              },
            ]}
            xDomain={[
              Math.min(...lrChartData.map((d) => d.x)),
              Math.max(...lrChartData.map((d) => d.x)),
            ]}
            yDomain={[0, Math.max(...lrChartData.map((d) => d.y)) * 1.2]}
            i18nStrings={{
              xTickFormatter: (x) => `Step ${x}`,
              yTickFormatter: (y) => y.toExponential(2),
            }}
            height={200}
            hideFilter
            hideLegend
          />
        </Container>
      )}
    </SpaceBetween>
  );
}

export default TrainingStatusMonitor;
