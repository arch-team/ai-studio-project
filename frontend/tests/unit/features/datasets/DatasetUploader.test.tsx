/**
 * DatasetUploader 单元测试
 *
 * 测试数据集文件上传组件的渲染、文件选择、上传进度和操作按钮
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "@tests/__utils__/test-utils";
import { DatasetUploader } from "@features/datasets/components";

// Mock useDatasetUpload hook
const mockUpload = vi.fn();
const mockCancel = vi.fn();
const mockReset = vi.fn();
const mockProgress = {
  loaded: 0,
  total: 0,
  percentage: 0,
  status: "idle" as const,
};

vi.mock("@features/datasets/hooks/useDatasetUpload", () => ({
  useDatasetUpload: () => ({
    progress: mockProgress,
    upload: mockUpload,
    cancel: mockCancel,
    reset: mockReset,
  }),
}));

describe("DatasetUploader", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockProgress.status = "idle";
    mockProgress.loaded = 0;
    mockProgress.total = 0;
    mockProgress.percentage = 0;
  });

  describe("初始渲染 (DropZone)", () => {
    it("应渲染拖拽上传区域", () => {
      renderWithProviders(<DatasetUploader />);
      expect(screen.getByText("将文件拖拽到此处")).toBeInTheDocument();
    });

    it("应渲染选择文件按钮", () => {
      renderWithProviders(<DatasetUploader />);
      expect(screen.getByText("选择文件")).toBeInTheDocument();
    });

    it('应渲染"或"分隔文本', () => {
      renderWithProviders(<DatasetUploader />);
      expect(screen.getByText("或")).toBeInTheDocument();
    });

    it("应有正确的 aria-label", () => {
      renderWithProviders(<DatasetUploader />);
      expect(
        screen.getByRole("button", {
          name: "拖拽文件到此处上传，或点击选择文件",
        }),
      ).toBeInTheDocument();
    });
  });

  describe("禁用状态", () => {
    it("应在禁用时设置 aria-disabled", () => {
      renderWithProviders(<DatasetUploader disabled={true} />);
      const dropZone = screen.getByRole("button", {
        name: "拖拽文件到此处上传，或点击选择文件",
      });
      expect(dropZone).toHaveAttribute("aria-disabled", "true");
    });

    it("应在禁用时禁用选择文件按钮", () => {
      renderWithProviders(<DatasetUploader disabled={true} />);
      const selectButton = screen.getByText("选择文件").closest("button");
      expect(selectButton).toBeDisabled();
    });
  });

  describe("文件选择后", () => {
    it("选择文件后应调用 upload", () => {
      renderWithProviders(<DatasetUploader />);

      const file = new File(["test content"], "test.csv", {
        type: "text/csv",
      });
      const input = document.querySelector(
        'input[type="file"]',
      ) as HTMLInputElement;

      fireEvent.change(input, { target: { files: [file] } });

      expect(mockUpload).toHaveBeenCalledWith(expect.any(File));
    });
  });
});
