/**
 * Billing hooks 单元测试
 *
 * 测试计费模块业务逻辑 hooks
 */

import { describe, it, expect } from 'vitest';
import { renderHook } from '@testing-library/react';
import {
  useFormatCurrency,
  useCostChangePercentage,
  useCostDistribution,
  useDailyCostTrend,
  useTopCostCategory,
} from '@features/billing/hooks';
import type { CostSummary, CostBreakdown, DailyCost } from '@features/billing/types';

describe('useFormatCurrency', () => {
  it('应该正确格式化金额', () => {
    const { result } = renderHook(() => useFormatCurrency());
    const format = result.current;

    const formatted = format(1234.56);
    expect(formatted).toContain('1,234.56');
  });

  it('null 值应该返回 "-"', () => {
    const { result } = renderHook(() => useFormatCurrency());
    const format = result.current;
    expect(format(null)).toBe('-');
  });

  it('undefined 值应该返回 "-"', () => {
    const { result } = renderHook(() => useFormatCurrency());
    const format = result.current;
    expect(format(undefined)).toBe('-');
  });

  it('0 应该格式化为货币', () => {
    const { result } = renderHook(() => useFormatCurrency());
    const format = result.current;
    const formatted = format(0);
    expect(formatted).toContain('0.00');
  });

  it('应该支持指定货币', () => {
    const { result } = renderHook(() => useFormatCurrency());
    const format = result.current;
    const formatted = format(100, 'CNY');
    expect(formatted).toContain('100.00');
  });
});

describe('useCostChangePercentage', () => {
  it('应该正确计算成本增加百分比', () => {
    const { result } = renderHook(() => useCostChangePercentage(150, 100));
    expect(result.current).not.toBeNull();
    expect(result.current!.value).toBe(50);
    expect(result.current!.isIncrease).toBe(true);
  });

  it('应该正确计算成本减少百分比', () => {
    const { result } = renderHook(() => useCostChangePercentage(80, 100));
    expect(result.current).not.toBeNull();
    expect(result.current!.value).toBe(20);
    expect(result.current!.isIncrease).toBe(false);
  });

  it('当前成本 undefined 应该返回 null', () => {
    const { result } = renderHook(() => useCostChangePercentage(undefined, 100));
    expect(result.current).toBeNull();
  });

  it('上期成本 undefined 应该返回 null', () => {
    const { result } = renderHook(() => useCostChangePercentage(100, undefined));
    expect(result.current).toBeNull();
  });

  it('上期成本为 0 应该返回 null', () => {
    const { result } = renderHook(() => useCostChangePercentage(100, 0));
    expect(result.current).toBeNull();
  });

  it('成本不变应该返回 0%', () => {
    const { result } = renderHook(() => useCostChangePercentage(100, 100));
    expect(result.current).not.toBeNull();
    expect(result.current!.value).toBe(0);
  });
});

describe('useCostDistribution', () => {
  it('undefined 输入应该返回空数组', () => {
    const { result } = renderHook(() => useCostDistribution(undefined));
    expect(result.current).toEqual([]);
  });

  it('总成本为 0 应该返回空数组', () => {
    const summary: CostSummary = {
      total_cost_usd: 0,
      compute_cost_usd: 0,
      storage_cost_usd: 0,
      network_cost_usd: 0,
      data_transfer_cost_usd: 0,
      other_cost_usd: 0,
      period_start: '2025-01-01',
      period_end: '2025-01-31',
    };
    const { result } = renderHook(() => useCostDistribution(summary));
    expect(result.current).toEqual([]);
  });

  it('应该正确计算成本分布', () => {
    const summary: CostSummary = {
      total_cost_usd: 1000,
      compute_cost_usd: 600,
      storage_cost_usd: 200,
      network_cost_usd: 100,
      data_transfer_cost_usd: 50,
      other_cost_usd: 50,
      period_start: '2025-01-01',
      period_end: '2025-01-31',
    };
    const { result } = renderHook(() => useCostDistribution(summary));

    expect(result.current.length).toBe(5);
    // 应该按成本从高到低排序
    expect(result.current[0].category).toBe('compute');
    expect(result.current[0].percentage).toBe(60);
    expect(result.current[1].category).toBe('storage');
    expect(result.current[1].percentage).toBe(20);
  });

  it('应该过滤掉成本为 0 的类别', () => {
    const summary: CostSummary = {
      total_cost_usd: 100,
      compute_cost_usd: 80,
      storage_cost_usd: 20,
      network_cost_usd: 0,
      data_transfer_cost_usd: 0,
      other_cost_usd: 0,
      period_start: '2025-01-01',
      period_end: '2025-01-31',
    };
    const { result } = renderHook(() => useCostDistribution(summary));

    expect(result.current.length).toBe(2);
    expect(result.current[0].category).toBe('compute');
    expect(result.current[1].category).toBe('storage');
  });
});

