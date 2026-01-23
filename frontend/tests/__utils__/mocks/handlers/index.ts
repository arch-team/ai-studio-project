/**
 * MSW Handlers 入口
 *
 * 汇总所有 API mock handlers
 */

import { trainingJobHandlers } from './trainingJobHandlers';

/**
 * 导出所有 handlers
 * 按需添加其他模块的 handlers
 */
export const handlers = [...trainingJobHandlers];
