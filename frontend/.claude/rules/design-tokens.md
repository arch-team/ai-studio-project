> **职责**: 设计 token 规范 - 深空离子青品牌主题（色板、字体、图表色、Hero）的单一真实源

# 设计 Token 规范 (Design Tokens)

> **适用范围**: 全站视觉基础——品牌色、链接/焦点/选中态、图表配色、字体栈、Hero 页头、Logo
> **事实基准**: 反向提炼自已落地的 `src/shared/theme/brandTheme.ts` 与 `src/shared/theme/brandAssets.ts`
> **核心命题**: 所有颜色走 Cloudscape design token；改色只改 token，禁止自定义 CSS 与硬编码 hex。色值唯一真实源是 `brandTheme.ts`，本文件与之逐字对齐。

---

## 0. 速查卡片

> Claude 生成页面/组件时优先查阅此章节

### 0.1 品牌色板速查（明 / 暗双列）

| 类别 | Token / 用途 | Light | Dark |
|------|-------------|-------|------|
| **主色** | 主按钮默认 | `#0D6557` | `#42E0CC` |
| 主色 · 悬停 | 主按钮 hover | `#0A5247` | `#5FE8D8` |
| 主色 · 按下 | 主按钮 active | `#08433A` | `#2FCBB7` |
| 主按钮文字 | 主按钮上的文字 | `#FFFFFF` | `#04332C` |
| **链接** | 链接默认 | `#0B5D50` | `#52E3D2` |
| 链接 · 悬停 | 链接 hover | `#08433A` | `#7FECDF` |
| **焦点环** | 键盘焦点边框 | `#0AA08E` | `#52E3D2` |
| **选中态背景** | 列表/表格选中行 | `#E6F7F4` | `#123A36` |

### 0.2 字体栈速查

```
"Open Sans", "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif
```

> 通过 `fontFamilyBase` token 全局生效；Cloudscape 默认 Open Sans 不含中文字形，补足苹方 / 思源 / 雅黑等系统中文字体。

### 0.3 「何时用 token」决策

| 场景 | ✅ 正确做法 | ❌ 禁止 |
|------|-----------|--------|
| 主操作按钮配色 | `<Button variant="primary">`（自动取 `colorBackgroundButtonPrimary*` token） | `style={{ background: '#0D6557' }}` |
| 链接/强调文字 | Cloudscape `<Link>` / `<Box color>`（取 `colorTextLink*` token） | `style={{ color: '#0B5D50' }}` |
| 状态指示 | `<StatusIndicator>`（颜色+图标+文字，见 [accessibility.md](accessibility.md) §5） | 裸 `<span style>` 上色 |
| 图表配色 | Cloudscape 图表组件自动取 `colorChartsPaletteCategorical*` token | 给图表传硬编码 hex 数组 |
| 调整品牌色 | 改 `brandTheme.ts` 的 token 值 | 在页面/组件里覆盖颜色 |

**铁律**: 用语义化 Cloudscape 组件 + design token，禁止在 features 代码里出现颜色 hex。需要新增/调整颜色时，唯一入口是 `brandTheme.ts`。

### 0.4 陷阱 ⚠️

- ❌ 在组件里硬编码 `#0D6557` 等品牌色 → ✅ 用 Cloudscape 组件，颜色由 token 注入
- ❌ 自定义 CSS / 内联样式覆盖颜色 → ✅ 仅通过 `applyTheme` 覆盖 design token（零自定义 CSS 铁律，§1.3）
- ❌ 暗黑模式沿用明亮模式色值 → ✅ 每个 token 明暗分别取值（明用深离子青配白字，暗用亮离子青配深字）
- ❌ 给图表硬塞颜色数组 → ✅ 走 `colorChartsPaletteCategorical1~5`，品牌青打头（§3）
- ❌ 状态色与图表分类色混用 → ✅ 状态语义走 `JOB_STATUS_CHART_COLORS`，分类区分走 Categorical 调色板

---

## 1. 品牌主题

### 1.1 深空离子青理念

| 维度 | 说明 |
|------|------|
| **目标** | 摆脱 Cloudscape/AWS 控制台默认蓝，建立平台自有视觉识别 |
| **基调** | 深空青黑（背景/Hero）+ 离子青（主色/强调），呼应「算力机房」氛围 |
| **双模式** | 明亮模式用**深**离子青（`#0D6557` 系）配白字；暗黑模式用**亮**离子青（`#42E0CC` 系）配深字——分别调校以保证 WCAG AA 对比度 |
| **Logo 语义** | 三节点互联的「分布式拓扑」图形，对应平台核心能力（多节点分布式训练），渐变离子青呼应主题色（§5） |

### 1.2 `applyBrandTheme()` 接入点

主题基于 Cloudscape 官方主题化 API（`@cloudscape-design/components/theming` 的 `applyTheme`）实现，仅覆盖必要 token，其余继承 Cloudscape 默认。

