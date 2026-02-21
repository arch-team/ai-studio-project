/**
 * DatasetTable 单元测试
 *
 * 测试数据集表格组件的渲染、分页、空状态和数据展示
 */

import { describe, it, expect, vi } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { DatasetTable } from "@features/datasets/components";
import type { DatasetSummary } from "@features/datasets/types";

// 构造 mock 数据
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
    total_size_bytes: 1024 * 1024 * 500, // 500 MB
    file_count: 1000,
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

const mockItems: DatasetSummary[] = [
  createMockDataset({
    id: 1,
    name: "训练图像集",
    dataset_type: "image",
    status: "available",
  }),
  createMockDataset({
    id: 2,
    name: "文本语料库",
    dataset_type: "text",
    status: "preparing",
    storage_type: "fsx",
  }),
  createMockDataset({
    id: 3,
    name: "归档数据",
    dataset_type: "tabular",
    status: "archived",
    visibility: "private",
  }),
];

describe("DatasetTable", () => {
  const defaultProps = {
    items: mockItems,
    currentPage: 1,
    totalPages: 3,
    onPageChange: vi.fn(),
  };

  describe("渲染", () => {
    it("应渲染表格", () => {
      renderWithProviders(<DatasetTable {...defaultProps} />);
      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    it('应渲染表头"数据集"', () => {
      renderWithProviders(<DatasetTable {...defaultProps} />);
      expect(screen.getByText("数据集")).toBeInTheDocument();
    });

    it("应渲染数据集名称", () => {
      renderWithProviders(<DatasetTable {...defaultProps} />);
      expect(screen.getByText("训练图像集")).toBeInTheDocument();
      expect(screen.getByText("文本语料库")).toBeInTheDocument();
      expect(screen.getByText("归档数据")).toBeInTheDocument();
    });

    it("应渲染数据集状态标签", () => {
      renderWithProviders(<DatasetTable {...defaultProps} />);
      expect(screen.getByText("可用")).toBeInTheDocument();
      expect(screen.getByText("准备中")).toBeInTheDocument();
      expect(screen.getByText("已归档")).toBeInTheDocument();
    });

    it("应渲染数据类型标签", () => {
      renderWithProviders(<DatasetTable {...defaultProps} />);
      expect(screen.getByText("图像")).toBeInTheDocument();
      expect(screen.getByText("文本")).toBeInTheDocument();
      expect(screen.getByText("表格")).toBeInTheDocument();
    });

    it("应渲染存储类型标签", () => {
      renderWithProviders(<DatasetTable {...defaultProps} />);
      // 2 项使用 s3 (训练图像集、归档数据)，1 项使用 fsx (文本语料库)
      const s3Labels = screen.getAllByText("Amazon S3");
      expect(s3Labels.length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("FSx for Lustre")).toBeInTheDocument();
    });

    it("应渲染可见性标签", () => {
      renderWithProviders(<DatasetTable {...defaultProps} />);
      expect(screen.getAllByText("公开").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("私有")).toBeInTheDocument();
    });

    it("应渲染总数量", () => {
      renderWithProviders(<DatasetTable {...defaultProps} totalCount={100} />);
      expect(screen.getByText("(100)")).toBeInTheDocument();
    });
  });

  describe("文件大小格式化", () => {
    it("应格式化 MB 大小", () => {
      const items = [
        createMockDataset({ total_size_bytes: 1024 * 1024 * 500 }),
      ];
      renderWithProviders(<DatasetTable {...defaultProps} items={items} />);
      expect(screen.getByText("500.00 MB")).toBeInTheDocument();
    });

    it('应显示 null 大小为 "-"', () => {
      const items = [createMockDataset({ total_size_bytes: null })];
      renderWithProviders(<DatasetTable {...defaultProps} items={items} />);
      // '-' 会出现在大小列和可能的文件数列
      const cells = screen.getAllByText("-");
      expect(cells.length).toBeGreaterThanOrEqual(1);
    });

    it('应格式化 0 字节为 "0 B"', () => {
      const items = [createMockDataset({ total_size_bytes: 0 })];
      renderWithProviders(<DatasetTable {...defaultProps} items={items} />);
      expect(screen.getByText("0 B")).toBeInTheDocument();
    });

    it("应格式化 GB 大小", () => {
      const items = [
        createMockDataset({ total_size_bytes: 1024 * 1024 * 1024 * 2.5 }),
      ];
      renderWithProviders(<DatasetTable {...defaultProps} items={items} />);
      expect(screen.getByText("2.50 GB")).toBeInTheDocument();
    });
  });

  describe("文件数格式化", () => {
    it("应格式化文件数量", () => {
      const items = [createMockDataset({ file_count: 1000 })];
      renderWithProviders(<DatasetTable {...defaultProps} items={items} />);
      expect(screen.getByText("1,000")).toBeInTheDocument();
    });

    it('应显示 null 文件数为 "-"', () => {
      const items = [createMockDataset({ file_count: null })];
      renderWithProviders(<DatasetTable {...defaultProps} items={items} />);
      const cells = screen.getAllByText("-");
      expect(cells.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("加载状态", () => {
    it("应显示加载状态", () => {
      renderWithProviders(
        <DatasetTable {...defaultProps} items={[]} loading={true} />,
      );
      expect(screen.getByText("加载中...")).toBeInTheDocument();
    });
  });

  describe("空状态", () => {
    it("应显示空状态提示", () => {
      renderWithProviders(
        <DatasetTable {...defaultProps} items={[]} totalPages={1} />,
      );
      expect(screen.getByText("暂无数据集")).toBeInTheDocument();
      expect(screen.getByText("尚未创建任何数据集")).toBeInTheDocument();
    });
  });

  describe("分页", () => {
    it("多页时应渲染分页组件", () => {
      renderWithProviders(<DatasetTable {...defaultProps} totalPages={3} />);
      // Cloudscape Pagination 渲染包含分页按钮的列表
      const paginationList = screen.getByRole("list");
      expect(paginationList).toBeInTheDocument();
    });

    it("单页时不应渲染分页组件", () => {
      renderWithProviders(<DatasetTable {...defaultProps} totalPages={1} />);
      expect(screen.queryByRole("list")).not.toBeInTheDocument();
    });
  });

  describe("交互", () => {
    it("点击数据集名称应调用 onDatasetClick", () => {
      const onDatasetClick = vi.fn();
      renderWithProviders(
        <DatasetTable {...defaultProps} onDatasetClick={onDatasetClick} />,
      );

      fireEvent.click(screen.getByText("训练图像集"));
      expect(onDatasetClick).toHaveBeenCalledWith(1);
    });
  });
});
