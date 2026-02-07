# CLAUDE.md - 后端项目入口

> **职责**: 后端项目的入口规范，定义技术栈、开发命令和核心原则。

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **回复语言要求参见根目录 `CLAUDE.md`**

---

## 技术栈

**核心**: Python 3.11 | FastAPI | SQLAlchemy 2.0+ (async) | Pydantic v2 | MySQL 8.0+

**工具**: black (格式化) | Ruff (lint) | MyPy (类型检查) | pytest + pytest-asyncio

**AWS**: boto3, aioboto3 (异步必须), sagemaker-hyperpod

版本矩阵和约束详见 [rules/tech-stack.md](.claude/rules/tech-stack.md)

---

## 开发命令

### 代码质量

```bash
# 格式化
black src/ tests/

# Lint
ruff check src/ tests/

# 类型检查
mypy src/

# 一键运行所有检查
black --check src/ && ruff check src/ && mypy src/
```

### 测试

```bash
# 运行所有测试
pytest

# 带覆盖率
pytest --cov=src --cov-report=term-missing

# 按类型运行
pytest tests/unit -v              # 单元测试
pytest tests/integration -v       # 集成测试
pytest tests/architecture -v      # 架构合规检查

# 按前缀筛选
pytest -k "test_entity_" -v      # 实体测试
pytest -k "test_svc_" -v         # 服务测试
```

### 服务运行

```bash
# 开发模式
uvicorn src.main:app --reload

# 数据库迁移
alembic upgrade head
alembic revision --autogenerate -m "xxx"
```

---

## 核心架构

**架构模式**: DDD + Modular Monolith + Clean Architecture

**依赖方向**: `API → Application → Domain ← Infrastructure`

**核心架构规范**: [`.claude/rules/architecture.md`](.claude/rules/architecture.md) — 架构规范单一真实源

---

## 异常处理

使用 `@problem` 装饰器 + `@dataclass` 简化异常定义（代码量减少 60%）：

```python
@problem(404, "TRAINING_JOB_NOT_FOUND", "TrainingJob '{job_id}' not found")
@dataclass
class TrainingJobNotFoundError(Problem):
    job_id: str

# 使用: raise TrainingJobNotFoundError(job_id="job-123")
```

> 详细实现参见 `.claude/skills/decorator-exception/SKILL.md`

---

## 环境变量

通过 `.env` 文件或环境变量配置:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `mysql+aiomysql://...` | 数据库连接串 |
| `AWS_REGION` | `us-east-1` | AWS 区域 |
| `S3_BUCKET_NAME` | `ai-training-platform` | S3 桶名称 |
| `SECRET_KEY` | `change-me-in-production` | JWT 密钥 |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | 允许的 CORS 源 |

---

## 规范文档索引

| 文档 | 位置 | 说明 |
|------|------|------|
| **架构规范** | [rules/architecture.md](.claude/rules/architecture.md) | 架构规范单一真实源 |
| **测试规范** | [rules/testing.md](.claude/rules/testing.md) | TDD 工作流、前缀命名、Fixture |
| **代码风格** | [rules/code-style.md](.claude/rules/code-style.md) | 类型提示、命名、Docstring |
| **安全规范** | [rules/security.md](.claude/rules/security.md) | 禁止事项、检测命令 |
| **API 设计** | [rules/api-design.md](.claude/rules/api-design.md) | RESTful 路由、状态码、错误格式 |
| **SDK 优先** | [rules/sdk-first.md](.claude/rules/sdk-first.md) | SDK 决策流程、aioboto3 规范 |
| **技术栈** | [rules/tech-stack.md](.claude/rules/tech-stack.md) | 版本矩阵、关键约束 |
| **日志规范** | [rules/logging.md](.claude/rules/logging.md) | structlog、Correlation ID、脱敏 |
| **可观测性** | [rules/observability.md](.claude/rules/observability.md) | Metrics、Tracing、Health Check |
| **项目结构** | [rules/project-structure.md](.claude/rules/project-structure.md) | 目录结构、配置文件 |
| **检查清单** | [rules/checklist.md](.claude/rules/checklist.md) | PR Review 8 类检查项 |
| **项目配置** | [.claude/project-config.md](.claude/project-config.md) | 模块清单、事件、导入路径 |
| **功能规范** | `specs/001-ai-training-platform/spec.md` | 术语标准、功能需求 |
| **数据模型** | `specs/001-ai-training-platform/data-model.md` | 数据库设计 |

---

## 预提交一键验证

```bash
black --check src/ && ruff check src/ && mypy src/ && pytest --cov=src --cov-fail-under=85
```
