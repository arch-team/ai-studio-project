# 前端 Claude Code 上下文管理规范 - 冗余分析与优化计划

## Context

前端子项目 (`frontend/`) 建立了完整的 Claude Code 上下文管理体系：1 个入口 CLAUDE.md + 9 个 `.claude/rules/*.md` 规则文件，合计约 67K / 2,326 行。本次分析的目的是：在不影响规范文件作用的前提下，识别冗余信息和职责重叠，提出优化建议以提升 token 效率和维护性。

## 关键文件清单

| 文件 | 大小 | 行数 | 声明职责 |
|------|------|------|---------|
| `frontend/CLAUDE.md` | 3.5K | 100 | 入口、技术栈、命令速查、架构速览 |
| `.claude/rules/architecture.md` | 19K | 551 | 分层规则、模块依赖、模块通信、共享内核、错误处理 |
| `.claude/rules/state-management.md` | 9.3K | 325 | React Query、Zustand、表单状态、EventBus 联动 |
| `.claude/rules/testing.md` | 9.5K | 347 | 测试分层、目录结构、命名规范、工具使用 |
| `.claude/rules/component-design.md` | 8.3K | 301 | Cloudscape 组件选择、Props 设计、交互模式 |
| `.claude/rules/accessibility.md` | 6.0K | 193 | WCAG 2.1 AA、ARIA 使用、键盘导航 |
| `.claude/rules/performance.md` | 4.3K | 170 | 代码分割、Memoization、列表优化 |
| `.claude/rules/checklist.md` | 3.8K | 149 | PR Review 检查清单 |
| `.claude/rules/security.md` | 3.5K | 160 | XSS 防护、敏感数据、输入验证 |
| `.claude/rules/code-style.md` | 3.3K | 130 | 命名规范、TypeScript 规范、导入排序 |

---

## 一、冗余分析结果

### 1.1 完全重复 (相同信息出现在多处)

#### [R1] performance.md 内部：性能指标表重复
- **位置**: `performance.md` §0 速查卡片 (L22-28) 与 §6 性能指标目标 (L148-155)
- **详情**: 两个表格内容完全一致 (LCP < 2.5s, INP < 200ms, CLS < 0.1, FCP < 1.8s, TTI < 3.8s)，仅 §6 的 INP 行多一句括号说明
- **浪费**: ~200 tokens

#### [R2] Props 规则：interface vs type 三处出现
- **位置**:
  1. `component-design.md` §0 Props 速查表 L37: `interface ButtonProps {}` vs `type ButtonProps = {}`
  2. `code-style.md` §0 TypeScript 速查 L26: 相同内容
  3. `code-style.md` §2.2 Interface vs Type 决策 L96-98: 扩展表格
- **浪费**: ~150 tokens

#### [R3] 路径别名表两处出现
- **位置**: `CLAUDE.md` L64-70 (5 个别名) 与 `testing.md` §6.1 L286-291 (含 `@tests/`)
- **浪费**: ~60 tokens

### 1.2 部分重复 (核心信息相同但角度/详细度不同)

#### [R4] EventBus 实现代码在两个文件
- **位置**:
  1. `architecture.md` §4.2-4.3 (L242-298): EventMap 接口 + 发布/订阅 hooks + Query Invalidation 示例
  2. `state-management.md` §4.1 (L274-291): 另一套 EventBus + Query Invalidation 联动示例
- **问题**: 两处都展示了如何通过 EventBus 订阅事件并触发 Query Invalidation，代码模式几乎相同
- **浪费**: ~300 tokens

#### [R5] Token 存储安全规则两处说明
- **位置**:
  1. `security.md` §3 (L72-81): Token 存储策略对照表
  2. `state-management.md` §2.1 (L155-181): Auth Store 安全说明 + 完整代码
- **互相引用**: 两个文件互相引用对方（做得较好），但核心规则仍重复
- **浪费**: ~120 tokens

#### [R6] 测试命令在入口和测试规范中重复
- **位置**: `CLAUDE.md` L22-29 与 `testing.md` §0 L12-19
- **重叠**: 3 条完全相同 (`npm test`, 单文件测试, `npm run test:coverage`)
- **浪费**: ~80 tokens

### 1.3 语义重复 (不同措辞传达相同规则)

#### [R7] Cloudscape-First 三处传达
- **位置**:
  1. `CLAUDE.md` L54: 一句话规则
  2. `component-design.md` §0 陷阱 L45-48 + §2.2 禁止事项 L155-162: 详细对照表
  3. `checklist.md` Cloudscape 合规 L58-61: 检查项
- **评估**: 作为入口 → 详情 → 检查清单的三层结构有一定合理性，但 checklist 与 component-design 的陷阱部分逐字对应
- **浪费**: ~150 tokens

