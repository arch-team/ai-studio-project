---
paths:
  - "frontend/**/*.{ts,tsx}"
---

# Cloudscape-First 原则

## 强制规则

- ✅ 仅使用 Cloudscape 组件
- ❌ 禁止自定义 CSS 和内联样式
- ❌ 禁止原生 HTML 元素 (input, select, button)
- ❌ 禁止第三方图表库 (使用 Cloudscape LineChart, PieChart)

## 布局规范

- 使用 `SpaceBetween` 控制间距，禁止 margin/padding
- 使用 `Container` + `Header` 组织内容区块
- 使用 `AppLayout` 作为页面框架

## 间距系统 (8px 网格)

| Size | 值 | 用途 |
|------|-----|------|
| xs | 4px | 紧凑元素 |
| s | 8px | 行内元素 |
| m | 16px | 段落/卡片内 |
| l | 24px | 区块间距 |
| xl | 32px | 页面区域 |

## 任务状态色彩

| 状态 | Badge | 说明 |
|------|-------|------|
| submitted | grey | 已提交，等待调度 |
| pending | blue | 等待资源 |
| running | green | 正在运行 |
| paused | yellow | 用户暂停 |
| preempted | orange | 被抢占 |
| completed | green | 成功完成 |
| failed | red | 执行失败 |
| cancelled | grey | 用户取消 |

## 页面结构模板

**列表页**: Container → Header (h1 + 操作按钮) → SpaceBetween → PropertyFilter + Table

**详情页**: SpaceBetween → Container (概览) → Tabs (指标/日志)

**表单页**: Form (actions) → Container (分区) → FormField
