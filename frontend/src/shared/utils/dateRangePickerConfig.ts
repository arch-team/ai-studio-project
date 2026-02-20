import type { DateRangePickerProps } from "@cloudscape-design/components";

/**
 * DateRangePicker 的国际化字符串配置（中文）
 * 供各页面复用，避免重复定义
 */
export const DATE_RANGE_PICKER_I18N: DateRangePickerProps.I18nStrings = {
  todayAriaLabel: "今天",
  nextMonthAriaLabel: "下个月",
  previousMonthAriaLabel: "上个月",
  customRelativeRangeDurationLabel: "时长",
  customRelativeRangeDurationPlaceholder: "输入时长",
  customRelativeRangeOptionLabel: "自定义范围",
  customRelativeRangeOptionDescription: "设置自定义范围",
  customRelativeRangeUnitLabel: "时间单位",
  formatRelativeRange: (e) => {
    const unitMap: Record<string, string> = {
      second: "秒",
      minute: "分钟",
      hour: "小时",
      day: "天",
      week: "周",
      month: "月",
      year: "年",
    };
    return `最近 ${e.amount} ${unitMap[e.unit] ?? e.unit}`;
  },
  formatUnit: (unit) => {
    const unitMap: Record<string, string> = {
      second: "秒",
      minute: "分钟",
      hour: "小时",
      day: "天",
      week: "周",
      month: "月",
      year: "年",
    };
    return unitMap[unit] ?? unit;
  },
  relativeModeTitle: "相对时间",
  absoluteModeTitle: "绝对时间",
  relativeRangeSelectionHeading: "选择时间范围",
  startDateLabel: "开始日期",
  endDateLabel: "结束日期",
  startTimeLabel: "开始时间",
  endTimeLabel: "结束时间",
  clearButtonLabel: "清除并关闭",
  cancelButtonLabel: "取消",
  applyButtonLabel: "应用",
};

/**
 * DateRangePicker 验证函数 - 确保开始时间不晚于结束时间
 */
export const validateDateRange = (
  value: DateRangePickerProps.Value | null,
): DateRangePickerProps.ValidationResult => {
  if (value?.type === "absolute") {
    if (new Date(value.startDate) > new Date(value.endDate)) {
      return { valid: false, errorMessage: "开始日期不能晚于结束日期" };
    }
  }
  return { valid: true };
};
