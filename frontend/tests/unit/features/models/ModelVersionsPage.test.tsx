/**
 * ModelVersionsPage 单元测试
 *
 * 测试模型版本管理页面的渲染、对比和回滚功能
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent, waitFor } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { useUIStore } from "@store/slices/uiSlice";
import { ModelVersionsPage } from "@features/models/pages";
import type {
  ModelDetail,
  ModelVersionSummary,
  ModelVersionsResponse,
} from "@features/models/types";

// Mock 数据
const mockModel: ModelDetail = {
  id: 1,
  model_name: "bert-base",
  version: "v2.0.0",
  display_name: "BERT Base",
  description: "基于 BERT 的文本分类模型",
  owner_id: 100,
  training_job_id: 10,
  checkpoint_id: 5,
  model_uri: null,
  model_path: null,
  registry_arn: null,
  registry_status: null,
  metrics: null,
  hyperparameters: null,
  framework: "pytorch",
  framework_version: "2.0",
  status: "registered",
  size_bytes: null,
  model_format: null,
  tags: null,
  created_at: "2024-01-15T10:00:00Z",
  updated_at: "2024-01-20T14:00:00Z",
  registered_at: "2024-01-15T12:00:00Z",
  archived_at: null,
};

const mockVersions: ModelVersionSummary[] = [
  {
    id: 1,
    version: "v1.0.0",
    status: "registered",
    metrics: { accuracy: 0.85 },
    hyperparameters: { lr: 0.001 },
    created_at: "2024-01-01T10:00:00Z",
    registered_at: "2024-01-01T12:00:00Z",
  },
  {
    id: 2,
    version: "v2.0.0",
    status: "registered",
    metrics: { accuracy: 0.92 },
    hyperparameters: { lr: 0.0005 },
    created_at: "2024-02-01T10:00:00Z",
    registered_at: "2024-02-01T12:00:00Z",
  },
];

const mockVersionsResponse: ModelVersionsResponse = {
  model_name: "bert-base",
  versions: mockVersions,
  comparison: null,
};

// Mock hooks
const mockUseModel = vi.fn();
const mockUseModelVersions = vi.fn();
const mockUseRollbackModelVersion = vi.fn();

vi.mock("@features/models/api", () => ({
  useModel: () => mockUseModel(),
  useModelVersions: () => mockUseModelVersions(),
  useRollbackModelVersion: () => mockUseRollbackModelVersion(),
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

describe("ModelVersionsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseModel.mockReturnValue({
      data: mockModel,
      isLoading: false,
    });

    mockUseModelVersions.mockReturnValue({
      data: mockVersionsResponse,
      isLoading: false,
      refetch: vi.fn(),
    });

    mockUseRollbackModelVersion.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    });
  });

  describe("基本渲染", () => {
    it("应该渲染页面标题（包含模型名称）", () => {
      renderWithProviders(<ModelVersionsPage />);
      expect(screen.getByText(/bert-base.*版本历史/)).toBeInTheDocument();
    });

    it("应该渲染面包屑导航", () => {
      renderWithProviders(<ModelVersionsPage />);
      // 面包屑经 PageLayout 同步到全局 UI Store，由 MainLayout 渲染
      const breadcrumbs = useUIStore.getState().breadcrumbs;
      expect(breadcrumbs.some((b) => b.text === "模型管理")).toBe(true);
      expect(breadcrumbs.some((b) => b.text === "bert-base")).toBe(true);
      expect(breadcrumbs.some((b) => b.text === "版本历史")).toBe(true);
    });

    it("应该渲染刷新按钮", () => {
      renderWithProviders(<ModelVersionsPage />);
      expect(screen.getByRole("button", { name: /刷新/ })).toBeInTheDocument();
    });

    it("应该渲染返回详情按钮", () => {
      renderWithProviders(<ModelVersionsPage />);
      expect(
        screen.getByRole("button", { name: /返回详情/ }),
      ).toBeInTheDocument();
    });

    it("应该显示版本列表标题和计数", () => {
      renderWithProviders(<ModelVersionsPage />);
      expect(screen.getByText("版本列表")).toBeInTheDocument();
      expect(screen.getByText("(2)")).toBeInTheDocument();
    });
  });

  describe("版本表格", () => {
    it("应该显示版本号", () => {
      renderWithProviders(<ModelVersionsPage />);
      expect(screen.getByText("v1.0.0")).toBeInTheDocument();
      expect(screen.getByText("v2.0.0")).toBeInTheDocument();
    });

    it("应该显示对比按钮（默认禁用）", () => {
      renderWithProviders(<ModelVersionsPage />);
      const compareButton = screen.getByRole("button", { name: /对比版本/ });
      expect(compareButton).toBeInTheDocument();
    });
  });

  describe("加载状态", () => {
    it("模型加载中应该显示加载提示", () => {
      mockUseModel.mockReturnValue({
        data: undefined,
        isLoading: true,
      });

      renderWithProviders(<ModelVersionsPage />);
      expect(screen.getByText("加载中...")).toBeInTheDocument();
    });

    it("版本加载中应该显示加载提示", () => {
      mockUseModelVersions.mockReturnValue({
        data: undefined,
        isLoading: true,
        refetch: vi.fn(),
      });

      renderWithProviders(<ModelVersionsPage />);
      expect(screen.getByText("加载中...")).toBeInTheDocument();
    });
  });

  describe("错误处理", () => {
    it("模型不存在时应该在骨架内显示 InlineErrorState（非裸塌缩）", () => {
      mockUseModel.mockReturnValue({
        data: undefined,
        isLoading: false,
      });

      renderWithProviders(<ModelVersionsPage />);

      // InlineErrorState 标题"模型不存在"
      expect(screen.getByText("模型不存在")).toBeInTheDocument();
      // 错误态仍保留页面骨架：PageLayout 渲染固定标题"模型版本历史"
      expect(
        screen.getByRole("heading", { name: "模型版本历史" }),
      ).toBeInTheDocument();
      // 面包屑骨架仍同步到全局 UI Store（至少含"模型管理"），证明不是裸 Container 塌缩
      const { breadcrumbs } = useUIStore.getState();
      expect(breadcrumbs.some((b) => b.text === "模型管理")).toBe(true);
    });

    it("版本列表加载失败时应该显式报错并提供重试（不静默降级为空表）", () => {
      const refetch = vi.fn();
      mockUseModelVersions.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        refetch,
      });

      renderWithProviders(<ModelVersionsPage />);

      // F-006 核心：版本区出现"加载失败"而非空表静默
      expect(
        screen.getByText(/版本列表加载失败/),
      ).toBeInTheDocument();
      // 提供重试按钮，点击触发 refetch
      const retryButton = screen.getByRole("button", { name: "重试" });
      expect(retryButton).toBeInTheDocument();
      fireEvent.click(retryButton);
      expect(refetch).toHaveBeenCalled();
    });
  });

  describe("回滚功能", () => {
    it("应该为非当前版本显示回滚按钮", () => {
      renderWithProviders(<ModelVersionsPage />);
      expect(screen.getByText("回滚到此版本")).toBeInTheDocument();
    });

    it('当前版本应该显示"当前版本"标签', () => {
      renderWithProviders(<ModelVersionsPage />);
      expect(screen.getByText("当前版本")).toBeInTheDocument();
    });

    it("点击回滚按钮应该打开确认弹窗", async () => {
      renderWithProviders(<ModelVersionsPage />);

      const rollbackButton = screen.getByText("回滚到此版本");
      fireEvent.click(rollbackButton);

      await waitFor(() => {
        // Modal header 和确认按钮都包含"确认回滚"文本
        expect(screen.getAllByText("确认回滚").length).toBeGreaterThanOrEqual(
          1,
        );
      });
    });

    it("回滚确认弹窗应该包含警告提示", async () => {
      renderWithProviders(<ModelVersionsPage />);

      fireEvent.click(screen.getByText("回滚到此版本"));

      await waitFor(() => {
        expect(
          screen.getByText(/回滚操作会创建一个新的模型版本/),
        ).toBeInTheDocument();
      });
    });

    it("回滚确认弹窗应该有取消按钮", async () => {
      renderWithProviders(<ModelVersionsPage />);

      fireEvent.click(screen.getByText("回滚到此版本"));

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /取消/ }),
        ).toBeInTheDocument();
      });
    });

    it("回滚确认弹窗应该有确认回滚按钮", async () => {
      renderWithProviders(<ModelVersionsPage />);

      fireEvent.click(screen.getByText("回滚到此版本"));

      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: /确认回滚/ }),
        ).toBeInTheDocument();
      });
    });
  });

  describe("导航操作", () => {
    it("点击返回详情按钮应该导航到模型详情", () => {
      renderWithProviders(<ModelVersionsPage />);
      fireEvent.click(screen.getByRole("button", { name: /返回详情/ }));
      expect(mockNavigate).toHaveBeenCalledWith("/models/1");
    });
  });
});
