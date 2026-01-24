# 死代码清理计划

## 概述

基于对 AI Studio 项目的深度分析，识别了后端和前端的死代码、未使用的导出、空模块和过时注释。本计划详细说明清理步骤和验证流程。

---

## 发现汇总

### 后端 (Python/FastAPI)

| 类别 | 数量 | 严重程度 |
|------|------|---------|
| 空 `__init__.py` 文件 | 13 | SAFE |
| 过时 TODO 注释 | 2 | DANGER |
| 未实现模块 (billing) | 1 | SAFE |
| 示例文件 | 1 | SAFE |

### 前端 (TypeScript/React)

| 类别 | 数量 | 严重程度 |
|------|------|---------|
| 占位符页面导出 | 5 | SAFE |
| 未使用 hooks | 15+ | CAUTION |
| 未使用共享 hooks | 4 | CAUTION |
| 测试覆盖缺陷 | 多 | CAUTION |

---

## 清理步骤

### Phase 1: 后端安全清理 (SAFE)

#### 1.1 删除 router.py 中过时的 TODO 注释

**文件**: `backend/src/router.py`

**操作**: 删除第 10 行和第 23 行的过时 TODO 注释

```python
# 删除这行: # TODO: Uncomment as modules are migrated
```

**验证**:
```bash
cd backend && pytest tests/ -v
```

#### 1.2 删除 Datasets 模块空文件

**文件列表**:
- `backend/src/modules/datasets/api/schemas/__init__.py`
- `backend/src/modules/datasets/application/__init__.py`
- `backend/src/modules/datasets/application/services/__init__.py`
- `backend/src/modules/datasets/domain/__init__.py`
- `backend/src/modules/datasets/domain/entities/__init__.py`
- `backend/src/modules/datasets/domain/repositories/__init__.py`
- `backend/src/modules/datasets/domain/value_objects/__init__.py`
- `backend/src/modules/datasets/infrastructure/__init__.py`
- `backend/src/modules/datasets/infrastructure/models/__init__.py`
- `backend/src/modules/datasets/infrastructure/repositories/__init__.py`

**验证**:
```bash
cd backend && python -c "from src.modules.datasets import router" && pytest tests/ -v
```

#### 1.3 移动示例文件

**操作**: 将 `backend/examples/mlflow_training_example.py` 移动到 `docs/examples/`

```bash
mkdir -p docs/examples
mv backend/examples/mlflow_training_example.py docs/examples/
rmdir backend/examples  # 如果为空
```

**验证**: 无需测试（示例文件不影响生产代码）

---

### Phase 2: 前端安全清理 (SAFE)

#### 2.1 删除空的页面导出文件

**文件列表**:
- `frontend/src/features/audit/pages/index.ts` (仅包含 `export {}`)
- `frontend/src/features/billing/pages/index.ts` (仅包含 `export {}`)
- `frontend/src/features/monitoring/pages/index.ts` (仅包含 `export {}`)

**验证**:
```bash
cd frontend && npm run build && npm test
```

---

### Phase 3: 前端谨慎清理 (CAUTION)

#### 3.1 删除未使用的 Training Hooks

**文件**: `frontend/src/features/training/hooks/index.ts`

**删除函数**:
- `useTrainingJobStats()`
- `useCanPauseJob()`
- `useCanResumeJob()`
- `useCanCancelJob()`
- `useCanDeleteJob()`
- `useJobDuration()`
- `useJobProgress()`
- `usePriorityWeight()`
- `useIsJobActive()`
- `useIsJobFinished()`
- `useTotalGpus()`

**验证**:
```bash
cd frontend && npm run build && npm test
```

#### 3.2 共享 Hooks (保留)

**决策**: 用户选择保留共享 hooks，不删除

**保留文件**:
- `frontend/src/shared/hooks/useEntity.ts` (260 行)
- `frontend/src/shared/hooks/usePagination.ts` (243 行)
- `frontend/src/shared/hooks/useDebounce.ts` (162 行)
- `frontend/src/shared/hooks/useLocalStorage.ts` (188 行)

**原因**: 通用工具可能在未来功能开发中使用

#### 3.3 删除未使用的 Resource Quotas Hooks

**文件**: `frontend/src/features/resource-quotas/hooks/index.ts`

**删除函数**:
- `useQuotaUsage()`
- `useUsagePercentage()`
- `useUsageColor()`
- `useIsQuotaNearLimit()`
- `useIsQuotaValid()`
- `useQuotaRemainingDays()`
- `useQuotaStatusLabel()`
- `useQuotaTypeLabel()`
- `useFormatGpuTypes()`

