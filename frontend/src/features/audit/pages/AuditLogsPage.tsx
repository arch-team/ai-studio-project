/**
 * Audit Logs Page
 *
 * 审计日志查询页面 - 支持过滤、分页和 CSV 导出
 */

import { useState, useMemo } from "react";
import {
  Box,
  Button,
  Container,
  DateRangePicker,
  Header,
  Pagination,
  Select,
  SpaceBetween,
  StatusIndicator,
  Table,
} from "@cloudscape-design/components";
import type { DateRangePickerProps } from "@cloudscape-design/components";
import { PageLayout, InlineErrorState } from "@shared/components";
import { useAuditLogs, useExportAuditLogs } from "../api";

// 面包屑（模块级常量，避免每次渲染创建新引用）
const BREADCRUMBS = [
  { text: "首页", href: "/" },
  { text: "审计日志", href: "/audit-logs" },
];
import {
  formatDateTime,
  DATE_RANGE_PICKER_I18N,
  validateDateRange,
} from "@shared/utils";
import type {
  AuditLog,
  AuditLogFilters,
  AuditAction,
  AuditResourceType,
  AuditResult,
} from "../types";
import {
  AUDIT_ACTION_LABELS,
  AUDIT_ACTION_COLORS,
  AUDIT_RESOURCE_TYPE_LABELS,
  AUDIT_RESULT_LABELS,
  AUDIT_RESULT_COLORS,
} from "../types";

// 构建 Select 选项
const actionOptions = [
  { value: "", label: "全部操作" },
  ...Object.entries(AUDIT_ACTION_LABELS).map(([value, label]) => ({
    value,
    label,
  })),
];

const resourceTypeOptions = [
  { value: "", label: "全部资源类型" },
  ...Object.entries(AUDIT_RESOURCE_TYPE_LABELS).map(([value, label]) => ({
    value,
    label,
  })),
];

const resultOptions = [
  { value: "", label: "全部结果" },
  ...Object.entries(AUDIT_RESULT_LABELS).map(([value, label]) => ({
    value,
    label,
  })),
];

