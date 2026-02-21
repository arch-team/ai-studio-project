/**
 * ModelDetailPage 单元测试
 *
 * 测试模型详情页面的渲染、操作和标签页
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { ModelDetailPage } from "@features/models/pages";
import type { ModelDetail } from "@features/models/types";

// Mock 数据
const mockModel: ModelDetail = {
  id: 1,
  model_name: "bert-base-v1",
  version: "v1.0.0",
  display_name: "BERT Base",
  description: "基于 BERT 的文本分类模型",
  owner_id: 100,
  training_job_id: 10,
  checkpoint_id: 5,
  model_uri: "s3://models/bert-base-v1",
  model_path: "/models/bert-base-v1",
  registry_arn: "arn:aws:sagemaker:us-east-1:123456789:model-package/bert-base",
  registry_status: "synced",
  metrics: { accuracy: 0.9512, loss: 0.1234 },
  hyperparameters: { learning_rate: 0.001, batch_size: 32, epochs: 10 },
  framework: "pytorch",
  framework_version: "2.0",
  status: "registered",
  size_bytes: 1073741824,
  model_format: "safetensors",
  tags: ["nlp", "production"],
  created_at: "2024-01-15T10:00:00Z",
  updated_at: "2024-01-20T14:00:00Z",
  registered_at: "2024-01-15T12:00:00Z",
  archived_at: null,
};

// Mock hooks
const mockUseModel = vi.fn();
const mockUseArchiveModel = vi.fn();
const mockUseRestoreModel = vi.fn();

vi.mock("@features/models/api", () => ({
  useModel: () => mockUseModel(),
  useArchiveModel: () => mockUseArchiveModel(),
  useRestoreModel: () => mockUseRestoreModel(),
}));

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

describe("ModelDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseModel.mockReturnValue({
      data: mockModel,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    mockUseArchiveModel.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });

    mockUseRestoreModel.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
  });

  describe("基本渲染", () => {
    it("应该渲染模型名称作为标题", () => {
      renderWithProviders(<ModelDetailPage />);
      // Header 中有模型名称
      expect(screen.getAllByText("bert-base-v1").length).toBeGreaterThan(0);
    });

    it("应该渲染面包屑导航", () => {
      renderWithProviders(<ModelDetailPage />);
      // 面包屑和 Header 中都有"模型管理"文本
      expect(screen.getAllByText("模型管理").length).toBeGreaterThan(0);
    });

    it("应该渲染刷新按钮", () => {
      renderWithProviders(<ModelDetailPage />);
      expect(screen.getByRole("button", { name: /刷新/ })).toBeInTheDocument();
    });

    it("应该渲染版本历史按钮", () => {
      renderWithProviders(<ModelDetailPage />);
      expect(
        screen.getByRole("button", { name: /版本历史/ }),
      ).toBeInTheDocument();
    });
  });

  describe("概览信息", () => {
    it("应该显示概览标题", () => {
      renderWithProviders(<ModelDetailPage />);
      expect(screen.getByText("概览")).toBeInTheDocument();
    });

    it("应该显示版本号", () => {
      renderWithProviders(<ModelDetailPage />);
      expect(screen.getAllByText("v1.0.0").length).toBeGreaterThan(0);
    });

    it("应该显示框架名称", () => {
      renderWithProviders(<ModelDetailPage />);
      expect(screen.getAllByText("PyTorch").length).toBeGreaterThan(0);
    });
  });

  describe("关联训练任务", () => {
    it("应该显示关联训练任务区域", () => {
      renderWithProviders(<ModelDetailPage />);
      expect(screen.getByText("关联训练任务")).toBeInTheDocument();
    });

    it("应该显示训练任务 ID", () => {
      renderWithProviders(<ModelDetailPage />);
      expect(screen.getByText("#10")).toBeInTheDocument();
    });

    it("应该显示检查点 ID", () => {
      renderWithProviders(<ModelDetailPage />);
      expect(screen.getByText("#5")).toBeInTheDocument();
    });

    it("无训练任务时不应该显示关联区域", () => {
      mockUseModel.mockReturnValue({
        data: { ...mockModel, training_job_id: null, checkpoint_id: null },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(<ModelDetailPage />);
      expect(screen.queryByText("关联训练任务")).not.toBeInTheDocument();
    });
  });

  describe("标签页", () => {
    it("应该渲染基本信息标签页", () => {
      renderWithProviders(<ModelDetailPage />);
      expect(screen.getByText("基本信息")).toBeInTheDocument();
    });

    it("应该渲染训练指标标签页", () => {
      renderWithProviders(<ModelDetailPage />);
      expect(screen.getByText("训练指标")).toBeInTheDocument();
    });

    it("应该渲染超参数标签页", () => {
      renderWithProviders(<ModelDetailPage />);
      expect(screen.getByText("超参数")).toBeInTheDocument();
    });
  });

  describe("操作按钮", () => {
    it("registered 状态应该显示归档按钮", () => {
      renderWithProviders(<ModelDetailPage />);
      expect(screen.getByRole("button", { name: /归档/ })).toBeInTheDocument();
    });

    it("registered 状态不应该显示恢复按钮", () => {
      renderWithProviders(<ModelDetailPage />);
      expect(
        screen.queryByRole("button", { name: /^恢复$/ }),
      ).not.toBeInTheDocument();
    });

    it("archived 状态应该显示恢复按钮", () => {
      mockUseModel.mockReturnValue({
        data: { ...mockModel, status: "archived" },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(<ModelDetailPage />);
      expect(screen.getByRole("button", { name: /恢复/ })).toBeInTheDocument();
    });

    it("training 状态不应该显示归档按钮", () => {
      mockUseModel.mockReturnValue({
        data: { ...mockModel, status: "training" },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(<ModelDetailPage />);
      expect(
        screen.queryByRole("button", { name: /^归档$/ }),
      ).not.toBeInTheDocument();
    });
  });

  describe("加载状态", () => {
    it("应该显示加载中提示", () => {
      mockUseModel.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(<ModelDetailPage />);
      expect(screen.getByText("加载中...")).toBeInTheDocument();
    });
  });

  describe("错误处理", () => {
    it("应该显示错误消息", () => {
      mockUseModel.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error("Not found"),
        refetch: vi.fn(),
      });

      renderWithProviders(<ModelDetailPage />);
      expect(screen.getByText("Not found")).toBeInTheDocument();
    });

    it("模型为空时应该显示不存在提示", () => {
      mockUseModel.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(<ModelDetailPage />);
      expect(screen.getByText("模型不存在")).toBeInTheDocument();
    });
  });
});
