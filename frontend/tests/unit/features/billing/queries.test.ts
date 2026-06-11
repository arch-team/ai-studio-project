/**
 * Billing queries 单元测试
 *
 * 测试计费模块的 TanStack Query hooks
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
// eslint-disable-next-line no-restricted-imports -- 直接测试 queries 子模块（白盒单元测试）
import {
  useCostReport,
  useUserCosts,
  useUserCostDetail,
  useResourceCosts,
} from "@features/billing/api/queries";
import type {
  CostReportResponse,
  UserCostListResponse,
  ResourceCostListResponse,
} from "@features/billing/types";
import React from "react";

// mock billingApi 函数，避免 jsdom 环境中 AbortSignal 兼容性问题
vi.mock("@features/billing/api/billingApi", () => ({
  fetchCostReport: vi.fn(),
  fetchUserCosts: vi.fn(),
  fetchUserCostDetail: vi.fn(),
  fetchResourceCosts: vi.fn(),
  exportBillingReport: vi.fn(),
}));

// eslint-disable-next-line no-restricted-imports -- 精确 mock 子模块以隔离 AbortSignal 兼容性问题
import {
  fetchCostReport,
  fetchUserCosts,
  fetchUserCostDetail,
  fetchResourceCosts,
} from "@features/billing/api/billingApi";

// 创建测试用 QueryClient wrapper
function createTestWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  });

  function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children,
    );
  }

  return Wrapper;
}

// 模拟数据
const mockCostReport: CostReportResponse = {
  summary: {
    total_cost_usd: 1000,
    compute_cost_usd: 600,
    storage_cost_usd: 200,
    network_cost_usd: 100,
    data_transfer_cost_usd: 50,
    other_cost_usd: 50,
    period_start: "2025-01-01",
    period_end: "2025-01-31",
  },
  breakdown: [
    {
      category: "compute",
      cost_usd: 600,
      percentage: 60,
      details: [],
    },
  ],
  daily_costs: [
    {
      date: "2025-01-01",
      total_cost_usd: 33,
      compute_cost_usd: 20,
      storage_cost_usd: 8,
      other_cost_usd: 5,
    },
  ],
};

const mockUserCosts: UserCostListResponse = {
  items: [
    {
      user_id: 1,
      username: "user1",
      total_cost_usd: 500,
      training_jobs_cost_usd: 300,
      spaces_cost_usd: 150,
      storage_cost_usd: 50,
      training_jobs_count: 5,
      total_gpu_hours: 100,
    },
  ],
  total: 1,
  total_cost_usd: 500,
};

const mockResourceCosts: ResourceCostListResponse = {
  items: [
    {
      id: 1,
      resource_type: "training_job",
      resource_id: "job-1",
      resource_name: "训练任务 1",
      owner_id: 1,
      owner_username: "user1",
      start_time: "2025-01-01T00:00:00Z",
      end_time: "2025-01-01T12:00:00Z",
      duration_seconds: 43200,
      instance_type: "ml.g5.xlarge",
      gpu_count: 1,
      compute_cost_usd: 100,
      storage_cost_usd: 10,
      total_cost_usd: 110,
      created_at: "2025-01-01T00:00:00Z",
    },
  ],
  total: 1,
  page: 1,
  page_size: 20,
  total_pages: 1,
  total_cost_usd: 110,
};

describe("Billing Query Hooks", () => {
  beforeEach(() => {
    vi.mocked(fetchCostReport).mockResolvedValue(mockCostReport);
    vi.mocked(fetchUserCosts).mockResolvedValue(mockUserCosts);
    vi.mocked(fetchUserCostDetail).mockResolvedValue(mockCostReport);
    vi.mocked(fetchResourceCosts).mockResolvedValue(mockResourceCosts);
  });

  describe("useCostReport", () => {
    it("应该获取成本报告数据", async () => {
      const { result } = renderHook(() => useCostReport({}), {
        wrapper: createTestWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data!.summary.total_cost_usd).toBe(1000);
      expect(result.current.data!.breakdown.length).toBe(1);
      expect(result.current.data!.daily_costs.length).toBe(1);
    });

    it("错误时应该返回错误状态", async () => {
      vi.mocked(fetchCostReport).mockRejectedValue(new Error("服务器错误"));

      const { result } = renderHook(() => useCostReport({}), {
        wrapper: createTestWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });
    });
  });

  describe("useUserCosts", () => {
    it("应该获取用户成本数据", async () => {
      const { result } = renderHook(() => useUserCosts({}), {
        wrapper: createTestWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data!.items.length).toBe(1);
      expect(result.current.data!.items[0].username).toBe("user1");
      expect(result.current.data!.total_cost_usd).toBe(500);
    });
  });

  describe("useUserCostDetail", () => {
    it("userId 为 undefined 时不应该发起请求", async () => {
      const { result } = renderHook(() => useUserCostDetail(undefined), {
        wrapper: createTestWrapper(),
      });

      // 等待确认不会发起请求
      await new Promise((r) => setTimeout(r, 100));
      expect(result.current.data).toBeUndefined();
      expect(result.current.isFetching).toBe(false);
    });

    it("有 userId 时应该获取用户成本详情", async () => {
      const { result } = renderHook(() => useUserCostDetail(1), {
        wrapper: createTestWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data!.summary.total_cost_usd).toBe(1000);
    });
  });

  describe("useResourceCosts", () => {
    it("应该获取资源成本数据", async () => {
      const { result } = renderHook(() => useResourceCosts({}), {
        wrapper: createTestWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data!.items.length).toBe(1);
      expect(result.current.data!.items[0].resource_type).toBe("training_job");
      expect(result.current.data!.total_cost_usd).toBe(110);
    });
  });
});
