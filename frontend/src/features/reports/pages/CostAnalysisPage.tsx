/**
 * Cost Analysis Dashboard Page
 *
 * Task: T075 - 成本分析仪表盘前端页面
 * 功能:
 * - 成本概要卡片（总成本、计算、存储、网络）
 * - 时间范围选择器
 * - 成本趋势图表
 * - 成本明细表格
 * - 聚合维度切换
 * - 导出功能
 */

import { useState, useMemo } from "react";
import {
  Box,
  Button,
  ColumnLayout,
  Container,
  DateRangePicker,
  Header,
  PieChart,
  Select,
  SpaceBetween,
  StatusIndicator,
  Table,
} from "@cloudscape-design/components";
import type {
  DateRangePickerProps,
  SelectProps,
} from "@cloudscape-design/components";
import { PageLayout, InlineErrorState } from "@shared/components";
import { useCostAnalysis, useExportReport } from "../api";

// 面包屑（模块级常量，避免每次渲染创建新引用）
const BREADCRUMBS = [
  { text: "首页", href: "/" },
  { text: "报表中心", href: "/reports" },
  { text: "成本分析", href: "/reports/cost-analysis" },
];
import { CostTrendChart } from "../components";
import {
  formatCurrency,
  calculateDateRange,
  DATE_RANGE_PICKER_I18N,
} from "@shared/utils";
import type { CostBreakdown, GroupBy, CostAnalysisFilters } from "../types";
import { GROUP_BY_LABELS, COST_CATEGORY_LABELS } from "../types";

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
  { value: "category", label: GROUP_BY_LABELS.category },
  { value: "user", label: GROUP_BY_LABELS.user },
  { value: "project", label: GROUP_BY_LABELS.project },
  { value: "resource_type", label: GROUP_BY_LABELS.resource_type },
];

// === 子组件 ===

/**
 * 成本概要卡片
 */
function CostSummaryCards({
  totalCost,
  computeCost,
  storageCost,
  networkCost,
  loading,
}: {
  totalCost: number;
  computeCost: number;
  storageCost: number;
  networkCost: number;
  loading: boolean;
}) {
  // 注：不再为 KPI 数值硬编码颜色（F-034）。数值用默认文字色，与 reports-home 一致；
  // 颜色区分交由下方图表的分类色板承载，KPI 卡保持中性专业。
  const costCards = [
    { label: "总成本", value: formatCurrency(totalCost) },
    { label: "计算成本", value: formatCurrency(computeCost) },
    { label: "存储成本", value: formatCurrency(storageCost) },
    { label: "网络成本", value: formatCurrency(networkCost) },
  ];

  if (loading) {
    return (
      <ColumnLayout columns={4} variant="text-grid">
        {costCards.map((card) => (
          <Container key={card.label}>
            <Box textAlign="center">
              <Box variant="awsui-key-label">{card.label}</Box>
              <Box padding={{ top: "xs" }}>
                <StatusIndicator type="loading">加载中</StatusIndicator>
              </Box>
            </Box>
          </Container>
        ))}
      </ColumnLayout>
    );
  }

  return (
    <ColumnLayout columns={4} variant="text-grid">
      {costCards.map((card) => (
        <Container key={card.label}>
          <Box textAlign="center">
            <Box variant="awsui-key-label">{card.label}</Box>
            <Box variant="awsui-value-large">
              {card.value}
            </Box>
          </Box>
        </Container>
      ))}
    </ColumnLayout>
  );
}

/**
 * 成本分布饼图
 */
function CostDistributionPie({
  breakdown,
  loading,
}: {
  breakdown: CostBreakdown[];
  loading: boolean;
}) {
  // 不传 color：交由 Cloudscape 分类色板 token 自动着色（F-013）。
  // 折线图与本饼图均走默认分类色板且分项顺序一致，同一成本类别跨图自动同色。
  const pieData = useMemo(() => {
    return breakdown.map((item) => ({
      title: COST_CATEGORY_LABELS[item.category] || item.name,
      value: item.cost_usd,
    }));
  }, [breakdown]);

  if (loading) {
    return (
      <Container header={<Header variant="h2">成本分布</Header>}>
        <Box textAlign="center" padding="l">
          <StatusIndicator type="loading">加载中...</StatusIndicator>
        </Box>
      </Container>
    );
  }

  if (breakdown.length === 0) {
    return (
      <Container header={<Header variant="h2">成本分布</Header>}>
        <Box textAlign="center" color="text-body-secondary" padding="l">
          暂无数据
        </Box>
      </Container>
    );
  }

  return (
    <Container header={<Header variant="h2">成本分布</Header>}>
      <PieChart
        data={pieData}
        size="medium"
        variant="donut"
        hideFilter
        hideLegend={false}
        i18nStrings={{
          detailsValue: "金额",
          detailsPercentage: "占比",
          legendAriaLabel: "图例",
          chartAriaRoleDescription: "成本分布饼图",
        }}
        empty={<Box textAlign="center">暂无数据</Box>}
      />
    </Container>
  );
}

/**
 * 成本明细表格
 */
