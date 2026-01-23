# CDK 规范索引

## 按需加载

| 规范 | 触发路径 |
|------|----------|
| 02-stack-design | `stacks/**/*.py` |
| 03-construct-design | `cdk_constructs/**/*.py` |
| 04-configuration | `config/**/*.py` |
| 06-testing | `tests/**/*.py` |
| 07-security | `stacks/**/*.py`, `utils/iam_*.py` |
| 08-hyperpod | `*hyperpod*.py`, `helm_charts/**` |

## 始终加载

- `01-architecture.md` - 依赖规则
- `05-code-style.md` - 代码风格

## 命令速查

```bash
ruff check . && mypy .          # 检查
pytest -m unit                  # 测试
cdk deploy --context env=dev    # 部署
```
