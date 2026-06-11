/**
 * useEntityMutations / useOptimisticUpdate / useBatchOperations 单元测试
 */

import { renderHook, act, waitFor } from "@testing-library/react";
import { vi, describe, it, expect } from "vitest";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  useEntityMutations,
  useOptimisticUpdate,
  useBatchOperations,
} from "@shared/hooks";

// 创建 QueryClient 包装器
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
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

  return { wrapper: Wrapper, queryClient };
}

// === useEntityMutations ===

describe("useEntityMutations", () => {
  it("应返回 create/update/delete mutation 对象", () => {
    const { wrapper } = createWrapper();

    const operations = {
      create: vi.fn().mockResolvedValue({ id: 1, name: "test" }),
      update: vi.fn().mockResolvedValue({ id: 1, name: "updated" }),
      delete: vi.fn().mockResolvedValue(undefined),
    };

    const { result } = renderHook(
      () =>
        useEntityMutations(operations, {
          queryKey: ["test-entities"],
        }),
      { wrapper },
    );

    expect(result.current.createMutation).toBeDefined();
    expect(result.current.updateMutation).toBeDefined();
    expect(result.current.deleteMutation).toBeDefined();
  });

  it("create mutation 应调用 operations.create 并触发回调", async () => {
    const { wrapper, queryClient } = createWrapper();
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const entity = { id: 1, name: "new-entity" };
    const operations = {
      create: vi.fn().mockResolvedValue(entity),
      update: vi.fn(),
      delete: vi.fn(),
    };
    const onCreateSuccess = vi.fn();

    const { result } = renderHook(
      () =>
        useEntityMutations(operations, {
          queryKey: ["entities"],
          onCreateSuccess,
        }),
      { wrapper },
    );

    act(() => {
      result.current.createMutation.mutate({ name: "new-entity" });
    });

    await waitFor(() => {
      expect(operations.create).toHaveBeenCalled();
      expect(operations.create.mock.calls[0][0]).toEqual({
        name: "new-entity",
      });
      expect(onCreateSuccess).toHaveBeenCalledWith(entity);
      expect(invalidateSpy).toHaveBeenCalled();
    });
  });

  it("update mutation 应调用 operations.update", async () => {
    const { wrapper } = createWrapper();

    const updated = { id: 1, name: "updated" };
    const operations = {
      create: vi.fn(),
      update: vi.fn().mockResolvedValue(updated),
      delete: vi.fn(),
    };
    const onUpdateSuccess = vi.fn();

    const { result } = renderHook(
      () =>
        useEntityMutations(operations, {
          queryKey: ["entities"],
          onUpdateSuccess,
        }),
      { wrapper },
    );

    act(() => {
      result.current.updateMutation.mutate({
        id: "1",
        data: { name: "updated" },
      });
    });

    await waitFor(() => {
      expect(operations.update).toHaveBeenCalledWith("1", { name: "updated" });
      expect(onUpdateSuccess).toHaveBeenCalledWith(updated);
    });
  });

  it("delete mutation 应调用 operations.delete", async () => {
    const { wrapper } = createWrapper();

    const operations = {
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn().mockResolvedValue(undefined),
    };
    const onDeleteSuccess = vi.fn();

    const { result } = renderHook(
      () =>
        useEntityMutations(operations, {
          queryKey: ["entities"],
          onDeleteSuccess,
        }),
      { wrapper },
    );

    act(() => {
      result.current.deleteMutation.mutate("1");
    });

    await waitFor(() => {
      expect(operations.delete).toHaveBeenCalled();
      expect(operations.delete.mock.calls[0][0]).toBe("1");
      expect(onDeleteSuccess).toHaveBeenCalledWith("1");
    });
  });

  it("mutation 失败时应触发 onError 回调", async () => {
    const { wrapper } = createWrapper();

    const error = new Error("创建失败");
    const operations = {
      create: vi.fn().mockRejectedValue(error),
      update: vi.fn(),
      delete: vi.fn(),
    };
    const onError = vi.fn();

    const { result } = renderHook(
      () =>
        useEntityMutations(operations, {
          queryKey: ["entities"],
          onError,
        }),
      { wrapper },
    );

    act(() => {
      result.current.createMutation.mutate({ name: "fail" });
    });

    await waitFor(() => {
      expect(onError).toHaveBeenCalled();
    });
  });
});

