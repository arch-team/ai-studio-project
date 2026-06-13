/**
 * CreateSpacePage 单元测试
 *
 * 测试创建开发空间页面的渲染、表单验证和提交
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { useUIStore } from "@store/slices/uiSlice";
import { CreateSpacePage } from "@features/spaces/pages";

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
const mockMutateAsync = vi.fn();
const mockCreateSpace = vi.fn();

vi.mock("@features/spaces/api", () => ({
  useCreateSpace: () => mockCreateSpace(),
}));

describe("CreateSpacePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // 默认成功的 mutation
    mockMutateAsync.mockResolvedValue({
      id: 1,
      name: "test-space",
      space_type: "jupyter",
      status: "creating",
    });

    mockCreateSpace.mockReturnValue({
      mutateAsync: mockMutateAsync,
      isPending: false,
      isError: false,
      error: null,
    });
  });

  describe("基本渲染", () => {
    it("应该渲染页面标题", () => {
      renderWithProviders(<CreateSpacePage />);
      // Header 组件会渲染页面标题
      const header = screen.getByRole("heading", { name: /创建开发空间/i });
      expect(header).toBeInTheDocument();
    });

    it("应该渲染面包屑导航", () => {
      renderWithProviders(<CreateSpacePage />);
      // 面包屑经 PageLayout 同步到全局 UI Store，由 MainLayout 渲染
      const breadcrumbs = useUIStore.getState().breadcrumbs;
      expect(breadcrumbs.some((b) => b.text === "开发空间")).toBe(true);
      expect(breadcrumbs.some((b) => b.text === "创建开发空间")).toBe(true);
    });

    it("应该渲染环境类型选择器", () => {
      renderWithProviders(<CreateSpacePage />);
      expect(screen.getByText("环境类型")).toBeInTheDocument();
    });

    it("应该渲染空间名称输入框", () => {
      renderWithProviders(<CreateSpacePage />);
      expect(screen.getByText("空间名称")).toBeInTheDocument();
    });

    it("应该渲染 IDE 类型选择器", () => {
      renderWithProviders(<CreateSpacePage />);
      expect(screen.getByText("IDE 类型")).toBeInTheDocument();
    });

    it("应该渲染实例类型选择器", () => {
      renderWithProviders(<CreateSpacePage />);
      expect(screen.getByText("实例类型")).toBeInTheDocument();
    });

    it("应该渲染存储大小输入框", () => {
      renderWithProviders(<CreateSpacePage />);
      expect(screen.getByText("存储大小 (GB)")).toBeInTheDocument();
    });

    it("应该渲染创建和取消按钮", () => {
      renderWithProviders(<CreateSpacePage />);
      expect(screen.getByText("创建空间")).toBeInTheDocument();
      expect(screen.getByText("取消")).toBeInTheDocument();
    });
  });

  describe("表单验证", () => {
    it("空间名称为空时应该显示错误", async () => {
      renderWithProviders(<CreateSpacePage />);

      fireEvent.click(screen.getByText("创建空间"));

      await waitFor(() => {
        expect(screen.getByText("请输入空间名称")).toBeInTheDocument();
      });
    });

    it("空间名称包含非法字符时应该显示错误", async () => {
      renderWithProviders(<CreateSpacePage />);

      const nameInput = screen.getByPlaceholderText("my-dev-space");
      fireEvent.change(nameInput, { target: { value: "Invalid Name!" } });
      fireEvent.click(screen.getByText("创建空间"));

      await waitFor(() => {
        expect(
          screen.getByText(/空间名称只能包含小写字母、数字和连字符/),
        ).toBeInTheDocument();
      });
    });

    it("空间名称超过 63 个字符应该显示错误", async () => {
      renderWithProviders(<CreateSpacePage />);

      const nameInput = screen.getByPlaceholderText("my-dev-space");
      const longName = "a".repeat(64);
      fireEvent.change(nameInput, { target: { value: longName } });
      fireEvent.click(screen.getByText("创建空间"));

      await waitFor(() => {
        expect(
          screen.getByText("空间名称不能超过 63 个字符"),
        ).toBeInTheDocument();
      });
    });

    it("存储大小超出范围应该显示错误", async () => {
      renderWithProviders(<CreateSpacePage />);

      const nameInput = screen.getByPlaceholderText("my-dev-space");
      fireEvent.change(nameInput, { target: { value: "valid-name" } });

      // 清除默认值并输入无效值
      const storageInput = document.querySelector(
        'input[type="number"]',
      ) as HTMLInputElement;
      fireEvent.change(storageInput, { target: { value: "999" } });
      fireEvent.click(screen.getByText("创建空间"));

      await waitFor(() => {
        expect(
          screen.getByText("存储大小必须在 5-500 GB 之间"),
        ).toBeInTheDocument();
      });
    });
  });

  describe("导航操作", () => {
    it("点击取消应该导航回列表页", () => {
      renderWithProviders(<CreateSpacePage />);

      fireEvent.click(screen.getByText("取消"));
      expect(mockNavigate).toHaveBeenCalledWith("/spaces");
    });
  });

  describe("表单提交", () => {
    it("表单验证通过后应该提交并导航（默认 studio）", async () => {
      renderWithProviders(<CreateSpacePage />);

      // 使用 Cloudscape Input 组件的实际 change 事件
      const nameInput = screen.getByPlaceholderText(
        "my-dev-space",
      ) as HTMLInputElement;
      // Cloudscape Input 组件使用 onChange({detail: {value}}) 事件
      // 但在测试中，我们模拟原生 input 的 change 事件
      fireEvent.change(nameInput, { target: { value: "my-test-space" } });

      // 点击创建按钮
      const createButton = screen.getByRole("button", { name: "创建空间" });
      fireEvent.click(createButton);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          space_name: "my-test-space",
          backend: "studio",
          space_type: "jupyter",
          instance_type: "ml.g5.xlarge",
          storage_size_gb: 10,
        });
      });

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith("/spaces");
      });
    });

    it("默认应该不显示 HyperPod 配额提示（backend=studio）", () => {
      renderWithProviders(<CreateSpacePage />);

      // 默认 backend=studio，不显示 HyperPod 提示
      expect(
        screen.queryByText(/HyperPod 集群空间将占用团队的 ClusterQueue 配额/)
      ).not.toBeInTheDocument();
    });

    it("通过 Select 选中「HyperPod 集群」后显示配额提示且提交 backend:hyperpod", async () => {
      const user = userEvent.setup();
      renderWithProviders(<CreateSpacePage />);

      // 初始（默认 studio）不应显示 HyperPod 配额提示
      expect(
        screen.queryByText(/HyperPod 集群空间将占用团队的 ClusterQueue 配额/)
      ).not.toBeInTheDocument();

      // 1. 找到「环境类型」Select 的 trigger（Cloudscape Select 渲染为
      //    aria-haspopup="listbox" 的 button，trigger 上显示当前选中值 "SageMaker Studio"）
      const backendTrigger = screen
        .getAllByRole("button")
        .find(
          (btn) =>
            btn.getAttribute("aria-haspopup") === "listbox" &&
            btn.textContent?.includes("SageMaker Studio")
        );
      expect(backendTrigger).toBeDefined();

      // 2. 点击展开 listbox，再点击「HyperPod 集群」选项（role="option"）
      await user.click(backendTrigger!);
      const hyperpodOption = await screen.findByRole("option", {
        name: /HyperPod 集群/,
      });
      await user.click(hyperpodOption);

      // 3. 选中 HyperPod 后，配额提示 Alert 应出现（文案含 "ClusterQueue 配额"）
      await waitFor(() => {
        expect(
          screen.getByText(/HyperPod 集群空间将占用团队的 ClusterQueue 配额/)
        ).toBeInTheDocument();
      });

      // 4. 填入合法名称并点击「创建空间」
      const nameInput = screen.getByPlaceholderText("my-dev-space");
      fireEvent.change(nameInput, { target: { value: "valid-name" } });
      await user.click(screen.getByRole("button", { name: "创建空间" }));

      // 5. 断言提交请求体携带 backend: 'hyperpod'
      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          space_name: "valid-name",
          backend: "hyperpod",
          space_type: "jupyter",
          instance_type: "ml.g5.xlarge",
          storage_size_gb: 10,
        });
      });
    });

    it("提交失败时应该显示错误信息", async () => {
      mockMutateAsync.mockRejectedValue(new Error("创建失败"));
      mockCreateSpace.mockReturnValue({
        mutateAsync: mockMutateAsync,
        isPending: false,
        isError: true,
        error: { message: "创建失败" },
      });

      renderWithProviders(<CreateSpacePage />);

      const nameInput = screen.getByPlaceholderText("my-dev-space");
      fireEvent.change(nameInput, { target: { value: "my-test-space" } });

      fireEvent.click(screen.getByText("创建空间"));

      await waitFor(() => {
        expect(screen.getByText(/创建失败/)).toBeInTheDocument();
      });
    });
  });
});
