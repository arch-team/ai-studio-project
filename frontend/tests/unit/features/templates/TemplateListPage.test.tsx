/**
 * TemplateListPage Tests
 *
 * 测试模板列表页面
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { TemplateListPage } from "@features/templates/pages";
import type { TemplateListResponse } from "@features/templates/types";

// Mock 数据
const mockListResponse: TemplateListResponse = {
  items: [
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
      visibility: "team",
      usage_count: 15,
      owner_id: 2,
      created_at: "2024-07-01T00:00:00Z",
    },
  ],
  total: 2,
  page: 1,
  page_size: 20,
  total_pages: 1,
};

// Mock API hooks
const mockUseJobTemplates = vi.fn();
const mockUsePopularTemplates = vi.fn();

vi.mock("@features/templates/api", () => ({
  useJobTemplates: (...args: unknown[]) => mockUseJobTemplates(...args),
  usePopularTemplates: (...args: unknown[]) => mockUsePopularTemplates(...args),
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe("TemplateListPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseJobTemplates.mockReturnValue({
      data: mockListResponse,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    mockUsePopularTemplates.mockReturnValue({
      data: [],
      isLoading: false,
      error: null,
    });
  });

  describe("基本渲染", () => {
    it("should render page header", () => {
      renderWithProviders(<TemplateListPage />);
      expect(
        screen.getByRole("heading", { level: 1, name: "任务模板" }),
      ).toBeInTheDocument();
    });

    it("should render page description", () => {
      renderWithProviders(<TemplateListPage />);
      expect(
        screen.getByText("管理和复用训练任务配置模板"),
      ).toBeInTheDocument();
    });

    it("should render create button", () => {
      renderWithProviders(<TemplateListPage />);
      expect(
        screen.getByRole("button", { name: /创建模板/i }),
      ).toBeInTheDocument();
    });

    it("should render refresh button", () => {
      renderWithProviders(<TemplateListPage />);
      expect(screen.getByRole("button", { name: /刷新/i })).toBeInTheDocument();
    });

    it("should render search input", () => {
      renderWithProviders(<TemplateListPage />);
      expect(
        screen.getByPlaceholderText("搜索模板名称..."),
      ).toBeInTheDocument();
    });

    it("should render search button", () => {
      renderWithProviders(<TemplateListPage />);
      expect(screen.getByRole("button", { name: "搜索" })).toBeInTheDocument();
    });

    it("should render template table", () => {
      renderWithProviders(<TemplateListPage />);
      expect(screen.getByRole("table")).toBeInTheDocument();
    });
  });

  describe("加载状态", () => {
    it("should show loading state in table", () => {
      mockUseJobTemplates.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        refetch: vi.fn(),
      });

      renderWithProviders(<TemplateListPage />);
      expect(screen.getByText("加载中...")).toBeInTheDocument();
    });
  });

  describe("错误状态", () => {
    it("should display error message on failure", () => {
      mockUseJobTemplates.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error("Network error"),
        refetch: vi.fn(),
      });

      renderWithProviders(<TemplateListPage />);
      expect(screen.getByText(/加载失败/i)).toBeInTheDocument();
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });
  });

  describe("导航交互", () => {
    it("should navigate to create page when clicking create button", () => {
      renderWithProviders(<TemplateListPage />);
      fireEvent.click(screen.getByRole("button", { name: /创建模板/i }));
      expect(mockNavigate).toHaveBeenCalledWith("/job-templates/create");
    });

    it("should call refetch when clicking refresh button", () => {
      const mockRefetch = vi.fn();
      mockUseJobTemplates.mockReturnValue({
        data: mockListResponse,
        isLoading: false,
        error: null,
        refetch: mockRefetch,
      });

      renderWithProviders(<TemplateListPage />);
      fireEvent.click(screen.getByRole("button", { name: /刷新/i }));
      expect(mockRefetch).toHaveBeenCalled();
    });
  });
});
