/**
 * TrainingStatusMonitor 单元测试
 *
 * 测试训练状态监控组件的渲染和指标展示
 */

import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { TrainingStatusMonitor } from "@features/training/components";
import type {
  TrainingJobDetail,
  TrainingMetric,
} from "@features/training/types";

// Mock useTrainingJobMetrics hook
const mockUseTrainingJobMetrics = vi.fn();
vi.mock("@features/training/api", () => ({
  useTrainingJobMetrics: (...args: unknown[]) =>
    mockUseTrainingJobMetrics(...args),
}));

// 创建运行中的任务 mock
function createRunningJob(
  overrides: Partial<TrainingJobDetail> = {},
): TrainingJobDetail {
  return {
    id: 1,
    job_name: "test-job",
    display_name: "测试任务",
    description: "测试描述",
    owner_id: 1,
    owner_username: "admin",
    status: "running",
    hyperpod_status: "InService",
    kueue_workload_name: "workload-test",
    kueue_status: "Admitted",
    image_uri: "123456789012.dkr.ecr.us-west-2.amazonaws.com/test:latest",
    instance_type: "ml.p4d.24xlarge",
    node_count: 4,
    gpu_per_node: 8,
    tasks_per_node: 1,
    entry_point: "train.py",
    entrypoint_command: ["python", "train.py"],
    environment_variables: {},
    dataset_id: 1,
    dataset_name: "dataset-v1",
    data_mount_path: "/opt/ml/input/data",
    checkpoint_mount_path: "/opt/ml/checkpoints",
    hyperparameters: {},
    max_epochs: 10,
    total_epochs: 10,
    batch_size: 32,
    learning_rate: 0.0001,
    distribution_strategy: "fsdp",
    priority: "high",
    mixed_precision: true,
    use_spot_instances: false,
    total_pods: 4,
    running_pods: 4,
    failed_pods: 0,
    preemption_count: 0,
    current_epoch: 5,
    current_step: 5000,
    latest_loss: 0.25,
    latest_accuracy: 0.85,
    submitted_at: "2024-01-15T08:00:00Z",
    started_at: "2024-01-15T08:05:00Z",
    completed_at: null,
    duration_seconds: 7200,
    total_gpu_hours: 64,
    estimated_cost_usd: 256.5,
    error_message: null,
    failure_reason: null,
    hyperpod_job_arn:
      "arn:aws:sagemaker:us-west-2:123456789012:training-job/test-job",
    checkpoints_count: 5,
    created_at: "2024-01-15T07:55:00Z",
    updated_at: "2024-01-15T10:00:00Z",
    ...overrides,
  };
}

// Mock 指标数据
const mockMetrics: TrainingMetric[] = [
  {
    metric_name: "loss",
    step: 1000,
    value: 0.5,
    timestamp: "2024-01-15T08:10:00Z",
  },
  {
    metric_name: "loss",
    step: 2000,
    value: 0.4,
    timestamp: "2024-01-15T08:20:00Z",
  },
  {
    metric_name: "loss",
    step: 3000,
    value: 0.3,
    timestamp: "2024-01-15T08:30:00Z",
  },
  {
    metric_name: "learning_rate",
    step: 1000,
    value: 0.0001,
    timestamp: "2024-01-15T08:10:00Z",
  },
  {
    metric_name: "learning_rate",
    step: 2000,
    value: 0.00009,
    timestamp: "2024-01-15T08:20:00Z",
  },
  {
    metric_name: "gpu_utilization",
    step: 3000,
    value: 85.5,
    timestamp: "2024-01-15T08:30:00Z",
  },
  {
    metric_name: "throughput",
    step: 3000,
    value: 150.2,
    timestamp: "2024-01-15T08:30:00Z",
  },
];

