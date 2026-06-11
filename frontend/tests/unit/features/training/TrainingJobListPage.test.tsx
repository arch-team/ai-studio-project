/**
 * TrainingJobListPage 单元测试
 *
 * 测试训练任务列表页面的渲染、过滤和导航
 */

import { describe, it, expect, vi } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { TrainingJobListPage } from "@features/training/pages";
import type { TrainingJobSummary } from "@features/training/types";

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock 任务列表数据
const mockItems: TrainingJobSummary[] = [
  {
    id: 1,
    job_name: "llama2-finetune-001",
    display_name: "LLaMA 2 微调训练",
    owner_id: 1,
    owner_username: "admin",
    status: "running",
    priority: "high",
    instance_type: "ml.p4d.24xlarge",
    node_count: 4,
    gpu_per_node: 8,
    distribution_strategy: "fsdp",
    current_epoch: 3,
    total_epochs: 10,
    latest_loss: 0.342,
    checkpoints_count: 3,
    submitted_at: "2024-01-15T08:00:00Z",
    started_at: "2024-01-15T08:05:00Z",
    completed_at: null,
    created_at: "2024-01-15T07:55:00Z",
    duration_seconds: 7200,
    estimated_cost_usd: 256.5,
  },
];

// Mock useTrainingJobs hook
const mockUseTrainingJobs = vi.fn();
const mockRefetch = vi.fn();

vi.mock("@features/training/api", () => ({
  useTrainingJobs: (...args: unknown[]) => mockUseTrainingJobs(...args),
}));

describe("TrainingJobListPage", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockRefetch.mockClear();
    // 默认返回有数据的状态
    mockUseTrainingJobs.mockReturnValue({
      data: {
        items: mockItems,
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
      isLoading: false,
      error: null,
      refetch: mockRefetch,
    });
  });

  describe("基本渲染", () => {
    it("应该渲染页面标题", () => {
      renderWithProviders(<TrainingJobListPage />);
      expect(
        screen.getByRole("heading", { name: "训练任务管理" }),
      ).toBeInTheDocument();
    });

    it("应该渲染创建按钮", () => {
      renderWithProviders(<TrainingJobListPage />);
      expect(
        screen.getByRole("button", { name: "创建训练任务" }),
      ).toBeInTheDocument();
    });

    it("应该渲染刷新按钮", () => {
      renderWithProviders(<TrainingJobListPage />);
      expect(screen.getByRole("button", { name: "刷新" })).toBeInTheDocument();
    });

    it("应该渲染状态过滤器", () => {
      renderWithProviders(<TrainingJobListPage />);
      expect(screen.getByText("全部状态")).toBeInTheDocument();
    });

    it("应该渲染优先级过滤器", () => {
      renderWithProviders(<TrainingJobListPage />);
      expect(screen.getByText("全部优先级")).toBeInTheDocument();
    });
  });

  describe("数据加载", () => {
    it("应该显示训练任务列表数据", () => {
      renderWithProviders(<TrainingJobListPage />);
      expect(screen.getByText("llama2-finetune-001")).toBeInTheDocument();
    });

    it("应该显示任务表格", () => {
      renderWithProviders(<TrainingJobListPage />);
      // 页面标题和表格标题都包含 "训练任务"，验证多处存在
      const elements = screen.getAllByText(/训练任务/);
      expect(elements.length).toBeGreaterThanOrEqual(2);
    });

    it("应该传递 30 秒轮询参数", () => {
      renderWithProviders(<TrainingJobListPage />);
      // 验证 useTrainingJobs 被调用时传入了 30000 轮询间隔
      expect(mockUseTrainingJobs).toHaveBeenCalledWith(
        expect.any(Object),
        30000,
      );
    });
  });

  describe("导航", () => {
    it("应该在点击创建按钮时导航到创建页面", () => {
      renderWithProviders(<TrainingJobListPage />);

      fireEvent.click(screen.getByRole("button", { name: "创建训练任务" }));

      expect(mockNavigate).toHaveBeenCalledWith("/training-jobs/create");
    });

    it("应该在点击任务名称时导航到详情页", () => {
      renderWithProviders(<TrainingJobListPage />);

      fireEvent.click(screen.getByText("llama2-finetune-001"));
      expect(mockNavigate).toHaveBeenCalledWith("/training-jobs/1");
    });
  });

  describe("错误处理", () => {
    it("应该在 API 错误时显示错误信息", () => {
      mockUseTrainingJobs.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: "服务器错误" },
        refetch: mockRefetch,
      });

      renderWithProviders(<TrainingJobListPage />);

      expect(screen.getByText(/加载失败/)).toBeInTheDocument();
    });
  });

  describe("空列表", () => {
    it("应该在无任务时显示空状态", () => {
      mockUseTrainingJobs.mockReturnValue({
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
          total_pages: 0,
        },
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });

      renderWithProviders(<TrainingJobListPage />);

      expect(screen.getByText("暂无训练任务")).toBeInTheDocument();
    });
  });
});
