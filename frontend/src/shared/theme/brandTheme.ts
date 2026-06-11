/**
 * 品牌主题 (Brand Theme)
 *
 * 基于 Cloudscape 官方主题化 API (applyTheme) 的「深空离子青」品牌定制。
 *
 * 设计意图:
 * - 摆脱默认 AWS 控制台蓝，建立平台自有品牌识别（深空青黑 + 离子青）
 * - 明 / 暗双模式分别调校，保证 WCAG AA 对比度
 * - 仅通过官方 design token 覆盖实现，不引入任何自定义 CSS
 *
 * 接入点: main.tsx 在 React 渲染前调用 applyBrandTheme()，避免主题闪烁。
 */

import { applyTheme, type Theme } from '@cloudscape-design/components/theming';

/** 品牌色板（集中定义，便于统一调整） */
export const BRAND_COLORS = {
  /** 主品牌色 - 明亮模式（深离子青，对白色文字对比度 ≈ 5.9:1） */
  primaryLight: '#0D6557',
  primaryLightHover: '#0A5247',
  primaryLightActive: '#08433A',
  /** 主品牌色 - 暗黑模式（亮离子青，配深色文字） */
  primaryDark: '#42E0CC',
  primaryDarkHover: '#5FE8D8',
  primaryDarkActive: '#2FCBB7',
  /** 暗黑模式主按钮上的文字色 */
  onPrimaryDark: '#04332C',
  /** 链接色 */
  linkLight: '#0B5D50',
  linkLightHover: '#08433A',
  linkDark: '#52E3D2',
  linkDarkHover: '#7FECDF',
  /** 焦点环 */
  focusLight: '#0AA08E',
  focusDark: '#52E3D2',
  /** 选中态背景 */
  selectedBgLight: '#E6F7F4',
  selectedBgDark: '#123A36',
} as const;

/**
 * 中文优先字体栈
 *
 * Cloudscape 默认 Open Sans 不含中文字形，补充
 * PingFang / 苹方、微软雅黑等系统中文字体，优化中文界面排版。
 */
const FONT_FAMILY_BASE =
  '"Open Sans", "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif';

/** 品牌主题定义（仅覆盖必要 token，其余继承 Cloudscape 默认） */
const brandTheme: Theme = {
  tokens: {
    // 字体
    fontFamilyBase: FONT_FAMILY_BASE,

    // 主操作按钮
    colorBackgroundButtonPrimaryDefault: {
      light: BRAND_COLORS.primaryLight,
      dark: BRAND_COLORS.primaryDark,
    },
    colorBackgroundButtonPrimaryHover: {
      light: BRAND_COLORS.primaryLightHover,
      dark: BRAND_COLORS.primaryDarkHover,
    },
    colorBackgroundButtonPrimaryActive: {
      light: BRAND_COLORS.primaryLightActive,
      dark: BRAND_COLORS.primaryDarkActive,
    },
    colorTextButtonPrimaryDefault: {
      light: '#FFFFFF',
      dark: BRAND_COLORS.onPrimaryDark,
    },

    // 次级按钮（normal variant 的文字与描边）
    colorTextButtonNormalDefault: {
      light: BRAND_COLORS.primaryLight,
      dark: BRAND_COLORS.primaryDark,
    },
    colorBorderButtonNormalDefault: {
      light: BRAND_COLORS.primaryLight,
      dark: BRAND_COLORS.primaryDark,
    },
    colorTextButtonNormalHover: {
      light: BRAND_COLORS.primaryLightHover,
      dark: BRAND_COLORS.primaryDarkHover,
    },
    colorBorderButtonNormalHover: {
      light: BRAND_COLORS.primaryLightHover,
      dark: BRAND_COLORS.primaryDarkHover,
    },
    colorTextButtonNormalActive: {
      light: BRAND_COLORS.primaryLightActive,
      dark: BRAND_COLORS.primaryDarkActive,
    },
    colorBorderButtonNormalActive: {
      light: BRAND_COLORS.primaryLightActive,
      dark: BRAND_COLORS.primaryDarkActive,
    },

    // 链接与强调文字
    colorTextLinkDefault: {
      light: BRAND_COLORS.linkLight,
      dark: BRAND_COLORS.linkDark,
    },
    colorTextLinkHover: {
      light: BRAND_COLORS.linkLightHover,
      dark: BRAND_COLORS.linkDarkHover,
    },
    colorTextAccent: {
      light: BRAND_COLORS.primaryLight,
      dark: BRAND_COLORS.linkDark,
    },

    // 表单控件（勾选框 / 单选 / 开关 选中态）
    colorBackgroundControlChecked: {
      light: BRAND_COLORS.primaryLight,
      dark: BRAND_COLORS.primaryDark,
    },
    colorForegroundControlDefault: {
      light: '#FFFFFF',
      dark: BRAND_COLORS.onPrimaryDark,
    },

    // 焦点环与选中项
    colorBorderItemFocused: {
      light: BRAND_COLORS.focusLight,
      dark: BRAND_COLORS.focusDark,
    },
    colorBackgroundItemSelected: {
      light: BRAND_COLORS.selectedBgLight,
      dark: BRAND_COLORS.selectedBgDark,
    },
    colorBorderItemSelected: {
      light: BRAND_COLORS.primaryLight,
      dark: BRAND_COLORS.primaryDark,
    },

    // 图表分类色板（品牌青打头，保持类别间区分度）
    colorChartsPaletteCategorical1: { light: '#0AA08E', dark: '#42E0CC' },
    colorChartsPaletteCategorical2: { light: '#5089C6', dark: '#7CA9DC' },
    colorChartsPaletteCategorical3: { light: '#B0833D', dark: '#D9A95B' },
    colorChartsPaletteCategorical4: { light: '#8D6C9F', dark: '#B095C4' },
    colorChartsPaletteCategorical5: { light: '#566977', dark: '#90A4B0' },
  },
};

/**
 * 应用品牌主题到全局。
 *
 * 必须在 React 首次渲染前调用（main.tsx），保证首屏即品牌化。
 */
export function applyBrandTheme(): void {
  applyTheme({ theme: brandTheme });
}

/**
 * Hero 页头深空渐变背景。
 *
 * 供 ContentLayout 的 headerBackgroundStyle 使用：
 * 深空青黑线性渐变叠加右上角离子青辉光，营造「算力机房」氛围。
 */
export function heroHeaderBackground(mode: 'light' | 'dark'): string {
  return mode === 'dark'
    ? 'radial-gradient(ellipse 60% 90% at 82% -12%, rgba(66, 224, 204, 0.18), transparent 60%), linear-gradient(132deg, #02110F 0%, #07211E 52%, #0B3B35 100%)'
    : 'radial-gradient(ellipse 60% 90% at 82% -12%, rgba(82, 227, 210, 0.26), transparent 60%), linear-gradient(132deg, #051F1C 0%, #0A3733 52%, #0E5147 100%)';
}

/** 训练任务状态语义色（与品牌色板协调，供图表使用） */
export const JOB_STATUS_CHART_COLORS = {
  /** 运行中 - 品牌活跃青（平台核心活动） */
  running: '#0AA08E',
  /** 已完成 - 沉稳绿 */
  completed: '#67A353',
  /** 已失败 - 警示红 */
  failed: '#D63F38',
  /** 已暂停 - 中性灰 */
  paused: '#8C8C94',
} as const;