#### [R8] 禁止导入模块内部文件
- **位置**:
  1. `architecture.md` §3.3 (L214-224): 带完整代码示例
  2. `code-style.md` §3.2 (L128-130): 简短说明
- **浪费**: ~100 tokens

#### [R9] 状态拆分避免不必要重渲染
- **位置**:
  1. `state-management.md` §5 (L303-316): 最佳实践代码示例
  2. `performance.md` §4 (L109-122): 状态优化代码示例
- **浪费**: ~100 tokens

#### [R10] Props 事件命名 on/handle 前缀
- **位置**:
  1. `component-design.md` §0 L39: 结论式速查
  2. `code-style.md` §1.1 (L57-68): 完整说明 + 代码示例
- **浪费**: ~80 tokens

**冗余合计**: 约 1,340 tokens (占总量约 6%)

---

## 二、职责越界分析

### [V1] component-design.md 越界到代码风格领域
- **越界内容**: §0 Props 设计速查表中的 3 条规则 (interface vs type / children 类型 / 事件命名)
- **应属于**: `code-style.md` (TypeScript 规范和命名规范)
- **理由**: 这些本质上是 TypeScript/命名规则，不是组件设计规则。组件设计应聚焦组件类型划分、Cloudscape 使用、交互模式

### [V2] architecture.md 越界到状态管理领域
- **越界内容**: §4.2-4.3 的 EventBus 完整实现代码 (~60 行)，包含 EventMap 接口定义、发布/订阅 hooks、Query Invalidation 联动
- **应属于**: `state-management.md` §4
- **理由**: architecture.md 的职责是定义"何时使用哪种通信模式"（§4.1 决策矩阵是合适的），但 EventBus 的具体实现属于状态管理范畴

### [V3] architecture.md 包含过度详细的类型模板
- **越界内容**: §5.2 类型定义规范 (L337-380) 的 43 行完整代码模板
- **理由**: 类型的组织位置属于架构规范，但类型的编写模板更偏向代码风格

### [V4] performance.md 包含状态管理建议
- **越界内容**: §4 状态优化 (L109-122) 的 useState 拆分示例
- **应属于**: `state-management.md` §5
- **理由**: 状态的组织方式应由 state-management.md 统一管理

### [V5] checklist.md 大部分内容是其他文件的摘要
- **性质**: checklist.md 的 8 个类别中，6 个完全是对应 rules 文件的精炼版
- **独有价值**: 仅 "Cloudscape 合规" 的页面/表单/表格必备检查和 "项目结构" 部分是独有的

---

## 三、CLAUDE.md 入口文件评估

### 做得好的部分
- 技术栈版本表 - 简洁，其他文件无重复
- 命令速查 - 高频使用，入口放置合理
- 架构速览 - 正确的高层抽象粒度
- 路径别名 - 高频查询信息
- API 集成 - 简洁且独有
- 文档导航表 - 入口文件最重要的功能

### 可改进的部分
- 核心约束表中的 5 条规则 → 作为"分层摘要"模式是合理的，不建议移除
- 测试部分 → 有 3 条命令与 testing.md 重叠，但作为入口指引可接受

### 遗漏的信息
- 无 Node.js/npm 版本要求
- 无首次环境配置步骤 (`npm install`, `.env` 配置)

---

## 四、交叉引用质量评估

### 做得好的交叉引用
- `state-management.md` → `security.md §3` (Token 安全)
- `security.md` → `state-management.md §2.1` (Auth Store)
- `security.md` → `state-management.md §3` (表单验证)
- `performance.md` → `state-management.md §2.3` (Selector 优化)

### 需要补充的交叉引用
- `architecture.md` §4 缺少对 `state-management.md §4` 的引用
- `component-design.md` §0 缺少对 `code-style.md §0/§1/§2` 的引用
- `performance.md` §4 缺少对 `state-management.md §5` 的引用

### 需要修正的问题
- `security.md` 缺少 §1 (从 §0 直接跳到 §2)，章节号不连续
- `checklist.md` 的引用过于笼统 ("详见 architecture.md")，应指定章节号

---

## 五、优化方案

### 优先级 1: 高收益低风险

#### 方案 A: 消除 performance.md 内部重复 [R1]
- **操作**: 删除 §6 性能指标目标表格，将 INP 的补充说明合并到 §0 速查卡片
- **文件**: `performance.md`
- **节省**: ~200 tokens

