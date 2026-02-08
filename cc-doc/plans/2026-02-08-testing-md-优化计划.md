# testing.md 优化计划

## 背景

对 `frontend/.claude/rules/testing.md` 进行 Claude Code 上下文管理最佳实践审查，识别冗余信息、内部重复、数据不一致和结构优化空间，在不影响其指导作用的前提下减少 token 浪费。

---

## 质量评估

**文件**: `frontend/.claude/rules/testing.md` (348 行)
**评分**: 78/100 (B)

| 维度 | 得分 | 说明 |
|------|------|------|
| 内容完整性 | 17/20 | 覆盖 Unit/Integration/E2E，模板实用 |
| 结构清晰度 | 15/20 | §0 速查 + 分章节详解，但末尾最佳实践无编号 |
| 冗余控制 | 12/20 | §0 陷阱与最佳实践章节高度重复 |
| 交叉引用 | 16/20 | checklist.md 引用范围偏窄 |
| 数据一致性 | 18/20 | 渲染函数名不一致 (render vs renderWithProviders) |

---

## 发现的问题

### R1: §0 陷阱 与 最佳实践章节高度重复 (~30 行冗余)

**位置**: §0 lines 52-57 vs 最佳实践 lines 333-348

| §0 陷阱 | 最佳实践 |
|---------|---------|
| ❌ 测试实现细节 → ✅ 测试行为 | ✅ 测试用户行为，而非实现细节 |
| | ❌ 测试实现细节（如内部状态） |
| ❌ `getByTestId` 优先 → ✅ 可访问性查询优先 | (无对应，但 §2.2 有完整列表) |
| ❌ 同步期望异步 → ✅ `waitFor` / `findBy` | ✅ 使用 `waitFor` 处理异步状态 |
| ❌ 硬编码 API 路径 → ✅ MSW handler 常量 | ❌ 测试文件中硬编码 API 路径 |
| | ✅ 使用 `renderWithProviders` 确保测试隔离 |
| | ❌ 过度 Mock 导致测试与真实行为偏离 |
| | ❌ 跳过测试而非修复问题 |

**问题**: 两个章节传达几乎相同的信息，且最佳实践无章节编号（不符合其他 rules 文件编号规范）

**优化方案**: 将最佳实践中的独有条目（renderWithProviders、过度 Mock、跳过测试）合并到 §0 陷阱，删除最佳实践章节

### R2: §6.1 路径别名 与 CLAUDE.md 部分重复

**位置**: testing.md §6.1 lines 286-291 vs CLAUDE.md line 82

- CLAUDE.md: `@tests/` → `tests/`
- testing.md §6.1: 列出 `@tests/`, `@features/`, `@shared/` 和 "继承 src 所有别名"

**问题**: `@features/`, `@shared/` 等非测试专属别名在 CLAUDE.md 的路径别名表中已有完整定义

**优化方案**: §6.1 只保留测试专属的 `@tests/` 别名，其余替换为引用

### D1: 渲染函数命名不一致

**位置**: §6.2 line 296 vs 最佳实践 line 337

- §6.2: `import { render, renderWithQuery } from '@tests/__utils__/test-utils'`
- 最佳实践: "使用 `renderWithProviders` 确保测试隔离"

**问题**: `renderWithProviders` 在 §6.2 中实际叫 `render`（带 Provider 包装）。名称不一致可能导致 Claude 生成不存在的函数调用

**优化方案**: 统一为 §6.2 的实际名称 `render`（来自 test-utils）

### X1: checklist.md 交叉引用范围偏窄

**位置**: checklist.md line 115

- 当前: "详见 [testing.md](testing.md) §1-4"
- 实际: 覆盖率在 §7，查询优先级在 §2，配置在 §6

**优化方案**: 更新为 "详见 [testing.md](testing.md) §0-7"

---

## 执行计划

按上次会话惯例，逐一确认执行：

### 方案 A: 合并最佳实践到 §0，消除重复

**文件**: `frontend/.claude/rules/testing.md`
**操作**:
1. 将最佳实践独有条目合并到 §0 陷阱表格
2. 统一渲染函数名为 `render`（来自 test-utils）
3. 删除末尾"最佳实践"章节 (lines 333-348)
**预计**: 净减少 ~15 行 / ~200 tokens

### 方案 B: 精简 §6.1 路径别名

**文件**: `frontend/.claude/rules/testing.md`
**操作**: §6.1 只保留 `@tests/` 别名 + CLAUDE.md 引用
**预计**: 净减少 ~4 行 / ~50 tokens

### 方案 C: 修正 checklist.md 交叉引用

**文件**: `frontend/.claude/rules/checklist.md`
**操作**: "§1-4" → "§0-7"
**预计**: 1 行修改

---

## 涉及文件

| 文件 | 变更类型 |
|------|---------|
| `frontend/.claude/rules/testing.md` | 方案 A, B |
| `frontend/.claude/rules/checklist.md` | 方案 C |

## 验证方式

1. 检查所有交叉引用章节号准确性
2. 确认 §0 陷阱表格包含所有关键规则（无遗漏）
3. 确认删除最佳实践章节后无信息丢失
