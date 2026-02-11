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

# Makefile 复合命令
make lint                       # ruff check + format + mypy
make test                       # pytest -m unit
make check                      # lint + test 一键验证

# CDK 操作
cdk synth                       # 合成模板
cdk diff --context env=dev      # 查看变更
cdk deploy --context env=dev    # 部署

# 安全门控（部署前必须执行）
make diff-check                 # dev 环境 diff 安全检查
make diff-check-staging         # staging 环境 diff 安全检查
make diff-check-prod            # prod 环境 diff 安全检查
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
| security | 编辑 `stacks/**/*.py`, `utils/nag_suppressions.py`, `utils/iam_helpers.py` |
| hyperpod | 编辑 `stacks/compute/sagemaker_hyperpod_stack.py`, `stacks/compute/hyperpod_addons_stack.py` |
| deployment | 编辑 `app.py`, `cdk.json` |
| cost-optimization | 编辑 `stacks/**/*.py`, `config/environments.py` |

**手动引用**:

| 规范 | 用途 |
|------|------|
| [checklist.md](.claude/rules/checklist.md) | PR Review 检查清单 (SSOT) |
| [tech-stack.md](.claude/rules/tech-stack.md) | 技术栈版本要求 (SSOT) |
| [project-config.md](.claude/project-config.md) | 项目信息、Construct 列表 |
