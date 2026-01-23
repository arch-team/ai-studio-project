# Claude Code 上下文配置最佳实践样例

本文档为 8 类项目规范提供完整的配置样例，遵循 Claude Code 上下文管理原则。

---

## 载体分配总览

| 规范类别 | 推荐载体 | 原因 |
|---------|---------|------|
| 术语与命名 | `CLAUDE.md` | 高频引用，全局可见 |
| 架构约束 | `CLAUDE.md` | 决策依据，需常驻 |
| 编码风格 | `.claude/rules/*.md` | 文件类型相关 |
| 测试策略 | `CLAUDE.md` + Rules | 原则在 CLAUDE.md，细节在 Rules |
| API 设计 | `CLAUDE.md` | 开发决策依据 |
| 安全约束 | `CLAUDE.md` + Rules | 核心原则 + 文件类型细则 |
| 文档要求 | `.claude/rules/*.md` | 文件类型相关 |
| 特殊约定 | `CLAUDE.md` | 项目级约束 |

---

## 1. 术语与命名

**载体**：`./CLAUDE.md`

```markdown
## Terminology

**核心实体命名**：

| 中文术语 | 英文类名 | 数据库表 | API 路径 |
|---------|---------|---------|---------|
| 训练任务 | `TrainingJob` | `training_jobs` | `/training-jobs` |
| 数据集 | `Dataset` | `datasets` | `/datasets` |
| 检查点 | `Checkpoint` | `checkpoints` | `/checkpoints` |
| 资源配额 | `ResourceQuota` | `resource_quotas` | `/resource-quotas` |

**状态枚举**：
- 训练任务：`pending` → `running` → `completed` / `failed` / `cancelled`
- 数据集：`uploading` → `processing` → `ready` / `error`

**命名约定**：
- 类名：PascalCase (`TrainingJob`)
- 变量/函数：snake_case (`get_training_job`)
- 常量：UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`)
- API 路径：kebab-case (`/training-jobs`)

**中英文策略**：
- 代码、注释、commit message：英文
- 用户界面、文档：中文
- 日志：英文（便于检索）
```

---

## 2. 架构约束

**载体**：`./CLAUDE.md`

```markdown
## Architecture

**架构模式**：DDD + Modular Monolith + Clean Architecture

**依赖方向**（严格遵循）：
```
API Layer → Application Layer → Domain Layer ← Infrastructure Layer
```

**模块边界**：
```
src/
├── training/          # 训练任务领域
│   ├── domain/        # 实体、值对象、领域服务
│   ├── application/   # 用例、命令、查询
│   ├── infrastructure/# 仓库实现、外部服务
│   └── api/           # 路由、DTO
├── dataset/           # 数据集领域
├── checkpoint/        # 检查点领域
└── shared/            # 共享内核（跨领域复用）
```

**架构约束**：
- Domain 层禁止依赖 Infrastructure
- 跨模块通信通过 Application 层事件
- 共享代码放 `shared/`，禁止模块间直接导入
- 外部服务调用必须通过 Infrastructure 层抽象

**关键入口**：
- API 入口：`src/*/api/routes.py`
- 领域模型：`src/*/domain/entities.py`
- 用例实现：`src/*/application/use_cases/`
```

---

## 3. 编码风格

**载体**：`.claude/rules/code-style.md`（无条件规则）

```markdown
# 编码风格规范

## Python

- 遵循 PEP 8，行宽 100 字符
- 使用 type hints（Python 3.10+ 语法）
- 导入排序：stdlib → third-party → local（isort 管理）
- 字符串：优先 f-string，禁止 % 格式化

## 类型注解

```python
# Good
def get_job(job_id: str) -> TrainingJob | None:
    ...

# Bad - 避免旧式 Optional
def get_job(job_id: str) -> Optional[TrainingJob]:
    ...
```

## 导入规范

```python
# Good - 明确导入
from training.domain.entities import TrainingJob
from training.domain.value_objects import JobStatus

# Bad - 禁止通配符导入
from training.domain.entities import *
```

## 格式化工具

- Python: `ruff format` + `ruff check`
- YAML/JSON: `prettier`
- Markdown: `prettier`
```

**载体**：`.claude/rules/python-style.md`（路径条件规则）

```yaml
---
paths:
  - "**/*.py"
