/**
 * HomePage 单元测试
 *
 * 重点验证首页仪表盘在数据加载失败时的「错误态显式报错」行为：
 * - 不再把加载失败静默伪装成「指标 0 + 系统全绿健康」（UI 审计 F-001/F-030）
 * - error 态显示 InlineErrorState（标题「加载失败」+「重试」按钮）
 * - 系统状态面板降级为「无法获取」，Hero 标识降级为「平台状态无法获取」
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { renderWithProviders } from '@tests/__utils__/test-utils';
import { HomePage } from '@features/dashboard/pages';

// === Mock API hooks ===
const mockUseTrainingJobs = vi.fn();
const mockUseDatasets = vi.fn();
const mockUseModels = vi.fn();

vi.mock('@features/training/api', () => ({
  useTrainingJobs: (...args: unknown[]) => mockUseTrainingJobs(...args),
}));

vi.mock('@features/datasets/api', () => ({
  useDatasets: (...args: unknown[]) => mockUseDatasets(...args),
}));

vi.mock('@features/models/api', () => ({
  useModels: (...args: unknown[]) => mockUseModels(...args),
}));

// === Mock Auth Store ===
vi.mock('@features/auth', () => ({
  useAuthStore: (selector: (state: { user: { name: string } }) => unknown) =>
    selector({ user: { name: '测试用户' } }),
}));

// 正常态返回值工厂（HomePage 仅读取 data?.total）
const okJobs = (total: number) => ({
  data: { total },
  isLoading: false,
  isError: false,
  error: null,
  refetch: vi.fn(),
});

describe('HomePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // 默认：所有查询正常返回
    mockUseTrainingJobs.mockReturnValue(okJobs(26));
    mockUseDatasets.mockReturnValue(okJobs(8));
    mockUseModels.mockReturnValue(okJobs(5));
  });

  describe('正常态', () => {
    it('应该渲染关键指标数字且不出现错误提示', () => {
      renderWithProviders(<HomePage />);

      // 训练任务总数指标卡渲染数字
      expect(screen.getByText('训练任务总数')).toBeInTheDocument();
      expect(screen.getAllByText('26').length).toBeGreaterThanOrEqual(1);

      // 正常态不应出现错误提示
      expect(screen.queryByText('加载失败')).not.toBeInTheDocument();
      expect(screen.queryByText('无法获取')).not.toBeInTheDocument();

      // 系统状态正常
      expect(screen.getByText('平台服务运行正常')).toBeInTheDocument();
    });
  });

  describe('error 态', () => {
    beforeEach(() => {
      // 核心数据源 allJobs 加载失败
      mockUseTrainingJobs.mockReturnValue({
        data: undefined,
        isLoading: false,
        isError: true,
        error: { message: '服务器内部错误' },
        refetch: vi.fn(),
      });
    });

    it('应该显示 InlineErrorState 并提供重试按钮', async () => {
      renderWithProviders(<HomePage />);

      // InlineErrorState 标题
      expect(await screen.findByText('加载失败')).toBeInTheDocument();
      // 重试按钮
      expect(
        screen.getByRole('button', { name: '重试' })
      ).toBeInTheDocument();
    });

    it('系统状态面板应降级为「无法获取」而非伪装健康', () => {
      renderWithProviders(<HomePage />);

      // 系统状态面板降级文案
      expect(screen.getByText('无法获取')).toBeInTheDocument();
      // 不再硬编码「运行正常」
      expect(screen.queryByText('运行正常')).not.toBeInTheDocument();
    });

    it('Hero 标识应降级为「平台状态无法获取」', () => {
      renderWithProviders(<HomePage />);

      expect(screen.getByText('平台状态无法获取')).toBeInTheDocument();
      expect(
        screen.queryByText('平台服务运行正常')
      ).not.toBeInTheDocument();
    });
  });
});
