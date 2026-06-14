/**
 * 报表图表数据转换（纯函数）
 *
 * 与图表组件分离，便于单测且满足 react-refresh（组件文件只导出组件）。
 * 量纲/配色规范见 page-templates.md §5 / design-tokens.md §3。
 */

import type { DailyCost } from '../types';

// 成本分项类别（不含 total）。顺序固定，保证折线图与成本分布饼图按 Cloudscape
// 分类色板顺序分配后「跨图同语义同色」（F-013）。
const COST_SERIES_KEYS = ['compute', 'storage', 'network', 'other'] as const;

type CostSeriesKey = (typeof COST_SERIES_KEYS)[number];

const COST_SERIES_LABELS: Record<CostSeriesKey, string> = {
  compute: '计算',
  storage: '存储',
  network: '网络',
  other: '其他',
};

function pickCost(item: DailyCost, key: CostSeriesKey): number {
  switch (key) {
    case 'compute':
      return item.compute_cost_usd;
    case 'storage':
      return item.storage_cost_usd;
    case 'network':
      return item.network_cost_usd;
    case 'other':
      return item.other_cost_usd;
    default:
      return 0;
  }
}

/**
 * 构建成本趋势折线图 series（F-012/F-013 修复）。
 *
 * baseline 缺陷：
 * - F-012：把「总计」聚合值与各分项画同图，总计与最大分项（计算）两条线高度重叠不可区分，
 *   存储/网络/其他被压缩贴底不可读。
 * - F-013：硬编码 hex，且与成本分布饼图同色不同义（蓝色折线=总计、饼图=计算）。
 *
 * 修复：
 * - 移除「总计」折线——总成本已由页面顶部 KPI 卡（CostSummaryCards）展示，分项图只画分项。
 * - 不传 color，交由 Cloudscape 分类色板 token 自动着色；分项顺序与饼图一致，跨图同类同色。
 */
export function buildCostTrendSeries(data: DailyCost[]): Array<{
  title: string;
  type: 'line';
  data: { x: string; y: number }[];
}> {
  return COST_SERIES_KEYS.map((key) => ({
    title: COST_SERIES_LABELS[key],
    type: 'line' as const,
    data: data.map((item) => ({ x: item.date, y: pickCost(item, key) })),
  })).filter((series) => series.data.some((point) => point.y > 0));
}

/**
 * 计算成本趋势折线图 Y 轴范围（仅基于分项，不含 total，与 F-012 一致）。
 */
export function calculateCostYDomain(data: DailyCost[]): [number, number] {
  if (data.length === 0) return [0, 100];

  const allValues = data.flatMap((d) =>
    COST_SERIES_KEYS.map((key) => pickCost(d, key)),
  );
  const positives = allValues.filter((v) => v > 0);

  const maxValue = Math.max(...allValues, 0);
  const minValue = positives.length > 0 ? Math.min(...positives) : 0;

  // 添加 10% 边距
  const padding = (maxValue - minValue) * 0.1 || maxValue * 0.1 || 10;
  return [Math.max(0, minValue - padding), maxValue + padding];
}
