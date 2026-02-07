# UX/UI 相关 Skills 调研报告

## 调研目的

为 AI Training Platform 项目识别最适合的 UX/UI 设计相关 skills，以提升前端开发效率和设计质量。

---

## 核心发现：6 个 UX/UI 相关 Skills

### 🎨 一、设计类 Skills

#### 1. `frontend-design:frontend-design` ⭐ 推荐

**触发方式**: `/frontend-design`

**核心能力**:
- 创建高质量、有特色的前端界面（避免"AI 风格"平庸设计）
- 强调设计哲学：色彩学、运动交互、空间构成、视觉细节
- 生产级代码输出

**适用场景**:
- 构建新页面或组件
- 需要视觉辨识度高的界面
- 避免模板化设计

**设计原则**:
- 选择明确美学方向（极简/极繁/复古未来/有机等）
- 使用非标准字体（避免 Inter、Roboto、Arial）
- 创建背景纹理和视觉深度

---

#### 2. `canvas-design`

**触发方式**: 通过 Skill 工具调用

**核心能力**:
- 创建视觉艺术作品（.png, .pdf）
- 生成海报、设计稿、艺术作品

**两步流程**:
1. 设计哲学创建 (.md) - 命名美学、阐述哲学
2. 画布表达 (.pdf/.png) - 90% 视觉，10% 文本

**适用场景**:
- 营销物料设计
- 品牌视觉创作
- 概念展示

---

#### 3. `kpi-dashboard-design`

**触发方式**: 通过 Skill 工具调用

**核心能力**:
- 设计有效的 KPI 仪表板
- 指标选择和可视化布局
- 实时监控模式

**适用场景**:
- 训练任务监控仪表板
- 资源使用统计面板
- 系统健康度展示

---

### 🧠 二、流程类 Skills

#### 4. `superpowers:brainstorming` ⭐ 必须使用

**触发方式**: `/brainstorming`

**强制规则**: **任何创意工作前必须先调用此 skill**

**工作流程**:
```
理解想法 → 探索方案(2-3种) → 设计呈现(分段验证)
```

**核心原则**:
- 一次一个问题（不压倒用户）
- 多选题优于开放题
- YAGNI 原则（不构建不需要的）
- 始终探索替代方案

**输出**: `docs/plans/YYYY-MM-DD-<topic>-design.md`

---

#### 5. `superpowers:writing-plans`

**触发方式**: `/writing-plans`

**前置要求**: 已完成 brainstorming

**核心能力**:
- 创建详细实现计划
- 每步 2-5 分钟的原子任务
- 记录每个任务要修改的文件

**输出**: `docs/plans/YYYY-MM-DD-<feature-name>.md`

---

### 🛠️ 三、实现类 Skills

#### 6. `frontend-patterns` (everything-claude-code)

**触发方式**: 通过 Skill 工具调用

**覆盖模式**:
| 类别 | 包含内容 |
|------|---------|
| 组件模式 | 组合优于继承、复合组件、Render Props |
| Hooks | 切换、数据获取、防抖 |
| 状态管理 | Context + Reducer |
| 性能优化 | Memoization、Code Splitting、虚拟化 |
| 可访问性 | 键盘导航、焦点管理 |

**适用场景**:
- React/Next.js 开发
- 性能优化
- 架构设计参考

---

#### 7. `tailwind-design-system` (补充)

**核心能力**:
- Tailwind CSS 设计系统构建
- Design Tokens 实现
- CVA 组件架构

**注意**: 本项目使用 AWS Cloudscape，此 skill 仅作参考

---

## 推荐工作流

```
用户提出 UI 需求
        ↓
┌───────────────────────────┐
│  superpowers:brainstorming │  ← 必须！探索设计方案
└───────────────────────────┘
        ↓
┌───────────────────────────┐
│  frontend-design          │  ← 高质量界面设计
└───────────────────────────┘
        ↓
┌───────────────────────────┐
│  superpowers:writing-plans │  ← 详细实现计划
└───────────────────────────┘
        ↓
      实现阶段
```

---

## 针对本项目的建议

### 项目背景
- **技术栈**: React + AWS Cloudscape Design System
- **特点**: 企业级 UI，强调 Cloudscape 组件优先

### 推荐组合

| 场景 | 推荐 Skills | 说明 |
|------|------------|------|
| **新功能设计** | brainstorming → frontend-design | 先探索后设计 |
| **仪表板页面** | brainstorming → kpi-dashboard-design | 专注数据可视化 |
| **组件开发** | frontend-patterns | 架构模式参考 |
| **营销页面** | canvas-design | 视觉艺术创作 |

### 注意事项

1. **Cloudscape 优先**: 本项目 CLAUDE.md 明确要求使用 Cloudscape 组件，frontend-design 的自定义样式建议仅用于补充场景

2. **brainstorming 必须先行**: 任何 UI 改动前都应先用 brainstorming 探索方案

3. **设计文档化**: 使用 writing-plans 将设计决策文档化，便于团队协作

---

## Skill 调用语法

```typescript
// 方式 1: 直接调用（推荐）
/brainstorming

// 方式 2: 通过 Skill 工具
Skill({ skill: "frontend-design" })
Skill({ skill: "superpowers:brainstorming" })
```

---

## 总结

| Skill | 优先级 | 用途 |
|-------|-------|------|
| `superpowers:brainstorming` | ⭐⭐⭐ 必须 | 创意工作前的探索 |
| `frontend-design` | ⭐⭐⭐ 推荐 | 高质量界面设计 |
| `frontend-patterns` | ⭐⭐ 常用 | React 架构参考 |
| `kpi-dashboard-design` | ⭐⭐ 常用 | 仪表板设计 |
| `writing-plans` | ⭐ 可选 | 实现计划文档化 |
| `canvas-design` | ⭐ 可选 | 视觉艺术创作 |