```typescript
// src/app/main.tsx —— 必须在 React 首次渲染前调用，避免首屏主题闪烁
import { applyBrandTheme } from '@shared/theme';

applyBrandTheme();                       // ① 先应用品牌主题
createRoot(rootElement).render(<App />); // ② 再渲染 React 树
```

> `applyBrandTheme()` 内部调用 `applyTheme({ theme: brandTheme })`，把 `brandTheme.ts` 定义的 token 写入全局。放在渲染前调用，保证首屏即品牌化。

### 1.3 零自定义 CSS 铁律 🔴

| 原则 | 落地方式 |
|------|---------|
| **只改 token** | 所有品牌化通过覆盖 Cloudscape design token 实现（`brandTheme.ts` 的 `tokens` 字段） |
| **零自定义 CSS** | 不引入任何 `.css` 文件、`style={{}}` 内联样式、第三方样式库（与 [tech-stack.md](tech-stack.md) 禁用清单一致） |
| **改色单一入口** | 调整任何颜色 = 修改 `brandTheme.ts` 对应 token 的 `light`/`dark` 值，全站自动生效 |
| **明暗自动适配** | 每个色彩 token 都提供 `{ light, dark }` 双值，Cloudscape 按当前 `Mode` 自动选取（暗色模式切换见 [component-design.md](component-design.md) §6） |

---

## 2. 色彩 Token

> 全部摘自 `BRAND_COLORS`（`brandTheme.ts`），并标注其映射的 Cloudscape token 与用途。色值与源码逐字一致。

### 2.1 主操作按钮（Primary Button）

| `BRAND_COLORS` 键 | Cloudscape Token | Light | Dark | 用途 |
|-------------------|------------------|-------|------|------|
| `primaryLight` / `primaryDark` | `colorBackgroundButtonPrimaryDefault` | `#0D6557` | `#42E0CC` | 主按钮默认背景 |
| `primaryLightHover` / `primaryDarkHover` | `colorBackgroundButtonPrimaryHover` | `#0A5247` | `#5FE8D8` | 主按钮悬停 |
| `primaryLightActive` / `primaryDarkActive` | `colorBackgroundButtonPrimaryActive` | `#08433A` | `#2FCBB7` | 主按钮按下 |
| `onPrimaryDark` | `colorTextButtonPrimaryDefault`（dark） | `#FFFFFF`（明亮模式直接用纯白） | `#04332C` | 主按钮上的文字色 |

> **WCAG AA**: 主色明亮值 `primaryLight` `#0D6557` 对白色文字对比度 ≈ **5.9:1**（源码注释，满足 AA 正常文本 ≥ 4.5:1）。暗黑模式用亮离子青 `#42E0CC` 配深色文字 `#04332C`，反相搭配同样保证可读性。

> 主色同时复用于：次级按钮（normal variant）的文字与描边（`colorTextButtonNormalDefault` / `colorBorderButtonNormalDefault` 及其 hover/active）、强调文字 `colorTextAccent`、表单控件选中态 `colorBackgroundControlChecked`、选中项边框 `colorBorderItemSelected`——均取同一组 `primary*` 值，保持全站强调色一致。

### 2.2 链接（Link）

| `BRAND_COLORS` 键 | Cloudscape Token | Light | Dark | 用途 |
|-------------------|------------------|-------|------|------|
| `linkLight` / `linkDark` | `colorTextLinkDefault` | `#0B5D50` | `#52E3D2` | 链接默认 |
| `linkLightHover` / `linkDarkHover` | `colorTextLinkHover` | `#08433A` | `#7FECDF` | 链接悬停 |

> `colorTextAccent` 在暗黑模式取 `linkDark`（`#52E3D2`），明亮模式取 `primaryLight`（`#0D6557`）。

### 2.3 焦点环与选中态

| `BRAND_COLORS` 键 | Cloudscape Token | Light | Dark | 用途 |
|-------------------|------------------|-------|------|------|
| `focusLight` / `focusDark` | `colorBorderItemFocused` | `#0AA08E` | `#52E3D2` | 键盘焦点环（禁止移除，见 [accessibility.md](accessibility.md) §5） |
| `selectedBgLight` / `selectedBgDark` | `colorBackgroundItemSelected` | `#E6F7F4` | `#123A36` | 列表/表格选中行背景 |

> 选中项边框 `colorBorderItemSelected` 复用主色（`primaryLight` / `primaryDark`），与选中态背景搭配区分被选行。

---

## 3. 图表色

> 摘自 `brandTheme.ts` 的 `colorChartsPaletteCategorical1~5` 与 `JOB_STATUS_CHART_COLORS`。Cloudscape 图表组件按调色板顺序自动取色，无需手动传 hex。

### 3.1 分类色板（Categorical Palette）

品牌青打头的 5 组分类色，保证类别间区分度。明暗双值，由 Cloudscape 按当前模式自动切换。

