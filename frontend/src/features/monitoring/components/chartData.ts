/**
 * 监控图表数据转换（纯函数）
 *
 * 与图表组件分离，便于单测且满足 react-refresh（组件文件只导出组件）。
 * 量纲规范见 page-templates.md §5 / design-tokens.md §3。
 */

import type { ResourceUtilization } from '../types';

// 资源类型中文映射
const RESOURCE_LABELS: Record<string, string> = {
  cpu: 'CPU',
  memory: '内存',
  gpu: 'GPU',
  storage: '存储',
};

/**
 * 将 ResourceUtilization 转换为利用率柱状图数据（F-009 修复）。
 *
 * baseline 缺陷：旧实现用裸 `used`/`available` 绝对值（CPU 核数 vs 存储 50 万 GB 量级悬殊），
 * 共用一条 Y 轴导致百分比量级的柱被压成贴地细线，整图退化为"单根存储柱"。
 * 修复：统一走 `utilization_percentage`（0-100% 同量纲），四种资源利用率可直接对比。
 * 不传 color，交由 Cloudscape 分类色板 token（page-templates §5.1 / design-tokens §3）。
 */
export function formatUtilizationBarData(
  data: ResourceUtilization[],
): Array<{
  title: string;
  type: 'bar';
  data: { x: string; y: number }[];
}> {
  return [
    {
      title: '利用率',
      type: 'bar' as const,
      data: data.map((item) => ({
        x: RESOURCE_LABELS[item.resource_type] || item.resource_type,
        y: item.utilization_percentage,
      })),
    },
  ];
}

/**
 * 将 ResourceUtilization 转换为利用率对比数据（F-010 修复）。
 *
 * baseline 缺陷：旧饼图用 `value: used` 把 CPU/内存/GPU 百分比与存储绝对字节数放入同一占比维度
 * 求"分布"，物理上无意义（异量纲不可加和求占比），致存储独占整环 95%+ 面积。
 * 修复：占比语义不成立，改为各资源利用率横向对比（与柱状图同为 0-100% 量纲），语义清晰可读。
 */
export function formatUtilizationCompareData(
  data: ResourceUtilization[],
): Array<{
  title: string;
  type: 'bar';
  data: { x: string; y: number }[];
}> {
  return [
    {
      title: '利用率',
      type: 'bar' as const,
      data: data.map((item) => ({
        x: RESOURCE_LABELS[item.resource_type] || item.resource_type,
        y: item.utilization_percentage,
      })),
    },
  ];
}
