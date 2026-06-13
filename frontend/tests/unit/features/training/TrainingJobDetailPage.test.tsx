/**
 * TrainingJobDetailPage 单元测试
 *
 * 测试训练任务详情页面的渲染、Tab 切换和操作按钮
 */

import { describe, it, expect, vi } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { TrainingJobDetailPage } from "@features/training/pages";
import type { TrainingJobDetail } from "@features/training/types";

// Mock useParams 和 useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: "1" }),
  };
});

// Mock 运行中的任务详情数据
const mockRunningJob: TrainingJobDetail = {
  id: 1,
  job_name: "llama2-finetune-001",
  display_name: "LLaMA 2 微调训练",
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
  current_epoch: 3,
  current_step: 3000,
  latest_loss: 0.342,
  latest_accuracy: null,
  submitted_at: "2024-01-15T08:00:00Z",
  started_at: "2024-01-15T08:05:00Z",
  completed_at: null,
  duration_seconds: 7200,
  total_gpu_hours: 64,
  estimated_cost_usd: 256.5,
  error_message: null,
  failure_reason: null,
  hyperpod_job_arn:
    "arn:aws:sagemaker:us-west-2:123456789012:training-job/test",
  checkpoints_count: 3,
  created_at: "2024-01-15T07:55:00Z",
  updated_at: "2024-01-15T10:00:00Z",
};

// Mock API hooks
const mockRefetch = vi.fn();
const mockRefetchLogs = vi.fn();
const mockPauseMutateAsync = vi.fn();
const mockResumeMutateAsync = vi.fn();
const mockDeleteMutateAsync = vi.fn();

const mockUseTrainingJob = vi.fn();
const mockUseTrainingJobCheckpoints = vi.fn();
const mockUseTrainingJobLogs = vi.fn();
const mockUsePauseTrainingJob = vi.fn();
const mockUseResumeTrainingJob = vi.fn();
const mockUseDeleteTrainingJob = vi.fn();

vi.mock("@features/training/api", () => ({
  useTrainingJob: (...args: unknown[]) => mockUseTrainingJob(...args),
  useTrainingJobCheckpoints: (...args: unknown[]) =>
    mockUseTrainingJobCheckpoints(...args),
  useTrainingJobLogs: (...args: unknown[]) => mockUseTrainingJobLogs(...args),
  usePauseTrainingJob: () => mockUsePauseTrainingJob(),
  useResumeTrainingJob: () => mockUseResumeTrainingJob(),
  useDeleteTrainingJob: () => mockUseDeleteTrainingJob(),
}));

// Mock TrainingStatusMonitor（避免其内部 hook 调用）
vi.mock("@features/training/components/TrainingStatusMonitor", () => ({
  TrainingStatusMonitor: () => (
    <div data-testid="status-monitor">训练指标监控</div>
  ),
}));

