# 前端 Claude Code 上下文管理规范 - 冗余分析与优化计划

## Context

前端子项目刚完成从 `ai-agents-platform` 的规范迁移，当前 `frontend/.claude/rules/` 下有 9 个规范文件 + 1 个 CLAUDE.md 入口文件。本次分析旨在：
1. 识别各规范文件之间的冗余信息
2. 检查是否存在职责重叠、违反单一职责原则的问题
3. 结合 Claude Code 上下文管理最佳实践提出优化方案

**决策**: 保持 9 个 rules 文件结构不变，不合并不删除，聚焦**冗余消除 + 职责归正**。

---

## 一、冗余信息分析

### 高优先级冗余（建议修复）

| # | 重复内容 | 文件 A | 文件 B | 严重度 |
|---|---------|--------|--------|--------|
| R1 | EventBus 通信概念描述 | `architecture.md` §4.2 | `state-management.md` §4.1-4.3 | **高** |
| R2 | 类型定义位置规则 | `architecture.md` §5.2 | `code-style.md` §2.1 | **中高** |
| R3 | `checklist.md` 全文 | `checklist.md` 10 个章节 | 其他 8 个 rules 文件 | **高（结构性）** |

**R1 详情**: `architecture.md` §4.2 描述了 EventBus 的核心概念和事件驱动通信方式，而 `state-management.md` §4 给出了完整的 EventMap 定义、发布/订阅 Hooks、Query Invalidation 联动实现。虽然已有交叉引用，但 architecture.md §4.2 的概念描述段落本质上是 state-management.md §4 的摘要，属于冗余。

**R2 详情**: `architecture.md` §5.2 定义"types/index.ts 应包含的类型分类"（枚举、Entity、Request/Response、Filter、UI Helper），`code-style.md` §2.1 定义"类型放在哪个文件"（实体类型、API 响应类型 → `features/{module}/types/index.ts`）。两者回答同一问题，内容几乎完全对齐。

**R3 详情**: `checklist.md` 的每个章节都是对应 rules 文件核心规则的提炼。暂不处理。

### 低优先级冗余（可接受，保持现状）

| # | 重复内容 | 说明 | 判断 |
|---|---------|------|------|
| R4 | CLAUDE.md 核心约束 vs 各 rules 详细展开 | CLAUDE.md 5 条核心约束是各 rules 的摘要 | **合理** — 入口文件应提供高频规则速查 |
| R5 | CLAUDE.md 命令速查 vs testing.md 命令列表 | CLAUDE.md 面向全场景，testing.md 面向测试 | **合理** — 各有侧重 |
| R6 | architecture.md §0.3 模块结构 vs component-design.md §5 组件文件结构 | 前者是模块级，后者是组件级 | **互补关系** — 粒度不同 |
| R7 | component-design.md §1.2 容器型组件 useQuery vs state-management.md §1.2 Query Hook | 前者是"使用方"视角，后者是"定义方"视角 | **合理** — 消费者-生产者分离 |

---

## 二、职责重叠分析

### O1: architecture.md 的"错误处理规范"(§7) 职责归属

- **现状**: architecture.md §6.3（错误类型体系）+ §7.1-7.4（错误处理层级、API 错误、Query 错误、错误码映射），共约 90 行，占 architecture.md 的 19%
- **分析**:
  - §6.3 ErrorCode/AppError 定义 → **属于架构职责**（共享内核的类型合同）
  - §7.1 错误处理层级图 → **属于架构职责**（系统级设计决策）
  - §7.2 API 错误处理 (ApiClient 实现) → 偏实现，但与共享内核 ApiClient 强相关，可保留
  - **§7.3 Query 错误处理 (QueryProvider 配置) → 应属 state-management.md**（React Query 全局配置）
  - §7.4 错误码映射表 → **属于架构职责**（前后端对齐信息）
- **建议**: 将 §7.3 移至 `state-management.md`

### O2: architecture.md §8.2 运行命令与 CLAUDE.md 命令速查重叠

