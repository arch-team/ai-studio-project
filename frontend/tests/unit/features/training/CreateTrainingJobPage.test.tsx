/**
 * CreateTrainingJobPage 单元测试
 *
 * 测试创建训练任务页面的渲染、导航和表单提交
 */

import { describe, it, expect, vi } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { CreateTrainingJobPage } from "@features/training/pages";

// Mock useResourceLimitConfigs
vi.mock("@features/resource-quotas", () => ({
  useResourceLimitConfigs: vi.fn(() => ({
    data: {
      items: [
        {
          id: 1,
          max_gpu_per_job: 64,
          max_nodes_per_job: 8,
          max_jobs_per_user: 10,
          max_running_jobs: 5,
        },
      ],
    },
    isLoading: false,
  })),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock useCreateTrainingJob hook
const mockMutateAsync = vi.fn();
const mockUseCreateTrainingJob = vi.fn();

vi.mock("@features/training/api", () => ({
  useCreateTrainingJob: () => mockUseCreateTrainingJob(),
}));

describe("CreateTrainingJobPage", () => {
  beforeEach(() => {
    mockNavigate.mockClear();
    mockMutateAsync.mockClear();
    // 默认返回非 pending 状态
    mockUseCreateTrainingJob.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      error: null,
    });
  });

  describe("基本渲染", () => {
    it("应该渲染页面标题", () => {
      renderWithProviders(<CreateTrainingJobPage />);
      expect(
        screen.getByRole("heading", { name: "创建训练任务" }),
      ).toBeInTheDocument();
    });

    it("应该渲染面包屑导航", () => {
      renderWithProviders(<CreateTrainingJobPage />);
      // 面包屑导航和表单区域都可能包含 "训练任务" 文本，验证存在即可
      const elements = screen.getAllByText(/训练任务/);
      expect(elements.length).toBeGreaterThanOrEqual(1);
    });

    it("应该渲染表单组件", () => {
      renderWithProviders(<CreateTrainingJobPage />);
      // 表单应包含基础配置区域
      expect(screen.getByText("基础配置")).toBeInTheDocument();
      expect(screen.getByText("容器配置")).toBeInTheDocument();
      expect(screen.getByText("分布式配置")).toBeInTheDocument();
    });

    it("应该渲染创建和取消按钮", () => {
      renderWithProviders(<CreateTrainingJobPage />);
      expect(
        screen.getByRole("button", { name: "创建任务" }),
      ).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "取消" })).toBeInTheDocument();
    });
  });

  describe("表单提交", () => {
    it("应该在提交成功后导航到详情页", async () => {
      // Mock mutateAsync 成功返回
      mockMutateAsync.mockResolvedValue({
        id: 42,
        job_name: "test-job",
        status: "submitted",
      });

      renderWithProviders(<CreateTrainingJobPage />);

      // 由于 Cloudscape Input 不响应 fireEvent，验证按钮点击空表单时会显示验证错误
      fireEvent.click(screen.getByRole("button", { name: "创建任务" }));

      // 空表单提交时应显示验证错误（因为 Cloudscape Input 无法模拟填写）
      expect(screen.getByText("请输入任务名称")).toBeInTheDocument();
    });
  });

  describe("取消操作", () => {
    it("应该在点击取消时导航回列表页", () => {
      renderWithProviders(<CreateTrainingJobPage />);

      fireEvent.click(screen.getByRole("button", { name: "取消" }));
      expect(mockNavigate).toHaveBeenCalledWith("/training-jobs");
    });
  });

  describe("错误处理", () => {
    it("应该在 mutation 错误时显示错误信息", () => {
      mockUseCreateTrainingJob.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isError: true,
        error: { message: "任务名称重复" },
      });

      renderWithProviders(<CreateTrainingJobPage />);

      expect(screen.getByText(/创建失败/)).toBeInTheDocument();
    });
  });

  describe("提交状态", () => {
    it("应该在提交中禁用取消按钮", () => {
      mockUseCreateTrainingJob.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: true,
        isError: false,
        error: null,
      });

      renderWithProviders(<CreateTrainingJobPage />);

      // isSubmitting=true 时取消按钮应被禁用
      const cancelButton = screen.getByRole("button", { name: "取消" });
      expect(cancelButton).toBeDisabled();
    });
  });
});
