/**
 * Billing business logic hooks.
 */

import { useMemo } from 'react';
import type { CostSummary, CostBreakdown, DailyCost, CostCategory } from '../types';

/**
 * 格式化金额
 */
export function useFormatCurrency() {
  return (amount: number | null | undefined, currency: string = 'USD'): string => {
    if (amount === null || amount === undefined) return '-';

    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };
}

/**
 * 计算成本变化百分比
 */
export function useCostChangePercentage(
  currentCost: number | undefined,
  previousCost: number | undefined
): { value: number; isIncrease: boolean } | null {
  return useMemo(() => {
    if (
      currentCost === undefined ||
      previousCost === undefined ||
      previousCost === 0
    ) {
      return null;
    }

    const change = ((currentCost - previousCost) / previousCost) * 100;
    return {
      value: Math.abs(change),
      isIncrease: change > 0,
    };
  }, [currentCost, previousCost]);
}

/**
 * 计算成本分类占比
 */
export function useCostDistribution(summary: CostSummary | undefined) {
  return useMemo(() => {
    if (!summary || summary.total_cost_usd === 0) {
      return [];
    }

    const categories: { category: CostCategory; cost: number; percentage: number }[] = [
      {
        category: 'compute',
        cost: summary.compute_cost_usd,
        percentage: (summary.compute_cost_usd / summary.total_cost_usd) * 100,
      },
      {
        category: 'storage',
        cost: summary.storage_cost_usd,
        percentage: (summary.storage_cost_usd / summary.total_cost_usd) * 100,
      },
      {
        category: 'network',
        cost: summary.network_cost_usd,
        percentage: (summary.network_cost_usd / summary.total_cost_usd) * 100,
      },
      {
        category: 'data_transfer',
        cost: summary.data_transfer_cost_usd,
        percentage: (summary.data_transfer_cost_usd / summary.total_cost_usd) * 100,
      },
      {
        category: 'other',
        cost: summary.other_cost_usd,
        percentage: (summary.other_cost_usd / summary.total_cost_usd) * 100,
      },
    ];

    return categories.filter((c) => c.cost > 0).sort((a, b) => b.cost - a.cost);
  }, [summary]);
}

/**
 * 计算每日成本趋势统计
 */
export function useDailyCostTrend(dailyCosts: DailyCost[] | undefined) {
  return useMemo(() => {
    if (!dailyCosts || dailyCosts.length === 0) {
      return {
        average: 0,
        max: 0,
        min: 0,
        total: 0,
      };
    }

    const costs = dailyCosts.map((d) => d.total_cost_usd);
    const total = costs.reduce((sum, c) => sum + c, 0);

    return {
      average: total / costs.length,
      max: Math.max(...costs),
      min: Math.min(...costs),
      total,
    };
  }, [dailyCosts]);
}

/**
 * 获取成本分类中占比最高的类别
 */
export function useTopCostCategory(breakdown: CostBreakdown[] | undefined) {
  return useMemo(() => {
    if (!breakdown || breakdown.length === 0) {
      return null;
    }

    return [...breakdown].sort((a, b) => b.cost_usd - a.cost_usd)[0];
  }, [breakdown]);
}
