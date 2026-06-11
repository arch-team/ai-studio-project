/**
 * CreateDatasetPage 单元测试
 *
 * 测试注册数据集页面的表单渲染、验证和提交
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { CreateDatasetPage } from "@features/datasets/pages";
import { useUIStore } from "@store/slices/uiSlice";

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// mock datasetApi 函数，避免 jsdom 环境中 AbortSignal 兼容性问题
vi.mock("@features/datasets/api/datasetApi", () => ({
  fetchDatasets: vi.fn(),
  fetchDataset: vi.fn(),
  createDataset: vi.fn(),
  updateDataset: vi.fn(),
  deleteDataset: vi.fn(),
  archiveDataset: vi.fn(),
  fetchDatasetVersions: vi.fn(),
  createDatasetVersion: vi.fn(),
}));

// eslint-disable-next-line no-restricted-imports -- 精确 mock 子模块以隔离 AbortSignal 兼容性问题
import { createDataset } from "@features/datasets/api/datasetApi";

describe("CreateDatasetPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // 设置 mock 返回值（用于提交成功场景）
    (createDataset as ReturnType<typeof vi.fn>).mockResolvedValue({
      id: 1,
      name: "test-dataset",
      status: "available",
      total_size_bytes: null,
      file_count: null,
      owner_id: 1,
      owner_username: "admin",
      training_jobs_count: 0,
      created_at: "2025-01-15T10:00:00Z",
      updated_at: "2025-01-15T10:00:00Z",
      last_accessed_at: null,
    });
  });

  describe("渲染", () => {
    it('应渲染页面标题"注册数据集"', () => {
      renderWithProviders(<CreateDatasetPage />);
      // Header variant="h1" 中的文本
      expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
        "注册数据集",
      );
    });

    it("应渲染面包屑导航", () => {
      renderWithProviders(<CreateDatasetPage />);
      // 面包屑经 PageLayout 同步到全局 UI Store，由 MainLayout 渲染
      const breadcrumbs = useUIStore.getState().breadcrumbs;
      expect(breadcrumbs.some((b) => b.text === "数据集")).toBe(true);
    });

    it("应渲染基本信息表单区域", () => {
      renderWithProviders(<CreateDatasetPage />);
      expect(screen.getByText("基本信息")).toBeInTheDocument();
    });

    it("应渲染存储配置表单区域", () => {
      renderWithProviders(<CreateDatasetPage />);
      expect(screen.getByText("存储配置")).toBeInTheDocument();
    });

    it("应渲染数据配置表单区域", () => {
      renderWithProviders(<CreateDatasetPage />);
      expect(screen.getByText("数据配置")).toBeInTheDocument();
    });

    it("应渲染标签和可见性表单区域", () => {
      renderWithProviders(<CreateDatasetPage />);
      expect(screen.getByText("标签和可见性")).toBeInTheDocument();
    });

    it("应渲染文件上传（可选）提示", () => {
      renderWithProviders(<CreateDatasetPage />);
      expect(screen.getByText("文件上传（可选）")).toBeInTheDocument();
      expect(
        screen.getByText("数据集创建成功后，可在详情页上传数据文件"),
      ).toBeInTheDocument();
    });

    it("应渲染提交和取消按钮", () => {
      renderWithProviders(<CreateDatasetPage />);
      // 按钮文本为"注册数据集"（不是页面标题）
      const buttons = screen.getAllByText("注册数据集");
      // 至少有 heading 和 button 两处
      expect(buttons.length).toBeGreaterThanOrEqual(2);
      expect(screen.getByText("取消")).toBeInTheDocument();
    });
  });

  describe("表单字段", () => {
    it("应渲染数据集名称输入框", () => {
      renderWithProviders(<CreateDatasetPage />);
      expect(screen.getByText("数据集名称")).toBeInTheDocument();
      expect(screen.getByPlaceholderText("my-dataset")).toBeInTheDocument();
    });

    it("应渲染版本输入框，默认值 v1", () => {
      renderWithProviders(<CreateDatasetPage />);
      expect(screen.getByText("版本")).toBeInTheDocument();
      expect(screen.getByDisplayValue("v1")).toBeInTheDocument();
    });

    it("应渲染描述文本框", () => {
      renderWithProviders(<CreateDatasetPage />);
      expect(screen.getByText("描述")).toBeInTheDocument();
      expect(screen.getByPlaceholderText("数据集描述...")).toBeInTheDocument();
    });

    it("应渲染存储类型下拉框", () => {
      renderWithProviders(<CreateDatasetPage />);
      expect(screen.getByText("存储类型")).toBeInTheDocument();
    });

    it("应渲染存储路径输入框", () => {
      renderWithProviders(<CreateDatasetPage />);
      expect(screen.getByText("存储路径")).toBeInTheDocument();
      expect(
        screen.getByPlaceholderText("s3://my-bucket/datasets/"),
      ).toBeInTheDocument();
    });

    it("应渲染数据类型下拉框", () => {
      renderWithProviders(<CreateDatasetPage />);
      expect(screen.getByText("数据类型")).toBeInTheDocument();
    });

    it("应渲染数据格式输入框", () => {
      renderWithProviders(<CreateDatasetPage />);
      expect(screen.getByText("数据格式")).toBeInTheDocument();
    });

    it("应渲染标签输入区域", () => {
      renderWithProviders(<CreateDatasetPage />);
      expect(screen.getByText("标签")).toBeInTheDocument();
      expect(screen.getByText("添加")).toBeInTheDocument();
    });

    it("应渲染可见性下拉框", () => {
      renderWithProviders(<CreateDatasetPage />);
      expect(screen.getByText("可见性")).toBeInTheDocument();
    });
  });

  describe("表单验证", () => {
    it("提交空表单应显示验证错误", async () => {
      renderWithProviders(<CreateDatasetPage />);

      // 点击提交按钮（非 heading 的"注册数据集"）
      const submitButtons = screen.getAllByText("注册数据集");
      const submitButton = submitButtons.find(
        (el) => el.closest("button") !== null,
      );
      if (submitButton) {
        fireEvent.click(submitButton);
      }

      await waitFor(() => {
        expect(screen.getByText("请输入数据集名称")).toBeInTheDocument();
      });
    });

    it("名称少于 3 字符应显示验证错误", async () => {
      renderWithProviders(<CreateDatasetPage />);

      const nameInput = screen.getByPlaceholderText("my-dataset");
      fireEvent.change(nameInput, { target: { value: "ab" } });

      const submitButtons = screen.getAllByText("注册数据集");
      const submitButton = submitButtons.find(
        (el) => el.closest("button") !== null,
      );
      if (submitButton) {
        fireEvent.click(submitButton);
      }

      await waitFor(() => {
        expect(screen.getByText("数据集名称至少 3 个字符")).toBeInTheDocument();
      });
    });
  });

  describe("导航", () => {
    it("点击取消按钮应导航回列表页", () => {
      renderWithProviders(<CreateDatasetPage />);

      fireEvent.click(screen.getByText("取消"));
      expect(mockNavigate).toHaveBeenCalledWith("/datasets");
    });

    it('面包屑"数据集"应指向列表页', () => {
      renderWithProviders(<CreateDatasetPage />);

      // 面包屑跳转由 MainLayout 的 BreadcrumbGroup 统一处理，
      // 此处验证 Store 中的面包屑项指向正确路径
      const breadcrumbs = useUIStore.getState().breadcrumbs;
      const datasetCrumb = breadcrumbs.find((b) => b.text === "数据集");
      expect(datasetCrumb?.href).toBe("/datasets");
    });
  });

  describe("标签管理", () => {
    it("点击添加按钮应添加标签", async () => {
      renderWithProviders(<CreateDatasetPage />);

      const tagInput = screen.getByPlaceholderText("输入标签...");
      fireEvent.change(tagInput, { target: { value: "my-tag" } });
      fireEvent.click(screen.getByText("添加"));

      await waitFor(() => {
        expect(screen.getByText("my-tag")).toBeInTheDocument();
      });
    });

    it("不应添加重复标签", async () => {
      renderWithProviders(<CreateDatasetPage />);

      const tagInput = screen.getByPlaceholderText("输入标签...");

      // 添加第一个标签
      fireEvent.change(tagInput, { target: { value: "tag1" } });
      fireEvent.click(screen.getByText("添加"));

      // 尝试添加重复标签
      fireEvent.change(tagInput, { target: { value: "tag1" } });
      fireEvent.click(screen.getByText("添加"));

      // 只应出现一次
      const tags = screen.getAllByText("tag1");
      expect(tags).toHaveLength(1);
    });

    it("不应添加空标签", () => {
      renderWithProviders(<CreateDatasetPage />);

      // 直接点击添加（不输入内容）
      fireEvent.click(screen.getByText("添加"));

      // TokenGroup 不应出现（没有标签被添加）
      // 使用 queryByText 检查 dismiss 按钮不存在来验证没有标签
      expect(screen.queryByLabelText("Remove")).not.toBeInTheDocument();
    });
  });

  describe("提交错误", () => {
    it("API 返回错误时应显示验证错误（未选择下拉框）", async () => {
      renderWithProviders(<CreateDatasetPage />);

      // 填写必填字段
      fireEvent.change(screen.getByPlaceholderText("my-dataset"), {
        target: { value: "existing-dataset" },
      });
      fireEvent.change(
        screen.getByPlaceholderText("s3://my-bucket/datasets/"),
        { target: { value: "s3://bucket/data" } },
      );

      // 由于未选择存储类型和数据类型下拉框，触发提交
      const submitButtons = screen.getAllByText("注册数据集");
      const submitButton = submitButtons.find(
        (el) => el.closest("button") !== null,
      );
      if (submitButton) {
        fireEvent.click(submitButton);
      }

      // 应触发存储类型验证错误
      await waitFor(() => {
        expect(screen.getByText("请选择存储类型")).toBeInTheDocument();
      });
    });
  });
});
