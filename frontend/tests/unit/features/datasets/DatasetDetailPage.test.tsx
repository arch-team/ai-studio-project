/**
 * DatasetDetailPage 单元测试
 *
 * 重点覆盖四态完整性（F-023）：
 * - loading 态：稳定标题 + Spinner
 * - error 态：保留 PageLayout 骨架（标题"数据集详情" + 面包屑）+ InlineErrorState（标题"加载失败" + "重试"按钮）
 * - !dataset 态：保留骨架 + "数据集不存在"，不提供重试
 * - default 态：渲染实体内容
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { DatasetDetailPage } from "@features/datasets/pages";
import { useUIStore } from "@store/slices/uiSlice";
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

// eslint-disable-next-line no-restricted-imports -- 精确 mock 子模块以隔离 AbortSignal 兼容性问题
import {
  fetchDataset,
  fetchDatasetVersions,
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
  ],
  total: 1,
};

describe("DatasetDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (fetchDataset as ReturnType<typeof vi.fn>).mockResolvedValue(mockDataset);
    (fetchDatasetVersions as ReturnType<typeof vi.fn>).mockResolvedValue(
      mockVersions,
    );
  });

  describe("default 态", () => {
    it("应渲染数据集名称作为标题", async () => {
      renderWithProviders(<DatasetDetailPage />);
      await waitFor(() => {
        // 标题为实体名，面包屑中也含实体名，使用 getAllByText
        expect(screen.getAllByText("测试数据集").length).toBeGreaterThanOrEqual(
          1,
        );
      });
    });

    it("应渲染基本信息区块", async () => {
      renderWithProviders(<DatasetDetailPage />);
      await waitFor(() => {
        expect(screen.getByText("基本信息")).toBeInTheDocument();
      });
    });
  });

  describe("loading 态", () => {
    it("应在数据加载时显示加载指示器", () => {
      // 让 fetchDataset 返回永不 resolve 的 Promise 模拟加载中
      (fetchDataset as ReturnType<typeof vi.fn>).mockReturnValue(
        new Promise(() => {}),
      );

      renderWithProviders(<DatasetDetailPage />);
      expect(screen.getByText("加载中...")).toBeInTheDocument();
    });
  });

  describe("error 态（F-023 核心）", () => {
    beforeEach(() => {
      (fetchDataset as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("网络异常"),
      );
    });

    it('应保留稳定标题"数据集详情"（PageLayout 骨架不塌缩）', async () => {
      renderWithProviders(<DatasetDetailPage />);
      await waitFor(() => {
        expect(screen.getByText("数据集详情")).toBeInTheDocument();
      });
    });

    it('应显示"加载失败"标题', async () => {
      renderWithProviders(<DatasetDetailPage />);
      await waitFor(() => {
        expect(screen.getByText("加载失败")).toBeInTheDocument();
      });
    });

    it('应显示"重试"按钮（提供恢复路径）', async () => {
      renderWithProviders(<DatasetDetailPage />);
      await waitFor(() => {
        expect(
          screen.getByRole("button", { name: "重试" }),
        ).toBeInTheDocument();
      });
    });

    it("应将面包屑同步到 UI Store（骨架保留）", async () => {
      renderWithProviders(<DatasetDetailPage />);
      await waitFor(() => {
        const breadcrumbs = useUIStore.getState().breadcrumbs;
        expect(breadcrumbs.some((b) => b.text === "数据集")).toBe(true);
      });
    });

    it("应展示错误 message", async () => {
      renderWithProviders(<DatasetDetailPage />);
      await waitFor(() => {
        expect(screen.getByText("网络异常")).toBeInTheDocument();
      });
    });
  });

  describe("数据集不存在态", () => {
    it('数据集为空时应显示"数据集不存在"且保留骨架', async () => {
      // 主资源解析为 null（成功但无数据）
      (fetchDataset as ReturnType<typeof vi.fn>).mockResolvedValue(null);

      renderWithProviders(<DatasetDetailPage />);
      await waitFor(() => {
        expect(screen.getByText("数据集不存在")).toBeInTheDocument();
        // 仍保留稳定标题
        expect(screen.getByText("数据集详情")).toBeInTheDocument();
      });
    });

    it("数据集为空时不应提供重试按钮", async () => {
      (fetchDataset as ReturnType<typeof vi.fn>).mockResolvedValue(null);

      renderWithProviders(<DatasetDetailPage />);
      await waitFor(() => {
        expect(screen.getByText("数据集不存在")).toBeInTheDocument();
      });
      expect(
        screen.queryByRole("button", { name: "重试" }),
      ).not.toBeInTheDocument();
    });
  });
});
