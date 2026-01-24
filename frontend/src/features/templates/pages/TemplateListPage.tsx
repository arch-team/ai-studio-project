/**
 * Template List Page
 *
 * 模板列表页面
 */

import {
  Box,
  Button,
  Container,
  Header,
  Input,
  Select,
  SpaceBetween,
} from '@cloudscape-design/components';
import { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useJobTemplates } from '../api';
import { PopularTemplates, TemplateTable } from '../components';
import type { TemplateFilters, TemplateVisibility } from '../types';
import { DEFAULT_PAGE_SIZE, VISIBILITY_LABELS } from '../types';

// 可见性过滤选项
const visibilityOptions = [
  { label: '全部', value: '' },
  ...Object.entries(VISIBILITY_LABELS).map(([value, label]) => ({
    label,
    value,
  })),
];

// 默认过滤条件
const defaultFilters: TemplateFilters = {
  page: 1,
  page_size: DEFAULT_PAGE_SIZE,
  sort_by: 'usage_count',
  sort_order: 'desc',
};

/**
 * 模板列表页面
 */
export function TemplateListPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<TemplateFilters>(defaultFilters);
  const [searchText, setSearchText] = useState('');
  const [selectedVisibility, setSelectedVisibility] = useState('');

  // 构建查询参数
  const queryFilters: TemplateFilters = {
    ...filters,
    search: searchText || undefined,
    visibility: selectedVisibility
      ? (selectedVisibility as TemplateVisibility)
      : undefined,
  };

  // 获取模板列表
  const { data, isLoading, error, refetch } = useJobTemplates(queryFilters);

  // 事件处理
  const handlePageChange = useCallback((page: number) => {
    setFilters((prev) => ({ ...prev, page }));
  }, []);

  const handleSearch = useCallback(() => {
    setFilters((prev) => ({ ...prev, page: 1 }));
  }, []);

  const handleVisibilityChange = useCallback((value: string) => {
    setSelectedVisibility(value);
    setFilters((prev) => ({ ...prev, page: 1 }));
  }, []);

  const handleTemplateClick = useCallback(
    (templateId: number) => {
      navigate(`/job-templates/${templateId}`);
    },
    [navigate]
  );

  const handleUseTemplate = useCallback(
    (templateId: number) => {
      navigate(`/training-jobs/create?template=${templateId}`);
    },
    [navigate]
  );

  const handleCreateClick = useCallback(() => {
    navigate('/job-templates/create');
  }, [navigate]);

  // 错误处理
  if (error) {
    return (
      <Container>
        <Box textAlign="center" color="text-status-error" padding="xl">
          加载失败: {error.message}
        </Box>
      </Container>
    );
  }

  return (
    <SpaceBetween size="l">
      {/* 标题和操作 */}
      <Header
        variant="h1"
        actions={
          <SpaceBetween direction="horizontal" size="xs">
            <Button iconName="refresh" onClick={() => refetch()}>
              刷新
            </Button>
            <Button variant="primary" onClick={handleCreateClick}>
              创建模板
            </Button>
          </SpaceBetween>
        }
        description="管理和复用训练任务配置模板"
      >
        任务模板
      </Header>

      {/* 热门模板推荐 */}
      <PopularTemplates limit={5} onUseTemplate={handleUseTemplate} />

      {/* 过滤器 */}
      <Container>
        <SpaceBetween direction="horizontal" size="s">
          <Box>
            <Input
              placeholder="搜索模板名称..."
              value={searchText}
              onChange={({ detail }) => setSearchText(detail.value)}
              onKeyDown={({ detail }) => {
                if (detail.key === 'Enter') {
                  handleSearch();
                }
              }}
            />
          </Box>
          <Box>
            <Select
              selectedOption={
                visibilityOptions.find((opt) => opt.value === selectedVisibility) ||
                visibilityOptions[0]
              }
              onChange={({ detail }) =>
                handleVisibilityChange(detail.selectedOption.value || '')
              }
              options={visibilityOptions}
              placeholder="选择可见性"
            />
          </Box>
          <Box>
            <Button onClick={handleSearch}>搜索</Button>
          </Box>
        </SpaceBetween>
      </Container>

      {/* 模板表格 */}
      <TemplateTable
        items={data?.items || []}
        loading={isLoading}
        totalCount={data?.total}
        currentPage={filters.page || 1}
        totalPages={data?.total_pages || 1}
        onPageChange={handlePageChange}
        onTemplateClick={handleTemplateClick}
        onUseTemplate={handleUseTemplate}
      />
    </SpaceBetween>
  );
}

export default TemplateListPage;
