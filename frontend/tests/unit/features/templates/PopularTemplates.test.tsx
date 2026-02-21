/**
 * PopularTemplates Component Tests
 *
 * 测试热门模板推荐组件
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, fireEvent } from '@testing-library/react';
import { renderWithProviders } from '@tests/__utils__/test-utils';
import { PopularTemplates } from '@features/templates/components';
import type { JobTemplateSummary } from '@features/templates/types';

// Mock 热门模板数据
const mockPopularTemplates: JobTemplateSummary[] = [
  {
    id: 1,
    name: 'LLM 微调模板',
    description: '大语言模型微调训练模板',
    visibility: 'public',
    usage_count: 128,
    owner_id: 1,
    created_at: '2024-06-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'CV 训练模板',
    description: '计算机视觉训练模板',
    visibility: 'public',
    usage_count: 89,
    owner_id: 2,
    created_at: '2024-07-01T00:00:00Z',
  },
  {
    id: 3,
    name: '无描述模板',
    visibility: 'team',
    usage_count: 50,
    owner_id: 1,
    created_at: '2024-08-01T00:00:00Z',
  },
];

// Mock API hooks
const mockUsePopularTemplates = vi.fn();

vi.mock('@features/templates/api', () => ({
  usePopularTemplates: (...args: unknown[]) => mockUsePopularTemplates(...args),
}));

describe('PopularTemplates', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUsePopularTemplates.mockReturnValue({
      data: mockPopularTemplates,
      isLoading: false,
      error: null,
    });
  });

  describe('基本渲染', () => {
    it('should render header', () => {
      renderWithProviders(<PopularTemplates />);
      expect(screen.getByText('热门模板')).toBeInTheDocument();
    });

    it('should render description', () => {
      renderWithProviders(<PopularTemplates />);
      expect(screen.getByText('最受欢迎的公开模板')).toBeInTheDocument();
    });

    it('should render template names', () => {
      renderWithProviders(<PopularTemplates />);
      expect(screen.getByText('LLM 微调模板')).toBeInTheDocument();
      expect(screen.getByText('CV 训练模板')).toBeInTheDocument();
      expect(screen.getByText('无描述模板')).toBeInTheDocument();
    });

    it('should render template descriptions', () => {
      renderWithProviders(<PopularTemplates />);
      expect(screen.getByText('大语言模型微调训练模板')).toBeInTheDocument();
      expect(screen.getByText('计算机视觉训练模板')).toBeInTheDocument();
    });

    it('should render 无描述 for templates without description', () => {
      renderWithProviders(<PopularTemplates />);
      expect(screen.getByText('无描述')).toBeInTheDocument();
    });

    it('should render usage counts', () => {
      renderWithProviders(<PopularTemplates />);
      expect(screen.getByText('128 次使用')).toBeInTheDocument();
      expect(screen.getByText('89 次使用')).toBeInTheDocument();
    });

    it('should render visibility badges', () => {
      renderWithProviders(<PopularTemplates />);
      const publicBadges = screen.getAllByText('公开');
      expect(publicBadges.length).toBe(2);
      expect(screen.getByText('团队')).toBeInTheDocument();
    });

    it('should render use buttons', () => {
      renderWithProviders(<PopularTemplates />);
      const useButtons = screen.getAllByText('使用此模板');
      expect(useButtons.length).toBe(3);
    });
  });

  describe('加载状态', () => {
    it('should display loading text when loading', () => {
      mockUsePopularTemplates.mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      });
      renderWithProviders(<PopularTemplates />);
      expect(screen.getByText('加载中...')).toBeInTheDocument();
    });
  });

  describe('错误状态', () => {
    it('should display error message on failure', () => {
      mockUsePopularTemplates.mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Network error'),
      });
      renderWithProviders(<PopularTemplates />);
      expect(screen.getByText('加载热门模板失败')).toBeInTheDocument();
    });
  });

  describe('空状态', () => {
    it('should display empty state when no templates', () => {
      mockUsePopularTemplates.mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      });
      renderWithProviders(<PopularTemplates />);
      expect(screen.getByText('暂无热门模板')).toBeInTheDocument();
    });
  });

  describe('交互', () => {
    it('should call onUseTemplate when clicking use button', () => {
      const handleUse = vi.fn();
      renderWithProviders(<PopularTemplates onUseTemplate={handleUse} />);
      const useButtons = screen.getAllByText('使用此模板');
      fireEvent.click(useButtons[0]);
      expect(handleUse).toHaveBeenCalledWith(1);
    });
  });

  describe('limit 参数', () => {
    it('should pass limit to usePopularTemplates', () => {
      renderWithProviders(<PopularTemplates limit={3} />);
      expect(mockUsePopularTemplates).toHaveBeenCalledWith(3);
    });

    it('should use default limit of 5', () => {
      renderWithProviders(<PopularTemplates />);
      expect(mockUsePopularTemplates).toHaveBeenCalledWith(5);
    });
  });
});