- **现状**: architecture.md §8.2 列出 `npm run lint` 和 `npx tsc --noEmit`
- **分析**: 与 CLAUDE.md 命令速查完全重复
- **建议**: 删除 §8.2，仅保留 §8.1 ESLint 规则配置

### O3: EventBus 决策层 vs 实现层边界模糊

- **现状**: architecture.md §4 = 决策矩阵(4.1) + 概念描述(4.2)；state-management.md §4 = 完整实现
- **分析**: architecture.md 应回答"何时用 EventBus"，state-management.md 应回答"如何用 EventBus"。当前 architecture.md §4.2 超出了决策层职责
- **建议**: architecture.md §4.2 精简为仅保留引用句

### O4: code-style.md §2.1 类型位置与 architecture.md §5.2 重叠

- **现状**: 两个文件都回答"类型定义放哪"
- **分析**: architecture.md §5.2 是模块结构约束（架构职责），code-style.md §2.1 应聚焦架构未覆盖的编码规范
- **建议**: code-style.md §2.1 删除重叠行，仅保留独有的"组件 Props"和"通用类型"位置规则

---

## 三、Claude Code 上下文管理分析

### Token 消耗估算

| 文件 | 行数 | 估算 token |
|------|------|-----------|
| CLAUDE.md | 100 | ~700 |
| architecture.md | 465 | ~3,200 |
| state-management.md | 357 | ~2,500 |
| component-design.md | 301 | ~2,100 |
| testing.md | 348 | ~2,400 |
| code-style.md | 131 | ~900 |
| security.md | 161 | ~1,100 |
| performance.md | 150 | ~1,000 |
| accessibility.md | 194 | ~1,300 |
| checklist.md | 150 | ~1,000 |
| **合计** | **~2,357** | **~16,200** |

### 关键观察

1. **全量加载**: `.claude/rules/` 下 9 个文件在每次对话时全部加载
2. **三层摘要**: CLAUDE.md 核心约束 → 各文件速查卡片 → 详细内容。对 Claude 来说速查卡片的边际价值降低
3. **交叉引用**: 文件间存在双向引用，本次优化后改为**单向引用**以降低认知复杂度

---

## 四、优化方案

### 方案: 保持 9 个文件结构不变，精简 3 个文件的冗余内容

| 文件 | 操作 |
|------|------|
| `architecture.md` | **精简 3 处**: §4.2 概念描述、§7.3 Query 错误处理、§8.2 运行命令 |
| `state-management.md` | **新增 1 处**: §1.4 全局错误处理（从 architecture.md §7.3 移入） |
| `code-style.md` | **精简 1 处**: §2.1 移除与 architecture.md 重叠的类型位置行 |
| 其他 6 个文件 | 不修改 |
| `CLAUDE.md` | 不修改（文档导航不变） |

### 4.1 architecture.md 精简（3 处修改）

**修改 A: §4.2 事件驱动通信 → 精简为引用句**

当前内容（architecture.md 第 239-245 行）包含 EventBus 概念描述 + 引用，与 state-management.md §4 重复。

修改后 §4.2 仅保留两行：
```markdown
### 4.2 事件驱动通信

事件驱动通信通过 `shared/events/eventBus.ts` 实现，支持类型安全的发布/订阅模式。

**核心概念**: `EventMap` 接口定义所有事件类型 → `useEventPublisher` 发布事件 → `useEventSubscription` 订阅事件

> EventBus 完整实现（EventMap 定义、发布/订阅 Hooks、Query Invalidation 联动示例）详见 [state-management.md](state-management.md) §4
```

（注：当前 §4.2 已经是这个精简形式了，即之前的迁移已做了正确处理。确认无需修改。）

**修改 B: §7.3 Query 错误处理 → 移至 state-management.md**

`architecture.md` 第 383-405 行的 QueryClient `defaultOptions` 代码块（retry 策略 + mutation onError）移至 `state-management.md`。

architecture.md §7 修改后结构：
- §7.1 错误处理层级（保留）
- §7.2 API 错误处理（保留）
- ~~§7.3 Query 错误处理~~（移出）→ 替换为引用：`> Query 层错误处理配置详见 [state-management.md](state-management.md) §1.4`
- §7.4 错误码映射（保留，原编号调整为 §7.3）

