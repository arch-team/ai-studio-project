# 优化 state-management.md Claude Code Context 文件

## Context

`frontend/.claude/rules/state-management.md` 作为 Claude Code 的上下文文件（387行），每次 Claude 处理前端状态管理相关任务时都会被自动加载。该文件存在以下问题：
- 速查卡片中决策表与流程图信息重复度约90%
- 代码示例中存在结构完全相同的重复模块
- 部分内容与 §2.3 节 Selector Hooks 重复
- 整体可压缩约 18%（~72行），节约约 1800-2000 token

**目标**: 在不改变文件指导作用的前提下，提高信息密度，减少冗余 token 消耗。

## 优化操作清单

### 高优先级

#### 1. 删除决策流程图，将关键信息并入决策表
- **位置**: §0 速查卡片，第23-41行
- **原因**: 决策流程图与上方决策表（第9-19行）信息重合度~90%。对 AI 来说，表格格式的结构化数据比 ASCII 流程图解析效率更高
- **操作**:
  - 删除整个"决策流程图"代码块
  - 将流程图中唯一的额外信息——"⚠️ 禁止持久化敏感数据"——作为备注添加到决策表"全局 UI 状态"行
- **节约**: ~18行

#### 2. queryKeys 工厂只保留1个模块示例
- **位置**: §1.1，第61-87行
- **原因**: `trainingJobs`、`datasets`、`models` 三个模块结构完全相同（all/lists/list/details/detail），只有命名不同
- **操作**: 只保留 `trainingJobs` 模块 + 末尾注释 `// datasets, models 等其他模块遵循相同结构`
- **节约**: ~12行

#### 3. 删除最佳实践中重复的 Selector 对比
- **位置**: §5，第379-386行
- **原因**: 这段"错误-获取整个 store / 正确-细粒度 selector"的对比与 §2.3 Selector Hooks 内容完全重复
- **操作**: 替换为一行引用 `// Zustand 细粒度 Selector 示例见 §2.3`
- **节约**: ~7行

### 中优先级

#### 4. 压缩 Auth Store 代码
- **位置**: §2.1，第189-211行
- **操作**: 去掉 interface 独立声明，改为 `create<{...}>()` 内联类型声明（或保留 interface 但去掉 TypeScript 已可自解释的注释行）
- **节约**: ~7行

#### 5. 压缩 UI Store 代码
- **位置**: §2.2，第215-238行
- **操作**: 精简 interface 定义，与 create 实现更紧凑排列，重点突出 `persist` 中间件包装模式
- **节约**: ~9行

#### 6. 压缩 React Hook Form + Zod 示例
- **位置**: §3，第264-295行
- **操作**: 保留 schema 定义 + useForm 配置核心代码，去掉完整的组件函数包装和 JSX return 部分（`<form>` 标签内容对指导价值较低，保留注释 `// JSX: handleSubmit(onSubmit)` 即可）
- **节约**: ~9行

#### 7. EventBus 订阅只保留1个示例
- **位置**: §4.3，第338-357行
- **操作**: `training-job:completed` 和 `dataset:deleted` 两个订阅结构完全相同，保留1个 + 注释说明其他事件同理
- **节约**: ~6行

### 低优先级

#### 8. 精简 Auth Store 安全说明
- **位置**: §2.1 的 blockquote，第186-187行
- **操作**: 从2行压缩为1行 + security.md 引用链接
- **节约**: ~1行

#### 9. EventMap 精简为3-4个代表性事件
- **位置**: §4.1，第306-316行
- **操作**: 保留3-4个代表不同 payload 形状的事件（对象、void、联合类型），去掉冗余事件
- **节约**: ~3行

## 关键约束

### 章节编号不可变
其他 rules 文件已通过章节号建立交叉引用，必须保持不变：
- `architecture.md` → "state-management.md §4"
- `architecture.md` → "state-management.md §1.4"
- `performance.md` → "state-management.md §2.3 和 §5"
- `security.md` → "state-management.md §2.1"

### 保留不动的高价值内容
- 乐观更新完整模式（§1.3）—— 复杂模式需完整步骤
- QueryClient 全局配置（§1.4）—— 错误处理策略关键配置
- Selector Hooks 三个示例（§2.3）—— 各有独立教学价值
- EventBus 发布事件示例（§4.2）—— mutation + event 联动核心模式
- 文件位置速查表（§0）—— 独立高价值索引

## 预期效果

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 总行数 | 387 | ~315 |
| 减少比例 | - | ~18.6% |
| Token 节约 | - | ~1800-2000 |
| 章节编号 | §0-§5 | §0-§5（不变） |
| 交叉引用 | 5处 | 5处（全部有效） |

## 涉及文件

- `frontend/.claude/rules/state-management.md` —— 本次修改的唯一文件
- `frontend/.claude/rules/architecture.md` —— 仅验证交叉引用有效（不修改）
- `frontend/.claude/rules/performance.md` —— 仅验证交叉引用有效（不修改）
- `frontend/.claude/rules/security.md` —— 仅验证交叉引用有效（不修改）

## 验证方式

1. 人工检查优化后的文件，确认所有核心模式模板仍完整可用
2. 验证其他 rules 文件的交叉引用（§编号）仍然指向正确内容
3. 对比优化前后行数，确认压缩目标达成
