# 优化 backend/.claude/rules/architecture.md

## Context

`architecture.md`（328 行）是后端架构规范 SSOT。通过代码验证发现 4 处与实际代码不符、1 处冗余、1 处遗漏。目标：修正准确性、消除冗余、补充遗漏模式。预计优化后约 325 行。

---

## Step 1: §8 测试类表格 — 分两组重写

**文件**: `backend/.claude/rules/architecture.md` 第 286-301 行

**原因**: `TestCleanArchitectureLayers` 不存在（虚构类名），且遗漏了 9 个实际测试类。

**替换为**:

```markdown
## 8. 架构合规测试

> **测试文件**: `tests/architecture/test_architecture_compliance.py`

```bash
pytest tests/architecture -v
```

**Clean Architecture 层级测试**:

| 测试类 | 验证规则 |
|--------|---------|
| `TestApplicationLayerDoesNotImportInfrastructure` | Application 不导入 Infrastructure |
| `TestDomainLayerIndependence` | Domain 不依赖 Infrastructure/API |
| `TestApiLayerDoesNotImportInfrastructureModels` | API 不直接使用 ORM |
| `TestDomainExceptionUsage` | Entity 用域异常，非 ValueError |

**Modular Monolith 模块隔离测试**:

| 测试类 | 验证规则 |
|--------|---------|
| `TestModuleDomainLayerIsolation` | R1: Domain 零跨模块导入 |
| `TestModuleApplicationLayerDependencies` | R2/R3: Application 跨模块隔离 |
| `TestModuleApiLayerAuthDependency` | R4: Auth 依赖例外验证 |
| `TestModuleInfrastructureLayerIsolation` | Infrastructure 跨模块隔离 |
| `TestModulePublicApiExports` | `__init__.py` 定义 `__all__` |
```

## Step 2: §0.1 依赖矩阵 — 补充 Composition Root 注释

**文件**: `backend/.claude/rules/architecture.md` 第 22 行之后

**原因**: 矩阵标注 API 层对其他模块为 ❌，但 `dependencies.py` 作为 Composition Root 合法地导入了 `quotas.infrastructure.QuotaCheckerImpl` 和 `monitoring.application.PrometheusService`。不加说明会导致 Claude 误判现有代码违规。

**新增一行**:

```markdown
> **Composition Root 例外**: API 层 `dependencies.py` 作为依赖组装点，允许导入其他模块 Infrastructure 实现来注入跨模块依赖。Service 层本身仍通过 shared 接口依赖。
```

## Step 3: §2 ORM 例外 — 补充 query_impl 例外

**文件**: `backend/.claude/rules/architecture.md` 第 116 行

**原因**: 架构合规测试 `TestModuleInfrastructureLayerIsolation` 预留了两个例外（`*_model.py` 和 `*_query_impl.py`），文档只写了一个且用"唯一"修饰。

**替换**:

```markdown
**唯一例外**: ORM 模型文件 (`*_model.py`) 允许导入其他模块 ORM Model 定义外键关系
```

**改为**:

```markdown
**Infrastructure 跨模块例外**:
- ORM 模型文件 (`*_model.py`): 允许导入其他模块 ORM Model 定义外键关系
- 跨模块查询实现 (`*_query_impl.py`): 允许导入其他模块 ORM Model 用于聚合查询
```

## Step 4: 删除底部快速参考卡片

**文件**: `backend/.claude/rules/architecture.md` 第 302-328 行

**原因**: 与 §0 速查卡片内容 80% 重复，释放 25 行。

**操作**: 删除从 `## 快速参考卡片` 到文件末尾的全部内容。

## Step 5: §6 DI — 补充跨模块注入示例

**文件**: `backend/.claude/rules/architecture.md` §6 标准模板代码之后

**原因**: 当前模板只展示模块内注入，但跨模块 DI（如 quotas → training）是高频模式。

**新增**:

```markdown
### 跨模块依赖注入

跨模块依赖在**消费方 API 层** `dependencies.py` 中组装，Service 只依赖 shared 接口:

```python
# training/api/dependencies.py — 注入 quotas 模块的 IQuotaChecker
from src.modules.quotas.infrastructure import QuotaCheckerImpl, ResourceQuotaRepository
from src.shared.domain.interfaces import IQuotaChecker

async def get_quota_checker(session = Depends(get_db)) -> IQuotaChecker:
    return QuotaCheckerImpl(ResourceQuotaRepository(session))
```

**规则**: Service 层通过接口依赖，API 层 `dependencies.py` 负责实例化具体实现。
```

## Step 6: 测试文件过时引用修复

**文件**: `backend/tests/architecture/test_architecture_compliance.py`

6 处更新:
| 行号 | 原文 | 改为 |
|------|------|------|
| 7 | `see docs/module-dependency-spec.md` | `see .claude/rules/architecture.md` |
| 612 | `See docs/module-dependency-spec.md Rule R1` | `See .claude/rules/architecture.md §2 Rule R1` |
| 679 | `See docs/module-dependency-spec.md Rule R3` | `See .claude/rules/architecture.md §2 Rule R3` |
| 712 | `See docs/module-dependency-spec.md Rule R2` | `See .claude/rules/architecture.md §2 Rule R2` |
| 776 | `See docs/module-dependency-spec.md Rule R4` | `See .claude/rules/architecture.md §2 Rule R4` |
| 815 | `See: docs/ARCHITECTURE.md Section 3.3, 4.3` | `See: .claude/rules/architecture.md §2, §3` |

---

## 验证

```bash
cd backend

# 1. 架构合规测试仍通过
pytest tests/architecture -v

# 2. 测试文件无过时引用
grep -n "docs/module-dependency-spec\|docs/ARCHITECTURE" tests/architecture/test_architecture_compliance.py
# 应返回空

# 3. architecture.md 无过时引用
grep -n "docs/ARCHITECTURE" .claude/rules/architecture.md
# 应返回空

# 4. 行数合理
wc -l .claude/rules/architecture.md
# 预期 320-330 行
```
