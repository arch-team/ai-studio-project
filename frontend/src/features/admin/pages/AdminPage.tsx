/**
 * Admin Page
 *
 * 管理后台入口页面 - 用户管理和角色管理
 */

import {
  Box,
  ColumnLayout,
  Container,
  Header,
  SpaceBetween,
  Tabs,
} from '@cloudscape-design/components';
import { useState } from 'react';
import { UserManagementPage } from './UserManagementPage';

/**
 * 管理后台页面
 */
export function AdminPage() {
  const [activeTabId, setActiveTabId] = useState('users');

  return (
    <SpaceBetween size="l">
      <Header variant="h1">管理后台</Header>

      <Tabs
        activeTabId={activeTabId}
        onChange={({ detail }) => setActiveTabId(detail.activeTabId)}
        tabs={[
          {
            id: 'users',
            label: '用户管理',
            content: <UserManagementPage />,
          },
          {
            id: 'roles',
            label: '角色管理',
            content: (
              <Container header={<Header variant="h2">角色说明</Header>}>
                <ColumnLayout columns={2} variant="text-grid">
                  <SpaceBetween size="m">
                    <SpaceBetween size="xxs">
                      <Box variant="h3">管理员 (admin)</Box>
                      <Box color="text-body-secondary">
                        拥有系统全部权限，包括用户管理、资源配额分配、系统配置
                      </Box>
                    </SpaceBetween>
                    <SpaceBetween size="xxs">
                      <Box variant="h3">项目经理 (project_manager)</Box>
                      <Box color="text-body-secondary">
                        管理项目下的训练任务、数据集，查看报表和资源使用情况
                      </Box>
                    </SpaceBetween>
                  </SpaceBetween>
                  <SpaceBetween size="m">
                    <SpaceBetween size="xxs">
                      <Box variant="h3">工程师 (engineer)</Box>
                      <Box color="text-body-secondary">
                        创建和管理自己的训练任务、数据集、开发空间
                      </Box>
                    </SpaceBetween>
                    <SpaceBetween size="xxs">
                      <Box variant="h3">查看者 (viewer)</Box>
                      <Box color="text-body-secondary">
                        只读权限，查看训练任务状态、数据集信息
                      </Box>
                    </SpaceBetween>
                  </SpaceBetween>
                </ColumnLayout>
              </Container>
            ),
          },
        ]}
      />
    </SpaceBetween>
  );
}

export default AdminPage;