---

# Python 编码规范

- 函数长度 < 50 行，超出需拆分
- 类方法数 < 10 个，超出考虑拆分职责
- 嵌套深度 < 4 层
- 禁止裸 except，必须指定异常类型
- 禁止 mutable 默认参数（`def foo(items=[])`）
```

---

## 4. 测试策略

**载体**：`./CLAUDE.md`（核心原则）

```markdown
## Testing Strategy

**TDD 工作流**：
```
1. Red   → 先写失败的测试
2. Green → 编写最少代码使测试通过
3. Refactor → 重构代码，保持测试通过
```

**测试分层**：

| 层级 | 目标 | 比例 | 运行频率 |
|------|------|:----:|---------|
| Unit | 实体、值对象、领域逻辑 | 70% | 每次提交 |
| Integration | API 端点、仓库实现 | 20% | PR 合并前 |
| E2E | 关键用户流程 | 10% | 发布前 |

**覆盖率要求**：
- 整体 ≥ 80%
- Domain 层 ≥ 90%
- 新代码 ≥ 85%

**测试诚信原则**：切勿为让测试通过而伪造结果。测试失败 = 代码有问题。
```

**载体**：`.claude/rules/testing.md`（路径条件规则）

```yaml
---
paths:
  - "**/tests/**"
  - "**/*_test.py"
  - "**/test_*.py"
---

# 测试编写规范

## 命名规范

```python
# 函数命名：test_<被测功能>_<场景>_<预期结果>
def test_create_job_with_valid_params_returns_job():
    ...

def test_create_job_with_empty_name_raises_validation_error():
    ...
```

## AAA 模式

```python
def test_job_status_transition():
    # Arrange - 准备测试数据
    job = TrainingJob.create(name="test")

    # Act - 执行被测行为
    job.start()

    # Assert - 验证结果
    assert job.status == JobStatus.RUNNING
```

## Mock 原则

- Mock 外部依赖（数据库、API、文件系统）
- 不 Mock 被测单元本身
- 优先使用 `pytest-mock` 的 `mocker` fixture
```

---

## 5. API 设计

**载体**：`./CLAUDE.md`

```markdown
## API Design

**风格**：RESTful + OpenAPI 3.0

**路径约定**：
- 资源复数：`/training-jobs`（非 `/training-job`）
- 嵌套资源：`/training-jobs/{id}/checkpoints`
- 操作动词：`POST /training-jobs/{id}/start`（非 CRUD 操作）

**版本控制**：
- URL 路径版本：`/api/v1/training-jobs`
- 主版本号变更 = 破坏性变更

**请求/响应格式**：

```json
// 成功响应
{
  "data": { ... },
  "meta": { "request_id": "xxx" }
}

// 错误响应
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Job name is required",
    "details": [
      { "field": "name", "message": "This field is required" }
    ]
  },
  "meta": { "request_id": "xxx" }
}
```

**HTTP 状态码**：
- 200：成功（GET/PUT/PATCH）
- 201：创建成功（POST）
- 204：删除成功（DELETE）
- 400：请求参数错误
- 401：未认证
- 403：无权限
- 404：资源不存在
- 422：业务逻辑错误
- 500：服务器内部错误
```

---

## 6. 安全约束

**载体**：`./CLAUDE.md`（核心原则）

```markdown
## Security

**敏感信息处理**：
- 禁止硬编码密钥、token、密码
- 敏感配置通过环境变量注入
- 日志禁止打印敏感字段（password、token、secret）

**认证授权**：
- 认证：JWT Bearer Token
- 授权：RBAC（基于角色的访问控制）
- Token 过期时间：Access 15min，Refresh 7day

**输入验证**：
- 所有外部输入必须验证
- 使用 Pydantic 进行类型校验
- SQL 参数化查询，禁止字符串拼接
```

**载体**：`.claude/rules/security.md`（路径条件规则）

```yaml
---
paths:
  - "**/*.py"
  - "**/*.env*"
  - "**/config/**"
---

# 安全编码规范

## 禁止项

