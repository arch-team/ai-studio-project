/**
 * 日期范围计算工具函数测试
 *
 * Task: T092 - 前端单元测试覆盖
 */

import { describe, it, expect } from 'vitest';
import { calculateTimeRange, calculateDateRange } from '@shared/utils/dateRange';

describe('dateRange', () => {
  describe('calculateTimeRange', () => {
    it('应在 dateRange 为 null 时使用默认小时数', () => {
      const result = calculateTimeRange(null, 1);
      const start = new Date(result.startTime);
      const end = new Date(result.endTime);
      const diffMs = end.getTime() - start.getTime();
      const diffHours = diffMs / (1000 * 60 * 60);
      // 允许小误差
      expect(diffHours).toBeCloseTo(1, 0);
    });

    it('应处理相对时间范围 (天)', () => {
      const result = calculateTimeRange({
        type: 'relative',
        amount: 7,
        unit: 'day',
      });
      const start = new Date(result.startTime);
      const end = new Date(result.endTime);
      const diffDays = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
      expect(diffDays).toBeCloseTo(7, 0);
    });

    it('应处理相对时间范围 (小时)', () => {
      const result = calculateTimeRange({
        type: 'relative',
        amount: 6,
        unit: 'hour',
      });
      const start = new Date(result.startTime);
      const end = new Date(result.endTime);
      const diffHours = (end.getTime() - start.getTime()) / (1000 * 60 * 60);
      expect(diffHours).toBeCloseTo(6, 0);
    });

    it('应处理相对时间范围 (周)', () => {
      const result = calculateTimeRange({
        type: 'relative',
        amount: 2,
        unit: 'week',
      });
      const start = new Date(result.startTime);
      const end = new Date(result.endTime);
      const diffDays = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
      expect(diffDays).toBeCloseTo(14, 0);
    });

    it('应处理相对时间范围 (月)', () => {
      const result = calculateTimeRange({
        type: 'relative',
        amount: 1,
        unit: 'month',
      });
      const start = new Date(result.startTime);
      const end = new Date(result.endTime);
      const diffDays = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
      expect(diffDays).toBeCloseTo(30, 0);
    });

    it('应处理绝对时间范围', () => {
      const result = calculateTimeRange({
        type: 'absolute',
        startDate: '2024-01-01T00:00:00Z',
        endDate: '2024-01-15T00:00:00Z',
      });
      expect(result.startTime).toContain('2024-01-01');
      expect(result.endTime).toContain('2024-01-15');
    });

    it('应返回 ISO 字符串格式', () => {
      const result = calculateTimeRange(null);
      expect(result.startTime).toMatch(/^\d{4}-\d{2}-\d{2}T/);
      expect(result.endTime).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    });

    it('应处理未知时间单位时使用天作为默认值', () => {
      const result = calculateTimeRange({
        type: 'relative',
        amount: 3,
        unit: 'unknown_unit' as 'day',
      });
      const start = new Date(result.startTime);
      const end = new Date(result.endTime);
      const diffDays = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
      // 未知单位使用默认 day 单位
      expect(diffDays).toBeCloseTo(3, 0);
    });
  });

  describe('calculateDateRange', () => {
    it('应在 dateRange 为 null 时使用默认天数', () => {
      const result = calculateDateRange(null, 30);
      const start = new Date(result.startDate);
      const end = new Date(result.endDate);
      const diffDays = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24);
      expect(diffDays).toBeCloseTo(30, 0);
    });

    it('应处理相对日期范围', () => {
      const result = calculateDateRange({
        type: 'relative',
        amount: 7,
        unit: 'day',
      });
      expect(result.startDate).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(result.endDate).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    });

    it('应处理绝对日期范围', () => {
      const result = calculateDateRange({
        type: 'absolute',
        startDate: '2024-01-01',
        endDate: '2024-01-31',
      });
      expect(result.startDate).toBe('2024-01-01');
      expect(result.endDate).toBe('2024-01-31');
    });

    it('应返回 YYYY-MM-DD 格式', () => {
      const result = calculateDateRange(null);
      expect(result.startDate).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(result.endDate).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    });
  });
});
