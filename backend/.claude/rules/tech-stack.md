# 技术栈规范 (Tech Stack Standards)

> **职责**: 技术栈版本要求的**单一真实源**。

---

## §0 速查卡片

### 版本要求矩阵

| 类别 | 技术 | 当前版本 | 说明 |
|------|------|---------|------|
| **语言** | Python | 3.11 | target-version |
| **Web 框架** | FastAPI | >=0.115.0 | 异步优先 |
| **ASGI 服务器** | Uvicorn | >=0.27.0 | 生产用 workers=4 |
| **数据验证** | Pydantic | >=2.10.0 | pydantic-settings 配置管理 |
| **ORM** | SQLAlchemy (async) | >=2.0.35 | aiomysql 异步驱动 |
| **数据库迁移** | Alembic | >=1.13.1 | 基于 SQLAlchemy |
| **数据库** | MySQL | 8.0+ | Aurora MySQL 3.x 兼容 |
| **AWS SDK** | boto3 / aioboto3 | >=1.34.14 / >=13.0.0 | 异步操作必须用 aioboto3 |
| **HyperPod** | sagemaker-hyperpod | 1.0.0 | 训练任务管理 |
| **认证** | Authlib | >=1.3.0 | OAuth2/OIDC |
| **JWT** | python-jose | - | JWT 签发和验证 |
| **密码** | passlib | - | bcrypt 哈希 |
| **日志** | structlog | >=24.1.0 | 结构化 JSON 日志 |
| **实验追踪** | MLflow | >=2.10.0 | 训练指标记录 |
| **格式化** | black | line-length=120 | Python 3.11 target |
| **代码检查** | Ruff | line-length=120 | E/W/F/I/UP 规则 |
| **类型检查** | MyPy | disallow_untyped_defs | 非 strict，有 overrides |
| **测试** | pytest + pytest-asyncio | asyncio_mode=auto | 含 coverage |

### 关键约束

- **格式化**: black (line-length=120)，Ruff 的 E501 委托 black 处理
- **异步 MySQL 驱动**: aiomysql（非 asyncmy）
- **MyPy 模式**: `disallow_untyped_defs=true`，非 strict。AWS SDK / passlib / 动态仓库方法有 overrides（详见 `pyproject.toml`）
- **AWS 异步**: 必须使用 aioboto3，禁止 boto3 + run_in_executor

### 快速验证命令

```bash
# 检查核心版本
python --version

# 检查依赖版本
python -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')"
python -c "import sqlalchemy; print(f'SQLAlchemy: {sqlalchemy.__version__}')"
python -c "import pydantic; print(f'Pydantic: {pydantic.__version__}')"
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| [../CLAUDE.md](../CLAUDE.md) | 技术栈概述和开发命令 |
| [testing.md](testing.md) | 测试规范 |
| [code-style.md](code-style.md) | 代码风格规范 |
| `pyproject.toml` | MyPy overrides 详细配置 |
