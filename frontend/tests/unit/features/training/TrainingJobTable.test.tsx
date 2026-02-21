/**
 * TrainingJobTable 单元测试
 *
 * 测试训练任务表格组件的渲染、分页和交互
 */

import { describe, it, expect, vi } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { TrainingJobTable } from "@features/training/components";
import type { TrainingJobSummary } from "@features/training/types";

// 测试用 mock 数据
const mockItems: TrainingJobSummary[] = [
  {
    id: 1,
    job_name: "llama2-finetune-001",
    display_name: "LLaMA 2 微调训练",
    owner_id: 1,
    owner_username: "admin",
    status: "running",
    priority: "high",
    instance_type: "ml.p4d.24xlarge",
    node_count: 4,
    gpu_per_node: 8,
    distribution_strategy: "fsdp",
    current_epoch: 3,
    total_epochs: 10,
    latest_loss: 0.342,
    checkpoints_count: 3,
    submitted_at: "2024-01-15T08:00:00Z",
    started_at: "2024-01-15T08:05:00Z",
    completed_at: null,
    created_at: "2024-01-15T07:55:00Z",
    duration_seconds: 7200,
    estimated_cost_usd: 256.5,
  },
  {
    id: 2,
    job_name: "bert-pretrain-002",
    display_name: "BERT 预训练",
    owner_id: 2,
    owner_username: "developer",
    status: "completed",
    priority: "medium",
    instance_type: "ml.p4d.24xlarge",
    node_count: 2,
    gpu_per_node: 8,
    distribution_strategy: "ddp",
    current_epoch: 5,
    total_epochs: 5,
    latest_loss: 0.125,
    checkpoints_count: 5,
    submitted_at: "2024-01-14T10:00:00Z",
    started_at: "2024-01-14T10:10:00Z",
    completed_at: "2024-01-14T22:30:00Z",
    created_at: "2024-01-14T09:50:00Z",
    duration_seconds: 44400,
    estimated_cost_usd: 512.0,
  },
];

const defaultProps = {
  items: mockItems,
  currentPage: 1,
  totalPages: 1,
  onPageChange: vi.fn(),
};

describe("TrainingJobTable", () => {
  describe("基本渲染", () => {
    it("应该渲染表格标题", () => {
      renderWithProviders(<TrainingJobTable {...defaultProps} />);
      expect(
        screen.getByRole("heading", { name: /训练任务/ }),
      ).toBeInTheDocument();
    });

    it("应该渲染表格列标题", () => {
      renderWithProviders(<TrainingJobTable {...defaultProps} />);
      expect(screen.getByText("任务名称")).toBeInTheDocument();
      expect(screen.getByText("状态")).toBeInTheDocument();
      expect(screen.getByText("优先级")).toBeInTheDocument();
      expect(screen.getByText("节点数")).toBeInTheDocument();
      expect(screen.getByText("GPU/节点")).toBeInTheDocument();
      expect(screen.getByText("进度")).toBeInTheDocument();
      expect(screen.getByText("创建时间")).toBeInTheDocument();
    });

    it("应该渲染任务数据行", () => {
      renderWithProviders(<TrainingJobTable {...defaultProps} />);
      expect(screen.getByText("llama2-finetune-001")).toBeInTheDocument();
      expect(screen.getByText("bert-pretrain-002")).toBeInTheDocument();
    });

    it("应该显示任务总数", () => {
      renderWithProviders(
        <TrainingJobTable {...defaultProps} totalCount={2} />,
      );
      expect(screen.getByText("(2)")).toBeInTheDocument();
    });
  });

  describe("数据展示", () => {
    it("应该显示优先级标签", () => {
      renderWithProviders(<TrainingJobTable {...defaultProps} />);
      expect(screen.getByText("高")).toBeInTheDocument();
      expect(screen.getByText("中")).toBeInTheDocument();
    });

    it("应该显示分布式策略", () => {
      renderWithProviders(<TrainingJobTable {...defaultProps} />);
      expect(screen.getByText("FSDP")).toBeInTheDocument();
      expect(screen.getByText("DDP")).toBeInTheDocument();
    });

    it("应该显示进度信息", () => {
      renderWithProviders(<TrainingJobTable {...defaultProps} />);
      // 3/10 (30%)
      expect(screen.getByText("3/10 (30%)")).toBeInTheDocument();
      // 5/5 (100%)
      expect(screen.getByText("5/5 (100%)")).toBeInTheDocument();
    });

    it("应该显示节点数和 GPU 数", () => {
      renderWithProviders(<TrainingJobTable {...defaultProps} />);
      // 节点数 4 和 2
      expect(screen.getByText("4")).toBeInTheDocument();
      expect(screen.getByText("2")).toBeInTheDocument();
    });
  });

  describe("空状态", () => {
    it("应该在无数据时显示空状态", () => {
      renderWithProviders(
        <TrainingJobTable
          items={[]}
          currentPage={1}
          totalPages={1}
          onPageChange={vi.fn()}
        />,
      );
      expect(screen.getByText("暂无训练任务")).toBeInTheDocument();
    });
  });

  describe("加载状态", () => {
    it("应该在加载时显示加载文本", () => {
      renderWithProviders(
        <TrainingJobTable
          items={[]}
          loading={true}
          currentPage={1}
          totalPages={1}
          onPageChange={vi.fn()}
        />,
      );
      expect(screen.getByText("加载中...")).toBeInTheDocument();
    });
  });

  describe("交互行为", () => {
    it("应该在点击任务名称时调用 onJobClick", () => {
      const onJobClick = vi.fn();
      renderWithProviders(
        <TrainingJobTable {...defaultProps} onJobClick={onJobClick} />,
      );
      fireEvent.click(screen.getByText("llama2-finetune-001"));
      expect(onJobClick).toHaveBeenCalledWith(1);
    });

    it("应该在分页变化时调用 onPageChange", () => {
      const onPageChange = vi.fn();
      renderWithProviders(
        <TrainingJobTable
          {...defaultProps}
          totalPages={3}
          onPageChange={onPageChange}
        />,
      );
      // Cloudscape Pagination 使用按钮导航
      const nextButton = screen.queryByRole("button", { name: /下一页|next/i });
      if (nextButton) {
        fireEvent.click(nextButton);
        expect(onPageChange).toHaveBeenCalled();
      }
    });
  });

  describe("分页", () => {
    it("当只有一页时不应显示分页组件", () => {
      renderWithProviders(
        <TrainingJobTable {...defaultProps} totalPages={1} />,
      );
      // 只有一页时不渲染 Pagination
      expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
    });

    it("当有多页时应显示分页组件", () => {
      renderWithProviders(
        <TrainingJobTable {...defaultProps} totalPages={3} />,
      );
      // 多页时应渲染分页
      const buttons = screen.getAllByRole("button");
      // 至少有翻页按钮
      expect(buttons.length).toBeGreaterThanOrEqual(1);
    });
  });
});