```python
# Bad - 硬编码密钥
API_KEY = "sk-xxxx"

# Good - 环境变量
API_KEY = os.environ["API_KEY"]
```

```python
# Bad - SQL 拼接
query = f"SELECT * FROM users WHERE id = {user_id}"

# Good - 参数化
query = "SELECT * FROM users WHERE id = :id"
session.execute(query, {"id": user_id})
```

## 日志脱敏

```python
# Bad
logger.info(f"User login: {username}, password: {password}")

# Good
logger.info(f"User login: {username}")
```

## 敏感文件

- `.env` 文件必须在 `.gitignore` 中
- 提供 `.env.example` 作为模板（不含真实值）
```

---

## 7. 文档要求

**载体**：`.claude/rules/documentation.md`（路径条件规则）

```yaml
---
paths:
  - "**/*.py"
---

# 文档规范

## Docstring 要求

公共 API（模块、类、函数）必须有 docstring：

```python
def create_training_job(
    name: str,
    config: JobConfig,
) -> TrainingJob:
    """创建训练任务。

    Args:
        name: 任务名称，长度 1-100 字符
        config: 任务配置，包含资源规格和训练参数

    Returns:
        创建的训练任务实例

    Raises:
        ValidationError: 参数校验失败
        QuotaExceededError: 资源配额不足
    """
```

## 注释原则

- 注释解释 WHY，代码说明 WHAT
- 复杂算法需要注释说明思路
- TODO 格式：`# TODO(author): description`
```

**载体**：`.claude/rules/readme.md`（路径条件规则）

```yaml
---
paths:
  - "**/README.md"
---

# README 结构规范

每个模块的 README 应包含：

1. **概述**：模块职责（1-2 句话）
2. **快速开始**：最小可运行示例
3. **API 参考**：关键接口说明
4. **配置项**：环境变量和配置文件
5. **开发指南**：本地开发和测试命令
```

---

## 8. 特殊约定

**载体**：`./CLAUDE.md`

```markdown
## Special Conventions

**项目禁忌**：
- 禁止直接操作数据库，必须通过 Repository
- 禁止在 Domain 层引入框架依赖（FastAPI、SQLAlchemy）
- 禁止跨模块直接导入（通过事件或共享内核）
- 禁止在生产代码中使用 `print()`，使用 `logger`

**外部集成要求**：
- AWS SDK 调用必须封装在 Infrastructure 层
- 第三方 API 调用需实现重试和熔断
- 外部服务超时设置：连接 5s，读取 30s

**Git 工作流**：
- 分支命名：`feature/xxx`、`fix/xxx`、`refactor/xxx`
- Commit message：Conventional Commits 格式
- PR 合并前需通过 CI 检查和 Code Review

**发布流程**：
- 版本号：语义化版本（SemVer）
- 发布分支：从 `main` 创建 `release/vX.Y.Z`
- Changelog：每个版本更新 CHANGELOG.md
```

---

## 完整配置文件结构

```
project/
├── CLAUDE.md                    # 项目核心配置
├── CLAUDE.local.md              # 个人偏好（不提交）
├── .claude/
│   └── rules/
│       ├── code-style.md        # 通用编码风格
│       ├── python-style.md      # Python 专用规则
│       ├── testing.md           # 测试规范
│       ├── security.md          # 安全规范
│       ├── documentation.md     # 文档规范
│       └── readme.md            # README 规范
├── backend/
│   └── CLAUDE.md                # 后端模块配置
├── frontend/
│   └── CLAUDE.md                # 前端模块配置
└── docs/
    └── decisions/               # 架构决策记录（ADR）
        ├── 001-use-ddd.md
        └── 002-api-versioning.md
```

---

## Token 预算估算

| 文件 | 预估行数 | Token 影响 |
|------|:-------:|:---------:|
| `CLAUDE.md` | ~150 行 | 常驻 |
| `.claude/rules/*.md` (6个) | ~200 行 | 常驻 |
| 子目录 `CLAUDE.md` (2个) | ~60 行 | 常驻 |
| **总计** | ~410 行 | 常驻 |

**优化建议**：如果 token 预算紧张，可将详细的 API 设计规范移至 `docs/api-guidelines.md`，在 CLAUDE.md 中仅保留索引链接。
