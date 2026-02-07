# Backend Tests 规范指南

> **版本**: 2.0 | **更新**: 2026-02-07

> **完整测试规范请参见**: [`../.claude/rules/testing.md`](../.claude/rules/testing.md)

本文件为测试目录的快速参考入口，详细规范已迁移至 `.claude/rules/testing.md`。

---

## 速查：文件前缀 → 测试对象

**单元测试 (unit/)**:

| 前缀 | 测试对象 | 示例 |
|------|---------|------|
| `test_entity_` | 领域实体 | `test_entity_training_job.py` |
| `test_vo_` | 值对象 | `test_vo_job_status.py` |
| `test_event_` | 域事件 | `test_event_job_completed.py` |
| `test_svc_` | 应用服务 | `test_svc_training.py` |
| `test_dto_` | DTO | `test_dto_training_job.py` |
| `test_schema_` | Pydantic Schema | `test_schema_training.py` |

**集成测试 (integration/)**:

| 前缀 | 测试对象 | 示例 |
|------|---------|------|
| `test_api_` | API 端点 | `test_api_training.py` |
| `test_repo_` | 仓库实现 | `test_repo_training_job.py` |

**特殊测试**: `test_arch_` (架构合规) | `test_e2e_` (端到端) | `test_aws_` (AWS 集成) | `test_perf_` (性能)

---

## 常用命令

```bash
pytest tests/unit -v              # 单元测试
pytest tests/integration -v       # 集成测试
pytest tests/architecture -v      # 架构合规
pytest -k "test_entity_" -v      # 按前缀筛选
pytest --lf                       # 重跑失败
pytest -x                         # 失败即停
pytest --cov=src                  # 带覆盖率
```

---

## 关键规则

- ❌ 创建无前缀的 `test_*.py` 文件
- ❌ 在 `unit/` 目录使用真实数据库
- ❌ Mock 被测对象 → ✅ 只 Mock 外部依赖
- ✅ AAA 模式: Arrange → Act → Assert
- ✅ 命名: `test_{action}_{condition}_{expected_result}`
- ✅ 覆盖率: 整体 ≥85%，Domain ≥95%

> 完整规范 (Mock 策略、Fixture 层级、标记系统、覆盖率要求) 见 [rules/testing.md](../.claude/rules/testing.md)