describe("TrainingJobDetailPage", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockRefetch.mockClear();

    // 默认设置：运行中的任务
    mockUseTrainingJob.mockReturnValue({
      data: mockRunningJob,
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    });

    mockUseTrainingJobCheckpoints.mockReturnValue({
      data: {
        items: [
          {
            id: 1,
            training_job_id: 1,
            checkpoint_name: "checkpoint-epoch-1",
            storage_path: "s3://bucket/checkpoints/epoch-1",
            checkpoint_type: "epoch",
            epoch: 1,
            step: 1000,
            size_bytes: 1073741824,
            loss: 0.5,
            accuracy: null,
            storage_tier: "fsx",
            status: "available",
            metadata: null,
            created_at: "2024-01-15T09:00:00Z",
          },
        ],
      },
      isLoading: false,
    });

    mockUseTrainingJobLogs.mockReturnValue({
      data: {
        logs: [
          {
            timestamp: "2024-01-15T09:00:00Z",
            pod_name: "worker-0",
            message: "Training started",
          },
        ],
        next_token: null,
      },
      isLoading: false,
      refetch: mockRefetchLogs,
    });

    mockUsePauseTrainingJob.mockReturnValue({
      mutateAsync: mockPauseMutateAsync,
      isPending: false,
    });

    mockUseResumeTrainingJob.mockReturnValue({
      mutateAsync: mockResumeMutateAsync,
      isPending: false,
    });

    mockUseDeleteTrainingJob.mockReturnValue({
      mutateAsync: mockDeleteMutateAsync,
      isPending: false,
    });
  });

  describe("基本渲染", () => {
    it("应该渲染任务名称作为标题", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      expect(
        screen.getByRole("heading", { name: "llama2-finetune-001" }),
      ).toBeInTheDocument();
    });

    it("应该渲染面包屑导航", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      // 面包屑中包含 "训练任务"，可能与其他区域重复，验证存在
      const breadcrumbTexts = screen.getAllByText(/训练任务/);
      expect(breadcrumbTexts.length).toBeGreaterThanOrEqual(1);
      // 面包屑中包含任务名
      expect(
        screen.getByRole("heading", { name: "llama2-finetune-001" }),
      ).toBeInTheDocument();
    });

    it("应该渲染概览区域", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      expect(screen.getByText("概览")).toBeInTheDocument();
      expect(screen.getByText("状态")).toBeInTheDocument();
      expect(screen.getByText("优先级")).toBeInTheDocument();
      expect(screen.getByText("分布式策略")).toBeInTheDocument();
      expect(screen.getByText("持续时间")).toBeInTheDocument();
    });

    it("应该显示优先级标签", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      expect(screen.getByText("高")).toBeInTheDocument();
    });

    it("应该显示分布式策略标签", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      expect(screen.getByText("PyTorch FSDP")).toBeInTheDocument();
    });
  });

  describe("训练进度", () => {
    it("应该渲染训练进度区域", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      expect(screen.getByText("训练进度")).toBeInTheDocument();
    });

    it("应该显示 Epoch 进度", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      expect(screen.getByText("当前 Epoch")).toBeInTheDocument();
    });
  });

  describe("Tab 标签页", () => {
    it("应该渲染配置信息 Tab", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      expect(screen.getByText("配置信息")).toBeInTheDocument();
    });

    it("应该渲染检查点 Tab", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      // "检查点" 出现在多处：检查点数量标签、检查点 Tab 标签
      const checkpointElements = screen.getAllByText(/检查点/);
      expect(checkpointElements.length).toBeGreaterThanOrEqual(1);
    });

    it("应该渲染日志 Tab", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      expect(screen.getByText("日志")).toBeInTheDocument();
    });

    it("应该渲染训练指标 Tab", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      expect(screen.getByText("训练指标")).toBeInTheDocument();
    });
  });

  describe("操作按钮", () => {
    it("运行中的任务应该显示暂停按钮", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      expect(screen.getByRole("button", { name: "暂停" })).toBeInTheDocument();
    });

    it("运行中的任务不应显示恢复按钮", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      expect(
        screen.queryByRole("button", { name: "恢复" }),
      ).not.toBeInTheDocument();
    });

    it("应该显示刷新按钮", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      expect(screen.getByRole("button", { name: "刷新" })).toBeInTheDocument();
    });

    it("运行中的任务应该禁用删除按钮", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      const deleteButton = screen.getByRole("button", { name: "删除" });
      expect(deleteButton).toBeDisabled();
    });
  });

  describe("已暂停任务", () => {
    beforeEach(() => {
      mockUseTrainingJob.mockReturnValue({
        data: { ...mockRunningJob, status: "paused" },
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });
    });

    it("应该显示恢复按钮", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      expect(screen.getByRole("button", { name: "恢复" })).toBeInTheDocument();
    });

    it("不应显示暂停按钮", () => {
      renderWithProviders(<TrainingJobDetailPage />);
      expect(
        screen.queryByRole("button", { name: "暂停" }),
      ).not.toBeInTheDocument();
    });
  });

  describe("删除确认", () => {
    beforeEach(() => {
      mockUseTrainingJob.mockReturnValue({
        data: { ...mockRunningJob, status: "completed" },
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });
    });

    it("应该在点击删除后显示确认弹窗", () => {
      renderWithProviders(<TrainingJobDetailPage />);

      const deleteButton = screen.getByRole("button", { name: "删除" });
      expect(deleteButton).toBeEnabled();

      fireEvent.click(deleteButton);

      // Modal header 和 button 都包含"确认删除"，使用 getAllByText
      const confirmDeleteElements = screen.getAllByText("确认删除");
      expect(confirmDeleteElements.length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText(/确定要删除训练任务/)).toBeInTheDocument();
    });

    it("应该在取消删除时关闭弹窗", () => {
      renderWithProviders(<TrainingJobDetailPage />);

      fireEvent.click(screen.getByRole("button", { name: "删除" }));

      // Modal header 和 button 都包含"确认删除"，使用 getAllByText
      const confirmDeleteElements = screen.getAllByText("确认删除");
      expect(confirmDeleteElements.length).toBeGreaterThanOrEqual(1);

      // 点击取消
      fireEvent.click(screen.getByRole("button", { name: "取消" }));

      // Modal 应关闭
      expect(screen.queryByText("确定要删除训练任务")).not.toBeInTheDocument();
    });
  });

  describe("加载状态", () => {
    it("应该在加载时显示 Spinner", () => {
      mockUseTrainingJob.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: mockRefetch,
      });

      renderWithProviders(<TrainingJobDetailPage />);
      expect(screen.getByText("加载中...")).toBeInTheDocument();
    });
  });

  describe("错误状态", () => {
    it("应该在任务不存在时在骨架内显示 InlineErrorState 并提供重试", async () => {
      mockUseTrainingJob.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: "训练任务不存在" },
        refetch: mockRefetch,
      });

      renderWithProviders(<TrainingJobDetailPage />);

      // InlineErrorState 标题
      expect(await screen.findByText("加载失败")).toBeInTheDocument();
      // error.message 作为错误描述仍渲染
      expect(screen.getByText(/训练任务不存在/)).toBeInTheDocument();
      // 重试按钮（onRetry → refetch）
      expect(
        screen.getByRole("button", { name: "重试" }),
      ).toBeInTheDocument();
    });
  });
});