#### 方案 B: EventBus 实现代码归一化 [R4, V2]
- **操作**:
  1. `architecture.md` §4: 保留 §4.1 通信模式决策矩阵 + 简短概念说明，删除 §4.2 和 §4.3 的完整代码示例 (~60 行)，添加引用 "EventBus 完整实现和使用示例详见 state-management.md §4"
  2. `state-management.md` §4: 承接 EventMap 定义，成为 EventBus 的单一真实源
- **文件**: `architecture.md`, `state-management.md`
- **节省**: ~400 tokens

### 优先级 2: 中等收益

#### 方案 C: Props 规则归一化 [R2, R10, V1]
- **操作**:
  1. `component-design.md` §0 Props 速查表移除 TypeScript 相关规则 (interface vs type / children 类型 / 事件命名)，保留组件设计特有的 Props 规则 (可选属性默认值)
  2. 添加引用 "Props 类型和命名规则详见 code-style.md §0 和 §1"
- **文件**: `component-design.md`
- **节省**: ~230 tokens

#### 方案 D: checklist.md 瘦身 [V5]
- **操作**:
  1. 保留 "Cloudscape 合规" 完整 (独有价值：页面/表单/表格必备检查)
  2. 保留 "项目结构" 完整 (独有内容)
  3. 其他 6 个类别各精简至 2-3 个最关键检查项
  4. 强化引用链接，补充具体章节号
- **文件**: `checklist.md`
- **节省**: ~400 tokens

### 优先级 3: 低收益 / 锦上添花

#### 方案 E: architecture.md 类型模板精简 [V3]
- **操作**: §5.2 的 43 行类型定义代码模板缩减为 15-20 行关键要素
- **文件**: `architecture.md`
- **节省**: ~200 tokens

#### 方案 F: performance.md 状态优化改引用 [R9, V4]
- **操作**: §4 状态拆分示例替换为引用 "详见 state-management.md §5"
- **文件**: `performance.md`
- **节省**: ~100 tokens

#### 方案 G: 补充缺失交叉引用
- **操作**: 为 architecture.md, component-design.md, performance.md 补充精确的交叉引用
- **文件**: 3 个文件
- **节省**: 无直接节省，但提升一致性

#### 方案 H: 修正章节号和引用精度
- **操作**: security.md 补充 §1 或调整章节号；checklist.md 引用补充章节号
- **文件**: `security.md`, `checklist.md`

---

## 六、预估影响

| 方案 | Token 节省 | 涉及文件 | 风险 |
|------|-----------|---------|------|
| A: performance 去重 | ~200 | 1 | 极低 |
| B: EventBus 归一化 | ~400 | 2 | 低 (需确认 state-management 承接完整) |
| C: Props 规则归一化 | ~230 | 1 | 低 |
| D: checklist 瘦身 | ~400 | 1 | 中 (需保留独有价值) |
| E: 类型模板精简 | ~200 | 1 | 低 |
| F: 状态优化引用化 | ~100 | 1 | 极低 |
| G+H: 引用补全修正 | 0 (质量提升) | 4 | 极低 |
| **合计** | **~1,530** | - | - |

### 核心结论

1. **冗余程度中等**: 约 6-7% 的 token 浪费，不算严重但值得优化
2. **职责越界明显**: 最突出的是 architecture.md 包含了过多的实现代码 (EventBus, 类型模板)，模糊了架构规范与状态管理/代码风格的边界
3. **checklist.md 定位尴尬**: 大部分内容是其他文件的摘要，独有价值仅在 Cloudscape 合规和项目结构部分
4. **交叉引用机制好但不完整**: 部分文件做了精准引用 (如 security ↔ state-management)，但部分文件缺失关键引用
5. **CLAUDE.md 入口整体合理**: 分层摘要模式正确，可补充环境配置信息

---

## 七、执行流程

**逐个问题处理，每个问题先说明优化依据，获得确认后再执行。**

执行顺序 (由简单到复杂):
1. 方案 A: performance.md 内部去重
2. 方案 B: EventBus 归一化
3. 方案 C: Props 规则归一化
4. 方案 D: checklist.md 瘦身
5. 方案 E: architecture.md 类型模板精简
6. 方案 F: performance.md 状态优化改引用
7. 方案 G: 补充缺失交叉引用
8. 方案 H: 修正章节号和引用精度

---

## 八、验证方式

优化完成后，通过以下方式验证：

1. **信息完整性**: 逐条检查被移除的内容是否在目标文件中有对应说明
2. **引用准确性**: 检查所有交叉引用 (详见 xxx.md §n) 的章节号是否指向正确位置
3. **职责单一性**: 每个文件的内容是否与文件顶部的职责声明一致
4. **Claude Code 加载测试**: 针对不同场景 (PR Review / 组件开发 / 安全审查)，验证 Claude Code 是否能正确加载对应文件并获取完整信息