export function AuditLogsPage() {
  // 分页状态
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  // 过滤器状态
  const [actionFilter, setActionFilter] = useState<string>("");
  const [resourceTypeFilter, setResourceTypeFilter] = useState<string>("");
  const [resultFilter, setResultFilter] = useState<string>("");
  const [dateRange, setDateRange] = useState<DateRangePickerProps.Value | null>(
    null,
  );

  // 构建过滤器参数
  const filters: AuditLogFilters = useMemo(() => {
    const params: AuditLogFilters = {
      page: currentPage,
      page_size: pageSize,
      sort_order: "desc",
    };

    if (actionFilter) {
      params.action = actionFilter as AuditAction;
    }

    if (resourceTypeFilter) {
      params.resource_type = resourceTypeFilter as AuditResourceType;
    }

    if (resultFilter) {
      params.result = resultFilter as AuditResult;
    }

    if (dateRange?.type === "absolute") {
      params.start_date = dateRange.startDate;
      params.end_date = dateRange.endDate;
    } else if (dateRange?.type === "relative") {
      const now = new Date();
      const msMap: Record<string, number> = {
        second: 1000,
        minute: 60 * 1000,
        hour: 60 * 60 * 1000,
        day: 24 * 60 * 60 * 1000,
        week: 7 * 24 * 60 * 60 * 1000,
        month: 30 * 24 * 60 * 60 * 1000,
        year: 365 * 24 * 60 * 60 * 1000,
      };
      const start = new Date(
        now.getTime() - dateRange.amount * (msMap[dateRange.unit] ?? msMap.day),
      );
      params.start_date = start.toISOString();
      params.end_date = now.toISOString();
    }

    return params;
  }, [currentPage, actionFilter, resourceTypeFilter, resultFilter, dateRange]);

  // 数据查询
  const { data, isLoading, error, refetch } = useAuditLogs(filters);

  // 导出功能
  const exportMutation = useExportAuditLogs();

  const handleExport = () => {
    exportMutation.mutate(filters);
  };

  // 表格列定义
  const columnDefinitions = [
    {
      id: "created_at",
      header: "时间",
      cell: (item: AuditLog) => formatDateTime(item.created_at),
      width: 180,
    },
    {
      id: "username",
      header: "用户",
      cell: (item: AuditLog) => item.username || "-",
      width: 120,
    },
    {
      id: "action",
      header: "操作",
      cell: (item: AuditLog) => (
        <StatusIndicator type={AUDIT_ACTION_COLORS[item.action]}>
          {AUDIT_ACTION_LABELS[item.action]}
        </StatusIndicator>
      ),
      width: 100,
    },
    {
      id: "resource_type",
      header: "资源类型",
      cell: (item: AuditLog) => AUDIT_RESOURCE_TYPE_LABELS[item.resource_type],
      width: 120,
    },
    {
      id: "resource_name",
      header: "资源名称",
      cell: (item: AuditLog) => item.resource_name || "-",
    },
    {
      id: "result",
      header: "结果",
      cell: (item: AuditLog) => (
        <StatusIndicator type={AUDIT_RESULT_COLORS[item.result]}>
          {AUDIT_RESULT_LABELS[item.result]}
        </StatusIndicator>
      ),
      width: 100,
    },
    {
      id: "ip_address",
      header: "IP 地址",
      cell: (item: AuditLog) => item.ip_address || "-",
      width: 130,
    },
  ];

  if (error) {
    return (
      <PageLayout title="审计日志" breadcrumbs={BREADCRUMBS}>
        <InlineErrorState message={error.message} onRetry={() => refetch()} />
      </PageLayout>
    );
  }

  return (
    <PageLayout
      title="审计日志"
      description="平台操作审计追踪，支持按操作、资源与时间筛选"
      breadcrumbs={BREADCRUMBS}
      actions={
        <Button
          variant="primary"
          onClick={handleExport}
          loading={exportMutation.isPending}
          iconName="download"
        >
          导出 CSV
        </Button>
      }
    >
    <SpaceBetween size="l">
      {/* 过滤器区域 */}
      <Container>
        <SpaceBetween direction="horizontal" size="m">
          <div style={{ minWidth: 150 }}>
            <Select
              selectedOption={
                actionFilter
                  ? actionOptions.find((o) => o.value === actionFilter) || null
                  : actionOptions[0]
              }
              onChange={({ detail }) => {
                setActionFilter(detail.selectedOption.value || "");
                setCurrentPage(1);
              }}
              options={actionOptions}
              ariaLabel="操作类型"
            />
          </div>

          <div style={{ minWidth: 150 }}>
            <Select
              selectedOption={
                resourceTypeFilter
                  ? resourceTypeOptions.find(
                      (o) => o.value === resourceTypeFilter,
                    ) || null
                  : resourceTypeOptions[0]
              }
              onChange={({ detail }) => {
                setResourceTypeFilter(detail.selectedOption.value || "");
                setCurrentPage(1);
              }}
              options={resourceTypeOptions}
              ariaLabel="资源类型"
            />
          </div>

          <div style={{ minWidth: 150 }}>
            <Select
              selectedOption={
                resultFilter
                  ? resultOptions.find((o) => o.value === resultFilter) || null
                  : resultOptions[0]
              }
              onChange={({ detail }) => {
                setResultFilter(detail.selectedOption.value || "");
                setCurrentPage(1);
              }}
              options={resultOptions}
              ariaLabel="结果"
            />
          </div>

          <div style={{ minWidth: 280 }}>
            <DateRangePicker
              value={dateRange}
              onChange={({ detail }) => {
                setDateRange(detail.value);
                setCurrentPage(1);
              }}
              relativeOptions={[
                { key: "day", amount: 1, unit: "day", type: "relative" },
                { key: "week", amount: 7, unit: "day", type: "relative" },
                { key: "month", amount: 1, unit: "month", type: "relative" },
              ]}
              isValidRange={validateDateRange}
              i18nStrings={DATE_RANGE_PICKER_I18N}
              placeholder="选择时间范围"
            />
          </div>
        </SpaceBetween>
      </Container>

      {/* 日志表格 */}
      <Table
        columnDefinitions={columnDefinitions}
        items={data?.items || []}
        loading={isLoading}
        loadingText="加载中..."
        sortingDisabled
        variant="container"
        header={
          <Header variant="h2" counter={data ? `(${data.total})` : undefined}>
            日志记录
          </Header>
        }
        empty={
          <Box textAlign="center" color="inherit" padding="xl">
            <SpaceBetween size="m">
              <b>暂无审计日志</b>
              <Box color="text-body-secondary">
                没有找到符合条件的审计日志记录
              </Box>
            </SpaceBetween>
          </Box>
        }
        pagination={
          data && data.total_pages > 1 ? (
            <Pagination
              currentPageIndex={currentPage}
              pagesCount={data.total_pages}
              onChange={({ detail }) => setCurrentPage(detail.currentPageIndex)}
            />
          ) : undefined
        }
      />
    </SpaceBetween>
    </PageLayout>
  );
}

export default AuditLogsPage;
