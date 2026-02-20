/**
 * Resource Usage Report Page
 *
 * Task: T074 - 资源使用报表前端页面
 * 功能:
 * - 展示用户和项目的资源使用统计
 * - 时间范围过滤
 * - 按用户/项目/时间聚合
 * - 导出 CSV 功能
 */

import { useState, useMemo } from "react";
import {
  Box,
  Button,
  ColumnLayout,
  Container,
  DateRangePicker,
  Header,
  Select,
  SpaceBetween,
  StatusIndicator,
  Table,
} from "@cloudscape-design/components";
import type {
  DateRangePickerProps,
  SelectProps,
} from "@cloudscape-design/components";
import { useResourceUsage, useExportReport } from "../api";
import { formatNumber, calculateDateRange } from "@shared/utils";
import type {
  GroupBy,
  ResourceUsageFilters,
  ResourceUsageItem,
  ResourceUsageBreakdown,
  DailyResourceUsage,
} from "../types";
import { GROUP_BY_LABELS } from "../types";

// === 常量配置 ===

// 时间范围预设选项
const TIME_RANGE_OPTIONS: DateRangePickerProps.RelativeOption[] = [
  { key: "7d", amount: 7, unit: "day", type: "relative" },
  { key: "14d", amount: 14, unit: "day", type: "relative" },
  { key: "30d", amount: 30, unit: "day", type: "relative" },
  { key: "90d", amount: 90, unit: "day", type: "relative" },
];

// 聚合维度选项
const GROUP_BY_OPTIONS: SelectProps.Option[] = [
  { value: "user", label: GROUP_BY_LABELS.user },
  { value: "project", label: GROUP_BY_LABELS.project },
  { value: "day", label: GROUP_BY_LABELS.day },
];

// === 工具函数 ===

/**
 * 将 breakdown 或 daily_usage 数据转换为表格显示格式
 */
function transformToTableItems(
  data: {
    breakdown?: ResourceUsageBreakdown[];
    daily_usage?: DailyResourceUsage[];
    items?: ResourceUsageItem[];
  },
  groupBy: GroupBy,
): ResourceUsageItem[] {
  // 如果后端返回了 items 字段，直接使用
  if (data.items && data.items.length > 0) {
    return data.items;
  }

  // 否则从 breakdown 或 daily_usage 转换
  if (groupBy === "day" || groupBy === "week" || groupBy === "month") {
    // 按时间聚合，使用 daily_usage
    const dailyUsage = data.daily_usage || [];
    return dailyUsage.map((item) => ({
      dimension_key: item.date,
      dimension_label: item.date,
      total_gpu_hours: item.gpu_hours,
      total_cpu_hours: item.cpu_hours,
      total_memory_gb_hours: item.memory_gb_hours,
      job_count: item.job_count,
      avg_duration_hours: 0, // daily_usage 没有这个字段
    }));
  } else {
    // 按用户或项目聚合，使用 breakdown
    const breakdown = data.breakdown || [];
    return breakdown.map((item) => ({
      dimension_key: item.name,
      dimension_label: item.name,
      total_gpu_hours: item.gpu_hours,
      total_cpu_hours: item.cpu_hours,
      total_memory_gb_hours: item.memory_gb_hours,
      job_count: item.count,
      avg_duration_hours: 0, // breakdown 没有这个字段
    }));
  }
}

// === 子组件 ===

/**
 * 汇总统计卡片
 */
function SummaryCards({
  summary,
}: {
  summary: {
    total_gpu_hours: number;
    total_cpu_hours: number;
    total_memory_gb_hours?: number;
    total_jobs_count?: number;
    total_job_count?: number;
  } | null;
}) {
  if (!summary) {
    return null;
  }

  const jobCount = summary.total_jobs_count ?? summary.total_job_count ?? 0;

  return (
    <Container header={<Header variant="h2">汇总统计</Header>}>
      <ColumnLayout columns={4} variant="text-grid">
        <div>
          <Box variant="awsui-key-label">GPU 总小时</Box>
          <Box variant="awsui-value-large">
            {formatNumber(summary.total_gpu_hours)}
          </Box>
        </div>
        <div>
          <Box variant="awsui-key-label">CPU 总小时</Box>
          <Box variant="awsui-value-large">
            {formatNumber(summary.total_cpu_hours)}
          </Box>
        </div>
        <div>
          <Box variant="awsui-key-label">内存总量 (GB·h)</Box>
          <Box variant="awsui-value-large">
            {formatNumber(summary.total_memory_gb_hours)}
          </Box>
        </div>
        <div>
          <Box variant="awsui-key-label">任务总数</Box>
          <Box variant="awsui-value-large">{jobCount}</Box>
        </div>
      </ColumnLayout>
    </Container>
  );
}