// === useOptimisticUpdate ===

describe("useOptimisticUpdate", () => {
  it("应在 mutate 时乐观更新缓存数据", async () => {
    const { wrapper, queryClient } = createWrapper();

    // 预设缓存数据
    queryClient.setQueryData(["item", "1"], { id: "1", status: "pending" });

    const { result } = renderHook(
      () =>
        useOptimisticUpdate({
          queryKey: ["item", "1"],
          updateFn: (
            current: { id: string; status: string },
            variables: { status: string },
          ) => ({
            ...current,
            status: variables.status,
          }),
          mutationFn: vi.fn().mockResolvedValue({ id: "1", status: "running" }),
        }),
      { wrapper },
    );

    act(() => {
      result.current.mutate({ status: "running" });
    });

    // 乐观更新应立即反映
    await waitFor(() => {
      const cached = queryClient.getQueryData(["item", "1"]) as {
        status: string;
      };
      expect(cached.status).toBe("running");
    });
  });

  it("mutation 失败时应回滚缓存数据", async () => {
    const { wrapper, queryClient } = createWrapper();

    queryClient.setQueryData(["item", "1"], { id: "1", status: "pending" });

    const onError = vi.fn();

    const { result } = renderHook(
      () =>
        useOptimisticUpdate({
          queryKey: ["item", "1"],
          updateFn: (
            current: { id: string; status: string },
            variables: { status: string },
          ) => ({
            ...current,
            status: variables.status,
          }),
          mutationFn: vi.fn().mockRejectedValue(new Error("更新失败")),
          onError,
        }),
      { wrapper },
    );

    act(() => {
      result.current.mutate({ status: "running" });
    });

    await waitFor(() => {
      // 应回滚到原始值
      const cached = queryClient.getQueryData(["item", "1"]) as {
        status: string;
      };
      expect(cached.status).toBe("pending");
      expect(onError).toHaveBeenCalled();
    });
  });

  it("应在成功时用服务器数据更新缓存", async () => {
    const { wrapper, queryClient } = createWrapper();

    queryClient.setQueryData(["item", "1"], {
      id: "1",
      status: "pending",
      extra: false,
    });

    const serverResponse = { id: "1", status: "running", extra: true };
    const onSuccess = vi.fn();

    const { result } = renderHook(
      () =>
        useOptimisticUpdate({
          queryKey: ["item", "1"],
          updateFn: (
            current: Record<string, unknown>,
            variables: { status: string },
          ) => ({
            ...current,
            status: variables.status,
          }),
          mutationFn: vi.fn().mockResolvedValue(serverResponse),
          onSuccess,
        }),
      { wrapper },
    );

    act(() => {
      result.current.mutate({ status: "running" });
    });

    await waitFor(() => {
      const cached = queryClient.getQueryData(["item", "1"]);
      expect(cached).toEqual(serverResponse);
      expect(onSuccess).toHaveBeenCalledWith(serverResponse, {
        status: "running",
      });
    });
  });

  it("应暴露 isPending 和 isError 状态", async () => {
    const { wrapper, queryClient } = createWrapper();

    queryClient.setQueryData(["item", "1"], { id: "1" });

    let resolveMutation!: (value: unknown) => void;
    const mutationFn = vi.fn(
      () =>
        new Promise<Record<string, unknown>>((resolve) => {
          resolveMutation = resolve;
        }),
    );

    const { result } = renderHook(
      () =>
        useOptimisticUpdate({
          queryKey: ["item", "1"],
          updateFn: (current: Record<string, unknown>) => current,
          mutationFn,
        }),
      { wrapper },
    );

    expect(result.current.isPending).toBe(false);

    act(() => {
      result.current.mutate({});
    });

    await waitFor(() => {
      expect(result.current.isPending).toBe(true);
    });

    await act(async () => {
      resolveMutation({ id: "1" });
    });

    await waitFor(() => {
      expect(result.current.isPending).toBe(false);
    });
  });
});

