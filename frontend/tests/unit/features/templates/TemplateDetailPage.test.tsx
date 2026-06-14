/**
 * TemplateDetailPage Tests
 *
 * 测试模板详情页面的渲染、加载态、错误态（F-025）。
 * 重点验证 error / !template 态保留 PageLayout 骨架（标题 + 面包屑），
 * 并提供 InlineErrorState 的「重试」入口（详情页范式 A，对齐 interaction-states.md §1）。
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { TemplateDetailPage } from "@features/templates/pages";
import { useUIStore } from "@store/slices/uiSlice";
import type { JobTemplateDetail } from "@features/templates/types";

// Mock API hooks（沿用 TemplateListPage.test.tsx 的模块级 mock 模式）
const mockUseJobTemplate = vi.fn();
const mockUseDeleteJobTemplate = vi.fn();

vi.mock("@features/templates/api", () => ({
  useJobTemplate: (...args: unknown[]) => mockUseJobTemplate(...args),
  useDeleteJobTemplate: (...args: unknown[]) => mockUseDeleteJobTemplate(...args),
}));

// Mock useNavigate / useParams
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: "1" }),
  };
});

const mockTemplate: JobTemplateDetail = {
  id: 1,
  name: "PyTorch DDP 模板",
  description: "分布式训练模板",
  visibility: "public",
  usage_count: 42,
  owner_id: 1,
  created_at: "2024-06-01T00:00:00Z",
  updated_at: "2024-06-02T00:00:00Z",
  last_used_at: "2024-06-03T00:00:00Z",
  training_config: {
    image: "pytorch/pytorch:2.1.0",
    script_path: "train.py",
    instance_type: "ml.p4d.24xlarge",
    instance_count: 4,
    distribution_strategy: "ddp",
    environment: { CUDA_VISIBLE_DEVICES: "0,1" },
    hyperparameters: { lr: 0.001, epochs: 10 },
  },
};

describe("TemplateDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseJobTemplate.mockReturnValue({
      data: mockTemplate,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    mockUseDeleteJobTemplate.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
  });

  describe("基本渲染", () => {
    it("加载完成应渲染模板名称作为标题", () => {
      renderWithProviders(<TemplateDetailPage />);
      expect(
        screen.getByRole("heading", { level: 1, name: "PyTorch DDP 模板" }),
      ).toBeInTheDocument();
    });

    it("应渲染基本信息和训练配置区块", () => {
      renderWithProviders(<TemplateDetailPage />);
      expect(screen.getByText("基本信息")).toBeInTheDocument();
      expect(screen.getByText("训练配置")).toBeInTheDocument();
    });
  });

  describe("加载状态", () => {
    it("加载时应显示加载指示器", () => {
      mockUseJobTemplate.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(<TemplateDetailPage />);
      expect(screen.getByText("加载中...")).toBeInTheDocument();
    });
  });

  describe("错误状态（F-025）", () => {
    it("加载失败应保留 PageLayout 骨架标题「模板详情」", () => {
      mockUseJobTemplate.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error("Network error"),
        refetch: vi.fn(),
      });

      renderWithProviders(<TemplateDetailPage />);
      // 骨架标题：error 态不得塌缩，必须保留固定通用标题
      expect(
        screen.getByRole("heading", { level: 1, name: "模板详情" }),
      ).toBeInTheDocument();
    });

    it("加载失败应显示「加载失败」标题与错误信息", () => {
      mockUseJobTemplate.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error("Network error"),
        refetch: vi.fn(),
      });

      renderWithProviders(<TemplateDetailPage />);
      expect(screen.getByText("加载失败")).toBeInTheDocument();
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });

    it("加载失败应提供「重试」按钮并调用 refetch", () => {
      const mockRefetch = vi.fn();
      mockUseJobTemplate.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error("Network error"),
        refetch: mockRefetch,
      });

      renderWithProviders(<TemplateDetailPage />);
      const retryButton = screen.getByRole("button", { name: "重试" });
      expect(retryButton).toBeInTheDocument();
      retryButton.click();
      expect(mockRefetch).toHaveBeenCalled();
    });

    it("加载失败应保留面包屑导航", () => {
      mockUseJobTemplate.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error("Network error"),
        refetch: vi.fn(),
      });

      renderWithProviders(<TemplateDetailPage />);
      // 面包屑经 PageLayout 同步到全局 UI Store
      const breadcrumbs = useUIStore.getState().breadcrumbs;
      expect(breadcrumbs.some((b) => b.text === "任务模板")).toBe(true);
    });
  });

  describe("模板不存在", () => {
    it("template 为空时应显示「模板不存在」且不提供重试", () => {
      mockUseJobTemplate.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(<TemplateDetailPage />);
      // 骨架标题仍保留
      expect(
        screen.getByRole("heading", { level: 1, name: "模板详情" }),
      ).toBeInTheDocument();
      expect(screen.getByText("模板不存在")).toBeInTheDocument();
      // 纯「不存在」场景不给重试入口
      expect(
        screen.queryByRole("button", { name: "重试" }),
      ).not.toBeInTheDocument();
    });
  });
});
