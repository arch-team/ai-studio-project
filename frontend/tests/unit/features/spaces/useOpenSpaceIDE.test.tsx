/**
 * useOpenSpaceIDE 单元测试
 *
 * 回归缺陷: window.open 传入 'noopener' 时按规范返回 null，
 * 导致 presigned URL 无法写入新窗口，点击「打开」后停留空白页。
 * 正确做法: 不传 noopener 拿到引用，手动 win.opener = null 切断关系。
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useOpenSpaceIDE } from "@features/spaces/api";

vi.mock("@shared/api", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import { apiClient } from "@shared/api";

const TRUSTED_URL =
  "https://xyz.studio.us-east-1.sagemaker.aws/auth?token=abc";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { mutations: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

function createFakeWindow() {
  return {
    opener: {},
    close: vi.fn(),
    location: { href: "about:blank" },
  } as unknown as Window;
}

describe("useOpenSpaceIDE", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("成功路径: 不带 noopener 开窗、手动切断 opener 并写入 presigned URL", async () => {
    const fakeWin = createFakeWindow();
    const openSpy = vi.spyOn(window, "open").mockReturnValue(fakeWin);
    vi.mocked(apiClient.post).mockResolvedValue({ url: TRUSTED_URL });

    const { result } = renderHook(() => useOpenSpaceIDE(), {
      wrapper: createWrapper(),
    });
    await result.current.mutateAsync("space-1");

    // 关键回归: 不能传 'noopener'（否则 window.open 返回 null）
    expect(openSpy).toHaveBeenCalledWith("about:blank", "_blank");
    expect(apiClient.post).toHaveBeenCalledWith("/spaces/space-1/access-url");
    // 安全: 导航前手动切断 opener
    expect((fakeWin as unknown as { opener: unknown }).opener).toBeNull();
    // URL 必须真实写入新窗口
    expect(fakeWin.location.href).toBe(TRUSTED_URL);
  });

  it("弹窗被浏览器拦截时给出明确错误且不请求 API", async () => {
    vi.spyOn(window, "open").mockReturnValue(null);

    const { result } = renderHook(() => useOpenSpaceIDE(), {
      wrapper: createWrapper(),
    });

    await expect(result.current.mutateAsync("space-1")).rejects.toThrow(
      /弹出窗口/,
    );
    expect(apiClient.post).not.toHaveBeenCalled();
  });

  it("不可信协议（非 HTTPS）拒绝跳转并关闭已开的窗口", async () => {
    const fakeWin = createFakeWindow();
    vi.spyOn(window, "open").mockReturnValue(fakeWin);
    vi.mocked(apiClient.post).mockResolvedValue({
      url: "http://evil.example.com/auth",
    });

    const { result } = renderHook(() => useOpenSpaceIDE(), {
      wrapper: createWrapper(),
    });

    await expect(result.current.mutateAsync("space-1")).rejects.toThrow(
      /不可信/,
    );
    expect(fakeWin.close).toHaveBeenCalled();
    expect(fakeWin.location.href).toBe("about:blank");
  });

  it("javascript: 协议拒绝跳转并关闭已开的窗口", async () => {
    const fakeWin = createFakeWindow();
    vi.spyOn(window, "open").mockReturnValue(fakeWin);
    vi.mocked(apiClient.post).mockResolvedValue({
      url: "javascript:alert(1)",
    });

    const { result } = renderHook(() => useOpenSpaceIDE(), {
      wrapper: createWrapper(),
    });

    await expect(result.current.mutateAsync("space-1")).rejects.toThrow(
      /不可信/,
    );
    expect(fakeWin.close).toHaveBeenCalled();
  });

  it("允许 HyperPod 自定义域名（HTTPS + 非 sagemaker.aws）", async () => {
    const hyperpodUrl = "https://custom.hyperpod.example.com/jupyter";
    const fakeWin = createFakeWindow();
    vi.spyOn(window, "open").mockReturnValue(fakeWin);
    vi.mocked(apiClient.post).mockResolvedValue({ url: hyperpodUrl });

    const { result } = renderHook(() => useOpenSpaceIDE(), {
      wrapper: createWrapper(),
    });

    await result.current.mutateAsync("space-2");

    expect(fakeWin.location.href).toBe(hyperpodUrl);
    expect(fakeWin.close).not.toHaveBeenCalled();
  });

  it("API 失败时关闭已开的窗口并抛出错误", async () => {
    const fakeWin = createFakeWindow();
    vi.spyOn(window, "open").mockReturnValue(fakeWin);
    vi.mocked(apiClient.post).mockRejectedValue(new Error("空间未运行"));

    const { result } = renderHook(() => useOpenSpaceIDE(), {
      wrapper: createWrapper(),
    });

    await expect(result.current.mutateAsync("space-1")).rejects.toThrow(
      "空间未运行",
    );
    expect(fakeWin.close).toHaveBeenCalled();
  });
});