| Token | 用途 | Light | Dark |
|-------|------|-------|------|
| `colorChartsPaletteCategorical1` | 分类 1（品牌青打头） | `#0AA08E` | `#42E0CC` |
| `colorChartsPaletteCategorical2` | 分类 2 | `#5089C6` | `#7CA9DC` |
| `colorChartsPaletteCategorical3` | 分类 3 | `#B0833D` | `#D9A95B` |
| `colorChartsPaletteCategorical4` | 分类 4 | `#8D6C9F` | `#B095C4` |
| `colorChartsPaletteCategorical5` | 分类 5 | `#566977` | `#90A4B0` |

### 3.2 训练任务状态语义色

`JOB_STATUS_CHART_COLORS`——与品牌色板协调的状态语义色，供图表/可视化使用。单值，明暗通用。

| 状态键 | 中文标签 | HEX | 语义 |
|--------|---------|-----|------|
| `running` | 运行中 | `#0AA08E` | 品牌活跃青（平台核心活动） |
| `completed` | 已完成 | `#67A353` | 沉稳绿 |
| `failed` | 已失败 | `#D63F38` | 警示红 |
| `paused` | 已暂停 | `#8C8C94` | 中性灰 |

> 状态**文字标签**走 `JOB_STATUS_LABELS`（见 [ux-writing.md](ux-writing.md) §1），状态**指示器**用 `<StatusIndicator>`（颜色+图标+文字）；此处色值专供图表着色，勿与分类色板混用。

---

## 4. 字体与排版

### 4.1 中文优先字体栈

通过 `fontFamilyBase` token 全局生效，完整字符串（`FONT_FAMILY_BASE`，逐字）:

```
"Open Sans", "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif
```

| 段位 | 字体 | 作用 |
|------|------|------|
| 1 | `Open Sans` | Cloudscape 默认西文字体，覆盖拉丁字符 |
| 2-5 | `PingFang SC` / `Hiragino Sans GB` / `Noto Sans SC` / `Microsoft YaHei` | 补足 Open Sans **缺失的中文字形**（苹方 / 冬青黑 / 思源黑体 / 微软雅黑，覆盖 macOS / Windows / Linux） |
| 6+ | `Helvetica Neue`, `Arial`, `sans-serif` | 兜底无衬线回退 |

> 中文与英文/数字之间的排版空格、标点全角等规则见 [ux-writing.md](ux-writing.md) §3，本文件只定义字体栈本身。

---

## 5. Hero 与 Logo

### 5.1 Hero 页头渐变 `heroHeaderBackground(mode)`

供 ContentLayout 的 `headerBackgroundStyle` 使用：深空青黑线性渐变叠加右上角离子青辉光，营造「算力机房」氛围。**仅用于首页 / 门户型页面**，常规列表/详情页不使用。

```typescript
import { heroHeaderBackground } from '@shared/theme';

// ContentLayout 头部背景（mode 取当前明暗模式）
<ContentLayout headerBackgroundStyle={() => heroHeaderBackground(mode)}>
```

| 模式 | 渐变值（逐字） |
|------|--------------|
| **light** | `radial-gradient(ellipse 60% 90% at 82% -12%, rgba(82, 227, 210, 0.26), transparent 60%), linear-gradient(132deg, #051F1C 0%, #0A3733 52%, #0E5147 100%)` |
| **dark** | `radial-gradient(ellipse 60% 90% at 82% -12%, rgba(66, 224, 204, 0.18), transparent 60%), linear-gradient(132deg, #02110F 0%, #07211E 52%, #0B3B35 100%)` |

> 渐变内的辅助色（深空青黑 `#051F1C/#0A3733/#0E5147` 明、`#02110F/#07211E/#0B3B35` 暗）与辉光 rgba 仅服务于 Hero 背景本身，**不作为独立 token 在别处复用**。

### 5.2 Logo `BRAND_LOGO_SRC` / `BRAND_LOGO_ALT`

平台 Logo 以**内联 SVG data URI** 提供（`brandAssets.ts`），供 Cloudscape `TopNavigation` / `SideNavigation` 的 logo 槽位直接使用——无需静态资源文件，亦不引入自定义 CSS。

```typescript
import { BRAND_LOGO_SRC, BRAND_LOGO_ALT } from '@shared/theme';

// TopNavigation logo 槽位
<TopNavigation identity={{ href: '/', logo: { src: BRAND_LOGO_SRC, alt: BRAND_LOGO_ALT } }} />
```

| 常量 | 值 | 说明 |
|------|-----|------|
| `BRAND_LOGO_SRC` | `data:image/svg+xml;utf8,<encodeURIComponent(SVG)>` | 32×32 视区内联 SVG：渐变离子青圆角底（`#52E3D2` → `#0AA08E`）+ 深色三节点拓扑字形（`#04332C`），明暗背景均清晰 |
| `BRAND_LOGO_ALT` | `AI 训练平台标识` | 无障碍替代文本（图片 alt，见 [accessibility.md](accessibility.md) §0） |

---

> 配色预览见 [`../../docs/brand-palette-preview.html`](../../docs/brand-palette-preview.html)（色值已与 `brandTheme.ts` 逐一核对一致，含明暗切换、点击复制 HEX、真实组件场景演示，是本规范的可视化交叉参考）。
