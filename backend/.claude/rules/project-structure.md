# 项目目录结构规范 (Project Structure)

> **职责**: 项目目录结构规范，定义文件组织和配置文件约定。

---

## 0. 速查卡片

### 后端目录结构

```
backend/                        # 后端项目根目录
├── .claude/                    # Claude Code 上下文 (规范文档)
│   ├── project-config.md       # 模块清单、事件、导入路径
│   └── rules/                  # 后端专用规则 (12 个文件)
├── docs/                       # 辅助文档
├── alembic/                    # 数据库迁移 (Alembic)
├── scripts/                    # 工具脚本
├── src/                        # 源代码
│   ├── modules/                # 业务模块 (9 个)
│   │   ├── auth/               # 用户认证与授权
│   │   ├── training/           # 训练任务管理
│   │   ├── models/             # 模型管理
│   │   ├── quotas/             # 资源配额管理
│   │   ├── spaces/             # 开发空间管理
│   │   ├── datasets/           # 数据集版本管理
│   │   ├── billing/            # 成本统计与计费
│   │   ├── monitoring/         # 训练监控与告警
│   │   └── audit/              # 审计日志
│   ├── shared/                 # 共享内核
│   │   ├── domain/             # 基础实体、仓库接口、域事件、跨模块接口
│   │   ├── application/        # 共享应用层基础设施
│   │   ├── infrastructure/     # 数据库、配置、安全
│   │   ├── api/                # 中间件、异常处理、分页
│   │   └── utils/              # 工具函数
│   ├── main.py                 # 应用入口
│   └── router.py               # 路由聚合
├── tests/                      # 测试代码 → testing.md
│   ├── conftest.py             # 全局 Fixture
│   ├── shared/                 # 共享测试基础设施
│   ├── unit/{module}/          # 单元测试 (类型前缀)
│   ├── integration/{module}/   # 集成测试
│   ├── architecture/           # 架构合规测试
│   ├── e2e/                    # 端到端测试
│   └── performance/            # 性能测试
├── CLAUDE.md                   # 后端入口规范
├── pyproject.toml              # 项目配置 (black/ruff/mypy/pytest)
├── Dockerfile                  # Docker 构建
└── alembic.ini                 # Alembic 配置
```

### 模块内部结构模板

```
modules/{module}/
├── __init__.py             # 模块公开 API 导出
├── api/
│   ├── endpoints/          # FastAPI router
│   ├── dependencies.py     # 依赖注入函数
│   └── schemas/            # Pydantic 请求/响应模型
├── application/
│   ├── dto/                # 数据传输对象
│   ├── interfaces/         # 模块内外部服务抽象
│   └── services/
├── domain/
│   ├── entities/
│   ├── value_objects/
│   ├── repositories/       # 仓库接口
│   ├── events.py
│   └── exceptions.py
└── infrastructure/
    ├── models/             # ORM 模型
    ├── repositories/       # 仓库实现
    └── {external}/         # 外部服务客户端
```

### 配置文件速查

| 文件 | 用途 | 必须 |
|------|------|:----:|
| `pyproject.toml` | 项目和工具配置 (black/ruff/mypy/pytest) | ✅ |
| `CLAUDE.md` | 后端入口规范 | ✅ |
| `Dockerfile` | 容器构建 | ✅ |
| `alembic.ini` | 数据库迁移配置 | ✅ |
| `.env.example` | 环境变量模板 | 推荐 |

---

## 1. 禁止事项

| 规则 | 说明 |
|------|------|
| ❌ 根目录放业务代码 | 所有业务代码必须在 `src/` 下 |
| ❌ 测试散落源码目录 | 测试必须在 `tests/`，镜像 `src/` 结构 |
| ❌ 配置文件散落各处 | 配置统一在根目录或 `.claude/` |
| ❌ 临时文件入版本控制 | `.gitignore` 必须排除 |
| ❌ 导出 ORM Model 或 RepositoryImpl | `__init__.py` 只导出公开 API |

---

## 2. 跨文档引用

| 内容 | 参考文档 |
|------|---------|
| `src/modules/{module}/` 内部结构 | [architecture.md](architecture.md) §7 |
| `tests/` 结构和前缀命名 | [testing.md](testing.md) §1 |
| 模块清单和导入路径 | [../project-config.md](../project-config.md) |
| 根级通用规范 | [../../CLAUDE.md](../../CLAUDE.md) |

---

## PR Review 检查清单

完整检查清单见 [checklist.md](checklist.md) §项目结构
