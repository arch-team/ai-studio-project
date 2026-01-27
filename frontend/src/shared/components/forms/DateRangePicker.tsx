/**
 * DateRangePicker Component
 *
 * Task: T076 - 时间范围选择器组件
 *
 * 可复用的日期范围选择器，用于报表页面的日期过滤。
 * 支持预设时间范围和自定义日期选择。
 *
 * 功能:
 * - 预设范围: 今天、过去7天、过去30天、过去90天
 * - 自定义日期范围选择
 * - 中文标签支持
 * - ISO 8601 日期格式输出 (YYYY-MM-DD)
 */

import { useCallback, useMemo } from 'react';
import { DateRangePicker as CloudscapeDateRangePicker } from '@cloudscape-design/components';
import type { DateRangePickerProps } from '@cloudscape-design/components';

// === 类型定义 ===

/**
 * 日期范围
 */
export interface DateRange {
  /** 开始日期 (ISO 8601 格式: YYYY-MM-DD) */
  startDate: string;
  /** 结束日期 (ISO 8601 格式: YYYY-MM-DD) */
  endDate: string;
}

/**
 * 组件属性
 */
export interface DateRangePickerComponentProps {
  /** 当前值 */
  value: DateRange | null;
  /** 值变更回调 */
  onChange: (range: DateRange | null) => void;
  /** 占位符文本 */
  placeholder?: string;
  /** 是否禁用 */
  disabled?: boolean;
  /** 最大允许的日期范围 (天数) */
  maxRangeDays?: number;
  /** 是否显示时间选择 */
  showTime?: boolean;
}

// === 常量配置 ===

/**
 * 预设时间范围选项
 */
const RELATIVE_OPTIONS: DateRangePickerProps.RelativeOption[] = [
  { key: 'today', amount: 0, unit: 'day', type: 'relative' },
  { key: 'last-7-days', amount: 7, unit: 'day', type: 'relative' },
  { key: 'last-30-days', amount: 30, unit: 'day', type: 'relative' },
  { key: 'last-90-days', amount: 90, unit: 'day', type: 'relative' },
];

/**
 * 国际化字符串 (中文)
 */
const I18N_STRINGS: DateRangePickerProps.I18nStrings = {
  todayAriaLabel: '今天',
  nextMonthAriaLabel: '下个月',
  previousMonthAriaLabel: '上个月',
  customRelativeRangeDurationLabel: '持续时间',
  customRelativeRangeDurationPlaceholder: '输入持续时间',
  customRelativeRangeOptionLabel: '自定义范围',
  customRelativeRangeOptionDescription: '设置自定义时间范围',
  customRelativeRangeUnitLabel: '时间单位',
  formatRelativeRange: (e) => {
    // 处理 "今天" 的特殊情况
    if (e.amount === 0 && e.unit === 'day') {
      return '今天';
    }
    const unitText = e.unit === 'day' ? '天' : e.unit === 'week' ? '周' : '月';
    return `过去 ${e.amount} ${unitText}`;
  },
  formatUnit: (unit, value) => {
    if (unit === 'day') return value === 1 ? '天' : '天';
    if (unit === 'week') return value === 1 ? '周' : '周';
    if (unit === 'month') return value === 1 ? '月' : '月';
    return unit;
  },
  dateTimeConstraintText: '',
  relativeModeTitle: '相对时间',
  absoluteModeTitle: '绝对时间',
  relativeRangeSelectionHeading: '选择时间范围',
  startDateLabel: '开始日期',
  endDateLabel: '结束日期',
  startTimeLabel: '开始时间',
  endTimeLabel: '结束时间',
  clearButtonLabel: '清除',
  cancelButtonLabel: '取消',
  applyButtonLabel: '应用',
};

// === 工具函数 ===

/**
 * 格式化日期为 ISO 8601 日期格式 (YYYY-MM-DD)
 */
