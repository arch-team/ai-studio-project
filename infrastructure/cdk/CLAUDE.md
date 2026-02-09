# CLAUDE.md

CDK 项目开发指南 - AI Training Platform 基础设施

> **回复语言**: 中文 (参见根目录 `CLAUDE.md`)

---

## 常用命令

```bash
# 代码质量
ruff check . && ruff format .   # Lint + Format
mypy .                          # 类型检查
pytest -m unit                  # 单元测试

# CDK 操作
cdk synth                       # 合成模板
cdk diff --context env=dev      # 查看变更
cdk deploy --context env=dev    # 部署
```

---

## 规范文档

**始终加载**: `architecture.md` (Stack 分层/VPC) + `code-style.md` (命名/类型注解)

**按需自动加载** (`.claude/rules/`):

| 规范 | 触发条件 |
|------|----------|
| stack-design | 编辑 `stacks/**/*.py` |
| construct-design | 编辑 `cdk_constructs/**/*.py` |
| configuration | 编辑 `config/**/*.py` |
| testing | 编辑 `tests/**/*.py` |
| security | 编辑安全相关代码 |
| hyperpod | 编辑 HyperPod 相关代码 |
| deployment | 编辑 `app.py`, `cdk.json` |
| cost-optimization | 编辑 `stacks/**/*.py`, `config/environments.py` |

**手动引用**:

| 规范 | 用途 |
|------|------|
| [checklist.md](.claude/rules/checklist.md) | PR Review 检查清单 (SSOT) |
| [tech-stack.md](.claude/rules/tech-stack.md) | 技术栈版本要求 (SSOT) |
