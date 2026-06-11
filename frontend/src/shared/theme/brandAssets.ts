/**
 * 品牌视觉资源 (Brand Assets)
 *
 * 平台 Logo 以内联 SVG data URI 提供，供 Cloudscape
 * TopNavigation / SideNavigation 的 logo 槽位直接使用，
 * 无需静态资源文件，亦不引入自定义 CSS。
 *
 * Logo 释义: 三节点互联的「分布式拓扑」图形 —— 对应平台核心能力
 * （多节点分布式训练），渐变离子青呼应品牌主题色。
 */

/** Logo SVG 源码（32x32 视区，深色字形配辉光青底，明暗背景均清晰） */
const BRAND_LOGO_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" role="img">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#52E3D2"/>
      <stop offset="1" stop-color="#0AA08E"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="30" height="30" rx="9" fill="url(#bg)"/>
  <g stroke="#04332C" stroke-width="2.2" stroke-linecap="round">
    <path d="M16 10.5 L10 21" fill="none"/>
    <path d="M16 10.5 L22 21" fill="none"/>
    <path d="M10 21 L22 21" fill="none"/>
  </g>
  <circle cx="16" cy="9.5" r="3.2" fill="#04332C"/>
  <circle cx="9.5" cy="21.5" r="3.2" fill="#04332C"/>
  <circle cx="22.5" cy="21.5" r="3.2" fill="#04332C"/>
</svg>`;

/** 平台 Logo data URI（用于 Cloudscape logo 槽位的 src） */
export const BRAND_LOGO_SRC = `data:image/svg+xml;utf8,${encodeURIComponent(BRAND_LOGO_SVG)}`;

/** Logo 无障碍替代文本 */
export const BRAND_LOGO_ALT = 'AI 训练平台标识';
