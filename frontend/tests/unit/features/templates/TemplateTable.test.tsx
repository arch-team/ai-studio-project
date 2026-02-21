/**
 * TemplateTable Component Tests
 *
 * 测试模板列表表格组件
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { TemplateTable } from "@features/templates/components";
import type { JobTemplateSummary } from "@features/templates/types";

// Mock 数据
const mockTemplates: JobTemplateSummary[] = [
  {
    id: 1,
    name: "PyTorch DDP 模板",
    description: "分布式训练模板",
    visibility: "public",
    usage_count: 42,
    owner_id: 1,
    created_at: "2024-06-01T00:00:00Z",
  },
  {
    id: 2,
    name: "DeepSpeed 模板",
    description: "DeepSpeed 训练模板",
    visibility: "team",
    usage_count: 15,
    owner_id: 2,
    created_at: "2024-07-01T00:00:00Z",
  },
  {
    id: 3,
    name: "私有模板",
    visibility: "private",
    usage_count: 3,
    owner_id: 1,
    created_at: "2024-08-01T00:00:00Z",
  },
];

const defaultProps = {
  items: mockTemplates,
  loading: false,
  totalCount: 3,
  currentPage: 1,
  totalPages: 1,
  onPageChange: vi.fn(),
};

describe("TemplateTable", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("基本渲染", () => {
    it("should render table element", () => {
      renderWithProviders(<TemplateTable {...defaultProps} />);
      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    it("should render table header with count", () => {
      renderWithProviders(<TemplateTable {...defaultProps} />);
      expect(screen.getByText("(3)")).toBeInTheDocument();
    });

    it("should render template names", () => {
      renderWithProviders(<TemplateTable {...defaultProps} />);
      expect(screen.getByText("PyTorch DDP 模板")).toBeInTheDocument();
      expect(screen.getByText("DeepSpeed 模板")).toBeInTheDocument();
      expect(screen.getByText("私有模板")).toBeInTheDocument();
    });

    it("should render visibility badges", () => {
      renderWithProviders(<TemplateTable {...defaultProps} />);
      expect(screen.getByText("公开")).toBeInTheDocument();
      expect(screen.getByText("团队")).toBeInTheDocument();
      expect(screen.getByText("私有")).toBeInTheDocument();
    });

    it("should render usage count", () => {
      renderWithProviders(<TemplateTable {...defaultProps} />);
      expect(screen.getByText("42")).toBeInTheDocument();
      expect(screen.getByText("15")).toBeInTheDocument();
    });

    it("should render action buttons", () => {
      const handleUse = vi.fn();
      renderWithProviders(
        <TemplateTable {...defaultProps} onUseTemplate={handleUse} />,
      );
      const useButtons = screen.getAllByText("使用此模板");
      expect(useButtons.length).toBe(3);
    });
  });

  describe("加载状态", () => {
    it("should display loading text when loading", () => {
      renderWithProviders(
        <TemplateTable {...defaultProps} items={[]} loading={true} />,
      );
      expect(screen.getByText("加载中...")).toBeInTheDocument();
    });
  });

  describe("空状态", () => {
    it("should display empty state when no items", () => {
      renderWithProviders(
        <TemplateTable {...defaultProps} items={[]} totalCount={0} />,
      );
      expect(screen.getByText("暂无模板")).toBeInTheDocument();
    });
  });

  describe("交互事件", () => {
    it("should call onTemplateClick when clicking template name", () => {
      const handleClick = vi.fn();
      renderWithProviders(
        <TemplateTable {...defaultProps} onTemplateClick={handleClick} />,
      );
      fireEvent.click(screen.getByText("PyTorch DDP 模板"));
      expect(handleClick).toHaveBeenCalledWith(1);
    });

    it("should call onUseTemplate when clicking use button", () => {
      const handleUse = vi.fn();
      renderWithProviders(
        <TemplateTable {...defaultProps} onUseTemplate={handleUse} />,
      );
      const useButtons = screen.getAllByText("使用此模板");
      fireEvent.click(useButtons[0]);
      expect(handleUse).toHaveBeenCalledWith(1);
    });
  });

  describe("分页", () => {
    it("should render pagination when multiple pages", () => {
      renderWithProviders(<TemplateTable {...defaultProps} totalPages={3} />);
      // Cloudscape Pagination 渲染分页控件
      expect(screen.getByRole("list")).toBeInTheDocument();
    });

    it("should not render pagination when single page", () => {
      renderWithProviders(<TemplateTable {...defaultProps} totalPages={1} />);
      // 单页时不应有分页数字按钮
      const pageButtons = screen.queryAllByRole("button", { name: /^[0-9]+$/ });
      expect(pageButtons.length).toBe(0);
    });

    it("should call onPageChange when changing page", () => {
      const handlePageChange = vi.fn();
      renderWithProviders(
        <TemplateTable
          {...defaultProps}
          totalPages={3}
          onPageChange={handlePageChange}
        />,
      );
      // Cloudscape Pagination 渲染页码按钮，点击第 2 页
      const page2Button = screen.getByRole("button", { name: "2" });
      fireEvent.click(page2Button);
      expect(handlePageChange).toHaveBeenCalled();
    });
  });

  describe("无 totalCount", () => {
    it("should not display count when totalCount is undefined", () => {
      renderWithProviders(
        <TemplateTable {...defaultProps} totalCount={undefined} />,
      );
      expect(screen.queryByText("(3)")).not.toBeInTheDocument();
    });
  });
});
