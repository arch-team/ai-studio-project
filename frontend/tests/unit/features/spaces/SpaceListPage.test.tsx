/**
 * SpaceListPage 单元测试
 *
 * 测试在线开发环境列表页面的渲染、过滤、操作和删除流程
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor, within, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { SpaceListPage } from "@features/spaces/pages";
import type { SpaceListResponse } from "@features/spaces/types";

// mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// mock spaces api hooks
const mockUseSpaces = vi.fn();
const mockStartMutate = vi.fn();
const mockStopMutate = vi.fn();
const mockDeleteMutate = vi.fn();
const mockOpenMutate = vi.fn();

vi.mock("@features/spaces/api", () => ({
  useSpaces: (...args: unknown[]) => mockUseSpaces(...args),
  useStartSpace: () => ({
    mutate: mockStartMutate,
    isPending: false,
  }),
  useStopSpace: () => ({
    mutate: mockStopMutate,
    isPending: false,
  }),
  useDeleteSpace: () => ({
    mutate: mockDeleteMutate,
    isPending: false,
  }),
  useOpenSpace: () => ({
    mutate: mockOpenMutate,
    isPending: false,
  }),
}));

// 模拟空间列表数据
const mockSpaceListResponse: SpaceListResponse = {
  items: [
    {
      id: 1,
      name: "dev-space-1",
      description: "开发空间 1",
      space_type: "jupyter",
      status: "running",
      instance_type: "ml.g5.xlarge",
      instance_size: "small",
      owner_id: 1,
      owner_username: "user1",
      url: "https://jupyter.example.com/1",
      created_at: "2025-01-01T00:00:00Z",
      started_at: "2025-01-01T01:00:00Z",
      stopped_at: null,
      last_activity_at: "2025-01-01T02:00:00Z",
    },
    {
      id: 2,
      name: "dev-space-2",
      description: "开发空间 2",
      space_type: "vscode",
      status: "stopped",
      instance_type: "ml.g5.2xlarge",
      instance_size: "medium",
      owner_id: 1,
      owner_username: "user1",
      url: null,
      created_at: "2025-01-02T00:00:00Z",
      started_at: null,
      stopped_at: "2025-01-02T05:00:00Z",
      last_activity_at: null,
    },
    {
      id: 3,
      name: "dev-space-3",
      description: null,
      space_type: "jupyter",
      status: "failed",
      instance_type: "ml.g5.xlarge",
      instance_size: "small",
      owner_id: 2,
      owner_username: "user2",
      url: null,
      created_at: "2025-01-03T00:00:00Z",
      started_at: null,
      stopped_at: null,
      last_activity_at: null,
    },
  ],
  total: 3,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

describe("SpaceListPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // 默认: 成功返回数据
    mockUseSpaces.mockReturnValue({
      data: mockSpaceListResponse,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    // 设置 delete mutate 自动触发 onSuccess
    mockDeleteMutate.mockImplementation(
      (_id: number, options?: { onSuccess?: () => void }) => {
        options?.onSuccess?.();
      },
    );
  });

  describe("基本渲染", () => {
    it("应该渲染页面标题", () => {
      renderWithProviders(<SpaceListPage />);
      // Header 组件渲染 h1 标题
      const header = screen.getByRole("heading", {
        name: /在线开发环境/i,
        level: 1,
      });
      expect(header).toBeInTheDocument();
    });

    it("应该渲染创建按钮", () => {
      renderWithProviders(<SpaceListPage />);
      const createButton = screen.getByRole("button", {
        name: /创建开发空间/i,
      });
      expect(createButton).toBeInTheDocument();
    });

    it("应该渲染刷新按钮", () => {
      renderWithProviders(<SpaceListPage />);
      const refreshButton = screen.getByRole("button", { name: /刷新/i });
      expect(refreshButton).toBeInTheDocument();
    });

    it("应该显示空间列表数据", () => {
      renderWithProviders(<SpaceListPage />);

      // Cloudscape Table 将名称渲染为链接
      expect(screen.getByText("dev-space-1")).toBeInTheDocument();
      expect(screen.getByText("dev-space-2")).toBeInTheDocument();
      expect(screen.getByText("dev-space-3")).toBeInTheDocument();
    });

    it("应该显示总数计数", () => {
      renderWithProviders(<SpaceListPage />);
      // Header 的 counter 属性渲染为 (total) 格式
      expect(screen.getByText(/\(3\)/)).toBeInTheDocument();
    });

    it("应该显示 IDE 类型标签", () => {
      renderWithProviders(<SpaceListPage />);

      // IDE 类型标签在 Table 的 cell 中渲染
      const jupyterLabCells = screen.getAllByText("JupyterLab");
      expect(jupyterLabCells.length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("VS Code Server")).toBeInTheDocument();
    });

    it("应该显示状态徽章", () => {
      renderWithProviders(<SpaceListPage />);

      // StatusIndicator 组件渲染状态文本
      expect(screen.getByText("运行中")).toBeInTheDocument();
      expect(screen.getByText("已停止")).toBeInTheDocument();
      expect(screen.getByText("失败")).toBeInTheDocument();
    });
  });

  describe("空数据状态", () => {
    it("列表为空时应该显示空状态提示", () => {
      mockUseSpaces.mockReturnValue({
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 20,
          total_pages: 0,
        },
        isLoading: false,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(<SpaceListPage />);
      // Table 的 empty 属性渲染空状态组件
      expect(screen.getByText("暂无开发空间")).toBeInTheDocument();
      // 空状态中的创建按钮也应该存在
      const createButtons = screen.getAllByRole("button", {
        name: /创建开发空间/i,
      });
      expect(createButtons.length).toBeGreaterThan(0);
    });
  });

  describe("错误状态", () => {
    it("加载失败时应该显示错误信息", () => {
      mockUseSpaces.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: { message: "服务器错误" },
        refetch: vi.fn(),
      });

      renderWithProviders(<SpaceListPage />);
      expect(screen.getByText(/加载失败/)).toBeInTheDocument();
    });
  });

  describe("导航操作", () => {
    it("点击创建按钮应该导航到创建页面", () => {
      renderWithProviders(<SpaceListPage />);

      // 点击头部的创建按钮
      const createButton = screen.getByRole("button", {
        name: /创建开发空间/i,
      });
      fireEvent.click(createButton);
      expect(mockNavigate).toHaveBeenCalledWith("/spaces/create");
    });
  });

  describe("操作按钮", () => {
    it("运行中的空间应该显示停止按钮", () => {
      renderWithProviders(<SpaceListPage />);
      // 使用 getByRole 查找按钮
      const stopButton = screen.getByRole("button", { name: /停止/i });
      expect(stopButton).toBeInTheDocument();
    });

    it("运行中且有 URL 的空间应该显示打开 IDE 按钮", () => {
      renderWithProviders(<SpaceListPage />);
      // 使用 getByRole 查找按钮
      const openButton = screen.getByRole("button", { name: /打开 IDE/i });
      expect(openButton).toBeInTheDocument();
    });

    it("已停止的空间应该显示启动和删除按钮", () => {
      renderWithProviders(<SpaceListPage />);
      // 使用 getByRole 查找按钮
      const startButton = screen.getByRole("button", { name: /启动/i });
      expect(startButton).toBeInTheDocument();
      // 删除按钮应该有 2 个（stopped 和 failed 状态）
      const deleteButtons = screen.getAllByRole("button", { name: /删除/i });
      expect(deleteButtons.length).toBeGreaterThanOrEqual(1);
    });

    it("失败的空间应该显示删除按钮", () => {
      renderWithProviders(<SpaceListPage />);

      // stopped (id=2) 和 failed (id=3) 都应该有删除按钮
      // 注意：空状态中也有一个"创建开发空间"按钮，但不影响删除按钮计数
      const deleteButtons = screen.getAllByRole("button", { name: /删除/i });
      // 至少应该有 2 个删除按钮
      expect(deleteButtons.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe("删除确认弹窗", () => {
    it("点击删除应该显示确认弹窗", async () => {
      renderWithProviders(<SpaceListPage />);

      // 使用 getByRole 获取删除按钮
      const deleteButtons = screen.getAllByRole("button", { name: /删除/i });
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        // Modal 的 header 和按钮都显示"确认删除"，使用 getAllByText 查询
        const confirmTexts = screen.getAllByText("确认删除");
        expect(confirmTexts.length).toBeGreaterThanOrEqual(1);
      });
      // Modal 的内容包含警告文本
      expect(screen.getByText(/此操作不可撤销/)).toBeInTheDocument();
    });

    it("点击取消应该关闭弹窗", async () => {
      renderWithProviders(<SpaceListPage />);

      // 使用 getByRole 获取删除按钮
      const deleteButtons = screen.getAllByRole("button", { name: /删除/i });
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/此操作不可撤销/)).toBeInTheDocument();
      });

      // 使用 getByRole 找取消按钮，优先找 variant='link' 的按钮（取消）
      const cancelButtons = screen.getAllByRole("button", { name: /取消/i });
      // 点击最后一个取消按钮（弹窗中的）
      fireEvent.click(cancelButtons[cancelButtons.length - 1]);

      await waitFor(() => {
        expect(screen.queryByText("此操作不可撤销")).not.toBeInTheDocument();
      });
    });

    it("确认删除应该调用删除 API", async () => {
      renderWithProviders(<SpaceListPage />);

      // 使用 getByRole 获取删除按钮
      const deleteButtons = screen.getAllByRole("button", { name: /删除/i });
      fireEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/此操作不可撤销/)).toBeInTheDocument();
      });

      // 使用 getByRole 找确认删除按钮（variant='primary'）
      const confirmButtons = screen.getAllByRole("button", {
        name: /确认删除/i,
      });
      // 点击最后一个确认删除按钮（弹窗中的）
      fireEvent.click(confirmButtons[confirmButtons.length - 1]);

      // 验证删除 API 被调用
      await waitFor(() => {
        expect(mockDeleteMutate).toHaveBeenCalled();
      });

      // 弹窗应该关闭
      await waitFor(() => {
        expect(screen.queryByText("此操作不可撤销")).not.toBeInTheDocument();
      });
    });
  });
});
