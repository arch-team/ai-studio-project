/**
 * DateRangePicker 配置测试
 *
 * Task: T092 - 前端单元测试覆盖
 */

import { describe, it, expect } from 'vitest';
import {
  DATE_RANGE_PICKER_I18N,
  validateDateRange,
} from '@shared/utils/dateRangePickerConfig';

describe('dateRangePickerConfig', () => {
  describe('DATE_RANGE_PICKER_I18N', () => {
    it('应包含中文国际化字符串', () => {
      expect(DATE_RANGE_PICKER_I18N.todayAriaLabel).toBe('今天');
      expect(DATE_RANGE_PICKER_I18N.cancelButtonLabel).toBe('取消');
      expect(DATE_RANGE_PICKER_I18N.applyButtonLabel).toBe('应用');
      expect(DATE_RANGE_PICKER_I18N.startDateLabel).toBe('开始日期');
      expect(DATE_RANGE_PICKER_I18N.endDateLabel).toBe('结束日期');
    });

    it('formatRelativeRange 应正确格式化相对范围', () => {
      const fn = DATE_RANGE_PICKER_I18N.formatRelativeRange!;

      expect(fn({ amount: 7, unit: 'day' } as never)).toBe('最近 7 天');
      expect(fn({ amount: 1, unit: 'hour' } as never)).toBe('最近 1 小时');
      expect(fn({ amount: 2, unit: 'week' } as never)).toBe('最近 2 周');
      expect(fn({ amount: 3, unit: 'month' } as never)).toBe('最近 3 月');
    });

    it('formatRelativeRange 应处理未知单位', () => {
      const fn = DATE_RANGE_PICKER_I18N.formatRelativeRange!;
      expect(fn({ amount: 5, unit: 'unknown' } as never)).toBe('最近 5 unknown');
    });

    it('formatUnit 应正确格式化时间单位', () => {
      const fn = DATE_RANGE_PICKER_I18N.formatUnit!;

      expect(fn('day', 1)).toBe('天');
      expect(fn('hour', 1)).toBe('小时');
      expect(fn('week', 1)).toBe('周');
      expect(fn('month', 1)).toBe('月');
      expect(fn('minute', 1)).toBe('分钟');
      expect(fn('second', 1)).toBe('秒');
      expect(fn('year', 1)).toBe('年');
    });

    it('formatUnit 应处理未知单位', () => {
      const fn = DATE_RANGE_PICKER_I18N.formatUnit!;
      expect(fn('unknown' as 'day', 1)).toBe('unknown');
    });
  });

  describe('validateDateRange', () => {
    it('应对 null 返回有效', () => {
      expect(validateDateRange(null)).toEqual({ valid: true });
    });

    it('应对相对时间范围返回有效', () => {
      const result = validateDateRange({
        type: 'relative',
        amount: 7,
        unit: 'day',
      });
      expect(result).toEqual({ valid: true });
    });

    it('应对有效的绝对时间范围返回有效', () => {
      const result = validateDateRange({
        type: 'absolute',
        startDate: '2024-01-01',
        endDate: '2024-01-31',
      });
      expect(result).toEqual({ valid: true });
    });

    it('应对开始日期晚于结束日期返回无效', () => {
      const result = validateDateRange({
        type: 'absolute',
        startDate: '2024-02-01',
        endDate: '2024-01-01',
      });
      expect(result).toEqual({
        valid: false,
        errorMessage: '开始日期不能晚于结束日期',
      });
    });
  });
});
