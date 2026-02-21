/**
 * Billing types 单元测试
 *
 * 测试计费模块类型定义和 UI 常量
 */

import { describe, it, expect } from 'vitest';
import {
  BILLING_PERIOD_LABELS,
  COST_CATEGORY_LABELS,
  COST_CATEGORY_COLORS,
  RESOURCE_COST_TYPE_LABELS,
} from '@features/billing/types';
import type {
  BillingPeriod,
  CostCategory,
  ResourceCostType,
} from '@features/billing/types';

describe('Billing Types', () => {
  describe('BILLING_PERIOD_LABELS', () => {
    it('应该包含所有计费周期标签', () => {
      const periods: BillingPeriod[] = ['daily', 'weekly', 'monthly', 'yearly'];
      for (const period of periods) {
        expect(BILLING_PERIOD_LABELS[period]).toBeDefined();
        expect(typeof BILLING_PERIOD_LABELS[period]).toBe('string');
      }
    });

    it('应该有正确的中文标签', () => {
      expect(BILLING_PERIOD_LABELS.daily).toBe('按天');
      expect(BILLING_PERIOD_LABELS.weekly).toBe('按周');
      expect(BILLING_PERIOD_LABELS.monthly).toBe('按月');
      expect(BILLING_PERIOD_LABELS.yearly).toBe('按年');
    });
  });

  describe('COST_CATEGORY_LABELS', () => {
    it('应该包含所有成本类别标签', () => {
      const categories: CostCategory[] = [
        'compute',
        'storage',
        'network',
        'data_transfer',
        'other',
      ];
      for (const cat of categories) {
        expect(COST_CATEGORY_LABELS[cat]).toBeDefined();
        expect(typeof COST_CATEGORY_LABELS[cat]).toBe('string');
      }
    });

    it('应该有正确的中文标签', () => {
      expect(COST_CATEGORY_LABELS.compute).toBe('计算');
      expect(COST_CATEGORY_LABELS.storage).toBe('存储');
      expect(COST_CATEGORY_LABELS.network).toBe('网络');
      expect(COST_CATEGORY_LABELS.data_transfer).toBe('数据传输');
      expect(COST_CATEGORY_LABELS.other).toBe('其他');
    });
  });

  describe('COST_CATEGORY_COLORS', () => {
    it('应该包含所有成本类别颜色', () => {
      const categories: CostCategory[] = [
        'compute',
        'storage',
        'network',
        'data_transfer',
        'other',
      ];
      for (const cat of categories) {
        expect(COST_CATEGORY_COLORS[cat]).toBeDefined();
        expect(COST_CATEGORY_COLORS[cat]).toMatch(/^#[0-9a-f]{6}$/i);
      }
    });

    it('每个类别应该有不同的颜色', () => {
      const colors = Object.values(COST_CATEGORY_COLORS);
      const uniqueColors = new Set(colors);
      expect(uniqueColors.size).toBe(colors.length);
    });
  });

  describe('RESOURCE_COST_TYPE_LABELS', () => {
    it('应该包含所有资源成本类型标签', () => {
      const types: ResourceCostType[] = [
        'training_job',
        'space',
        'storage',
        'cluster',
      ];
      for (const type of types) {
        expect(RESOURCE_COST_TYPE_LABELS[type]).toBeDefined();
        expect(typeof RESOURCE_COST_TYPE_LABELS[type]).toBe('string');
      }
    });

    it('应该有正确的中文标签', () => {
      expect(RESOURCE_COST_TYPE_LABELS.training_job).toBe('训练任务');
      expect(RESOURCE_COST_TYPE_LABELS.space).toBe('开发空间');
      expect(RESOURCE_COST_TYPE_LABELS.storage).toBe('存储');
      expect(RESOURCE_COST_TYPE_LABELS.cluster).toBe('集群');
    });
  });
});
