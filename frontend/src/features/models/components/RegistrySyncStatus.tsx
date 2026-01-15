/**
 * Registry Sync Status Component
 *
 * 显示模型与 SageMaker Model Registry 的同步状态
 */

import { StatusIndicator, Popover, Box } from '@cloudscape-design/components';
import type { ModelDetail } from '../types';
import { getRegistrySyncStatus } from '../types';

interface RegistrySyncStatusProps {
  model: ModelDetail;
}

/**
 * Registry 同步状态指示器
 */
export function RegistrySyncStatus({ model }: RegistrySyncStatusProps) {
  const syncStatus = getRegistrySyncStatus(model);

  const statusConfig: Record<
    string,
    { type: 'success' | 'pending' | 'stopped' | 'error'; label: string; description: string }
  > = {
    synced: {
      type: 'success',
      label: '已同步',
      description: '模型已成功注册到 SageMaker Model Registry',
    },
    pending: {
      type: 'pending',
      label: '同步中',
      description: '模型正在同步到 SageMaker Model Registry',
    },
    not_registered: {
      type: 'stopped',
      label: '未注册',
      description: '模型尚未注册到 SageMaker Model Registry',
    },
    failed: {
      type: 'error',
      label: '同步失败',
      description: '模型同步到 Registry 失败，请检查配置',
    },
  };

  const config = statusConfig[syncStatus] || statusConfig['not_registered'];

  return (
    <Popover
      dismissButton={false}
      position="top"
      size="small"
      triggerType="custom"
      content={
        <Box>
          <Box fontWeight="bold">{config.label}</Box>
          <Box color="text-body-secondary">{config.description}</Box>
          {model.registry_arn && (
            <Box margin={{ top: 'xs' }} fontSize="body-s">
              <code>{model.registry_arn}</code>
            </Box>
          )}
        </Box>
      }
    >
      <StatusIndicator type={config.type}>{config.label}</StatusIndicator>
    </Popover>
  );
}

export default RegistrySyncStatus;