**修改 C: §8.2 运行合规检查 → 删除**

删除 architecture.md 第 448-452 行：
```bash
npm run lint            # ESLint 检查
npx tsc --noEmit        # TypeScript 类型检查
```

这两个命令已在 CLAUDE.md 命令速查中列出。§8 仅保留 §8.1 ESLint 规则配置。

### 4.2 state-management.md 微调（1 处修改）

**新增 §1.4 全局错误处理配置**

在 §1.3（乐观更新模式）之后新增，内容为从 architecture.md §7.3 移入的 QueryClient 错误处理代码块：

```typescript
// app/providers/QueryProvider.tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        if (error instanceof AppError && error.isNotFound()) {
          return false; // 404 不重试
        }
        return failureCount < 3;
      },
    },
    mutations: {
      onError: (error) => {
        if (error instanceof AppError) {
          eventBus.publish('notification:show', {
            type: 'error',
            message: getErrorMessage(error),
          });
        }
      },
    },
  },
});
```

引用：`> 错误类型体系（ErrorCode, AppError）定义详见 [architecture.md](architecture.md) §6.3`

### 4.3 code-style.md 精简（1 处修改）

**修改: §2.1 类型定义位置**

当前表格（code-style.md 第 83-91 行）4 行中，"实体类型"和"API 响应类型"与 architecture.md §5.2 重复。

修改后：
```markdown
### 2.1 类型定义位置

> 模块类型分类（枚举、Entity、Request/Response、Filter、UI Helper Constants）详见 [architecture.md](architecture.md) §5.2

| 类型 | 位置 |
|------|------|
| 组件 Props | 组件文件内或同目录 `.types.ts` |
| 通用类型 | `shared/types/` |
```

### 优化后交叉引用关系

```
architecture.md (架构决策)
  → state-management.md  (§4.2 EventBus 实现, §7.3→1.4 Query 错误处理)

state-management.md (状态实现)
  → architecture.md      (§1.4 引用错误类型定义 §6.3)
  → security.md          (§2.1 引用 Token 安全)

component-design.md (组件设计)
  → code-style.md        (§0 引用命名规范)

code-style.md (编码风格)
  → architecture.md      (§2.1 引用类型分类 §5.2)
```

注意：architecture.md ↔ state-management.md 之间仍有引用关系，但不再是**同一主题的双向描述**。architecture.md 引用 state-management 的 EventBus 实现（不同主题），state-management 引用 architecture 的错误类型定义（不同主题），这是合理的"概念定义方 vs 使用方"关系。

---

## 五、涉及文件

| 文件 | 操作 |
|------|------|
| `frontend/.claude/rules/architecture.md` | 精简 §4.2/§7.3/§8.2 |
| `frontend/.claude/rules/state-management.md` | 新增 §1.4 |
| `frontend/.claude/rules/code-style.md` | 精简 §2.1 |

## 六、执行步骤

1. **architecture.md**: 将 §7.3 Query 错误处理代码块完整复制备用
2. **architecture.md**: 删除 §7.3 代码块，替换为引用句
3. **architecture.md**: 删除 §8.2 运行命令小节
4. **architecture.md**: 确认 §4.2 已是精简形式（如果不是则精简）
5. **state-management.md**: 在 §1.3 之后新增 §1.4，粘贴移入的代码块 + 引用句
6. **code-style.md**: 精简 §2.1，移除重复行，添加引用句
7. **验证所有交叉引用链接正确**

## 七、验证方式

- 确认 architecture.md 不再包含 §7.3 Query 错误处理代码块（约 20 行）
- 确认 architecture.md §8 不再包含运行命令（约 5 行）
- 确认 state-management.md 新增了 §1.4 全局错误处理，内容与原 architecture.md §7.3 一致
- 确认 code-style.md §2.1 仅保留"组件 Props"和"通用类型"两行
- 确认所有交叉引用路径和章节编号正确
- `git diff` 审查所有变更
