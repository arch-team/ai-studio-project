/**
 * ModelTable 单元测试
 *
 * 测试模型表格组件的渲染、分页、选择和交互
 */

import { describe, it, expect, vi } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { ModelTable } from "@features/models/components";
import type { ModelSummary } from "@features/models/types";

// Mock 数据
const mockModels: ModelSummary[] = [
  {
    id: 1,
    model_name: "bert-base-v1",
    version: "v1.0.0",
    display_name: "BERT Base",
    owner_id: 100,
    training_job_id: 10,
    status: "registered",
    framework: "pytorch",
    metrics: { accuracy: 0.95 },
    tags: ["nlp"],
    created_at: "2024-01-15T10:00:00Z",
    registered_at: "2024-01-15T12:00:00Z",
  },
  {
    id: 2,
    model_name: "resnet50-v2",
    version: "v2.0.0",
    display_name: "ResNet50",
    owner_id: 101,
    training_job_id: null,
    status: "training",
    framework: "tensorflow",
    metrics: null,
    tags: null,
    created_at: "2024-02-01T08:00:00Z",
    registered_at: null,
  },
  {
    id: 3,
    model_name: "gpt-mini-v1",
    version: "v1.0.0",
    display_name: null,
    owner_id: 102,
    training_job_id: 20,
    status: "failed",
    framework: "jax",
    metrics: null,
    tags: null,
    created_at: "2024-03-01T08:00:00Z",
    registered_at: null,
  },
];

const defaultProps = {
  items: mockModels,
  loading: false,
  totalCount: 3,
  currentPage: 1,
  totalPages: 1,
  onPageChange: vi.fn(),
};

describe("ModelTable", () => {
  describe("基本渲染", () => {
    it("应该渲染表格", () => {
      renderWithProviders(<ModelTable {...defaultProps} />);
      expect(screen.getByRole("table")).toBeInTheDocument();
    });

    it("应该显示表头", () => {
      renderWithProviders(<ModelTable {...defaultProps} />);
      expect(screen.getByText("模型列表")).toBeInTheDocument();
    });

    it("应该显示总数", () => {
      renderWithProviders(<ModelTable {...defaultProps} />);
      expect(screen.getByText("(3)")).toBeInTheDocument();
    });

    it("应该显示模型名称列", () => {
      renderWithProviders(<ModelTable {...defaultProps} />);
      expect(screen.getByText("bert-base-v1")).toBeInTheDocument();
      expect(screen.getByText("resnet50-v2")).toBeInTheDocument();
    });

    it("应该显示版本列", () => {
      renderWithProviders(<ModelTable {...defaultProps} />);
      // 两个模型都有 v1.0.0 版本号，gpt-mini 和 bert-base 重复
      expect(screen.getAllByText("v1.0.0").length).toBeGreaterThan(0);
      expect(screen.getByText("v2.0.0")).toBeInTheDocument();
    });

    it("应该显示框架列（中文标签）", () => {
      renderWithProviders(<ModelTable {...defaultProps} />);
      expect(screen.getByText("PyTorch")).toBeInTheDocument();
      expect(screen.getByText("TensorFlow")).toBeInTheDocument();
      expect(screen.getByText("JAX")).toBeInTheDocument();
    });

    it("应该显示训练任务链接", () => {
      renderWithProviders(<ModelTable {...defaultProps} />);
      expect(screen.getByText("#10")).toBeInTheDocument();
      expect(screen.getByText("#20")).toBeInTheDocument();
    });

    it("无训练任务时显示横杠", () => {
      renderWithProviders(<ModelTable {...defaultProps} />);
      // resnet50-v2 没有 training_job_id，应显示 '-'
      const dashCells = screen.getAllByText("-");
      expect(dashCells.length).toBeGreaterThan(0);
    });
  });

  describe("加载状态", () => {
    it("应该显示加载状态", () => {
      renderWithProviders(
        <ModelTable {...defaultProps} items={[]} loading={true} />,
      );
      expect(screen.getByText("加载中...")).toBeInTheDocument();
    });
  });

  describe("空状态", () => {
    it("应该显示空状态提示", () => {
      renderWithProviders(
        <ModelTable {...defaultProps} items={[]} totalCount={0} />,
      );
      expect(screen.getByText("暂无模型")).toBeInTheDocument();
    });
  });

  describe("分页", () => {
    it("多页时应该显示分页组件", () => {
      renderWithProviders(<ModelTable {...defaultProps} totalPages={3} />);
      // Cloudscape Pagination 渲染 list
      expect(screen.getByRole("list")).toBeInTheDocument();
    });

    it("单页时不应该显示分页组件", () => {
      renderWithProviders(<ModelTable {...defaultProps} totalPages={1} />);
      // 单页时不应有分页数字按钮
      const paginationButtons = screen.queryAllByRole("button", {
        name: /^[0-9]+$/,
      });
      expect(paginationButtons.length).toBe(0);
    });
  });

  describe("点击交互", () => {
    it("点击模型名称应该触发 onModelClick", () => {
      const onModelClick = vi.fn();
      renderWithProviders(
        <ModelTable {...defaultProps} onModelClick={onModelClick} />,
      );

      fireEvent.click(screen.getByText("bert-base-v1"));
      expect(onModelClick).toHaveBeenCalledWith(1);
    });
  });

  describe("选择功能", () => {
    it("启用选择时应该渲染多选功能", () => {
      const onSelectionChange = vi.fn();
      renderWithProviders(
        <ModelTable
          {...defaultProps}
          selectable={true}
          selectedItems={[]}
          onSelectionChange={onSelectionChange}
        />,
      );
      // 多选模式下，Cloudscape Table 会渲染 checkbox
      const checkboxes = screen.getAllByRole("checkbox");
      expect(checkboxes.length).toBeGreaterThan(0);
    });

    it("未启用选择时不应该渲染多选功能", () => {
      renderWithProviders(<ModelTable {...defaultProps} selectable={false} />);
      const checkboxes = screen.queryAllByRole("checkbox");
      expect(checkboxes.length).toBe(0);
    });
  });
});
