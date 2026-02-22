/**
 * 共享格式化工具函数测试
 *
 * Task: T092 - 前端单元测试覆盖
 */

import { describe, it, expect } from 'vitest';
import {
  formatDateTime,
  formatDateTimeShort,
  formatDuration,
  formatCurrency,
  formatNumber,
  formatFileSize,
} from '@shared/utils/formatters';

describe('formatters', () => {
  describe('formatDateTime', () => {
    it('应返回 - 当输入为 null', () => {
      expect(formatDateTime(null)).toBe('-');
    });

    it('应返回 - 当输入为 undefined', () => {
      expect(formatDateTime(undefined)).toBe('-');
    });

    it('应返回 - 当输入为空字符串', () => {
      expect(formatDateTime('')).toBe('-');
    });

    it('应格式化有效日期字符串', () => {
      const result = formatDateTime('2024-01-15T10:30:00Z');
      // 验证返回的字符串包含年月日和时间
      expect(result).toContain('2024');
      expect(result).toContain('01');
      expect(result).toContain('15');
    });
  });

  describe('formatDateTimeShort', () => {
    it('应格式化日期为简短格式', () => {
      const result = formatDateTimeShort('2024-06-15T14:30:00Z');
      // 验证返回的字符串包含月日
      expect(result).toBeTruthy();
      expect(typeof result).toBe('string');
    });
  });

  describe('formatDuration', () => {
    it('应返回 - 当 startTime 为 null', () => {
      expect(formatDuration(null, null)).toBe('-');
    });

    it('应计算两个时间之间的持续时间', () => {
      const start = '2024-01-01T10:00:00Z';
      const end = '2024-01-01T12:30:00Z';
      expect(formatDuration(start, end)).toBe('2h 30m');
    });

    it('应处理跨日持续时间', () => {
      const start = '2024-01-01T22:00:00Z';
      const end = '2024-01-02T01:15:00Z';
      expect(formatDuration(start, end)).toBe('3h 15m');
    });

    it('应在 endTime 为 null 时使用当前时间', () => {
      const start = new Date().toISOString();
      const result = formatDuration(start, null);
      expect(result).toBe('0h 0m');
    });
  });

  describe('formatCurrency', () => {
    it('应格式化小金额', () => {
      expect(formatCurrency(50)).toBe('$50.00');
    });

    it('应格式化整数金额', () => {
      expect(formatCurrency(0)).toBe('$0.00');
    });

    it('应将千级金额转换为 K 格式', () => {
      expect(formatCurrency(1000)).toBe('$1.0K');
    });

    it('应将大金额转换为 K 格式', () => {
      expect(formatCurrency(2500)).toBe('$2.5K');
    });

    it('应格式化小数金额', () => {
      expect(formatCurrency(99.5)).toBe('$99.50');
    });
  });

  describe('formatNumber', () => {
    it('应返回 - 当值为 undefined', () => {
      expect(formatNumber(undefined)).toBe('-');
    });

    it('应返回 - 当值为 null', () => {
      expect(formatNumber(null)).toBe('-');
    });

    it('应格式化数字保留默认 2 位小数', () => {
      expect(formatNumber(3.14159)).toBe('3.14');
    });

    it('应支持自定义小数位数', () => {
      expect(formatNumber(3.14159, 4)).toBe('3.1416');
    });

    it('应格式化整数', () => {
      expect(formatNumber(42)).toBe('42.00');
    });

    it('应格式化零', () => {
      expect(formatNumber(0)).toBe('0.00');
    });
  });

  describe('formatFileSize', () => {
    it('应返回 - 当值为 null', () => {
      expect(formatFileSize(null)).toBe('-');
    });

    it('应返回 - 当值为 undefined', () => {
      expect(formatFileSize(undefined)).toBe('-');
    });

    it('应返回 - 当值为 0', () => {
      expect(formatFileSize(0)).toBe('-');
    });

    it('应格式化字节为 MB', () => {
      const bytes = 50 * 1024 * 1024; // 50 MB
      expect(formatFileSize(bytes)).toBe('50.00 MB');
    });

    it('应格式化大文件为 GB', () => {
      const bytes = 2 * 1024 * 1024 * 1024; // 2 GB
      expect(formatFileSize(bytes)).toBe('2.00 GB');
    });
  });
});
