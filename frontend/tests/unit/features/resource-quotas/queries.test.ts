/**
 * Resource Quotas queries 单元测试
 *
 * 测试资源配额模块的 TanStack Query mutation hooks
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { queryKeys } from "@lib/query";
// eslint-disable-next-line no-restricted-imports -- 直接测试 queries 子模块（白盒单元测试）
import { useDeleteResourceLimitConfig } from "@features/resource-quotas/api/queries";
import React from "react";

// mock resourceQuotasApi 函数，隔离网络请求
vi.mock("@features/resource-quotas/api/resourceQuotasApi", () => ({
  fetchResourceLimitConfigs: vi.fn(),
  createResourceLimitConfig: vi.fn(),
  updateResourceLimitConfig: vi.fn(),
  deleteResourceLimitConfig: vi.fn(),
}));

// eslint-disable-next-line no-restricted-imports -- 精确 mock 子模块以隔离网络请求
import { deleteResourceLimitConfig } from "@features/resource-quotas/api/resourceQuotasApi";

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

  return { Wrapper, queryClient };
}

describe("Resource Quotas Mutation Hooks", () => {
  beforeEach(() => {
    vi.mocked(deleteResourceLimitConfig).mockResolvedValue(undefined);
  });

  describe("useDeleteResourceLimitConfig", () => {
    it("调用后应该删除指定配置并刷新列表缓存", async () => {
      const { Wrapper, queryClient } = createTestWrapper();
      const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

      const { result } = renderHook(() => useDeleteResourceLimitConfig(), {
        wrapper: Wrapper,
      });

      result.current.mutate(42);

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      // 调用了删除 API 且传入正确 id
      expect(deleteResourceLimitConfig).toHaveBeenCalledWith(42);

      // 成功后失效列表缓存（与 create/update hook 使用相同的 lists key）
      expect(invalidateSpy).toHaveBeenCalledWith({
        queryKey: queryKeys.resourceQuotas.lists(),
      });
    });

    it("删除失败时应该返回错误状态", async () => {
      vi.mocked(deleteResourceLimitConfig).mockRejectedValue(
        new Error("服务器错误"),
      );

      const { Wrapper } = createTestWrapper();
      const { result } = renderHook(() => useDeleteResourceLimitConfig(), {
        wrapper: Wrapper,
      });

      result.current.mutate(42);

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });
    });
  });
});