function CostBreakdownTable({
  breakdown,
  loading,
}: {
  breakdown: CostBreakdown[];
  loading: boolean;
}) {
  const columnDefinitions = [
    {
      id: "category",
      header: "类别",
      cell: (item: CostBreakdown) =>
        COST_CATEGORY_LABELS[item.category] || item.name,
      width: 150,
    },
    {
      id: "cost",
      header: "成本",
      cell: (item: CostBreakdown) => formatCurrency(item.cost_usd),
      width: 120,
    },
    {
      id: "percentage",
      header: "占比",
      cell: (item: CostBreakdown) => `${item.percentage.toFixed(1)}%`,
      width: 100,
    },
    {
      id: "count",
      header: "项目数",
      cell: (item: CostBreakdown) => item.item_count ?? "-",
      width: 100,
    },
  ];

  return (
    <Table
      columnDefinitions={columnDefinitions}
      items={breakdown}
      loading={loading}
      loadingText="加载成本明细..."
      sortingDisabled
      variant="container"
      header={
        <Header
          variant="h2"
          counter={breakdown.length > 0 ? `(${breakdown.length})` : undefined}
        >
          成本明细
        </Header>
      }
      empty={
        <Box textAlign="center" color="inherit" padding="l">
          <Box color="text-body-secondary">暂无成本数据</Box>
        </Box>
      }
    />
  );
}

// === 主组件 ===

/**
 * 成本分析仪表盘页面
 */
export function CostAnalysisPage() {
  // === 状态管理 ===

  // 时间范围状态 (默认最近 30 天)
  const [dateRange, setDateRange] = useState<DateRangePickerProps.Value | null>(
    {
      type: "relative",
      amount: 30,
      unit: "day",
    } as DateRangePickerProps.RelativeValue,
  );

  // 聚合维度状态
  const [groupBy, setGroupBy] = useState<SelectProps.Option | null>(
    GROUP_BY_OPTIONS[0],
  );

  // === 计算过滤条件 ===
  const filters: CostAnalysisFilters = useMemo(() => {
    const { startDate, endDate } = calculateDateRange(dateRange);
    return {
      start_date: startDate,
      end_date: endDate,
      group_by: (groupBy?.value as GroupBy) || "category",
    };
  }, [dateRange, groupBy]);

  // === 数据查询 ===
  const { data, isLoading, error, refetch } = useCostAnalysis(filters);
  const exportMutation = useExportReport();

  // === 数据处理 ===
  const summary = data?.summary;
  const breakdown = data?.breakdown || [];
  const dailyCosts = data?.daily_costs || [];

  // === 事件处理 ===
  const handleRefresh = () => {
    refetch();
  };

  const handleExport = () => {
    const { startDate, endDate } = calculateDateRange(dateRange);
    exportMutation.mutate({
      report_type: "cost_analysis",
      format: "csv",
      start_date: startDate,
      end_date: endDate,
      group_by: (groupBy?.value as GroupBy) || "category",
    });
  };

  // === 错误处理：保留页面骨架（标题/面包屑），提供重试 ===
  if (error) {
    return (
      <PageLayout title="成本分析" breadcrumbs={BREADCRUMBS}>
        <InlineErrorState message={error.message} onRetry={() => refetch()} />
      </PageLayout>
    );
  }

  // === 渲染 ===
  return (
    <PageLayout
      title="成本分析"
      description="分析和追踪平台资源使用成本"
      breadcrumbs={BREADCRUMBS}
      actions={
        <SpaceBetween direction="horizontal" size="xs">
          <Button
            iconName="refresh"
            onClick={handleRefresh}
            loading={isLoading}
          >
            刷新
          </Button>
          <Button
            iconName="download"
            onClick={handleExport}
            loading={exportMutation.isPending}
          >
            导出 CSV
          </Button>
        </SpaceBetween>
      }
    >
    <SpaceBetween size="l" data-testid="cost-analysis-page">
      {/* 过滤器区域 */}
      <Container>
        <SpaceBetween direction="horizontal" size="m">
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
                  // 限制最大范围为 365 天
                  const maxRange = 365 * 24 * 60 * 60 * 1000;
                  if (end.getTime() - start.getTime() > maxRange) {
                    return {
                      valid: false,
                      errorMessage: "时间范围不能超过 365 天",
                    };
                  }
                }
                return { valid: true };
              }}
              i18nStrings={DATE_RANGE_PICKER_I18N}
              placeholder="选择时间范围"
            />
          </div>

          <div style={{ minWidth: 180 }}>
            <Select
              selectedOption={groupBy}
              onChange={({ detail }) => setGroupBy(detail.selectedOption)}
              options={GROUP_BY_OPTIONS}
              placeholder="聚合维度"
            />
          </div>
        </SpaceBetween>
      </Container>

      {/* 成本概要卡片 */}
      <CostSummaryCards
        totalCost={summary?.total_cost_usd || 0}
        computeCost={summary?.compute_cost_usd || 0}
        storageCost={summary?.storage_cost_usd || 0}
        networkCost={summary?.network_cost_usd || 0}
        loading={isLoading}
      />

      {/* 成本趋势图表 */}
      <CostTrendChart
        data={dailyCosts}
        title="成本趋势"
        loading={isLoading}
        height={350}
      />

      {/* 成本分布和明细 */}
      <ColumnLayout columns={2}>
        <CostDistributionPie breakdown={breakdown} loading={isLoading} />
        <CostBreakdownTable breakdown={breakdown} loading={isLoading} />
      </ColumnLayout>
    </SpaceBetween>
    </PageLayout>
  );
}

export default CostAnalysisPage;