describe('useDailyCostTrend', () => {
  it('undefined 输入应该返回全零统计', () => {
    const { result } = renderHook(() => useDailyCostTrend(undefined));
    expect(result.current.average).toBe(0);
    expect(result.current.max).toBe(0);
    expect(result.current.min).toBe(0);
    expect(result.current.total).toBe(0);
  });

  it('空数组应该返回全零统计', () => {
    const { result } = renderHook(() => useDailyCostTrend([]));
    expect(result.current.average).toBe(0);
    expect(result.current.total).toBe(0);
  });

  it('应该正确计算趋势统计', () => {
    const dailyCosts: DailyCost[] = [
      {
        date: '2025-01-01',
        total_cost_usd: 100,
        compute_cost_usd: 80,
        storage_cost_usd: 15,
        other_cost_usd: 5,
      },
      {
        date: '2025-01-02',
        total_cost_usd: 200,
        compute_cost_usd: 160,
        storage_cost_usd: 30,
        other_cost_usd: 10,
      },
      {
        date: '2025-01-03',
        total_cost_usd: 150,
        compute_cost_usd: 120,
        storage_cost_usd: 20,
        other_cost_usd: 10,
      },
    ];

    const { result } = renderHook(() => useDailyCostTrend(dailyCosts));

    expect(result.current.total).toBe(450);
    expect(result.current.average).toBe(150);
    expect(result.current.max).toBe(200);
    expect(result.current.min).toBe(100);
  });

  it('单天数据应该返回正确统计', () => {
    const dailyCosts: DailyCost[] = [
      {
        date: '2025-01-01',
        total_cost_usd: 100,
        compute_cost_usd: 80,
        storage_cost_usd: 15,
        other_cost_usd: 5,
      },
    ];

    const { result } = renderHook(() => useDailyCostTrend(dailyCosts));

    expect(result.current.total).toBe(100);
    expect(result.current.average).toBe(100);
    expect(result.current.max).toBe(100);
    expect(result.current.min).toBe(100);
  });
});

describe('useTopCostCategory', () => {
  it('undefined 输入应该返回 null', () => {
    const { result } = renderHook(() => useTopCostCategory(undefined));
    expect(result.current).toBeNull();
  });

  it('空数组应该返回 null', () => {
    const { result } = renderHook(() => useTopCostCategory([]));
    expect(result.current).toBeNull();
  });

  it('应该返回成本最高的类别', () => {
    const breakdown: CostBreakdown[] = [
      {
        category: 'storage',
        cost_usd: 200,
        percentage: 20,
        details: [],
      },
      {
        category: 'compute',
        cost_usd: 800,
        percentage: 80,
        details: [],
      },
    ];

    const { result } = renderHook(() => useTopCostCategory(breakdown));
    expect(result.current).not.toBeNull();
    expect(result.current!.category).toBe('compute');
    expect(result.current!.cost_usd).toBe(800);
  });

  it('单个类别应该直接返回', () => {
    const breakdown: CostBreakdown[] = [
      {
        category: 'compute',
        cost_usd: 500,
        percentage: 100,
        details: [],
      },
    ];

    const { result } = renderHook(() => useTopCostCategory(breakdown));
    expect(result.current!.category).toBe('compute');
  });
});