function formatDateToISO(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * 将 Cloudscape 日期范围值转换为简化的 DateRange
 */
function convertToDateRange(value: DateRangePickerProps.Value | null): DateRange | null {
  if (!value) {
    return null;
  }

  const now = new Date();
  let startDate: Date;
  let endDate: Date = now;

  if (value.type === 'relative') {
    const { amount, unit } = value;

    // 处理 "今天" 的特殊情况
    if (amount === 0) {
      startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      endDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);
    } else {
      // 计算相对时间
      switch (unit) {
        case 'day':
          startDate = new Date(now.getTime() - amount * 24 * 60 * 60 * 1000);
          break;
        case 'week':
          startDate = new Date(now.getTime() - amount * 7 * 24 * 60 * 60 * 1000);
          break;
        case 'month':
          startDate = new Date(now);
          startDate.setMonth(startDate.getMonth() - amount);
          break;
        default:
          startDate = new Date(now.getTime() - amount * 24 * 60 * 60 * 1000);
      }
    }
  } else {
    // 绝对时间
    startDate = new Date(value.startDate);
    endDate = new Date(value.endDate);
  }

  return {
    startDate: formatDateToISO(startDate),
    endDate: formatDateToISO(endDate),
  };
}

/**
 * 将简化的 DateRange 转换为 Cloudscape 日期范围值
 */
function convertFromDateRange(range: DateRange | null): DateRangePickerProps.Value | null {
  if (!range) {
    return null;
  }

  return {
    type: 'absolute',
    startDate: range.startDate,
    endDate: range.endDate,
  };
}

// === 组件实现 ===

/**
 * 日期范围选择器组件
 *
 * @example
 * ```tsx
 * const [dateRange, setDateRange] = useState<DateRange | null>(null);
 *
 * <DateRangePicker
 *   value={dateRange}
 *   onChange={setDateRange}
 *   placeholder="选择日期范围"
 * />
 * ```
 */
export function DateRangePicker({
  value,
  onChange,
  placeholder = '选择日期范围',
  disabled = false,
  maxRangeDays = 365,
  showTime = false,
}: DateRangePickerComponentProps) {
  // 内部值转换
  const internalValue = useMemo(
    () => convertFromDateRange(value),
    [value]
  );

  // 值变更处理
  const handleChange = useCallback(
    ({ detail }: { detail: DateRangePickerProps.ChangeDetail }) => {
      const newRange = convertToDateRange(detail.value);
      onChange(newRange);
    },
    [onChange]
  );

  // 范围验证
  const isValidRange = useCallback(
    (range: DateRangePickerProps.Value | null): DateRangePickerProps.ValidationResult => {
      if (!range) {
        return { valid: true };
      }

      if (range.type === 'absolute') {
        const start = new Date(range.startDate);
        const end = new Date(range.endDate);

        // 检查开始日期是否晚于结束日期
        if (start > end) {
          return {
            valid: false,
            errorMessage: '开始日期不能晚于结束日期',
          };
        }

        // 检查范围是否超过最大限制
        const diffDays = Math.ceil(
          (end.getTime() - start.getTime()) / (24 * 60 * 60 * 1000)
        );
        if (diffDays > maxRangeDays) {
          return {
            valid: false,
            errorMessage: `日期范围不能超过 ${maxRangeDays} 天`,
          };
        }
      }

      return { valid: true };
    },
    [maxRangeDays]
  );

  // 更新国际化字符串 (包含最大范围提示)
  const i18nStrings = useMemo(
    () => ({
      ...I18N_STRINGS,
      dateTimeConstraintText: `日期范围最长 ${maxRangeDays} 天`,
    }),
    [maxRangeDays]
  );

  return (
    <CloudscapeDateRangePicker
      value={internalValue}
      onChange={handleChange}
      relativeOptions={RELATIVE_OPTIONS}
      isValidRange={isValidRange}
      i18nStrings={i18nStrings}
      placeholder={placeholder}
      disabled={disabled}
      dateOnly={!showTime}
      expandToViewport
    />
  );
}

export default DateRangePicker;