// === useBatchOperations ===

describe("useBatchOperations", () => {
  const mockItems = [
    { id: 1, name: "item1" },
    { id: 2, name: "item2" },
    { id: 3, name: "item3" },
  ];

  it("应初始化为空选择", () => {
    const { wrapper } = createWrapper();

    const { result } = renderHook(
      () =>
        useBatchOperations({
          items: mockItems,
          getItemId: (item) => item.id,
        }),
      { wrapper },
    );

    expect(result.current.selectedIds).toEqual([]);
    expect(result.current.selectedCount).toBe(0);
    expect(result.current.isAllSelected).toBe(false);
    expect(result.current.isSomeSelected).toBe(false);
  });

  it("toggleSelect 应切换选择状态", () => {
    const { wrapper } = createWrapper();

    const { result } = renderHook(
      () =>
        useBatchOperations({
          items: mockItems,
          getItemId: (item) => item.id,
        }),
      { wrapper },
    );

    act(() => {
      result.current.toggleSelect(1);
    });

    expect(result.current.selectedIds).toContain(1);
    expect(result.current.selectedCount).toBe(1);
    expect(result.current.isSelected(1)).toBe(true);
    expect(result.current.isSelected(2)).toBe(false);
    expect(result.current.isSomeSelected).toBe(true);

    // 再次切换应取消选择
    act(() => {
      result.current.toggleSelect(1);
    });

    expect(result.current.selectedIds).not.toContain(1);
    expect(result.current.selectedCount).toBe(0);
  });

  it("selectAll 应选择所有项", () => {
    const { wrapper } = createWrapper();

    const { result } = renderHook(
      () =>
        useBatchOperations({
          items: mockItems,
          getItemId: (item) => item.id,
        }),
      { wrapper },
    );

    act(() => {
      result.current.selectAll();
    });

    expect(result.current.selectedCount).toBe(3);
    expect(result.current.isAllSelected).toBe(true);
  });

  it("clearSelection 应清除所有选择", () => {
    const { wrapper } = createWrapper();

    const { result } = renderHook(
      () =>
        useBatchOperations({
          items: mockItems,
          getItemId: (item) => item.id,
        }),
      { wrapper },
    );

    act(() => {
      result.current.selectAll();
    });
    expect(result.current.selectedCount).toBe(3);

    act(() => {
      result.current.clearSelection();
    });
    expect(result.current.selectedCount).toBe(0);
    expect(result.current.isAllSelected).toBe(false);
  });

  it("batchDelete 应调用 onBatchDelete 并清除选择", async () => {
    const { wrapper } = createWrapper();

    const onBatchDelete = vi.fn().mockResolvedValue(undefined);

    const { result } = renderHook(
      () =>
        useBatchOperations({
          items: mockItems,
          getItemId: (item) => item.id,
          onBatchDelete,
        }),
      { wrapper },
    );

    act(() => {
      result.current.toggleSelect(1);
      result.current.toggleSelect(2);
    });

    act(() => {
      result.current.batchDelete();
    });

    await waitFor(() => {
      expect(onBatchDelete).toHaveBeenCalledWith([1, 2]);
      expect(result.current.selectedCount).toBe(0);
    });
  });

  it("items 为 undefined 时 selectAll 不应报错", () => {
    const { wrapper } = createWrapper();

    const { result } = renderHook(
      () =>
        useBatchOperations({
          items: undefined,
          getItemId: (item: { id: number }) => item.id,
        }),
      { wrapper },
    );

    // 不应抛出异常
    act(() => {
      result.current.selectAll();
    });

    expect(result.current.selectedCount).toBe(0);
  });

  it("items 为空数组时 isAllSelected 应为 false", () => {
    const { wrapper } = createWrapper();

    const { result } = renderHook(
      () =>
        useBatchOperations({
          items: [],
          getItemId: (item: { id: number }) => item.id,
        }),
      { wrapper },
    );

    expect(result.current.isAllSelected).toBe(false);
  });
});