// === 主组件 ===

/**
 * 资源使用报表页面
 */
export function ResourceUsageReportPage() {
  // === 状态管理 ===

  // 时间范围状态 (默认最近 7 天)
  const [dateRange, setDateRange] = useState<DateRangePickerProps.Value | null>(
    {
      type: "relative",
      amount: 7,
      unit: "day",
    } as DateRangePickerProps.RelativeValue,
  );

  // 聚合维度
  const [groupBy, setGroupBy] = useState<GroupBy>("user");

  // === 计算时间范围 ===
  const { startDate: start_date, endDate: end_date } = useMemo(
    () => calculateDateRange(dateRange, 7),
    [dateRange],
  );

  // === 构建过滤器 ===
  const filters: ResourceUsageFilters = useMemo(
    () => ({
      start_date,
      end_date,
      group_by: groupBy,
    }),
    [start_date, end_date, groupBy],
  );

  // === 数据查询 ===
  const { data, isLoading, error, refetch } = useResourceUsage(filters);

  // === 导出功能 ===
  const exportMutation = useExportReport();

  const handleExport = () => {
    exportMutation.mutate({
      report_type: "resource_usage",
      format: "csv",
      start_date,
      end_date,
      group_by: groupBy,
    });
  };

  const handleRefresh = () => {
    refetch();
  };

  // === 转换数据为表格格式 ===
  const tableItems = useMemo(() => {
    if (!data) return [];
    return transformToTableItems(data, groupBy);
  }, [data, groupBy]);

  // === 表格列定义 ===
  const columnDefinitions = useMemo(
    () => [
      {
        id: "dimension_label",
        header:
          groupBy === "user" ? "用户" : groupBy === "project" ? "项目" : "日期",
        cell: (item: ResourceUsageItem) => item.dimension_label,
        sortingField: "dimension_label",
      },
      {
        id: "total_gpu_hours",
        header: "GPU 小时",
        cell: (item: ResourceUsageItem) => formatNumber(item.total_gpu_hours),
        sortingField: "total_gpu_hours",
      },
      {
        id: "total_cpu_hours",
        header: "CPU 小时",
        cell: (item: ResourceUsageItem) => formatNumber(item.total_cpu_hours),
        sortingField: "total_cpu_hours",
      },
      {
        id: "total_memory_gb_hours",
        header: "内存 (GB·h)",
        cell: (item: ResourceUsageItem) =>
          formatNumber(item.total_memory_gb_hours),
        sortingField: "total_memory_gb_hours",
      },
      {
        id: "job_count",
        header: "任务数",
        cell: (item: ResourceUsageItem) => item.job_count,
        sortingField: "job_count",
      },
      {
        id: "avg_duration_hours",
        header: "平均时长 (h)",
        cell: (item: ResourceUsageItem) =>
          formatNumber(item.avg_duration_hours),
        sortingField: "avg_duration_hours",
      },
    ],
    [groupBy],
  );

  // === 错误处理 ===
  if (error) {
    return (
      <Container>
        <Box textAlign="center" color="text-status-error" padding="xl">
          加载失败: {error.message}
        </Box>
      </Container>
    );
  }

  // === 渲染 ===
  return (
    <SpaceBetween size="l" data-testid="resource-usage-report-page">
      {/* 页面标题和操作按钮 */}
      <Header
        variant="h1"
        description="查看用户和项目的资源使用统计"
        actions={
          <SpaceBetween direction="horizontal" size="s">
            <Button
              iconName="refresh"
              onClick={handleRefresh}
              loading={isLoading}
            >
              刷新
            </Button>
            <Button
              variant="primary"
              iconName="download"
              onClick={handleExport}
              loading={exportMutation.isPending}
            >
              导出 CSV
            </Button>
          </SpaceBetween>
        }
      >
        资源使用报表
      </Header>

      {/* 过滤器区域 */}
      <Container>
        <SpaceBetween direction="horizontal" size="m">
          {/* 时间范围选择器 */}
          <div style={{ minWidth: 280 }}>
            <DateRangePicker
              value={dateRange}
              onChange={({ detail }) => setDateRange(detail.value)}
              relativeOptions={TIME_RANGE_OPTIONS}
              isValidRange={(range) => {
                if (range?.type === "absolute") {
                  const start = new Date(range.startDate);
                  const end = new Date(range.endDate);
                  if (start > end) {
                    return {
                      valid: false,
                      errorMessage: "开始时间不能晚于结束时间",
                    };
                  }
                  // 限制最大范围为 90 天
                  const maxRange = 90 * 24 * 60 * 60 * 1000;
                  if (end.getTime() - start.getTime() > maxRange) {
                    return {
                      valid: false,
                      errorMessage: "时间范围不能超过 90 天",
                    };
                  }
                }
                return { valid: true };
              }}
              i18nStrings={{
                todayAriaLabel: "今天",
                nextMonthAriaLabel: "下个月",
                previousMonthAriaLabel: "上个月",
                customRelativeRangeDurationLabel: "持续时间",
                customRelativeRangeDurationPlaceholder: "输入持续时间",
                customRelativeRangeOptionLabel: "自定义范围",
                customRelativeRangeOptionDescription: "设置自定义时间范围",
                customRelativeRangeUnitLabel: "时间单位",
                formatRelativeRange: (e) => {
                  const unitText =
                    e.unit === "day" ? "天" : e.unit === "week" ? "周" : "月";
                  return `最近 ${e.amount} ${unitText}`;
                },
                formatUnit: (e, _n) =>
                  e === "day" ? "天" : e === "week" ? "周" : "月",
                dateTimeConstraintText: "时间范围最长 90 天",
                relativeModeTitle: "相对时间",
                absoluteModeTitle: "绝对时间",
                relativeRangeSelectionHeading: "选择时间范围",
                startDateLabel: "开始日期",
                endDateLabel: "结束日期",
                startTimeLabel: "开始时间",
                endTimeLabel: "结束时间",
                clearButtonLabel: "清除",
                cancelButtonLabel: "取消",
                applyButtonLabel: "应用",
              }}
              placeholder="选择时间范围"
            />
          </div>

          {/* 聚合维度选择器 */}
          <div style={{ minWidth: 150 }}>
            <Select
              selectedOption={
                GROUP_BY_OPTIONS.find((o) => o.value === groupBy) ||
                GROUP_BY_OPTIONS[0]
              }
              onChange={({ detail }) => {
                setGroupBy(detail.selectedOption.value as GroupBy);
              }}
              options={GROUP_BY_OPTIONS}
              ariaLabel="聚合维度"
            />
          </div>
        </SpaceBetween>
      </Container>

      {/* 加载状态或数据展示 */}
      {isLoading ? (
        <Container>
          <Box textAlign="center" padding="l">
            <StatusIndicator type="loading">加载中...</StatusIndicator>
          </Box>
        </Container>
      ) : (
        <>
          {/* 汇总统计 */}
          {data?.summary && <SummaryCards summary={data.summary} />}

          {/* 数据表格 */}
          <Table
            columnDefinitions={columnDefinitions}
            items={tableItems}
            sortingDisabled={false}
            variant="container"
            stickyHeader
            header={
              <Header
                variant="h2"
                counter={
                  tableItems.length > 0 ? `(${tableItems.length})` : undefined
                }
                description={`${start_date} 至 ${end_date}`}
              >
                资源使用明细
              </Header>
            }
            empty={
              <Box textAlign="center" color="inherit" padding="xl">
                <SpaceBetween size="m">
                  <b>暂无数据</b>
                  <Box color="text-body-secondary">
                    选定时间范围内没有资源使用记录
                  </Box>
                </SpaceBetween>
              </Box>
            }
          />
        </>
      )}
    </SpaceBetween>
  );
}

export default ResourceUsageReportPage;
