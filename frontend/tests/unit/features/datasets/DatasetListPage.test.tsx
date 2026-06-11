/**
 * DatasetListPage 单元测试
 *
 * 测试数据集列表页面的渲染、过滤器、分页和导航
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { DatasetListPage } from "@features/datasets/pages";
import type {
  DatasetListResponse,
  DatasetSummary,
} from "@features/datasets/types";

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
import { fetchDatasets } from "@features/datasets/api/datasetApi";

// 创建 mock 数据集
function createMockDataset(
  overrides: Partial<DatasetSummary> = {},
): DatasetSummary {
  return {
    id: 1,
    name: "测试数据集",
    description: "测试描述",
    version: "v1",
    storage_type: "s3",
    storage_uri: "s3://bucket/path",
    total_size_bytes: 1024 * 1024,
    file_count: 100,
    dataset_type: "image",
    data_format: "imagenet",
    tags: ["test"],
    visibility: "public",
    owner_id: 1,
    owner_username: "admin",
    status: "available",
    created_at: "2025-01-15T10:00:00Z",
    updated_at: "2025-01-15T10:00:00Z",
    last_accessed_at: null,
    ...overrides,
  };
}

const mockDatasetList: DatasetListResponse = {
  items: [
    createMockDataset({ id: 1, name: "图像数据集", dataset_type: "image" }),
    createMockDataset({
      id: 2,
      name: "文本数据集",
      dataset_type: "text",
      status: "preparing",
    }),
  ],
  total: 2,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

describe("DatasetListPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // 设置 mock 返回值
    (fetchDatasets as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockDatasetList,
    );
  });

  describe("渲染", () => {
    it('应渲染页面标题"数据集管理"', async () => {
      renderWithProviders(<DatasetListPage />);
      expect(screen.getByText("数据集管理")).toBeInTheDocument();
    });

    it('应渲染"注册数据集"按钮', async () => {
      renderWithProviders(<DatasetListPage />);
      expect(screen.getByText("注册数据集")).toBeInTheDocument();
    });

    it('应渲染"刷新"按钮', async () => {
      renderWithProviders(<DatasetListPage />);
      expect(screen.getByText("刷新")).toBeInTheDocument();
    });

    it("应加载并显示数据集列表", async () => {
      renderWithProviders(<DatasetListPage />);
      await waitFor(() => {
        expect(screen.getByText("图像数据集")).toBeInTheDocument();
      });
      expect(screen.getByText("文本数据集")).toBeInTheDocument();
    });
  });

  describe("过滤器", () => {
    it("应渲染存储类型过滤器", async () => {
      renderWithProviders(<DatasetListPage />);
      expect(screen.getByText("全部存储类型")).toBeInTheDocument();
    });

    it("应渲染数据类型过滤器", async () => {
      renderWithProviders(<DatasetListPage />);
      expect(screen.getByText("全部数据类型")).toBeInTheDocument();
    });

    it("应渲染状态过滤器", async () => {
      renderWithProviders(<DatasetListPage />);
      expect(screen.getByText("全部状态")).toBeInTheDocument();
    });

    it("应渲染可见性过滤器", async () => {
      renderWithProviders(<DatasetListPage />);
      expect(screen.getByText("全部可见性")).toBeInTheDocument();
    });
  });

  describe("导航", () => {
    it('点击"注册数据集"应导航到创建页面', async () => {
      renderWithProviders(<DatasetListPage />);

      fireEvent.click(screen.getByText("注册数据集"));
      expect(mockNavigate).toHaveBeenCalledWith("/datasets/create");
    });

    it("点击数据集名称应导航到详情页", async () => {
      renderWithProviders(<DatasetListPage />);

      await waitFor(() => {
        expect(screen.getByText("图像数据集")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("图像数据集"));
      expect(mockNavigate).toHaveBeenCalledWith("/datasets/1");
    });
  });

  describe("错误状态", () => {
    it("API 错误时应显示错误提示", async () => {
      (fetchDatasets as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("服务器错误"),
      );

      renderWithProviders(<DatasetListPage />);

      await waitFor(() => {
        expect(screen.getByText(/加载失败/)).toBeInTheDocument();
      });
    });
  });

  describe("加载状态", () => {
    it("应在数据加载时显示加载指示", () => {
      // 让 fetchDatasets 返回一个永不 resolve 的 Promise 模拟加载中
      (fetchDatasets as ReturnType<typeof vi.fn>).mockReturnValue(
        new Promise(() => {}),
      );

      renderWithProviders(<DatasetListPage />);
      // 表格组件应显示加载文本
      expect(screen.getByText("加载中...")).toBeInTheDocument();
    });
  });
});
