/**
 * Popular Templates Component
 *
 * 热门模板推荐卡片
 */

import {
  Badge,
  Box,
  Button,
  Cards,
  Header,
  SpaceBetween,
} from '@cloudscape-design/components';
import { usePopularTemplates } from '../api';
import type { JobTemplateSummary } from '../types';
import { VISIBILITY_COLORS, VISIBILITY_LABELS } from '../types';

interface PopularTemplatesProps {
  limit?: number;
  onUseTemplate?: (templateId: number) => void;
}

/**
 * 热门模板组件
 */
export function PopularTemplates({
  limit = 5,
  onUseTemplate,
}: PopularTemplatesProps) {
  const { data: templates, isLoading, error } = usePopularTemplates(limit);

  if (error) {
    return (
      <Box textAlign="center" color="text-status-error" padding="l">
        加载热门模板失败
      </Box>
    );
  }

  return (
    <Cards
      header={
        <Header
          variant="h2"
          description="最受欢迎的公开模板"
        >
          热门模板
        </Header>
      }
      loading={isLoading}
      loadingText="加载中..."
      items={templates || []}
      cardDefinition={{
        header: (item: JobTemplateSummary) => item.name,
        sections: [
          {
            id: 'description',
            content: (item: JobTemplateSummary) => (
              <Box color="text-body-secondary">
                {item.description || '无描述'}
              </Box>
            ),
          },
          {
            id: 'stats',
            content: (item: JobTemplateSummary) => (
              <SpaceBetween direction="horizontal" size="xs">
                <Badge color={VISIBILITY_COLORS[item.visibility]}>
                  {VISIBILITY_LABELS[item.visibility]}
                </Badge>
                <Box color="text-body-secondary">
                  {item.usage_count} 次使用
                </Box>
              </SpaceBetween>
            ),
          },
          {
            id: 'action',
            content: (item: JobTemplateSummary) => (
              <Button
                variant="link"
                onClick={() => onUseTemplate?.(item.id)}
              >
                使用此模板
              </Button>
            ),
          },
        ],
      }}
      empty={
        <Box textAlign="center" color="inherit" padding="l">
          <Box variant="p" color="inherit">
            暂无热门模板
          </Box>
        </Box>
      }
    />
  );
}