**保留**: `useResourceLimitConfigs()` (被 ResourceQuotasPage 使用)

**验证**:
```bash
cd frontend && npm run build && npm test
```

---

### Phase 4: 暂不处理 (DEFER)

以下项目暂不清理，原因如下：

#### 4.1 Billing 模块 (backend) - 用户确认保留

**原因**: 虽然是骨架模块，但在 `specs/001-ai-training-platform/plan.md` 中列为未来功能
**决定**: 保留并标记为 WIP
**操作**: 在模块 `__init__.py` 添加 WIP 文档注释

#### 4.2 Spaces 模块 (backend)

**原因**: 数据模型完整，仅缺 SageMaker 集成
**决定**: 保留，将 TODO 转为 GitHub Issue

#### 4.3 占位符页面 (frontend router)

**原因**: 这些是路由系统的必要占位符，移除会破坏导航
**决定**: 保留，实现实际页面组件

---

## 验证流程

### 每步验证清单

1. **运行完整测试套件**
   ```bash
   # 后端
   cd backend && pytest tests/ -v --tb=short

   # 前端
   cd frontend && npm test && npm run build
   ```

2. **验证导入完整性**
   ```bash
   # 后端
   cd backend && python -c "from src.main import app"

   # 前端
   cd frontend && npx tsc --noEmit
   ```

3. **验证 lint 通过**
   ```bash
   # 后端
   cd backend && ruff check src/

   # 前端
   cd frontend && npm run lint
   ```

### 回滚策略

每次清理操作前：
1. 确保在 feature 分支上工作
2. 提交当前状态
3. 执行清理
4. 运行测试
5. 如失败，执行 `git checkout .`

---

## 预期结果

### 清理后统计

| 指标 | 清理前 | 清理后 | 减少 |
|------|--------|--------|------|
| 后端空文件 | 13 | 3 | 10 |
| 后端过时注释 | 2 | 0 | 2 |
| 前端模块特定未使用 hooks | 20+ | 0 | 20+ |
| 前端未使用共享 hooks | 4 | 4 (保留) | 0 |
| 总代码行数减少 | - | - | ~300 行 |

**注意**: 用户选择保留共享 hooks (850 行)，因此总删除量减少。

### 报告生成位置

清理完成后，报告将保存至：
- `.reports/dead-code-analysis.md` - 完整分析报告
- `.reports/cleanup-summary.md` - 清理摘要

---

## 关键文件路径

### 后端

- `backend/src/router.py` - 路由注册（删除过时注释）
- `backend/src/modules/datasets/` - 空文件清理
- `backend/examples/` - 示例文件移动

### 前端

- `frontend/src/features/*/pages/index.ts` - 空导出清理
- `frontend/src/features/training/hooks/index.ts` - 未使用 hooks
- `frontend/src/shared/hooks/` - 未使用共享 hooks
- `frontend/src/features/resource-quotas/hooks/index.ts` - 未使用 hooks

---

## 执行命令汇总

```bash
# Phase 1: 后端清理
cd backend
pytest tests/ -v  # 预检查

# 删除空文件（Phase 1.2）
rm src/modules/datasets/api/schemas/__init__.py
rm src/modules/datasets/application/__init__.py
rm src/modules/datasets/application/services/__init__.py
rm src/modules/datasets/domain/__init__.py
rm src/modules/datasets/domain/entities/__init__.py
rm src/modules/datasets/domain/repositories/__init__.py
rm src/modules/datasets/domain/value_objects/__init__.py
rm src/modules/datasets/infrastructure/__init__.py
rm src/modules/datasets/infrastructure/models/__init__.py
rm src/modules/datasets/infrastructure/repositories/__init__.py

pytest tests/ -v  # 后检查

# Phase 2-3: 前端清理
cd ../frontend
npm test  # 预检查
npm run build  # 预检查

# 删除空导出文件
rm src/features/audit/pages/index.ts
rm src/features/billing/pages/index.ts
rm src/features/monitoring/pages/index.ts

npm test  # 后检查
npm run build  # 后检查
```

---

## 风险评估

| 操作 | 风险级别 | 回滚难度 |
|------|---------|---------|
| 删除空 `__init__.py` | 低 | 简单 (git checkout) |
| 删除过时注释 | 无 | 简单 |
| 删除未使用 hooks | 中 | 简单 |
| 移动示例文件 | 无 | 简单 |

---

## 注意事项

1. **测试诚信**: 切勿跳过或禁用测试来通过清理
2. **增量提交**: 每个 Phase 完成后提交
3. **分支策略**: 在 `refactor/dead-code-cleanup` 分支上工作
4. **代码审查**: 清理 PR 需要审查后合并