describe("TrainingStatusMonitor", () => {
  beforeEach(() => {
    mockUseTrainingJobMetrics.mockReturnValue({
      data: { metrics: mockMetrics },
      isLoading: false,
    });
  });

  describe("训练进度", () => {
    it("应该渲染训练进度区域", () => {
      const job = createRunningJob();
      renderWithProviders(<TrainingStatusMonitor job={job} />);
      expect(screen.getByText("训练进度")).toBeInTheDocument();
    });

    it("应该显示 Epoch 信息", () => {
      const job = createRunningJob({ current_epoch: 5, total_epochs: 10 });
      renderWithProviders(<TrainingStatusMonitor job={job} />);
      expect(screen.getByText("当前 Epoch")).toBeInTheDocument();
      expect(screen.getByText("总 Epochs")).toBeInTheDocument();
    });

    it("应该显示进度百分比", () => {
      const job = createRunningJob({ current_epoch: 5, total_epochs: 10 });
      renderWithProviders(<TrainingStatusMonitor job={job} />);
      // Cloudscape ProgressBar 在多个 DOM 元素中渲染 label，使用 getAllByText
      const elements = screen.getAllByText(/Epoch 5 \/ 10/);
      expect(elements.length).toBeGreaterThanOrEqual(1);
    });

    it("应该显示当前 Step", () => {
      const job = createRunningJob({ current_step: 5000 });
      renderWithProviders(<TrainingStatusMonitor job={job} />);
      expect(screen.getByText("当前 Step")).toBeInTheDocument();
    });

    it("应该显示检查点数量", () => {
      const job = createRunningJob({ checkpoints_count: 5 });
      renderWithProviders(<TrainingStatusMonitor job={job} />);
      expect(screen.getByText("检查点数")).toBeInTheDocument();
    });
  });

  describe("实时指标", () => {
    it("应该渲染实时指标区域", () => {
      const job = createRunningJob();
      renderWithProviders(<TrainingStatusMonitor job={job} />);
      expect(screen.getByText("实时指标")).toBeInTheDocument();
    });

    it("应该显示 GPU 利用率", () => {
      const job = createRunningJob();
      renderWithProviders(<TrainingStatusMonitor job={job} />);
      expect(screen.getByText("GPU 利用率")).toBeInTheDocument();
      // 最新的 gpu_utilization 值为 85.5%
      expect(screen.getByText("85.5%")).toBeInTheDocument();
    });

    it("应该显示当前 Loss", () => {
      const job = createRunningJob();
      renderWithProviders(<TrainingStatusMonitor job={job} />);
      expect(screen.getByText("当前 Loss")).toBeInTheDocument();
      // 最新的 loss 值为 0.3
      expect(screen.getByText("0.300000")).toBeInTheDocument();
    });

    it("应该显示学习率", () => {
      const job = createRunningJob();
      renderWithProviders(<TrainingStatusMonitor job={job} />);
      expect(screen.getByText("学习率")).toBeInTheDocument();
    });

    it("应该显示吞吐量", () => {
      const job = createRunningJob();
      renderWithProviders(<TrainingStatusMonitor job={job} />);
      expect(screen.getByText("吞吐量")).toBeInTheDocument();
      expect(screen.getByText("150.2 samples/s")).toBeInTheDocument();
    });
  });

  describe("Loss 曲线", () => {
    it("应该渲染 Loss 曲线区域", () => {
      const job = createRunningJob();
      renderWithProviders(<TrainingStatusMonitor job={job} />);
      expect(screen.getByText("Loss 曲线")).toBeInTheDocument();
    });

    it("应该在无 Loss 数据时显示空状态", () => {
      mockUseTrainingJobMetrics.mockReturnValue({
        data: { metrics: [] },
        isLoading: false,
      });
      const job = createRunningJob();
      renderWithProviders(<TrainingStatusMonitor job={job} />);
      expect(screen.getByText("暂无 Loss 数据")).toBeInTheDocument();
    });
  });

  describe("GPU 利用率指示器", () => {
    it('应该在无数据时显示 "无数据"', () => {
      mockUseTrainingJobMetrics.mockReturnValue({
        data: { metrics: [] },
        isLoading: false,
      });
      const job = createRunningJob();
      renderWithProviders(<TrainingStatusMonitor job={job} />);
      expect(screen.getByText("无数据")).toBeInTheDocument();
    });
  });

  describe("加载状态", () => {
    it("应该在加载指标时显示加载文本", () => {
      mockUseTrainingJobMetrics.mockReturnValue({
        data: undefined,
        isLoading: true,
      });
      const job = createRunningJob();
      renderWithProviders(<TrainingStatusMonitor job={job} />);
      expect(screen.getByText("加载指标数据...")).toBeInTheDocument();
    });
  });

  describe("轮询控制", () => {
    it("运行中的任务应该启用指标轮询", () => {
      const job = createRunningJob({ status: "running" });
      renderWithProviders(
        <TrainingStatusMonitor job={job} pollInterval={30000} />,
      );

      // 验证 useTrainingJobMetrics 传入了正确的轮询参数
      expect(mockUseTrainingJobMetrics).toHaveBeenCalledWith(
        1,
        expect.objectContaining({
          metric_names: [
            "loss",
            "learning_rate",
            "gpu_utilization",
            "throughput",
          ],
        }),
        30000, // 运行中任务应启用轮询
      );
    });

    it("已完成的任务不应轮询", () => {
      const job = createRunningJob({ status: "completed" });
      renderWithProviders(<TrainingStatusMonitor job={job} />);

      // 已完成任务的 pollInterval 应为 undefined
      expect(mockUseTrainingJobMetrics).toHaveBeenCalledWith(
        1,
        expect.any(Object),
        undefined,
      );
    });
  });
});
