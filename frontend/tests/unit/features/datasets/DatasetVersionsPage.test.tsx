/**
 * DatasetVersionsPage 单元测试
 *
 * 测试数据集版本管理页面的渲染、版本列表、创建新版本
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { DatasetVersionsPage } from "@features/datasets/pages";
import type {
  DatasetDetail,
  DatasetVersionListResponse,
} from "@features/datasets/types";

// Mock useNavigate 和 useParams
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ id: "1" }),
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

import {
  fetchDataset,
  fetchDatasetVersions,
  createDatasetVersion,
} from "@features/datasets/api/datasetApi";

const mockDataset: DatasetDetail = {
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
  training_jobs_count: 3,
};

const mockVersions: DatasetVersionListResponse = {
  items: [
    {
      id: 1,
      dataset_id: 1,
      version: "v1",
      description: "初始版本",
      storage_uri: "s3://bucket/v1",
      total_size_bytes: 1024 * 1024,
      file_count: 50,
      created_at: "2025-01-15T10:00:00Z",
      created_by_username: "admin",
    },
    {
      id: 2,
      dataset_id: 1,
      version: "v2",
      description: "增量更新",
      storage_uri: "s3://bucket/v2",
      total_size_bytes: 2048 * 1024,
      file_count: 80,
      created_at: "2025-02-01T10:00:00Z",
      created_by_username: "admin",
    },
  ],
  total: 2,
};

describe("DatasetVersionsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // 设置 mock 返回值
    (fetchDataset as ReturnType<typeof vi.fn>).mockResolvedValue(mockDataset);
    (fetchDatasetVersions as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockVersions,
    );
    (createDatasetVersion as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockDataset,
    );
  });

  describe("渲染", () => {
    it("应渲染页面标题，包含数据集名称", async () => {
      renderWithProviders(<DatasetVersionsPage />);
      await waitFor(() => {
        expect(screen.getByText("测试数据集 - 版本历史")).toBeInTheDocument();
      });
    });

    it("应渲染面包屑导航", async () => {
      renderWithProviders(<DatasetVersionsPage />);
      await waitFor(() => {
        // Cloudscape BreadcrumbGroup 会为每个项渲染多个包含相同文本的 span
        const datasetItems = screen.getAllByText("数据集");
        expect(datasetItems.length).toBeGreaterThanOrEqual(1);
        expect(screen.getAllByText("测试数据集").length).toBeGreaterThanOrEqual(
          1,
        );
        expect(screen.getAllByText("版本历史").length).toBeGreaterThanOrEqual(
          1,
        );
      });
    });

    it('应渲染"刷新"按钮', async () => {
      renderWithProviders(<DatasetVersionsPage />);
      await waitFor(() => {
        expect(screen.getByText("刷新")).toBeInTheDocument();
      });
    });

    it('应渲染"创建新版本"按钮', async () => {
      renderWithProviders(<DatasetVersionsPage />);
      await waitFor(() => {
        // Cloudscape Modal header 即使 visible={false} 也会渲染，因此"创建新版本"可能出现多次
        const elements = screen.getAllByText("创建新版本");
        expect(elements.length).toBeGreaterThanOrEqual(1);
      });
    });

    it("应渲染版本列表标题和数量", async () => {
      renderWithProviders(<DatasetVersionsPage />);
      await waitFor(() => {
        expect(screen.getByText("版本列表")).toBeInTheDocument();
        expect(screen.getByText("(2)")).toBeInTheDocument();
      });
    });
  });

  describe("版本列表", () => {
    it("应显示版本号", async () => {
      renderWithProviders(<DatasetVersionsPage />);
      await waitFor(() => {
        expect(screen.getByText("v1")).toBeInTheDocument();
        expect(screen.getByText("v2")).toBeInTheDocument();
      });
    });

    it("应显示版本描述", async () => {
      renderWithProviders(<DatasetVersionsPage />);
      await waitFor(() => {
        expect(screen.getByText("初始版本")).toBeInTheDocument();
        expect(screen.getByText("增量更新")).toBeInTheDocument();
      });
    });

    it("应显示创建者", async () => {
      renderWithProviders(<DatasetVersionsPage />);
      await waitFor(() => {
        const adminCells = screen.getAllByText("admin");
        expect(adminCells.length).toBeGreaterThanOrEqual(1);
      });
    });
  });

  describe("创建新版本弹窗", () => {
    it('点击"创建新版本"应打开确认弹窗', async () => {
      renderWithProviders(<DatasetVersionsPage />);

      await waitFor(() => {
        expect(screen.getAllByText("创建新版本").length).toBeGreaterThanOrEqual(
          1,
        );
      });

      // 点击 primary 按钮（非 Modal header）
      const createButton = screen
        .getAllByText("创建新版本")
        .find((el) => el.closest("button") !== null);
      fireEvent.click(createButton!);

      await waitFor(() => {
        expect(screen.getByText("确认创建")).toBeInTheDocument();
      });
    });

    it("弹窗应显示数据集名称确认信息", async () => {
      renderWithProviders(<DatasetVersionsPage />);

      await waitFor(() => {
        expect(screen.getAllByText("创建新版本").length).toBeGreaterThanOrEqual(
          1,
        );
      });

      const createButton = screen
        .getAllByText("创建新版本")
        .find((el) => el.closest("button") !== null);
      fireEvent.click(createButton!);

      await waitFor(() => {
        // "测试数据集"在面包屑中也会出现多次，使用 getAllByText 验证
        expect(screen.getAllByText(/测试数据集/).length).toBeGreaterThanOrEqual(
          1,
        );
        expect(
          screen.getByText(/新版本将基于当前数据集的最新状态创建/),
        ).toBeInTheDocument();
      });
    });

    it("弹窗应包含取消和确认创建按钮", async () => {
      renderWithProviders(<DatasetVersionsPage />);

      await waitFor(() => {
        expect(screen.getAllByText("创建新版本").length).toBeGreaterThanOrEqual(
          1,
        );
      });

      const createButton = screen
        .getAllByText("创建新版本")
        .find((el) => el.closest("button") !== null);
      fireEvent.click(createButton!);

      await waitFor(() => {
        // 弹窗应包含"确认创建"和"取消"按钮
        expect(screen.getByText("确认创建")).toBeInTheDocument();
        expect(screen.getByText("取消")).toBeInTheDocument();
      });
    });
  });

  describe("加载状态", () => {
    it("应在数据加载时显示加载指示器", () => {
      // 让 fetchDataset 返回一个永不 resolve 的 Promise 模拟加载中
      (fetchDataset as ReturnType<typeof vi.fn>).mockReturnValue(
        new Promise(() => {}),
      );

      renderWithProviders(<DatasetVersionsPage />);
      expect(screen.getByText("加载中...")).toBeInTheDocument();
    });
  });

  describe("数据集不存在", () => {
    it("数据集不存在时应显示错误提示", async () => {
      (fetchDataset as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("数据集不存在"),
      );

      renderWithProviders(<DatasetVersionsPage />);

      await waitFor(() => {
        expect(screen.getByText("数据集不存在")).toBeInTheDocument();
      });
    });
  });

  describe("空版本列表", () => {
    it("无版本时应显示空状态", async () => {
      (fetchDatasetVersions as ReturnType<typeof vi.fn>).mockResolvedValue({
        items: [],
        total: 0,
      });

      renderWithProviders(<DatasetVersionsPage />);

      await waitFor(() => {
        expect(screen.getByText("暂无版本记录")).toBeInTheDocument();
      });
    });

    it("空版本列表应显示创建按钮", async () => {
      (fetchDatasetVersions as ReturnType<typeof vi.fn>).mockResolvedValue({
        items: [],
        total: 0,
      });

      renderWithProviders(<DatasetVersionsPage />);

      await waitFor(() => {
        expect(screen.getByText("创建第一个版本")).toBeInTheDocument();
      });
    });
  });

  describe("导航", () => {
    it('点击面包屑"数据集"应导航回列表页', async () => {
      renderWithProviders(<DatasetVersionsPage />);

      await waitFor(() => {
        const datasetItems = screen.getAllByText("数据集");
        expect(datasetItems.length).toBeGreaterThanOrEqual(1);
      });

      const breadcrumbItems = screen.getAllByText("数据集");
      fireEvent.click(breadcrumbItems[0]);
      expect(mockNavigate).toHaveBeenCalledWith("/datasets");
    });
  });
});
