/**
 * DatasetVersionsPage 单元测试
 *
 * 测试数据集版本管理页面的渲染、版本列表、创建新版本
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { DatasetVersionsPage } from "@features/datasets/pages";
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
        // 面包屑经 PageLayout 同步到全局 UI Store，由 MainLayout 渲染
        const breadcrumbs = useUIStore.getState().breadcrumbs;
        expect(breadcrumbs.some((b) => b.text === "数据集")).toBe(true);
        expect(breadcrumbs.some((b) => b.text === "测试数据集")).toBe(true);
        expect(breadcrumbs.some((b) => b.text === "版本历史")).toBe(true);
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

  describe("数据集加载失败", () => {
    it("数据集加载失败时应显示错误提示", async () => {
      (fetchDataset as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("数据集不存在"),
      );

      renderWithProviders(<DatasetVersionsPage />);

      await waitFor(() => {
        expect(screen.getByText("数据集不存在")).toBeInTheDocument();
      });
    });

    it("数据集加载失败时应渲染 InlineErrorState（标题+重试），而非裸文本块", async () => {
      // fetchDataset 拒绝 → datasetError 为真 → "加载失败"态（带重试）
      (fetchDataset as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("数据集不存在"),
      );

      renderWithProviders(<DatasetVersionsPage />);

      // InlineErrorState 标题"加载失败" + 错误消息 + 重试按钮（裸 Box 路径无重试）
      await waitFor(() => {
        expect(screen.getByText("加载失败")).toBeInTheDocument();
        expect(screen.getByText("数据集不存在")).toBeInTheDocument();
        expect(screen.getByText("重试")).toBeInTheDocument();
      });
      // 仍保留页面骨架（面包屑出口同步到 UI Store），不裸 Container 塌缩
      expect(useUIStore.getState().breadcrumbs.length).toBeGreaterThan(0);
    });
  });

  describe("版本列表加载失败", () => {
    it("版本列表加载失败时应显式报错并提供重试，而非静默降级为空表", async () => {
      // 主资源（数据集）正常，仅子资源（版本列表）加载失败
      (fetchDatasetVersions as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("网络错误"),
      );

      renderWithProviders(<DatasetVersionsPage />);

      await waitFor(() => {
        // 显式错误提示（InlineErrorState message）
        expect(screen.getByText("版本列表加载失败。")).toBeInTheDocument();
        // 提供重试入口
        expect(screen.getByText("重试")).toBeInTheDocument();
      });

      // 错误态必须抑制 empty 态：不得出现"暂无版本记录"+"创建第一个版本" CTA
      expect(screen.queryByText("暂无版本记录")).not.toBeInTheDocument();
      expect(screen.queryByText("创建第一个版本")).not.toBeInTheDocument();
    });

    it("版本列表加载失败时仍保留页面骨架（标题与刷新按钮）", async () => {
      (fetchDatasetVersions as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error("网络错误"),
      );

      renderWithProviders(<DatasetVersionsPage />);

      await waitFor(() => {
        // 数据集加载成功 → 标题正常渲染，错误只发生在版本子资源
        expect(screen.getByText("测试数据集 - 版本历史")).toBeInTheDocument();
        expect(screen.getByText("刷新")).toBeInTheDocument();
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
    it('面包屑"数据集"应指向列表页', async () => {
      renderWithProviders(<DatasetVersionsPage />);

      // 面包屑跳转由 MainLayout 的 BreadcrumbGroup 统一处理，
      // 此处验证 Store 中的面包屑项指向正确路径
      await waitFor(() => {
        const breadcrumbs = useUIStore.getState().breadcrumbs;
        const datasetCrumb = breadcrumbs.find((b) => b.text === "数据集");
        expect(datasetCrumb?.href).toBe("/datasets");
      });
    });
  });
});
