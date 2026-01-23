/**
 * MSW Server 配置
 *
 * 为集成测试提供 API Mock 服务
 */

import { setupServer } from 'msw/node';
import { handlers } from './mocks/handlers';

/**
 * MSW Server 实例
 * 在 setup.ts 中启动，用于拦截 API 请求
 */
export const server = setupServer(...handlers);
